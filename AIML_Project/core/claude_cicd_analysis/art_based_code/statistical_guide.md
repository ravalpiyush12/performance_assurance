# CI/CD Analysis System - Complete Statistical Logic Guide

## 📊 Statistical Calculations Explained with Examples

---

## 1. Failure Rate Prediction (Linear Regression)

### **What It Does:**
Predicts future failure rates based on historical trends

### **Algorithm:** Linear Regression
**Formula:** `y = mx + b`
- `y` = predicted failure rate
- `m` = slope (trend direction)
- `x` = day number
- `b` = y-intercept

### **How It Works:**

#### **Step 1: Collect Historical Data**
```
Day 0 (7 days ago): 5% failure rate
Day 1 (6 days ago): 6% failure rate  
Day 2 (5 days ago): 7% failure rate
Day 3 (4 days ago): 8% failure rate
Day 4 (3 days ago): 9% failure rate
Day 5 (2 days ago): 10% failure rate
Day 6 (yesterday):  11% failure rate
```

#### **Step 2: Calculate the Trend Line**
Model finds: `y = 1.0x + 5.0`
- Slope (m) = 1.0 (increasing 1% per day)
- Intercept (b) = 5.0

#### **Step 3: Predict Future Values**
```
Day 7 (today):     y = 1.0(7) + 5.0 = 12%
Day 8 (tomorrow):  y = 1.0(8) + 5.0 = 13%
Day 14 (next week): y = 1.0(14) + 5.0 = 19%
```

### **Trend Classification:**
```python
if slope > 0.1:
    trend = "increasing"  # Getting worse
elif slope < -0.1:
    trend = "decreasing"  # Getting better
else:
    trend = "stable"      # No significant change
```

**Example:**
- Slope = 1.5 → "increasing" (failure rate rising fast)
- Slope = -0.8 → "decreasing" (failure rate improving)
- Slope = 0.05 → "stable" (minimal change)

### **Confidence Score (R²):**
Measures how well the model fits the data (0-100%)

**Calculation:** R² = 1 - (Sum of Squared Errors / Total Variance)

**Example:**
```
Perfect linear data: R² = 100% (very confident)
Random scattered data: R² = 30% (low confidence)
```

**Interpretation:**
- 90-100%: Excellent prediction reliability
- 70-89%: Good prediction
- 50-69%: Moderate (data is somewhat random)
- <50%: Poor (predictions unreliable)

### **Minimum Data Requirement:**
**Why 3 days minimum?**
- Need at least 3 points to fit a line
- Less than 3 = insufficient data for trend analysis

**What happens with only 2 days:**
```
Day 1: 5% failures
Day 2: 10% failures
→ Cannot determine if this is a trend or anomaly
→ Returns "insufficient_data" message
```

---

## 2. Daily Failure Rate Calculation

### **Formula:**
```
Failure Rate = (Total Failures / Total Tests) × 100
```

### **Example:**
```
Day 1 Test Results:
- API 1: 50 passes, 5 failures
- API 2: 100 passes, 10 failures
- API 3: 80 passes, 8 failures

Daily Totals:
- Total Passes: 230
- Total Failures: 23
- Total Tests: 253

Failure Rate = (23 / 253) × 100 = 9.09%
```

---

## 3. API/ART Trend Analysis

### **How Trends Are Determined:**

#### **Step 1: Split Data**
```
Recent Period: Last 3 days of data
Older Period: First 3 days of data
```

#### **Step 2: Calculate Average Failure Rates**
```
API: /api/payment/process

Older 3 days:
Day 1: 4% failure
Day 2: 5% failure  
Day 3: 6% failure
Average = (4 + 5 + 6) / 3 = 5%

Recent 3 days:
Day 5: 10% failure
Day 6: 12% failure
Day 7: 14% failure
Average = (10 + 12 + 14) / 3 = 12%
```

#### **Step 3: Compare and Classify**
```python
difference = recent_avg - older_avg
difference = 12% - 5% = 7%

if difference > 2%:
    trend = "increasing"
    severity = "high" if recent_avg > 10% else "medium"
elif difference < -2%:
    trend = "decreasing"
    severity = "low"
else:
    trend = "stable"
    severity = "medium" if recent_avg > 5% else "low"
```

**Result:** Trend = "increasing", Severity = "high"

### **Severity Assignment Logic:**

