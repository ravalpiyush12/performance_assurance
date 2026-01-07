#!/usr/bin/env python3

"""
PC 24.1 Complete Report Download Test Script
This script authenticates, gets cookie, and downloads the report
"""

import sys
import base64
import requests
from urllib3.exceptions import InsecureRequestWarning
import zipfile
import os

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================
PC_HOST = "pc-server.example.com"
PC_PORT = "443"
PC_USERNAME = "your-username"
PC_PASSWORD = "your-password"
DOMAIN = "DEFAULT"
PROJECT = "MyProject"
RUN_ID = "12345"
RESULT_ID = "67890"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")

def authenticate():
    """Authenticate with PC and get cookie"""
    print_section("STEP 1: Authentication")
    
    # Generate Base64 token
    token_string = f"{PC_USERNAME}:{PC_PASSWORD}"
    base64_token = base64.b64encode(token_string.encode()).decode()
    
    print(f"✓ Base64 token generated (length: {len(base64_token)})")
    print(f"  Token preview: {base64_token[:20]}...")
    
    # Authenticate
    url = f"https://{PC_HOST}:{PC_PORT}/LoadTest/rest/authentication-point/authenticate"
    headers = {"Content-Type": "application/json"}
    payload = {"Token": base64_token}
    
    print(f"\nAuthenticating with PC...")
    print(f"  URL: {url}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, verify=False)
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✓ Authentication successful")
            
            # Extract cookies
            cookies = response.cookies
            if not cookies:
                print("✗ No cookies received!")
                print(f"Response headers: {dict(response.headers)}")
                sys.exit(1)
            
            cookie_string = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            print(f"✓ Cookie extracted (length: {len(cookie_string)})")
            print(f"  Cookie preview: {cookie_string[:80]}...")
            
            return cookie_string
        else:
            print(f"✗ Authentication failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Error during authentication: {e}")
        sys.exit(1)

def test_endpoints(cookie):
    """Test different endpoint variations to find working one"""
    print_section("STEP 2: Testing Endpoints")
    
    endpoints = [
        f"/LoadTest/rest/domains/{DOMAIN}/projects/{PROJECT}/Runs/{RUN_ID}/Results/{RESULT_ID}/data",
        f"/LoadTest/rest/domains/{DOMAIN}/projects/{PROJECT}/Runs/{RUN_ID}/Results/{RESULT_ID}",
        f"/LoadTest/rest/domains/{DOMAIN}/projects/{PROJECT}/Results/{RESULT_ID}/data",
        f"/LoadTest/rest/domains/{DOMAIN}/projects/{PROJECT}/Results/{RESULT_ID}/Report.zip",
        f"/loadtest/rest/domains/{DOMAIN}/projects/{PROJECT}/Runs/{RUN_ID}/Results/{RESULT_ID}/data",
    ]
    
    headers = {
        "Cookie": cookie,
        "Accept": "application/octet-stream"
    }
    
    for endpoint in endpoints:
        url = f"https://{PC_HOST}:{PC_PORT}{endpoint}"
        print(f"Testing: {endpoint}")
        
        try:
            response = requests.head(url, headers=headers, verify=False, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✓ 200 OK - Endpoint is accessible!")
                return endpoint
            elif response.status_code == 404:
                print(f"  ✗ 404 Not Found")
            elif response.status_code == 401:
                print(f"  ✗ 401 Unauthorized")
            else:
                print(f"  ? Status: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✗ No working endpoint found!")
    print("\nTried all endpoints:")
    for ep in endpoints:
        print(f"  - {ep}")
    print("\nPlease verify your configuration values.")
    sys.exit(1)

def download_report(cookie, endpoint):
    """Download the report using the working endpoint"""
    print_section("STEP 3: Downloading Report")
    
    url = f"https://{PC_HOST}:{PC_PORT}{endpoint}"
    print(f"Using endpoint: {endpoint}")
    print(f"Full URL: {url}\n")
    
    headers = {
        "Cookie": cookie,
        "Accept": "application/octet-stream"
    }
    
    print("Starting download...")
    
    try:
        response = requests.get(url, headers=headers, verify=False, stream=True)
        
        print(f"  Status Code: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code != 200:
            print(f"✗ Download failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            sys.exit(1)
        
        # Save to file
        filename = "Report.zip"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(filename)
        print(f"✓ Download complete!")
        print(f"  File size: {file_size:,} bytes")
        
        return filename, file_size
        
    except Exception as e:
        print(f"✗ Error during download: {e}")
        sys.exit(1)

def verify_and_extract(filename, file_size):
    """Verify the downloaded file and extract if it's a valid zip"""
    print_section("STEP 4: Verify and Extract")
    
    print(f"File: {filename}")
    print(f"Size: {file_size:,} bytes\n")
    
    if file_size < 100:
        print("⚠ File is very small (probably an error response)")
        with open(filename, 'r') as f:
            print(f"Content:\n{f.read()}")
        sys.exit(1)
    
    # Check if it's a valid ZIP
    if not zipfile.is_zipfile(filename):
        print("⚠ File is not a valid ZIP archive")
        print("First 500 bytes:")
        with open(filename, 'rb') as f:
            print(f.read(500))
        sys.exit(1)
    
    print("✓ File is a valid ZIP archive!\n")
    
    # Extract
    extract_dir = "extracted_report"
    print(f"Extracting to: {extract_dir}/")
    
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print("✓ Extraction complete\n")
    
    # List extracted files
    print("Extracted files:")
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            print(f"  {filepath} ({size:,} bytes)")
    
    # Find HTML files
    print("\nHTML files:")
    html_files = []
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith(('.html', '.htm')):
                filepath = os.path.join(root, file)
                html_files.append(filepath)
                print(f"  {filepath}")
    
    # Find main report
    main_report = None
    for name in ['index.html', 'report.html', 'Report.html']:
        for html_file in html_files:
            if html_file.endswith(name):
                main_report = html_file
                break
        if main_report:
            break
    
    if not main_report and html_files:
        main_report = html_files[0]
    
    if main_report:
        print(f"\n✓ Main report: {main_report}")
        print(f"\nYou can open it with:")
        print(f"  python -m webbrowser {main_report}")
        print(f"  or")
        print(f"  open {main_report}")
    else:
        print("\n⚠ Could not find HTML report file")

def main():
    print("=" * 60)
    print("PC 24.1 Complete Download Test")
    print("=" * 60)
    
    print("\nConfiguration:")
    print(f"  PC Host: {PC_HOST}:{PC_PORT}")
    print(f"  Username: {PC_USERNAME}")
    print(f"  Domain: {DOMAIN}")
    print(f"  Project: {PROJECT}")
    print(f"  Run ID: {RUN_ID}")
    print(f"  Result ID: {RESULT_ID}")
    
    # Step 1: Authenticate
    cookie = authenticate()
    
    # Step 2: Test endpoints
    working_endpoint = test_endpoints(cookie)
    
    # Step 3: Download report
    filename, file_size = download_report(cookie, working_endpoint)
    
    # Step 4: Verify and extract
    verify_and_extract(filename, file_size)
    
    # Summary
    print_section("SUMMARY")
    print("✓ Authentication: Success")
    print(f"✓ Cookie extracted: {len(cookie)} bytes")
    print(f"✓ Working endpoint: {working_endpoint}")
    print(f"✓ Report downloaded: {file_size:,} bytes")
    print("✓ Report extracted successfully")
    print("\nFiles created:")
    print("  - Report.zip (original download)")
    print("  - extracted_report/ (extracted contents)")
    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
