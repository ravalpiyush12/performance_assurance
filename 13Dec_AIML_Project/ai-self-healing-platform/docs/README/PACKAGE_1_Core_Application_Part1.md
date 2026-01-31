# PACKAGE 1: CORE APPLICATION & CONFIGURATION
## Complete Source Code for Additional Modules

---

## FILE 1: src/monitoring/collector.py

```python
"""
Metrics Collector - Observability Engine
Collects system and application metrics for monitoring
"""

import psutil
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects system and application metrics
    """
    
    def __init__(self, collection_interval: int = 5):
        self.collection_interval = collection_interval
        self.metrics_history = deque(maxlen=1000)
        self.is_collecting = False
        
    def collect_system_metrics(self) -> Dict:
        """Collect system-level metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            
            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available': memory.available / (1024 ** 3),  # GB
                'disk_usage': disk.percent,
                'disk_free': disk.free / (1024 ** 3),  # GB
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def collect_process_metrics(self) -> Dict:
        """Collect process-level metrics"""
        try:
            process = psutil.Process()
            
            with process.oneshot():
                cpu_times = process.cpu_times()
                memory_info = process.memory_info()
                io_counters = process.io_counters() if hasattr(process, 'io_counters') else None
                
                return {
                    'process_cpu_percent': process.cpu_percent(),
                    'process_memory_mb': memory_info.rss / (1024 ** 2),
                    'process_threads': process.num_threads(),
                    'process_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                    'process_cpu_user': cpu_times.user,
                    'process_cpu_system': cpu_times.system,
                    'process_io_read': io_counters.read_bytes if io_counters else 0,
                    'process_io_write': io_counters.write_bytes if io_counters else 0,
                }
        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
            return {}
    
    def collect_all_metrics(self) -> Dict:
        """Collect all metrics"""
        system_metrics = self.collect_system_metrics()
        process_metrics = self.collect_process_metrics()
        
        return {
            **system_metrics,
            **process_metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    async def start_collection(self):
        """Start continuous metrics collection"""
        self.is_collecting = True
        logger.info(f"Starting metrics collection (interval: {self.collection_interval}s)")
        
        while self.is_collecting:
            try:
                metrics = self.collect_all_metrics()
                self.metrics_history.append(metrics)
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        logger.info("Stopped metrics collection")
    
    def get_recent_metrics(self, limit: int = 10) -> List[Dict]:
        """Get recent metrics"""
        return list(self.metrics_history)[-limit:]
    
    def get_metrics_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.metrics_history:
            return {}
        
        recent = list(self.metrics_history)[-20:]
        
        cpu_values = [m.get('cpu_usage', 0) for m in recent]
        memory_values = [m.get('memory_usage', 0) for m in recent]
        
        return {
            'cpu_avg': sum(cpu_values) / len(cpu_values),
            'cpu_max': max(cpu_values),
            'cpu_min': min(cpu_values),
            'memory_avg': sum(memory_values) / len(memory_values),
            'memory_max': max(memory_values),
            'memory_min': min(memory_values),
            'samples_collected': len(self.metrics_history)
        }


class ApplicationMetricsCollector:
    """
    Collects application-specific metrics
    """
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)
        self.anomalies_detected = 0
        self.healing_actions = 0
        
    def record_request(self, response_time: float, is_error: bool = False):
        """Record an API request"""
        self.request_count += 1
        self.response_times.append(response_time)
        
        if is_error:
            self.error_count += 1
    
    def record_anomaly(self):
        """Record an anomaly detection"""
        self.anomalies_detected += 1
    
    def record_healing_action(self):
        """Record a healing action"""
        self.healing_actions += 1
    
    def get_metrics(self) -> Dict:
        """Get application metrics"""
        if not self.response_times:
            avg_response = 0
            p95_response = 0
        else:
            sorted_times = sorted(self.response_times)
            avg_response = sum(self.response_times) / len(self.response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p95_response = sorted_times[p95_index] if sorted_times else 0
        
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate_percent': error_rate,
            'avg_response_time_ms': avg_response,
            'p95_response_time_ms': p95_response,
            'anomalies_detected': self.anomalies_detected,
            'healing_actions_taken': self.healing_actions,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset(self):
        """Reset counters"""
        self.request_count = 0
        self.error_count = 0
        self.response_times.clear()
        self.anomalies_detected = 0
        self.healing_actions = 0


# Example usage
if __name__ == '__main__':
    import asyncio
    
    async def main():
        collector = MetricsCollector(collection_interval=2)
        
        # Start collection
        task = asyncio.create_task(collector.start_collection())
        
        # Let it run for 10 seconds
        await asyncio.sleep(10)
        
        # Stop collection
        collector.stop_collection()
        
        # Show summary
        print("Metrics Summary:")
        print(collector.get_metrics_summary())
        
        # Cancel task
        task.cancel()
    
    asyncio.run(main())
```

---

## FILE 2: src/security/authentication.py

