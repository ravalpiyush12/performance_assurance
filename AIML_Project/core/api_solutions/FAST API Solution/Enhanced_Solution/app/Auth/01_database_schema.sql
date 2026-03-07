-- ============================================
-- TOTP Authentication System - Database Schema
-- Complete SQL for Oracle Database
-- ============================================

-- Drop existing tables (if reinstalling)
-- DROP TABLE AUTH_AUDIT_LOG;
-- DROP TABLE AUTH_SESSIONS;
-- DROP TABLE AUTH_USERS;
-- DROP TABLE AUTH_ROLES;
-- DROP SEQUENCE AUTH_USER_SEQ;
-- DROP SEQUENCE AUTH_AUDIT_SEQ;

-- ============================================
-- 1. Sequences
-- ============================================

CREATE SEQUENCE AUTH_USER_SEQ START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE AUTH_AUDIT_SEQ START WITH 1 INCREMENT BY 1;

-- ============================================
-- 2. Roles and Permissions Table
-- ============================================

CREATE TABLE AUTH_ROLES (
    ROLE_NAME VARCHAR2(50) PRIMARY KEY,
    PERMISSIONS VARCHAR2(4000) NOT NULL,  -- JSON array of permissions
    DESCRIPTION VARCHAR2(500),
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE
);

COMMENT ON TABLE AUTH_ROLES IS 'Defines roles and their permissions';
COMMENT ON COLUMN AUTH_ROLES.PERMISSIONS IS 'JSON array like ["read","write","delete"]';

-- Insert default roles
INSERT INTO AUTH_ROLES (ROLE_NAME, PERMISSIONS, DESCRIPTION) VALUES 
('admin', '["read","write","delete","configure","user_manage"]', 'Full system access - can manage users and configurations');

INSERT INTO AUTH_ROLES (ROLE_NAME, PERMISSIONS, DESCRIPTION) VALUES 
('performance_engineer', '["read","write","register_test"]', 'Can register tests, upload AWR reports, and view monitoring data');

INSERT INTO AUTH_ROLES (ROLE_NAME, PERMISSIONS, DESCRIPTION) VALUES 
('test_lead', '["read","write","register_test","approve"]', 'Can register tests, approve results, and manage test lifecycle');

INSERT INTO AUTH_ROLES (ROLE_NAME, PERMISSIONS, DESCRIPTION) VALUES 
('viewer', '["read"]', 'Read-only access to monitoring dashboards and reports');

COMMIT;

-- ============================================
-- 3. Users Table
-- ============================================

CREATE TABLE AUTH_USERS (
    USER_ID NUMBER PRIMARY KEY,
    USERNAME VARCHAR2(100) UNIQUE NOT NULL,
    EMAIL VARCHAR2(200) NOT NULL,
    FULL_NAME VARCHAR2(200),
    PASSWORD_HASH VARCHAR2(256) NOT NULL,      -- bcrypt hash
    TOTP_SECRET VARCHAR2(100),                 -- Base32 encoded TOTP secret
    ROLE VARCHAR2(50) NOT NULL,
    IS_ACTIVE CHAR(1) DEFAULT 'Y' NOT NULL,
    MFA_ENABLED CHAR(1) DEFAULT 'Y' NOT NULL,
    FAILED_ATTEMPTS NUMBER DEFAULT 0,
    LOCKED_UNTIL DATE,
    LAST_LOGIN DATE,
    CREATED_DATE DATE DEFAULT SYSDATE,
    UPDATED_DATE DATE DEFAULT SYSDATE,
    CREATED_BY VARCHAR2(100),
    
    CONSTRAINT CHK_USER_ACTIVE CHECK (IS_ACTIVE IN ('Y', 'N')),
    CONSTRAINT CHK_USER_MFA CHECK (MFA_ENABLED IN ('Y', 'N')),
    CONSTRAINT FK_USER_ROLE FOREIGN KEY (ROLE) REFERENCES AUTH_ROLES(ROLE_NAME)
);

COMMENT ON TABLE AUTH_USERS IS 'Stores user accounts with TOTP secrets';
COMMENT ON COLUMN AUTH_USERS.PASSWORD_HASH IS 'bcrypt hashed password (never store plain text)';
COMMENT ON COLUMN AUTH_USERS.TOTP_SECRET IS 'Base32 encoded secret for Google Authenticator';
COMMENT ON COLUMN AUTH_USERS.FAILED_ATTEMPTS IS 'Counter for failed login attempts';
COMMENT ON COLUMN AUTH_USERS.LOCKED_UNTIL IS 'Account locked until this timestamp';

-- Indexes
CREATE INDEX IDX_USER_USERNAME ON AUTH_USERS(USERNAME);
CREATE INDEX IDX_USER_EMAIL ON AUTH_USERS(EMAIL);
CREATE INDEX IDX_USER_ROLE ON AUTH_USERS(ROLE);

