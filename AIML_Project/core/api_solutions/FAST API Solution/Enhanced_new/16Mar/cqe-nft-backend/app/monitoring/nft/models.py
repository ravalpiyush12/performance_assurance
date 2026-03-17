"""
NFT Platform Pydantic Models - v1.10.x compatible
Uses schema_extra for examples, matching existing monitoring/appd pattern.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# =============================================================================
# USER LOB ACCESS
# =============================================================================

class UserLobGrantRequest(BaseModel):
    username: str
    lob_name: str
    granted_by: str

    class Config:
        schema_extra = {
            "example": {
                "username": "john.doe",
                "lob_name": "Digital Technology",
                "granted_by": "admin"
            }
        }


class UserLobRevokeRequest(BaseModel):
    username: str
    lob_name: str
    revoked_by: str

    class Config:
        schema_extra = {
            "example": {
                "username": "john.doe",
                "lob_name": "Digital Technology",
                "revoked_by": "admin"
            }
        }


class UserLobAccessResponse(BaseModel):
    success: bool
    message: str
    access_id: Optional[int] = None
    username: Optional[str] = None
    lob_name: Optional[str] = None


# =============================================================================
# APPD CONFIG
# =============================================================================

class AppdConfigRequest(BaseModel):
    lob_name: str
    track: str
    controller_url: str
    account_name: str
    token_env_var: str                          # Env var NAME only
    application_names: Optional[str] = None    # Comma-separated
    tier_filter: Optional[str] = None
    node_filter: Optional[str] = None
    collection_interval: int = 300
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "controller_url": "https://mycompany.saas.appdynamics.com",
                "account_name": "mycompany",
                "token_env_var": "APPD_TOKEN_DT_CDV3",
                "application_names": "DT-API,DT-Web,DT-Payment",
                "tier_filter": "API-GW,Card-Auth,Payment",
                "node_filter": None,
                "collection_interval": 300,
                "created_by": "admin"
            }
        }


class AppdConfigResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[int] = None
    lob_name: Optional[str] = None
    track: Optional[str] = None
    contact_app_team: bool = False  # True when test finds no data


# =============================================================================
# KIBANA CONFIG
# =============================================================================

class KibanaConfigRequest(BaseModel):
    lob_name: str
    track: str
    kibana_url: str
    dashboard_id: Optional[str] = None
    display_name: Optional[str] = None
    index_pattern: Optional[str] = None
    token_env_var: Optional[str] = None
    time_field: str = "@timestamp"
    default_time_range: str = "last_1h"
    custom_filters: Optional[str] = None
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "kibana_url": "https://kibana.mycompany.com",
                "dashboard_id": "abc123-def456",
                "display_name": "DT CDV3 Performance",
                "index_pattern": "logstash-dt-*",
                "token_env_var": "KIBANA_TOKEN_DT_CDV3",
                "time_field": "@timestamp",
                "default_time_range": "last_1h",
                "custom_filters": None,
                "created_by": "admin"
            }
        }


class KibanaConfigResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[int] = None
    lob_name: Optional[str] = None
    track: Optional[str] = None
    contact_app_team: bool = False


# =============================================================================
# SPLUNK CONFIG
# =============================================================================

class SplunkConfigRequest(BaseModel):
    lob_name: str
    track: str
    splunk_url: str
    token_env_var: str
    default_index: Optional[str] = None
    saved_search_name: Optional[str] = None
    spl_query: Optional[str] = None
    search_type: str = "search"               # search or dashboard
    dashboard_name: Optional[str] = None
    time_range: str = "-1h"
    error_patterns: Optional[str] = None     # Comma-sep patterns
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "splunk_url": "https://splunk.mycompany.com:8089",
                "token_env_var": "SPLUNK_TOKEN_DT_CDV3",
                "default_index": "dt_prod_logs",
                "saved_search_name": "DT CDV3 Error Summary",
                "spl_query": "index=dt_prod_logs level=ERROR | stats count by source",
                "search_type": "search",
                "time_range": "-1h",
                "error_patterns": "ORA-,NullPointerException,Connection timeout",
                "created_by": "admin"
            }
        }


class SplunkConfigResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[int] = None
    lob_name: Optional[str] = None
    track: Optional[str] = None
    contact_app_team: bool = False


# =============================================================================
# MONGODB CONFIG
# =============================================================================

class MongoDbConfigRequest(BaseModel):
    lob_name: str
    track: str
    uri_env_var: str                          # Env var NAME for MongoDB URI
    database_name: str
    collection_names: Optional[str] = None   # Comma-separated
    replica_set: Optional[str] = None
    auth_db: str = "admin"
    slow_query_ms: int = 100
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "uri_env_var": "MONGODB_URI_DT_CDV3",
                "database_name": "dt_transactions",
                "collection_names": "payments,cards,limits",
                "replica_set": "rs0",
                "auth_db": "admin",
                "slow_query_ms": 100,
                "created_by": "admin"
            }
        }


class MongoDbConfigResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[int] = None
    lob_name: Optional[str] = None
    track: Optional[str] = None
    contact_app_team: bool = False


# =============================================================================
# PC CONFIG
# =============================================================================

class PcConfigRequest(BaseModel):
    lob_name: str
    track: str
    pc_url: str
    pc_domain: str
    pc_project: str
    username: str
    password_env_var: str                    # Env var NAME for PC password
    duration_format: str = "HM"             # HM or SECONDS
    cookie_flag: str = "-b"                 # PC 24.1 requirement
    default_timeout_min: int = 120
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "pc_url": "https://pc.mycompany.com",
                "pc_domain": "DEFAULT",
                "pc_project": "DT_NFT_CDV3",
                "username": "pc_svc_account",
                "password_env_var": "PC_PASSWORD_DT_CDV3",
                "duration_format": "HM",
                "cookie_flag": "-b",
                "default_timeout_min": 120,
                "created_by": "admin"
            }
        }


class PcConfigResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[int] = None
    lob_name: Optional[str] = None
    track: Optional[str] = None
    contact_app_team: bool = False


# =============================================================================
# DB CONFIG
# =============================================================================

class DbConfigRequest(BaseModel):
    lob_name: str
    track: str
    db_alias: str
    host: str
    port: int = 1521
    service_name: str
    username: str
    password_env_var: str                    # Env var NAME - never plain text
    use_cyberark: bool = False
    cyberark_safe: Optional[str] = None
    cyberark_object: Optional[str] = None
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "db_alias": "DT_PTE",
                "host": "db-server.mycompany.com",
                "port": 1521,
                "service_name": "DTPTE",
                "username": "dt_awr_user",
                "password_env_var": "DB_PASSWORD_DT_CDV3",
                "use_cyberark": False,
                "cyberark_safe": None,
                "cyberark_object": None,
                "created_by": "admin"
            }
        }


class DbConfigResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[int] = None
    lob_name: Optional[str] = None
    track: Optional[str] = None
    contact_app_team: bool = False


# =============================================================================
# TRACK TEMPLATE
# =============================================================================

class TrackTemplateRequest(BaseModel):
    lob_name: str
    track: str
    appd_config_ids: Optional[str] = None   # Comma-separated IDs
    kibana_config_ids: Optional[str] = None
    splunk_config_ids: Optional[str] = None
    mongodb_config_ids: Optional[str] = None
    pc_config_ids: Optional[str] = None
    db_config_ids: Optional[str] = None
    created_by: str

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "appd_config_ids": "1",
                "kibana_config_ids": "1",
                "splunk_config_ids": "1",
                "mongodb_config_ids": "1",
                "pc_config_ids": "1",
                "db_config_ids": "1",
                "created_by": "admin"
            }
        }


class TrackTemplateResponse(BaseModel):
    success: bool
    message: str
    template_id: Optional[int] = None
    lob_name: Optional[str] = None
    track: Optional[str] = None


# =============================================================================
# RELEASE REPORTS
# =============================================================================

class ReleaseReportSaveRequest(BaseModel):
    run_id: str
    lob_name: str
    track: Optional[str] = None
    test_name: Optional[str] = None
    test_type: Optional[str] = None          # LOAD/STRESS/ENDURANCE/SPIKE/SOAK
    pc_run_id: Optional[str] = None
    report_title: Optional[str] = None
    report_html: str                          # Full HTML content
    generated_by: str
    retain_months: Optional[int] = 12        # Months to retain (None = forever)
    notes: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "run_id": "RUN_20260316_001",
                "lob_name": "Digital Technology",
                "track": "CDV3",
                "test_name": "Peak Load Test Q1 2026",
                "test_type": "LOAD",
                "pc_run_id": "12345",
                "report_title": "DT CDV3 NFT Report - March 2026",
                "report_html": "<html>...</html>",
                "generated_by": "john.doe",
                "retain_months": 12,
                "notes": "Q1 baseline test"
            }
        }


class ReleaseReportSaveResponse(BaseModel):
    success: bool
    message: str
    report_id: Optional[int] = None
    report_size_kb: Optional[int] = None


class ReleaseReportListItem(BaseModel):
    report_id: int
    run_id: str
    lob_name: str
    track: Optional[str]
    test_name: Optional[str]
    test_type: Optional[str]
    pc_run_id: Optional[str]
    report_title: Optional[str]
    report_size_kb: Optional[int]
    generated_by: Optional[str]
    generated_date: Optional[str]
    retain_until: Optional[str]


# =============================================================================
# TEST CONNECTION RESPONSES (generic)
# =============================================================================

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    status: str                               # PASS / FAIL / NOT_TESTED
    contact_app_team: bool = False            # True = no data found, contact team
    details: Optional[str] = None
