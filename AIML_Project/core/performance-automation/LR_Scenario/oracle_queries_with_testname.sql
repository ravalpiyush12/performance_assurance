-- Sample SQL Queries with Scenario Name

-- ============================================
-- 1. Latest Test Results by Scenario
-- ============================================
SELECT 
    r.TEST_NAME,
    r.RUN_ID,
    r.RUN_DATE,
    r.TEST_STATUS,
    COUNT(t.TRANSACTION_ID) as TRANSACTION_COUNT,
    ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as OVERALL_AVG_RESPONSE,
    ROUND(MAX(t.MAX_RESPONSE_TIME), 2) as MAX_RESPONSE_TIME,
    ROUND(AVG(t.ERROR_RATE), 2) as AVG_ERROR_RATE
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 7  -- Last 7 days
GROUP BY r.TEST_NAME, r.RUN_ID, r.RUN_DATE, r.TEST_STATUS
ORDER BY r.RUN_DATE DESC;

-- ============================================
-- 2. Compare Scenarios - Last Run
-- ============================================
WITH LastRuns AS (
    SELECT 
        TEST_NAME,
        MAX(RUN_DATE) as LAST_RUN_DATE
    FROM PC_TEST_RUNS
    GROUP BY TEST_NAME
)
SELECT 
    r.TEST_NAME,
    r.RUN_ID,
    r.RUN_DATE,
    r.TEST_STATUS,
    COUNT(t.TRANSACTION_ID) as TRANSACTION_COUNT,
    ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as AVG_RESPONSE,
    ROUND(AVG(t.ERROR_RATE), 2) as AVG_ERROR_RATE
FROM PC_TEST_RUNS r
JOIN LastRuns lr ON r.TEST_NAME = lr.TEST_NAME 
    AND r.RUN_DATE = lr.LAST_RUN_DATE
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
GROUP BY r.TEST_NAME, r.RUN_ID, r.RUN_DATE, r.TEST_STATUS
ORDER BY r.TEST_NAME;

-- ============================================
-- 3. Scenario Performance Trend (Last 30 Days)
-- ============================================
SELECT 
    r.TEST_NAME,
    TRUNC(r.RUN_DATE) as RUN_DAY,
    COUNT(DISTINCT r.RUN_ID) as RUN_COUNT,
    ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as AVG_RESPONSE,
    ROUND(MIN(t.MIN_RESPONSE_TIME), 2) as MIN_RESPONSE,
    ROUND(MAX(t.MAX_RESPONSE_TIME), 2) as MAX_RESPONSE,
    ROUND(AVG(t.ERROR_RATE), 2) as AVG_ERROR_RATE
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 30
GROUP BY r.TEST_NAME, TRUNC(r.RUN_DATE)
ORDER BY r.TEST_NAME, RUN_DAY DESC;

-- ============================================
-- 4. Find Specific Scenario Runs
-- ============================================
SELECT 
    r.TEST_NAME,
    r.RUN_ID,
    r.BUILD_NUMBER,
    r.RUN_DATE,
    r.TEST_STATUS,
    r.TEST_DURATION,
    COUNT(t.TRANSACTION_ID) as TRANSACTION_COUNT
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.TEST_NAME LIKE '%Login%'  -- Change to your scenario name
GROUP BY r.TEST_NAME, r.RUN_ID, r.BUILD_NUMBER, r.RUN_DATE, 
         r.TEST_STATUS, r.TEST_DURATION
ORDER BY r.RUN_DATE DESC;

-- ============================================
-- 5. Transaction Performance by Scenario
-- ============================================
SELECT 
    r.TEST_NAME,
    t.TRANSACTION_NAME,
    COUNT(*) as RUN_COUNT,
    ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as AVG_RESPONSE,
    ROUND(MIN(t.MIN_RESPONSE_TIME), 2) as BEST_RESPONSE,
    ROUND(MAX(t.MAX_RESPONSE_TIME), 2) as WORST_RESPONSE,
    ROUND(AVG(t.PERCENTILE_90), 2) as AVG_P90,
    ROUND(AVG(t.ERROR_RATE), 2) as AVG_ERROR_RATE
FROM PC_TEST_RUNS r
JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 30
GROUP BY r.TEST_NAME, t.TRANSACTION_NAME
ORDER BY r.TEST_NAME, AVG_RESPONSE DESC;

