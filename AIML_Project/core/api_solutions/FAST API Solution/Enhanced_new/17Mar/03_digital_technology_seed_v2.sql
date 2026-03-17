-- =============================================================================
-- SEED DATA v2 (CORRECTED) -- Digital Technology LOB
-- Fixes: CONFIG_ID column name, sequence names, column order safety
-- Run in SQL Developer against CQE_NFT schema AFTER all DDL scripts.
-- =============================================================================

-- ─── 1. API_LOB_MASTER ────────────────────────────────────────────────────────
-- Confirmed columns: ID(identity), LOB_NAME, TRACK_NAME, DATABASE_NAME,
--                    IS_ACTIVE, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE

MERGE INTO API_LOB_MASTER t
USING (SELECT 'Digital Technology' AS lob_name, 'CDV3' AS track_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name)
WHEN NOT MATCHED THEN
  INSERT (LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE, CREATED_BY, CREATED_DATE)
  VALUES ('Digital Technology', 'CDV3', 'CQE_NFT', 'Y', 'SYSTEM', SYSDATE);

MERGE INTO API_LOB_MASTER t
USING (SELECT 'Digital Technology' AS lob_name, 'Track1' AS track_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name)
WHEN NOT MATCHED THEN
  INSERT (LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE, CREATED_BY, CREATED_DATE)
  VALUES ('Digital Technology', 'Track1', 'CQE_NFT', 'Y', 'SYSTEM', SYSDATE);

MERGE INTO API_LOB_MASTER t
USING (SELECT 'Digital Technology' AS lob_name, 'Track2' AS track_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name)
WHEN NOT MATCHED THEN
  INSERT (LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE, CREATED_BY, CREATED_DATE)
  VALUES ('Digital Technology', 'Track2', 'CQE_NFT', 'Y', 'SYSTEM', SYSDATE);

COMMIT;

-- ─── 2. APPD_APPLICATIONS_MASTER ──────────────────────────────────────────────
-- Confirmed columns from appd/database.py:
-- APPLICATION_NAME, LOB_NAME, TRACK, DESCRIPTION, IS_ACTIVE, CREATED_DATE

MERGE INTO APPD_APPLICATIONS_MASTER t
USING (SELECT 'icg-tts-cirp-ng-173720_PTE' AS app_name FROM DUAL) s
ON (t.APPLICATION_NAME = s.app_name)
WHEN NOT MATCHED THEN
  INSERT (APPLICATION_NAME, LOB_NAME, TRACK, DESCRIPTION, IS_ACTIVE, CREATED_DATE)
  VALUES ('icg-tts-cirp-ng-173720_PTE', 'Digital Technology', 'CDV3',
          'Cards digital technology NFT application', 'Y', SYSDATE);

MERGE INTO APPD_APPLICATIONS_MASTER t
USING (SELECT 'CDV3_NFT_Digital_Technology' AS app_name FROM DUAL) s
ON (t.APPLICATION_NAME = s.app_name)
WHEN NOT MATCHED THEN
  INSERT (APPLICATION_NAME, LOB_NAME, TRACK, DESCRIPTION, IS_ACTIVE, CREATED_DATE)
  VALUES ('CDV3_NFT_Digital_Technology', 'Digital Technology', 'CDV3',
          'Digital Technology main monitoring app', 'Y', SYSDATE);

COMMIT;

-- ─── 3. API_APPD_LOB_CONFIG ───────────────────────────────────────────────────
-- From appd/database.py save_config():
-- Columns: LOB_ID, CONFIG_NAME, LOB_NAME, TRACK, APPLICATION_NAMES(CLOB),
--          IS_ACTIVE, CREATED_DATE, UPDATED_DATE
-- Sequence: API_APPD_LOB_CONFIG_SEQ (used in save_config method)
-- Note: if API_APPD_LOB_CONFIG_SEQ does not exist on your DB, create it first:
--   CREATE SEQUENCE API_APPD_LOB_CONFIG_SEQ START WITH 1 INCREMENT BY 1;

MERGE INTO API_APPD_LOB_CONFIG t
USING (SELECT 'Digital Technology CDV3' AS config_name FROM DUAL) s
ON (t.CONFIG_NAME = s.config_name)
WHEN NOT MATCHED THEN
  INSERT (LOB_ID, CONFIG_NAME, LOB_NAME, TRACK, APPLICATION_NAMES,
          IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_APPD_LOB_CONFIG_SEQ.NEXTVAL,
    'Digital Technology CDV3',
    'Digital Technology',
    'CDV3',
    '["icg-tts-cirp-ng-173720_PTE", "CDV3_NFT_Digital_Technology"]',
    'Y', SYSDATE, SYSDATE
  );

COMMIT;

