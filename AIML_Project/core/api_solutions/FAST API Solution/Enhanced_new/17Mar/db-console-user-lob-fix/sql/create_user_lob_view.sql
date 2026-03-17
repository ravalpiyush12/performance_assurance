-- =============================================================
-- ALTER: Support LOB filtering in user management
-- =============================================================
-- Note: LOB access is already stored in API_NFT_USER_LOB_ACCESS table.
-- This approach queries that table — NO ALTER to API_AUTH_USERS needed.
-- The frontend loads LOB assignments per user from:
--   GET /api/v1/nft/user-lob-access/{username}

-- If you want a convenience view that joins users + LOB access:
CREATE OR REPLACE VIEW V_AUTH_USERS_WITH_LOB AS
SELECT
    u.USER_ID,
    u.USERNAME,
    u.EMAIL,
    u.FULL_NAME,
    u.ROLE,
    u.IS_ACTIVE,
    u.MFA_ENABLED,
    u.LAST_LOGIN,
    u.CREATED_DATE,
    LISTAGG(l.LOB_NAME, ', ')
        WITHIN GROUP (ORDER BY l.LOB_NAME) AS LOB_ACCESS,
    COUNT(l.LOB_NAME) AS LOB_COUNT
FROM API_AUTH_USERS u
LEFT JOIN API_NFT_USER_LOB_ACCESS l
    ON u.USERNAME = l.USERNAME AND l.IS_ACTIVE = 'Y'
GROUP BY
    u.USER_ID, u.USERNAME, u.EMAIL, u.FULL_NAME, u.ROLE,
    u.IS_ACTIVE, u.MFA_ENABLED, u.LAST_LOGIN, u.CREATED_DATE;

-- Grant access
-- GRANT SELECT ON V_AUTH_USERS_WITH_LOB TO your_app_user;

COMMIT;

-- Verification
SELECT USERNAME, ROLE, LOB_ACCESS, LOB_COUNT
FROM V_AUTH_USERS_WITH_LOB
ORDER BY USERNAME;
