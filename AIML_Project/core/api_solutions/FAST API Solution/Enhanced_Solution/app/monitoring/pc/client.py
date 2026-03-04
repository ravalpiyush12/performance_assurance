"""
Performance Center REST API Client
Handles authentication and communication with PC
"""
import requests
import base64
from typing import Dict, Optional
import logging
import xml.etree.ElementTree as ET

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
        """
        Initialize PC client
        
        Args:
            base_url: PC server URL (e.g., http://pc-server.company.com:8080)
            username: PC username
            password: PC password
            domain: PC domain
            project: PC project name
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.domain = domain
        self.project = project
        self.session = requests.Session()
        self.auth_token = None
        
        logger.info(f"PC Client initialized for {domain}/{project}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Performance Center
        
        Returns:
            bool: True if authentication successful
        """
        try:
            # Create Basic Auth header
            credentials = f"{self.username}:{self.password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            # Authenticate
            url = f"{self.base_url}/rest/site-session"
            
            logger.info(f"Authenticating to PC: {url}")
            
            response = self.session.post(url, headers=headers, timeout=30)
            
            if response.status_code == 201 or response.status_code == 200:
                logger.info("✓ Successfully authenticated with Performance Center")
                
                # Store session cookies
                logger.debug(f"Session cookies: {self.session.cookies}")
                
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise Exception(
                    f"Authentication failed with status {response.status_code}: {response.text}"
                )
                
        except requests.exceptions.Timeout:
            logger.error("Authentication timeout - PC server not responding")
            raise Exception("PC server timeout - please check PC URL and network connectivity")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise Exception(f"Cannot connect to PC server: {self.base_url}")
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            raise
    
    def get_test_run_status(self, run_id: str) -> Dict:
        """
        Get test run status from Performance Center
        
        Args:
            run_id: PC run ID
            
        Returns:
            dict with 'status', 'collation_status', 'start_time', 'end_time'
        """
        try:
            url = (
                f"{self.base_url}/rest/domains/{self.domain}/"
                f"projects/{self.project}/runs/{run_id}"
            )
            
            logger.info(f"Getting test status: {url}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                # Parse XML response
                root = ET.fromstring(response.text)
                
                # Extract status fields (adjust based on actual PC XML structure)
                status_elem = root.find('.//{http://www.hp.com/PC/REST/API}State')
                collation_elem = root.find('.//{http://www.hp.com/PC/REST/API}PostRunAction')
                
                # Alternative paths if namespace not found
                if status_elem is None:
                    status_elem = root.find('.//State')
                if collation_elem is None:
                    collation_elem = root.find('.//PostRunAction')
                
                test_status = status_elem.text if status_elem is not None else 'Unknown'
                
                # Map collation status
                if collation_elem is not None:
                    post_run = collation_elem.text
                    if 'Collate' in post_run or post_run == 'CollateAndAnalyze':
                        collation_status = 'Collated'
                    elif post_run == 'DoNotCollate':
                        collation_status = 'Not Collated'
                    else:
                        collation_status = post_run
                else:
                    collation_status = 'Unknown'
                
                logger.info(f"Test status: {test_status}, Collation: {collation_status}")
                
                return {
                    'status': test_status,
                    'collation_status': collation_status,
                    'run_id': run_id
                }
            elif response.status_code == 404:
                raise Exception(f"Test run {run_id} not found in PC")
            else:
                raise Exception(
                    f"Failed to get run status: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            logger.error(f"Error getting test status: {e}")
            raise
    
    def download_summary_report(self, run_id: str) -> str:
        """
        Download summary.html report from Performance Center
        
        Args:
            run_id: PC run ID
            
        Returns:
            HTML content as string
        """
        try:
            # Try different possible paths for summary report
            possible_paths = [
                f"/rest/domains/{self.domain}/projects/{self.project}/runs/{run_id}/results/summary.html",
                f"/rest/domains/{self.domain}/projects/{self.project}/runs/{run_id}/Results/summary.html",
                f"/rest/domains/{self.domain}/projects/{self.project}/runs/{run_id}/report/summary.html"
            ]
            
            for path in possible_paths:
                url = f"{self.base_url}{path}"
                logger.info(f"Attempting to download: {url}")
                
                response = self.session.get(url, timeout=60)
                
                if response.status_code == 200:
                    logger.info(f"✓ Downloaded summary.html ({len(response.text)} bytes)")
                    return response.text
            
            # If all paths failed
            raise Exception(
                f"Could not download summary.html for run {run_id}. "
                f"Tried {len(possible_paths)} different paths. "
                f"Last status: {response.status_code}"
            )
                
        except Exception as e:
            logger.error(f"Error downloading summary report: {e}")
            raise
    
    def logout(self):
        """Logout from Performance Center"""
        try:
            url = f"{self.base_url}/rest/site-session"
            self.session.delete(url, timeout=10)
            logger.info("Logged out from Performance Center")
        except Exception as e:
            logger.warning(f"Logout error (non-critical): {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.authenticate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.logout()