```
High Severity:
- Failure rate > 10% AND trend is increasing
- Example: 12% failure rate and getting worse

Medium Severity:
- Failure rate 5-10%
- OR stable trend with moderate failures
- Example: 7% failure rate, stable

Low Severity:
- Failure rate < 5%
- OR decreasing trend
- Example: 3% failure rate and improving
```

---

## 4. Performance Degradation Detection

### **How It's Calculated:**

#### **Step 1: Get Baseline**
```
First 3 days average P95 response time:
Day 1: 180ms
Day 2: 200ms
Day 3: 190ms
Baseline = (180 + 200 + 190) / 3 = 190ms
```

#### **Step 2: Get Current Performance**
```
Recent 3 days average:
Day 5: 240ms
Day 6: 260ms
Day 7: 280ms
Current = (240 + 260 + 280) / 3 = 260ms
```

#### **Step 3: Calculate Degradation**
```
Degradation % = ((Current - Baseline) / Baseline) × 100
Degradation % = ((260 - 190) / 190) × 100
Degradation % = (70 / 190) × 100 = 36.84%
```

**Threshold:** > 10% degradation = Performance issue

**Result:** 36.84% > 10% → Flag as degrading performance

### **Rolling Average:**
Uses 3-day rolling window to smooth daily spikes

```
Day 1: 200ms
Day 2: 180ms  → Rolling avg = (200 + 180 + 220)/3 = 200ms
Day 3: 220ms
Day 4: 240ms  → Rolling avg = (180 + 220 + 240)/3 = 213ms
Day 5: 190ms
```

---

## 5. Instability Score Calculation

### **What It Measures:**
How unpredictable and unreliable an API/endpoint is

### **Formula:**
```
Instability Score = (Variance × 0.5) + (Avg_Failures × 0.3) + (|Trend| × 0.2)
```

### **Components:**

#### **1. Variance (50% weight) - Measures Unpredictability**
```
API Failure Rates over 7 days:
[5%, 15%, 3%, 18%, 7%, 20%, 4%]

Step 1: Calculate Mean
Mean = (5+15+3+18+7+20+4) / 7 = 10.29%

Step 2: Calculate Variance
Variance = Average of (each value - mean)²

Differences from mean:
(5-10.29)² = 27.98
(15-10.29)² = 22.19
(3-10.29)² = 53.14
(18-10.29)² = 59.42
(7-10.29)² = 10.82
(20-10.29)² = 94.30
(4-10.29)² = 39.56

Variance = (27.98+22.19+53.14+59.42+10.82+94.30+39.56) / 7 = 43.92

High Variance = Unstable (unpredictable failures)
Low Variance = Stable (consistent behavior)
```

#### **2. Average Failures (30% weight) - Volume of Issues**
```
Daily Failure Counts:
Day 1: 12 failures
Day 2: 35 failures
Day 3: 8 failures
Day 4: 42 failures
Day 5: 15 failures
Day 6: 50 failures
Day 7: 10 failures

Average = (12+35+8+42+15+50+10) / 7 = 24.57 failures
```

#### **3. Failure Trend (20% weight) - Direction of Change**
```
Calculate day-to-day change:
Day 1→2: 35-12 = +23
Day 2→3: 8-35 = -27
Day 3→4: 42-8 = +34
Day 4→5: 15-42 = -27
Day 5→6: 50-15 = +35
Day 6→7: 10-50 = -40

Average change = (23-27+34-27+35-40) / 6 = -0.33
Absolute value = 0.33
```

### **Final Calculation Example:**
```
Instability Score = (43.92 × 0.5) + (24.57 × 0.3) + (0.33 × 0.2)
                  = 21.96 + 7.37 + 0.07
                  = 29.40
```

### **Score Interpretation:**
```
Score > 8.0:   CRITICAL - Highly unstable, immediate action needed
Score 5.0-8.0: MODERATE - Unstable, monitor closely
Score 2.0-5.0: MINOR - Some instability, watch trends
Score < 2.0:   STABLE - Reliable and predictable
```

### **Why This Matters:**

**Stable API Example:**
```
Failure rates: [5%, 5%, 6%, 5%, 5%, 6%, 5%]
Variance: ~0.29 (low)
Avg failures: 3
Score: (0.29×0.5) + (3×0.3) + (0×0.2) = 1.05
→ STABLE - Predictable behavior
```

**Unstable API Example:**
```
Failure rates: [2%, 25%, 1%, 30%, 3%, 28%, 2%]
Variance: ~188.82 (high)
Avg failures: 45
Score: (188.82×0.5) + (45×0.3) + (5×0.2) = 108.91
→ CRITICAL - Unpredictable, requires investigation
```

