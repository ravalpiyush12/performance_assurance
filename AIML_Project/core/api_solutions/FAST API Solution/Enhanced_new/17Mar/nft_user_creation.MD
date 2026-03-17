-- Step 1: Check existing users
SELECT USER_ID, USERNAME, ROLE FROM API_AUTH_USERS ORDER BY CREATED_DATE;

-- Step 2: Grant Digital Technology access to admin user
-- (Replace 'admin' with your actual admin username if different)
INSERT INTO API_NFT_USER_LOB_ACCESS 
    (USERNAME, LOB_NAME, GRANTED_BY, IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
VALUES 
    ('admin', 'Digital Technology', 'SYSTEM', 'Y', SYSDATE, SYSDATE);

-- Step 3: Grant ALL LOBs to admin (run for each LOB in API_LOB_MASTER)
INSERT INTO API_NFT_USER_LOB_ACCESS 
    (USERNAME, LOB_NAME, GRANTED_BY, IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
SELECT 
    'admin',              -- change if your admin username is different
    LOB_NAME,
    'SYSTEM',
    'Y',
    SYSDATE,
    SYSDATE
FROM (
    SELECT DISTINCT LOB_NAME FROM API_LOB_MASTER WHERE IS_ACTIVE = 'Y'
)
WHERE NOT EXISTS (
    SELECT 1 FROM API_NFT_USER_LOB_ACCESS 
    WHERE USERNAME = 'admin' AND LOB_NAME = LOB_NAME
);

COMMIT;

-- Verify
SELECT USERNAME, LOB_NAME, IS_ACTIVE FROM API_NFT_USER_LOB_ACCESS ORDER BY USERNAME;


Deeper fix:
