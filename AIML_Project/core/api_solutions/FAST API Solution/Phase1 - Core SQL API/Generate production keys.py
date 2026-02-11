#!/usr/bin/env python3
"""
Quick Production Keys Generator
Run this to generate secure keys for your production environment
"""
import secrets
from datetime import datetime, timedelta

def generate_secret_key():
    """Generate 256-bit SECRET_KEY"""
    return secrets.token_hex(32)

def generate_api_key(prefix="apk_live"):
    """Generate secure API key"""
    random = secrets.token_urlsafe(32).replace('=', '').replace('-', '').replace('_', '')[:40]
    return f"{prefix}_{random}"

print("=" * 70)
print("PRODUCTION KEYS GENERATOR")
print("=" * 70)
print()

# Generate SECRET_KEY
print("SECRET_KEY (for .env):")
print(generate_secret_key())
print()

# Generate API Keys
print("VALID_API_KEYS (for .env):")
api_keys = [generate_api_key() for _ in range(3)]
print(",".join(api_keys))
print()

print("Or copy individually:")
for i, key in enumerate(api_keys, 1):
    print(f"  Key {i}: {key}")
print()

print("=" * 70)
print("COPY TO YOUR .env FILE:")
print("=" * 70)
print()
print(f"SECRET_KEY={generate_secret_key()}")
print(f"VALID_API_KEYS={','.join([generate_api_key() for _ in range(3)])}")
print()
print("⚠️  IMPORTANT:")
print("  • Never commit these keys to Git")
print("  • Store in AWS Secrets Manager for production")
print("  • Rotate every 90 days")
print("=" * 70)