-- ─── 4. API_NFT_APPD_CONFIG ───────────────────────────────────────────────────
-- DDL column: CONFIG_ID (NOT APPD_CONFIG_ID — that was the bug)
-- Sequence:   API_NFT_APPD_CFG_SEQ
-- No separate APPD_CONFIG_ID column in DDL.
-- Replace controller_url and account_name with your real values.

MERGE INTO API_NFT_APPD_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name)
WHEN NOT MATCHED THEN
  INSERT (CONFIG_ID, LOB_NAME, CONTROLLER_URL, ACCOUNT_NAME,
          TOKEN_ENV_VAR, DEFAULT_NODE_COUNT, IS_ACTIVE,
          CREATED_BY, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_APPD_CFG_SEQ.NEXTVAL,
    'Digital Technology',
    'https://appdynamics.corp.internal:8090',  -- CHANGE THIS to your real URL
    'corp-prod-account',                        -- CHANGE THIS to your account name
    'APPD_TOKEN_DIGTECH',
    3,
    'Y', 'SYSTEM', SYSDATE, SYSDATE
  );

COMMIT;

-- ─── 5. API_NFT_KIBANA_CONFIG ─────────────────────────────────────────────────
-- DDL columns confirmed: KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
--   USERNAME, TOKEN_ENV_VAR, AUTH_TYPE, DASHBOARD_ID, DISPLAY_NAME,
--   INDEX_PATTERN, TIME_FIELD, IS_ACTIVE, LAST_TEST_STATUS, LAST_TEST_DATE,
--   CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
-- Sequence: API_NFT_KIBANA_SEQ
-- Replace kibana_url and dashboard_id with your real values.

MERGE INTO API_NFT_KIBANA_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name, 'CDV3' AS track_name,
              'API Performance - CDV3' AS display_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name
    AND t.DISPLAY_NAME = s.display_name)
WHEN NOT MATCHED THEN
  INSERT (KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
          TOKEN_ENV_VAR, AUTH_TYPE, DASHBOARD_ID, DISPLAY_NAME,
          TIME_FIELD, IS_ACTIVE, LAST_TEST_STATUS,
          CREATED_BY, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_KIBANA_SEQ.NEXTVAL,
    'Digital Technology', 'CDV3',
    'https://kibana.corp.internal:5601',       -- CHANGE THIS
    'KIBANA_TOKEN_DIGTECH',
    'apikey',
    'abc12345-def6-7890-abcd-kib01',           -- CHANGE THIS: real dashboard ID
    'API Performance - CDV3',
    '@timestamp',
    'Y', 'NOT_TESTED', 'SYSTEM', SYSDATE, SYSDATE
  );

MERGE INTO API_NFT_KIBANA_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name, 'CDV3' AS track_name,
              'Application Errors - CDV3' AS display_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name
    AND t.DISPLAY_NAME = s.display_name)
WHEN NOT MATCHED THEN
  INSERT (KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
          TOKEN_ENV_VAR, AUTH_TYPE, DASHBOARD_ID, DISPLAY_NAME,
          TIME_FIELD, IS_ACTIVE, LAST_TEST_STATUS,
          CREATED_BY, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_KIBANA_SEQ.NEXTVAL,
    'Digital Technology', 'CDV3',
    'https://kibana.corp.internal:5601',       -- CHANGE THIS
    'KIBANA_TOKEN_DIGTECH',
    'apikey',
    'abc12345-def6-7890-abcd-kib02',           -- CHANGE THIS: real dashboard ID
    'Application Errors - CDV3',
    '@timestamp',
    'Y', 'NOT_TESTED', 'SYSTEM', SYSDATE, SYSDATE
  );

COMMIT;

-- ─── 6. API_NFT_PC_CONFIG ─────────────────────────────────────────────────────
-- DDL columns confirmed: PC_CONFIG_ID, LOB_NAME, TRACK_NAME, PC_URL, PC_PORT,
--   USERNAME, PASS_ENV_VAR, DOMAIN, PROJECT_NAME, DISPLAY_NAME,
--   DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC,
--   IS_ACTIVE, LAST_TEST_STATUS, LAST_TEST_DATE, LAST_RUN_ID,
--   CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
-- Sequence: API_NFT_PC_CONFIG_SEQ
-- Replace pc_url, username, project_name with your real values.

MERGE INTO API_NFT_PC_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name, 'CDV3' AS track_name,
              'CQE_CARDS_NFT' AS project_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name
    AND t.PROJECT_NAME = s.project_name)
