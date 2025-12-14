from production_pte_analyzer import run_comprehensive_analysis
from html_dashboard_generator import generate_html_dashboard

# 1. Run the analysis
db_config = {
    'username': 'your_username',
    'password': 'your_password',
    'dsn': 'hostname:1521/service_name'
}

report = run_comprehensive_analysis(db_config)

# 2. Generate interactive HTML dashboard
html_file = generate_html_dashboard(report)
print(f"Dashboard generated: {html_file}")

# 3. Open in browser
import webbrowser
webbrowser.open(html_file)