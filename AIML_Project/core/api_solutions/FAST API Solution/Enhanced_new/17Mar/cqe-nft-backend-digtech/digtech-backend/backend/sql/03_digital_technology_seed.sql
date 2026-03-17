-- =============================================================================
-- SEED DATA — Digital Technology LOB
-- Run in SQL Developer against CQE_NFT schema AFTER running all DDL scripts.
-- =============================================================================

-- 1. LOB Master — Digital Technology with 3 tracks
-- (Update existing API_LOB_MASTER entries if they exist, or insert new ones)
-- -----------------------------------------------------------------------------
MERGE INTO API_LOB_MASTER t
USING (SELECT 'Digital Technology' AS lob_name, 'CDV3' AS track_name,
              'CQE_NFT' AS database_name FROM DUAL) s
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


-- 2. AppD LOB Master — your actual AppD applications for Digital Technology
-- Replace application names and IDs with your real values.
-- -----------------------------------------------------------------------------
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


-- 3. AppD LOB Config — the config entry that discovery uses
-- Replace TRACK, APPLICATION_NAMES with your real values.
-- -----------------------------------------------------------------------------
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


-- 4. NFT AppD Config — controller connection (token is in env var, NOT here)
-- Replace controller_url and account_name with your real values.
-- -----------------------------------------------------------------------------
MERGE INTO API_NFT_APPD_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.IS_ACTIVE = 'Y')
WHEN NOT MATCHED THEN
  INSERT (APPD_CONFIG_ID, LOB_NAME, CONTROLLER_URL, ACCOUNT_NAME,
          TOKEN_ENV_VAR, DEFAULT_NODE_COUNT, IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_APPD_CONFIG_SEQ.NEXTVAL,
    'Digital Technology',
    'https://appdynamics.corp.internal:8090',   -- CHANGE THIS
    'corp-prod-account',                          -- CHANGE THIS
    'APPD_TOKEN_DIGTECH',                         -- env var name
    3,
    'Y', SYSDATE, SYSDATE
  );


-- 5. NFT Kibana Config — dashboards (token_env_var, NOT actual token)
-- Replace kibana_url and dashboard_id with your real values.
-- -----------------------------------------------------------------------------
MERGE INTO API_NFT_KIBANA_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name,
              'CDV3' AS track_name,
              'API Performance — CDV3' AS display_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name AND t.DISPLAY_NAME = s.display_name)
WHEN NOT MATCHED THEN
  INSERT (KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
          TOKEN_ENV_VAR, AUTH_TYPE, DASHBOARD_ID, DISPLAY_NAME,
          TIME_FIELD, LAST_TEST_STATUS, IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_KIBANA_CONFIG_SEQ.NEXTVAL,
    'Digital Technology',
    'CDV3',
    'https://kibana.corp.internal:5601',          -- CHANGE THIS
    'KIBANA_TOKEN_DIGTECH',                        -- env var name
    'apikey',
    'abc12345-def6-7890-abcd-kib01',              -- CHANGE THIS: your real dashboard ID
    'API Performance — CDV3',
    '@timestamp',
    'NOT_TESTED',
    'Y', SYSDATE, SYSDATE
  );

MERGE INTO API_NFT_KIBANA_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name,
              'CDV3' AS track_name,
              'Application Errors — CDV3' AS display_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name AND t.DISPLAY_NAME = s.display_name)
WHEN NOT MATCHED THEN
  INSERT (KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
          TOKEN_ENV_VAR, AUTH_TYPE, DASHBOARD_ID, DISPLAY_NAME,
          TIME_FIELD, LAST_TEST_STATUS, IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_KIBANA_CONFIG_SEQ.NEXTVAL,
    'Digital Technology',
    'CDV3',
    'https://kibana.corp.internal:5601',          -- CHANGE THIS
    'KIBANA_TOKEN_DIGTECH',
    'apikey',
    'abc12345-def6-7890-abcd-kib02',              -- CHANGE THIS: your real dashboard ID
    'Application Errors — CDV3',
    '@timestamp',
    'NOT_TESTED',
    'Y', SYSDATE, SYSDATE
  );


