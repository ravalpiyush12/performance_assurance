"""
Security Manager - Multi-Database Support
Each database has its own SECRET_KEY and API_KEYS
"""
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
from passlib.context import CryptContext


class SecurityManager:
    """Manages authentication and authorization for a specific database"""
    
    def __init__(self, db_config):
        """
        Initialize security manager for a database
        
        Args:
            db_config: DatabaseConfig object with secret_key and api_keys
        """
        self.db_config = db_config
        self.secret_key = db_config.secret_key
        self.algorithm = "HS256"
        self.api_keys = db_config.get_api_keys_list()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify if API key is valid for this database
        
        Args:
            api_key: API key to verify
            
        Returns:
            True if valid, False otherwise
        """
        return api_key in self.api_keys
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "database": self.db_config.name
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token data if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)