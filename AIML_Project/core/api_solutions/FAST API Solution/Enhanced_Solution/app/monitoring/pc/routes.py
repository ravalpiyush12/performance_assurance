"""
Performance Center API Routes
Includes test registration, fetching results, and health status
"""
from fastapi import APIRouter, HTTPException, Form
from typing import Optional
import logging
from datetime import datetime

from .models import (
    PCConnectionRequest,
    PCFetchResponse,
    PCResultsResponse,
    PCHealthStatus
)
from .client import PerformanceCenterClient
from .parser import SummaryHTMLParser
from .database import PCDatabase
from common.run_id_generator import RunIDGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pc", tags=["Performance Center"])

# Global database instance (initialized at startup)
pc_db: Optional[PCDatabase] = None


def init_pc_routes(db_pool):
    """
    Initialize PC routes with database connection
    
    Args:
        db_pool: Oracle connection pool
    """
    global pc_db
    pc_db = PCDatabase(db_pool)
    logger.info("PC routes initialized")


# ==========================================
# Test Registration Endpoints
# ==========================================

@router.post("/test-run/register")
async def register_test_run(
    pc_run_id: str = Form(..., description="Performance Center run ID"),
    lob_name: str = Form(..., description="Line of Business"),
    test_name: str = Form(..., description="Test name"),
    track: Optional[str] = Form(None),
    test_start_time: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None)
):
    """
    Register a Performance Center test run
    Creates master RUN_ID that all monitoring solutions will link to
    
    This should be called FIRST before starting any monitoring activities
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        # Generate master run ID
        sequence = pc_db.get_next_sequence_for_pc_run(pc_run_id)
        master_run_id = RunIDGenerator.generate_master_run_id(pc_run_id, sequence)
        
        logger.info(f"Registering test run: {master_run_id} for PC_RUN_ID: {pc_run_id}")
        
        # Parse start time if provided
        start_time = None
        if test_start_time:
            start_time = datetime.fromisoformat(test_start_time)
        
        # Create master entry
        success = pc_db.create_master_run(
            run_id=master_run_id,
            pc_run_id=pc_run_id,
            lob_name=lob_name,
            track=track,
            test_name=test_name,
            created_by=created_by
        )
        
        if success:
            # Update start time if provided
            if start_time:
                pc_db.update_run_start_time(master_run_id, start_time)
            
            logger.info(f"✓ Test run registered: {master_run_id}")
            
            return {
                "success": True,
                "master_run_id": master_run_id,
                "pc_run_id": pc_run_id,
                "lob_name": lob_name,
                "track": track,
                "test_name": test_name,
                "message": f"Test run registered successfully! Master Run ID: {master_run_id}"
            }
        else:
            # Run already exists
            logger.warning(f"Test run already registered for PC_RUN_ID: {pc_run_id}")
            return {
                "success": False,
                "message": f"Test run with PC_RUN_ID {pc_run_id} is already registered today"
            }
            
    except Exception as e:
        logger.error(f"Error registering test run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-run/current")
async def get_current_test_run():
    """Get the most recently registered test run"""
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        run = pc_db.get_latest_test_run()
        
        if run:
            return {
                "success": True,
                "has_active_test": True,
                "test_run": run
            }
        else:
            return {
                "success": True,
                "has_active_test": False,
                "message": "No active test run found"
            }
            
    except Exception as e:
        logger.error(f"Error getting current test run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-run/recent")
async def get_recent_test_runs(limit: int = 10):
    """Get recent test run registrations"""
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        runs = pc_db.get_recent_test_runs(limit)
        
        return {
            "success": True,
            "count": len(runs),
            "test_runs": runs
        }
            
    except Exception as e:
        logger.error(f"Error getting recent test runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-run/by-pc-id/{pc_run_id}")
async def get_test_run_by_pc_id(pc_run_id: str):
    """Get master run info by PC run ID"""
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        run = pc_db.get_master_run_by_pc_id(pc_run_id)
        
        if run:
            return {
                "success": True,
                "test_run": run
            }
        else:
            return {
                "success": False,
                "message": f"No test run found for PC_RUN_ID: {pc_run_id}"
            }
            
    except Exception as e:
        logger.error(f"Error getting test run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# PC Results Fetching Endpoints
# ==========================================

@router.post("/fetch-results", response_model=PCFetchResponse)
async def fetch_pc_results(request: PCConnectionRequest):
    """
    Fetch LoadRunner test results from Performance Center
    
    Prerequisites:
    - Test run must be registered first (use /test-run/register)
    - PC test must be finished and collated
    
    Steps:
    1. Validate that master run exists
    2. Connect to Performance Center
    3. Check test status and collation
    4. Download summary.html report
    5. Parse LoadRunner transactions
    6. Store in database
    
    Args:
        request: PC connection request with credentials and run details
        
    Returns:
        PCFetchResponse with transactions and test status
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        logger.info(f"Fetching PC results for run {request.pc_run_id}")
        
        # Validate that master run exists
        master_run = pc_db.get_master_run_by_pc_id(request.pc_run_id)
        if not master_run:
            raise HTTPException(
                status_code=400,
                detail=f"Test run not registered. Please register PC_RUN_ID {request.pc_run_id} first using /test-run/register"
            )
        
        # Use master run_id from database
        run_id = master_run['run_id']
        logger.info(f"Using master RUN_ID: {run_id}")
        
        # Create PC client
        pc_url_full = f"{request.pc_url}:{request.pc_port}"
        pc_client = PerformanceCenterClient(
            base_url=pc_url_full,
            username=request.username,
            password=request.password,
            domain=request.pc_domain,
            project=request.pc_project
        )
        
        # Authenticate
        logger.info("Authenticating with Performance Center...")
        pc_client.authenticate()
        
        # Get test status
        logger.info(f"Getting test status for run {request.pc_run_id}...")
        test_info = pc_client.get_test_run_status(request.pc_run_id)
        
        test_status = test_info.get('status', 'Unknown')
        collation_status = test_info.get('collation_status', 'Unknown')
        
        logger.info(f"Test Status: {test_status}, Collation: {collation_status}")
        
        # Check if collation is complete
        if collation_status.lower() not in ['collated', 'collate and analyze']:
            # Save test run even if not collated
            pc_test_id = pc_db.save_pc_test_run(
                run_id=run_id,
                pc_run_id=request.pc_run_id,
                pc_url=request.pc_url,
                pc_domain=request.pc_domain,
                pc_project=request.pc_project,
                test_status=test_status,
                collation_status=collation_status,
                test_set_name=request.test_set_name,
                test_instance_id=request.test_instance_id
            )
            
            pc_client.logout()
            
            return PCFetchResponse(
                success=False,
                run_id=run_id,
                pc_run_id=request.pc_run_id,
                pc_test_id=pc_test_id,
                test_status=test_status,
                collation_status=collation_status,
                transactions=[],
                total_transactions=0,
                passed_transactions=0,
                failed_transactions=0,
                average_response_time=0.0,
                message=(
                    f"Test not ready. Collation status: {collation_status}. "
                    f"Please wait for collation to complete before fetching results."
                )
            )
        
        # Download summary.html
        logger.info("Downloading summary.html report...")
        summary_html = pc_client.download_summary_report(request.pc_run_id)
        
        # Logout
        pc_client.logout()
        
        # Parse transactions
        logger.info("Parsing LoadRunner transactions...")
        parser = SummaryHTMLParser(summary_html)
        transactions = parser.parse_transactions()
        
        if not transactions:
            raise HTTPException(
                status_code=404,
                detail="No transactions found in summary.html report"
            )
        
        # Save to database
        logger.info(f"Saving {len(transactions)} transactions to database...")
        
        # Save PC test run
        pc_test_id = pc_db.save_pc_test_run(
            run_id=run_id,
            pc_run_id=request.pc_run_id,
            pc_url=request.pc_url,
            pc_domain=request.pc_domain,
            pc_project=request.pc_project,
            test_status=test_status,
            collation_status=collation_status,
            test_set_name=request.test_set_name,
            test_instance_id=request.test_instance_id
        )
        
        # Mark report as fetched
        pc_db.update_pc_test_status(
            pc_test_id=pc_test_id,
            test_status=test_status,
            collation_status=collation_status,
            report_fetched=True
        )
        
        # Save transactions
        pc_db.save_lr_transactions(
            run_id=run_id,
            pc_run_id=request.pc_run_id,
            transactions=[t.dict() for t in transactions]
        )
        
        # Update master run status
        pc_db.update_run_status(run_id, 'COMPLETED')
        
        # Calculate statistics
        total = len(transactions)
        passed = sum(1 for t in transactions if t.pass_percentage >= 95.0)
        failed = total - passed
        avg_response = sum(t.average_time for t in transactions) / total if total > 0 else 0.0
        
        logger.info(
            f"✓ Successfully fetched PC results: {total} transactions "
            f"({passed} passed, {failed} failed)"
        )
        
        return PCFetchResponse(
            success=True,
            run_id=run_id,
            pc_run_id=request.pc_run_id,
            pc_test_id=pc_test_id,
            test_status=test_status,
            collation_status=collation_status,
            transactions=transactions,
            total_transactions=total,
            passed_transactions=passed,
            failed_transactions=failed,
            average_response_time=avg_response,
            message=f"Successfully fetched {total} transactions. {passed} passed, {failed} failed."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching PC results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{run_id}", response_model=PCResultsResponse)
async def get_pc_results(run_id: str):
    """
    Get LoadRunner transaction results for a run
    
    Args:
        run_id: Master run ID
        
    Returns:
        PCResultsResponse with transactions
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        # Get PC test info
        pc_test = pc_db.get_pc_test_by_run_id(run_id)
        
        if not pc_test:
            raise HTTPException(
                status_code=404,
                detail=f"No PC test found for run {run_id}"
            )
        
        # Get transactions
        transactions = pc_db.get_lr_transactions(run_id)
        
        if not transactions:
            raise HTTPException(
                status_code=404,
                detail=f"No transactions found for run {run_id}"
            )
        
        # Calculate statistics
        total = len(transactions)
        passed = sum(1 for t in transactions if t['pass_percentage'] >= 95.0)
        failed = total - passed
        avg_response = sum(t['average_time'] for t in transactions) / total if total > 0 else 0.0
        
        # Convert to LRTransaction models
        from .models import LRTransaction
        trans_models = [LRTransaction(**t) for t in transactions]
        
        return PCResultsResponse(
            success=True,
            run_id=run_id,
            pc_run_id=pc_test['pc_run_id'],
            test_status=pc_test['test_status'],
            collation_status=pc_test['collation_status'],
            total_transactions=total,
            passed_transactions=passed,
            failed_transactions=failed,
            average_response_time=avg_response,
            transactions=trans_models
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving PC results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/pc/{pc_run_id}", response_model=PCResultsResponse)
async def get_pc_results_by_pc_id(pc_run_id: str):
    """
    Get LoadRunner transaction results by PC run ID
    
    Args:
        pc_run_id: Performance Center run ID
        
    Returns:
        PCResultsResponse with transactions
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        # Get PC test info
        pc_test = pc_db.get_pc_test_by_pc_run_id(pc_run_id)
        
        if not pc_test:
            raise HTTPException(
                status_code=404,
                detail=f"No PC test found for PC run {pc_run_id}"
            )
        
        # Use the run_id to get transactions
        return await get_pc_results(pc_test['run_id'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving PC results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{lob_name}", response_model=PCHealthStatus)
async def get_pc_health_status(lob_name: str):
    """
    Get Performance Center health status for landing page
    
    Args:
        lob_name: Line of Business name
        
    Returns:
        PCHealthStatus with recent test count
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        # Get recent tests for this LOB
        recent_tests = pc_db.get_recent_pc_tests(limit=100)
        
        # Filter by LOB
        lob_tests = [t for t in recent_tests if t.get('lob_name') == lob_name]
        
        last_test_date = None
        if lob_tests:
            last_test_date = lob_tests[0].get('created_date')
        
        return PCHealthStatus(
            lob_name=lob_name,
            status="configured" if lob_tests else "not_configured",
            recent_tests=len(lob_tests),
            last_test_date=last_test_date,
            message=f"Found {len(lob_tests)} recent tests for {lob_name}"
        )
        
    except Exception as e:
        logger.error(f"Error getting PC health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_pc_tests(limit: int = 10):
    """
    Get recent PC test runs
    
    Args:
        limit: Number of tests to retrieve (default: 10)
        
    Returns:
        List of recent PC tests
    """
    if not pc_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        tests = pc_db.get_recent_pc_tests(limit=limit)
        
        return {
            "success": True,
            "count": len(tests),
            "tests": tests
        }
        
    except Exception as e:
        logger.error(f"Error getting recent PC tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))
