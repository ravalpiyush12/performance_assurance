"""
NFT Platform Pydantic Models
Pydantic v1.10.x style — matches existing codebase (BaseModel, Field, schema_extra)
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================================
# USER LOB ACCESS
# ============================================================

class UserLobGrantRequest(BaseModel):
    username: str
    lob_names: List[str]    # Grant multiple LOBs at once

    class Config:
        schema_extra = {
            "example": {
                "username": "priya.r",
                "lob_names": ["Digital Technology", "Payments"]
            }
        }


class UserLobRevokeRequest(BaseModel):
    username: str
    lob_name: str

    class Config:
        schema_extra = {
            "example": {"username": "priya.r", "lob_name": "Payments"}
        }


# ============================================================
# APPD CONFIG
# ============================================================

class AppdToolConfigRequest(BaseModel):
    lob_name: str
    controller_url: str
    account_name: str
    token_env_var: str          # e.g. APPD_TOKEN_CARDS — env var name only, not value
    default_node_count: int = 3

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "controller_url": "https://appdynamics.corp.internal:8090",
                "account_name": "corp-prod-account",
                "token_env_var": "APPD_TOKEN_DIGTECH",
                "default_node_count": 3
            }
        }


# ============================================================
# KIBANA CONFIG
# ============================================================

class KibanaConfigRequest(BaseModel):
    lob_name: str
    track_name: str
    kibana_url: str
    username: Optional[str] = None
    token_env_var: str              # e.g. KIBANA_TOKEN_CARDS
    auth_type: str = "apikey"       # apikey | basic
    dashboard_id: str
    display_name: str               # User-defined name e.g. "API Performance — CDV3"
    index_pattern: Optional[str] = None
    time_field: str = "@timestamp"

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track_name": "CDV3",
                "kibana_url": "https://kibana.corp.internal:5601",
                "token_env_var": "KIBANA_TOKEN_DIGTECH",
                "auth_type": "apikey",
                "dashboard_id": "abc12345-def6-7890-ghij-klmnopqrstuv",
                "display_name": "API Performance — CDV3",
                "index_pattern": "cards-prod-*",
                "time_field": "@timestamp"
            }
        }


class KibanaTestConnectionRequest(BaseModel):
    kibana_config_id: int

    class Config:
        schema_extra = {"example": {"kibana_config_id": 1}}


class KibanaTestConnectionResponse(BaseModel):
    success: bool
    kibana_config_id: int
    display_name: str
    status: str                     # PASS | FAIL
    record_count: Optional[int] = None
    error_rate: Optional[float] = None
    p95_ms: Optional[float] = None
    last_data_point: Optional[str] = None
    message: str
    contact_app_team: bool = False  # True when no data found


# ============================================================
# SPLUNK CONFIG
# ============================================================

class SplunkConfigRequest(BaseModel):
    lob_name: str
    track_name: str
    splunk_url: str
    token_env_var: str              # e.g. SPLUNK_TOKEN_CARDS
    default_index: Optional[str] = None
    search_name: str                # Saved search name or dashboard ID
    display_name: str
    search_type: str = "search"     # search | dashboard
    spl_query: Optional[str] = None
    search_timeout_sec: int = 60

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track_name": "CDV3",
                "splunk_url": "https://splunk.corp.internal:8089",
                "token_env_var": "SPLUNK_TOKEN_DIGTECH",
                "default_index": "cards_prod",
                "search_name": "Error_Rate_CDV3",
                "display_name": "Error Rate Analysis — CDV3",
                "search_type": "search",
                "spl_query": "index=cards_prod sourcetype=app_log | stats count by http_status, endpoint | sort -count",
                "search_timeout_sec": 60
            }
        }


class SplunkTestConnectionResponse(BaseModel):
    success: bool
    splunk_config_id: int
    display_name: str
    status: str
    event_count: Optional[int] = None
    error_events: Optional[int] = None
    slow_events: Optional[int] = None
    message: str
    contact_app_team: bool = False


# ============================================================
# MONGODB CONFIG
# ============================================================

class MongoDBConfigRequest(BaseModel):
    lob_name: str
    track_name: str
    uri_env_var: str                # e.g. MONGO_URI_CARDS
    database_name: str
    collection_name: str
    display_name: str
    auth_database: str = "admin"
    username: Optional[str] = None
    pass_env_var: Optional[str] = None   # e.g. MONGO_PASS_CARDS
    replica_set: Optional[str] = None
    slow_query_ms: int = 100
    read_preference: str = "primaryPreferred"
    connection_timeout: int = 5000

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track_name": "CDV3",
                "uri_env_var": "MONGO_URI_DIGTECH",
                "database_name": "cards_db",
                "collection_name": "transactions",
                "display_name": "Transactions — CDV3",
                "auth_database": "admin",
                "pass_env_var": "MONGO_PASS_DIGTECH",
                "replica_set": "rs0",
                "slow_query_ms": 100
            }
        }


class MongoDBTestConnectionResponse(BaseModel):
    success: bool
    mongodb_config_id: int
    display_name: str
    status: str
    document_count: Optional[int] = None
    avg_doc_size_kb: Optional[float] = None
    index_count: Optional[int] = None
    slow_queries: Optional[int] = None
    collscan_count: Optional[int] = None
    message: str
    contact_app_team: bool = False


# ============================================================
# PC CONFIG
# ============================================================

class PCToolConfigRequest(BaseModel):
    lob_name: str
    track_name: str
    pc_url: str
    pc_port: int = 443
    username: str
    pass_env_var: str               # e.g. PC_PASS_CARDS
    domain: str = "DEFAULT"
    project_name: str
    display_name: str
    duration_format: str = "HM"    # HM = Hours/Minutes (PC 24.1)
    cookie_flag: str = "-b"        # Required for PC 24.1 report downloads
    report_timeout_sec: int = 300

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track_name": "CDV3",
                "pc_url": "https://pc.corp.internal",
                "pc_port": 443,
                "username": "pc_svc_account",
                "pass_env_var": "PC_PASS_DIGTECH",
                "domain": "DEFAULT",
                "project_name": "CQE_CARDS_NFT",
                "display_name": "Cards NFT — CDV3",
                "duration_format": "HM",
                "cookie_flag": "-b",
                "report_timeout_sec": 300
            }
        }


class PCTestConnectionResponse(BaseModel):
    success: bool
    pc_config_id: int
    display_name: str
    status: str
    pc_version: Optional[str] = None
    latest_run_id: Optional[str] = None
    latest_run_status: Optional[str] = None
    latest_run_date: Optional[str] = None
    latest_run_duration: Optional[str] = None
    latest_pass_rate: Optional[float] = None
    message: str


# ============================================================
# DB CONFIG
# ============================================================

class DBConfigRequest(BaseModel):
    lob_name: str
    display_name: str               # e.g. CQE_NFT
    db_type: str = "Oracle"
    host: str
    port: int = 1521
    service_name: str
    username: str
    pass_env_var: str               # e.g. DB_PASS_CQE_NFT — never store actual password
    use_cyberark: bool = False
    cyberark_safe: Optional[str] = None
    cyberark_object: Optional[str] = None
    allowed_operations: str = "DQL"   # DQL | DML | DQL,DML

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "display_name": "CQE_NFT",
                "db_type": "Oracle",
                "host": "NAINS1U.oraas.dyn.nsroot.net",
                "port": 8889,
                "service_name": "HANAINS1U",
                "username": "nft_svc_user",
                "pass_env_var": "DB_PASS_CQE_NFT",
                "use_cyberark": False,
                "allowed_operations": "DQL,DML"
            }
        }


class DBTestConnectionResponse(BaseModel):
    success: bool
    db_config_id: int
    display_name: str
    dsn: str
    status: str
    server_time: Optional[str] = None
    connected_as: Optional[str] = None
    message: str


# ============================================================
# TRACK TEMPLATE
# ============================================================

class TrackTemplateRequest(BaseModel):
    lob_name: str
    track_name: str
    appd_app_ids: Optional[str] = None      # Comma-separated APP_MASTER_IDs
    kibana_config_ids: Optional[str] = None  # Comma-separated KIBANA_CONFIG_IDs
    splunk_config_ids: Optional[str] = None
    mongodb_config_ids: Optional[str] = None
    pc_config_ids: Optional[str] = None
    db_config_ids: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "lob_name": "Digital Technology",
                "track_name": "CDV3",
                "appd_app_ids": "1,2,3",
                "kibana_config_ids": "1,2",
                "splunk_config_ids": "1",
                "mongodb_config_ids": "1,2",
                "pc_config_ids": "1",
                "db_config_ids": "1,2"
            }
        }


class TrackTemplateResponse(BaseModel):
    success: bool
    template_id: Optional[int] = None
    lob_name: str
    track_name: str
    appd_app_count: int = 0
    kibana_count: int = 0
    splunk_count: int = 0
    mongodb_count: int = 0
    pc_count: int = 0
    db_count: int = 0
    message: str


# ============================================================
# TEST REGISTRATION
# ============================================================

class TestRegistrationRequest(BaseModel):
    pc_run_id: str
    lob_name: str
    track_name: str
    test_name: str
    test_type: Optional[str] = None     # LOAD|STRESS|ENDURANCE|SPIKE|SOAK
    environment: str = "PERF"
    release_name: Optional[str] = None
    peak_vusers: Optional[int] = None
    ramp_up_minutes: Optional[int] = None
    planned_duration_hrs: Optional[float] = None
    jenkins_build: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "pc_run_id": "65989",
                "lob_name": "Digital Technology",
                "track_name": "CDV3",
                "test_name": "Peak Load Test — Release 2.5",
                "test_type": "LOAD",
                "environment": "PERF",
                "release_name": "Release 2.5",
                "peak_vusers": 2847,
                "ramp_up_minutes": 30,
                "planned_duration_hrs": 2,
                "jenkins_build": "#312"
            }
        }


class TestRegistrationResponse(BaseModel):
    success: bool
    run_id: Optional[str] = None
    pc_run_id: str
    lob_name: str
    track_name: str
    test_name: str
    message: str


# ============================================================
# RELEASE REPORT
# ============================================================

class SaveReportRequest(BaseModel):
    run_id: str
    pc_run_id: str
    lob_name: str
    release_name: str
    test_type: str              # LOAD | STRESS | ENDURANCE
    test_name: Optional[str] = None
    track_name: Optional[str] = None
    report_html: str            # Full HTML of the test report page
    overall_status: Optional[str] = None   # PASS | FAIL | PARTIAL
    pass_rate_pct: Optional[float] = None
    peak_vusers: Optional[int] = None
    avg_response_ms: Optional[float] = None
    p95_response_ms: Optional[float] = None
    total_transactions: Optional[int] = None
    failed_transactions: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "run_id": "RUN_20260315_001",
                "pc_run_id": "65989",
                "lob_name": "Digital Technology",
                "release_name": "Release 2.5",
                "test_type": "LOAD",
                "test_name": "Peak Load Test",
                "overall_status": "PARTIAL",
                "pass_rate_pct": 98.7,
                "peak_vusers": 2847,
                "avg_response_ms": 842,
                "p95_response_ms": 3841,
                "total_transactions": 253110,
                "failed_transactions": 3266,
                "report_html": "<html>...</html>"
            }
        }


class SaveReportResponse(BaseModel):
    success: bool
    report_id: Optional[int] = None
    run_id: str
    release_name: str
    test_type: str
    report_size_kb: Optional[int] = None
    message: str


class ReportListItem(BaseModel):
    report_id: int
    run_id: str
    pc_run_id: str
    lob_name: str
    release_name: str
    test_type: str
    test_name: Optional[str]
    track_name: Optional[str]
    report_size_kb: Optional[int]
    overall_status: Optional[str]
    pass_rate_pct: Optional[float]
    peak_vusers: Optional[int]
    saved_by: str
    saved_date: str
