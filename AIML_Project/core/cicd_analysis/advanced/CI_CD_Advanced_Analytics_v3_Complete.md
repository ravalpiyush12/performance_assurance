# CI/CD Advanced Analytics - Complete Architecture & Implementation Guide (Version 3)

## 📋 Executive Summary

**Project:** Enterprise-grade ML/AI-powered predictive analytics platform for CI/CD testing  
**Timeline:** 4 weeks (complete by end of month)  
**Tech Stack:** FastAPI, React, Oracle DB, Redis, Scikit-learn, TensorFlow, Anthropic Claude  

---

## ✅ Confirmed Requirements

| Category | Specification |
|----------|---------------|
| **Database** | Oracle DB (existing infrastructure) |
| **ML Approach** | Ensemble methods (Isolation Forest + LSTM + Statistical) |
| **Scoring Model** | ART-based with 5 dimensions (30% Test Success, 25% Performance, 20% Resources, 15% Errors, 10% Stability) |
| **Forecasting** | 7-day horizon with high accuracy (ARIMA + Prophet + LSTM ensemble) |
| **Test Optimization** | Prod vs PTE analysis, edge case detection, workload pattern comparison |
| **UI/UX** | Single-page dashboard, remote machine access |
| **Backend** | FastAPI + Redis + Scikit-learn + TensorFlow |
| **Frontend** | React + TypeScript |
| **LLM Integration** | Anthropic Claude API (for RCA narratives) |
| **Network** | Office network with internet access |
| **Deployment** | Can run from remote machines |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                │
├─────────────────────────────────────────────────────────────────┤
│  • Kibana API (Real-time: API, pass/fail, response times)      │
│  • LoadRunner (Batch CSV: transactions → API mappings)          │
│  • AppDynamics (API/JSON: CPU, Memory, GC, exceptions)         │
│  • Production Logs (Files: endpoint, status, response times)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DATA INGESTION LAYER                           │
│  FastAPI Endpoints + Background Workers                          │
│  • Data validation & cleansing                                   │
│  • Timestamp normalization (EST timezone)                        │
│  • Schema mapping & transformation                               │
│  • Missing value imputation                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ORACLE DATABASE                               │
│  Tables:                                                         │
│  ├─ test_results (PTE: API, pass/fail, response_time)          │
│  ├─ loadrunner_transactions (transaction, APIs, metrics)        │
│  ├─ appd_metrics (CPU, memory, GC, exceptions, timestamp)      │
│  ├─ prod_logs (endpoint, status, response_time, timestamp)     │
│  ├─ anomalies (detected anomalies, severity, confidence)       │
│  ├─ rca_results (primary cause, timeline, narrative)           │
│  ├─ health_scores (ART, overall, components, timestamp)        │
│  ├─ predictions (metric, forecast, confidence intervals)       │
│  ├─ test_optimization (recommendations, impact, status)        │
│  └─ prod_pte_comparison (coverage gaps, workload similarity)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ML/AI ANALYTICS ENGINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ANOMALY DETECTION ENSEMBLE                                   │
│     ├─ Isolation Forest (multivariate anomalies)               │
│     │   • Contamination: 10%                                    │
│     │   • N_estimators: 100                                     │
│     │   • Weight: 35%                                           │
│     ├─ LSTM Autoencoder (temporal patterns)                     │
│     │   • Architecture: 64→32→16→32→64                         │
│     │   • Reconstruction threshold: MSE > 0.05                  │
│     │   • Weight: 35%                                           │
│     ├─ Statistical (Z-score, IQR)                               │
│     │   • Z-score threshold: 3.0                                │
│     │   • Weight: 30%                                           │
│     └─ Ensemble Voter                                           │
│         • Agreement threshold: 70%                              │
│         • Confidence = weighted votes                           │
│                                                                  │
│  2. ROOT CAUSE ANALYSIS (Multi-Stage)                           │
│     ├─ Stage 1: Correlation Matrix                              │
│     │   • Pearson (linear relationships)                        │
│     │   • Spearman (monotonic relationships)                    │
│     │   • Mutual Information (non-linear)                       │
│     ├─ Stage 2: Causal Inference                                │
│     │   • Granger Causality Test (temporal precedence)         │
│     │   • Max lag: 15 minutes                                   │
│     │   • Significance level: 0.05                              │
│     ├─ Stage 3: Feature Importance                              │
│     │   • SHAP values (explain ML predictions)                 │
│     │   • Decision tree rules (interpretable)                   │
│     ├─ Stage 4: LLM Narrative Generation                        │
│     │   • Anthropic Claude Sonnet 4                             │
│     │   • Structured data → Natural language                    │
│     │   • Context-aware explanations                            │
│     │   • Actionable recommendations                            │
│     └─ Output: Primary cause + timeline + narrative             │
│                                                                  │
│  3. ART-BASED HEALTH SCORING                                     │
│     Formula: Σ(Component_Score × Weight)                        │
│     ├─ Test Success Score (30%)                                 │
│     │   • Pass rate vs baseline                                 │
│     │   • Penalty for below baseline (up to 50%)               │
│     │   • Bonus for consistency (up to 20%)                     │
│     ├─ Performance Score (25%)                                  │
│     │   • P95 response time vs baseline                         │
│     │   • 100 if ≤ baseline                                     │
│     │   • Degradation penalty: -100 per 50% increase           │
│     ├─ Resource Health Score (20%)                              │
│     │   • CPU: optimal <50%, critical >90%                      │
│     │   • Memory: optimal <70%, critical >85%                   │
│     │   • GC time: optimal <100ms, critical >500ms             │
│     ├─ Error Rate Score (15%)                                   │
│     │   • Exception rate vs baseline                            │
│     │   • HTTP 5xx rate vs baseline                             │
│     └─ Stability Score (10%)                                    │
│         • Anomaly frequency (0=100, 5+=0)                       │
│         • Variance in metrics                                   │
│                                                                  │
│     Grades: A(90-100), B(80-89), C(70-79), D(60-69), F(<60)   │
│                                                                  │
│  4. TREND FORECASTING (7-day horizon)                            │
│     ├─ ARIMA (statsmodels)                                      │
│     │   • Auto ARIMA for parameter selection                    │
│     │   • Weight: 25%                                           │
│     ├─ Prophet (Facebook)                                       │
│     │   • Handles weekly seasonality                            │
│     │   • Holiday effects                                       │
│     │   • Weight: 35%                                           │
│     ├─ LSTM (TensorFlow)                                        │
│     │   • Sequence length: 14 days                              │
│     │   • Hidden units: 50                                      │
│     │   • Weight: 40%                                           │
│     └─ Ensemble with Confidence Intervals                       │
│         • Weighted average predictions                          │
│         • 95% confidence bounds                                 │
│         • Model agreement score                                 │
│                                                                  │
│  5. TEST OPTIMIZATION                                            │
│     ├─ Prod vs PTE Coverage Analysis                            │
│     │   • Endpoint overlap detection                            │
│     │   • Traffic pattern comparison                            │
│     │   • Error scenario coverage                               │
│     ├─ Edge Case Detection                                      │
│     │   • Scenarios in prod not in PTE                          │
│     │   • Rare failure patterns                                 │
│     │   • Boundary condition testing gaps                       │
│     ├─ Workload Pattern Comparison                              │
│     │   • Request distribution similarity                       │
│     │   • Load patterns (peak vs normal)                        │
│     │   • User behavior patterns                                │
│     ├─ Test Redundancy Detection                                │
│     │   • Tests with 100% correlation                           │
│     │   • Time savings calculation                              │
│     ├─ Flakiness Detection                                      │
│     │   • Tests with <85% consistency                           │
│     │   • Intermittent failure patterns                         │
│     └─ Suite Upgrade Recommendations                            │
│         • Based on prod issues not caught                       │
│         • Prioritized by business impact                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   REDIS CACHE LAYER                              │
│  • Real-time metrics (TTL: 5 min)                               │
│  • Computed health scores (TTL: 15 min)                         │
│  • Anomaly alerts (TTL: 1 hour)                                 │
│  • API response cache (TTL: 2 min)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI REST API (Port 8000)                   │
│  Endpoints:                                                      │
│  ├─ GET  /api/health                                            │
│  ├─ GET  /api/dashboard/summary?days={N}&art={name}            │
│  ├─ GET  /api/anomalies?days={N}&severity={level}              │
│  ├─ POST /api/anomalies/detect                                  │
│  ├─ GET  /api/rca/{anomaly_id}                                 │
│  ├─ GET  /api/health-scores/{art}?days={N}                     │
│  ├─ GET  /api/forecasts/{art}?metric={name}&horizon={days}    │
│  ├─ GET  /api/test-optimization?days={N}                       │
│  └─ GET  /api/prod-vs-pte?days={N}                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               REACT SINGLE-PAGE DASHBOARD                        │
│  Components:                                                     │
│  ├─ Header (ART selector, time range, refresh)                 │
│  ├─ Health Score Overview                                       │
│  │   • Overall score gauge (0-100)                              │
│  │   • Grade indicator (A-F)                                    │
│  │   • Component breakdown (5 dimensions)                       │
│  │   • Trend arrows (↑↓→)                                       │
│  ├─ Real-time Anomaly Timeline                                  │
│  │   • Interactive time-series chart                            │
│  │   • Severity color-coded markers                             │
│  │   • Click for RCA details                                    │
│  │   • Hover for quick summary                                  │
│  ├─ RCA Viewer (Modal/Side Panel)                               │
│  │   • Primary cause with confidence                            │
│  │   • Contributing factors tree                                │
│  │   • Event timeline                                           │
│  │   • LLM narrative                                            │
│  │   • Action recommendations                                   │
│  ├─ 7-Day Forecast Charts                                       │
│  │   • Failure rate prediction                                  │
│  │   • Response time prediction                                 │
│  │   • Confidence bands (shaded area)                           │
│  │   • Model agreement indicator                                │
│  ├─ Test Optimization Panel                                     │
│  │   • Recommendations list (prioritized)                       │
│  │   • Time savings calculator                                  │
│  │   • Coverage gap visualizations                              │
│  │   • Accept/Reject actions                                    │
│  └─ Prod vs PTE Comparison                                      │
│      • Endpoint coverage matrix                                 │
│      • Traffic pattern comparison                               │
│      • Workload similarity score                                │
│      • Edge cases not covered                                   │
│                                                                  │
│  Features:                                                       │
│  • Responsive design (works on remote machines)                 │
│  • WebSocket updates (real-time data)                           │
│  • Time range filters: 1h / 6h / 1d / 7d / 30d                │
│  • ART dropdown with search                                     │
│  • Dark theme (easier on eyes)                                  │
│  • Export buttons (future: PDF, CSV)                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema (Oracle)

