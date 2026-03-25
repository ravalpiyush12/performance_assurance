# =============================================================================
# ADD TO main.py — Combined Audit Logs Endpoint
#
# Queries BOTH tables:
#   API_AUDIT_LOG      — system/SQL audit events
#   API_AUTH_AUDIT_LOG — authentication events (login, logout, failed login)
#
# Replaces or supplements GET /api/v1/audit/logs
# New endpoint: GET /api/v1/audit/combined
# =============================================================================

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Query

@app.get("/api/v1/audit/combined", tags=["Audit"])
async def get_combined_audit_logs(
    start_date:  Optional[str] = Query(None,  description="Start datetime (ISO format)"),
    end_date:    Optional[str] = Query(None,  description="End datetime (ISO format)"),
    source:      Optional[str] = Query(None,  description="Filter: 'auth' or 'system'"),
    username:    Optional[str] = Query(None,  description="Filter by username"),
    status:      Optional[str] = Query(None,  description="Filter: 'success' or 'failed'"),
    event_type:  Optional[str] = Query(None,  description="Filter by event type"),
    database:    Optional[str] = Query(None,  description="Filter by database name"),
    limit:       int           = Query(200,   ge=1, le=1000),
    current_user: str = Depends(verify_auth_token),
):
    """
    GET /api/v1/audit/combined
    Returns combined records from API_AUDIT_LOG (system) + API_AUTH_AUDIT_LOG (auth).
    Each record includes a 'source' field: 'system' or 'auth'.
    """
    try:
        # Default: last 24 hours
        if not start_date:
            start_dt = datetime.now() - timedelta(hours=24)
        else:
            start_dt = datetime.fromisoformat(start_date)

        end_dt = datetime.fromisoformat(end_date) if end_date else datetime.now()

        pool = app.state.connection_manager.get_pool('CQE_NFT')
        results = []

        with pool.acquire() as conn:
            cursor = conn.cursor()

            # ── 1. SYSTEM AUDIT — API_AUDIT_LOG ────────────────────────────
            if source in (None, 'system'):
                sys_filters = ["EVENT_TIMESTAMP >= :start_dt", "EVENT_TIMESTAMP <= :end_dt"]
                sys_params  = {'start_dt': start_dt, 'end_dt': end_dt}

                if username:
                    sys_filters.append("UPPER(USERNAME) LIKE UPPER(:username)")
                    sys_params['username'] = f'%{username}%'
                if status == 'success':
                    sys_filters.append("STATUS = 'success'")
                elif status == 'failed':
                    sys_filters.append("STATUS != 'success'")
                if event_type:
                    sys_filters.append("UPPER(EVENT_TYPE) = UPPER(:event_type)")
                    sys_params['event_type'] = event_type
                if database:
                    sys_filters.append("UPPER(DATABASE_NAME) LIKE UPPER(:database)")
                    sys_params['database'] = f'%{database}%'

                where = " AND ".join(sys_filters)
                cursor.execute(f"""
                    SELECT
                        AUDIT_ID, EVENT_TIMESTAMP, EVENT_TYPE, DATABASE_NAME,
                        USERNAME, SQL_STATEMENT, ROWS_AFFECTED, EXECUTION_TIME_MS,
                        STATUS, ERROR_MESSAGE, CLIENT_IP, ENVIRONMENT
                    FROM API_AUDIT_LOG
                    WHERE {where}
                    ORDER BY EVENT_TIMESTAMP DESC
                    FETCH FIRST :limit ROWS ONLY
                """, {**sys_params, 'limit': limit})

                for row in cursor.fetchall():
                    ts = row[1]
                    sql_text = row[5]
                    if sql_text and hasattr(sql_text, 'read'):
                        sql_text = sql_text.read()
                    results.append({
                        'source':           'system',
                        'audit_id':         int(row[0]) if row[0] else None,
                        'event_timestamp':  ts.isoformat() if ts else None,
                        'event_type':       row[2] or '',
                        'database_name':    row[3] or '',
                        'username':         row[4] or '',
                        'sql_statement':    str(sql_text or ''),
                        'rows_affected':    int(row[6]) if row[6] is not None else None,
                        'execution_time_ms':float(row[7]) if row[7] is not None else None,
                        'status':           row[8] or '',
                        'error_message':    row[9] or '',
                        'client_ip':        row[10] or '',
                        'environment':      row[11] or '',
                        # Normalised fields for unified display
                        'action':           row[2] or '',
                        'details':          str(sql_text or '')[:200] if sql_text else (row[9] or ''),
                    })

            # ── 2. AUTH AUDIT — API_AUTH_AUDIT_LOG ─────────────────────────
            if source in (None, 'auth'):
                auth_filters = ["TIMESTAMP >= :start_dt", "TIMESTAMP <= :end_dt"]
                auth_params  = {'start_dt': start_dt, 'end_dt': end_dt}

                if username:
                    auth_filters.append("UPPER(USERNAME) LIKE UPPER(:username)")
                    auth_params['username'] = f'%{username}%'
                if status == 'success':
                    auth_filters.append("SUCCESS = 'Y'")
                elif status == 'failed':
                    auth_filters.append("SUCCESS = 'N'")
                if event_type:
                    auth_filters.append("UPPER(ACTION) = UPPER(:event_type)")
                    auth_params['event_type'] = event_type

                where_auth = " AND ".join(auth_filters)
                cursor.execute(f"""
                    SELECT
                        AUDIT_ID, TIMESTAMP, ACTION, RESOURCE_NAME,
                        USERNAME, USER_ID, SUCCESS, FAILURE_REASON,
                        IP_ADDRESS, USER_AGENT
                    FROM API_AUTH_AUDIT_LOG
                    WHERE {where_auth}
                    ORDER BY TIMESTAMP DESC
                    FETCH FIRST :limit ROWS ONLY
                """, {**auth_params, 'limit': limit})

                for row in cursor.fetchall():
                    ts = row[1]
                    success_flag = str(row[6] or 'N').upper()
                    results.append({
                        'source':           'auth',
                        'audit_id':         int(row[0]) if row[0] else None,
                        'event_timestamp':  ts.isoformat() if ts else None,
                        'event_type':       row[2] or '',   # ACTION field
                        'database_name':    '',             # not applicable for auth
                        'username':         row[4] or '',
                        'user_id':          int(row[5]) if row[5] else None,
                        'resource_name':    row[3] or '',
                        'sql_statement':    '',
                        'rows_affected':    None,
                        'execution_time_ms':None,
                        'status':           'success' if success_flag == 'Y' else 'failed',
                        'failure_reason':   row[7] or '',
                        'client_ip':        row[8] or '',
                        'user_agent':       row[9] or '',
                        # Normalised fields
                        'action':           row[2] or '',
                        'details':          row[7] or row[3] or '',  # failure reason or resource
                    })

        # ── 3. Sort combined by timestamp desc ─────────────────────────────
        def get_ts(r):
            try:
                return r.get('event_timestamp') or ''
            except Exception:
                return ''

        results.sort(key=get_ts, reverse=True)
        results = results[:limit]

        # ── 4. Statistics ───────────────────────────────────────────────────
        total         = len(results)
        success_count = sum(1 for r in results if r['status'] == 'success')
        failed_count  = total - success_count
        auth_count    = sum(1 for r in results if r['source'] == 'auth')
        system_count  = total - auth_count
        exec_times    = [r['execution_time_ms'] for r in results if r['execution_time_ms'] is not None]
        avg_exec_ms   = round(sum(exec_times) / len(exec_times), 2) if exec_times else None

        event_types = {}
        for r in results:
            et = r.get('event_type') or 'unknown'
            event_types[et] = event_types.get(et, 0) + 1

        return {
            "success":        True,
            "total_records":  total,
            "statistics": {
                "total_events":      total,
                "successful_events": success_count,
                "failed_events":     failed_count,
                "auth_events":       auth_count,
                "system_events":     system_count,
                "avg_execution_ms":  avg_exec_ms,
                "event_types":       event_types,
            },
            "records": results,
        }

    except Exception as e:
        logger.error(f"Combined audit error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
