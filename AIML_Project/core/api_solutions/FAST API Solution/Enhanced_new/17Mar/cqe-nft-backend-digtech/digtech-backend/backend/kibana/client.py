"""
Kibana Monitoring Client
Thin wrapper around fetchers/kibana_fetcher.KibanaDataFetcher.
Follows exact pattern of appd/client.py.
"""
import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class KibanaMonitoringClient:
    """
    Client for Kibana metric collection during NFT monitoring.
    Wraps KibanaDataFetcher using credentials from environment variables.
    """

    def __init__(self, kibana_url: str, username: Optional[str],
                 token_env_var: str, auth_type: str = 'apikey'):
        self.kibana_url = kibana_url.rstrip('/')
        self.username = username
        self.token_env_var = token_env_var
        self.auth_type = auth_type
        self._fetcher = None

    def _get_token(self) -> str:
        """Read API token from environment variable."""
        token = os.environ.get(self.token_env_var)
        if not token:
            raise ValueError(
                f"Environment variable '{self.token_env_var}' is not set or empty. "
                f"Please set it on the server before starting monitoring."
            )
        return token

    def _get_fetcher(self):
        """Lazy-initialize KibanaDataFetcher with credentials from env."""
        if self._fetcher is None:
            # Import here to avoid circular imports
            from fetchers.kibana_fetcher import KibanaDataFetcher
            token = self._get_token()
            # KibanaDataFetcher takes (kibana_url, username, password)
            # For API key auth: username='', password=token
            # For basic auth: username=self.username, password=token
            if self.auth_type == 'basic':
                username = self.username or ''
                password = token
            else:
                username = self.username or ''
                password = token
            self._fetcher = KibanaDataFetcher(self.kibana_url, username, password)
        return self._fetcher

    def test_connection(self) -> Dict:
        """
        Test Kibana connectivity.
        Returns: {success, status, message, kibana_version}
        """
        try:
            fetcher = self._get_fetcher()
            connected = fetcher.test_connection()
            if connected:
                return {
                    'success': True,
                    'status': 'PASS',
                    'message': f'Connected to Kibana at {self.kibana_url}',
                }
            else:
                return {
                    'success': False,
                    'status': 'FAIL',
                    'message': f'Kibana connection failed at {self.kibana_url}',
                    'contact_app_team': False,
                }
        except ValueError as e:
            return {'success': False, 'status': 'FAIL', 'message': str(e), 'contact_app_team': False}
        except Exception as e:
            logger.error(f"Kibana test_connection error: {e}", exc_info=True)
            return {'success': False, 'status': 'FAIL', 'message': str(e), 'contact_app_team': False}

    def collect_dashboard_metrics(self, dashboard_id: str,
                                   time_range_minutes: int = 10) -> Dict:
        """
        Collect metrics from a single Kibana dashboard.

        Uses KibanaDataFetcher.fetch_data_using_dynamic_analysis() which
        returns a list of API endpoint metrics dicts.

        Returns:
            {
              success, dashboard_id, record_count, error_rate, p95_ms,
              last_data_point, metrics: [...], contact_app_team
            }
        """
        try:
            fetcher = self._get_fetcher()
            api_metrics = fetcher.fetch_data_using_dynamic_analysis(
                dashboard_id=dashboard_id,
                time_range_minutes=time_range_minutes
            )

            if not api_metrics:
                return {
                    'success': True,
                    'status': 'FAIL',
                    'message': f'No data found in dashboard {dashboard_id} for the last {time_range_minutes} minutes.',
                    'record_count': 0,
                    'error_rate': 0,
                    'p95_ms': 0,
                    'metrics': [],
                    'contact_app_team': True,
                }

            # Aggregate summary stats across all endpoints
            total_requests = sum(m.get('total_requests', 0) for m in api_metrics)
            total_fail = sum(m.get('fail_count', 0) for m in api_metrics)
            error_rate = round(total_fail / total_requests * 100, 2) if total_requests > 0 else 0
            p95_values = [m.get('p95_response_time', 0) for m in api_metrics if m.get('p95_response_time')]
            p95_ms = round(max(p95_values), 2) if p95_values else 0

            from datetime import datetime
            return {
                'success': True,
                'status': 'PASS',
                'message': f'Collected {len(api_metrics)} API endpoints from dashboard.',
                'record_count': total_requests,
                'error_rate': error_rate,
                'p95_ms': p95_ms,
                'last_data_point': datetime.utcnow().isoformat(),
                'metrics': api_metrics,
                'contact_app_team': False,
            }

        except ValueError as e:
            return {'success': False, 'status': 'FAIL', 'message': str(e),
                    'metrics': [], 'contact_app_team': False}
        except Exception as e:
            logger.error(f"Kibana collect_dashboard_metrics error: {e}", exc_info=True)
            return {'success': False, 'status': 'FAIL', 'message': str(e),
                    'metrics': [], 'contact_app_team': False}
