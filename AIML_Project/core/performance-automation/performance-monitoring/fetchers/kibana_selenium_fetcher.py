"""
Kibana Data Fetcher using Selenium (fallback method)
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from typing import Dict, List, Optional
from utils.logger import setup_logger

class KibanaSeleniumFetcher:
    """Fetch data from Kibana using Selenium (web scraping)"""
    
    def __init__(self, kibana_url: str, username: str, password: str):
        self.kibana_url = kibana_url.rstrip('/')
        self.username = username
        self.password = password
        self.driver = None
        self.logger = setup_logger('KibanaSeleniumFetcher')
        
    def setup_driver(self):
        """Initialize Chrome driver with headless mode"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--ignore-certificate-errors')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        self.logger.info("✓ Chrome driver initialized")
    
    def login(self) -> bool:
        """Login to Kibana"""
        try:
            self.driver.get(f"{self.kibana_url}/login")
            
            # Wait for login form
            username_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit
            password_field.submit()
            
            # Wait for redirect to main page
            time.sleep(5)
            
            # Check if login successful
            if "login" not in self.driver.current_url.lower():
                self.logger.info("✓ Kibana login successful")
                return True
            else:
                self.logger.error("✗ Kibana login failed")
                return False
                
        except Exception as e:
            self.logger.error(f"✗ Kibana login error: {e}")
            return False
    
    def extract_visualization_data(self, viz_url: str, viz_type: str = 'table') -> Optional[List[Dict]]:
        """
        Navigate to visualization and extract data
        
        Args:
            viz_url: Full URL to visualization
            viz_type: Type of visualization (table, metric, line, etc.)
            
        Returns:
            Extracted data or None
        """
        try:
            self.driver.get(viz_url)
            
            # Wait for visualization to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-subj='visualizationLoader']"))
            )
            
            # Additional wait for data to render
            time.sleep(5)
            
            if viz_type == 'table':
                return self._extract_table_data()
            elif viz_type == 'metric':
                return self._extract_metric_data()
            elif viz_type == 'line':
                return self._extract_chart_data()
            else:
                return self._extract_generic_data()
                
        except Exception as e:
            self.logger.error(f"✗ Error extracting visualization data: {e}")
            return None
    
    def _extract_table_data(self) -> List[Dict]:
        """Extract data from table visualization"""
        data = []
        try:
            # Find table element
            table = self.driver.find_element(By.CSS_SELECTOR, "table.euiTable")
            
            # Get headers
            headers = []
            header_cells = table.find_elements(By.CSS_SELECTOR, "thead th")
            for cell in header_cells:
                headers.append(cell.text)
            
            # Get rows
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.text
                data.append(row_data)
            
            self.logger.info(f"✓ Extracted {len(data)} rows from table")
            return data
            
        except Exception as e:
            self.logger.error(f"✗ Error extracting table data: {e}")
            return []
    
    def _extract_metric_data(self) -> List[Dict]:
        """Extract data from metric visualization"""
        data = []
        try:
            metrics = self.driver.find_elements(By.CSS_SELECTOR, ".legacyMtrVis__value")
            
            for metric in metrics:
                value_text = metric.text
                data.append({
                    'metric': 'value',
                    'value': value_text
                })
            
            self.logger.info(f"✓ Extracted {len(data)} metrics")
            return data
            
        except Exception as e:
            self.logger.error(f"✗ Error extracting metric data: {e}")
            return []
    
    def _extract_chart_data(self) -> List[Dict]:
        """Extract data from chart visualization"""
        # This is complex and depends on chart library used
        # May need to execute JavaScript to get data
        try:
            # Try to get data from JavaScript
            chart_data = self.driver.execute_script("""
                var charts = window.__kibanaCharts || [];
                if (charts.length > 0) {
                    return charts[0].data;
                }
                return null;
            """)
            
            if chart_data:
                self.logger.info(f"✓ Extracted chart data")
                return chart_data
            else:
                self.logger.warning("⚠ No chart data found")
                return []
                
        except Exception as e:
            self.logger.error(f"✗ Error extracting chart data: {e}")
            return []
    
    def _extract_generic_data(self) -> List[Dict]:
        """Extract generic text data from visualization"""
        data = []
        try:
            viz_container = self.driver.find_element(By.CSS_SELECTOR, "[data-test-subj='visualizationLoader']")
            text_content = viz_container.text
            
            data.append({
                'content': text_content,
                'timestamp': int(time.time() * 1000)
            })
            
            self.logger.info(f"✓ Extracted generic visualization data")
            return data
            
        except Exception as e:
            self.logger.error(f"✗ Error extracting generic data: {e}")
            return []
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("✓ Chrome driver closed")