# Production Security Keys Generation Guide

## 🔐 Security Keys for Production Environment

### Overview
For production environments, you need **cryptographically secure** random keys, not simple strings like "local-dev-api-key".

---

## 🎯 Quick Answer for Production

### SECRET_KEY (JWT Token Signing)
```env
# Production - 64 character hex string (256-bit)
SECRET_KEY=a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3
```

### VALID_API_KEYS (API Authentication)
```env
# Production - Multiple strong API keys, comma-separated
VALID_API_KEYS=apk_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6,apk_live_q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5f6,apk_live_g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6
```

---

## 🔧 How to Generate Secure Keys

### Method 1: Using OpenSSL (Recommended)

```bash
# Generate SECRET_KEY (256-bit / 64 hex characters)
openssl rand -hex 32

# Output example:
# a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3

# Generate API Keys (256-bit / 64 hex characters)
openssl rand -hex 32
openssl rand -hex 32
openssl rand -hex 32

# Or use base64 encoding (shorter, URL-safe)
openssl rand -base64 32

# Output example:
# Xk7mQ9pL2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4u=
```

### Method 2: Using Python

```python
#!/usr/bin/env python3
"""Generate secure keys for production"""
import secrets
import string

def generate_secret_key(length=64):
    """Generate SECRET_KEY (hex)"""
    return secrets.token_hex(32)  # 32 bytes = 64 hex characters

def generate_api_key(prefix="apk_live_"):
    """Generate API key with prefix"""
    random_part = secrets.token_urlsafe(32)  # URL-safe base64
    return f"{prefix}{random_part}"

def generate_api_key_simple():
    """Generate simple alphanumeric API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(48))

# Generate keys
print("=" * 70)
print("PRODUCTION SECURITY KEYS")
print("=" * 70)
print()

print("SECRET_KEY (for JWT signing):")
print(generate_secret_key())
print()

print("VALID_API_KEYS (comma-separated):")
api_keys = []
for i in range(3):
    api_keys.append(generate_api_key())
print(",".join(api_keys))
print()

print("Or individual API keys:")
for i in range(3):
    print(f"  Key {i+1}: {generate_api_key()}")
print()

print("=" * 70)
```

**Save as `generate_keys.py` and run:**
```bash
python generate_keys.py
```

### Method 3: Using Node.js

```javascript
// generate_keys.js
const crypto = require('crypto');

function generateSecretKey() {
    return crypto.randomBytes(32).toString('hex');
}

function generateApiKey(prefix = 'apk_live_') {
    const randomPart = crypto.randomBytes(32).toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
    return prefix + randomPart;
}

console.log('=' .repeat(70));
console.log('PRODUCTION SECURITY KEYS');
console.log('=' .repeat(70));
console.log();

console.log('SECRET_KEY (for JWT signing):');
console.log(generateSecretKey());
console.log();

console.log('VALID_API_KEYS (comma-separated):');
const apiKeys = [];
for (let i = 0; i < 3; i++) {
    apiKeys.push(generateApiKey());
}
console.log(apiKeys.join(','));
console.log();
```

Run:
```bash
node generate_keys.js
```

### Method 4: Online (Use with Caution)

⚠️ **Warning**: Only use trusted sources, preferably generate locally

```bash
# Generate on your local machine
# NEVER use public websites for production keys!

# Linux/Mac - Use /dev/urandom
head -c 32 /dev/urandom | xxd -p -c 32

# Or
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 48 | head -n 1
```

---

## 📝 Production .env Configuration

### Complete Production Example

```env
# ========================================
# PRODUCTION CONFIGURATION
# ========================================

# Environment
ENVIRONMENT=prod
DEBUG=false
LOG_LEVEL=INFO

# ========================================
# SECURITY - PRODUCTION KEYS
# ========================================

# SECRET_KEY for JWT token signing
# Generate with: openssl rand -hex 32
SECRET_KEY=a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3

# VALID_API_KEYS - Comma-separated list
# Generate each with: openssl rand -base64 32
# Format: prefix_environment_randomstring
VALID_API_KEYS=apk_live_Xk7mQ9pL2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4u,apk_live_9pL2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4uXk7m,apk_live_2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4uXk7mQ9p

# Rate Limiting (Stricter for production)
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_PERIOD=3600

# ========================================
# ORACLE DATABASE - PRODUCTION
# ========================================

# Using CyberArk for production
ORACLE_HOST=production-oracle-db.example.com
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=PRODDB
# Note: Username/Password retrieved from CyberArk

# Connection Pool (Production sizing)
ORACLE_POOL_MIN=5
ORACLE_POOL_MAX=20
ORACLE_POOL_INCREMENT=2

# ========================================
# CYBERARK - PRODUCTION
# ========================================

CYBERARK_ENABLED=true
CYBERARK_URL=https://cyberark.example.com
CYBERARK_APP_ID=OracleSQLAPI_PROD
CYBERARK_SAFE=DatabaseCredentials
CYBERARK_OBJECT=PROD_OracleDB_AppUser
CYBERARK_CERT_PATH=/app/certs/cyberark-client.pem
CYBERARK_CERT_KEY_PATH=/app/certs/cyberark-client-key.pem

# ========================================
# AUDIT LOGGING - PRODUCTION
# ========================================

ENABLE_AUDIT_LOG=true
AUDIT_LOG_PATH=/app/logs/audit

# ========================================
# AWS SETTINGS
# ========================================

AWS_REGION=us-east-1
```

