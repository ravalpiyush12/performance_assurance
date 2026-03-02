# Updated API endpoint for /master/applications with TRACK support

@router.get("/master/applications")
async def get_master_applications(
    lob_name: Optional[str] = None,
    track: Optional[str] = None
):
    """
    Get list of all applications for dropdown
    
    Query Parameters:
        lob_name: Optional LOB name to filter
        track: Optional Track to filter
        
    Returns applications filtered by LOB and/or Track
    """
    if not appd_db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        apps = appd_db.get_master_applications(lob_name, track)
        return {
            "total": len(apps),
            "applications": apps,
            "filters": {
                "lob_name": lob_name,
                "track": track
            }
        }
    except Exception as e:
        logger.error(f"Failed to get master applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))