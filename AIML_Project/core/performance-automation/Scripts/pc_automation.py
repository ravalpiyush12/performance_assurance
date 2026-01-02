#!/usr/bin/env python3
"""
Performance Center Automation Script
Handles triggering, monitoring, and downloading test results
"""

import argparse
import requests
import json
import time
import sys
import os
from datetime import datetime
import urllib3

# Disable SSL warnings for demo (remove in production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PerformanceCenterAPI:
    """Performance Center REST API Client"""
    
    def __init__(self, server, domain, project, username, password):
        self.base_url = f"http://{server}/LoadTest/rest"
        self.domain = domain
        self.project = project
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # For demo only
        self.token = None
        
    def authenticate(self):
        """Authenticate with Performance Center"""
        print("Authenticating with Performance Center...")
        
        auth_url = f"{self.base_url}/authentication-point/authenticate"
        
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            response = self.session.post(auth_url, json=payload, timeout=30)
            response.raise_for_status()
            
            auth_data = response.json()
            self.token = auth_data.get('token') or auth_data.get('authenticity-token')
            
            # Set authentication header
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            })
            
            print("✓ Authentication successful!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def trigger_test(self, test_id, duration, post_run_action='COLLATE_AND_ANALYZE'):
        """Trigger a performance test"""
        print(f"Triggering test ID: {test_id}")
        
        url = f"{self.base_url}/domains/{self.domain}/projects/{self.project}/test-runs"
        
        payload = {
            "testId": test_id,
            "timeslotDuration": int(duration),
            "postRunAction": post_run_action,
            "vudsMode": False
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            run_data = response.json()
            run_id = run_data.get('ID') or run_data.get('id') or run_data.get('testRunId')
            
            print(f"✓ Test triggered successfully!")
            print(f"  Run ID: {run_id}")
            
            return {
                'success': True,
                'run_id': str(run_id),
                'status': 'INITIALIZING',
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to trigger test: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_run_status(self, run_id):
        """Get current status of a test run"""
        url = f"{self.base_url}/domains/{self.domain}/projects/{self.project}/runs/{run_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            run_data = response.json()
            status = run_data.get('status') or run_data.get('testState')
            
            return {
                'success': True,
                'status': status,
                'run_data': run_data
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to get status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def monitor_test(self, run_id, poll_interval=60, max_wait=18000):
        """Monitor test execution until completion"""
        print(f"Monitoring test execution (Run ID: {run_id})")
        print(f"Poll interval: {poll_interval} seconds")
        print("-" * 50)
        
        start_time = time.time()
        iteration = 0
        
        while True:
            iteration += 1
            elapsed = int(time.time() - start_time)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Check #{iteration} (Elapsed: {elapsed}s)")
            
            status_info = self.get_run_status(run_id)
            
            if not status_info['success']:
                print("  ⚠ Failed to retrieve status, retrying...")
                time.sleep(poll_interval)
                continue
            
            current_status = status_info['status']
            print(f"  Status: {current_status}")
            
            # Check if test is complete
            if current_status in ['FINISHED', 'RUN_FAILURE', 'FAILED', 'STOPPED']:
                print("-" * 50)
                print(f"✓ Test completed with status: {current_status}")
                print(f"  Total execution time: {elapsed} seconds ({elapsed/60:.1f} minutes)")
                
                return {
                    'success': True,
                    'final_status': current_status,
                    'execution_time': f"{elapsed} seconds",
                    'execution_time_minutes': round(elapsed/60, 1),
                    'iterations': iteration
                }
            
            # Check timeout
            if elapsed > max_wait:
                print(f"✗ Timeout reached ({max_wait}s)")
                return {
                    'success': False,
                    'final_status': 'TIMEOUT',
                    'error': 'Maximum wait time exceeded'
                }
            
            # Wait before next check
            time.sleep(poll_interval)
    
    def download_results(self, run_id, output_dir):
        """Download test results and analysis data"""
        print(f"Downloading results for Run ID: {run_id}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Download main report
        report_url = f"{self.base_url}/domains/{self.domain}/projects/{self.project}/runs/{run_id}/report"
        
        try:
            print("  Downloading report...")
            response = self.session.get(report_url, timeout=120)
            
            if response.status_code == 200:
                report_file = os.path.join(output_dir, f"report_{run_id}.html")
                with open(report_file, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ Report saved: {report_file}")
            
        except Exception as e:
            print(f"  ⚠ Failed to download report: {e}")
        
        # Download results data
        results_url = f"{self.base_url}/domains/{self.domain}/projects/{self.project}/runs/{run_id}/results"
        
        try:
            print("  Downloading results data...")
            response = self.session.get(results_url, timeout=120)
            
            if response.status_code == 200:
                results_file = os.path.join(output_dir, f"results_{run_id}.zip")
                with open(results_file, 'wb') as f:
                    f.write(response.content)
                print(f"  ✓ Results saved: {results_file}")
            
        except Exception as e:
            print(f"  ⚠ Failed to download results: {e}")
        
        # Save run metadata
        run_info = self.get_run_status(run_id)
        if run_info['success']:
            metadata_file = os.path.join(output_dir, f"metadata_{run_id}.json")
            with open(metadata_file, 'w') as f:
                json.dump(run_info['run_data'], f, indent=2)
            print(f"  ✓ Metadata saved: {metadata_file}")
        
        print("✓ Download completed!")
        
        return {
            'success': True,
            'output_dir': output_dir
        }
    
    def logout(self):
        """Logout from Performance Center"""
        try:
            logout_url = f"{self.base_url}/authentication-point/logout"
            self.session.post(logout_url, timeout=10)
            print("✓ Logged out successfully")
        except:
            pass


def trigger_command(args):
    """Handle trigger command"""
    pc = PerformanceCenterAPI(
        args.server, args.domain, args.project,
        args.username, args.password
    )
    
    if not pc.authenticate():
        sys.exit(1)
    
    result = pc.trigger_test(args.test_id, args.duration, args.post_run_action)
    
    # Save result
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    pc.logout()
    
    if not result['success']:
        sys.exit(1)
    
    print(f"\nResults saved to: {args.output}")


def monitor_command(args):
    """Handle monitor command"""
    pc = PerformanceCenterAPI(
        args.server, args.domain, args.project,
        args.username, args.password
    )
    
    if not pc.authenticate():
        sys.exit(1)
    
    result = pc.monitor_test(args.run_id, args.poll_interval)
    
    # Save result
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    pc.logout()
    
    if not result['success'] or result['final_status'] != 'FINISHED':
        print(f"\n✗ Test did not complete successfully: {result.get('final_status')}")
        sys.exit(1)
    
    print(f"\nResults saved to: {args.output}")


def download_command(args):
    """Handle download command"""
    pc = PerformanceCenterAPI(
        args.server, args.domain, args.project,
        args.username, args.password
    )
    
    if not pc.authenticate():
        sys.exit(1)
    
    result = pc.download_results(args.run_id, args.output_dir)
    
    pc.logout()
    
    if not result['success']:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Performance Center Automation')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Trigger command
    trigger_parser = subparsers.add_parser('trigger', help='Trigger a test')
    trigger_parser.add_argument('--server', required=True, help='PC Server')
    trigger_parser.add_argument('--domain', required=True, help='PC Domain')
    trigger_parser.add_argument('--project', required=True, help='PC Project')
    trigger_parser.add_argument('--username', required=True, help='Username')
    trigger_parser.add_argument('--password', required=True, help='Password')
    trigger_parser.add_argument('--test-id', required=True, help='Test ID')
    trigger_parser.add_argument('--duration', required=True, help='Duration in seconds')
    trigger_parser.add_argument('--post-run-action', default='COLLATE_AND_ANALYZE')
    trigger_parser.add_argument('--output', required=True, help='Output JSON file')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor test execution')
    monitor_parser.add_argument('--server', required=True)
    monitor_parser.add_argument('--domain', required=True)
    monitor_parser.add_argument('--project', required=True)
    monitor_parser.add_argument('--username', required=True)
    monitor_parser.add_argument('--password', required=True)
    monitor_parser.add_argument('--run-id', required=True, help='Run ID to monitor')
    monitor_parser.add_argument('--poll-interval', type=int, default=60)
    monitor_parser.add_argument('--output', required=True, help='Output JSON file')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download test results')
    download_parser.add_argument('--server', required=True)
    download_parser.add_argument('--domain', required=True)
    download_parser.add_argument('--project', required=True)
    download_parser.add_argument('--username', required=True)
    download_parser.add_argument('--password', required=True)
    download_parser.add_argument('--run-id', required=True)
    download_parser.add_argument('--output-dir', required=True)
    
    args = parser.parse_args()
    
    if args.command == 'trigger':
        trigger_command(args)
    elif args.command == 'monitor':
        monitor_command(args)
    elif args.command == 'download':
        download_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()