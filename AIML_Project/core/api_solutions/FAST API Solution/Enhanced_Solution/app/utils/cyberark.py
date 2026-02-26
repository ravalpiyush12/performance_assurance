"""
CyberArk Integration Client
"""
import requests
from typing import Dict, Optional


class CyberArkClient:
    """Client for CyberArk AIM (Application Identity Manager)"""
    
    def __init__(
        self,
        url: str,
        app_id: str,
        cert_path: Optional[str] = None,
        cert_key_path: Optional[str] = None
    ):
        """
        Initialize CyberArk client
        
        Args:
            url: CyberArk AIM URL
            app_id: Application ID
            cert_path: Path to client certificate
            cert_key_path: Path to client certificate key
        """
        self.url = url
        self.app_id = app_id
        self.cert = None
        
        if cert_path and cert_key_path:
            self.cert = (cert_path, cert_key_path)
    
    def get_password(self, safe: str, object_name: str) -> Dict:
        """
        Retrieve password from CyberArk
        
        Args:
            safe: Safe name
            object_name: Object name (account)
            
        Returns:
            Dict with credential information
        """
        params = {
            "AppID": self.app_id,
            "Safe": safe,
            "Object": object_name
        }
        
        try:
            response = requests.get(
                self.url,
                params=params,
                cert=self.cert,
                verify=True,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"CyberArk request failed: {str(e)}")