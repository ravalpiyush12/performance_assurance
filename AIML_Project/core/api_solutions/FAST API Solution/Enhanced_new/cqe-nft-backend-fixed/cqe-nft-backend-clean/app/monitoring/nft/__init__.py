"""
NFT Platform package init.
Import order matters:
  1. models first (no internal dependencies)
  2. database second (no dependency on models)
  3. routes last (depends on both models and database)
"""

# --- models (no deps) — import first ---
from .models import (
    UserLobGrantRequest,
    UserLobRevokeRequest,
    AppdToolConfigRequest,
    KibanaConfigRequest,
    KibanaTestConnectionRequest,
    KibanaTestConnectionResponse,
    SplunkConfigRequest,
    SplunkTestConnectionResponse,
    MongoDBConfigRequest,
    MongoDBTestConnectionResponse,
    PCToolConfigRequest,
    PCTestConnectionResponse,
    DBConfigRequest,
    DBTestConnectionResponse,
    TrackTemplateRequest,
    TrackTemplateResponse,
    TestRegistrationRequest,
    TestRegistrationResponse,
    SaveReportRequest,
    SaveReportResponse,
    ReportListItem,
)

# --- database layer ---
from .database import NFTPlatformDatabase

# --- routes (depends on models + database) — import last ---
from .routes import router, init_nft_routes

__all__ = [
    "router", "init_nft_routes",
    "NFTPlatformDatabase",
    "UserLobGrantRequest", "UserLobRevokeRequest",
    "AppdToolConfigRequest",
    "KibanaConfigRequest", "KibanaTestConnectionRequest", "KibanaTestConnectionResponse",
    "SplunkConfigRequest", "SplunkTestConnectionResponse",
    "MongoDBConfigRequest", "MongoDBTestConnectionResponse",
    "PCToolConfigRequest", "PCTestConnectionResponse",
    "DBConfigRequest", "DBTestConnectionResponse",
    "TrackTemplateRequest", "TrackTemplateResponse",
    "TestRegistrationRequest", "TestRegistrationResponse",
    "SaveReportRequest", "SaveReportResponse",
    "ReportListItem",
]
