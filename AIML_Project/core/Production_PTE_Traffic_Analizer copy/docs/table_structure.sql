-- ============================================================================
-- Oracle Table Structures for Production vs PTE Traffic Analysis
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PROD_PTE_COMPARISON Table
-- Stores comparison results between production and PTE metrics
-- ----------------------------------------------------------------------------
CREATE TABLE prod_pte_comparison (
    comparison_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analysis_id         VARCHAR2(50) NOT NULL,
    api_endpoint        VARCHAR2(500) NOT NULL,
    metric_name         VARCHAR2(100) NOT NULL,
    prod_value          NUMBER(18,4),
    pte_value           NUMBER(18,4),
    difference          NUMBER(18,4),
    difference_pct      NUMBER(10,2),
    severity            VARCHAR2(20) CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    status              VARCHAR2(20) CHECK (status IN ('pass', 'fail', 'warning')),
    created_date        DATE DEFAULT SYSDATE,
    CONSTRAINT uk_comparison UNIQUE (analysis_id, api_endpoint, metric_name)
);

-- Add comments for documentation
COMMENT ON TABLE prod_pte_comparison IS 'Stores comparison results between production and PTE endpoint metrics';
COMMENT ON COLUMN prod_pte_comparison.comparison_id IS 'Unique identifier for each comparison record';
COMMENT ON COLUMN prod_pte_comparison.analysis_id IS 'Analysis run identifier (format: ANALYSIS_YYYYMMDD_HHMMSS)';
COMMENT ON COLUMN prod_pte_comparison.api_endpoint IS 'API endpoint being compared';
COMMENT ON COLUMN prod_pte_comparison.metric_name IS 'Metric type: call_count, avg_duration, p90_duration, p95_duration';
COMMENT ON COLUMN prod_pte_comparison.prod_value IS 'Production metric value';
COMMENT ON COLUMN prod_pte_comparison.pte_value IS 'PTE test metric value';
COMMENT ON COLUMN prod_pte_comparison.difference IS 'Absolute difference (pte_value - prod_value)';
COMMENT ON COLUMN prod_pte_comparison.difference_pct IS 'Percentage difference';
COMMENT ON COLUMN prod_pte_comparison.severity IS 'Issue severity: critical, high, medium, low';
COMMENT ON COLUMN prod_pte_comparison.status IS 'Test status: pass, fail, warning';

-- Create indexes for better query performance
CREATE INDEX idx_comparison_analysis ON prod_pte_comparison(analysis_id);
CREATE INDEX idx_comparison_endpoint ON prod_pte_comparison(api_endpoint);
CREATE INDEX idx_comparison_severity ON prod_pte_comparison(severity);
CREATE INDEX idx_comparison_status ON prod_pte_comparison(status);
CREATE INDEX idx_comparison_date ON prod_pte_comparison(created_date);

-- ----------------------------------------------------------------------------
-- 2. ANALYSIS_SUMMARY Table
-- Stores high-level summary of each analysis run
-- ----------------------------------------------------------------------------
CREATE TABLE analysis_summary (
    analysis_id                 VARCHAR2(50) PRIMARY KEY,
    analysis_timestamp          DATE DEFAULT SYSDATE,
    prod_days_analyzed          NUMBER(5),
    pte_days_analyzed           NUMBER(5),
    total_comparisons           NUMBER(10),
    critical_issues             NUMBER(10),
    high_issues                 NUMBER(10),
    medium_issues               NUMBER(10),
    low_issues                  NUMBER(10),
    failed_tests                NUMBER(10),
    passed_tests                NUMBER(10),
    coverage_percentage         NUMBER(5,2),
    total_prod_endpoints        NUMBER(10),
    total_pte_endpoints         NUMBER(10),
    untested_endpoints          NUMBER(10),
    analysis_status             VARCHAR2(20) DEFAULT 'COMPLETED',
    created_by                  VARCHAR2(100),
    created_date                DATE DEFAULT SYSDATE,
    CONSTRAINT chk_analysis_status CHECK (analysis_status IN ('RUNNING', 'COMPLETED', 'FAILED'))
);

COMMENT ON TABLE analysis_summary IS 'High-level summary of each analysis run';
COMMENT ON COLUMN analysis_summary.analysis_id IS 'Unique analysis run identifier';
COMMENT ON COLUMN analysis_summary.coverage_percentage IS 'Percentage of production endpoints tested in PTE';

