# ======================================================
# PERFORMANCE TEST VALIDATOR v4.2 – FINAL (17 Nov 2025)
# ART + TPS + ART-wise Merged Graph + Optional Terminal Summary
# ======================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime, timedelta
import os
from pathlib import Path
from collections import Counter
import warnings
warnings.filterwarnings("ignore")

# --------------------------------------------------------------
# CONFIG – DATA SOURCE & SLA
# --------------------------------------------------------------
SLA_P95_MS = 2000
SLA_ERROR_PCT = 0.1

# ========================================
# CONTROL DATA SOURCE HERE
# "DEMO" | "CSV" | "ORACLE"
# ========================================
DATA_SOURCE = "DEMO"          # ← Change this line only

OUTPUT_DIR = "reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)
REPORT_TIME = datetime.now().strftime("%Y%m%d_%H%M")
EXCEL_FILE = f"{OUTPUT_DIR}/perf_test_validation_{REPORT_TIME}.xlsx"
PLOT_FILE_ART = f"{OUTPUT_DIR}/art_peak_comparison_{REPORT_TIME}.jpg"

PROD_CSV = f"{OUTPUT_DIR}/prod_traffic.csv"
CERT_CSV = f"{OUTPUT_DIR}/cert_traffic.csv"

# --------------------------------------------------------------
# 1. ART REGEX (for CSV/ORACLE)
# --------------------------------------------------------------
ART_REGEX_MAP = [
    (r"payment.?initiation", "Payment Initiation"),
    (r"payment.?management", "Payment Management"),
    (r"platform",            "Platform"),
    (r"entitlement",         "Entitlement"),
    (r"trade",               "Trade"),
    (r"information.?management", "Information Management"),
    (r"liquidity",           "Liquidity"),
    (r"connect.?api",        "Connect API"),
    (r".*",                  "Others")
]

def assign_art_from_path(path: str) -> str:
    low = re.sub(r'[-_]', '', path.lower())
    for pat, art in ART_REGEX_MAP:
        if re.search(pat, low):
            return art
    return "Others"

# --------------------------------------------------------------
# 2. LIGHT DEMO DATA + 8 ARTs
# --------------------------------------------------------------
def create_demo_data():
    print("Generating LIGHT DEMO data with 8 ARTs (~120k rows)...")
    np.random.seed(42)
    base_time = datetime(2025, 11, 15, 8, 0, 0)
    hours = 24
    arts = [
        "Payment Initiation", "Payment Management", "Platform",
        "Entitlement", "Trade", "Information Management",
        "Liquidity", "Connect API"
    ]
    apis = [f"/v1/payment{i}" for i in range(1, 81)]
    api_to_art = {api: arts[i % 8] for i, api in enumerate(apis)}

    def generate_for_source(is_cert):
        data = []
        load_factor = 1.8 if is_cert else 1.0
        rt_shift = 300 if is_cert else 0
        error_rate = 0.005 if is_cert else 0.001

        for h in range(hours):
            hour_start = base_time + timedelta(hours=h)
            base_tps = 30 + 20 * np.sin(np.pi * h / 24)

            for api in apis:
                tps = max(10, (base_tps + np.random.normal(0, 8)) * load_factor)
                count = int(tps * 3600) // 35

                for _ in range(count):
                    rt = np.random.lognormal(mean=np.log(600 + rt_shift), sigma=0.6)
                    status = 200 if np.random.rand() > error_rate else 500
                    secs = np.random.randint(0, 3600)
                    ts = hour_start + timedelta(seconds=secs)
                    data.append([ts.strftime("%Y-%m-%d %H:%M:%S"), api, round(rt, 1), status, api_to_art[api]])
        return data

    prod_data = generate_for_source(False)
    cert_data = generate_for_source(True)

    pd.DataFrame(prod_data, columns=["timestamp", "api", "response_time_ms", "status", "art"]).to_csv(PROD_CSV, index=False)
    pd.DataFrame(cert_data, columns=["timestamp", "api", "response_time_ms", "status", "art"]).to_csv(CERT_CSV, index=False)
    print(f"DEMO data created → {len(prod_data)+len(cert_data):,} rows | 8 ARTs assigned")

# --------------------------------------------------------------
# 3. LOAD FUNCTIONS
# --------------------------------------------------------------
def load_from_oracle(table_name, source_name):
    try:
        import oracledb
        conn = oracledb.connect(user="monitor", password="pass123", dsn="localhost:1521/XE")
        query = f"SELECT TO_CHAR(log_time, 'YYYY-MM-DD HH24:MI:SS') AS timestamp, api_name AS api, response_time_ms, status FROM {table_name} WHERE log_time >= SYSDATE - 3"
        df = pd.read_sql(query, conn)
        conn.close()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        print(f"Loaded {len(df):,} rows from Oracle ({source_name})")
        return df
    except Exception as e:
        print(f"Oracle failed: {e}")
        return None

def load_csv(file_path, source_name):
    if not Path(file_path).exists(): return None
    df = pd.read_csv(file_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"Loaded {len(df):,} rows from {source_name}")
    return df