-- 6. NFT PC Config — PC project connection
-- Replace pc_url, username, project_name, pass_env_var with real values.
-- -----------------------------------------------------------------------------
MERGE INTO API_NFT_PC_CONFIG t
USING (SELECT 'Digital Technology' AS lob_name,
              'CDV3' AS track_name,
              'Cards NFT — CDV3' AS display_name FROM DUAL) s
ON (t.LOB_NAME = s.lob_name AND t.TRACK_NAME = s.track_name AND t.DISPLAY_NAME = s.display_name)
WHEN NOT MATCHED THEN
  INSERT (PC_CONFIG_ID, LOB_NAME, TRACK_NAME, PC_URL, PC_PORT,
          USERNAME, PASS_ENV_VAR, DOMAIN, PROJECT_NAME, DISPLAY_NAME,
          DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC,
          LAST_TEST_STATUS, IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
  VALUES (
    API_NFT_PC_CONFIG_SEQ.NEXTVAL,
    'Digital Technology',
    'CDV3',
    'https://pc.corp.internal',                   -- CHANGE THIS
    443,
    'pc_svc_account',                             -- CHANGE THIS
    'PC_PASS_DIGTECH',                            -- env var name
    'DEFAULT',
    'CQE_CARDS_NFT',                              -- CHANGE THIS: your real project name
    'Cards NFT — CDV3',
    'HM',
    '-b',
    300,
    'NOT_TESTED',
    'Y', SYSDATE, SYSDATE
  );


-- 7. NFT Track Template — links all tools together for CDV3
-- Run this AFTER saving all tool configs above so the IDs exist.
-- You can also do this via the Admin UI Track Management page.
-- -----------------------------------------------------------------------------
-- First get the config IDs:
-- SELECT APPD_CONFIG_ID FROM API_NFT_APPD_CONFIG WHERE LOB_NAME = 'Digital Technology';
-- SELECT KIBANA_CONFIG_ID FROM API_NFT_KIBANA_CONFIG WHERE LOB_NAME = 'Digital Technology';
-- SELECT PC_CONFIG_ID FROM API_NFT_PC_CONFIG WHERE LOB_NAME = 'Digital Technology';

-- Then insert the template (replace IDs with actual values from above selects):
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
    API_NFT_TRACK_TEMPLATE_SEQ.NEXTVAL,
    'Digital Technology', 'CDV3',
    '1',   -- CHANGE: appd_config_id from step 4
    1,
    '1,2', -- CHANGE: kibana_config_ids from step 5 (comma-separated)
    2,
    '1',   -- CHANGE: pc_config_id from step 6
    1,
    NULL, 0,   -- Splunk on hold
    NULL, 0,   -- MongoDB on hold
    NULL, 0,   -- DB configs
    'Y', 'SYSTEM', SYSDATE, SYSDATE
  );

COMMIT;

-- =============================================================================
-- VERIFICATION QUERIES — run after seeding to confirm data
-- =============================================================================
SELECT LOB_NAME, TRACK_NAME, IS_ACTIVE FROM API_LOB_MASTER
  WHERE LOB_NAME = 'Digital Technology' ORDER BY TRACK_NAME;

SELECT LOB_NAME, TRACK_NAME, DISPLAY_NAME, TOKEN_ENV_VAR FROM API_NFT_KIBANA_CONFIG
  WHERE LOB_NAME = 'Digital Technology';

SELECT LOB_NAME, TRACK_NAME, PROJECT_NAME, PASS_ENV_VAR FROM API_NFT_PC_CONFIG
  WHERE LOB_NAME = 'Digital Technology';

SELECT LOB_NAME, CONTROLLER_URL, TOKEN_ENV_VAR FROM API_NFT_APPD_CONFIG
  WHERE LOB_NAME = 'Digital Technology';

SELECT LOB_NAME, TRACK_NAME, APPD_APP_COUNT, KIBANA_COUNT, PC_COUNT
  FROM API_NFT_TRACK_TEMPLATE WHERE LOB_NAME = 'Digital Technology';