### **Complete Table Definitions:**

```sql
-- 1. Test Results (PTE Data from Kibana)
CREATE TABLE test_results (
    id NUMBER PRIMARY KEY,
    test_date DATE NOT NULL,
    art VARCHAR2(100) NOT NULL,
    api VARCHAR2(500) NOT NULL,
    pass_count NUMBER DEFAULT 0,
    fail_count NUMBER DEFAULT 0,
    p50_response_time NUMBER,
    p95_response_time NUMBER,
    p99_response_time NUMBER,
    execution_time NUMBER,
    http_status_codes CLOB,  -- JSON: {"200": 450, "400": 5, "500": 50}
    exceptions CLOB,          -- JSON: {"NullPointerException": 5, "TimeoutException": 10}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_test_results_date ON test_results(test_date);
CREATE INDEX idx_test_results_art ON test_results(art);
CREATE INDEX idx_test_results_api ON test_results(api);
CREATE INDEX idx_test_results_date_art ON test_results(test_date, art);

-- 2. LoadRunner Transactions
CREATE TABLE loadrunner_transactions (
    id NUMBER PRIMARY KEY,
    test_date DATE NOT NULL,
    transaction_name VARCHAR2(200) NOT NULL,
    apis CLOB,                -- JSON: ["api1", "api2", "api3"]
    pass_count NUMBER DEFAULT 0,
    fail_count NUMBER DEFAULT 0,
    avg_response_time NUMBER,
    p90_response_time NUMBER,
    throughput NUMBER,        -- Transactions per second
    user_load NUMBER,         -- Virtual users
    think_time NUMBER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lr_date ON loadrunner_transactions(test_date);
CREATE INDEX idx_lr_transaction ON loadrunner_transactions(transaction_name);

-- 3. AppDynamics Metrics
CREATE TABLE appd_metrics (
    id NUMBER PRIMARY KEY,
    metric_time TIMESTAMP NOT NULL,
    art VARCHAR2(100),
    cpu_usage NUMBER,         -- Percentage (0-100)
    memory_heap NUMBER,       -- MB
    memory_non_heap NUMBER,   -- MB
    gc_time NUMBER,           -- Milliseconds per interval
    gc_count NUMBER,          -- GC cycles
    stall_count NUMBER,       -- Blocked threads
    exception_count NUMBER,
    db_conn_pool_usage NUMBER, -- Percentage
    thread_count NUMBER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_appd_time ON appd_metrics(metric_time);
CREATE INDEX idx_appd_art ON appd_metrics(art);
CREATE INDEX idx_appd_time_art ON appd_metrics(metric_time, art);

-- 4. Production Logs
CREATE TABLE prod_logs (
    id NUMBER PRIMARY KEY,
    log_time TIMESTAMP NOT NULL,
    endpoint VARCHAR2(500) NOT NULL,
    http_status NUMBER,
    response_time NUMBER,     -- Milliseconds
    exception_type VARCHAR2(200),
    request_count NUMBER DEFAULT 1,
    user_agent VARCHAR2(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prod_logs_time ON prod_logs(log_time);
CREATE INDEX idx_prod_logs_endpoint ON prod_logs(endpoint);
CREATE INDEX idx_prod_logs_status ON prod_logs(http_status);

-- 5. Detected Anomalies
CREATE TABLE anomalies (
    id NUMBER PRIMARY KEY,
    detected_at TIMESTAMP NOT NULL,
    art VARCHAR2(100),
    anomaly_type VARCHAR2(50),  -- 'multivariate', 'temporal', 'statistical'
    severity VARCHAR2(20),       -- 'low', 'medium', 'high', 'critical'
    confidence NUMBER,           -- 0.0 to 1.0
    affected_metrics CLOB,       -- JSON: ["cpu_usage", "response_time", "memory"]
    features CLOB,               -- JSON: all feature values at detection time
    is_resolved NUMBER(1) DEFAULT 0,
    resolved_at TIMESTAMP,
    resolution_notes VARCHAR2(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anomalies_date ON anomalies(detected_at);
CREATE INDEX idx_anomalies_art ON anomalies(art);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_resolved ON anomalies(is_resolved);

-- 6. RCA Results
CREATE TABLE rca_results (
    id NUMBER PRIMARY KEY,
    anomaly_id NUMBER REFERENCES anomalies(id),
    primary_cause VARCHAR2(200),
    primary_cause_confidence NUMBER,  -- 0.0 to 1.0
    contributing_factors CLOB,        -- JSON array of factors
    correlation_scores CLOB,          -- JSON: correlation matrix
    causal_graph CLOB,                -- JSON: Granger causality results
    timeline CLOB,                    -- JSON array of events
    narrative CLOB,                   -- LLM generated explanation
    recommendations CLOB,             -- JSON array of actions
    analysis_duration_sec NUMBER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rca_anomaly ON rca_results(anomaly_id);

-- 7. ART Health Scores
CREATE TABLE health_scores (
    id NUMBER PRIMARY KEY,
    score_date DATE NOT NULL,
    art VARCHAR2(100) NOT NULL,
    overall_score NUMBER,            -- 0-100
    test_success_score NUMBER,
    performance_score NUMBER,
    resource_score NUMBER,
    error_rate_score NUMBER,
    stability_score NUMBER,
    grade VARCHAR2(1),               -- A, B, C, D, F
    trend_direction VARCHAR2(20),    -- 'improving', 'degrading', 'stable'
    trend_percentage NUMBER,         -- +5.2 or -3.1
    risk_level VARCHAR2(20),         -- 'low', 'medium', 'high', 'critical'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_health_date ON health_scores(score_date);
CREATE INDEX idx_health_art ON health_scores(art);
CREATE INDEX idx_health_date_art ON health_scores(score_date, art);

-- 8. Predictions/Forecasts
CREATE TABLE predictions (
    id NUMBER PRIMARY KEY,
    prediction_date DATE NOT NULL,
    art VARCHAR2(100),
    metric_name VARCHAR2(100),       -- 'failure_rate', 'response_time', 'error_rate'
    horizon_days NUMBER,              -- 1-7
    predicted_values CLOB,            -- JSON: [day1, day2, ..., day7]
    confidence_lower CLOB,            -- JSON: lower bounds
    confidence_upper CLOB,            -- JSON: upper bounds
    model_agreement NUMBER,           -- 0.0 to 1.0
    accuracy_score NUMBER,            -- Historical MAPE
    model_weights CLOB,               -- JSON: {"arima": 0.25, "prophet": 0.35, "lstm": 0.40}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pred_date ON predictions(prediction_date);
CREATE INDEX idx_pred_art ON predictions(art);

-- 9. Test Optimization Recommendations
CREATE TABLE test_optimization (
    id NUMBER PRIMARY KEY,
    analysis_date DATE NOT NULL,
    recommendation_type VARCHAR2(50),  -- 'redundancy', 'coverage_gap', 'flakiness', 'edge_case'
    impact VARCHAR2(20),               -- 'high', 'medium', 'low'
    description CLOB,
    affected_tests CLOB,               -- JSON array
    evidence CLOB,                     -- JSON: supporting data
    time_savings_min NUMBER,
    confidence NUMBER,                 -- 0.0 to 1.0
    status VARCHAR2(20) DEFAULT 'pending',  -- 'pending', 'accepted', 'rejected', 'implemented'
    status_notes VARCHAR2(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_opt_date ON test_optimization(analysis_date);
CREATE INDEX idx_opt_type ON test_optimization(recommendation_type);
CREATE INDEX idx_opt_status ON test_optimization(status);

-- 10. Prod vs PTE Comparison
CREATE TABLE prod_pte_comparison (
    id NUMBER PRIMARY KEY,
    comparison_date DATE NOT NULL,
    endpoint VARCHAR2(500) NOT NULL,
    prod_request_count NUMBER,
    pte_test_count NUMBER,
    prod_avg_response NUMBER,
    pte_avg_response NUMBER,
    prod_p95 NUMBER,
    pte_p95 NUMBER,
    prod_error_rate NUMBER,
    pte_error_rate NUMBER,
    workload_similarity NUMBER,       -- 0.0 to 1.0 score
    coverage_gap CLOB,                -- JSON: scenarios in prod not in PTE
    traffic_pattern_diff CLOB,        -- JSON: peak hours, load distribution
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comparison_date ON prod_pte_comparison(comparison_date);
CREATE INDEX idx_comparison_endpoint ON prod_pte_comparison(endpoint);

-- Create sequences for primary keys
CREATE SEQUENCE seq_test_results START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_lr_transactions START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_appd_metrics START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_prod_logs START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_anomalies START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_rca_results START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_health_scores START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_predictions START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_test_optimization START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_prod_pte_comparison START WITH 1 INCREMENT BY 1;
```

