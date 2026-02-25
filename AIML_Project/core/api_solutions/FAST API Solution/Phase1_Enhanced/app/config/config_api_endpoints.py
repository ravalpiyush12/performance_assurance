"""
Configuration API Endpoints
Add these to main.py to serve database configuration and API keys to the frontend
"""

from fastapi import APIRouter
from typing import Dict, List

# Configuration Router
config_router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])


@config_router.get("/databases-info", summary="Get databases configuration for UI")
async def get_databases_info():
    """
    Get all databases configuration including available operations and auth type
    Used by frontend to populate database dropdown
    """
    databases_info = {}
    
    for db_name in app.state.connection_manager.get_available_databases():
        db_config = app.state.settings.get_database(db_name)
        databases_info[db_name] = {
            "name": db_name,
            "host": db_config.host,
            "port": db_config.port,
            "service_name": db_config.service_name,
            "allowed_operations": db_config.allowed_operations,
            "auth_type": "CyberArk" if db_config.use_cyberark else "Direct",
            "status": "available"
        }
    
    # Add failed databases
    for db_name, error in app.state.connection_manager.failed_databases.items():
        db_config = app.state.settings.get_database(db_name)
        if db_config:
            databases_info[db_name] = {
                "name": db_name,
                "host": db_config.host,
                "allowed_operations": db_config.allowed_operations,
                "auth_type": "CyberArk" if db_config.use_cyberark else "Direct",
                "status": "unavailable",
                "error": error
            }
    
    return {
        "environment": app.state.settings.ENVIRONMENT,
        "version": app.state.settings.APP_VERSION,
        "total_databases": len(databases_info),
        "databases": list(databases_info.values())
    }


@config_router.get("/api-keys", summary="Get API keys for all databases")
async def get_api_keys_config():
    """
    Get available API keys for all databases
    Used by frontend to display and auto-select API keys
    
    Returns a mapping of database name to list of API keys
    """
    api_keys_map = {}
    
    databases = app.state.settings.get_databases()
    
    for db_name, db_config in databases.items():
        # Get list of API keys for this database
        api_keys = db_config.get_api_keys_list()
        api_keys_map[db_name] = api_keys
    
    return {
        "api_keys": api_keys_map,
        "total_databases": len(api_keys_map),
        "note": "These API keys are read from environment variables"
    }


@config_router.get("/environment", summary="Get environment information")
async def get_environment_info():
    """
    Get current environment configuration
    """
    return {
        "environment": app.state.settings.ENVIRONMENT,
        "version": app.state.settings.APP_VERSION,
        "debug": app.state.settings.DEBUG,
        "audit_enabled": app.state.settings.ENABLE_AUDIT_LOG,
        "cyberark_enabled": app.state.settings.CYBERARK_ENABLED
    }


# ========================================
# Add to main.py after creating app
# ========================================
# app.include_router(config_router)


"""
INTEGRATION WITH MAIN.PY:

1. Add import at top:
   from fastapi import APIRouter

2. After creating app, include this router:
   config_router = APIRouter(prefix="/api/v1/config", tags=["Configuration"])
   
   # ... add the endpoints above ...
   
   app.include_router(config_router)

3. The frontend will call:
   - GET /api/v1/config/databases-info  (for dropdown population)
   - GET /api/v1/config/api-keys        (for API key display)
   - GET /api/v1/config/environment     (for header info)
"""