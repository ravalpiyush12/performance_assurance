-- ============================================================
-- API_NFT_RELEASE_REPORTS — DDL
-- Stores final NFT report HTML as CLOB for long-term retention
-- Run this once in SQL Developer against CQE_NFT schema
-- ============================================================

CREATE TABLE API_NFT_RELEASE_REPORTS (
    REPORT_ID           NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    RUN_ID              VARCHAR2(100)   NOT NULL,           -- Master run ID e.g. RUNID_35678_24Mar2026_001
    PC_RUN_ID           VARCHAR2(20)    NOT NULL,           -- 5-digit PC run ID
    LOB_NAME            VARCHAR2(100)   NOT NULL,
    RELEASE_NAME        VARCHAR2(200)   NOT NULL,           -- e.g. Release 2.5
    TEST_TYPE           VARCHAR2(50)    NOT NULL,           -- LOAD / STRESS / ENDURANCE
    TEST_NAME           VARCHAR2(200),
    TRACK_NAME          VARCHAR2(100),
    REPORT_HTML         CLOB,                               -- Full rendered HTML of the report
    REPORT_SIZE_KB      NUMBER,
    OVERALL_STATUS      VARCHAR2(50),                       -- PASS / FAIL / WARN
    PASS_RATE_PCT       NUMBER(5,2),
    PEAK_VUSERS         NUMBER,
    AVG_RESPONSE_MS     NUMBER(10,2),
    P95_RESPONSE_MS     NUMBER(10,2),
    TOTAL_TRANSACTIONS  NUMBER,
    FAILED_TRANSACTIONS NUMBER,
    SAVED_BY            VARCHAR2(100),                      -- Username who saved
    SAVED_DATE          DATE            DEFAULT SYSDATE,
    NOTES               VARCHAR2(2000),
    IS_ACTIVE           VARCHAR2(1)     DEFAULT 'Y'         -- Soft delete flag
);

-- Index for fast lookup by LOB + release
CREATE INDEX IDX_NFT_REL_RPT_LOB  ON API_NFT_RELEASE_REPORTS (LOB_NAME, RELEASE_NAME);
CREATE INDEX IDX_NFT_REL_RPT_RUN  ON API_NFT_RELEASE_REPORTS (RUN_ID);
CREATE INDEX IDX_NFT_REL_RPT_DATE ON API_NFT_RELEASE_REPORTS (SAVED_DATE);

-- Prevent duplicate save for same run + test type
CREATE UNIQUE INDEX UQ_NFT_REL_RPT_RUN_TYPE ON API_NFT_RELEASE_REPORTS (RUN_ID, TEST_TYPE);

COMMENT ON TABLE  API_NFT_RELEASE_REPORTS                IS 'Long-term storage for final NFT test reports (LOAD/STRESS/ENDURANCE). Retained 12+ months.';
COMMENT ON COLUMN API_NFT_RELEASE_REPORTS.REPORT_HTML    IS 'Full rendered HTML of pc_report.html at time of save';
COMMENT ON COLUMN API_NFT_RELEASE_REPORTS.REPORT_SIZE_KB IS 'Size of REPORT_HTML in kilobytes';
COMMENT ON COLUMN API_NFT_RELEASE_REPORTS.IS_ACTIVE      IS 'Y=active, N=soft-deleted';

COMMIT;