# --------------------------------------------------------------
# 4. LOAD + ART ASSIGNMENT
# --------------------------------------------------------------
print(f"Loading from {DATA_SOURCE}...")
prod_df = cert_df = None
is_demo = False
data_source_label = ""

if DATA_SOURCE == "ORACLE":
    prod_df = load_from_oracle("prod_logs", "Production")
    cert_df = load_from_oracle("cert_logs", "Certification")
    data_source_label = "ORACLE DATA" if prod_df is not None and cert_df is not None else "CSV DATA (fallback)"
elif DATA_SOURCE == "CSV":
    prod_df = load_csv(PROD_CSV, "Production CSV")
    cert_df = load_csv(CERT_CSV, "Certification CSV")
    if prod_df is None or cert_df is None:
        create_demo_data()
        prod_df = load_csv(PROD_CSV, "Production DEMO")
        cert_df = load_csv(CERT_CSV, "Certification DEMO")
        is_demo = True
        data_source_label = "DEMO DATA"
    else:
        data_source_label = "CSV DATA"
elif DATA_SOURCE == "DEMO":
    for f in [PROD_CSV, CERT_CSV]: 
        if Path(f).exists(): os.remove(f)
    create_demo_data()
    prod_df = load_csv(PROD_CSV, "Production DEMO")
    cert_df = load_csv(CERT_CSV, "Certification DEMO")
    is_demo = True
    data_source_label = "DEMO DATA"

# ART assignment
if not is_demo:
    for df, name in [(prod_df, "Production"), (cert_df, "Certification")]:
        if "art" not in df.columns or df["art"].isna().all():
            print(f"REAL DATA → deriving ART for {name} using regex")
            df["art"] = df["api"].apply(assign_art_from_path)
        else:
            blanks = df["art"].isna() | (df["art"].str.strip() == "")
            if blanks.any():
                print(f"REAL DATA → filling {blanks.sum()} missing ARTs in {name}")
                df.loc[blanks, "art"] = df.loc[blanks, "api"].apply(assign_art_from_path)
else:
    print("DEMO MODE → ART already assigned (8 ARTs)")

# Mandatory ART check
for df, name in [(prod_df, "Production"), (cert_df, "Certification")]:
    if df["art"].isna().any():
        raise ValueError(f"ART is MANDATORY! Missing in {name}")

# --------------------------------------------------------------
# 5. PER-API PEAK TPS & P95
# --------------------------------------------------------------
def get_peak_per_api(df, name):
    df["hour"] = df["timestamp"].dt.floor('H')
    hourly = df.groupby(["api", "art", "hour"]).agg(
        requests=("api", "count"),
        p95_rt=("response_time_ms", lambda x: np.percentile(x, 95))
    ).reset_index()
    hourly["tps"] = hourly["requests"] / 3600
    peak = hourly.loc[hourly.groupby("api")["tps"].idxmax()]
    peak = peak[["api", "art", "tps", "p95_rt"]].rename(columns={
        "tps": f"peak_tps_{name.lower()}",
        "p95_rt": f"peak_p95_{name.lower()}"
    })
    return peak

prod_peak = get_peak_per_api(prod_df, "Production")
cert_peak = get_peak_per_api(cert_df, "Certification")
api_comparison = pd.merge(prod_peak, cert_peak, on=["api", "art"], how="outer").fillna(0)

api_comparison["tps_gap_pct"] = ((api_comparison["peak_tps_certification"] - api_comparison["peak_tps_production"]) /
                                api_comparison["peak_tps_production"].replace(0, 1)) * 100
api_comparison["p95_gap_ms"] = api_comparison["peak_p95_certification"] - api_comparison["peak_p95_production"]
api_comparison["under_tested"] = api_comparison["peak_tps_certification"] < api_comparison["peak_tps_production"] * 0.8
api_comparison["p95_worse"] = (api_comparison["peak_p95_certification"] > SLA_P95_MS) & (api_comparison["peak_p95_production"] <= SLA_P95_MS)

# --------------------------------------------------------------
# 6. SUMMARY & SCORE
# --------------------------------------------------------------
summary = {
    "Data Source": data_source_label,
    "Total APIs": len(api_comparison),
    "Total ARTs": len(api_comparison["art"].unique()),
    "Under-Tested APIs": int(api_comparison["under_tested"].sum()),
    "P95 Degraded APIs": int(api_comparison["p95_worse"].sum()),
    "Avg TPS Gap (%)": round(api_comparison["tps_gap_pct"].mean(), 1),
}

score = 100 - min(api_comparison["under_tested"].mean() * 100, 50) \
             - min(api_comparison["p95_worse"].mean() * 100, 30) \
             - min(abs(api_comparison["tps_gap_pct"]).mean() / 5, 20)
summary["Validation Score"] = f"{round(max(score, 0), 1)}/100"

