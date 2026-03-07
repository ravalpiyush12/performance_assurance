"""
TOTP Authentication Manager
Complete implementation with TOTP, password hashing, session management
"""
import pyotp
import bcrypt
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import cx_Oracle
import logging

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """
    Manages user authentication with TOTP (Time-Based One-Time Password)
    
    Features:
    - User registration with TOTP secret generation
    - Password hashing with bcrypt
    - Two-factor authentication (password + TOTP)
    - Session management with expiry
    - Account lockout after failed attempts
    - Full audit logging
    - Role-based access control
    """
    
    def __init__(self, db_pool, session_expiry_minutes=60):
        """
        Initialize authentication manager
        
        Args:
            db_pool: Oracle connection pool
            session_expiry_minutes: Session expiry time (default: 60 minutes)
        """
        self.pool = db_pool
        self.session_expiry_minutes = session_expiry_minutes
        logger.info("AuthenticationManager initialized")
    
    # ==========================================
    # User Management
    # ==========================================
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        role: str = "viewer",
        created_by: str = "admin"
    ) -> Dict:
        """
        Create new user with TOTP secret
        
        Args:
            username: Unique username
            email: User email
            password: Plain text password (will be hashed)
            full_name: User's full name
            role: User role (admin, performance_engineer, test_lead, viewer)
            created_by: Who created this user
            
        Returns:
            Dict with user info and TOTP setup instructions
        """
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            # Hash password with bcrypt
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Generate TOTP secret (Base32 encoded)
            totp_secret = pyotp.random_base32()
            
            # Insert user
            cursor.execute("""
                INSERT INTO AUTH_USERS (
                    USER_ID, USERNAME, EMAIL, FULL_NAME,
                    PASSWORD_HASH, TOTP_SECRET, ROLE,
                    IS_ACTIVE, MFA_ENABLED, CREATED_BY
                ) VALUES (
                    AUTH_USER_SEQ.NEXTVAL, :username, :email, :full_name,
                    :password_hash, :totp_secret, :role,
                    'Y', 'Y', :created_by
                ) RETURNING USER_ID INTO :user_id
            """, {
                'username': username,
                'email': email,
                'full_name': full_name,
                'password_hash': password_hash,
                'totp_secret': totp_secret,
                'role': role,
                'created_by': created_by,
                'user_id': cursor.var(cx_Oracle.NUMBER)
            })
            
            user_id = int(cursor.getvalue()[0])
            conn.commit()
            
            # Generate provisioning URI for QR code
            totp = pyotp.TOTP(totp_secret)
            provisioning_uri = totp.provisioning_uri(
                name=email,
                issuer_name="Monitoring System"
            )
            
            logger.info(f"✓ Created user: {username} (ID: {user_id})")
            
            # Log audit
            self._log_audit(username, user_id, 'USER_CREATED', None, 'Y', None, None)
            
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'totp_secret': totp_secret,  # Show once for user to save
                'provisioning_uri': provisioning_uri,
                'message': 'User created. Scan QR code with Google Authenticator app.'
            }
            
        except cx_Oracle.IntegrityError as e:
            conn.rollback()
            error_msg = str(e)
            if 'unique constraint' in error_msg.lower():
                raise ValueError(f"Username '{username}' already exists")
            raise ValueError(f"Database error: {error_msg}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # Authentication
    # ==========================================
    
    def authenticate(
        self,
        username: str,
        password: str,
        totp_code: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Optional[Dict]:
        """
        Authenticate user with password and optional TOTP
        
        Args:
            username: Username
            password: Plain text password
            totp_code: 6-digit TOTP code (required if MFA enabled)
            ip_address: Client IP address
            user_agent: Browser user agent
            
        Returns:
            Dict with session info if successful, None if failed
        """
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            # Get user
            cursor.execute("""
                SELECT 
                    USER_ID, USERNAME, EMAIL, FULL_NAME,
                    PASSWORD_HASH, TOTP_SECRET, ROLE,
                    IS_ACTIVE, MFA_ENABLED, FAILED_ATTEMPTS,
                    LOCKED_UNTIL
                FROM AUTH_USERS
                WHERE USERNAME = :username
            """, {'username': username})
            
            user = cursor.fetchone()
            
            if not user:
                self._log_audit(username, None, 'FAILED_LOGIN', None, 'N', 'User not found', ip_address)
                logger.warning(f"Login failed: User not found - {username}")
                return None
            
            (user_id, username, email, full_name, password_hash, 
             totp_secret, role, is_active, mfa_enabled, 
             failed_attempts, locked_until) = user
            
            # Check if account is active
            if is_active != 'Y':
                self._log_audit(username, user_id, 'FAILED_LOGIN', None, 'N', 'Account disabled', ip_address)
                logger.warning(f"Login failed: Account disabled - {username}")
                return None
            
            # Check if account is locked
            if locked_until and locked_until > datetime.now():
                remaining = (locked_until - datetime.now()).total_seconds() / 60
                self._log_audit(username, user_id, 'FAILED_LOGIN', None, 'N', f'Account locked for {int(remaining)} min', ip_address)
                logger.warning(f"Login failed: Account locked - {username}")
                return None
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                self._handle_failed_login(user_id, username, ip_address)
                logger.warning(f"Login failed: Invalid password - {username}")
                return None
            
            # Verify TOTP (if MFA enabled)
            if mfa_enabled == 'Y':
                if not totp_code:
                    self._log_audit(username, user_id, 'FAILED_LOGIN', None, 'N', 'TOTP code required', ip_address)
                    logger.warning(f"Login failed: TOTP code required - {username}")
                    return None
                
                totp = pyotp.TOTP(totp_secret)
                # valid_window=1 allows 30 seconds clock skew
                if not totp.verify(totp_code, valid_window=1):
                    self._handle_failed_login(user_id, username, ip_address)
                    logger.warning(f"Login failed: Invalid TOTP - {username}")
                    return None
            
            # Authentication successful - create session
            session_token = secrets.token_urlsafe(32)
            expires = datetime.now() + timedelta(minutes=self.session_expiry_minutes)
            
            cursor.execute("""
                INSERT INTO AUTH_SESSIONS (
                    SESSION_ID, USER_ID, USERNAME, ROLE,
                    IP_ADDRESS, USER_AGENT, EXPIRES_DATE
                ) VALUES (
                    :session_id, :user_id, :username, :role,
                    :ip, :agent, :expires
                )
            """, {
                'session_id': session_token,
                'user_id': user_id,
                'username': username,
                'role': role,
                'ip': ip_address,
                'agent': user_agent,
                'expires': expires
            })
            
            # Reset failed attempts and update last login
            cursor.execute("""
                UPDATE AUTH_USERS
                SET FAILED_ATTEMPTS = 0,
                    LOCKED_UNTIL = NULL,
                    LAST_LOGIN = SYSDATE,
                    UPDATED_DATE = SYSDATE
                WHERE USER_ID = :user_id
            """, {'user_id': user_id})
            
            conn.commit()
            
            # Log successful login
            self._log_audit(username, user_id, 'LOGIN', None, 'Y', None, ip_address, user_agent)
            
            logger.info(f"✓ User authenticated: {username} (Role: {role}, IP: {ip_address})")
            
            return {
                'success': True,
                'session_token': session_token,
                'user_id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'role': role,
                'expires': expires.isoformat(),
                'expires_in_minutes': self.session_expiry_minutes
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Authentication error: {e}", exc_info=True)
            return None
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # Session Management
    # ==========================================
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """
        Validate session token and return user info
        
        Args:
            session_token: Session token from login
            
        Returns:
            Dict with user info if valid, None if invalid/expired
        """
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    s.USER_ID, s.USERNAME, s.ROLE, s.EXPIRES_DATE,
                    u.EMAIL, u.FULL_NAME, u.IS_ACTIVE
                FROM AUTH_SESSIONS s
                JOIN AUTH_USERS u ON s.USER_ID = u.USER_ID
                WHERE s.SESSION_ID = :session_id
            """, {'session_id': session_token})
            
            session = cursor.fetchone()
            
            if not session:
                return None
            
            user_id, username, role, expires, email, full_name, is_active = session
            
            # Check if session expired
            if expires < datetime.now():
                # Delete expired session
                cursor.execute(
                    "DELETE FROM AUTH_SESSIONS WHERE SESSION_ID = :sid",
                    {'sid': session_token}
                )
                conn.commit()
                logger.debug(f"Session expired: {username}")
                return None
            
            # Check if user is still active
            if is_active != 'Y':
                logger.warning(f"Session invalid: User disabled - {username}")
                return None
            
            # Update last activity
            cursor.execute("""
                UPDATE AUTH_SESSIONS
                SET LAST_ACTIVITY = SYSDATE
                WHERE SESSION_ID = :sid
            """, {'sid': session_token})
            conn.commit()
            
            return {
                'user_id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'role': role,
                'session_token': session_token,
                'expires': expires.isoformat()
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def logout(self, session_token: str, username: str = None):
        """
        Logout user and invalidate session
        
        Args:
            session_token: Session token to invalidate
            username: Optional username for logging
        """
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            # Get user info before deleting
            if not username:
                cursor.execute(
                    "SELECT USERNAME, USER_ID FROM AUTH_SESSIONS WHERE SESSION_ID = :sid",
                    {'sid': session_token}
                )
                result = cursor.fetchone()
                if result:
                    username, user_id = result
                else:
                    user_id = None
            
            # Delete session
            cursor.execute(
                "DELETE FROM AUTH_SESSIONS WHERE SESSION_ID = :sid",
                {'sid': session_token}
            )
            conn.commit()
            
            if username:
                self._log_audit(username, user_id, 'LOGOUT', None, 'Y', None, None)
                logger.info(f"✓ User logged out: {username}")
            
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # Permission Checking
    # ==========================================
    
    def has_permission(self, role: str, permission: str) -> bool:
        """
        Check if role has specific permission
        
        Args:
            role: User role
            permission: Permission to check (e.g., 'write', 'delete')
            
        Returns:
            True if role has permission, False otherwise
        """
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT PERMISSIONS
                FROM AUTH_ROLES
                WHERE ROLE_NAME = :role
            """, {'role': role})
            
            result = cursor.fetchone()
            
            if not result:
                return False
            
            permissions = json.loads(result[0])
            
            return permission in permissions
            
        finally:
            cursor.close()
            conn.close()
    
    def get_user_permissions(self, username: str) -> List[str]:
        """Get list of permissions for user"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT r.PERMISSIONS
                FROM AUTH_USERS u
                JOIN AUTH_ROLES r ON u.ROLE = r.ROLE_NAME
                WHERE u.USERNAME = :username
            """, {'username': username})
            
            result = cursor.fetchone()
            
            if not result:
                return []
            
            return json.loads(result[0])
            
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    def _handle_failed_login(self, user_id: int, username: str, ip: str):
        """Handle failed login - increment counter and lock if needed"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE AUTH_USERS
                SET FAILED_ATTEMPTS = FAILED_ATTEMPTS + 1,
                    LOCKED_UNTIL = CASE 
                        WHEN FAILED_ATTEMPTS + 1 >= 5 
                        THEN SYSDATE + INTERVAL '30' MINUTE 
                        ELSE NULL 
                    END,
                    UPDATED_DATE = SYSDATE
                WHERE USER_ID = :user_id
            """, {'user_id': user_id})
            
            conn.commit()
            
            # Check if account was locked
            cursor.execute(
                "SELECT FAILED_ATTEMPTS, LOCKED_UNTIL FROM AUTH_USERS WHERE USER_ID = :uid",
                {'uid': user_id}
            )
            failed, locked = cursor.fetchone()
            
            reason = f'Invalid credentials (Attempt {failed}/5)'
            if locked:
                reason = f'Account locked for 30 minutes (5 failed attempts)'
            
            self._log_audit(username, user_id, 'FAILED_LOGIN', None, 'N', reason, ip)
            
        finally:
            cursor.close()
            conn.close()
    
    def _log_audit(
        self,
        username: str,
        user_id: int,
        action: str,
        resource: str = None,
        success: str = 'Y',
        failure_reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log audit event"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO AUTH_AUDIT_LOG (
                    AUDIT_ID, USERNAME, USER_ID, ACTION, RESOURCE,
                    SUCCESS, FAILURE_REASON, IP_ADDRESS, USER_AGENT
                ) VALUES (
                    AUTH_AUDIT_SEQ.NEXTVAL, :username, :user_id, :action, :resource,
                    :success, :reason, :ip, :agent
                )
            """, {
                'username': username,
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'success': success,
                'reason': failure_reason,
                'ip': ip_address,
                'agent': user_agent
            })
            
            conn.commit()
            
        except Exception as e:
            # Don't fail main operation if audit logging fails
            logger.error(f"Audit logging failed: {e}")
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # Admin Functions
    # ==========================================
    
    def get_active_sessions(self, limit: int = 100) -> List[Dict]:
        """Get list of active sessions"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM (
                    SELECT 
                        SESSION_ID, USERNAME, ROLE, IP_ADDRESS,
                        CREATED_DATE, EXPIRES_DATE, LAST_ACTIVITY
                    FROM AUTH_SESSIONS
                    WHERE EXPIRES_DATE > SYSDATE
                    ORDER BY CREATED_DATE DESC
                ) WHERE ROWNUM <= :limit
            """, {'limit': limit})
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'username': row[1],
                    'role': row[2],
                    'ip_address': row[3],
                    'created': row[4].isoformat() if row[4] else None,
                    'expires': row[5].isoformat() if row[5] else None,
                    'last_activity': row[6].isoformat() if row[6] else None
                })
            
            return sessions
            
        finally:
            cursor.close()
            conn.close()
    
    def get_audit_log(
        self,
        username: str = None,
        action: str = None,
        days: int = 7,
        limit: int = 100
    ) -> List[Dict]:
        """Get audit log entries"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT * FROM (
                    SELECT 
                        USERNAME, ACTION, RESOURCE, SUCCESS,
                        FAILURE_REASON, IP_ADDRESS, TIMESTAMP
                    FROM AUTH_AUDIT_LOG
                    WHERE TIMESTAMP > SYSDATE - :days
            """
            
            params = {'days': days, 'limit': limit}
            
            if username:
                query += " AND USERNAME = :username"
                params['username'] = username
            
            if action:
                query += " AND ACTION = :action"
                params['action'] = action
            
            query += " ORDER BY TIMESTAMP DESC ) WHERE ROWNUM <= :limit"
            
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'username': row[0],
                    'action': row[1],
                    'resource': row[2],
                    'success': row[3] == 'Y',
                    'failure_reason': row[4],
                    'ip_address': row[5],
                    'timestamp': row[6].isoformat() if row[6] else None
                })
            
            return logs
            
        finally:
            cursor.close()
            conn.close()
