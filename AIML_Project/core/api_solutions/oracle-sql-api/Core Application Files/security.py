"""
Security and Authentication Module
Handles API key validation, JWT tokens, and rate limiting
"""
from fastapi import Security, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from collections import defaultdict
from threading import Lock
from config import Settings

logger = logging.getLogger(__name__)

# Security schemes
security_bearer = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed based on rate limit
        
        Args:
            identifier: Unique identifier (API key, IP, etc.)
            
        Returns:
            True if allowed, False if rate limited
        """
        with self.lock:
            now = datetime.now()
            period_start = now - timedelta(seconds=self.settings.RATE_LIMIT_PERIOD)
            
            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > period_start
            ]
            
            # Check limit
            if len(self.requests[identifier]) >= self.settings.RATE_LIMIT_REQUESTS:
                logger.warning(f"Rate limit exceeded for {identifier}")
                return False
            
            # Add current request
            self.requests[identifier].append(now)
            return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        with self.lock:
            now = datetime.now()
            period_start = now - timedelta(seconds=self.settings.RATE_LIMIT_PERIOD)
            
            recent_requests = [
                req_time for req_time in self.requests.get(identifier, [])
                if req_time > period_start
            ]
            
            return max(0, self.settings.RATE_LIMIT_REQUESTS - len(recent_requests))


class TokenManager:
    """JWT token management"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token
        
        Args:
            data: Payload data
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            return None


class SecurityManager:
    """Unified security management"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.rate_limiter = RateLimiter(settings)
        self.token_manager = TokenManager(settings)
        self.valid_api_keys = set(settings.get_api_keys())
    
    def verify_api_key(self, api_key: Optional[str]) -> str:
        """
        Verify API key
        
        Args:
            api_key: API key from request
            
        Returns:
            API key if valid
            
        Raises:
            HTTPException: If API key is invalid
        """
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        if api_key not in self.valid_api_keys:
            logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        return api_key
    
    def verify_bearer_token(
        self,
        credentials: HTTPAuthorizationCredentials
    ) -> Dict:
        """
        Verify bearer token
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            Token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        token = credentials.credentials
        payload = self.token_manager.verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    def check_rate_limit(self, identifier: str):
        """
        Check rate limit for identifier
        
        Args:
            identifier: Unique identifier
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self.rate_limiter.is_allowed(identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.settings.RATE_LIMIT_REQUESTS} requests per {self.settings.RATE_LIMIT_PERIOD} seconds",
            )
    
    def get_rate_limit_info(self, identifier: str) -> Dict:
        """Get rate limit information for identifier"""
        return {
            "limit": self.settings.RATE_LIMIT_REQUESTS,
            "period_seconds": self.settings.RATE_LIMIT_PERIOD,
            "remaining": self.rate_limiter.get_remaining(identifier)
        }


# Dependency functions for FastAPI
def get_security_manager() -> SecurityManager:
    """Get security manager instance"""
    from main import app
    return app.state.security_manager


async def verify_api_key_dependency(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """FastAPI dependency for API key verification"""
    from main import app
    security_manager = app.state.security_manager
    
    verified_key = security_manager.verify_api_key(api_key)
    
    # Check rate limit
    security_manager.check_rate_limit(verified_key)
    
    return verified_key


async def verify_token_dependency(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer)
) -> Dict:
    """FastAPI dependency for token verification"""
    from main import app
    security_manager = app.state.security_manager
    return security_manager.verify_bearer_token(credentials)


async def get_request_identifier(request: Request) -> str:
    """Get unique identifier for request (for rate limiting)"""
    # Try API key first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    
    # Fall back to IP address
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"