# --------------------------------------------------------------
# 7. EXCEL EXPORT
# --------------------------------------------------------------
with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
    api_comparison.to_excel(writer, sheet_name="Per_API_Peak_Comparison", index=False)
    pd.DataFrame(list(summary.items()), columns=["Metric", "Value"]).to_excel(writer, sheet_name="Summary", index=False)
    critical = api_comparison[api_comparison[["under_tested", "p95_worse"]].any(axis=1)]
    critical.to_excel(writer, sheet_name="Critical_APIs", index=False)
print(f"Excel report → {EXCEL_FILE}")

# --------------------------------------------------------------
# 8. ART-WISE MERGED GRAPH
# --------------------------------------------------------------
api_comparison["api_short"] = api_comparison["api"].str.replace("/v1/", "").str.replace("/v2/", "")
api_comparison = api_comparison.sort_values(["art", "peak_tps_production"], ascending=[True, False])

arts = api_comparison["art"].unique()
fig = plt.figure(figsize=(22, 14))
gs = fig.add_gridspec(2, 4, hspace=0.45, wspace=0.4)

for idx, art in enumerate(arts):
    ax = fig.add_subplot(gs[idx // 4, idx % 4])
    df_art = api_comparison[api_comparison["art"] == art].copy()

    x = np.arange(len(df_art))
    width = 0.35
    colors_prod = ['#1f77b4' if not (row.under_tested or row.p95_worse) else '#d62728' for row in df_art.itertuples()]
    colors_cert = ['#ff7f0e' if not (row.under_tested or row.p95_worse) else '#8c564b' for row in df_art.itertuples()]

    ax.bar(x - width/2, df_art["peak_tps_production"], width, label="Prod TPS", color=colors_prod)
    ax.bar(x + width/2, df_art["peak_tps_certification"], width, label="Cert TPS", color=colors_cert)
    ax.set_title(f"{art}\n({len(df_art)} APIs)", fontsize=13, fontweight='bold', pad=15)
    ax.set_ylabel("Peak TPS")
    ax.set_xticks(x)
    ax.set_xticklabels(df_art["api_short"], rotation=50, ha='right', fontsize=9)
    ax.legend(fontsize=9)
    ax.grid(True, axis='y', alpha=0.3)

    ax2 = ax.twinx()
    ax2.plot(x - width/2, df_art["peak_p95_production"], 'o--', color='green', label="Prod P95", markersize=5)
    ax2.plot(x + width/2, df_art["peak_p95_certification"], 'x--', color='darkred', label="Cert P95", markersize=5)
    ax2.axhline(SLA_P95_MS, color='red', linestyle='-', alpha=0.8, linewidth=1.5)
    ax2.set_ylabel("P95 (ms)", color='darkred')
    ax2.tick_params(axis='y', labelcolor='darkred')

    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc='upper right', fontsize=8)

fig.suptitle(f"Performance Test Validation by ART  |  Score: {summary['Validation Score']}  |  {data_source_label}\nRun: {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}",
             fontsize=18, fontweight='bold', y=0.98)
plt.tight_layout()
plt.savefig(PLOT_FILE_ART, dpi=220, bbox_inches='tight')
plt.close()
print(f"ART-wise merged graph → {PLOT_FILE_ART}")

# --------------------------------------------------------------
# 9. OPTIONAL RICH TERMINAL SUMMARY
# --------------------------------------------------------------
print("\n" + "═"*96)
print(f" PERFORMANCE TEST VALIDATION RESULT – {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}")
print("═"*96)
print(f"{'Data Source':<25}: {data_source_label}")
print(f"{'Total APIs':<25}: {summary['Total APIs']}")
print(f"{'Total ARTs':<25}: {summary['Total ARTs']} → {', '.join(api_comparison['art'].unique())}")
print(f"{'Under-Tested APIs':<25}: {summary['Under-Tested APIs']}")
print(f"{'P95 Degraded APIs':<25}: {summary['P95 Degraded APIs']}")
print(f"{'Average TPS Gap':<25}: {summary['Avg TPS Gap (%)']}%")
print(f"{'Validation Score':<25}: {summary['Validation Score']}")
print("═"*96)
score_val = float(summary["Validation Score"].split('/')[0])
if score_val >= 80:
    print("TEST EFFICACY: STRONG – Certification is realistic and safe")
elif score_val >= 60:
    print("TEST EFFICACY: MODERATE – Review red bars in ART graph")
else:
    print("TEST EFFICACY: WEAK – Multiple APIs/ARTs under-tested")
print("ART-wise merged graph generated → One image to rule them all!")
print("═"*96)

if score_val < 80:
    print("CRITICAL APIs (Under-tested or P95 degraded):")
    crit = api_comparison[api_comparison["under_tested"] | api_comparison["p95_worse"]]
    for _, row in crit.iterrows():
        flags = []
        if row["under_tested"]: flags.append("UNDER-TESTED")
        if row["p95_worse"]: flags.append("P95 DEGRADED")
        print(f"  • {row['art']:<20} | {row['api_short']:<15} → Prod TPS: {row['peak_tps_production']:>6.1f} | Cert TPS: {row['peak_tps_certification']:>6.1f} | P95: {row['peak_p95_production']:>4.0f}→{row['peak_p95_certification']:>4.0f} ms [{' | '.join(flags)}]")
print("═"*96)