WHEN NOT MATCHED THEN
  INSERT (PC_CONFIG_ID, LOB_NAME, TRACK_NAME, PC_URL, PC_PORT,
          USERNAME, PASS_ENV_VAR, DOMAIN, PROJECT_NAME, DISPLAY_NAME,
          DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC,
          IS_ACTIVE, LAST_TEST_STATUS,
          CREATED_BY, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_PC_CONFIG_SEQ.NEXTVAL,
    'Digital Technology', 'CDV3',
    'https://pc.corp.internal',                -- CHANGE THIS
    443,
    'pc_svc_account',                          -- CHANGE THIS
    'PC_PASS_DIGTECH',
    'DEFAULT',
    'CQE_CARDS_NFT',                           -- CHANGE THIS: real project name
    'Cards NFT - CDV3',
    'HM', '-b', 300,
    'Y', 'NOT_TESTED',
    'SYSTEM', SYSDATE, SYSDATE
  );

COMMIT;

-- ─── 7. API_NFT_TRACK_TEMPLATE ────────────────────────────────────────────────
-- Run the 3 queries below FIRST to get actual IDs, then update the VALUES.
-- DDL columns: TEMPLATE_ID, LOB_NAME, TRACK_NAME, APPD_APP_IDS, APPD_APP_COUNT,
--   KIBANA_CONFIG_IDS, KIBANA_COUNT, SPLUNK_CONFIG_IDS, SPLUNK_COUNT,
--   MONGODB_CONFIG_IDS, MONGODB_COUNT, PC_CONFIG_IDS, PC_COUNT,
--   DB_CONFIG_IDS, DB_COUNT, IS_ACTIVE, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
-- Sequence: API_NFT_TRACK_SEQ

-- Step A: Get IDs (run these SELECT first, note the values):
SELECT CONFIG_ID AS appd_config_id FROM API_NFT_APPD_CONFIG
  WHERE LOB_NAME = 'Digital Technology';

SELECT KIBANA_CONFIG_ID, DISPLAY_NAME FROM API_NFT_KIBANA_CONFIG
  WHERE LOB_NAME = 'Digital Technology' ORDER BY KIBANA_CONFIG_ID;

SELECT PC_CONFIG_ID FROM API_NFT_PC_CONFIG
  WHERE LOB_NAME = 'Digital Technology' AND TRACK_NAME = 'CDV3';

-- Step B: Insert template (replace ID values with results from Step A):
MERGE INTO API_NFT_TRACK_TEMPLATE t
USING (SELECT 'Digital Technology' AS lob_name, 'CDV3' AS track_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name)
WHEN NOT MATCHED THEN
  INSERT (TEMPLATE_ID, LOB_NAME, TRACK_NAME,
          APPD_APP_IDS, APPD_APP_COUNT,
          KIBANA_CONFIG_IDS, KIBANA_COUNT,
          PC_CONFIG_IDS, PC_COUNT,
          SPLUNK_CONFIG_IDS, SPLUNK_COUNT,
          MONGODB_CONFIG_IDS, MONGODB_COUNT,
          DB_CONFIG_IDS, DB_COUNT,
          IS_ACTIVE, CREATED_BY, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_TRACK_SEQ.NEXTVAL,
    'Digital Technology', 'CDV3',
    '1',   -- CHANGE: CONFIG_ID from API_NFT_APPD_CONFIG above
    1,
    '1,2', -- CHANGE: comma-separated KIBANA_CONFIG_IDs from above
    2,
    '1',   -- CHANGE: PC_CONFIG_ID from above
    1,
    NULL, 0,
    NULL, 0,
    NULL, 0,
    'Y', 'SYSTEM', SYSDATE, SYSDATE
  );

COMMIT;

-- =============================================================================
-- VERIFICATION — run these after seeding
-- =============================================================================
SELECT 'API_LOB_MASTER' AS tbl, COUNT(*) AS cnt
  FROM API_LOB_MASTER WHERE LOB_NAME = 'Digital Technology'
UNION ALL
SELECT 'APPD_APPLICATIONS_MASTER', COUNT(*)
  FROM APPD_APPLICATIONS_MASTER WHERE LOB_NAME = 'Digital Technology'
UNION ALL
SELECT 'API_APPD_LOB_CONFIG', COUNT(*)
  FROM API_APPD_LOB_CONFIG WHERE LOB_NAME = 'Digital Technology'
UNION ALL
SELECT 'API_NFT_APPD_CONFIG', COUNT(*)
  FROM API_NFT_APPD_CONFIG WHERE LOB_NAME = 'Digital Technology'
UNION ALL
SELECT 'API_NFT_KIBANA_CONFIG', COUNT(*)
  FROM API_NFT_KIBANA_CONFIG WHERE LOB_NAME = 'Digital Technology'
UNION ALL
SELECT 'API_NFT_PC_CONFIG', COUNT(*)
  FROM API_NFT_PC_CONFIG WHERE LOB_NAME = 'Digital Technology'
UNION ALL
SELECT 'API_NFT_TRACK_TEMPLATE', COUNT(*)
  FROM API_NFT_TRACK_TEMPLATE WHERE LOB_NAME = 'Digital Technology';
-- All rows should show count >= 1