---

## 🧠 ML/AI Algorithms - Implementation Details

### **Feature Engineering:**

```python
# Input Features for Anomaly Detection (30+ dimensions)

FEATURES = {
    # 1. Test Metrics
    'failure_rate_current': float,
    'failure_rate_5min_avg': float,
    'failure_rate_1hour_avg': float,
    'response_time_p50': float,
    'response_time_p95': float,
    'response_time_p99': float,
    'throughput': float,
    'test_duration': float,
    'failure_rate_trend': float,  # delta from previous hour
    
    # 2. System Metrics
    'cpu_usage_current': float,
    'cpu_usage_avg': float,
    'cpu_usage_max': float,
    'cpu_usage_stddev': float,
    'memory_heap_current': float,
    'memory_heap_avg': float,
    'memory_heap_max': float,
    'memory_heap_growth_rate': float,
    'memory_non_heap_current': float,
    'gc_time_total': float,
    'gc_frequency': float,
    'gc_avg_duration': float,
    'gc_time_percentage': float,  # gc_time / total_time
    'thread_count_total': int,
    'thread_count_stalled': int,
    'thread_count_blocked': int,
    
    # 3. Error Patterns
    'exception_count_total': int,
    'http_5xx_count': int,
    'http_4xx_count': int,
    'timeout_count': int,
    'error_rate_current': float,
    'error_rate_trend': float,
    
    # 4. Temporal Features (cyclical encoding)
    'hour_of_day_sin': float,
    'hour_of_day_cos': float,
    'day_of_week_sin': float,
    'day_of_week_cos': float,
    'is_peak_hour': int,  # binary
    'time_since_deployment': float,  # hours
    'test_run_sequence': int,
    
    # 5. Correlation Features
    'cpu_memory_correlation': float,
    'response_time_cpu_correlation': float,
    'failure_gc_correlation': float,
    'lag_1min': dict,  # t-1 features
    'lag_5min': dict,  # t-5 features
    'lag_15min': dict  # t-15 features
}
```

