"""Kibana monitoring configuration."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class KibanaConfig:
    kibana_url: str
    token_env_var: str
    username: Optional[str] = None
    auth_type: str = 'apikey'
    default_time_range_minutes: int = 10
    verify_ssl: bool = False
    timeout_seconds: int = 30