-- ============================================
-- 4. Sessions Table
-- ============================================

CREATE TABLE AUTH_SESSIONS (
    SESSION_ID VARCHAR2(100) PRIMARY KEY,
    USER_ID NUMBER NOT NULL,
    USERNAME VARCHAR2(100) NOT NULL,
    ROLE VARCHAR2(50) NOT NULL,
    IP_ADDRESS VARCHAR2(50),
    USER_AGENT VARCHAR2(500),
    CREATED_DATE DATE DEFAULT SYSDATE,
    EXPIRES_DATE DATE NOT NULL,
    LAST_ACTIVITY DATE DEFAULT SYSDATE,
    
    CONSTRAINT FK_SESSION_USER FOREIGN KEY (USER_ID) REFERENCES AUTH_USERS(USER_ID) ON DELETE CASCADE
);

COMMENT ON TABLE AUTH_SESSIONS IS 'Active user sessions with expiry tracking';
COMMENT ON COLUMN AUTH_SESSIONS.EXPIRES_DATE IS 'Session automatically expires after this time';

-- Indexes
CREATE INDEX IDX_SESSION_USER ON AUTH_SESSIONS(USER_ID);
CREATE INDEX IDX_SESSION_EXPIRES ON AUTH_SESSIONS(EXPIRES_DATE);

-- ============================================
-- 5. Audit Log Table
-- ============================================

CREATE TABLE AUTH_AUDIT_LOG (
    AUDIT_ID NUMBER PRIMARY KEY,
    USERNAME VARCHAR2(100),
    USER_ID NUMBER,
    ACTION VARCHAR2(100) NOT NULL,           -- LOGIN, LOGOUT, FAILED_LOGIN, WRITE, DELETE, etc.
    RESOURCE VARCHAR2(200),                  -- Table/endpoint accessed
    DETAILS VARCHAR2(4000),                  -- Additional details in JSON
    IP_ADDRESS VARCHAR2(50),
    USER_AGENT VARCHAR2(500),
    SUCCESS CHAR(1) NOT NULL,
    FAILURE_REASON VARCHAR2(500),
    TIMESTAMP DATE DEFAULT SYSDATE,
    
    CONSTRAINT CHK_AUDIT_SUCCESS CHECK (SUCCESS IN ('Y', 'N'))
);

COMMENT ON TABLE AUTH_AUDIT_LOG IS 'Complete audit trail of all authentication and authorization events';
COMMENT ON COLUMN AUTH_AUDIT_LOG.ACTION IS 'Type of action performed';
COMMENT ON COLUMN AUTH_AUDIT_LOG.SUCCESS IS 'Y if action succeeded, N if failed';

-- Indexes
CREATE INDEX IDX_AUDIT_USERNAME ON AUTH_AUDIT_LOG(USERNAME);
CREATE INDEX IDX_AUDIT_ACTION ON AUTH_AUDIT_LOG(ACTION);
CREATE INDEX IDX_AUDIT_TIMESTAMP ON AUTH_AUDIT_LOG(TIMESTAMP);
CREATE INDEX IDX_AUDIT_SUCCESS ON AUTH_AUDIT_LOG(SUCCESS);

-- ============================================
-- 6. Create Default Admin User
-- ============================================

-- Note: This creates admin with password 'Admin@123' 
-- You MUST change this password immediately after first login!

-- The bcrypt hash below is for password: Admin@123
-- Generated with: bcrypt.hashpw('Admin@123'.encode(), bcrypt.gensalt())

INSERT INTO AUTH_USERS (
    USER_ID, USERNAME, EMAIL, FULL_NAME, 
    PASSWORD_HASH, TOTP_SECRET, ROLE, 
    IS_ACTIVE, MFA_ENABLED, CREATED_BY
) VALUES (
    AUTH_USER_SEQ.NEXTVAL,
    'admin',
    'admin@company.com',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYmPvr6yXw2',  -- Admin@123
    NULL,  -- TOTP will be set on first login
    'admin',
    'Y',
    'N',  -- MFA disabled for first login, enable after setup
    'SYSTEM'
);

COMMIT;

-- ============================================
-- 7. Cleanup Job (Optional)
-- ============================================

-- Create job to clean expired sessions daily
BEGIN
    DBMS_SCHEDULER.CREATE_JOB (
        job_name        => 'CLEANUP_EXPIRED_SESSIONS',
        job_type        => 'PLSQL_BLOCK',
        job_action      => 'BEGIN DELETE FROM AUTH_SESSIONS WHERE EXPIRES_DATE < SYSDATE; COMMIT; END;',
        start_date      => SYSTIMESTAMP,
        repeat_interval => 'FREQ=DAILY; BYHOUR=2',
        enabled         => TRUE,
        comments        => 'Clean up expired sessions daily at 2 AM'
    );
