"""
NFT Platform Database Layer
All CRUD operations for API_NFT_* tables.
Follows exact pattern of monitoring/appd/database.py and monitoring/pc/database.py:
  - with self.pool.get_connection() as conn
  - cursor = conn.cursor()
  - try/except/finally with cursor.close()
  - Row access by index: row[0], row[1], ...
  - dict(zip(columns, row)) for multi-column fetches
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class NFTPlatformDatabase:
    """Database operations for all API_NFT_* tables."""

    def __init__(self, pool):
        """
        Args:
            pool: Oracle connection pool (OracleConnectionPool instance)
        """
        self.pool = pool
        logger.info("NFTPlatformDatabase initialized")

    # =========================================================================
    # USER LOB ACCESS
    # =========================================================================

    def get_user_lobs(self, username: str) -> List[Dict]:
        """Get all active LOBs accessible to a user."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY,
                           GRANTED_DATE, IS_ACTIVE
                    FROM API_NFT_USER_LOB_ACCESS
                    WHERE USERNAME = :username
                      AND IS_ACTIVE = 'Y'
                    ORDER BY LOB_NAME
                """, {'username': username})
                columns = ['access_id', 'username', 'lob_name', 'granted_by',
                           'granted_date', 'is_active']
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                logger.error(f"Error getting user LOBs for {username}: {e}")
                return []
            finally:
                cursor.close()

    def grant_user_lob_access(self, username: str, lob_name: str,
                               granted_by: str) -> Dict:
        """Grant a user access to a LOB."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Check if access already exists (even if revoked)
                cursor.execute("""
                    SELECT ACCESS_ID, IS_ACTIVE
                    FROM API_NFT_USER_LOB_ACCESS
                    WHERE USERNAME = :username AND LOB_NAME = :lob_name
                """, {'username': username, 'lob_name': lob_name})
                row = cursor.fetchone()
                if row:
                    if row[1] == 'Y':
                        return {'success': False,
                                'error': f'User {username} already has access to {lob_name}'}
                    # Re-activate revoked access
                    cursor.execute("""
                        UPDATE API_NFT_USER_LOB_ACCESS
                        SET IS_ACTIVE = 'Y',
                            GRANTED_BY = :granted_by,
                            GRANTED_DATE = SYSDATE,
                            REVOKED_BY = NULL,
                            REVOKED_DATE = NULL
                        WHERE ACCESS_ID = :access_id
                    """, {'granted_by': granted_by, 'access_id': row[0]})
                    conn.commit()
                    return {'success': True,
                            'message': f'LOB access re-activated for {username}',
                            'access_id': row[0]}
                # New grant
                access_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_USER_LOB_ACCESS
                        (ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY)
                    VALUES
                        (API_NFT_USER_LOB_SEQ.NEXTVAL, :username, :lob_name, :granted_by)
                    RETURNING ACCESS_ID INTO :access_id
                """, {'username': username, 'lob_name': lob_name,
                      'granted_by': granted_by, 'access_id': access_id_var})
                conn.commit()
                access_id = access_id_var.getvalue()[0]
                logger.info(f"LOB access granted: {username} -> {lob_name} by {granted_by}")
                return {'success': True,
                        'message': f'Access granted to {lob_name} for {username}',
                        'access_id': access_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error granting LOB access: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def revoke_user_lob_access(self, username: str, lob_name: str,
                                revoked_by: str) -> Dict:
        """Revoke a user's access to a LOB (soft delete)."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_USER_LOB_ACCESS
                    SET IS_ACTIVE = 'N',
                        REVOKED_BY = :revoked_by,
                        REVOKED_DATE = SYSDATE
                    WHERE USERNAME = :username
                      AND LOB_NAME = :lob_name
                      AND IS_ACTIVE = 'Y'
                """, {'revoked_by': revoked_by, 'username': username,
                      'lob_name': lob_name})
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"LOB access revoked: {username} -> {lob_name}")
                    return {'success': True,
                            'message': f'Access to {lob_name} revoked for {username}'}
                return {'success': False, 'error': 'Access record not found or already revoked'}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error revoking LOB access: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def list_all_user_lob_access(self, lob_name: Optional[str] = None) -> List[Dict]:
        """List all user-LOB access records, optionally filtered by LOB."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if lob_name:
                    cursor.execute("""
                        SELECT a.ACCESS_ID, a.USERNAME, a.LOB_NAME,
                               a.GRANTED_BY, a.GRANTED_DATE, a.IS_ACTIVE,
                               u.FULL_NAME, u.ROLE
                        FROM API_NFT_USER_LOB_ACCESS a
                        JOIN API_AUTH_USERS u ON u.USERNAME = a.USERNAME
                        WHERE a.LOB_NAME = :lob_name
                        ORDER BY a.LOB_NAME, a.USERNAME
                    """, {'lob_name': lob_name})
                else:
                    cursor.execute("""
                        SELECT a.ACCESS_ID, a.USERNAME, a.LOB_NAME,
                               a.GRANTED_BY, a.GRANTED_DATE, a.IS_ACTIVE,
                               u.FULL_NAME, u.ROLE
                        FROM API_NFT_USER_LOB_ACCESS a
                        JOIN API_AUTH_USERS u ON u.USERNAME = a.USERNAME
                        ORDER BY a.LOB_NAME, a.USERNAME
                    """)
                columns = ['access_id', 'username', 'lob_name', 'granted_by',
                           'granted_date', 'is_active', 'full_name', 'role']
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                logger.error(f"Error listing user LOB access: {e}")
                return []
            finally:
                cursor.close()

    # =========================================================================
    # APPD CONFIG
    # =========================================================================

    def save_appd_config(self, lob_name: str, track: str, controller_url: str,
                          account_name: str, token_env_var: str,
                          application_names: Optional[str], tier_filter: Optional[str],
                          node_filter: Optional[str], collection_interval: int,
                          created_by: str) -> Dict:
        """Create AppD config. Returns config_id."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                config_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_APPD_CONFIG (
                        CONFIG_ID, LOB_NAME, TRACK, CONTROLLER_URL,
                        ACCOUNT_NAME, TOKEN_ENV_VAR, APPLICATION_NAMES,
                        TIER_FILTER, NODE_FILTER, COLLECTION_INTERVAL,
                        CREATED_BY
                    ) VALUES (
                        API_NFT_APPD_CFG_SEQ.NEXTVAL, :lob_name, :track,
                        :controller_url, :account_name, :token_env_var,
                        :application_names, :tier_filter, :node_filter,
                        :collection_interval, :created_by
                    ) RETURNING CONFIG_ID INTO :config_id
                """, {
                    'lob_name': lob_name, 'track': track,
                    'controller_url': controller_url, 'account_name': account_name,
                    'token_env_var': token_env_var,
                    'application_names': application_names,
                    'tier_filter': tier_filter, 'node_filter': node_filter,
                    'collection_interval': collection_interval,
                    'created_by': created_by, 'config_id': config_id_var
                })
                conn.commit()
                config_id = config_id_var.getvalue()[0]
                logger.info(f"AppD config saved for {lob_name}/{track}: id={config_id}")
                return {'success': True, 'config_id': config_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving AppD config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_appd_config(self, lob_name: str, track: str) -> Optional[Dict]:
        """Get AppD config by LOB and track."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, CONTROLLER_URL,
                           ACCOUNT_NAME, TOKEN_ENV_VAR, APPLICATION_NAMES,
                           TIER_FILTER, NODE_FILTER, COLLECTION_INTERVAL,
                           IS_ACTIVE, LAST_TEST_STATUS, LAST_TEST_DATE,
                           CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
                    FROM API_NFT_APPD_CONFIG
                    WHERE LOB_NAME = :lob_name AND TRACK = :track
                      AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track': track})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'controller_url': row[3], 'account_name': row[4],
                    'token_env_var': row[5], 'application_names': row[6],
                    'tier_filter': row[7], 'node_filter': row[8],
                    'collection_interval': row[9], 'is_active': row[10] == 'Y',
                    'last_test_status': row[11], 'last_test_date': row[12],
                    'created_by': row[13],
                    'created_date': row[14].isoformat() if row[14] else None,
                    'updated_by': row[15],
                    'updated_date': row[16].isoformat() if row[16] else None
                }
            except Exception as e:
                logger.error(f"Error getting AppD config: {e}")
                return None
            finally:
                cursor.close()

    def get_appd_config_by_id(self, config_id: int) -> Optional[Dict]:
        """Get AppD config by config_id."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, CONTROLLER_URL,
                           ACCOUNT_NAME, TOKEN_ENV_VAR, APPLICATION_NAMES,
                           TIER_FILTER, NODE_FILTER, COLLECTION_INTERVAL,
                           IS_ACTIVE, LAST_TEST_STATUS, LAST_TEST_DATE,
                           CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
                    FROM API_NFT_APPD_CONFIG
                    WHERE CONFIG_ID = :config_id
                """, {'config_id': config_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'controller_url': row[3], 'account_name': row[4],
                    'token_env_var': row[5], 'application_names': row[6],
                    'tier_filter': row[7], 'node_filter': row[8],
                    'collection_interval': row[9], 'is_active': row[10] == 'Y',
                    'last_test_status': row[11], 'last_test_date': row[12],
                    'created_by': row[13],
                    'created_date': row[14].isoformat() if row[14] else None,
                    'updated_by': row[15],
                    'updated_date': row[16].isoformat() if row[16] else None
                }
            except Exception as e:
                logger.error(f"Error getting AppD config by id: {e}")
                return None
            finally:
                cursor.close()

    def update_appd_config(self, config_id: int, updated_by: str, **kwargs) -> Dict:
        """Update AppD config fields. Only updates provided kwargs."""
        allowed = {'controller_url', 'account_name', 'token_env_var',
                   'application_names', 'tier_filter', 'node_filter',
                   'collection_interval', 'is_active', 'last_test_status'}
        sets = []
        params = {'config_id': config_id, 'updated_by': updated_by}
        for k, v in kwargs.items():
            if k in allowed:
                col = k.upper()
                sets.append(f"{col} = :{k}")
                params[k] = v
        if not sets:
            return {'success': False, 'error': 'No valid fields to update'}
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                sql = f"""
                    UPDATE API_NFT_APPD_CONFIG
                    SET {', '.join(sets)},
                        UPDATED_BY = :updated_by,
                        UPDATED_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """
                cursor.execute(sql, params)
                conn.commit()
                return {'success': True, 'rows_updated': cursor.rowcount}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating AppD config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def delete_appd_config(self, config_id: int, updated_by: str) -> Dict:
        """Soft delete AppD config (set IS_ACTIVE = N)."""
        return self.update_appd_config(config_id, updated_by, is_active='N')

    def update_appd_test_status(self, config_id: int, status: str) -> None:
        """Update last test status after connection test."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_APPD_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'status': status, 'config_id': config_id})
                conn.commit()
            except Exception as e:
                logger.error(f"Error updating AppD test status: {e}")
            finally:
                cursor.close()

    # =========================================================================
    # KIBANA CONFIG  (same pattern as AppD)
    # =========================================================================

    def save_kibana_config(self, lob_name: str, track: str, kibana_url: str,
                            dashboard_id: Optional[str], display_name: Optional[str],
                            index_pattern: Optional[str], token_env_var: Optional[str],
                            time_field: str, default_time_range: str,
                            custom_filters: Optional[str], created_by: str) -> Dict:
        """Create Kibana config."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                config_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_KIBANA_CONFIG (
                        CONFIG_ID, LOB_NAME, TRACK, KIBANA_URL, DASHBOARD_ID,
                        DISPLAY_NAME, INDEX_PATTERN, TOKEN_ENV_VAR, TIME_FIELD,
                        DEFAULT_TIME_RANGE, CUSTOM_FILTERS, CREATED_BY
                    ) VALUES (
                        API_NFT_KIBANA_CFG_SEQ.NEXTVAL, :lob_name, :track,
                        :kibana_url, :dashboard_id, :display_name, :index_pattern,
                        :token_env_var, :time_field, :default_time_range,
                        :custom_filters, :created_by
                    ) RETURNING CONFIG_ID INTO :config_id
                """, {
                    'lob_name': lob_name, 'track': track, 'kibana_url': kibana_url,
                    'dashboard_id': dashboard_id, 'display_name': display_name,
                    'index_pattern': index_pattern, 'token_env_var': token_env_var,
                    'time_field': time_field, 'default_time_range': default_time_range,
                    'custom_filters': custom_filters, 'created_by': created_by,
                    'config_id': config_id_var
                })
                conn.commit()
                config_id = config_id_var.getvalue()[0]
                return {'success': True, 'config_id': config_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving Kibana config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_kibana_config(self, lob_name: str, track: str) -> Optional[Dict]:
        """Get Kibana config by LOB and track."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, KIBANA_URL, DASHBOARD_ID,
                           DISPLAY_NAME, INDEX_PATTERN, TOKEN_ENV_VAR, TIME_FIELD,
                           DEFAULT_TIME_RANGE, CUSTOM_FILTERS, IS_ACTIVE,
                           LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                    FROM API_NFT_KIBANA_CONFIG
                    WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track': track})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'kibana_url': row[3], 'dashboard_id': row[4],
                    'display_name': row[5], 'index_pattern': row[6],
                    'token_env_var': row[7], 'time_field': row[8],
                    'default_time_range': row[9], 'custom_filters': row[10],
                    'is_active': row[11] == 'Y', 'last_test_status': row[12],
                    'last_test_date': row[13],
                    'created_by': row[14],
                    'created_date': row[15].isoformat() if row[15] else None
                }
            except Exception as e:
                logger.error(f"Error getting Kibana config: {e}")
                return None
            finally:
                cursor.close()

    def get_kibana_config_by_id(self, config_id: int) -> Optional[Dict]:
        """Get Kibana config by config_id."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, KIBANA_URL, DASHBOARD_ID,
                           DISPLAY_NAME, INDEX_PATTERN, TOKEN_ENV_VAR, TIME_FIELD,
                           DEFAULT_TIME_RANGE, CUSTOM_FILTERS, IS_ACTIVE,
                           LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                    FROM API_NFT_KIBANA_CONFIG
                    WHERE CONFIG_ID = :config_id
                """, {'config_id': config_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'kibana_url': row[3], 'dashboard_id': row[4],
                    'display_name': row[5], 'index_pattern': row[6],
                    'token_env_var': row[7], 'time_field': row[8],
                    'default_time_range': row[9], 'custom_filters': row[10],
                    'is_active': row[11] == 'Y', 'last_test_status': row[12],
                    'last_test_date': row[13],
                    'created_by': row[14],
                    'created_date': row[15].isoformat() if row[15] else None
                }
            except Exception as e:
                logger.error(f"Error getting Kibana config by id: {e}")
                return None
            finally:
                cursor.close()

    def delete_kibana_config(self, config_id: int, updated_by: str) -> Dict:
        """Soft delete Kibana config."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_KIBANA_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :updated_by, UPDATED_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'updated_by': updated_by, 'config_id': config_id})
                conn.commit()
                return {'success': True, 'rows_updated': cursor.rowcount}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error deleting Kibana config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_kibana_test_status(self, config_id: int, status: str) -> None:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_KIBANA_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'status': status, 'config_id': config_id})
                conn.commit()
            except Exception as e:
                logger.error(f"Error updating Kibana test status: {e}")
            finally:
                cursor.close()

    # =========================================================================
    # SPLUNK CONFIG
    # =========================================================================

    def save_splunk_config(self, lob_name: str, track: str, splunk_url: str,
                            token_env_var: str, default_index: Optional[str],
                            saved_search_name: Optional[str], spl_query: Optional[str],
                            search_type: str, dashboard_name: Optional[str],
                            time_range: str, error_patterns: Optional[str],
                            created_by: str) -> Dict:
        """Create Splunk config."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                config_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_SPLUNK_CONFIG (
                        CONFIG_ID, LOB_NAME, TRACK, SPLUNK_URL, TOKEN_ENV_VAR,
                        DEFAULT_INDEX, SAVED_SEARCH_NAME, SPL_QUERY, SEARCH_TYPE,
                        DASHBOARD_NAME, TIME_RANGE, ERROR_PATTERNS, CREATED_BY
                    ) VALUES (
                        API_NFT_SPLUNK_CFG_SEQ.NEXTVAL, :lob_name, :track,
                        :splunk_url, :token_env_var, :default_index,
                        :saved_search_name, :spl_query, :search_type,
                        :dashboard_name, :time_range, :error_patterns, :created_by
                    ) RETURNING CONFIG_ID INTO :config_id
                """, {
                    'lob_name': lob_name, 'track': track, 'splunk_url': splunk_url,
                    'token_env_var': token_env_var, 'default_index': default_index,
                    'saved_search_name': saved_search_name, 'spl_query': spl_query,
                    'search_type': search_type, 'dashboard_name': dashboard_name,
                    'time_range': time_range, 'error_patterns': error_patterns,
                    'created_by': created_by, 'config_id': config_id_var
                })
                conn.commit()
                config_id = config_id_var.getvalue()[0]
                return {'success': True, 'config_id': config_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving Splunk config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_splunk_config(self, lob_name: str, track: str) -> Optional[Dict]:
        """Get Splunk config by LOB and track."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, SPLUNK_URL, TOKEN_ENV_VAR,
                           DEFAULT_INDEX, SAVED_SEARCH_NAME, SPL_QUERY, SEARCH_TYPE,
                           DASHBOARD_NAME, TIME_RANGE, ERROR_PATTERNS, IS_ACTIVE,
                           LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                    FROM API_NFT_SPLUNK_CONFIG
                    WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track': track})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'splunk_url': row[3], 'token_env_var': row[4],
                    'default_index': row[5], 'saved_search_name': row[6],
                    'spl_query': row[7].read() if row[7] else None,
                    'search_type': row[8], 'dashboard_name': row[9],
                    'time_range': row[10], 'error_patterns': row[11],
                    'is_active': row[12] == 'Y', 'last_test_status': row[13],
                    'last_test_date': row[14],
                    'created_by': row[15],
                    'created_date': row[16].isoformat() if row[16] else None
                }
            except Exception as e:
                logger.error(f"Error getting Splunk config: {e}")
                return None
            finally:
                cursor.close()

    def delete_splunk_config(self, config_id: int, updated_by: str) -> Dict:
        """Soft delete Splunk config."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_SPLUNK_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :updated_by, UPDATED_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'updated_by': updated_by, 'config_id': config_id})
                conn.commit()
                return {'success': True, 'rows_updated': cursor.rowcount}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error deleting Splunk config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_splunk_test_status(self, config_id: int, status: str) -> None:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_SPLUNK_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'status': status, 'config_id': config_id})
                conn.commit()
            except Exception as e:
                logger.error(f"Error updating Splunk test status: {e}")
            finally:
                cursor.close()

    # =========================================================================
    # MONGODB CONFIG
    # =========================================================================

    def save_mongodb_config(self, lob_name: str, track: str, uri_env_var: str,
                             database_name: str, collection_names: Optional[str],
                             replica_set: Optional[str], auth_db: str,
                             slow_query_ms: int, created_by: str) -> Dict:
        """Create MongoDB config."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                config_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_MONGODB_CONFIG (
                        CONFIG_ID, LOB_NAME, TRACK, URI_ENV_VAR, DATABASE_NAME,
                        COLLECTION_NAMES, REPLICA_SET, AUTH_DB, SLOW_QUERY_MS,
                        CREATED_BY
                    ) VALUES (
                        API_NFT_MONGODB_CFG_SEQ.NEXTVAL, :lob_name, :track,
                        :uri_env_var, :database_name, :collection_names,
                        :replica_set, :auth_db, :slow_query_ms, :created_by
                    ) RETURNING CONFIG_ID INTO :config_id
                """, {
                    'lob_name': lob_name, 'track': track, 'uri_env_var': uri_env_var,
                    'database_name': database_name, 'collection_names': collection_names,
                    'replica_set': replica_set, 'auth_db': auth_db,
                    'slow_query_ms': slow_query_ms, 'created_by': created_by,
                    'config_id': config_id_var
                })
                conn.commit()
                config_id = config_id_var.getvalue()[0]
                return {'success': True, 'config_id': config_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving MongoDB config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_mongodb_config(self, lob_name: str, track: str) -> Optional[Dict]:
        """Get MongoDB config by LOB and track."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, URI_ENV_VAR, DATABASE_NAME,
                           COLLECTION_NAMES, REPLICA_SET, AUTH_DB, SLOW_QUERY_MS,
                           IS_ACTIVE, LAST_TEST_STATUS, LAST_TEST_DATE,
                           CREATED_BY, CREATED_DATE
                    FROM API_NFT_MONGODB_CONFIG
                    WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track': track})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'uri_env_var': row[3], 'database_name': row[4],
                    'collection_names': row[5], 'replica_set': row[6],
                    'auth_db': row[7], 'slow_query_ms': row[8],
                    'is_active': row[9] == 'Y', 'last_test_status': row[10],
                    'last_test_date': row[11],
                    'created_by': row[12],
                    'created_date': row[13].isoformat() if row[13] else None
                }
            except Exception as e:
                logger.error(f"Error getting MongoDB config: {e}")
                return None
            finally:
                cursor.close()

    def delete_mongodb_config(self, config_id: int, updated_by: str) -> Dict:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_MONGODB_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :updated_by, UPDATED_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'updated_by': updated_by, 'config_id': config_id})
                conn.commit()
                return {'success': True, 'rows_updated': cursor.rowcount}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_mongodb_test_status(self, config_id: int, status: str) -> None:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_MONGODB_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'status': status, 'config_id': config_id})
                conn.commit()
            except Exception as e:
                logger.error(f"Error updating MongoDB test status: {e}")
            finally:
                cursor.close()

    # =========================================================================
    # PC CONFIG
    # =========================================================================

    def save_pc_config(self, lob_name: str, track: str, pc_url: str,
                        pc_domain: str, pc_project: str, username: str,
                        password_env_var: str, duration_format: str,
                        cookie_flag: str, default_timeout_min: int,
                        created_by: str) -> Dict:
        """Create PC config."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                config_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_PC_CONFIG (
                        CONFIG_ID, LOB_NAME, TRACK, PC_URL, PC_DOMAIN,
                        PC_PROJECT, USERNAME, PASSWORD_ENV_VAR, DURATION_FORMAT,
                        COOKIE_FLAG, DEFAULT_TIMEOUT_MIN, CREATED_BY
                    ) VALUES (
                        API_NFT_PC_CFG_SEQ.NEXTVAL, :lob_name, :track, :pc_url,
                        :pc_domain, :pc_project, :username, :password_env_var,
                        :duration_format, :cookie_flag, :default_timeout_min,
                        :created_by
                    ) RETURNING CONFIG_ID INTO :config_id
                """, {
                    'lob_name': lob_name, 'track': track, 'pc_url': pc_url,
                    'pc_domain': pc_domain, 'pc_project': pc_project,
                    'username': username, 'password_env_var': password_env_var,
                    'duration_format': duration_format, 'cookie_flag': cookie_flag,
                    'default_timeout_min': default_timeout_min,
                    'created_by': created_by, 'config_id': config_id_var
                })
                conn.commit()
                config_id = config_id_var.getvalue()[0]
                return {'success': True, 'config_id': config_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving PC config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_pc_config(self, lob_name: str, track: str) -> Optional[Dict]:
        """Get PC config by LOB and track."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, PC_URL, PC_DOMAIN,
                           PC_PROJECT, USERNAME, PASSWORD_ENV_VAR, DURATION_FORMAT,
                           COOKIE_FLAG, DEFAULT_TIMEOUT_MIN, LAST_RUN_ID,
                           IS_ACTIVE, LAST_TEST_STATUS, LAST_TEST_DATE,
                           CREATED_BY, CREATED_DATE
                    FROM API_NFT_PC_CONFIG
                    WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track': track})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'pc_url': row[3], 'pc_domain': row[4], 'pc_project': row[5],
                    'username': row[6], 'password_env_var': row[7],
                    'duration_format': row[8], 'cookie_flag': row[9],
                    'default_timeout_min': row[10], 'last_run_id': row[11],
                    'is_active': row[12] == 'Y', 'last_test_status': row[13],
                    'last_test_date': row[14],
                    'created_by': row[15],
                    'created_date': row[16].isoformat() if row[16] else None
                }
            except Exception as e:
                logger.error(f"Error getting PC config: {e}")
                return None
            finally:
                cursor.close()

    def delete_pc_config(self, config_id: int, updated_by: str) -> Dict:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_PC_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :updated_by, UPDATED_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'updated_by': updated_by, 'config_id': config_id})
                conn.commit()
                return {'success': True, 'rows_updated': cursor.rowcount}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_pc_test_status(self, config_id: int, status: str) -> None:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_PC_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'status': status, 'config_id': config_id})
                conn.commit()
            except Exception as e:
                logger.error(f"Error updating PC test status: {e}")
            finally:
                cursor.close()

    # =========================================================================
    # DB CONFIG
    # =========================================================================

    def save_db_config(self, lob_name: str, track: str, db_alias: str,
                        host: str, port: int, service_name: str,
                        username: str, password_env_var: str,
                        use_cyberark: bool, cyberark_safe: Optional[str],
                        cyberark_object: Optional[str], created_by: str) -> Dict:
        """Create DB config."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                config_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_DB_CONFIG (
                        CONFIG_ID, LOB_NAME, TRACK, DB_ALIAS, HOST, PORT,
                        SERVICE_NAME, USERNAME, PASSWORD_ENV_VAR, USE_CYBERARK,
                        CYBERARK_SAFE, CYBERARK_OBJECT, CREATED_BY
                    ) VALUES (
                        API_NFT_DB_CFG_SEQ.NEXTVAL, :lob_name, :track, :db_alias,
                        :host, :port, :service_name, :username, :password_env_var,
                        :use_cyberark, :cyberark_safe, :cyberark_object, :created_by
                    ) RETURNING CONFIG_ID INTO :config_id
                """, {
                    'lob_name': lob_name, 'track': track, 'db_alias': db_alias,
                    'host': host, 'port': port, 'service_name': service_name,
                    'username': username, 'password_env_var': password_env_var,
                    'use_cyberark': 'Y' if use_cyberark else 'N',
                    'cyberark_safe': cyberark_safe, 'cyberark_object': cyberark_object,
                    'created_by': created_by, 'config_id': config_id_var
                })
                conn.commit()
                config_id = config_id_var.getvalue()[0]
                return {'success': True, 'config_id': config_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving DB config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_db_config(self, lob_name: str, track: str) -> Optional[Dict]:
        """Get DB config by LOB and track."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, TRACK, DB_ALIAS, HOST, PORT,
                           SERVICE_NAME, USERNAME, PASSWORD_ENV_VAR, USE_CYBERARK,
                           CYBERARK_SAFE, CYBERARK_OBJECT, IS_ACTIVE,
                           LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                    FROM API_NFT_DB_CONFIG
                    WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track': track})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'db_alias': row[3], 'host': row[4], 'port': row[5],
                    'service_name': row[6], 'username': row[7],
                    'password_env_var': row[8], 'use_cyberark': row[9] == 'Y',
                    'cyberark_safe': row[10], 'cyberark_object': row[11],
                    'is_active': row[12] == 'Y', 'last_test_status': row[13],
                    'last_test_date': row[14],
                    'created_by': row[15],
                    'created_date': row[16].isoformat() if row[16] else None
                }
            except Exception as e:
                logger.error(f"Error getting DB config: {e}")
                return None
            finally:
                cursor.close()

    def delete_db_config(self, config_id: int, updated_by: str) -> Dict:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_DB_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :updated_by, UPDATED_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'updated_by': updated_by, 'config_id': config_id})
                conn.commit()
                return {'success': True, 'rows_updated': cursor.rowcount}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_db_test_status(self, config_id: int, status: str) -> None:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_DB_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE
                    WHERE CONFIG_ID = :config_id
                """, {'status': status, 'config_id': config_id})
                conn.commit()
            except Exception as e:
                logger.error(f"Error updating DB test status: {e}")
            finally:
                cursor.close()

    # =========================================================================
    # TRACK TEMPLATE
    # =========================================================================

    def save_track_template(self, lob_name: str, track: str,
                             appd_config_ids: Optional[str],
                             kibana_config_ids: Optional[str],
                             splunk_config_ids: Optional[str],
                             mongodb_config_ids: Optional[str],
                             pc_config_ids: Optional[str],
                             db_config_ids: Optional[str],
                             created_by: str) -> Dict:
        """Create track template linking all tool configs."""

        def count_ids(ids_str):
            if not ids_str:
                return 0
            return len([x for x in ids_str.split(',') if x.strip()])

        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                template_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_TRACK_TEMPLATE (
                        TEMPLATE_ID, LOB_NAME, TRACK,
                        APPD_CONFIG_IDS, KIBANA_CONFIG_IDS, SPLUNK_CONFIG_IDS,
                        MONGODB_CONFIG_IDS, PC_CONFIG_IDS, DB_CONFIG_IDS,
                        APPD_COUNT, KIBANA_COUNT, SPLUNK_COUNT,
                        MONGODB_COUNT, PC_COUNT, DB_COUNT,
                        CREATED_BY
                    ) VALUES (
                        API_NFT_TRACK_TPL_SEQ.NEXTVAL, :lob_name, :track,
                        :appd_config_ids, :kibana_config_ids, :splunk_config_ids,
                        :mongodb_config_ids, :pc_config_ids, :db_config_ids,
                        :appd_count, :kibana_count, :splunk_count,
                        :mongodb_count, :pc_count, :db_count,
                        :created_by
                    ) RETURNING TEMPLATE_ID INTO :template_id
                """, {
                    'lob_name': lob_name, 'track': track,
                    'appd_config_ids': appd_config_ids,
                    'kibana_config_ids': kibana_config_ids,
                    'splunk_config_ids': splunk_config_ids,
                    'mongodb_config_ids': mongodb_config_ids,
                    'pc_config_ids': pc_config_ids,
                    'db_config_ids': db_config_ids,
                    'appd_count': count_ids(appd_config_ids),
                    'kibana_count': count_ids(kibana_config_ids),
                    'splunk_count': count_ids(splunk_config_ids),
                    'mongodb_count': count_ids(mongodb_config_ids),
                    'pc_count': count_ids(pc_config_ids),
                    'db_count': count_ids(db_config_ids),
                    'created_by': created_by,
                    'template_id': template_id_var
                })
                conn.commit()
                template_id = template_id_var.getvalue()[0]
                logger.info(f"Track template saved: {lob_name}/{track} id={template_id}")
                return {'success': True, 'template_id': template_id}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving track template: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_track_template(self, lob_name: str, track: str) -> Optional[Dict]:
        """Get track template by LOB and track."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT TEMPLATE_ID, LOB_NAME, TRACK,
                           APPD_CONFIG_IDS, KIBANA_CONFIG_IDS, SPLUNK_CONFIG_IDS,
                           MONGODB_CONFIG_IDS, PC_CONFIG_IDS, DB_CONFIG_IDS,
                           APPD_COUNT, KIBANA_COUNT, SPLUNK_COUNT,
                           MONGODB_COUNT, PC_COUNT, DB_COUNT,
                           IS_ACTIVE, CREATED_BY, CREATED_DATE,
                           UPDATED_BY, UPDATED_DATE
                    FROM API_NFT_TRACK_TEMPLATE
                    WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track': track})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'template_id': row[0], 'lob_name': row[1], 'track': row[2],
                    'appd_config_ids': row[3], 'kibana_config_ids': row[4],
                    'splunk_config_ids': row[5], 'mongodb_config_ids': row[6],
                    'pc_config_ids': row[7], 'db_config_ids': row[8],
                    'appd_count': row[9], 'kibana_count': row[10],
                    'splunk_count': row[11], 'mongodb_count': row[12],
                    'pc_count': row[13], 'db_count': row[14],
                    'is_active': row[15] == 'Y',
                    'created_by': row[16],
                    'created_date': row[17].isoformat() if row[17] else None,
                    'updated_by': row[18],
                    'updated_date': row[19].isoformat() if row[19] else None
                }
            except Exception as e:
                logger.error(f"Error getting track template: {e}")
                return None
            finally:
                cursor.close()

    def list_track_templates(self, lob_name: Optional[str] = None) -> List[Dict]:
        """List all active track templates, optionally filtered by LOB."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if lob_name:
                    cursor.execute("""
                        SELECT TEMPLATE_ID, LOB_NAME, TRACK,
                               APPD_COUNT, KIBANA_COUNT, SPLUNK_COUNT,
                               MONGODB_COUNT, PC_COUNT, DB_COUNT,
                               IS_ACTIVE, CREATED_DATE
                        FROM API_NFT_TRACK_TEMPLATE
                        WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                        ORDER BY TRACK
                    """, {'lob_name': lob_name})
                else:
                    cursor.execute("""
                        SELECT TEMPLATE_ID, LOB_NAME, TRACK,
                               APPD_COUNT, KIBANA_COUNT, SPLUNK_COUNT,
                               MONGODB_COUNT, PC_COUNT, DB_COUNT,
                               IS_ACTIVE, CREATED_DATE
                        FROM API_NFT_TRACK_TEMPLATE
                        WHERE IS_ACTIVE = 'Y'
                        ORDER BY LOB_NAME, TRACK
                    """)
                columns = ['template_id', 'lob_name', 'track',
                           'appd_count', 'kibana_count', 'splunk_count',
                           'mongodb_count', 'pc_count', 'db_count',
                           'is_active', 'created_date']
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                logger.error(f"Error listing track templates: {e}")
                return []
            finally:
                cursor.close()

    def delete_track_template(self, lob_name: str, track: str,
                               updated_by: str) -> Dict:
        """Soft delete track template."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_TRACK_TEMPLATE
                    SET IS_ACTIVE = 'N', UPDATED_BY = :updated_by, UPDATED_DATE = SYSDATE
                    WHERE LOB_NAME = :lob_name AND TRACK = :track AND IS_ACTIVE = 'Y'
                """, {'updated_by': updated_by, 'lob_name': lob_name, 'track': track})
                conn.commit()
                if cursor.rowcount > 0:
                    return {'success': True, 'message': f'Template deleted for {lob_name}/{track}'}
                return {'success': False, 'error': 'Template not found'}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error deleting track template: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================================
    # RELEASE REPORTS
    # =========================================================================

    def save_release_report(self, run_id: str, lob_name: str, track: Optional[str],
                             test_name: Optional[str], test_type: Optional[str],
                             pc_run_id: Optional[str], report_title: Optional[str],
                             report_html: str, generated_by: str,
                             retain_until=None, notes: Optional[str] = None) -> Dict:
        """Save final test report HTML as CLOB."""
        report_size_kb = len(report_html.encode('utf-8')) // 1024
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                report_id_var = cursor.var(int)
                cursor.execute("""
                    INSERT INTO API_NFT_RELEASE_REPORTS (
                        REPORT_ID, RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                        TEST_TYPE, PC_RUN_ID, REPORT_TITLE, REPORT_HTML,
                        REPORT_SIZE_KB, GENERATED_BY, RETAIN_UNTIL, NOTES
                    ) VALUES (
                        API_NFT_REPORT_SEQ.NEXTVAL, :run_id, :lob_name, :track,
                        :test_name, :test_type, :pc_run_id, :report_title,
                        :report_html, :report_size_kb, :generated_by,
                        :retain_until, :notes
                    ) RETURNING REPORT_ID INTO :report_id
                """, {
                    'run_id': run_id, 'lob_name': lob_name, 'track': track,
                    'test_name': test_name, 'test_type': test_type,
                    'pc_run_id': pc_run_id, 'report_title': report_title,
                    'report_html': report_html, 'report_size_kb': report_size_kb,
                    'generated_by': generated_by, 'retain_until': retain_until,
                    'notes': notes, 'report_id': report_id_var
                })
                conn.commit()
                report_id = report_id_var.getvalue()[0]
                logger.info(f"Release report saved: run_id={run_id} size={report_size_kb}KB")
                return {'success': True, 'report_id': report_id,
                        'report_size_kb': report_size_kb}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving release report: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def list_release_reports(self, lob_name: Optional[str] = None,
                              limit: int = 50) -> List[Dict]:
        """List release reports (metadata only, no HTML)."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if lob_name:
                    cursor.execute("""
                        SELECT REPORT_ID, RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                               TEST_TYPE, PC_RUN_ID, REPORT_TITLE, REPORT_SIZE_KB,
                               GENERATED_BY, GENERATED_DATE, RETAIN_UNTIL, IS_ACTIVE
                        FROM API_NFT_RELEASE_REPORTS
                        WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                        ORDER BY GENERATED_DATE DESC
                        FETCH FIRST :limit ROWS ONLY
                    """, {'lob_name': lob_name, 'limit': limit})
                else:
                    cursor.execute("""
                        SELECT REPORT_ID, RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                               TEST_TYPE, PC_RUN_ID, REPORT_TITLE, REPORT_SIZE_KB,
                               GENERATED_BY, GENERATED_DATE, RETAIN_UNTIL, IS_ACTIVE
                        FROM API_NFT_RELEASE_REPORTS
                        WHERE IS_ACTIVE = 'Y'
                        ORDER BY GENERATED_DATE DESC
                        FETCH FIRST :limit ROWS ONLY
                    """, {'limit': limit})
                columns = ['report_id', 'run_id', 'lob_name', 'track', 'test_name',
                           'test_type', 'pc_run_id', 'report_title', 'report_size_kb',
                           'generated_by', 'generated_date', 'retain_until', 'is_active']
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                logger.error(f"Error listing release reports: {e}")
                return []
            finally:
                cursor.close()

    def get_release_report(self, report_id: int) -> Optional[Dict]:
        """Get full release report including HTML CLOB."""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT REPORT_ID, RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                           TEST_TYPE, PC_RUN_ID, REPORT_TITLE, REPORT_HTML,
                           REPORT_SIZE_KB, GENERATED_BY, GENERATED_DATE,
                           RETAIN_UNTIL, IS_ACTIVE, NOTES
                    FROM API_NFT_RELEASE_REPORTS
                    WHERE REPORT_ID = :report_id AND IS_ACTIVE = 'Y'
                """, {'report_id': report_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'report_id': row[0], 'run_id': row[1], 'lob_name': row[2],
                    'track': row[3], 'test_name': row[4], 'test_type': row[5],
                    'pc_run_id': row[6], 'report_title': row[7],
                    'report_html': row[8].read() if row[8] else None,  # Read CLOB
                    'report_size_kb': row[9], 'generated_by': row[10],
                    'generated_date': row[11].isoformat() if row[11] else None,
                    'retain_until': row[12].isoformat() if row[12] else None,
                    'is_active': row[13] == 'Y', 'notes': row[14]
                }
            except Exception as e:
                logger.error(f"Error getting release report {report_id}: {e}")
                return None
            finally:
                cursor.close()
