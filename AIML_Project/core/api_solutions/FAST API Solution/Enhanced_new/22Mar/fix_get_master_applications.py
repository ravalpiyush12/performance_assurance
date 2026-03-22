# =============================================================================
# FIX: database.py — get_master_applications
# Add APP_ID to the SELECT so frontend can use it for DELETE
# =============================================================================
# Find the get_master_applications method and update the SQL SELECT.
# The exact method name may vary — search for "APPD_APPLICATIONS_MASTER" or
# "master_applications" in your database.py

# FIND this SQL (approximate — your columns may differ slightly):
"""
SELECT
    APPLICATION_NAME,
    LOB_NAME,
    TRACK,
    DISCOVERY_FREQUENCY,
    IS_ACTIVE,
    CREATED_DATE
FROM API_APPD_APPLICATIONS_MASTER    -- or APPD_APPLICATIONS depending on your schema
WHERE IS_ACTIVE = 'Y'
"""

# REPLACE WITH (add APP_ID / APP_MASTER_ID as first column):
"""
SELECT
    APP_ID,               -- ADD THIS LINE
    APPLICATION_NAME,
    LOB_NAME,
    TRACK,
    DISCOVERY_FREQUENCY,
    IS_ACTIVE,
    DESCRIPTION,          -- ADD THIS if not already present
    CREATED_DATE
FROM API_APPD_APPLICATIONS_MASTER
WHERE IS_ACTIVE = 'Y'
"""

# AND update the row mapping to include it:
# FIND:
{
    'application_name':   row[0],
    'lob_name':           row[1],
    'track':              row[2],
    'discovery_frequency': row[3],
    'is_active':          row[4],
    'created_date':       row[5].isoformat() if row[5] else None,
}

# REPLACE WITH:
{
    'app_master_id':       row[0],    # ADD — used by frontend DELETE
    'application_name':    row[1],
    'lob_name':            row[2],
    'track':               row[3],
    'discovery_frequency': row[4],
    'is_active':           row[5],
    'description':         row[6],    # ADD — now returned to frontend
    'created_date':        row[7].isoformat() if row[7] else None,
}

# NOTE: Row indices depend on your exact SELECT order.
# The key point: add APP_ID (or whatever your PK column is called)
# as 'app_master_id' in the returned dict.
# Frontend already looks for: app.app_master_id || app.id || app.app_id
# So naming it 'app_master_id' will work immediately.
