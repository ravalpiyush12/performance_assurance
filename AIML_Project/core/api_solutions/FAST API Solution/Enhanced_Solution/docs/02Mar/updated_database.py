# Updated database method for get_master_applications with TRACK support

def get_master_applications(self, lob_name: Optional[str] = None, track: Optional[str] = None) -> List[dict]:
    """
    Get all applications from master table
    
    Args:
        lob_name: Optional LOB name to filter
        track: Optional Track to filter
        
    Returns:
        List of application dicts
    """
    conn = self.pool.acquire()
    cursor = conn.cursor()
    
    try:
        # Build dynamic query based on filters
        sql = """
            SELECT APPLICATION_NAME, LOB_NAME, TRACK, DESCRIPTION
            FROM APPD_APPLICATIONS_MASTER
            WHERE IS_ACTIVE = 'Y'
        """
        
        params = {}
        
        if lob_name and track:
            sql += " AND LOB_NAME = :lob_name AND TRACK = :track"
            params = {'lob_name': lob_name, 'track': track}
        elif lob_name:
            sql += " AND LOB_NAME = :lob_name"
            params = {'lob_name': lob_name}
        elif track:
            sql += " AND TRACK = :track"
            params = {'track': track}
        
        sql += " ORDER BY APPLICATION_NAME"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        apps = []
        for row in rows:
            apps.append({
                'application_name': row[0],
                'lob_name': row[1],
                'track': row[2],
                'description': row[3]
            })
        
        return apps
        
    finally:
        cursor.close()
        conn.close()