```python
"""
Authentication Module
JWT-based authentication for API endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


# Configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # Store in env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    roles: list = []


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: list = []


class UserInDB(User):
    hashed_password: str


# Mock database - Replace with real database
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
        "roles": ["admin", "user"]
    },
    "user": {
        "username": "user",
        "full_name": "Regular User",
        "email": "user@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
        "roles": ["user"]
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(
            username=username,
            roles=payload.get("roles", [])
        )
        
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user


def require_role(required_role: str):
    """Decorator to require specific role"""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return role_checker


# Example FastAPI usage:
"""
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI()

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.username}"}

@app.get("/admin-only")
async def admin_route(current_user: User = Depends(require_role("admin"))):
    return {"message": "Admin access granted"}
"""
```

---

## FILE 3: src/security/input_validation.py

```python
"""
Input Validation Module
Validates and sanitizes user inputs
"""

import re
from typing import Any, Dict, Optional
from datetime import datetime
import json
import html


class ValidationError(Exception):
    """Custom validation error"""
    pass


class InputValidator:
    """
    Validates and sanitizes user inputs
    """
    
    @staticmethod
    def validate_metric_value(value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Validate metric value is within range"""
        try:
            val = float(value)
            
            if not min_val <= val <= max_val:
                raise ValidationError(
                    f"Value {val} out of range [{min_val}, {max_val}]"
                )
            
            return val
            
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid metric value: {value}")
    
    @staticmethod
    def validate_string(text: str, max_length: int = 1000, allow_empty: bool = False) -> str:
        """Validate and sanitize string input"""
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")
        
        # Check empty
        if not allow_empty and not text.strip():
            raise ValidationError("String cannot be empty")
        
        # Check length
        if len(text) > max_length:
            raise ValidationError(f"String exceeds maximum length of {max_length}")
        
        # Sanitize HTML
        sanitized = html.escape(text)
        
        return sanitized
    
    @staticmethod
    def validate_timestamp(timestamp: str) -> datetime:
        """Validate timestamp format"""
        try:
            # Try ISO format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Check not too far in future
            now = datetime.now()
            if dt > now:
                raise ValidationError("Timestamp cannot be in the future")
            
            return dt
            
        except (ValueError, AttributeError):
            raise ValidationError(f"Invalid timestamp format: {timestamp}")
    
    @staticmethod
    def validate_json(data: str, max_size: int = 10000) -> Dict:
        """Validate JSON string"""
        if not isinstance(data, str):
            raise ValidationError("JSON data must be a string")
        
        if len(data) > max_size:
            raise ValidationError(f"JSON data exceeds maximum size of {max_size} bytes")
        
        try:
            parsed = json.loads(data)
            
            if not isinstance(parsed, dict):
                raise ValidationError("JSON must be an object")
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {str(e)}")
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Sanitize input to prevent SQL injection"""
        # Remove common SQL injection patterns
        dangerous_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(--|;|\/\*|\*\/|@@|@)",
            r"(\bOR\b.*=.*)",
            r"(\bAND\b.*=.*)",
            r"('|\")",
        ]
        
        sanitized = text
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_metrics_dict(metrics: Dict) -> Dict:
        """Validate complete metrics dictionary"""
        required_fields = [
            'cpu_usage', 'memory_usage', 'response_time',
            'error_rate', 'requests_per_sec'
        ]
        
        validated = {}
        
        # Check required fields
        for field in required_fields:
            if field not in metrics:
                raise ValidationError(f"Missing required field: {field}")
            
            # Validate based on field type
            if field in ['cpu_usage', 'memory_usage', 'error_rate']:
                validated[field] = InputValidator.validate_metric_value(
                    metrics[field], 0, 100
                )
            elif field == 'response_time':
                validated[field] = InputValidator.validate_metric_value(
                    metrics[field], 0, 10000  # Max 10 seconds
                )
            elif field == 'requests_per_sec':
                validated[field] = InputValidator.validate_metric_value(
                    metrics[field], 0, 10000  # Max 10k requests/sec
                )
        
        # Validate timestamp if present
        if 'timestamp' in metrics:
            InputValidator.validate_timestamp(metrics['timestamp'])
            validated['timestamp'] = metrics['timestamp']
        
        return validated
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return email.lower()
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate username"""
        if not 3 <= len(username) <= 30:
            raise ValidationError("Username must be 3-30 characters")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError(
                "Username can only contain letters, numbers, hyphens, and underscores"
            )
        
        return username


# Example usage
if __name__ == '__main__':
    validator = InputValidator()
    
    # Test metric validation
    try:
        cpu = validator.validate_metric_value(85.5)
        print(f"✓ Valid CPU: {cpu}")
    except ValidationError as e:
        print(f"✗ Error: {e}")
    
    # Test string validation
    try:
        text = validator.validate_string("Hello, World!")
        print(f"✓ Valid string: {text}")
    except ValidationError as e:
        print(f"✗ Error: {e}")
    
    # Test metrics dict
    try:
        metrics = {
            'cpu_usage': 75.0,
            'memory_usage': 60.0,
            'response_time': 250.0,
            'error_rate': 2.5,
            'requests_per_sec': 120.0,
            'timestamp': datetime.now().isoformat()
        }
        
        validated = validator.validate_metrics_dict(metrics)
        print("✓ Valid metrics dictionary")
        
    except ValidationError as e:
        print(f"✗ Error: {e}")
```

---

*This is Package 1 Part 1. Continuing with optimization modules and configuration files...*