---

## 🎨 API Key Naming Conventions

### Recommended Format

```
{prefix}_{environment}_{random}

Examples:
- apk_live_Xk7mQ9pL2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4u    (Production)
- apk_test_9pL2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4uXk7m    (Testing)
- apk_dev_2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4uXk7mQ9p     (Development)
```

### Prefixes by Purpose

```env
# Application API keys
VALID_API_KEYS=apk_live_xxx,apk_live_yyy,apk_live_zzz

# Service-to-service keys
VALID_API_KEYS=svc_live_xxx,svc_live_yyy

# Admin/maintenance keys
VALID_API_KEYS=adm_live_xxx

# Combined
VALID_API_KEYS=apk_live_xxx,svc_live_yyy,adm_live_zzz
```

---

## 🔒 Key Management Best Practices

### 1. **Separate Keys by Environment**

```env
# Development
SECRET_KEY=dev_a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2
VALID_API_KEYS=apk_dev_xxx,apk_dev_yyy

# Staging
SECRET_KEY=stg_b8g9d0e2c5b6a7f4d8e9c3b6a8g9d0e2
VALID_API_KEYS=apk_test_xxx,apk_test_yyy

# Production
SECRET_KEY=prod_c9h0e1f3d6c7b8g5e9f0d4c7b9h0e1f3
VALID_API_KEYS=apk_live_xxx,apk_live_yyy
```

### 2. **Use AWS Secrets Manager / Azure Key Vault**

```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
    --name prod/oracle-api/secret-key \
    --secret-string "a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3"

aws secretsmanager create-secret \
    --name prod/oracle-api/api-keys \
    --secret-string "apk_live_xxx,apk_live_yyy,apk_live_zzz"

# Reference in ECS task definition (already configured in your files)
```

### 3. **Rotate Keys Regularly**

```bash
# Production key rotation schedule
- API Keys: Every 90 days
- SECRET_KEY: Every 180 days
- After any suspected breach: Immediately
```

### 4. **Track API Key Usage**

```python
# Add metadata to API keys
API_KEYS = {
    "apk_live_xxx": {
        "name": "Production App Server 1",
        "created": "2024-01-15",
        "expires": "2024-04-15",
        "permissions": ["sql.execute", "sql.read"]
    },
    "apk_live_yyy": {
        "name": "Jenkins CI/CD Pipeline",
        "created": "2024-01-20",
        "expires": "2024-04-20",
        "permissions": ["sql.read"]
    }
}
```

---

## 🎯 Key Strength Requirements

### SECRET_KEY (JWT Signing)
- **Minimum**: 32 bytes (256 bits)
- **Recommended**: 32 bytes in hex = 64 characters
- **Format**: Hexadecimal (0-9, a-f)
- **Example**: `a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3`

### API Keys
- **Minimum**: 32 characters
- **Recommended**: 40-48 characters
- **Format**: Base64 URL-safe or alphanumeric
- **Example**: `apk_live_Xk7mQ9pL2vN8zR4tY6wH3jK5nM1qS0bF7dG9cE2aV4u`

---

## ⚠️ What NOT to Do

### ❌ NEVER Use These in Production:

```env
# ❌ Default/Example values
SECRET_KEY=your-secret-key-change-in-production
SECRET_KEY=change-me
SECRET_KEY=secret

# ❌ Simple/predictable strings
SECRET_KEY=password123
SECRET_KEY=mysecretkey
SECRET_KEY=production

# ❌ Short keys
SECRET_KEY=abc123
SECRET_KEY=key

# ❌ Dictionary words
SECRET_KEY=thequickbrownfox
SECRET_KEY=supersecret

# ❌ Dates/sequential
SECRET_KEY=20240207
SECRET_KEY=12345678

# ❌ Same key in multiple environments
SECRET_KEY=same-key-everywhere  # BAD!

# ❌ Keys committed to Git
# NEVER commit .env files with real keys!
```

---

## 📋 Complete Key Generation Script

Save as `generate_production_keys.py`:

```python
#!/usr/bin/env python3
"""
Production Security Keys Generator
Generates cryptographically secure keys for Oracle SQL API
"""
import secrets
import sys
from datetime import datetime, timedelta

def generate_secret_key():
    """Generate 256-bit SECRET_KEY"""
    return secrets.token_hex(32)

def generate_api_key(prefix="apk_live"):
    """Generate secure API key with prefix"""
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"

def generate_keys():
    """Generate all production keys"""
    print("=" * 80)
    print("ORACLE SQL API - PRODUCTION SECURITY KEYS")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Rotate by: {(datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')}")
    print()
    
    # SECRET_KEY
    print("=" * 80)
    print("1. SECRET_KEY (JWT Token Signing)")
    print("=" * 80)
    secret_key = generate_secret_key()
    print(f"SECRET_KEY={secret_key}")
    print()
    print("Use this for JWT token signing in production.")
    print("Store in AWS Secrets Manager or similar.")
    print()
    
    # API Keys
    print("=" * 80)
    print("2. VALID_API_KEYS (API Authentication)")
    print("=" * 80)
    
    api_keys = []
    key_purposes = [
        "Production Application Server",
        "CI/CD Pipeline / Jenkins",
        "Monitoring System / Nagios"
    ]
    
    for i, purpose in enumerate(key_purposes, 1):
        key = generate_api_key()
        api_keys.append(key)
        print(f"Key {i} ({purpose}):")
        print(f"  {key}")
        print()
    
    print("Combined (for .env):")
    print(f"VALID_API_KEYS={','.join(api_keys)}")
    print()
    
    # Environment file
    print("=" * 80)
    print("3. Complete Production .env Configuration")
    print("=" * 80)
    print()
    print(f"""# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Rotate by: {(datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')}

ENVIRONMENT=prod
DEBUG=false
LOG_LEVEL=INFO

# Security Keys
SECRET_KEY={secret_key}
VALID_API_KEYS={','.join(api_keys)}

# Rate Limiting
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_PERIOD=3600

# CyberArk
CYBERARK_ENABLED=true

# Audit Logging
ENABLE_AUDIT_LOG=true
AUDIT_LOG_PATH=/app/logs/audit
""")
    
    # Warnings
    print()
    print("=" * 80)
    print("IMPORTANT SECURITY REMINDERS")
    print("=" * 80)
    print()
    print("✓ Store these keys in AWS Secrets Manager / Azure Key Vault")
    print("✓ Never commit these keys to Git")
    print("✓ Rotate keys every 90 days")
    print("✓ Use different keys for dev/staging/production")
    print("✓ Track which key is used by which service")
    print("✓ Revoke keys immediately if compromised")
    print()
    print("=" * 80)

if __name__ == "__main__":
    generate_keys()
```

**Run:**
```bash
chmod +x generate_production_keys.py
python generate_production_keys.py > production_keys.txt

# Review the keys
cat production_keys.txt

# Store in AWS Secrets Manager (recommended)
# DON'T store in Git!

# Then securely delete
shred -u production_keys.txt  # Linux
# or
rm production_keys.txt  # Mac/Windows
```

---

## 🔐 Storing Keys Securely

### AWS Secrets Manager (Recommended)

```bash
# Store SECRET_KEY
aws secretsmanager create-secret \
    --name prod/oracle-sql-api/secret-key \
    --description "JWT signing key for Oracle SQL API" \
    --secret-string "a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3c8d9e2b5a7f8c9d2e1b4a6f3"

# Store API Keys
aws secretsmanager create-secret \
    --name prod/oracle-sql-api/api-keys \
    --description "Valid API keys for Oracle SQL API" \
    --secret-string "apk_live_xxx,apk_live_yyy,apk_live_zzz"

# Retrieve in ECS (already configured in your task definition)
```

### Environment Variables (ECS)

Your `ecs-task-definition.json` already has this configured:

```json
"secrets": [
  {
    "name": "SECRET_KEY",
    "valueFrom": "arn:aws:secretsmanager:region:account:secret:oracle-api-secret-key"
  },
  {
    "name": "VALID_API_KEYS",
    "valueFrom": "arn:aws:secretsmanager:region:account:secret:oracle-api-keys"
  }
]
```

---

## ✅ Final Checklist

Before deploying to production:

- [ ] Generate strong SECRET_KEY (64 hex characters)
- [ ] Generate multiple API keys (40+ characters each)
- [ ] Store keys in AWS Secrets Manager
- [ ] Update ECS task definition with Secret ARNs
- [ ] Never commit keys to Git (.env in .gitignore)
- [ ] Test keys in staging first
- [ ] Document which key is used by which service
- [ ] Set up key rotation schedule (90 days)
- [ ] Configure monitoring for failed auth attempts
- [ ] Have key revocation procedure ready

---

## 🎯 Quick Command Reference

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate API Key (hex)
openssl rand -hex 32

# Generate API Key (base64)
openssl rand -base64 32

# Generate API Key (alphanumeric, 48 chars)
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 48 | head -n 1

# Generate multiple keys at once
for i in {1..3}; do echo "Key $i: apk_live_$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-40)"; done
```

---

**Remember**: Security is only as strong as your weakest key. Always use cryptographically secure random generators! 🔐