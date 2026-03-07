#!/usr/bin/env python3
"""
TOTP Authentication System - Test Script
Verifies installation and functionality
"""
import sys
import requests
import pyotp
import time
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000/api/v1"
TEST_ADMIN_USER = "admin"
TEST_ADMIN_PASS = "Admin@123"

def print_header(message):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {message}")
    print("="*60)

def print_result(test_name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} - {test_name}")
    if message:
        print(f"       {message}")

def test_dependencies():
    """Test 1: Check Python dependencies"""
    print_header("Test 1: Checking Dependencies")
    
    try:
        import fastapi
        print_result("FastAPI installed", True, f"Version: {fastapi.__version__}")
    except ImportError:
        print_result("FastAPI installed", False, "Run: pip install fastapi")
        return False
    
    try:
        import pyotp
        print_result("PyOTP installed", True)
    except ImportError:
        print_result("PyOTP installed", False, "Run: pip install pyotp")
        return False
    
    try:
        import bcrypt
        print_result("bcrypt installed", True)
    except ImportError:
        print_result("bcrypt installed", False, "Run: pip install bcrypt")
        return False
    
    try:
        import qrcode
        print_result("qrcode installed", True)
    except ImportError:
        print_result("qrcode installed", False, "Run: pip install qrcode[pil]")
        return False
    
    try:
        import cx_Oracle
        print_result("cx_Oracle installed", True)
    except ImportError:
        print_result("cx_Oracle installed", False, "Run: pip install cx-Oracle")
        return False
    
    return True

def test_server_running():
    """Test 2: Check if server is running"""
    print_header("Test 2: Server Connectivity")
    
    try:
        response = requests.get(f"{API_BASE}/auth/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_result("Server running", True, f"Status: {data.get('status')}")
            print_result("Auth enabled", data.get('auth_enabled', False))
            return True
        else:
            print_result("Server running", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_result("Server running", False, "Cannot connect - is server started?")
        print("       Run: python 04_main.py")
        return False
    except Exception as e:
        print_result("Server running", False, str(e))
        return False

def test_login_without_mfa():
    """Test 3: Login without MFA (default admin)"""
    print_header("Test 3: Login Without MFA")
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "username": TEST_ADMIN_USER,
                "password": TEST_ADMIN_PASS,
                "totp_code": None
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result("Login successful", True, f"User: {data.get('username')}")
                print_result("Session token received", True, f"Expires in {data.get('expires_in_minutes')} min")
                return data.get('session_token')
            else:
                print_result("Login successful", False, "No success flag in response")
                return None
        elif response.status_code == 401:
            print_result("Login failed", False, "Invalid credentials")
            print("       Check admin password in database")
            return None
        else:
            print_result("Login failed", False, f"HTTP {response.status_code}")
            return None
    except Exception as e:
        print_result("Login failed", False, str(e))
        return None

def test_authenticated_request(token):
    """Test 4: Make authenticated request"""
    print_header("Test 4: Authenticated Request")
    
    if not token:
        print_result("Get user info", False, "No token available")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Get user info", True, f"User: {data.get('username')}")
            print_result("Role", True, data.get('role'))
            print_result("Permissions", True, f"{len(data.get('permissions', []))} permissions")
            for perm in data.get('permissions', []):
                print(f"         - {perm}")
            return True
        elif response.status_code == 401:
            print_result("Get user info", False, "Token invalid or expired")
            return False
        else:
            print_result("Get user info", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Get user info", False, str(e))
        return False

def test_permission_check(token):
    """Test 5: Permission checking"""
    print_header("Test 5: Permission Checks")
    
    if not token:
        print_result("Permission check", False, "No token available")
        return False
    
    # Admin should have access to sessions endpoint
    try:
        response = requests.get(
            f"{API_BASE}/auth/sessions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Admin access granted", True, f"Found {data.get('count', 0)} sessions")
            return True
        elif response.status_code == 403:
            print_result("Admin access granted", False, "Permission denied")
            return False
        else:
            print_result("Admin access granted", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Permission check", False, str(e))
        return False

def test_invalid_token():
    """Test 6: Invalid token handling"""
    print_header("Test 6: Invalid Token Handling")
    
    fake_token = "invalid_token_12345"
    
    try:
        response = requests.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {fake_token}"},
            timeout=5
        )
        
        if response.status_code == 401:
            print_result("Rejects invalid token", True, "401 Unauthorized as expected")
            return True
        else:
            print_result("Rejects invalid token", False, f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_result("Invalid token test", False, str(e))
        return False

def test_totp_generation():
    """Test 7: TOTP generation"""
    print_header("Test 7: TOTP Generation")
    
    try:
        # Generate random TOTP secret
        secret = pyotp.random_base32()
        print_result("Generate TOTP secret", True, f"Secret: {secret[:10]}...")
        
        # Create TOTP instance
        totp = pyotp.TOTP(secret)
        code = totp.now()
        print_result("Generate TOTP code", True, f"Code: {code}")
        
        # Verify code
        is_valid = totp.verify(code, valid_window=1)
        print_result("Verify TOTP code", is_valid, f"Verification: {is_valid}")
        
        # Generate provisioning URI
        uri = totp.provisioning_uri("test@example.com", "Monitoring System")
        print_result("Generate QR URI", True, "URI created successfully")
        
        return True
    except Exception as e:
        print_result("TOTP generation", False, str(e))
        return False

def test_logout(token):
    """Test 8: Logout"""
    print_header("Test 8: Logout")
    
    if not token:
        print_result("Logout", False, "No token available")
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_result("Logout successful", True, data.get('message'))
                
                # Verify token is now invalid
                verify = requests.get(
                    f"{API_BASE}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                
                if verify.status_code == 401:
                    print_result("Token invalidated", True, "Token no longer works")
                    return True
                else:
                    print_result("Token invalidated", False, "Token still works after logout")
                    return False
            else:
                print_result("Logout successful", False, "No success flag")
                return False
        else:
            print_result("Logout", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_result("Logout", False, str(e))
        return False

def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: \033[92m{passed}\033[0m")
    print(f"Failed: \033[91m{failed}\033[0m")
    
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"Success Rate: {percentage:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! TOTP authentication is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return failed == 0

def main():
    """Run all tests"""
    print("\n" + "🔒 TOTP Authentication System - Test Suite ".center(60, "="))
    print(f"Testing server at: {API_BASE}")
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run tests
    results.append(test_dependencies())
    
    if not results[-1]:
        print("\n❌ Dependencies missing. Install with:")
        print("   pip install -r requirements.txt --break-system-packages")
        return 1
    
    results.append(test_server_running())
    
    if not results[-1]:
        print("\n❌ Server not running. Start with:")
        print("   python 04_main.py")
        return 1
    
    # Login and get token
    token = test_login_without_mfa()
    results.append(token is not None)
    
    if token:
        results.append(test_authenticated_request(token))
        results.append(test_permission_check(token))
    else:
        results.append(False)
        results.append(False)
    
    results.append(test_invalid_token())
    results.append(test_totp_generation())
    
    if token:
        results.append(test_logout(token))
    else:
        results.append(False)
    
    # Print summary
    all_passed = print_summary(results)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
