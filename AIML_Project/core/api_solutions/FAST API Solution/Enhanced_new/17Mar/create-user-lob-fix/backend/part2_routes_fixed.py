"""
CHANGE in: Auth/routes_fixed.py
ENDPOINT: POST /create-user

Find this line in the endpoint:
    result = auth_mgr.create_user(username, email, password, full_name, role, created_by)

REPLACE WITH:
"""

        # Get optional lob_names from request body
        # Frontend sends: { username, email, password, full_name, role, lob_names: [...] }
        # lob_names = None or [] means grant ALL active LOBs automatically
        lob_names = body.get('lob_names', None)

        result = auth_mgr.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            role=role,
            created_by=created_by,
            lob_names=lob_names,
        )

# NOTE: The response now includes:
#   { success, user_id, username, role, lobs_granted: [...], lob_count, message }
# The frontend already handles this — no frontend change needed.
# saveUser() in user-management.html already sends lob_names via the separate
# grant API calls. With this fix those calls become redundant (still harmless).
