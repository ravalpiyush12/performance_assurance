"""
LoadRunner Summary.html Parser
Extracts transaction statistics from PC summary reports
"""
from bs4 import BeautifulSoup
import re
from typing import List, Optional
import logging
from .models import LRTransaction

logger = logging.getLogger(__name__)


class SummaryHTMLParser:
    """Parse LoadRunner summary.html report"""
    
    def __init__(self, html_content: str):
        """
        Initialize parser with HTML content
        
        Args:
            html_content: HTML content from summary.html
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        logger.info("Summary HTML parser initialized")
    
    def parse_transactions(self) -> List[LRTransaction]:
        """
        Parse transaction summary table
        
        Returns:
            List of LRTransaction objects
        """
        transactions = []
        
        try:
            # Find "Transaction Summary" or "Transaction Response Time" table
            tables = self.soup.find_all('table')
            
            logger.info(f"Found {len(tables)} tables in summary.html")
            
            for table_idx, table in enumerate(tables):
                # Check if this is the transaction table
                headers = table.find_all('th')
                header_text = ' '.join([h.get_text().strip().lower() for h in headers])
                
                logger.debug(f"Table {table_idx} headers: {header_text}")
                
                # Look for transaction-related keywords
                if any(keyword in header_text for keyword in [
                    'transaction', 'response time', 'minimum', 'average', 'maximum'
                ]):
                    logger.info(f"Found transaction table at index {table_idx}")
                    
                    rows = table.find_all('tr')
                    logger.info(f"Processing {len(rows)} rows")
                    
                    for row_idx, row in enumerate(rows[1:], 1):  # Skip header
                        cols = row.find_all('td')
                        
                        if len(cols) >= 8:  # Ensure we have enough columns
                            try:
                                transaction = self._parse_transaction_row(cols)
                                if transaction:
                                    transactions.append(transaction)
                                    logger.debug(
                                        f"Parsed transaction: {transaction.transaction_name} "
                                        f"(Avg: {transaction.average_time}s)"
                                    )
                            except Exception as e:
                                logger.warning(f"Error parsing row {row_idx}: {e}")
                                continue
            
            logger.info(f"✓ Successfully parsed {len(transactions)} transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Error parsing transactions: {e}", exc_info=True)
            return []
    
    def _parse_transaction_row(self, cols) -> Optional[LRTransaction]:
        """
        Parse single transaction row
        
        Args:
            cols: List of table cell elements
            
        Returns:
            LRTransaction object or None if parsing fails
        """
        try:
            # Typical LoadRunner summary.html format:
            # Transaction Name | Min | Avg | Max | Std Dev | 90% | Pass | Fail | Stop
            
            # Column 0: Transaction Name
            name = cols[0].get_text().strip()
            
            # Skip summary/total rows
            if name.lower() in ['total', 'average', 'summary', '']:
                return None
            
            # Columns 1-6: Response times
            minimum = self._extract_number(cols[1].get_text())
            average = self._extract_number(cols[2].get_text())
            maximum = self._extract_number(cols[3].get_text())
            std_dev = self._extract_number(cols[4].get_text())
            p90 = self._extract_number(cols[5].get_text())
            
            # Try to get 95th and 99th percentiles if available
            p95 = None
            p99 = None
            if len(cols) > 10:
                p95 = self._extract_number(cols[6].get_text())
                p99 = self._extract_number(cols[7].get_text())
                pass_col = 8
                fail_col = 9
                stop_col = 10
            else:
                pass_col = 6
                fail_col = 7
                stop_col = 8 if len(cols) > 8 else None
            
            # Pass/Fail/Stop counts
            pass_count = int(self._extract_number(cols[pass_col].get_text()) or 0)
            fail_count = int(self._extract_number(cols[fail_col].get_text()) or 0)
            stop_count = int(self._extract_number(cols[stop_col].get_text()) or 0) if stop_col else 0
            
            # Calculate totals and percentage
            total = pass_count + fail_count + stop_count
            
            if total == 0:
                logger.warning(f"Transaction {name} has 0 total executions")
                return None
            
            pass_pct = (pass_count / total * 100) if total > 0 else 0.0
            
            return LRTransaction(
                transaction_name=name,
                minimum_time=minimum,
                average_time=average,
                maximum_time=maximum,
                std_deviation=std_dev,
                percentile_90=p90,
                percentile_95=p95,
                percentile_99=p99,
                pass_count=pass_count,
                fail_count=fail_count,
                stop_count=stop_count,
                total_count=total,
                pass_percentage=pass_pct
            )
            
        except Exception as e:
            logger.warning(f"Error parsing transaction row: {e}")
            return None
    
    def _extract_number(self, text: str) -> float:
        """
        Extract numeric value from text
        
        Args:
            text: Text containing number
            
        Returns:
            Extracted float value or 0.0
        """
        try:
            # Remove commas, spaces, and other non-numeric characters
            clean = text.replace(',', '').replace(' ', '').strip()
            
            # Extract first number found (handles cases like "1.23 sec")
            match = re.search(r'[\d.]+', clean)
            if match:
                return float(match.group())
            
            return 0.0
            
        except:
            return 0.0
    
    def get_test_summary(self) -> dict:
        """
        Extract test summary information if available
        
        Returns:
            dict with test metadata
        """
        summary = {
            'scenario_name': None,
            'duration': None,
            'vusers': None,
            'start_time': None,
            'end_time': None
        }
        
        try:
            # Look for test information in various places
            text = self.soup.get_text()
            
            # Extract scenario name
            scenario_match = re.search(r'Scenario[:\s]+([^\n]+)', text, re.IGNORECASE)
            if scenario_match:
                summary['scenario_name'] = scenario_match.group(1).strip()
            
            # Extract duration
            duration_match = re.search(r'Duration[:\s]+([\d:]+)', text, re.IGNORECASE)
            if duration_match:
                summary['duration'] = duration_match.group(1).strip()
            
            # Extract vusers
            vuser_match = re.search(r'VUsers[:\s]+(\d+)', text, re.IGNORECASE)
            if vuser_match:
                summary['vusers'] = int(vuser_match.group(1))
            
        except Exception as e:
            logger.warning(f"Error extracting test summary: {e}")
        
        return summary