-- ============================================
-- 6. Scenario Health Dashboard
-- ============================================
SELECT 
    r.TEST_NAME,
    COUNT(DISTINCT r.RUN_ID) as TOTAL_RUNS,
    SUM(CASE WHEN r.TEST_STATUS LIKE '%FINISHED%' THEN 1 ELSE 0 END) as SUCCESSFUL_RUNS,
    SUM(CASE WHEN r.TEST_STATUS LIKE '%FAILED%' THEN 1 ELSE 0 END) as FAILED_RUNS,
    ROUND(AVG(r.TEST_DURATION), 2) as AVG_DURATION_SECONDS,
    MAX(r.RUN_DATE) as LAST_RUN,
    ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as AVG_RESPONSE_TIME,
    ROUND(AVG(t.ERROR_RATE), 2) as AVG_ERROR_RATE
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 30
GROUP BY r.TEST_NAME
ORDER BY LAST_RUN DESC;

-- ============================================
-- 7. Daily Scenario Summary
-- ============================================
SELECT 
    TRUNC(r.RUN_DATE) as RUN_DATE,
    r.TEST_NAME,
    COUNT(DISTINCT r.RUN_ID) as RUN_COUNT,
    r.TEST_STATUS,
    ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as AVG_RESPONSE,
    COUNT(t.TRANSACTION_ID) as TOTAL_TRANSACTIONS
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 7
GROUP BY TRUNC(r.RUN_DATE), r.TEST_NAME, r.TEST_STATUS
ORDER BY RUN_DATE DESC, r.TEST_NAME;

-- ============================================
-- 8. Scenario Comparison - Same Transaction
-- ============================================
WITH ScenarioTxn AS (
    SELECT 
        r.TEST_NAME,
        t.TRANSACTION_NAME,
        ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as AVG_RESPONSE,
        COUNT(*) as SAMPLE_COUNT
    FROM PC_TEST_RUNS r
    JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
    WHERE r.RUN_DATE >= SYSDATE - 30
      AND t.TRANSACTION_NAME = 'Login'  -- Change to your transaction name
    GROUP BY r.TEST_NAME, t.TRANSACTION_NAME
)
SELECT 
    TEST_NAME,
    TRANSACTION_NAME,
    AVG_RESPONSE,
    SAMPLE_COUNT,
    RANK() OVER (ORDER BY AVG_RESPONSE) as PERFORMANCE_RANK
FROM ScenarioTxn
ORDER BY AVG_RESPONSE;

-- ============================================
-- 9. Find Slow Transactions by Scenario
-- ============================================
SELECT 
    r.TEST_NAME,
    r.RUN_ID,
    r.RUN_DATE,
    t.TRANSACTION_NAME,
    t.AVG_RESPONSE_TIME,
    t.MAX_RESPONSE_TIME,
    t.PERCENTILE_90,
    t.ERROR_RATE
FROM PC_TEST_RUNS r
JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE t.AVG_RESPONSE_TIME > 5000  -- Slower than 5 seconds
  AND r.RUN_DATE >= SYSDATE - 7
ORDER BY r.TEST_NAME, t.AVG_RESPONSE_TIME DESC;

-- ============================================
-- 10. Scenario Test History with Metadata
-- ============================================
SELECT 
    r.TEST_NAME,
    r.RUN_ID,
    r.TEST_ID,
    r.BUILD_NUMBER,
    r.RUN_DATE,
    r.TEST_STATUS,
    r.TEST_DURATION,
    r.PC_HOST,
    r.PC_PROJECT,
    COUNT(t.TRANSACTION_ID) as TRANSACTION_COUNT,
    ROUND(AVG(t.AVG_RESPONSE_TIME), 2) as AVG_RESPONSE
FROM PC_TEST_RUNS r
LEFT JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
GROUP BY r.TEST_NAME, r.RUN_ID, r.TEST_ID, r.BUILD_NUMBER, 
         r.RUN_DATE, r.TEST_STATUS, r.TEST_DURATION, r.PC_HOST, r.PC_PROJECT
ORDER BY r.RUN_DATE DESC
FETCH FIRST 50 ROWS ONLY;

-- ============================================
-- 11. Export Data for Excel/CSV
-- ============================================
SELECT 
    r.TEST_NAME,
    r.RUN_ID,
    TO_CHAR(r.RUN_DATE, 'YYYY-MM-DD HH24:MI:SS') as RUN_DATETIME,
    r.BUILD_NUMBER,
    t.TRANSACTION_NAME,
    t.AVG_RESPONSE_TIME,
    t.MIN_RESPONSE_TIME,
    t.MAX_RESPONSE_TIME,
    t.PERCENTILE_90,
    t.PERCENTILE_95,
    t.ERROR_RATE,
    t.TRANSACTION_COUNT
FROM PC_TEST_RUNS r
JOIN PC_TRANSACTIONS t ON r.RUN_ID = t.RUN_ID
WHERE r.RUN_DATE >= SYSDATE - 7
ORDER BY r.RUN_DATE DESC, r.TEST_NAME, t.TRANSACTION_NAME;
