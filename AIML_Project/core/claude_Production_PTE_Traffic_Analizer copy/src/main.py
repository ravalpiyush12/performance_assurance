# 1. Configure database connection
db_config = {
    'username': 'your_oracle_user',
    'password': 'your_password',
    'dsn': 'hostname:1521/ORCL'  # or use TNS name
}

# 2. Run the analysis
from custom_oracle_analyzer import run_custom_analysis
from custom_html_dashboard import generate_custom_dashboard

report = run_custom_analysis(
    db_config, 
    prod_days=7,   # Analyze last 7 days of production
    pte_days=30    # Analyze last 30 days of PTE tests
)

# 3. Print console report
from custom_oracle_analyzer import print_custom_report
print_custom_report(report)

# 4. Generate interactive HTML dashboard
dashboard_file = generate_custom_dashboard(report)

# 5. Open in browser
import webbrowser
webbrowser.open(dashboard_file)
