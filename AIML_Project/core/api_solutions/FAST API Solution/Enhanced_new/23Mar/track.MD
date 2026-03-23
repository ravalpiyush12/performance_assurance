# Lines 12-13: read track_name (frontend sends track_name)
lob_name = body.get('lob_name')
track    = body.get('track_name') or body.get('track')  # accept both

# Lines 18-24: values are already strings from frontend, don't join
appd_ids = body.get('appd_config_ids', '') or ''
pc_ids   = body.get('pc_config_ids',   '') or ''
db_ids   = body.get('db_config_ids',   '') or ''

# Force to string (safety — in case list still arrives)
appd_str = ','.join(str(x) for x in appd_ids) if isinstance(appd_ids, list) else str(appd_ids)
pc_str   = ','.join(str(x) for x in pc_ids)   if isinstance(pc_ids,   list) else str(pc_ids)
db_str   = ','.join(str(x) for x in db_ids)   if isinstance(db_ids,   list) else str(db_ids)

# Lines 58-60: count items by splitting the string, not len() of string
'appd_count': len([x for x in appd_str.split(',') if x.strip()]),
'pc_count':   len([x for x in pc_str.split(',')   if x.strip()]),
'db_count':   len([x for x in db_str.split(',')   if x.strip()]),



--------------------------------------------

Fix in nft/routes.py save_track_template:
python# Change this line (in routes.py save_track_template):
'created_by': current_user

# To:
'created_by': current_user['username'] if isinstance(current_user, dict) else str(current_user)
And in database.py save_track_template, the bind variable 'by' maps to data.get('created_by', 'admin') — add safety there too:
python# In database.py, find the line:
'by': data.get('created_by', 'admin')
# Change to:
'by': (data.get('created_by') or {}).get('username', 'admin') if isinstance(data.get('created_by'), dict) else str(data.get('created_by') or 'admin'),
This is the same root cause as all previous DPY-3002 errors — verify_auth_token returns a dict {'username': 'admin', ...} not a plain string, even though the type hint says str. Every endpoint that passes current_user directly into a DB bind needs this fix.
Global fix — add this helper at the top of both routes.py and database.py:
pythondef get_username(current_user) -> str:
    """Safely extract username string from current_user (may be str or dict)."""
    if isinstance(current_user, dict):
        return str(current_user.get('username', 'system'))
    return str(current_user) if current_user else 'system'
Then replace every current_user used as a DB bind value with get_username(current_user). This will fix not just track template save but also PC config save and any other endpoint showing DPY-3002.