---

## 6. Why Predictions May Show 0% or "No Prediction"

### **Reasons:**

#### **1. Insufficient Data (Most Common)**
```
Scenario: You selected "Last 2 Days"
Data available: 2 days
Minimum required: 3 days
Result: "Insufficient data for prediction"
```

#### **2. No Variance in Data**
```
All days have exactly 5% failure rate
Model can't learn a trend from flat data
Result: Prediction = 5% (flat line)
```

#### **3. First Time Running**
```
No historical data in database
Need to wait for daily test runs to accumulate
After 3+ days: Predictions will appear
```

#### **4. Data Quality Issues**
```
All tests passed (0 failures every day)
Result: 0% failure rate predicted
This is actually good news!
```

### **How to Get Better Predictions:**

1. **Wait for More Data**
   - Run tests daily for at least 3-5 days
   - More data = better predictions

2. **Use Longer Time Ranges**
   - 7 days: Good for weekly trends
   - 15 days: Better for seasonal patterns
   - 30 days: Best for long-term trends

3. **Ensure Test Consistency**
   - Run tests at same time daily (12-2 PM EST)
   - Use same test suite
   - Consistent environment

---

## 7. Tab-Specific Features

### **Executive View (Tab 1):**
- **Overview of entire system**
- All APIs and ARTs combined
- High-level trends and predictions
- Strategic insights for management

### **ART Specific View (Tab 2):**
- **Drill-down into specific application**
- Shows only selected ART's data
- APIs belonging to that ART
- Detailed tactical insights

**Example:**
```
Executive View shows:
- Total system failure rate: 8%
- 50 APIs across all ARTs

ART View (Payment Module) shows:
- Payment failure rate: 12%
- 5 APIs specific to payments
- Trends within payment system only
```

---

## 8. Real-World Example Walkthrough

### **Scenario: Payment API Investigation**

#### **Day 0-2: Initial Data**
```
Day 0: 100 tests, 5 failures (5%)
Day 1: 100 tests, 8 failures (8%)
Day 2: 100 tests, 12 failures (12%)
```

**Analysis:**
- Not enough data for prediction (need 3+ days)
- Shows "Insufficient data" message

#### **Day 3: First Prediction Available**
```
Day 0: 5%
Day 1: 8%
Day 2: 12%
Day 3: 15%

Model learns: slope = 3.5% increase per day
Prediction for Day 4: 18.5%
Trend: "increasing"
Confidence: 98% (perfect linear trend)
```

**Alert Generated:**
🚨 "Predicted failure rate of 18.5% exceeds 8% threshold"

#### **Day 4: Trend Continues**
```
Actual Day 4: 19% (close to prediction!)
Updated prediction for Day 5: 22%
Recommendation: "Immediate investigation required"
```

#### **Instability Analysis:**
```
Failure rates: [5%, 8%, 12%, 15%, 19%]
Variance: 25.5 (moderate)
Avg failures: 11.8
Trend: +3.5 per day

Score = (25.5×0.5) + (11.8×0.3) + (3.5×0.2)
      = 12.75 + 3.54 + 0.70
      = 16.99

Result: CRITICAL instability score
```

---

## 9. Quick Reference Table

| Metric | Formula | Good Value | Bad Value |
|--------|---------|------------|-----------|
| Failure Rate | (Failures/Total)×100 | <5% | >10% |
| Prediction Confidence | R² × 100 | >80% | <50% |
| Performance Degradation | ((New-Old)/Old)×100 | <10% | >20% |
| Instability Score | See formula above | <5 | >8 |
| Trend Slope | Linear regression | Negative | >1.0 |

---

## 10. Troubleshooting Predictions

### **"Why do I see 0% prediction?"**
✅ Check: Do you have 3+ days of data?
✅ Check: Is there variation in your failure rates?
✅ Check: Are tests actually running and recording data?

### **"Predictions seem wrong"**
✅ Check confidence score - is it >70%?
✅ More data points = better accuracy
✅ Look for anomalies in your data

### **"No trend detected"**
✅ This might be good! Stable failure rate
✅ Or need more time for pattern to emerge

---

## Summary

The system uses proven statistical methods to:
1. **Predict** future failures using linear regression
2. **Detect** trends by comparing recent vs historical data
3. **Identify** unstable components using variance analysis
4. **Alert** teams before issues become critical
5. **Recommend** actions based on data patterns

All calculations are transparent and based on your actual test data!
