# 🏗️ Unified Architecture - Part 2: Unified Routes & PC Integration

## 📝 PART 3: Unified Routes (All Monitoring Solutions)

### File: `monitoring/routes.py`

```python
"""
Unified API Routes for All Monitoring Solutions
- AWR Analysis
- Performance Center
- AppDynamics
- MongoDB
- Splunk
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import Optional
import logging

from .models import (
    AWRUploadRequest, AWRAnalysisResponse,
    PCConnectionRequest, PCFetchResponse,
    MongoDBStatsResponse, SplunkStatusResponse
)
from .database import MonitoringDatabase
from .awr.parser import AWRParser
from .awr.analyzer import AWRAnalyzer
from .pc.client import PerformanceCenterClient
from .pc.parser import SummaryHTMLParser
from common.run_id_generator import RunIDGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])

# Global database instance (initialized at startup)
monitoring_db: Optional[MonitoringDatabase] = None


def init_monitoring_routes(db_pool):
    """Initialize monitoring routes with database connection"""
    global monitoring_db
    monitoring_db = MonitoringDatabase(db_pool)
    logger.info("Monitoring routes initialized")


# ==========================================
# AWR Analysis Endpoints
# ==========================================

@router.post("/awr/upload", response_model=AWRAnalysisResponse)
async def upload_awr_report(
    file: UploadFile = File(..., description="AWR HTML report file"),
    run_id: str = Form(..., description="Master run ID"),
    pc_run_id: str = Form(..., description="Performance Center run ID"),
    database_name: str = Form(...),
    lob_name: str = Form(...),
    track: Optional[str] = Form(None),
    test_name: Optional[str] = Form(None)
):
    """
    Upload and analyze AWR HTML report
    
    Steps:
    1. Parse AWR HTML report
    2. Analyze for performance concerns
    3. Store in database
    4. Return analysis summary
    """
    if not monitoring_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        logger.info(f"Uploading AWR report for run {run_id}")
        
        # Ensure RUN_MASTER entry exists
        monitoring_db.create_master_run(
            run_id=run_id,
            pc_run_id=pc_run_id,
            lob_name=lob_name,
            track=track,
            test_name=test_name
        )
        
        # Read file
        content = await file.read()
        html_content = content.decode('utf-8', errors='ignore')
        
        # Generate AWR-specific run ID
        awr_run_id = RunIDGenerator.generate_solution_run_id("AWR", pc_run_id, 1)
        
        # Parse AWR report
        logger.info("Parsing AWR report...")
        parser = AWRParser(html_content)
        parsed_data = parser.parse()
        header = parsed_data['header']
        
        # Analyze report
        logger.info("Analyzing AWR data...")
        analyzer = AWRAnalyzer(parsed_data)
        concerns = analyzer.analyze()
        
        # Save to database
        logger.info("Saving analysis to database...")
        analysis_id = monitoring_db.save_awr_analysis(
            run_id=run_id,
            awr_run_id=awr_run_id,
            header=header,
            parsed_data=parsed_data,
            concerns=[c.dict() for c in concerns],
            top_sql=parsed_data.get('top_sql', []),
            wait_events=parsed_data.get('wait_events', [])
        )
        
        # Update run status
        monitoring_db.update_run_status(run_id, 'ANALYZING')
        
        summary = analyzer.get_summary()
        
        return AWRAnalysisResponse(
            success=True,
            awr_run_id=awr_run_id,
            run_id=run_id,
            analysis_id=analysis_id,
            database_name=header.get('db_name', database_name),
            instance_name=header.get('instance_name', 'UNKNOWN'),
            snapshot_begin=header.get('snapshot_begin', 0),
            snapshot_end=header.get('snapshot_end', 0),
            elapsed_time_minutes=header.get('elapsed_time_minutes', 0),
            db_time_minutes=header.get('db_time_minutes', 0),
            total_concerns=summary['total_concerns'],
            critical_concerns=summary['critical_concerns'],
            warning_concerns=summary['warning_concerns'],
            concerns=concerns,
            message=f"AWR analysis completed. Found {summary['critical_concerns']} critical concerns."
        )
        
    except Exception as e:
        logger.error(f"Error processing AWR report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/awr/analysis/{run_id}")
async def get_awr_analysis(run_id: str):
    """Get AWR analysis for a specific run"""
    if not monitoring_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        analysis = monitoring_db.get_awr_analysis_by_run(run_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"No AWR analysis found for {run_id}")
        
        concerns = monitoring_db.get_awr_concerns(analysis['analysis_id'])
        
        return {
            "success": True,
            "analysis": analysis,
            "concerns": concerns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AWR analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Performance Center Endpoints
# ==========================================

@router.post("/pc/fetch-results", response_model=PCFetchResponse)
async def fetch_pc_results(request: PCConnectionRequest):
    """
    Fetch LoadRunner test results from Performance Center
    
    Steps:
    1. Connect to Performance Center
    2. Check test status and collation
    3. Download summary.html report
    4. Parse LoadRunner transactions
    5. Store in database
    """
    if not monitoring_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        logger.info(f"Fetching PC results for run {request.pc_run_id}")
        
        # Ensure RUN_MASTER entry exists
        monitoring_db.create_master_run(
            run_id=request.run_id,
            pc_run_id=request.pc_run_id,
            lob_name=request.lob_name,
            track=request.track
        )
        
        # Create PC client
        pc_client = PerformanceCenterClient(
            base_url=f"{request.pc_url}:{request.pc_port}",
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
        if collation_status.lower() != 'collated':
            return PCFetchResponse(
                success=False,
                run_id=request.run_id,
                pc_run_id=request.pc_run_id,
                test_status=test_status,
                collation_status=collation_status,
                transactions=[],
                total_transactions=0,
                passed_transactions=0,
                failed_transactions=0,
                message=f"Test not ready. Collation status: {collation_status}. Please wait for collation to complete."
            )
        
        # Download summary.html
        logger.info("Downloading summary.html report...")
        summary_html = pc_client.download_summary_report(request.pc_run_id)
        
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
        monitoring_db.save_pc_test_run(
            run_id=request.run_id,
            pc_run_id=request.pc_run_id,
            pc_url=request.pc_url,
            pc_domain=request.pc_domain,
            pc_project=request.pc_project,
            test_status=test_status,
            collation_status=collation_status
        )
        
        # Save transactions
        monitoring_db.save_lr_transactions(
            run_id=request.run_id,
            pc_run_id=request.pc_run_id,
            transactions=[t.dict() for t in transactions]
        )
        
        # Update run status
        monitoring_db.update_run_status(request.run_id, 'COMPLETED')
        
        # Calculate stats
        total = len(transactions)
        passed = sum(1 for t in transactions if t.pass_percentage >= 95.0)
        failed = total - passed
        
        return PCFetchResponse(
            success=True,
            run_id=request.run_id,
            pc_run_id=request.pc_run_id,
            test_status=test_status,
            collation_status=collation_status,
            transactions=transactions,
            total_transactions=total,
            passed_transactions=passed,
            failed_transactions=failed,
            message=f"Successfully fetched {total} transactions. {passed} passed, {failed} failed."
        )
        
    except Exception as e:
        logger.error(f"Error fetching PC results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pc/results/{run_id}")
async def get_pc_results(run_id: str):
    """Get LoadRunner transaction results for a run"""
    if not monitoring_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        transactions = monitoring_db.get_lr_transactions(run_id)
        
        if not transactions:
            raise HTTPException(status_code=404, detail=f"No PC results found for {run_id}")
        
        # Calculate summary stats
        total = len(transactions)
        passed = sum(1 for t in transactions if t['pass_percentage'] >= 95.0)
        failed = total - passed
        avg_response_time = sum(t['average_time'] for t in transactions) / total if total > 0 else 0
        
        return {
            "success": True,
            "run_id": run_id,
            "total_transactions": total,
            "passed_transactions": passed,
            "failed_transactions": failed,
            "avg_response_time": avg_response_time,
            "transactions": transactions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving PC results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pc/status/{lob_name}")
async def get_pc_health_status(lob_name: str):
    """Get Performance Center health status for landing page"""
    # Placeholder - implement based on needs
    return {
        "lob_name": lob_name,
        "status": "configured",
        "recent_tests": 0,
        "message": "Performance Center configured"
    }


# ==========================================
# MongoDB Endpoints
# ==========================================

@router.get("/mongodb/stats", response_model=MongoDBStatsResponse)
async def get_mongodb_stats(lob: str):
    """Get MongoDB statistics for LOB (placeholder)"""
    # TODO: Implement MongoDB integration
    return MongoDBStatsResponse(
        lob_name=lob,
        collections=0,
        documents=0,
        size_bytes=0,
        avg_document_size=0,
        indexes=0
    )


# ==========================================
# Splunk Endpoints
# ==========================================

@router.get("/splunk/status", response_model=SplunkStatusResponse)
async def get_splunk_status(lob: str):
    """Get Splunk indexing status for LOB (placeholder)"""
    from datetime import datetime
    
    # TODO: Implement Splunk integration
    return SplunkStatusResponse(
        lob_name=lob,
        status="active",
        last_indexed=datetime.now(),
        events_today=0,
        indexes=0
    )
```