-- ----------------------------------------------------------------------------
-- 3. ENDPOINT_RECOMMENDATIONS Table
-- Stores actionable recommendations for each endpoint
-- ----------------------------------------------------------------------------
CREATE TABLE endpoint_recommendations (
    recommendation_id       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    analysis_id             VARCHAR2(50) NOT NULL,
    api_endpoint            VARCHAR2(500),
    recommendation_type     VARCHAR2(50),
    priority                VARCHAR2(20) CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    recommendation_text     VARCHAR2(4000),
    target_metric           VARCHAR2(100),
    current_value           NUMBER(18,4),
    recommended_value       NUMBER(18,4),
    estimated_impact        VARCHAR2(20),
    status                  VARCHAR2(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
    created_date            DATE DEFAULT SYSDATE,
    resolved_date           DATE,
    CONSTRAINT fk_recommendation_analysis FOREIGN KEY (analysis_id) 
        REFERENCES analysis_summary(analysis_id) ON DELETE CASCADE
);

COMMENT ON TABLE endpoint_recommendations IS 'Actionable recommendations for improving PTE test coverage';
COMMENT ON COLUMN endpoint_recommendations.recommendation_type IS 'Type: INCREASE_LOAD, EXTEND_DURATION, ADD_COVERAGE, FIX_PERFORMANCE';

CREATE INDEX idx_recommendation_analysis ON endpoint_recommendations(analysis_id);
CREATE INDEX idx_recommendation_endpoint ON endpoint_recommendations(api_endpoint);
CREATE INDEX idx_recommendation_priority ON endpoint_recommendations(priority);
CREATE INDEX idx_recommendation_status ON endpoint_recommendations(status);

-- ----------------------------------------------------------------------------
-- 4. ANALYSIS_TRENDS Table
-- Tracks trends over multiple analysis runs
-- ----------------------------------------------------------------------------
CREATE TABLE analysis_trends (
    trend_id                NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    api_endpoint            VARCHAR2(500) NOT NULL,
    metric_name             VARCHAR2(100) NOT NULL,
    analysis_date           DATE NOT NULL,
    prod_value              NUMBER(18,4),
    pte_value               NUMBER(18,4),
    difference_pct          NUMBER(10,2),
    trend_direction         VARCHAR2(20) CHECK (trend_direction IN ('IMPROVING', 'DEGRADING', 'STABLE')),
    created_date            DATE DEFAULT SYSDATE,
    CONSTRAINT uk_trend UNIQUE (api_endpoint, metric_name, analysis_date)
);

COMMENT ON TABLE analysis_trends IS 'Tracks metric trends over time for trend analysis';

CREATE INDEX idx_trend_endpoint ON analysis_trends(api_endpoint);
CREATE INDEX idx_trend_date ON analysis_trends(analysis_date);
CREATE INDEX idx_trend_direction ON analysis_trends(trend_direction);

-- ----------------------------------------------------------------------------
-- 5. ALERT_THRESHOLDS Table
-- Define custom thresholds for alerts
-- ----------------------------------------------------------------------------
CREATE TABLE alert_thresholds (
    threshold_id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    metric_name             VARCHAR2(100) NOT NULL,
    endpoint_pattern        VARCHAR2(500),  -- NULL means applies to all endpoints
    warning_threshold_pct   NUMBER(10,2),
    critical_threshold_pct  NUMBER(10,2),
    is_active               CHAR(1) DEFAULT 'Y' CHECK (is_active IN ('Y', 'N')),
    created_date            DATE DEFAULT SYSDATE,
    modified_date           DATE,
    created_by              VARCHAR2(100),
    CONSTRAINT uk_threshold UNIQUE (metric_name, endpoint_pattern)
);

COMMENT ON TABLE alert_thresholds IS 'Custom threshold definitions for different metrics and endpoints';

-- Insert default thresholds
INSERT INTO alert_thresholds (metric_name, warning_threshold_pct, critical_threshold_pct)
VALUES ('call_count', 30, 50);

INSERT INTO alert_thresholds (metric_name, warning_threshold_pct, critical_threshold_pct)
VALUES ('avg_duration', 20, 40);

INSERT INTO alert_thresholds (metric_name, warning_threshold_pct, critical_threshold_pct)
VALUES ('p90_duration', 25, 45);

INSERT INTO alert_thresholds (metric_name, warning_threshold_pct, critical_threshold_pct)
VALUES ('p95_duration', 25, 50);

COMMIT;

-- ----------------------------------------------------------------------------
-- 6. Useful Views for Reporting
-- ----------------------------------------------------------------------------

-- View: Latest Analysis Summary
CREATE OR REPLACE VIEW v_latest_analysis AS
SELECT 
    a.analysis_id,
    a.analysis_timestamp,
    a.total_comparisons,
    a.critical_issues,
    a.high_issues,
    a.failed_tests,
    a.passed_tests,
    a.coverage_percentage,
    ROUND((a.passed_tests / NULLIF(a.total_comparisons, 0)) * 100, 2) as pass_rate,
    a.untested_endpoints,
    a.analysis_status
FROM analysis_summary a
WHERE a.analysis_timestamp = (SELECT MAX(analysis_timestamp) FROM analysis_summary);

COMMENT ON VIEW v_latest_analysis IS 'Shows the most recent analysis run summary';

-- View: Critical Issues by Endpoint
CREATE OR REPLACE VIEW v_critical_issues AS
SELECT 
    c.analysis_id,
    c.api_endpoint,
    c.metric_name,
    c.prod_value,
    c.pte_value,
    c.difference,
    c.difference_pct,
    c.severity,
    c.status,
    c.created_date
FROM prod_pte_comparison c
WHERE c.severity IN ('critical', 'high')
    AND c.status = 'fail'
ORDER BY 
    CASE c.severity 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        ELSE 3 
    END,
    ABS(c.difference_pct) DESC;

COMMENT ON VIEW v_critical_issues IS 'Shows all critical and high severity failed tests';

-- View: Endpoint Performance Comparison
CREATE OR REPLACE VIEW v_endpoint_performance AS
SELECT 
    c.api_endpoint,
    MAX(CASE WHEN c.metric_name = 'call_count' THEN c.prod_value END) as prod_calls,
    MAX(CASE WHEN c.metric_name = 'call_count' THEN c.pte_value END) as pte_calls,
    MAX(CASE WHEN c.metric_name = 'avg_duration' THEN c.prod_value END) as prod_avg_duration,
    MAX(CASE WHEN c.metric_name = 'avg_duration' THEN c.pte_value END) as pte_avg_duration,
    MAX(CASE WHEN c.metric_name = 'p95_duration' THEN c.prod_value END) as prod_p95_duration,
    MAX(CASE WHEN c.metric_name = 'p95_duration' THEN c.pte_value END) as pte_p95_duration,
    COUNT(CASE WHEN c.status = 'fail' THEN 1 END) as failed_metrics,
    MAX(c.created_date) as last_analyzed
FROM prod_pte_comparison c
WHERE c.analysis_id = (SELECT MAX(analysis_id) FROM prod_pte_comparison)
GROUP BY c.api_endpoint
ORDER BY failed_metrics DESC, c.api_endpoint;

COMMENT ON VIEW v_endpoint_performance IS 'Consolidated view of endpoint metrics comparison';

-- View: Coverage Analysis
CREATE OR REPLACE VIEW v_coverage_analysis AS
WITH prod_endpoints AS (
    SELECT DISTINCT api_endpoint
    FROM prod
    WHERE measuredate >= SYSDATE - 7
),
pte_endpoints AS (
    SELECT DISTINCT api_endpoint
    FROM pte
    WHERE measuredate >= SYSDATE - 30
)
SELECT 
    p.api_endpoint,
    CASE WHEN t.api_endpoint IS NOT NULL THEN 'Tested' ELSE 'Not Tested' END as test_status,
    (SELECT COUNT(*) FROM prod WHERE api_endpoint = p.api_endpoint AND measuredate >= SYSDATE - 7) as prod_call_count,
    (SELECT AVG(avgduration) FROM prod WHERE api_endpoint = p.api_endpoint AND measuredate >= SYSDATE - 7) as prod_avg_duration
FROM prod_endpoints p
LEFT JOIN pte_endpoints t ON p.api_endpoint = t.api_endpoint
ORDER BY test_status, prod_call_count DESC;

COMMENT ON VIEW v_coverage_analysis IS 'Shows which endpoints are tested vs untested';

-- ----------------------------------------------------------------------------
-- 7. Stored Procedures
-- ----------------------------------------------------------------------------

-- Procedure: Clean up old analysis data
CREATE OR REPLACE PROCEDURE sp_cleanup_old_analysis (
    p_days_to_keep IN NUMBER DEFAULT 90
) AS
    v_cutoff_date DATE;
    v_deleted_count NUMBER;
BEGIN
    v_cutoff_date := SYSDATE - p_days_to_keep;
    
    -- Delete old comparison records
    DELETE FROM prod_pte_comparison
    WHERE created_date < v_cutoff_date;
    
    v_deleted_count := SQL%ROWCOUNT;
    
    -- Delete old analysis summaries
    DELETE FROM analysis_summary
    WHERE created_date < v_cutoff_date;
    
    -- Delete old trends
    DELETE FROM analysis_trends
    WHERE created_date < v_cutoff_date;
    
    COMMIT;
    
    DBMS_OUTPUT.PUT_LINE('Cleanup completed. Deleted ' || v_deleted_count || ' comparison records.');
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END sp_cleanup_old_analysis;
/

-- Procedure: Get analysis statistics
CREATE OR REPLACE PROCEDURE sp_get_analysis_stats (
    p_analysis_id IN VARCHAR2,
    p_cursor OUT SYS_REFCURSOR
) AS
BEGIN
    OPEN p_cursor FOR
    SELECT 
        metric_name,
        COUNT(*) as total_comparisons,
        SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as failed_count,
        SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passed_count,
        AVG(difference_pct) as avg_difference_pct,
        MAX(difference_pct) as max_difference_pct,
        MIN(difference_pct) as min_difference_pct
    FROM prod_pte_comparison
    WHERE analysis_id = p_analysis_id
    GROUP BY metric_name
    ORDER BY failed_count DESC;
END sp_get_analysis_stats;
/

-- ----------------------------------------------------------------------------
-- 8. Grant Permissions (adjust as needed)
-- ----------------------------------------------------------------------------

-- Grant SELECT to read-only users
-- GRANT SELECT ON prod_pte_comparison TO readonly_role;
-- GRANT SELECT ON analysis_summary TO readonly_role;
-- GRANT SELECT ON v_latest_analysis TO readonly_role;
-- GRANT SELECT ON v_critical_issues TO readonly_role;

-- Grant INSERT, UPDATE, DELETE to application users
-- GRANT SELECT, INSERT, UPDATE, DELETE ON prod_pte_comparison TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON analysis_summary TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON endpoint_recommendations TO app_user;

-- ----------------------------------------------------------------------------
-- 9. Sample Queries for Analysis
-- ----------------------------------------------------------------------------

-- Query 1: Get latest analysis summary
/*
SELECT * FROM v_latest_analysis;
*/

-- Query 2: Get all critical issues from latest analysis
/*
SELECT 
    api_endpoint,
    metric_name,
    prod_value,
    pte_value,
    difference_pct,
    severity
FROM v_critical_issues
WHERE analysis_id = (SELECT MAX(analysis_id) FROM analysis_summary);
*/

-- Query 3: Get endpoints with most failures
/*
SELECT 
    api_endpoint,
    COUNT(*) as failure_count,
    STRING_AGG(metric_name, ', ') as failed_metrics
FROM prod_pte_comparison
WHERE status = 'fail'
    AND analysis_id = (SELECT MAX(analysis_id) FROM analysis_summary)
GROUP BY api_endpoint
ORDER BY failure_count DESC
FETCH FIRST 10 ROWS ONLY;
*/

-- Query 4: Trend analysis for specific endpoint
/*
SELECT 
    analysis_date,
    metric_name,
    prod_value,
    pte_value,
    difference_pct,
    trend_direction
FROM analysis_trends
WHERE api_endpoint = '/api/v1/users'
ORDER BY analysis_date DESC, metric_name;
*/

-- Query 5: Coverage statistics
/*
SELECT 
    test_status,
    COUNT(*) as endpoint_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM v_coverage_analysis
GROUP BY test_status;
*/

-- ----------------------------------------------------------------------------
-- End of DDL Script
-- ----------------------------------------------------------------------------