FIXES:
1. pre-login.html  - No more API call pre-login (was causing 401 spam)
2. login.html      - Static QR replaced with dynamic Load QR Code button
                     Uses GET /api/v1/auth/qr-image/{username} endpoint
3. login.html      - Forgot password shows admin instructions (no auth needed)
4. login.html      - TOTP timer turns red in last 5 seconds
5. login.html      - Default username/password fields cleared
No backend restart needed.
