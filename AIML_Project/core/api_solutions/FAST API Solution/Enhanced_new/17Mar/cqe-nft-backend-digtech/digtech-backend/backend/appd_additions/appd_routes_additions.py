"""
APPD ROUTES ADDITIONS
=====================
Add these endpoints to your existing monitoring/appd/routes.py file.

Place them after the existing discovery endpoints.
They use the same appd_db global and verify_auth_token dependency.
"""

# ─── ADD THESE IMPORTS at the top of appd/routes.py (if not already present) ──
# from typing import Optional, List  ← already there
# from fastapi import APIRouter, HTTPException, Depends, Query  ← already there

# ─── ADD THESE ENDPOINTS to appd/routes.py ────────────────────────────────────


@router.get("/metrics/{run_id}")
async def get_appd_metrics_for_run(
    run_id: str,
    current_user: str = Depends(verify_auth_token)
):
    """
    Retrieve all AppDynamics metrics stored for a run_id.
    Used by test-report.html AppDynamics Analysis tab.
    Returns: application_metrics, server_metrics, jvm_metrics, node_summary
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="AppDynamics service not initialized")
    try:
        # Get application-level metrics (response time, errors, BT counts, apdex)
        app_metrics = appd_db.get_application_metrics_by_run(run_id)

        # Get server metrics (CPU, memory, disk, network)
        server_metrics = appd_db.get_server_metrics_by_run(run_id)

        # Get JVM metrics (heap, GC, threads)
        jvm_metrics = appd_db.get_jvm_metrics_by_run(run_id)

        # Get node summary from monitoring run record
        monitoring_session = appd_db.get_monitoring_sessions(run_id=run_id)

        return {
            'success': True,
            'run_id': run_id,
            'application_metrics': app_metrics,
            'server_metrics': server_metrics,
            'jvm_metrics': jvm_metrics,
            'monitoring_session': monitoring_session[0] if monitoring_session else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get AppD metrics error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AppD metrics: {str(e)}")


@router.get("/metrics/{run_id}/summary")
async def get_appd_metrics_summary(
    run_id: str,
    current_user: str = Depends(verify_auth_token)
):
    """
    Aggregated summary of AppD metrics for a run.
    Returns avg response time, error rate, apdex, top nodes by CPU.
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="AppDynamics service not initialized")
    try:
        summary = appd_db.get_run_summary(run_id)
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"No AppDynamics metrics found for run_id '{run_id}'"
            )
        return {'success': True, 'run_id': run_id, 'summary': summary}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get AppD summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")


@router.get("/nodes/{run_id}")
async def get_active_nodes_for_run(
    run_id: str,
    current_user: str = Depends(verify_auth_token)
):
    """
    Get the node-level detail for a specific run.
    Returns node name, tier, app, CPM, active status — for the AppD node table in test-report.html.
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="AppDynamics service not initialized")
    try:
        nodes = appd_db.get_nodes_for_run(run_id)
        return {
            'success': True,
            'run_id': run_id,
            'nodes': nodes,
            'total_nodes': len(nodes),
            'active_nodes': sum(1 for n in nodes if n.get('is_active') == 'Y'),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get AppD nodes error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nodes: {str(e)}")