END;
/

-- ============================================
-- 8. Views for Monitoring
-- ============================================

-- Active sessions view
CREATE OR REPLACE VIEW V_ACTIVE_SESSIONS AS
SELECT 
    s.SESSION_ID,
    s.USERNAME,
    u.FULL_NAME,
    s.ROLE,
    s.IP_ADDRESS,
    s.CREATED_DATE,
    s.EXPIRES_DATE,
    ROUND((s.EXPIRES_DATE - SYSDATE) * 24 * 60, 0) AS MINUTES_REMAINING,
    s.LAST_ACTIVITY
FROM AUTH_SESSIONS s
JOIN AUTH_USERS u ON s.USER_ID = u.USER_ID
WHERE s.EXPIRES_DATE > SYSDATE
ORDER BY s.CREATED_DATE DESC;

-- Recent login attempts
CREATE OR REPLACE VIEW V_RECENT_LOGINS AS
SELECT 
    USERNAME,
    ACTION,
    IP_ADDRESS,
    SUCCESS,
    FAILURE_REASON,
    TIMESTAMP
FROM AUTH_AUDIT_LOG
WHERE ACTION IN ('LOGIN', 'FAILED_LOGIN', 'LOGOUT')
  AND TIMESTAMP > SYSDATE - 7  -- Last 7 days
ORDER BY TIMESTAMP DESC;

-- Failed login summary
CREATE OR REPLACE VIEW V_FAILED_LOGINS_SUMMARY AS
SELECT 
    USERNAME,
    COUNT(*) AS FAILED_COUNT,
    MAX(TIMESTAMP) AS LAST_FAILED,
    LISTAGG(IP_ADDRESS, ', ') WITHIN GROUP (ORDER BY TIMESTAMP) AS IP_ADDRESSES
FROM AUTH_AUDIT_LOG
WHERE ACTION = 'FAILED_LOGIN'
  AND TIMESTAMP > SYSDATE - 1  -- Last 24 hours
GROUP BY USERNAME
HAVING COUNT(*) >= 3
ORDER BY FAILED_COUNT DESC;

-- ============================================
-- 9. Grant Permissions (Adjust as needed)
-- ============================================

-- Grant to your application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON AUTH_USERS TO your_app_user;
-- GRANT SELECT, INSERT, DELETE ON AUTH_SESSIONS TO your_app_user;
-- GRANT SELECT, INSERT ON AUTH_AUDIT_LOG TO your_app_user;
-- GRANT SELECT ON AUTH_ROLES TO your_app_user;
-- GRANT SELECT ON V_ACTIVE_SESSIONS TO your_app_user;
-- GRANT SELECT ON V_RECENT_LOGINS TO your_app_user;
-- GRANT SELECT, UPDATE ON AUTH_USER_SEQ TO your_app_user;
-- GRANT SELECT, UPDATE ON AUTH_AUDIT_SEQ TO your_app_user;

-- ============================================
-- 10. Verification Queries
-- ============================================

-- Check if everything is created
SELECT 'Tables Created' AS STATUS FROM DUAL;
SELECT TABLE_NAME FROM USER_TABLES WHERE TABLE_NAME LIKE 'AUTH_%' ORDER BY TABLE_NAME;

SELECT 'Sequences Created' AS STATUS FROM DUAL;
SELECT SEQUENCE_NAME FROM USER_SEQUENCES WHERE SEQUENCE_NAME LIKE 'AUTH_%';

SELECT 'Default Roles' AS STATUS FROM DUAL;
SELECT ROLE_NAME, DESCRIPTION FROM AUTH_ROLES ORDER BY ROLE_NAME;

SELECT 'Default Admin User' AS STATUS FROM DUAL;
SELECT USER_ID, USERNAME, EMAIL, ROLE, IS_ACTIVE, MFA_ENABLED FROM AUTH_USERS;

-- ============================================
-- INSTALLATION COMPLETE
-- ============================================

-- NEXT STEPS:
-- 1. Run this script in your Oracle database
-- 2. Note the default admin credentials: admin / Admin@123
-- 3. Start the Python backend
-- 4. Login and set up TOTP for admin user
-- 5. Change admin password immediately
-- 6. Create additional users as needed

PROMPT 
PROMPT ========================================
PROMPT Authentication Database Setup Complete!
PROMPT ========================================
PROMPT 
PROMPT Default Admin User Created:
PROMPT   Username: admin
PROMPT   Password: Admin@123
PROMPT   Email: admin@company.com
PROMPT 
PROMPT ⚠️  SECURITY WARNING:
PROMPT   1. Change admin password immediately after first login
PROMPT   2. Enable MFA for admin user
PROMPT   3. Create individual user accounts (do not share admin)
PROMPT 
PROMPT Next: Install Python dependencies and start backend
PROMPT ========================================
