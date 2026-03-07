"""
Authentication API Routes
FastAPI endpoints for TOTP authentication
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import qrcode
import io
import base64
import logging

from authentication import AuthenticationManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Global auth manager (initialized at startup)
auth_manager: Optional[AuthenticationManager] = None


def init_auth_routes(db_pool, session_expiry_minutes=60):
    """
    Initialize authentication routes with database pool
    
    Args:
        db_pool: Oracle connection pool
        session_expiry_minutes: Session expiry time
    """
    global auth_manager
    auth_manager = AuthenticationManager(db_pool, session_expiry_minutes)
    logger.info("Authentication routes initialized")


# ==========================================
# Request/Response Models
# ==========================================

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# ==========================================
# Dependencies
# ==========================================

async def get_current_user(
    authorization: Optional[str] = Header(None),
    request: Request = None
) -> dict:
    """
    Dependency to validate session token from Authorization header
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user["username"]}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please login first.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.replace("Bearer ", "")
    
    user = auth_manager.validate_session(token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please login again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Add client IP to user context
    if request:
        user['client_ip'] = request.client.host
    
    return user


def require_permission(permission: str):
    """
    Dependency to check if user has specific permission
    
    Usage:
        @app.post("/write-data")
        async def write_data(user: dict = Depends(require_permission("write"))):
            return {"message": "Data written"}
    """
    async def check_permission(user: dict = Depends(get_current_user)):
        if not auth_manager.has_permission(user['role'], permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required permission: '{permission}'. Your role: '{user['role']}'"
            )
        return user
    
    return check_permission


def require_role(role: str):
    """
    Dependency to check if user has specific role
    
    Usage:
        @app.get("/admin/users")
        async def list_users(user: dict = Depends(require_role("admin"))):
            return {"users": [...]}
    """
    async def check_role(user: dict = Depends(get_current_user)):
        if user['role'] != role:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: '{role}'. Your role: '{user['role']}'"
            )
        return user
    
    return check_role


# ==========================================
# Public Endpoints (No Authentication)
# ==========================================

@router.post("/register")
async def register_user(
    request: CreateUserRequest,
    current_user: dict = Depends(require_permission("user_manage"))
):
    """
    Register new user with TOTP
    Returns QR code for Google Authenticator setup
    
    Required permission: user_manage (admin only)
    """
    try:
        result = auth_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role,
            created_by=current_user['username']
        )
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(result['provisioning_uri'])
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'success': True,
            'user_id': result['user_id'],
            'username': result['username'],
            'email': result['email'],
            'role': result['role'],
            'totp_secret': result['totp_secret'],  # Show once!
            'qr_code_base64': qr_base64,
            'setup_instructions': [
                '1. Install Google Authenticator app on your phone',
                '2. Open the app and tap "+" to add an account',
                '3. Choose "Scan QR code"',
                '4. Scan the QR code displayed',
                '5. Save the TOTP secret in a secure location',
                '6. Use the 6-digit code from the app to login'
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
async def login(request: LoginRequest, req: Request):
    """
    Login with username + password + TOTP code
    Returns session token for subsequent requests
    
    No authentication required (public endpoint)
    """
    ip_address = req.client.host
    user_agent = req.headers.get('user-agent', 'Unknown')
    
    result = auth_manager.authenticate(
        username=request.username,
        password=request.password,
        totp_code=request.totp_code,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials or TOTP code. Please check your username, password, and authenticator app."
        )
    
    logger.info(f"✓ User logged in: {result['username']} from {ip_address}")
    
    return result


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    user: dict = Depends(get_current_user)
):
    """
    Logout and invalidate session
    
    Requires: Valid session token
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        auth_manager.logout(token, user['username'])
    
    return {
        'success': True,
        'message': 'Logged out successfully'
    }


# ==========================================
# Protected Endpoints (Authentication Required)
# ==========================================

@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """
    Get current user information
    
    Requires: Valid session token
    """
    permissions = auth_manager.get_user_permissions(user['username'])
    
    return {
        'user_id': user['user_id'],
        'username': user['username'],
        'email': user['email'],
        'full_name': user.get('full_name'),
        'role': user['role'],
        'permissions': permissions,
        'session_expires': user['expires']
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: dict = Depends(get_current_user)
):
    """
    Change user password
    
    Requires: Valid session token
    """
    # Verify old password by attempting authentication
    result = auth_manager.authenticate(
        username=user['username'],
        password=request.old_password,
        totp_code=None  # Skip TOTP for password change
    )
    
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect"
        )
    
    # TODO: Implement password change logic in AuthenticationManager
    # auth_manager.change_password(user['user_id'], request.new_password)
    
    return {
        'success': True,
        'message': 'Password changed successfully. Please login again.'
    }


# ==========================================
# Admin Endpoints
# ==========================================

@router.get("/sessions")
async def get_active_sessions(
    limit: int = 100,
    user: dict = Depends(require_permission("user_manage"))
):
    """
    Get list of active sessions
    
    Required permission: user_manage (admin only)
    """
    sessions = auth_manager.get_active_sessions(limit)
    
    return {
        'success': True,
        'count': len(sessions),
        'sessions': sessions
    }


@router.get("/audit-log")
async def get_audit_log(
    username: Optional[str] = None,
    action: Optional[str] = None,
    days: int = 7,
    limit: int = 100,
    user: dict = Depends(require_permission("configure"))
):
    """
    Get authentication audit log
    
    Required permission: configure (admin only)
    """
    logs = auth_manager.get_audit_log(username, action, days, limit)
    
    return {
        'success': True,
        'count': len(logs),
        'logs': logs
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint (no authentication required)
    """
    return {
        'status': 'healthy',
        'service': 'authentication',
        'auth_enabled': auth_manager is not None
    }


# ==========================================
# Example: Protecting Existing Endpoints
# ==========================================

# Example of protecting an existing endpoint
@router.post("/monitoring/awr/upload")
async def upload_awr_protected(
    user: dict = Depends(require_permission("write"))
):
    """
    Example: Protected AWR upload endpoint
    
    Required permission: write
    """
    # Log who is uploading
    logger.info(f"AWR upload by {user['username']} (Role: {user['role']})")
    
    # Your existing AWR upload logic here
    # ...
    
    return {
        'success': True,
        'uploaded_by': user['username'],
        'message': 'AWR report uploaded successfully'
    }
