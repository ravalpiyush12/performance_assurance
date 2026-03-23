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