"""
ADD TO: main.py
----------------
Admin proxy endpoint for DB health checks.
Uses Bearer token auth (session) and internally uses API keys server-side.
Avoids exposing API keys to the frontend.

Add AFTER existing health check endpoints.
"""

@app.get("/api/v1/admin/db-health", tags=["Admin"])
async def admin_db_health_all(
    current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint: returns health status for ALL configured databases.
    Uses Bearer token auth. Internally uses each DB's API key server-side.
    Safe to call from frontend — no API keys exposed.
    """
    settings = get_settings()
    results = []

    # List of all DB names from config
    db_names = [
        'CQE_NFT', 'CD_PTE_READ', 'CD_PTE_WRITE',
        'CAS_PTE_READ', 'CAS_PTE_WRITE',
        'PORTAL_PTE_READ', 'PORTAL_PTE_WRITE',
    ]

    for db_name in db_names:
        try:
            # Get config for this DB
            db_config = getattr(settings, db_name.lower().replace('-','_'), None)
            if not db_config:
                # Try dynamic lookup from connection_manager
                pool = app.state.connection_manager.get_pool(db_name)
                if not pool:
                    continue

            pool = app.state.connection_manager.get_pool(db_name)
            if not pool:
                results.append({
                    'db_name': db_name,
                    'status': 'not_configured',
                    'connected': False,
                    'error': 'Pool not initialized',
                    'allowed_operations': 'N/A',
                })
                continue

            # Test connection
            try:
                with pool.acquire() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT SYSDATE, USER FROM DUAL")
                    row = cursor.fetchone()
                    cursor.close()
                    results.append({
                        'db_name': db_name,
                        'status': 'ok',
                        'connected': True,
                        'server_time': row[0].isoformat() if row else None,
                        'connected_as': row[1] if row else None,
                        'allowed_operations': getattr(pool, 'allowed_operations', 'DQL'),
                    })
            except Exception as conn_err:
                results.append({
                    'db_name': db_name,
                    'status': 'error',
                    'connected': False,
                    'error': str(conn_err),
                    'allowed_operations': 'N/A',
                })

        except Exception as e:
            results.append({
                'db_name': db_name,
                'status': 'error',
                'connected': False,
                'error': str(e),
                'allowed_operations': 'N/A',
            })

    healthy = sum(1 for r in results if r['connected'])
    return {
        'success': True,
        'total': len(results),
        'healthy': healthy,
        'unhealthy': len(results) - healthy,
        'databases': results,
    }


@app.post("/api/v1/admin/db-execute", tags=["Admin"])
async def admin_db_execute(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Admin endpoint: execute SQL on a selected database.
    Uses Bearer token auth. Server selects appropriate pool.
    Body: { db_name: str, sql: str, limit: int }
    """
    if current_user.get('role') not in ('admin', 'performance_engineer'):
        raise HTTPException(status_code=403, detail="Admin or PE access required")

    body = await request.json()
    db_name = body.get('db_name', '').strip().upper()
    sql = body.get('sql', '').strip()
    limit = min(int(body.get('limit', 200)), 1000)

    if not db_name:
        raise HTTPException(status_code=400, detail="db_name is required")
    if not sql:
        raise HTTPException(status_code=400, detail="sql is required")

    # Block dangerous statements for read-only DBs
    write_dbs = {'CQE_NFT', 'CD_PTE_WRITE', 'CAS_PTE_WRITE', 'PORTAL_PTE_WRITE'}
    sql_upper = sql.strip().upper()
    is_write = any(sql_upper.startswith(k) for k in ('INSERT','UPDATE','DELETE','MERGE','CREATE','DROP','ALTER','TRUNCATE','COMMIT','ROLLBACK'))

    if is_write and db_name not in write_dbs:
        raise HTTPException(
            status_code=403,
            detail=f"Database '{db_name}' is read-only (DQL only). Write operations require a write database."
        )

    pool = app.state.connection_manager.get_pool(db_name)
    if not pool:
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not configured")

    try:
        with pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                import time
                start = time.time()

                # Add FETCH FIRST for SELECT without limit
                exec_sql = sql
                if sql_upper.startswith('SELECT') and 'FETCH FIRST' not in sql_upper and 'ROWNUM' not in sql_upper:
                    exec_sql = sql.rstrip(';') + f'\nFETCH FIRST {limit} ROWS ONLY'

                cursor.execute(exec_sql)
                elapsed = round(time.time() - start, 3)

                if cursor.description:
                    # SELECT — return rows
                    columns = [col[0].lower() for col in cursor.description]
                    rows_raw = cursor.fetchmany(limit)
                    rows = []
                    for row in rows_raw:
                        d = {}
                        for i, col in enumerate(columns):
                            v = row[i]
                            if hasattr(v, 'isoformat'):
                                v = v.isoformat()
                            elif hasattr(v, 'read'):
                                v = v.read()
                            d[col] = v
                        rows.append(d)
                    return {
                        'success': True,
                        'type': 'SELECT',
                        'columns': columns,
                        'rows': rows,
                        'row_count': len(rows),
                        'elapsed_sec': elapsed,
                        'message': f'{len(rows)} row(s) returned',
                    }
                else:
                    # DML
                    row_count = cursor.rowcount
                    conn.commit()
                    # Build message like Oracle SQL*Plus
                    sql_type = sql_upper.split()[0]
                    if sql_type == 'INSERT':
                        msg = f'{row_count} row(s) inserted. Commit successful.'
                    elif sql_type == 'UPDATE':
                        msg = f'{row_count} row(s) updated. Commit successful.'
                    elif sql_type == 'DELETE':
                        msg = f'{row_count} row(s) deleted. Commit successful.'
                    elif sql_type in ('COMMIT',):
                        msg = 'Commit complete.'
                    else:
                        msg = f'Statement executed. {row_count} row(s) affected. Commit successful.'
                    return {
                        'success': True,
                        'type': sql_type,
                        'row_count': row_count,
                        'elapsed_sec': elapsed,
                        'message': msg,
                        'rows': [],
                        'columns': [],
                    }
            except Exception as sql_err:
                conn.rollback()
                error_msg = str(sql_err)
                # Extract Oracle error code for clean display
                import re
                ora_match = re.search(r'ORA-\d+:.*', error_msg)
                clean_error = ora_match.group(0) if ora_match else error_msg
                raise HTTPException(status_code=400, detail=clean_error)
            finally:
                cursor.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
