"""
CyberArk Credential Provider Module
Handles secure credential retrieval from CyberArk
"""
import requests
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from config import Settings

logger = logging.getLogger(__name__)


@dataclass
class OracleCredentials:
    """Oracle database credentials"""
    username: str
    password: str
    host: str
    port: int
    service_name: str
    
    def get_dsn(self) -> str:
        """Build DSN string"""
        return f"{self.host}:{self.port}/{self.service_name}"


class CyberArkProvider:
    """CyberArk AIM API Integration"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = None
        
    def _get_session(self) -> requests.Session:
        """Create authenticated session with certificate"""
        if self.session is None:
            self.session = requests.Session()
            
            # Configure client certificate if provided
            if self.settings.CYBERARK_CERT_PATH:
                if self.settings.CYBERARK_CERT_KEY_PATH:
                    self.session.cert = (
                        self.settings.CYBERARK_CERT_PATH,
                        self.settings.CYBERARK_CERT_KEY_PATH
                    )
                else:
                    self.session.cert = self.settings.CYBERARK_CERT_PATH
        
        return self.session
    
    def get_credentials(self) -> OracleCredentials:
        """
        Retrieve Oracle credentials from CyberArk
        
        Returns:
            OracleCredentials object with connection details
            
        Raises:
            Exception: If credential retrieval fails
        """
        if not self.settings.CYBERARK_ENABLED:
            raise ValueError("CyberArk is not enabled")
        
        try:
            logger.info(f"Retrieving credentials from CyberArk for {self.settings.CYBERARK_OBJECT}")
            
            # Build CyberArk AIM API URL
            url = f"{self.settings.CYBERARK_URL}/AIMWebService/api/Accounts"
            
            # Request parameters
            params = {
                "AppID": self.settings.CYBERARK_APP_ID,
                "Safe": self.settings.CYBERARK_SAFE,
                "Object": self.settings.CYBERARK_OBJECT,
            }
            
            # Make request with certificate authentication
            session = self._get_session()
            response = session.get(url, params=params, timeout=30, verify=True)
            
            if response.status_code != 200:
                logger.error(f"CyberArk API returned status {response.status_code}: {response.text}")
                raise Exception(f"Failed to retrieve credentials: {response.status_code}")
            
            # Parse response
            data = response.json()
            
            # Extract credentials (adjust based on your CyberArk response structure)
            username = data.get("UserName") or data.get("Content")
            password = data.get("Content") or data.get("Password")
            
            # Extract connection details from address or properties
            address = data.get("Address", "")
            properties = data.get("Properties", {})
            
            # Parse host, port, service name
            # Format expected: hostname:port/service_name or from properties
            host = properties.get("host") or address.split(":")[0] if ":" in address else address
            port = int(properties.get("port", self.settings.ORACLE_PORT))
            service_name = properties.get("service_name") or self.settings.ORACLE_SERVICE_NAME
            
            logger.info("Successfully retrieved credentials from CyberArk")
            
            return OracleCredentials(
                username=username,
                password=password,
                host=host,
                port=port,
                service_name=service_name
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error retrieving CyberArk credentials: {e}")
            raise Exception(f"CyberArk connection failed: {e}")
        except Exception as e:
            logger.error(f"Error retrieving CyberArk credentials: {e}")
            raise
    
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
            self.session = None


class CredentialManager:
    """Unified credential management for local and CyberArk"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cyberark_provider = CyberArkProvider(settings) if settings.CYBERARK_ENABLED else None
    
    def get_oracle_credentials(self) -> OracleCredentials:
        """
        Get Oracle credentials based on environment
        
        Returns:
            OracleCredentials for database connection
        """
        # Production: Use CyberArk
        if self.settings.CYBERARK_ENABLED:
            logger.info("Retrieving Oracle credentials from CyberArk")
            return self.cyberark_provider.get_credentials()
        
        # Local/Dev: Use environment variables
        logger.info("Using local Oracle credentials from environment")
        
        if not all([
            self.settings.ORACLE_USERNAME,
            self.settings.ORACLE_PASSWORD,
            self.settings.ORACLE_HOST,
            self.settings.ORACLE_SERVICE_NAME
        ]):
            raise ValueError("Oracle credentials not configured in environment")
        
        return OracleCredentials(
            username=self.settings.ORACLE_USERNAME,
            password=self.settings.ORACLE_PASSWORD,
            host=self.settings.ORACLE_HOST,
            port=self.settings.ORACLE_PORT,
            service_name=self.settings.ORACLE_SERVICE_NAME
        )
    
    def close(self):
        """Cleanup resources"""
        if self.cyberark_provider:
            self.cyberark_provider.close()