---

## 🎯 Implementation Timeline (4 Weeks)

### **Week 1: Foundation & Data Pipeline**

**Days 1-2:** Setup
- Oracle DB schema creation
- FastAPI project structure
- Database connection manager with python-oracledb
- Redis setup and configuration

**Days 3-4:** Data Ingestion
- Kibana API connector (handle localhost:8609/ttselk)
- LoadRunner CSV parser
- AppDynamics API client
- Production log ingester

**Days 5-7:** Basic Analytics
- Statistical anomaly detection (Z-score, IQR)
- Basic health scoring logic
- Simple forecasting (linear regression baseline)
- FastAPI endpoints setup

**Deliverable:** Working backend with basic analytics

---

### **Week 2: ML/AI Core**

**Days 8-10:** Anomaly Detection Ensemble
- Isolation Forest implementation
- LSTM Autoencoder training pipeline
- Ensemble voting logic
- Model persistence and loading

**Days 11-12:** RCA Framework
- Correlation analysis (Pearson, Spearman, MI)
- Granger causality testing
- SHAP feature importance
- Anthropic Claude API integration for narratives

**Days 13-14:** ART-Based Health Scoring
- Component score calculations
- Weighted scoring formula
- Trend analysis logic
- Grade assignment (A-F)

**Deliverable:** Complete ML/AI engine

---

### **Week 3: Advanced Features & UI**

**Days 15-17:** Forecasting & Optimization
- ARIMA implementation (auto parameter selection)
- Prophet integration (seasonality, holidays)
- LSTM forecaster
- Ensemble predictions with confidence intervals
- Test optimizer (prod vs PTE analysis)

**Days 18-21:** React Dashboard
- Project setup (Create React App + TypeScript)
- Component architecture
- API service layer
- Chart components (Recharts/Chart.js)
- WebSocket real-time updates
- Responsive design

**Deliverable:** Working dashboard with all features

---

### **Week 4: Integration, Testing & Deployment**

**Days 22-24:** Integration & Testing
- End-to-end testing
- Performance optimization
- Redis caching implementation
- Error handling improvements
- Load testing

**Days 25-27:** Deployment & Documentation
- Deployment scripts
- Configuration management (.env files)
- User documentation
- API documentation (Swagger/OpenAPI)
- Training materials

**Day 28:** Final Review & Handoff
- Demo presentation
- Knowledge transfer
- Production deployment

**Deliverable:** Production-ready system

---

## 📁 Project Structure

```
cicd-advanced-analytics/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Configuration
│   │   ├── database.py             # Oracle connection
│   │   ├── models.py               # Pydantic models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── dashboard.py
│   │   │   ├── anomalies.py
│   │   │   ├── rca.py
│   │   │   ├── forecasts.py
│   │   │   └── optimization.py
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── anomaly_detection.py
│   │   │   ├── health_scoring.py
│   │   │   ├── rca_analyzer.py
│   │   │   ├── forecaster.py
│   │   │   └── test_optimizer.py
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── kibana_connector.py
│   │   │   ├── loadrunner_parser.py
│   │   │   ├── appd_connector.py
│   │   │   └── prod_log_parser.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── feature_engineering.py
│   │       ├── data_validation.py
│   │       └── cache.py
│   ├── models/                     # Trained ML models
│   │   ├── anomaly/
│   │   │   ├── isolation_forest.pkl
│   │   │   ├── lstm_autoencoder.h5
│   │   │   └── scaler.pkl
│   │   └── forecaster/
│   │       ├── arima_models.pkl
│   │       ├── prophet_models.pkl
│   │       └── lstm_forecaster.h5
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── HealthScoreCard.tsx
│   │   │   ├── AnomalyTimeline.tsx
│   │   │   ├── RCAViewer.tsx
│   │   │   ├── ForecastChart.tsx
│   │   │   ├── OptimizationPanel.tsx
│   │   │   └── ProdVsPTEComparison.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── utils/
│   │   │   └── helpers.ts
│   │   ├── App.tsx
│   │   ├── index.tsx
│   │   └── config.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
│
├── database/
│   ├── schema.sql                  # Complete Oracle schema
│   ├── views.sql                   # Useful database views
│   ├── sample_data.sql             # Test data
│   └── migrations/
│
├── deployment/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   └── deploy.sh
│
├── docs/
│   ├── API.md                      # API documentation
│   ├── SETUP.md                    # Setup instructions
│   ├── ARCHITECTURE.md             # This document
│   └── USER_GUIDE.md               # End-user guide
│
└── tests/
    ├── backend/
    │   ├── test_anomaly_detection.py
    │   ├── test_health_scoring.py
    │   └── test_api.py
    └── frontend/
        └── Dashboard.test.tsx
```

