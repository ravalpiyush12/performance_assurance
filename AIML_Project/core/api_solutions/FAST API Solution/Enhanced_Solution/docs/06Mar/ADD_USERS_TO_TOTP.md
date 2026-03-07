# 🔐 Add Users with TOTP & Test Different Permissions

## 🎯 Overview

You'll learn how to:
1. Add users with different roles via API (recommended)
2. Add users via SQL (alternative)
3. Set up Google Authenticator
4. Test TOTP login
5. Test different permissions

---

## ✅ Method 1: Add Users via API (Recommended)

### Step 1: Login as Admin to Get Session Token

```bash
# Login to get admin session token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123",
    "totp_code": null
  }'

# Response will include:
# {
#   "success": true,
#   "session_token": "abc123...",
#   "username": "admin",
#   "role": "admin",
#   ...
# }

# COPY THE session_token VALUE
```

### Step 2: Create Users with Different Roles

**Create Performance Engineer:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" \
  -d '{
    "username": "john.doe",
    "email": "john@company.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "role": "performance_engineer"
  }'

# Response includes:
# {
#   "success": true,
#   "user_id": 2,
#   "username": "john.doe",
#   "totp_secret": "JBSWY3DPEHPK3PXP",  ← SAVE THIS!
#   "qr_code_base64": "iVBORw0KGgoAAAANS...",  ← QR code image
#   "setup_instructions": [...]
# }
```

**Create Test Lead:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" \
  -d '{
    "username": "jane.smith",
    "email": "jane@company.com",
    "password": "SecurePass456!",
    "full_name": "Jane Smith",
    "role": "test_lead"
  }'
```

**Create Viewer:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" \
  -d '{
    "username": "bob.viewer",
    "email": "bob@company.com",
    "password": "SecurePass789!",
    "full_name": "Bob Viewer",
    "role": "viewer"
  }'
```

### Step 3: Save the QR Code

The response includes `qr_code_base64`. You can:

**Option A: View in Browser (easiest)**
Create an HTML file:

```html
<!DOCTYPE html>
<html>
<head><title>TOTP Setup</title></head>
<body>
    <h2>Scan with Google Authenticator</h2>
    <img src="data:image/png;base64,PASTE_BASE64_HERE" />
    <p>TOTP Secret: PASTE_SECRET_HERE</p>
</body>
</html>
```

**Option B: Use Python to Save Image**
```python
import base64

# From API response
qr_base64 = "iVBORw0KGgoAAAANS..."  # Paste actual base64 here

# Save as image
with open("john_doe_qr.png", "wb") as f:
    f.write(base64.b64decode(qr_base64))

print("✓ QR code saved as john_doe_qr.png")
print("Scan this with Google Authenticator app")
```

---

## ✅ Method 2: Add Users via SQL (Alternative)

### Create User with Python Script

Save as `create_user.py`:

```python
#!/usr/bin/env python3
"""
Create user with TOTP secret
"""
import bcrypt
import pyotp
import qrcode
import oracledb

# Database config
DB_CONFIG = {
    'user': 'your_db_user',
    'password': 'your_db_password',
    'dsn': 'localhost:1521/ORCL'
}

def create_user(username, email, password, full_name, role="performance_engineer"):
    """Create user with TOTP"""
    
    # Generate password hash
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # Generate TOTP secret
    totp_secret = pyotp.random_base32()
    
    # Connect to database
    conn = oracledb.connect(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        dsn=DB_CONFIG['dsn']
    )
    
    cursor = conn.cursor()
    
    try:
        # Insert user
        user_id_var = cursor.var(int)
        
        cursor.execute("""
            INSERT INTO AUTH_USERS (
                USER_ID, USERNAME, EMAIL, FULL_NAME,
                PASSWORD_HASH, TOTP_SECRET, ROLE,
                IS_ACTIVE, MFA_ENABLED, CREATED_BY
            ) VALUES (
                AUTH_USER_SEQ.NEXTVAL, :username, :email, :full_name,
                :password_hash, :totp_secret, :role,
                'Y', 'Y', 'admin'
            ) RETURNING USER_ID INTO :user_id
        """, {
            'username': username,
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'totp_secret': totp_secret,
            'role': role,
            'user_id': user_id_var
        })
        
        user_id = user_id_var.getvalue()[0]
        conn.commit()
        
        print(f"✓ User created: {username} (ID: {user_id})")
        print(f"  Email: {email}")
        print(f"  Role: {role}")
        print(f"  TOTP Secret: {totp_secret}")
        print(f"  Password: {password}")
        
        # Generate QR code
        totp = pyotp.TOTP(totp_secret)
        uri = totp.provisioning_uri(email, "Monitoring System")
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        filename = f"{username}_qr.png"
        img.save(filename)
        
        print(f"✓ QR code saved: {filename}")
        print(f"\nSetup Instructions:")
        print(f"  1. Install Google Authenticator on your phone")
        print(f"  2. Open app and tap '+' to add account")
        print(f"  3. Scan {filename}")
        print(f"  4. Use 6-digit code from app to login")
        
        return {
            'user_id': user_id,
            'username': username,
            'totp_secret': totp_secret,
            'qr_file': filename
        }
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Create performance engineer
    create_user(
        username="john.doe",
        email="john@company.com",
        password="SecurePass123!",
        full_name="John Doe",
        role="performance_engineer"
    )
    
    print("\n" + "="*60)
    
    # Create test lead
    create_user(
        username="jane.smith",
        email="jane@company.com",
        password="SecurePass456!",
        full_name="Jane Smith",
        role="test_lead"
    )
    
    print("\n" + "="*60)
    
    # Create viewer
    create_user(
        username="bob.viewer",
        email="bob@company.com",
        password="SecurePass789!",
        full_name="Bob Viewer",
        role="viewer"
    )
```

Run it:
```bash
python create_user.py

# Output:
# ✓ User created: john.doe (ID: 2)
#   TOTP Secret: JBSWY3DPEHPK3PXP
#   Password: SecurePass123!
# ✓ QR code saved: john_doe_qr.png
```

---

## 📱 Step-by-Step: Setup Google Authenticator

### 1. Install Google Authenticator

**On iPhone:**
- App Store → Search "Google Authenticator"
- Install (free app)

**On Android:**
- Play Store → Search "Google Authenticator"
- Install (free app)

### 2. Add Account to Authenticator

1. **Open Google Authenticator app**
2. **Tap "+"** (Add account)
3. **Choose "Scan QR code"**
4. **Scan the QR code** you saved (john_doe_qr.png)
5. **Account added!** You'll see:
   ```
   Monitoring System
   john@company.com
   123 456  ← 6-digit code (changes every 30 seconds)
   ```

### 3. Save TOTP Secret (Backup)

**IMPORTANT:** Write down the TOTP secret somewhere safe!

If you lose your phone:
- You can manually enter the secret in a new Authenticator app
- Or admin can reset it in the database

---

## 🧪 Test TOTP Login

### Test 1: Login with TOTP

1. **Open UI:** http://localhost:8000/
2. **Enter credentials:**
   - Username: `john.doe`
   - Password: `SecurePass123!`
   - TOTP: `123456` ← Get from Google Authenticator app
3. **Click Login**
4. **✓ Should login successfully!**

### Test 2: Test Invalid TOTP

1. Enter username and password
2. Enter wrong TOTP: `000000`
3. Should show error: "Invalid credentials or TOTP code"
4. After 5 failed attempts → Account locked for 30 min

### Test 3: Test Different Roles

**Login as Performance Engineer (john.doe):**
```bash
# Get 6-digit code from Google Authenticator
TOTP_CODE="123456"  # Replace with actual code

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"john.doe\",
    \"password\": \"SecurePass123!\",
    \"totp_code\": \"$TOTP_CODE\"
  }"

# Response shows permissions:
# {
#   "username": "john.doe",
#   "role": "performance_engineer",
#   "permissions": ["read", "write", "register_test"]
# }
```

---

## 🔒 Test Permissions

### Performance Engineer Permissions

```bash
# Get session token
TOKEN="abc123..."

# ✅ Can read (allowed)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# ✅ Can write/upload (allowed)
curl -X POST http://localhost:8000/api/v1/monitoring/awr/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt"

# ❌ Cannot manage users (denied - needs 'user_manage')
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Authorization: Bearer $TOKEN" \
  -d '{...}'
# Response: 403 Permission denied
```

### Viewer Permissions

```bash
# Login as viewer
# bob.viewer / SecurePass789! / TOTP

# ✅ Can read (allowed)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $VIEWER_TOKEN"

# ❌ Cannot write (denied - only has 'read')
curl -X POST http://localhost:8000/api/v1/monitoring/awr/upload \
  -H "Authorization: Bearer $VIEWER_TOKEN"