---

## 📝 PART 4: Performance Center Client

### File: `monitoring/pc/client.py`

```python
"""
Performance Center REST API Client
"""
import requests
import base64
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PerformanceCenterClient:
    """Client for Performance Center REST API"""
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        domain: str,
        project: str
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.domain = domain
        self.project = project
        self.session = requests.Session()
        self.auth_token = None
    
    def authenticate(self):
        """Authenticate with Performance Center"""
        try:
            # Create Basic Auth header
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/xml'
            }
            
            # Authenticate
            url = f"{self.base_url}/rest/site-session"
            response = self.session.post(url, headers=headers)
            
            if response.status_code == 201:
                # Extract session cookies
                logger.info("Successfully authenticated with Performance Center")
                return True
            else:
                raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
    
    def get_test_run_status(self, run_id: str) -> Dict:
        """
        Get test run status from Performance Center
        
        Returns:
            dict with 'status' and 'collation_status'
        """
        try:
            url = f"{self.base_url}/rest/domains/{self.domain}/projects/{self.project}/runs/{run_id}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                # Extract status fields
                status = root.find('.//status')
                collation = root.find('.//collation-status')
                
                return {
                    'status': status.text if status is not None else 'Unknown',
                    'collation_status': collation.text if collation is not None else 'Unknown',
                    'run_id': run_id
                }
            else:
                raise Exception(f"Failed to get run status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting test status: {e}")
            raise
    
    def download_summary_report(self, run_id: str) -> str:
        """
        Download summary.html report from Performance Center
        
        Returns:
            HTML content as string
        """
        try:
            # Get report download URL
            url = f"{self.base_url}/rest/domains/{self.domain}/projects/{self.project}/runs/{run_id}/results/summary.html"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                logger.info(f"Downloaded summary.html for run {run_id}")
                return response.text
            else:
                raise Exception(f"Failed to download report: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error downloading summary report: {e}")
            raise
    
    def logout(self):
        """Logout from Performance Center"""
        try:
            url = f"{self.base_url}/rest/site-session"
            self.session.delete(url)
            logger.info("Logged out from Performance Center")
        except Exception as e:
            logger.warning(f"Logout error: {e}")
```

