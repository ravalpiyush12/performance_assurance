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