---

## 💻 Key Implementation Code Snippets

### **1. Database Connection Manager (database.py)**

```python
import oracledb
import logging
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class OracleConnectionManager:
    """Manages Oracle database connections using python-oracledb"""
    
    def __init__(self, config: dict):
        self.config = config
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            # Thin mode (no Oracle Client required)
            self.pool = oracledb.create_pool(
                user=self.config['user'],
                password=self.config['password'],
                dsn=self.config['dsn'],
                min=2,
                max=10,
                increment=1,
                threaded=True
            )
            logger.info("Oracle connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool (context manager)"""
        conn = None
        try:
            conn = self.pool.acquire()
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.pool.release(conn)
    
    def execute_query(self, query: str, params: Optional[dict] = None):
        """Execute SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or {})
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    
    def execute_dml(self, query: str, params: Optional[dict] = None):
        """Execute INSERT/UPDATE/DELETE"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or {})
            conn.commit()
            return cursor.rowcount
    
    def close(self):
        """Close connection pool"""
        if self.pool:
            self.pool.close()
            logger.info("Connection pool closed")
```

---

### **2. Anomaly Detection Ensemble (anomaly_detection.py)**

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from tensorflow import keras
import pickle
import logging

logger = logging.getLogger(__name__)

class AnomalyDetectionEnsemble:
    """Ensemble anomaly detector using Isolation Forest + LSTM + Statistical"""
    
    def __init__(self, config: dict):
        self.config = config
        self.scaler = StandardScaler()
        self.isolation_forest = None
        self.lstm_autoencoder = None
        self.weights = {
            'isolation_forest': 0.35,
            'lstm_autoencoder': 0.35,
            'statistical': 0.30
        }
    
    def train(self, X_train: np.ndarray):
        """Train all anomaly detection models"""
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_train)
        
        # 1. Train Isolation Forest
        logger.info("Training Isolation Forest...")
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            n_estimators=100,
            random_state=42
        )
        self.isolation_forest.fit(X_scaled)
        
        # 2. Train LSTM Autoencoder
        logger.info("Training LSTM Autoencoder...")
        self.lstm_autoencoder = self._build_lstm_autoencoder(X_train.shape[1])
        
        # Reshape for LSTM (samples, timesteps, features)
        X_lstm = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])
        
        self.lstm_autoencoder.fit(
            X_lstm, X_lstm,
            epochs=50,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        logger.info("Training complete")
    
    def _build_lstm_autoencoder(self, input_dim: int):
        """Build LSTM autoencoder architecture"""
        model = keras.Sequential([
            keras.layers.LSTM(64, activation='relu', input_shape=(1, input_dim), return_sequences=True),
            keras.layers.LSTM(32, activation='relu', return_sequences=True),
            keras.layers.LSTM(16, activation='relu', return_sequences=True),
            keras.layers.LSTM(32, activation='relu', return_sequences=True),
            keras.layers.LSTM(64, activation='relu', return_sequences=True),
            keras.layers.TimeDistributed(keras.layers.Dense(input_dim))
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def detect(self, X_new: np.ndarray) -> dict:
        """Detect anomalies using ensemble voting"""
        
        X_scaled = self.scaler.transform(X_new)
        
        # 1. Isolation Forest predictions
        if_scores = self.isolation_forest.decision_function(X_scaled)
        if_anomalies = (if_scores < 0).astype(int)
        
        # 2. LSTM Autoencoder predictions
        X_lstm = X_scaled.reshape(X_scaled.shape[0], 1, X_scaled.shape[1])
        reconstructions = self.lstm_autoencoder.predict(X_lstm, verbose=0)
        mse = np.mean(np.square(X_lstm - reconstructions), axis=(1, 2))
        lstm_anomalies = (mse > 0.05).astype(int)
        
        # 3. Statistical predictions (Z-score)
        z_scores = np.abs((X_scaled - np.mean(X_scaled, axis=0)) / np.std(X_scaled, axis=0))
        stat_anomalies = (np.max(z_scores, axis=1) > 3.0).astype(int)
        
        # Ensemble voting
        votes = (
            if_anomalies * self.weights['isolation_forest'] +
            lstm_anomalies * self.weights['lstm_autoencoder'] +
            stat_anomalies * self.weights['statistical']
        )
        
        # Anomaly if weighted vote > 0.7
        is_anomaly = (votes > 0.7).astype(int)
        
        # Confidence = weighted vote score
        confidence = np.clip(votes, 0, 1)
        
        # Determine severity based on confidence
        severity = []
        for conf in confidence:
            if conf >= 0.9:
                severity.append('critical')
            elif conf >= 0.8:
                severity.append('high')
            elif conf >= 0.7:
                severity.append('medium')
            else:
                severity.append('low')
        
        return {
            'is_anomaly': is_anomaly,
            'confidence': confidence,
            'severity': severity,
            'if_scores': if_scores,
            'lstm_mse': mse,
            'stat_z_scores': np.max(z_scores, axis=1)
        }
    
    def save_models(self, path: str):
        """Save trained models"""
        with open(f"{path}/isolation_forest.pkl", 'wb') as f:
            pickle.dump(self.isolation_forest, f)
        
        with open(f"{path}/scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        self.lstm_autoencoder.save(f"{path}/lstm_autoencoder.h5")
        
        logger.info(f"Models saved to {path}")
    
    def load_models(self, path: str):
        """Load trained models"""
        with open(f"{path}/isolation_forest.pkl", 'rb') as f:
            self.isolation_forest = pickle.load(f)
        
        with open(f"{path}/scaler.pkl", 'rb') as f:
            self.scaler = pickle.load(f)
        
        self.lstm_autoencoder = keras.models.load_model(f"{path}/lstm_autoencoder.h5")
        
        logger.info(f"Models loaded from {path}")
```

---

### **3. Health Scoring Engine (health_scoring.py)**

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ARTHealthScorer:
    """Calculate ART-based health scores with 5 dimensions"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.weights = {
            'test_success': 0.30,
            'performance': 0.25,
            'resource': 0.20,
            'error_rate': 0.15,
            'stability': 0.10
        }
    
    def calculate_health_score(self, art: str, days: int = 1) -> dict:
        """Calculate comprehensive health score for an ART"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch data
        test_data = self._fetch_test_data(art, start_date, end_date)
        appd_data = self._fetch_appd_data(art, start_date, end_date)
        anomaly_data = self._fetch_anomaly_data(art, start_date, end_date)
        baseline_data = self._fetch_baseline_data(art)
        
        # Calculate component scores
        test_success_score = self._calculate_test_success_score(test_data, baseline_data)
        performance_score = self._calculate_performance_score(test_data, baseline_data)
        resource_score = self._calculate_resource_score(appd_data)
        error_rate_score = self._calculate_error_rate_score(test_data, baseline_data)
        stability_score = self._calculate_stability_score(anomaly_data, test_data)
        
        # Overall weighted score
        overall_score = (
            test_success_score * self.weights['test_success'] +
            performance_score * self.weights['performance'] +
            resource_score * self.weights['resource'] +
            error_rate_score * self.weights['error_rate'] +
            stability_score * self.weights['stability']
        )
        
        # Assign grade
        grade = self._assign_grade(overall_score)
        
        # Calculate trend
        trend_info = self._calculate_trend(art, overall_score)
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score, anomaly_data)
        
        return {
            'art': art,
            'overall_score': round(overall_score, 2),
            'grade': grade,
            'components': {
                'test_success': round(test_success_score, 2),
                'performance': round(performance_score, 2),
                'resource': round(resource_score, 2),
                'error_rate': round(error_rate_score, 2),
                'stability': round(stability_score, 2)
            },
            'trend_direction': trend_info['direction'],
            'trend_percentage': trend_info['percentage'],
            'risk_level': risk_level,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_test_success_score(self, test_data: pd.DataFrame, baseline: dict) -> float:
        """Calculate test success score (30% weight)"""
        if test_data.empty:
            return 0.0
        
        current_pass_rate = test_data['pass_count'].sum() / (
            test_data['pass_count'].sum() + test_data['fail_count'].sum()
        )
        
        baseline_pass_rate = baseline.get('pass_rate', 0.95)
        
        # Base score
        score = (current_pass_rate / baseline_pass_rate) * 100
        
        # Penalty for below baseline (up to 50%)
        if current_pass_rate < baseline_pass_rate:
            penalty = (baseline_pass_rate - current_pass_rate) * 50
            score -= penalty
        
        # Bonus for consistency (up to 20%)
        pass_rate_std = test_data.groupby('test_date')['pass_count'].sum().std()
        if pass_rate_std < 0.05:
            score += 20
        
        return max(0, min(100, score))
    
    def _calculate_performance_score(self, test_data: pd.DataFrame, baseline: dict) -> float:
        """Calculate performance score (25% weight)"""
        if test_data.empty:
            return 0.0
        
        current_p95 = test_data['p95_response_time'].mean()
        baseline_p95 = baseline.get('p95_response_time', 1000)
        
        if current_p95 <= baseline_p95:
            return 100.0
        
        # Degradation penalty: -100 per 50% increase
        degradation = (current_p95 - baseline_p95) / baseline_p95
        score = 100 - (degradation * 200)
        
        return max(0, min(100, score))
    
    def _calculate_resource_score(self, appd_data: pd.DataFrame) -> float:
        """Calculate resource health score (20% weight)"""
        if appd_data.empty:
            return 100.0  # No data = assume healthy
        
        # CPU score
        avg_cpu = appd_data['cpu_usage'].mean()
        if avg_cpu < 50:
            cpu_score = 100
        elif avg_cpu < 90:
            cpu_score = 100 - ((avg_cpu - 50) * 2.5)  # Linear decline
        else:
            cpu_score = 0
        
        # Memory score
        avg_memory = appd_data['memory_heap'].mean()
        memory_limit = appd_data['memory_heap'].max() * 0.85  # 85% threshold
        
        if avg_memory < memory_limit * 0.7:
            memory_score = 100
        elif avg_memory < memory_limit:
            memory_score = 100 - ((avg_memory - memory_limit * 0.7) / memory_limit * 100)
        else:
            memory_score = 0
        
        # GC score
        avg_gc_time = appd_data['gc_time'].mean()
        if avg_gc_time < 100:
            gc_score = 100
        elif avg_gc_time < 500:
            gc_score = 100 - ((avg_gc_time - 100) / 400 * 100)
        else:
            gc_score = 0
        
        # Weighted resource score
        resource_score = (cpu_score * 0.4 + memory_score * 0.4 + gc_score * 0.2)
        
        return max(0, min(100, resource_score))
    
    def _calculate_error_rate_score(self, test_data: pd.DataFrame, baseline: dict) -> float:
        """Calculate error rate score (15% weight)"""
        if test_data.empty:
            return 100.0
        
        # Exception rate
        current_exceptions = test_data['exceptions'].apply(
            lambda x: sum(eval(x).values()) if x else 0
        ).sum()
        
        total_requests = test_data['pass_count'].sum() + test_data['fail_count'].sum()
        current_exception_rate = current_exceptions / total_requests if total_requests > 0 else 0
        
        baseline_exception_rate = baseline.get('exception_rate', 0.01)
        
        # HTTP 5xx rate
        current_5xx = test_data['http_status_codes'].apply(
            lambda x: sum([v for k, v in eval(x).items() if 500 <= int(k) < 600]) if x else 0
        ).sum()
        
        current_5xx_rate = current_5xx / total_requests if total_requests > 0 else 0
        baseline_5xx_rate = baseline.get('5xx_rate', 0.005)
        
        # Score based on both metrics
        exception_score = max(0, 100 - (current_exception_rate / baseline_exception_rate * 100))
        http_5xx_score = max(0, 100 - (current_5xx_rate / baseline_5xx_rate * 100))
        
        error_score = (exception_score * 0.6 + http_5xx_score * 0.4)
        
        return max(0, min(100, error_score))
    
    def _calculate_stability_score(self, anomaly_data: pd.DataFrame, test_data: pd.DataFrame) -> float:
        """Calculate stability score (10% weight)"""
        
        # Anomaly frequency
        anomaly_count = len(anomaly_data)
        if anomaly_count == 0:
            anomaly_score = 100
        elif anomaly_count <= 5:
            anomaly_score = 100 - (anomaly_count * 20)
        else:
            anomaly_score = 0
        
        # Metric variance
        if not test_data.empty:
            response_time_cv = (
                test_data['p95_response_time'].std() / test_data['p95_response_time'].mean()
            )
            variance_score = max(0, 100 - (response_time_cv * 200))
        else:
            variance_score = 100
        
        stability = (anomaly_score * 0.7 + variance_score * 0.3)
        
        return max(0, min(100, stability))
    
    def _assign_grade(self, score: float) -> str:
        """Assign letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _calculate_trend(self, art: str, current_score: float) -> dict:
        """Calculate trend compared to previous period"""
        query = """
            SELECT overall_score 
            FROM health_scores 
            WHERE art = :art 
            AND score_date < TRUNC(SYSDATE)
            ORDER BY score_date DESC 
            FETCH FIRST 1 ROWS ONLY
        """
        
        previous = self.db.execute_query(query, {'art': art})
        
        if not previous:
            return {'direction': 'stable', 'percentage': 0}
        
        prev_score = previous[0]['overall_score']
        diff = current_score - prev_score
        percentage = (diff / prev_score * 100) if prev_score > 0 else 0
        
        if abs(percentage) < 2:
            direction = 'stable'
        elif percentage > 0:
            direction = 'improving'
        else:
            direction = 'degrading'
        
        return {
            'direction': direction,
            'percentage': round(percentage, 2)
        }
    
    def _determine_risk_level(self, score: float, anomaly_data: pd.DataFrame) -> str:
        """Determine risk level"""
        critical_anomalies = len(anomaly_data[anomaly_data['severity'] == 'critical'])
        
        if score < 60 or critical_anomalies > 0:
            return 'critical'
        elif score < 70 or len(anomaly_data) > 3:
            return 'high'
        elif score < 80 or len(anomaly_data) > 1:
            return 'medium'
        else:
            return 'low'
    
    def _fetch_test_data(self, art: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch test results from database"""
        query = """
            SELECT * FROM test_results
            WHERE art = :art
            AND test_date BETWEEN :start_date AND :end_date
            ORDER BY test_date
        """
        
        results = self.db.execute_query(query, {
            'art': art,
            'start_date': start_date,
            'end_date': end_date
        })
        
        return pd.DataFrame(results)
    
    def _fetch_appd_data(self, art: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch AppDynamics metrics"""
        query = """
            SELECT * FROM appd_metrics
            WHERE art = :art
            AND metric_time BETWEEN :start_date AND :end_date
            ORDER BY metric_time
        """
        
        results = self.db.execute_query(query, {
            'art': art,
            'start_date': start_date,
            'end_date': end_date
        })
        
        return pd.DataFrame(results)
    
    def _fetch_anomaly_data(self, art: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch detected anomalies"""
        query = """
            SELECT * FROM anomalies
            WHERE art = :art
            AND detected_at BETWEEN :start_date AND :end_date
            AND is_resolved = 0
            ORDER BY detected_at
        """
        
        results = self.db.execute_query(query, {
            'art': art,
            'start_date': start_date,
            'end_date': end_date
        })
        
        return pd.DataFrame(results)
    
    def _fetch_baseline_data(self, art: str) -> dict:
        """Fetch baseline metrics for comparison"""
        # This would typically come from a baseline table
        # For now, using defaults
        return {
            'pass_rate': 0.95,
            'p95_response_time': 1000,
            'exception_rate': 0.01,
            '5xx_rate': 0.005
        }
```

---

### **4. FastAPI Main Application (main.py)**

```python
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uvicorn
import logging

from app.database import OracleConnectionManager
from app.ml.anomaly_detection import AnomalyDetectionEnsemble
from app.ml.health_scoring import ARTHealthScorer
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CI/CD Advanced Analytics API",
    version="1.0.0",
    description="ML/AI-powered predictive analytics for CI/CD testing"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_manager = OracleConnectionManager(settings.DATABASE_CONFIG)
health_scorer = ARTHealthScorer(db_manager)
anomaly_detector = AnomalyDetectionEnsemble(settings.ML_CONFIG)

# Load trained models
try:
    anomaly_detector.load_models(settings.MODEL_PATH)
    logger.info("ML models loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ML models: {e}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/dashboard/summary")
async def get_dashboard_summary(
    art: str = Query(..., description="ART name"),
    days: int = Query(1, ge=1, le=30, description="Number of days to analyze")
):
    """Get comprehensive dashboard summary"""
    try:
        # Calculate health score
        health_data = health_scorer.calculate_health_score(art, days)
        
        # Get recent anomalies
        anomalies = _get_recent_anomalies(art, days)
        
        # Get forecasts
        forecasts = _get_forecasts(art)
        
        # Get test optimization recommendations
        optimization = _get_optimization_recommendations(days)
        
        return {
            "health_score": health_data,
            "recent_anomalies": anomalies,
            "forecasts": forecasts,
            "optimization": optimization,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anomalies")
async def get_anomalies(
    art: str = Query(None, description="Filter by ART"),
    days: int = Query(7, ge=1, le=90),
    severity: str = Query(None, description="Filter by severity")
):
    """Get detected anomalies"""
    try:
        query = """
            SELECT id, detected_at, art, anomaly_type,
                severity, confidence, affected_metrics
            FROM anomalies
            WHERE detected_at >= :start_date
        """
        params = {'start_date': datetime.now() - timedelta(days=days)}
        
        if art:
            query += " AND art = :art"
            params['art'] = art
        
        if severity:
            query += " AND severity = :severity"
            params['severity'] = severity
        
        query += " ORDER BY detected_at DESC"
        
        anomalies = db_manager.execute_query(query, params)
        
        return {
            "count": len(anomalies),
            "anomalies": anomalies
        }
    except Exception as e:
        logger.error(f"Get anomalies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/anomalies/detect")
async def detect_anomalies(data: dict):
    """Run anomaly detection on new data"""
    try:
        import pandas as pd
        import numpy as np
        
        # Convert input data to feature matrix
        features = _extract_features(data)
        X = np.array([features])
        
        # Detect anomalies
        results = anomaly_detector.detect(X)
        
        # If anomaly detected, store in database
        if results['is_anomaly'][0] == 1:
            _store_anomaly(data, results)
        
        return {
            "is_anomaly": bool(results['is_anomaly'][0]),
            "confidence": float(results['confidence'][0]),
            "severity": results['severity'][0],
            "details": {
                "isolation_forest_score": float(results['if_scores'][0]),
                "lstm_mse": float(results['lstm_mse'][0]),
                "stat_z_score": float(results['stat_z_scores'][0])
            }
        }
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rca/{anomaly_id}")
async def get_root_cause_analysis(anomaly_id: int):
    """Get RCA for a specific anomaly"""
    try:
        query = """
            SELECT r.*, a.detected_at, a.art, a.severity
            FROM rca_results r
            JOIN anomalies a ON r.anomaly_id = a.id
            WHERE r.anomaly_id = :anomaly_id
        """
        
        result = db_manager.execute_query(query, {'anomaly_id': anomaly_id})
        
        if not result:
            raise HTTPException(status_code=404, detail="RCA not found")
        
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get RCA error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health-scores/{art}")
async def get_health_scores(
    art: str,
    days: int = Query(7, ge=1, le=90)
):
    """Get health score history for an ART"""
    try:
        query = """
            SELECT * FROM health_scores
            WHERE art = :art
            AND score_date >= :start_date
            ORDER BY score_date DESC
        """
        
        scores = db_manager.execute_query(query, {
            'art': art,
            'start_date': datetime.now() - timedelta(days=days)
        })
        
        return {
            "art": art,
            "count": len(scores),
            "scores": scores
        }
    except Exception as e:
        logger.error(f"Get health scores error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecasts/{art}")
async def get_forecasts(
    art: str,
    metric: str = Query("failure_rate", description="Metric to forecast"),
    horizon: int = Query(7, ge=1, le=30, description="Forecast horizon in days")
):
    """Get forecasts for a specific metric"""
    try:
        query = """
            SELECT * FROM predictions
            WHERE art = :art
            AND metric_name = :metric
            AND horizon_days = :horizon
            AND prediction_date = TRUNC(SYSDATE)
        """
        
        forecast = db_manager.execute_query(query, {
            'art': art,
            'metric': metric,
            'horizon': horizon
        })
        
        if not forecast:
            # Generate new forecast if not available
            forecast = _generate_forecast(art, metric, horizon)
        else:
            forecast = forecast[0]
        
        return forecast
    except Exception as e:
        logger.error(f"Get forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-optimization")
async def get_test_optimization(
    days: int = Query(7, ge=1, le=30)
):
    """Get test optimization recommendations"""
    try:
        query = """
            SELECT * FROM test_optimization
            WHERE analysis_date >= :start_date
            AND status = 'pending'
            ORDER BY impact DESC, confidence DESC
        """
        
        recommendations = db_manager.execute_query(query, {
            'start_date': datetime.now() - timedelta(days=days)
        })
        
        return {
            "count": len(recommendations),
            "recommendations": recommendations,
            "total_time_savings": sum(r['time_savings_min'] for r in recommendations)
        }
    except Exception as e:
        logger.error(f"Get test optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prod-vs-pte")
async def get_prod_vs_pte_comparison(
    days: int = Query(7, ge=1, le=30)
):
    """Get production vs PTE comparison"""
    try:
        query = """
            SELECT * FROM prod_pte_comparison
            WHERE comparison_date >= :start_date
            ORDER BY workload_similarity ASC, comparison_date DESC
        """
        
        comparisons = db_manager.execute_query(query, {
            'start_date': datetime.now() - timedelta(days=days)
        })
        
        # Calculate summary statistics
        total_endpoints = len(set(c['endpoint'] for c in comparisons))
        low_similarity = len([c for c in comparisons if c['workload_similarity'] < 0.7])
        
        return {
            "total_endpoints": total_endpoints,
            "low_similarity_count": low_similarity,
            "comparisons": comparisons
        }
    except Exception as e:
        logger.error(f"Get prod vs PTE error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def _get_recent_anomalies(art: str, days: int, limit: int = 10):
    """Fetch recent anomalies"""
    query = """
        SELECT 
            id, detected_at, art, anomaly_type,
            severity, confidence, affected_metrics
        FROM anomalies
        WHERE art = :art
        AND detected_at >= :start_date
        AND is_resolved = 0
        ORDER BY detected_at DESC
        FETCH FIRST :limit ROWS ONLY
    """
    
    return db_manager.execute_query(query, {
        'art': art,
        'start_date': datetime.now() - timedelta(days=days),
        'limit': limit
    })


def _get_forecasts(art: str):
    """Fetch latest forecasts"""
    # Implementation similar to get_forecasts endpoint
    pass


def _get_optimization_recommendations(days: int):
    """Fetch test optimization recommendations"""
    # Implementation similar to get_test_optimization endpoint
    pass


def _extract_features(data: dict) -> list:
    """Extract feature vector from input data"""
    # Implementation to convert raw data to feature vector
    pass


def _store_anomaly(data: dict, results: dict):
    """Store detected anomaly in database"""
    # Implementation to insert anomaly record
    pass


def _generate_forecast(art: str, metric: str, horizon: int):
    """Generate new forecast"""
    # Implementation using forecasting models
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    db_manager.close()
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

---

### **5. Requirements.txt**

```txt
# FastAPI and web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# Database
oracledb==2.0.0
sqlalchemy==2.0.23

# Data processing
pandas==2.1.3
numpy==1.24.3

# Machine Learning
scikit-learn==1.3.2
tensorflow==2.15.0
statsmodels==0.14.0
prophet==1.1.5
shap==0.43.0

# Caching and async
redis==5.0.1
aioredis==2.0.1

# LLM Integration
anthropic==0.7.0

# Utilities
python-dotenv==1.0.0
requests==2.31.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Logging and monitoring
loguru==0.7.2
```

---

### **6. Configuration (.env.example)**

```bash
# Database Configuration
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=1521
DB_SERVICE_NAME=ORCL

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Anthropic API (for RCA narratives)
ANTHROPIC_API_KEY=your_api_key_here

# ML Model Configuration
MODEL_PATH=./models
CONTAMINATION_RATE=0.1
LSTM_RECONSTRUCTION_THRESHOLD=0.05

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Kibana Configuration
KIBANA_HOST=localhost
KIBANA_PORT=8609
KIBANA_BASE_PATH=/ttselk

# AppDynamics Configuration
APPD_BASE_URL=https://your-appdynamics-instance
APPD_API_KEY=your_appd_key
```

---

## 🚀 Next Steps

1. **Review this architecture** - Confirm all requirements are met
2. **Start Week 1** - Set up Oracle database and basic data pipeline
3. **Iterative development** - Build, test, and refine each component
4. **Regular check-ins** - Weekly reviews to ensure we're on track

**Ready to start implementation?** Let me know which component you'd like to begin with!