---

## 📝 PART 5: Summary.html Parser

### File: `monitoring/pc/parser.py`

```python
"""
LoadRunner Summary.html Parser
Extracts transaction statistics from Performance Center summary reports
"""
from bs4 import BeautifulSoup
import re
from typing import List
import logging
from ..models import LRTransaction

logger = logging.getLogger(__name__)


class SummaryHTMLParser:
    """Parse LoadRunner summary.html report"""
    
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
    
    def parse_transactions(self) -> List[LRTransaction]:
        """Parse transaction summary table"""
        transactions = []
        
        try:
            # Find "Transaction Summary" table
            tables = self.soup.find_all('table')
            
            for table in tables:
                # Check if this is the transaction summary table
                caption = table.find('caption')
                headers = table.find_all('th')
                header_text = ' '.join([h.get_text().strip() for h in headers])
                
                if 'Transaction' in header_text or 'Response Time' in header_text:
                    logger.info("Found transaction summary table")
                    
                    rows = table.find_all('tr')
                    
                    for row in rows[1:]:  # Skip header
                        cols = row.find_all('td')
                        
                        if len(cols) >= 10:  # Ensure we have enough columns
                            try:
                                transaction = self._parse_transaction_row(cols)
                                if transaction:
                                    transactions.append(transaction)
                            except Exception as e:
                                logger.warning(f"Error parsing row: {e}")
                                continue
            
            logger.info(f"Parsed {len(transactions)} transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Error parsing transactions: {e}", exc_info=True)
            return []
    
    def _parse_transaction_row(self, cols) -> Optional[LRTransaction]:
        """Parse single transaction row"""
        try:
            # Extract values from columns
            # Typical format:
            # Transaction Name | Min | Avg | Max | Std Dev | 90% | Pass | Fail | Stop
            
            name = cols[0].get_text().strip()
            minimum = self._extract_number(cols[1].get_text())
            average = self._extract_number(cols[2].get_text())
            maximum = self._extract_number(cols[3].get_text())
            std_dev = self._extract_number(cols[4].get_text())
            p90 = self._extract_number(cols[5].get_text())
            
            # Pass/Fail counts
            pass_count = int(self._extract_number(cols[6].get_text()) or 0)
            fail_count = int(self._extract_number(cols[7].get_text()) or 0)
            stop_count = int(self._extract_number(cols[8].get_text()) or 0) if len(cols) > 8 else 0
            
            total = pass_count + fail_count + stop_count
            pass_pct = (pass_count / total * 100) if total > 0 else 0
            
            # Try to get 95th and 99th percentiles if available
            p95 = self._extract_number(cols[9].get_text()) if len(cols) > 9 else None
            p99 = self._extract_number(cols[10].get_text()) if len(cols) > 10 else None
            
            return LRTransaction(
                transaction_name=name,
                minimum_time=minimum,
                average_time=average,
                maximum_time=maximum,
                std_deviation=std_dev,
                percentile_90=p90,
                percentile_95=p95,
                percentile_99=p99,
                pass_count=pass_count,
                fail_count=fail_count,
                stop_count=stop_count,
                total_count=total,
                pass_percentage=pass_pct
            )
            
        except Exception as e:
            logger.warning(f"Error parsing transaction row: {e}")
            return None
    
    def _extract_number(self, text: str) -> float:
        """Extract numeric value from text"""
        try:
            # Remove commas and spaces
            clean = text.replace(',', '').replace(' ', '').strip()
            
            # Extract first number found
            match = re.search(r'[\d.]+', clean)
            if match:
                return float(match.group())
            
            return 0.0
            
        except:
            return 0.0
```

**Continue to Part 3 with UI Components...**