# Response: 403 Permission denied. Required: 'write'
```

---

## 📊 Role Permissions Summary

| Role | Permissions | Can Do |
|------|-------------|--------|
| **admin** | read, write, delete, configure, user_manage | Everything |
| **performance_engineer** | read, write, register_test | Upload AWR, register tests |
| **test_lead** | read, write, register_test, approve | Manage test lifecycle |
| **viewer** | read | View dashboards only |

---

## 🔧 Manage Users

### View All Users

```sql
SELECT 
    USER_ID, USERNAME, EMAIL, ROLE,
    IS_ACTIVE, MFA_ENABLED,
    CASE WHEN TOTP_SECRET IS NULL THEN 'NO' ELSE 'YES' END AS TOTP_SET
FROM AUTH_USERS
ORDER BY USER_ID;
```

### Disable User

```sql
UPDATE AUTH_USERS 
SET IS_ACTIVE = 'N'
WHERE USERNAME = 'john.doe';
COMMIT;
```

### Reset User Password

```python
import bcrypt

new_password = "NewPass123!"
new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
print(f"New hash: {new_hash}")

# Then in SQL:
# UPDATE AUTH_USERS 
# SET PASSWORD_HASH = 'paste_hash_here'
# WHERE USERNAME = 'john.doe';
```

### Reset TOTP Secret (if phone lost)

```python
import pyotp
import qrcode

# Generate new secret
new_secret = pyotp.random_base32()
print(f"New TOTP secret: {new_secret}")

# Generate new QR code
totp = pyotp.TOTP(new_secret)
uri = totp.provisioning_uri("john@company.com", "Monitoring System")

qr = qrcode.QRCode()
qr.add_data(uri)
qr.make()
img = qr.make_image()
img.save("john_new_qr.png")

# Then in SQL:
# UPDATE AUTH_USERS 
# SET TOTP_SECRET = 'new_secret_here'
# WHERE USERNAME = 'john.doe';
```

---

## 🎓 Complete Example Workflow

### 1. Create User (as admin)

```bash
# Via UI or API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "username": "test.user",
    "email": "test@company.com",
    "password": "Test123!",
    "full_name": "Test User",
    "role": "performance_engineer"
  }' > user_response.json
```

### 2. Save QR Code

```python
import json
import base64

# Load response
with open('user_response.json') as f:
    data = json.load(f)

# Save QR code
qr_data = base64.b64decode(data['qr_code_base64'])
with open('test_user_qr.png', 'wb') as f:
    f.write(qr_data)

print(f"Username: {data['username']}")
print(f"TOTP Secret: {data['totp_secret']}")
print(f"QR Code: test_user_qr.png")
```

### 3. User Sets Up TOTP

1. User opens test_user_qr.png
2. Scans with Google Authenticator
3. Sees 6-digit code in app

### 4. User Logs In

1. Goes to http://localhost:8000/
2. Enters: test.user / Test123! / [6-digit code]
3. Clicks Login
4. ✓ Success!

---

## 🐛 Troubleshooting

### TOTP Code Not Working

**Check:**
1. Phone time is synchronized (Settings → Date & Time → Auto)
2. Code hasn't expired (changes every 30 seconds)
3. Entered correct 6 digits (no spaces)
4. TOTP secret in database matches Authenticator

### "Account Locked"

```sql
-- Reset failed attempts
UPDATE AUTH_USERS 
SET FAILED_ATTEMPTS = 0,
    LOCKED_UNTIL = NULL
WHERE USERNAME = 'john.doe';
COMMIT;
```

### Lost Phone / Can't Generate TOTP

**Option 1: Admin resets TOTP**
```sql
-- Temporarily disable MFA
UPDATE AUTH_USERS 
SET MFA_ENABLED = 'N'
WHERE USERNAME = 'john.doe';
COMMIT;

-- User can login, then enable MFA again with new secret
```

**Option 2: Generate new TOTP secret**
Use the reset script above

---

## ✅ Quick Summary

**To add users with TOTP:**

1. **Create user** via API or Python script
2. **Save TOTP secret** and QR code
3. **Scan QR code** with Google Authenticator app
4. **Login** with username + password + 6-digit TOTP code
5. **Test permissions** based on role

**Default users to create:**
- `admin` - Already exists
- `performance_engineer` - Can upload data
- `test_lead` - Can manage tests
- `viewer` - Read-only access

**All users need:**
- Unique username
- Email address
- Secure password
- TOTP secret (from Google Authenticator)

---

**You're all set! Create users and test TOTP now!** 🎉