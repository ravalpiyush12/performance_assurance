-- Production traffic metrics
CREATE TABLE prod_traffic_metrics (
    metric_timestamp TIMESTAMP,
    request_rate NUMBER,
    response_time_p50 NUMBER,
    response_time_p95 NUMBER,
    response_time_p99 NUMBER,
    error_rate NUMBER,
    throughput_mbps NUMBER,
    concurrent_users NUMBER,
    cpu_utilization NUMBER,
    memory_utilization NUMBER,
    db_connections NUMBER,
    cache_hit_rate NUMBER,
    endpoint_name VARCHAR2(200),
    http_method VARCHAR2(10)
);

-- PTE test runs
CREATE TABLE pte_test_runs (
    test_run_id VARCHAR2(50) PRIMARY KEY,
    test_type VARCHAR2(50),
    load_pattern VARCHAR2(100),
    test_duration_minutes NUMBER,
    test_description VARCHAR2(500),
    test_status VARCHAR2(20),
    test_timestamp TIMESTAMP
);

-- PTE traffic metrics
CREATE TABLE pte_traffic_metrics (
    test_run_id VARCHAR2(50),
    metric_timestamp TIMESTAMP,
    -- same columns as prod_traffic_metrics
);

-- Discrepancy reports
CREATE TABLE discrepancy_reports (
    analysis_id VARCHAR2(50),
    metric_name VARCHAR2(100),
    prod_value NUMBER,
    pte_value NUMBER,
    discrepancy_pct NUMBER,
    severity VARCHAR2(20),
    recommendation VARCHAR2(1000),
    created_date TIMESTAMP
);