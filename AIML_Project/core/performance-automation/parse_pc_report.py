#!/usr/bin/env python3
"""
Performance Center Report Parser
Extracts transaction data from PC HTML report and prepares for Oracle database insertion
"""

import sys
import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
import argparse

class PCReportParser:
    def __init__(self, report_path):
        self.report_path = report_path
        self.transactions = []
        
    def parse_html_report(self):
        """Parse the PC HTML report and extract transaction data"""
        print(f"Parsing report: {self.report_path}")
        
        try:
            with open(self.report_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try multiple methods to find transaction data
        # Method 1: Look for transaction tables
        self._parse_transaction_tables(soup)
        
        # Method 2: Look for embedded JavaScript data
        if not self.transactions:
            self._parse_javascript_data(html_content)
        
        # Method 3: Look for JSON data
        if not self.transactions:
            self._parse_json_data(html_content)
        
        print(f"Found {len(self.transactions)} transactions")
        return len(self.transactions) > 0
    
    def _parse_transaction_tables(self, soup):
        """Parse transaction data from HTML tables"""
        # Look for tables with transaction data
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this looks like a transaction table
            headers = table.find_all('th')
            if not headers:
                continue
            
            header_text = [h.get_text().strip().lower() for h in headers]
            
            # Check if this table contains transaction info
            if any(keyword in ' '.join(header_text) for keyword in 
                   ['transaction', 'response', 'error', 'average', 'percentile']):
                
                self._extract_from_table(table, header_text)
    
    def _extract_from_table(self, table, headers):
        """Extract data from a transaction table"""
        rows = table.find_all('tr')
        
        # Find column indices
        name_idx = self._find_column_index(headers, ['transaction', 'name', 'script'])
        avg_idx = self._find_column_index(headers, ['average', 'avg', 'mean'])
        min_idx = self._find_column_index(headers, ['minimum', 'min'])
        max_idx = self._find_column_index(headers, ['maximum', 'max'])
        p90_idx = self._find_column_index(headers, ['90', 'percentile 90', '90th'])
        p95_idx = self._find_column_index(headers, ['95', 'percentile 95', '95th'])
        error_idx = self._find_column_index(headers, ['error', 'fail', 'failure'])
        count_idx = self._find_column_index(headers, ['count', 'total', 'hits'])
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_all('td')
            if not cells or len(cells) < 2:
                continue
            
            transaction = {
                'transaction_name': self._get_cell_value(cells, name_idx),
                'avg_response_time': self._get_numeric_value(cells, avg_idx),
                'min_response_time': self._get_numeric_value(cells, min_idx),
                'max_response_time': self._get_numeric_value(cells, max_idx),
                'percentile_90': self._get_numeric_value(cells, p90_idx),
                'percentile_95': self._get_numeric_value(cells, p95_idx),
                'error_rate': self._get_numeric_value(cells, error_idx),
                'transaction_count': self._get_numeric_value(cells, count_idx, is_int=True)
            }
            
            if transaction['transaction_name']:
                self.transactions.append(transaction)
    
    def _parse_javascript_data(self, html_content):
        """Extract data from embedded JavaScript"""
        # Look for JavaScript variables containing transaction data
        patterns = [
            r'var\s+transactionData\s*=\s*(\[.*?\]);',
            r'var\s+summaryData\s*=\s*(\[.*?\]);',
            r'transactions\s*:\s*(\[.*?\])',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                try:
                    # Try to parse as JSON
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                transaction = self._normalize_transaction_dict(item)
                                if transaction:
                                    self.transactions.append(transaction)
                except:
                    pass
    
    def _parse_json_data(self, html_content):
        """Extract JSON data from HTML"""
        # Look for JSON objects
        json_pattern = r'\{["\']name["\']\s*:\s*["\']([^"\']+)["\'].*?\}'
        matches = re.finditer(json_pattern, html_content)
        
        for match in matches:
            try:
                json_str = match.group(0)
                data = json.loads(json_str)
                transaction = self._normalize_transaction_dict(data)
                if transaction:
                    self.transactions.append(transaction)
            except:
                pass
    
    def _normalize_transaction_dict(self, data):
        """Normalize different data formats to standard transaction dict"""
        transaction = {
            'transaction_name': None,
            'avg_response_time': None,
            'min_response_time': None,
            'max_response_time': None,
            'percentile_90': None,
            'percentile_95': None,
            'error_rate': None,
            'transaction_count': None
        }
        
        # Map various field names to standard names
        name_fields = ['name', 'transaction', 'transactionName', 'label']
        avg_fields = ['average', 'avg', 'avgResponseTime', 'mean']
        min_fields = ['minimum', 'min', 'minResponseTime']
        max_fields = ['maximum', 'max', 'maxResponseTime']
        
        for field in name_fields:
            if field in data:
                transaction['transaction_name'] = str(data[field])
                break
        
        for field in avg_fields:
            if field in data:
                transaction['avg_response_time'] = self._parse_number(data[field])
                break
        
        for field in min_fields:
            if field in data:
                transaction['min_response_time'] = self._parse_number(data[field])
                break
        
        for field in max_fields:
            if field in data:
                transaction['max_response_time'] = self._parse_number(data[field])
                break
        
        return transaction if transaction['transaction_name'] else None
    
    def _find_column_index(self, headers, keywords):
        """Find column index by matching keywords"""
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in keywords):
                return i
        return None
    
    def _get_cell_value(self, cells, idx):
        """Get cell value safely"""
        if idx is not None and idx < len(cells):
            return cells[idx].get_text().strip()
        return None
    
    def _get_numeric_value(self, cells, idx, is_int=False):
        """Get numeric value from cell"""
        value = self._get_cell_value(cells, idx)
        return self._parse_number(value, is_int)
    
    def _parse_number(self, value, is_int=False):
        """Parse number from string"""
        if value is None:
            return None
        
        # Remove common characters
        cleaned = str(value).replace(',', '').replace('%', '').strip()
        
        try:
            if is_int:
                return int(float(cleaned))
            else:
                return float(cleaned)
        except:
            return None
    
    def get_transactions_data(self):
        """Get extracted transactions as list of dicts"""
        return self.transactions
    
    def save_to_json(self, output_path):
        """Save extracted data to JSON file"""
        data = {
            'report_path': self.report_path,
            'parse_date': datetime.now().isoformat(),
            'transaction_count': len(self.transactions),
            'transactions': self.transactions
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data saved to: {output_path}")
        return output_path
    
    def save_to_csv(self, output_path):
        """Save extracted data to CSV file"""
        if not self.transactions:
            print("No transactions to save")
            return None
        
        import csv
        
        with open(output_path, 'w', newline='') as f:
            if self.transactions:
                writer = csv.DictWriter(f, fieldnames=self.transactions[0].keys())
                writer.writeheader()
                writer.writerows(self.transactions)
        
        print(f"Data saved to: {output_path}")
        return output_path
    
    def print_summary(self):
        """Print summary of extracted data"""
        print("\n" + "="*60)
        print("TRANSACTION SUMMARY")
        print("="*60)
        
        if not self.transactions:
            print("No transactions found")
            return
        
        print(f"\nTotal Transactions: {len(self.transactions)}\n")
        
        for i, txn in enumerate(self.transactions, 1):
            print(f"{i}. {txn['transaction_name']}")
            if txn['avg_response_time']:
                print(f"   Avg Response Time: {txn['avg_response_time']:.2f} ms")
            if txn['min_response_time']:
                print(f"   Min: {txn['min_response_time']:.2f} ms")
            if txn['max_response_time']:
                print(f"   Max: {txn['max_response_time']:.2f} ms")
            if txn['percentile_90']:
                print(f"   90th Percentile: {txn['percentile_90']:.2f} ms")
            if txn['percentile_95']:
                print(f"   95th Percentile: {txn['percentile_95']:.2f} ms")
            if txn['error_rate'] is not None:
                print(f"   Error Rate: {txn['error_rate']:.2f}%")
            if txn['transaction_count']:
                print(f"   Count: {txn['transaction_count']}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Parse PC Report and extract transaction data')
    parser.add_argument('report_path', help='Path to PC HTML report file')
    parser.add_argument('--output-json', help='Output JSON file path')
    parser.add_argument('--output-csv', help='Output CSV file path')
    parser.add_argument('--print-summary', action='store_true', help='Print summary to console')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.report_path):
        print(f"Error: Report file not found: {args.report_path}")
        sys.exit(1)
    
    # Parse report
    parser_obj = PCReportParser(args.report_path)
    success = parser_obj.parse_html_report()
    
    if not success:
        print("Failed to parse report or no transactions found")
        sys.exit(1)
    
    # Save outputs
    if args.output_json:
        parser_obj.save_to_json(args.output_json)
    
    if args.output_csv:
        parser_obj.save_to_csv(args.output_csv)
    
    if args.print_summary:
        parser_obj.print_summary()
    
    # If no output specified, default to JSON
    if not args.output_json and not args.output_csv:
        default_output = args.report_path.replace('.html', '_data.json')
        parser_obj.save_to_json(default_output)
    
    print(f"\n✓ Successfully parsed {len(parser_obj.get_transactions_data())} transactions")

if __name__ == "__main__":
    main()
