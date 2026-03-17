"""
NFT Platform Database Layer
Handles all DB operations for the new API_NFT_* tables.
Follows exact pattern of monitoring/appd/database.py and monitoring/pc/database.py:
  - self.pool (OracleConnectionPool)
  - with self.pool.get_connection() as conn
  - cursor = conn.cursor()
  - try/except/finally with cursor.close()
  - Row indexed access: row[0], row[1] etc.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class NFTPlatformDatabase:
    """Database operations for CQE NFT platform config and registration tables."""

    def __init__(self, pool):
        self.pool = pool

    # =========================================================
    # USER LOB ACCESS
    # =========================================================

    def get_user_lob_access(self, username: str) -> List[Dict]:
        """Get all LOBs accessible to a user. Uses correct column names from DESCRIBE."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY, IS_ACTIVE,
                           GRANTED_DATE, REVOKED_BY, REVOKED_DATE, UPDATED_DATE
                    FROM API_NFT_USER_LOB_ACCESS
                    WHERE USERNAME = :username AND IS_ACTIVE = 'Y'
                    ORDER BY LOB_NAME
                """, {'username': username})
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    result.append({
                        'access_id':   row[0],
                        'username':    row[1],
                        'lob_name':    row[2],
                        'granted_by':  row[3],
                        'is_active':   row[4],
                        'granted_date': row[5].isoformat() if row[5] else None,
                        'revoked_by':  row[6],
                        'revoked_date': row[7].isoformat() if row[7] else None,
                        'updated_date': row[8].isoformat() if row[8] else None,
                    })
                return result
            except Exception as e:
                logger.error(f"Error getting user LOB access for {username}: {e}", exc_info=True)
                return []
            finally:
                cursor.close()

    def grant_user_lob_access(self, username: str, lob_name: str, granted_by: str) -> Dict:
        """Grant a user access to a LOB. Uses correct column names from DESCRIBE."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # Check if row already exists (may be inactive from prior revoke)
                cursor.execute("""
                    SELECT ACCESS_ID FROM API_NFT_USER_LOB_ACCESS
                    WHERE USERNAME = :username AND LOB_NAME = :lob_name
                """, {'username': username, 'lob_name': lob_name})
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE API_NFT_USER_LOB_ACCESS
                        SET IS_ACTIVE    = 'Y',
                            GRANTED_BY   = :granted_by,
                            GRANTED_DATE = SYSDATE,
                            REVOKED_BY   = NULL,
                            REVOKED_DATE = NULL,
                            UPDATED_DATE = SYSDATE
                        WHERE USERNAME = :username AND LOB_NAME = :lob_name
                    """, {'granted_by': granted_by, 'username': username, 'lob_name': lob_name})
                else:
                    cursor.execute("""
                        INSERT INTO API_NFT_USER_LOB_ACCESS (
                            ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY,
                            GRANTED_DATE, IS_ACTIVE, UPDATED_DATE
                        ) VALUES (
                            API_NFT_ULA_SEQ.NEXTVAL,
                            :username, :lob_name, :granted_by,
                            SYSDATE, 'Y', SYSDATE
                        )
                    """, {'username': username, 'lob_name': lob_name, 'granted_by': granted_by})
                conn.commit()
                logger.info(f"LOB access granted: {username} -> {lob_name} by {granted_by}")
                return {'success': True, 'message': f'Access to {lob_name} granted for {username}'}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False, 'error': f'User {username} already has access to {lob_name}'}
                logger.error(f"Error granting LOB access: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def revoke_user_lob_access(self, username: str, lob_name: str, revoked_by: str) -> Dict:
        """Revoke user access to a LOB (soft delete)."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_USER_LOB_ACCESS
                    SET IS_ACTIVE    = 'N',
                            REVOKED_BY   = :revoked_by,
                            REVOKED_DATE = SYSDATE,
                            UPDATED_DATE = SYSDATE
                    WHERE USERNAME = :username AND LOB_NAME = :lob_name
                """, {'username': username, 'lob_name': lob_name})
                conn.commit()
                return {'success': True, 'message': f'Access to {lob_name} revoked for {username}'}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error revoking LOB access: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def list_users_with_lob_access(self, lob_name: Optional[str] = None) -> List[Dict]:
        """List all users with optional LOB filter."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                if lob_name:
                    cursor.execute("""
                        SELECT ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY, IS_ACTIVE, CREATED_DATE
                        FROM API_NFT_USER_LOB_ACCESS
                        WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                        ORDER BY USERNAME
                    """, {'lob_name': lob_name})
                else:
                    cursor.execute("""
                        SELECT ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY, IS_ACTIVE, CREATED_DATE
                        FROM API_NFT_USER_LOB_ACCESS
                        WHERE IS_ACTIVE = 'Y'
                        ORDER BY LOB_NAME, USERNAME
                    """)
                rows = cursor.fetchall()
                columns = ['id', 'username', 'lob_name', 'granted_by', 'is_active', 'created_date']
                return [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                logger.error(f"Error listing users with LOB access: {e}")
                return []
            finally:
                cursor.close()

    # =========================================================
    # APPD CONFIG
    # =========================================================

    def get_appd_config(self, lob_name: str) -> Optional[Dict]:
        """Get AppDynamics config for a LOB."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT CONFIG_ID, LOB_NAME, CONTROLLER_URL, ACCOUNT_NAME,
                           TOKEN_ENV_VAR, DEFAULT_NODE_COUNT, IS_ACTIVE,
                           CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
                    FROM API_NFT_APPD_CONFIG
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'config_id': row[0], 'lob_name': row[1],
                    'controller_url': row[2], 'account_name': row[3],
                    'token_env_var': row[4], 'default_node_count': row[5],
                    'is_active': row[6] == 'Y',
                    'created_by': row[7],
                    'created_date': row[8].isoformat() if row[8] else None,
                    'updated_by': row[9], 'updated_date': row[10].isoformat() if row[10] else None
                }
            except Exception as e:
                logger.error(f"Error getting AppD config for {lob_name}: {e}")
                return None
            finally:
                cursor.close()

    def save_appd_config(self, lob_name: str, controller_url: str, account_name: str,
                         token_env_var: str, default_node_count: int, created_by: str) -> Dict:
        """Insert or update AppDynamics config."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # Check if exists
                cursor.execute(
                    "SELECT CONFIG_ID FROM API_NFT_APPD_CONFIG WHERE LOB_NAME = :lob_name",
                    {'lob_name': lob_name}
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE API_NFT_APPD_CONFIG
                        SET CONTROLLER_URL = :url, ACCOUNT_NAME = :account,
                            TOKEN_ENV_VAR = :token_env, DEFAULT_NODE_COUNT = :node_count,
                            UPDATED_BY = :updated_by, UPDATED_DATE = SYSDATE
                        WHERE LOB_NAME = :lob_name
                    """, {'url': controller_url, 'account': account_name,
                          'token_env': token_env_var, 'node_count': default_node_count,
                          'updated_by': created_by, 'lob_name': lob_name})
                else:
                    cursor.execute("""
                        INSERT INTO API_NFT_APPD_CONFIG
                            (LOB_NAME, CONTROLLER_URL, ACCOUNT_NAME, TOKEN_ENV_VAR,
                             DEFAULT_NODE_COUNT, IS_ACTIVE, CREATED_BY, CREATED_DATE, UPDATED_DATE)
                        VALUES (:lob_name, :url, :account, :token_env, :node_count,
                                'Y', :created_by, SYSDATE, SYSDATE)
                    """, {'lob_name': lob_name, 'url': controller_url, 'account': account_name,
                          'token_env': token_env_var, 'node_count': default_node_count,
                          'created_by': created_by})
                conn.commit()
                logger.info(f"AppD config saved for LOB: {lob_name}")
                return {'success': True, 'message': f'AppD config saved for {lob_name}'}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving AppD config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================
    # KIBANA CONFIG
    # =========================================================

    def get_kibana_configs(self, lob_name: str, track_name: Optional[str] = None) -> List[Dict]:
        """Get all Kibana configs for a LOB/Track."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                if track_name:
                    cursor.execute("""
                        SELECT KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
                               USERNAME, TOKEN_ENV_VAR, AUTH_TYPE, DASHBOARD_ID,
                               DISPLAY_NAME, INDEX_PATTERN, TIME_FIELD, IS_ACTIVE,
                               LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                        FROM API_NFT_KIBANA_CONFIG
                        WHERE LOB_NAME = :lob_name AND TRACK_NAME = :track_name
                          AND IS_ACTIVE = 'Y'
                        ORDER BY DISPLAY_NAME
                    """, {'lob_name': lob_name, 'track_name': track_name})
                else:
                    cursor.execute("""
                        SELECT KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
                               USERNAME, TOKEN_ENV_VAR, AUTH_TYPE, DASHBOARD_ID,
                               DISPLAY_NAME, INDEX_PATTERN, TIME_FIELD, IS_ACTIVE,
                               LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                        FROM API_NFT_KIBANA_CONFIG
                        WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                        ORDER BY TRACK_NAME, DISPLAY_NAME
                    """, {'lob_name': lob_name})
                rows = cursor.fetchall()
                columns = ['kibana_config_id', 'lob_name', 'track_name', 'kibana_url',
                           'username', 'token_env_var', 'auth_type', 'dashboard_id',
                           'display_name', 'index_pattern', 'time_field', 'is_active',
                           'last_test_status', 'last_test_date', 'created_by', 'created_date']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['is_active'] = d['is_active'] == 'Y'
                    d['last_test_date'] = d['last_test_date'].isoformat() if d['last_test_date'] else None
                    d['created_date'] = d['created_date'].isoformat() if d['created_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error getting Kibana configs: {e}")
                return []
            finally:
                cursor.close()

    def save_kibana_config(self, data: Dict) -> Dict:
        """Insert Kibana config."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO API_NFT_KIBANA_CONFIG
                        (LOB_NAME, TRACK_NAME, KIBANA_URL, USERNAME, TOKEN_ENV_VAR,
                         AUTH_TYPE, DASHBOARD_ID, DISPLAY_NAME, INDEX_PATTERN, TIME_FIELD,
                         IS_ACTIVE, LAST_TEST_STATUS, CREATED_BY, CREATED_DATE, UPDATED_DATE)
                    VALUES (:lob_name, :track_name, :kibana_url, :username, :token_env_var,
                            :auth_type, :dashboard_id, :display_name, :index_pattern, :time_field,
                            'Y', 'NOT_TESTED', :created_by, SYSDATE, SYSDATE)
                    RETURNING KIBANA_CONFIG_ID INTO :config_id
                """, {
                    'lob_name': data['lob_name'], 'track_name': data['track_name'],
                    'kibana_url': data['kibana_url'], 'username': data.get('username'),
                    'token_env_var': data['token_env_var'], 'auth_type': data.get('auth_type', 'apikey'),
                    'dashboard_id': data['dashboard_id'], 'display_name': data['display_name'],
                    'index_pattern': data.get('index_pattern'), 'time_field': data.get('time_field', '@timestamp'),
                    'created_by': data.get('created_by', 'admin'),
                    'config_id': cursor.var(__import__('oracledb').NUMBER)
                })
                conn.commit()
                logger.info(f"Kibana config saved: {data['display_name']} for {data['lob_name']}/{data['track_name']}")
                return {'success': True, 'message': f"Kibana config '{data['display_name']}' saved"}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False, 'error': f"Dashboard ID '{data['dashboard_id']}' already configured for this track"}
                logger.error(f"Error saving Kibana config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_kibana_test_status(self, kibana_config_id: int, status: str) -> None:
        """Update last test status for a Kibana config."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_KIBANA_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE, UPDATED_DATE = SYSDATE
                    WHERE KIBANA_CONFIG_ID = :config_id
                """, {'status': status, 'config_id': kibana_config_id})
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating Kibana test status: {e}")
            finally:
                cursor.close()

    def delete_kibana_config(self, kibana_config_id: int, deleted_by: str) -> Dict:
        """Soft delete Kibana config."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_KIBANA_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :deleted_by, UPDATED_DATE = SYSDATE
                    WHERE KIBANA_CONFIG_ID = :config_id
                """, {'deleted_by': deleted_by, 'config_id': kibana_config_id})
                conn.commit()
                return {'success': True, 'message': 'Kibana config deactivated'}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error deleting Kibana config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================
    # SPLUNK CONFIG  (same pattern as Kibana)
    # =========================================================

    def get_splunk_configs(self, lob_name: str, track_name: Optional[str] = None) -> List[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                params = {'lob_name': lob_name}
                sql = """
                    SELECT SPLUNK_CONFIG_ID, LOB_NAME, TRACK_NAME, SPLUNK_URL,
                           TOKEN_ENV_VAR, DEFAULT_INDEX, SEARCH_NAME, DISPLAY_NAME,
                           SEARCH_TYPE, SPL_QUERY, SEARCH_TIMEOUT_SEC, IS_ACTIVE,
                           LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                    FROM API_NFT_SPLUNK_CONFIG
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                """
                if track_name:
                    sql += " AND TRACK_NAME = :track_name"
                    params['track_name'] = track_name
                sql += " ORDER BY TRACK_NAME, DISPLAY_NAME"
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = ['splunk_config_id', 'lob_name', 'track_name', 'splunk_url',
                           'token_env_var', 'default_index', 'search_name', 'display_name',
                           'search_type', 'spl_query', 'search_timeout_sec', 'is_active',
                           'last_test_status', 'last_test_date', 'created_by', 'created_date']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['is_active'] = d['is_active'] == 'Y'
                    d['last_test_date'] = d['last_test_date'].isoformat() if d['last_test_date'] else None
                    d['created_date'] = d['created_date'].isoformat() if d['created_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error getting Splunk configs: {e}")
                return []
            finally:
                cursor.close()

    def save_splunk_config(self, data: Dict) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO API_NFT_SPLUNK_CONFIG
                        (LOB_NAME, TRACK_NAME, SPLUNK_URL, TOKEN_ENV_VAR, DEFAULT_INDEX,
                         SEARCH_NAME, DISPLAY_NAME, SEARCH_TYPE, SPL_QUERY, SEARCH_TIMEOUT_SEC,
                         IS_ACTIVE, LAST_TEST_STATUS, CREATED_BY, CREATED_DATE, UPDATED_DATE)
                    VALUES (:lob_name, :track_name, :splunk_url, :token_env_var, :default_index,
                            :search_name, :display_name, :search_type, :spl_query, :timeout,
                            'Y', 'NOT_TESTED', :created_by, SYSDATE, SYSDATE)
                """, {
                    'lob_name': data['lob_name'], 'track_name': data['track_name'],
                    'splunk_url': data['splunk_url'], 'token_env_var': data['token_env_var'],
                    'default_index': data.get('default_index'), 'search_name': data['search_name'],
                    'display_name': data['display_name'], 'search_type': data.get('search_type', 'search'),
                    'spl_query': data.get('spl_query'), 'timeout': data.get('search_timeout_sec', 60),
                    'created_by': data.get('created_by', 'admin')
                })
                conn.commit()
                return {'success': True, 'message': f"Splunk config '{data['display_name']}' saved"}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False, 'error': f"Search '{data['search_name']}' already configured for this track"}
                logger.error(f"Error saving Splunk config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_splunk_test_status(self, splunk_config_id: int, status: str) -> None:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_SPLUNK_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE, UPDATED_DATE = SYSDATE
                    WHERE SPLUNK_CONFIG_ID = :config_id
                """, {'status': status, 'config_id': splunk_config_id})
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating Splunk test status: {e}")
            finally:
                cursor.close()

    def delete_splunk_config(self, splunk_config_id: int, deleted_by: str) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_SPLUNK_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :deleted_by, UPDATED_DATE = SYSDATE
                    WHERE SPLUNK_CONFIG_ID = :config_id
                """, {'deleted_by': deleted_by, 'config_id': splunk_config_id})
                conn.commit()
                return {'success': True, 'message': 'Splunk config deactivated'}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================
    # MONGODB CONFIG  (same pattern)
    # =========================================================

    def get_mongodb_configs(self, lob_name: str, track_name: Optional[str] = None) -> List[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                params = {'lob_name': lob_name}
                sql = """
                    SELECT MONGODB_CONFIG_ID, LOB_NAME, TRACK_NAME, URI_ENV_VAR,
                           DATABASE_NAME, COLLECTION_NAME, DISPLAY_NAME, AUTH_DATABASE,
                           USERNAME, PASS_ENV_VAR, REPLICA_SET, SLOW_QUERY_MS,
                           READ_PREFERENCE, CONNECTION_TIMEOUT, IS_ACTIVE,
                           LAST_TEST_STATUS, LAST_TEST_DATE, CREATED_BY, CREATED_DATE
                    FROM API_NFT_MONGODB_CONFIG
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                """
                if track_name:
                    sql += " AND TRACK_NAME = :track_name"
                    params['track_name'] = track_name
                sql += " ORDER BY TRACK_NAME, DISPLAY_NAME"
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = ['mongodb_config_id', 'lob_name', 'track_name', 'uri_env_var',
                           'database_name', 'collection_name', 'display_name', 'auth_database',
                           'username', 'pass_env_var', 'replica_set', 'slow_query_ms',
                           'read_preference', 'connection_timeout', 'is_active',
                           'last_test_status', 'last_test_date', 'created_by', 'created_date']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['is_active'] = d['is_active'] == 'Y'
                    d['last_test_date'] = d['last_test_date'].isoformat() if d['last_test_date'] else None
                    d['created_date'] = d['created_date'].isoformat() if d['created_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error getting MongoDB configs: {e}")
                return []
            finally:
                cursor.close()

    def save_mongodb_config(self, data: Dict) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO API_NFT_MONGODB_CONFIG
                        (LOB_NAME, TRACK_NAME, URI_ENV_VAR, DATABASE_NAME, COLLECTION_NAME,
                         DISPLAY_NAME, AUTH_DATABASE, USERNAME, PASS_ENV_VAR, REPLICA_SET,
                         SLOW_QUERY_MS, READ_PREFERENCE, CONNECTION_TIMEOUT,
                         IS_ACTIVE, LAST_TEST_STATUS, CREATED_BY, CREATED_DATE, UPDATED_DATE)
                    VALUES (:lob_name, :track_name, :uri_env_var, :database_name, :collection_name,
                            :display_name, :auth_db, :username, :pass_env_var, :replica_set,
                            :slow_ms, :read_pref, :conn_timeout,
                            'Y', 'NOT_TESTED', :created_by, SYSDATE, SYSDATE)
                """, {
                    'lob_name': data['lob_name'], 'track_name': data['track_name'],
                    'uri_env_var': data['uri_env_var'], 'database_name': data['database_name'],
                    'collection_name': data['collection_name'], 'display_name': data['display_name'],
                    'auth_db': data.get('auth_database', 'admin'), 'username': data.get('username'),
                    'pass_env_var': data.get('pass_env_var'), 'replica_set': data.get('replica_set'),
                    'slow_ms': data.get('slow_query_ms', 100),
                    'read_pref': data.get('read_preference', 'primaryPreferred'),
                    'conn_timeout': data.get('connection_timeout', 5000),
                    'created_by': data.get('created_by', 'admin')
                })
                conn.commit()
                return {'success': True, 'message': f"MongoDB config '{data['display_name']}' saved"}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False, 'error': 'Collection already configured for this track'}
                logger.error(f"Error saving MongoDB config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_mongodb_test_status(self, mongodb_config_id: int, status: str) -> None:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_MONGODB_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE, UPDATED_DATE = SYSDATE
                    WHERE MONGODB_CONFIG_ID = :config_id
                """, {'status': status, 'config_id': mongodb_config_id})
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating MongoDB test status: {e}")
            finally:
                cursor.close()

    def delete_mongodb_config(self, mongodb_config_id: int, deleted_by: str) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_MONGODB_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :deleted_by, UPDATED_DATE = SYSDATE
                    WHERE MONGODB_CONFIG_ID = :config_id
                """, {'deleted_by': deleted_by, 'config_id': mongodb_config_id})
                conn.commit()
                return {'success': True, 'message': 'MongoDB config deactivated'}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================
    # PC CONFIG
    # =========================================================

    def get_pc_configs(self, lob_name: str, track_name: Optional[str] = None) -> List[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                params = {'lob_name': lob_name}
                sql = """
                    SELECT PC_CONFIG_ID, LOB_NAME, TRACK_NAME, PC_URL, PC_PORT,
                           USERNAME, PASS_ENV_VAR, DOMAIN, PROJECT_NAME, DISPLAY_NAME,
                           DURATION_FORMAT, COOKIE_FLAG, REPORT_TIMEOUT_SEC, IS_ACTIVE,
                           LAST_TEST_STATUS, LAST_TEST_DATE, LAST_RUN_ID,
                           CREATED_BY, CREATED_DATE
                    FROM API_NFT_PC_CONFIG
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                """
                if track_name:
                    sql += " AND TRACK_NAME = :track_name"
                    params['track_name'] = track_name
                sql += " ORDER BY TRACK_NAME, DISPLAY_NAME"
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = ['pc_config_id', 'lob_name', 'track_name', 'pc_url', 'pc_port',
                           'username', 'pass_env_var', 'domain', 'project_name', 'display_name',
                           'duration_format', 'cookie_flag', 'report_timeout_sec', 'is_active',
                           'last_test_status', 'last_test_date', 'last_run_id',
                           'created_by', 'created_date']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['is_active'] = d['is_active'] == 'Y'
                    d['last_test_date'] = d['last_test_date'].isoformat() if d['last_test_date'] else None
                    d['created_date'] = d['created_date'].isoformat() if d['created_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error getting PC configs: {e}")
                return []
            finally:
                cursor.close()

    def save_pc_config(self, data: Dict) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO API_NFT_PC_CONFIG
                        (LOB_NAME, TRACK_NAME, PC_URL, PC_PORT, USERNAME, PASS_ENV_VAR,
                         DOMAIN, PROJECT_NAME, DISPLAY_NAME, DURATION_FORMAT, COOKIE_FLAG,
                         REPORT_TIMEOUT_SEC, IS_ACTIVE, LAST_TEST_STATUS,
                         CREATED_BY, CREATED_DATE, UPDATED_DATE)
                    VALUES (:lob_name, :track_name, :pc_url, :pc_port, :username, :pass_env_var,
                            :domain, :project_name, :display_name, :duration_format, :cookie_flag,
                            :report_timeout, 'Y', 'NOT_TESTED',
                            :created_by, SYSDATE, SYSDATE)
                """, {
                    'lob_name': data['lob_name'], 'track_name': data['track_name'],
                    'pc_url': data['pc_url'], 'pc_port': data.get('pc_port', 443),
                    'username': data['username'], 'pass_env_var': data['pass_env_var'],
                    'domain': data.get('domain', 'DEFAULT'), 'project_name': data['project_name'],
                    'display_name': data['display_name'],
                    'duration_format': data.get('duration_format', 'HM'),
                    'cookie_flag': data.get('cookie_flag', '-b'),
                    'report_timeout': data.get('report_timeout_sec', 300),
                    'created_by': data.get('created_by', 'admin')
                })
                conn.commit()
                return {'success': True, 'message': f"PC config '{data['display_name']}' saved"}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False, 'error': f"Project '{data['project_name']}' already configured for this track"}
                logger.error(f"Error saving PC config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def update_pc_test_status(self, pc_config_id: int, status: str, last_run_id: Optional[str] = None) -> None:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_PC_CONFIG
                    SET LAST_TEST_STATUS = :status, LAST_TEST_DATE = SYSDATE,
                        LAST_RUN_ID = NVL(:run_id, LAST_RUN_ID), UPDATED_DATE = SYSDATE
                    WHERE PC_CONFIG_ID = :config_id
                """, {'status': status, 'run_id': last_run_id, 'config_id': pc_config_id})
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating PC test status: {e}")
            finally:
                cursor.close()

    def delete_pc_config(self, pc_config_id: int, deleted_by: str) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_PC_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :deleted_by, UPDATED_DATE = SYSDATE
                    WHERE PC_CONFIG_ID = :config_id
                """, {'deleted_by': deleted_by, 'config_id': pc_config_id})
                conn.commit()
                return {'success': True, 'message': 'PC config deactivated'}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================
    # DB CONFIG
    # =========================================================

    def get_db_configs(self, lob_name: str) -> List[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT DB_CONFIG_ID, LOB_NAME, DISPLAY_NAME, DB_TYPE,
                           HOST, PORT, SERVICE_NAME, USERNAME, PASS_ENV_VAR,
                           USE_CYBERARK, CYBERARK_SAFE, CYBERARK_OBJECT,
                           ALLOWED_OPERATIONS, IS_ACTIVE, CREATED_BY, CREATED_DATE
                    FROM API_NFT_DB_CONFIG
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                    ORDER BY DISPLAY_NAME
                """, {'lob_name': lob_name})
                rows = cursor.fetchall()
                columns = ['db_config_id', 'lob_name', 'display_name', 'db_type',
                           'host', 'port', 'service_name', 'username', 'pass_env_var',
                           'use_cyberark', 'cyberark_safe', 'cyberark_object',
                           'allowed_operations', 'is_active', 'created_by', 'created_date']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['is_active'] = d['is_active'] == 'Y'
                    d['use_cyberark'] = d['use_cyberark'] == 'Y'
                    d['dsn'] = f"{d['host']}:{d['port']}/{d['service_name']}"
                    d['created_date'] = d['created_date'].isoformat() if d['created_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error getting DB configs: {e}")
                return []
            finally:
                cursor.close()

    def save_db_config(self, data: Dict) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO API_NFT_DB_CONFIG
                        (LOB_NAME, DISPLAY_NAME, DB_TYPE, HOST, PORT, SERVICE_NAME,
                         USERNAME, PASS_ENV_VAR, USE_CYBERARK, CYBERARK_SAFE, CYBERARK_OBJECT,
                         ALLOWED_OPERATIONS, IS_ACTIVE, CREATED_BY, CREATED_DATE, UPDATED_DATE)
                    VALUES (:lob_name, :display_name, :db_type, :host, :port, :service_name,
                            :username, :pass_env_var, :use_cyberark, :cyberark_safe, :cyberark_object,
                            :allowed_ops, 'Y', :created_by, SYSDATE, SYSDATE)
                """, {
                    'lob_name': data['lob_name'], 'display_name': data['display_name'],
                    'db_type': data.get('db_type', 'Oracle'),
                    'host': data['host'], 'port': data.get('port', 1521),
                    'service_name': data['service_name'], 'username': data['username'],
                    'pass_env_var': data['pass_env_var'],
                    'use_cyberark': 'Y' if data.get('use_cyberark') else 'N',
                    'cyberark_safe': data.get('cyberark_safe'),
                    'cyberark_object': data.get('cyberark_object'),
                    'allowed_ops': data.get('allowed_operations', 'DQL'),
                    'created_by': data.get('created_by', 'admin')
                })
                conn.commit()
                return {'success': True, 'message': f"DB config '{data['display_name']}' saved"}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False, 'error': f"Database '{data['display_name']}' already configured for this LOB"}
                logger.error(f"Error saving DB config: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def delete_db_config(self, db_config_id: int, deleted_by: str) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_DB_CONFIG
                    SET IS_ACTIVE = 'N', UPDATED_BY = :deleted_by, UPDATED_DATE = SYSDATE
                    WHERE DB_CONFIG_ID = :config_id
                """, {'deleted_by': deleted_by, 'config_id': db_config_id})
                conn.commit()
                return {'success': True, 'message': 'DB config deactivated'}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================
    # TRACK TEMPLATE
    # =========================================================

    def get_track_template(self, lob_name: str, track_name: str) -> Optional[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT TEMPLATE_ID, LOB_NAME, TRACK_NAME,
                           APPD_APP_IDS, KIBANA_CONFIG_IDS, SPLUNK_CONFIG_IDS,
                           MONGODB_CONFIG_IDS, PC_CONFIG_IDS, DB_CONFIG_IDS,
                           APPD_APP_COUNT, KIBANA_COUNT, SPLUNK_COUNT,
                           MONGODB_COUNT, PC_COUNT, DB_COUNT,
                           IS_ACTIVE, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
                    FROM API_NFT_TRACK_TEMPLATE
                    WHERE LOB_NAME = :lob_name AND TRACK_NAME = :track_name AND IS_ACTIVE = 'Y'
                """, {'lob_name': lob_name, 'track_name': track_name})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'template_id': row[0], 'lob_name': row[1], 'track_name': row[2],
                    'appd_app_ids': row[3], 'kibana_config_ids': row[4],
                    'splunk_config_ids': row[5], 'mongodb_config_ids': row[6],
                    'pc_config_ids': row[7], 'db_config_ids': row[8],
                    'appd_app_count': row[9], 'kibana_count': row[10],
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

    def list_track_templates(self, lob_name: str) -> List[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT TEMPLATE_ID, LOB_NAME, TRACK_NAME,
                           APPD_APP_COUNT, KIBANA_COUNT, SPLUNK_COUNT,
                           MONGODB_COUNT, PC_COUNT, DB_COUNT,
                           CREATED_BY, CREATED_DATE, UPDATED_DATE
                    FROM API_NFT_TRACK_TEMPLATE
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                    ORDER BY TRACK_NAME
                """, {'lob_name': lob_name})
                rows = cursor.fetchall()
                columns = ['template_id', 'lob_name', 'track_name',
                           'appd_app_count', 'kibana_count', 'splunk_count',
                           'mongodb_count', 'pc_count', 'db_count',
                           'created_by', 'created_date', 'updated_date']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['created_date'] = d['created_date'].isoformat() if d['created_date'] else None
                    d['updated_date'] = d['updated_date'].isoformat() if d['updated_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error listing track templates: {e}")
                return []
            finally:
                cursor.close()

    def save_track_template(self, data: Dict) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                lob_name   = data['lob_name']
                track_name = data['track_name']
                appd_ids   = data.get('appd_app_ids', '')
                kib_ids    = data.get('kibana_config_ids', '')
                spl_ids    = data.get('splunk_config_ids', '')
                mdb_ids    = data.get('mongodb_config_ids', '')
                pc_ids     = data.get('pc_config_ids', '')
                db_ids     = data.get('db_config_ids', '')

                def count_ids(s): return len([x for x in str(s or '').split(',') if x.strip()])

                # Check if exists
                cursor.execute(
                    "SELECT TEMPLATE_ID FROM API_NFT_TRACK_TEMPLATE WHERE LOB_NAME = :l AND TRACK_NAME = :t",
                    {'l': lob_name, 't': track_name}
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE API_NFT_TRACK_TEMPLATE
                        SET APPD_APP_IDS = :appd, KIBANA_CONFIG_IDS = :kib,
                            SPLUNK_CONFIG_IDS = :spl, MONGODB_CONFIG_IDS = :mdb,
                            PC_CONFIG_IDS = :pc, DB_CONFIG_IDS = :db,
                            APPD_APP_COUNT = :ac, KIBANA_COUNT = :kc, SPLUNK_COUNT = :sc,
                            MONGODB_COUNT = :mc, PC_COUNT = :pc_c, DB_COUNT = :dc,
                            UPDATED_BY = :by, UPDATED_DATE = SYSDATE, IS_ACTIVE = 'Y'
                        WHERE LOB_NAME = :l AND TRACK_NAME = :t
                    """, {'appd': appd_ids, 'kib': kib_ids, 'spl': spl_ids,
                          'mdb': mdb_ids, 'pc': pc_ids, 'db': db_ids,
                          'ac': count_ids(appd_ids), 'kc': count_ids(kib_ids),
                          'sc': count_ids(spl_ids), 'mc': count_ids(mdb_ids),
                          'pc_c': count_ids(pc_ids), 'dc': count_ids(db_ids),
                          'by': data.get('created_by', 'admin'),
                          'l': lob_name, 't': track_name})
                else:
                    cursor.execute("""
                        INSERT INTO API_NFT_TRACK_TEMPLATE
                            (LOB_NAME, TRACK_NAME, APPD_APP_IDS, KIBANA_CONFIG_IDS,
                             SPLUNK_CONFIG_IDS, MONGODB_CONFIG_IDS, PC_CONFIG_IDS, DB_CONFIG_IDS,
                             APPD_APP_COUNT, KIBANA_COUNT, SPLUNK_COUNT, MONGODB_COUNT,
                             PC_COUNT, DB_COUNT, IS_ACTIVE, CREATED_BY, CREATED_DATE, UPDATED_DATE)
                        VALUES (:l, :t, :appd, :kib, :spl, :mdb, :pc, :db,
                                :ac, :kc, :sc, :mc, :pc_c, :dc,
                                'Y', :by, SYSDATE, SYSDATE)
                    """, {'l': lob_name, 't': track_name,
                          'appd': appd_ids, 'kib': kib_ids, 'spl': spl_ids,
                          'mdb': mdb_ids, 'pc': pc_ids, 'db': db_ids,
                          'ac': count_ids(appd_ids), 'kc': count_ids(kib_ids),
                          'sc': count_ids(spl_ids), 'mc': count_ids(mdb_ids),
                          'pc_c': count_ids(pc_ids), 'dc': count_ids(db_ids),
                          'by': data.get('created_by', 'admin')})
                conn.commit()
                logger.info(f"Track template saved: {lob_name}/{track_name}")
                return {'success': True, 'message': f"Template for {lob_name}/{track_name} saved"}
            except Exception as e:
                conn.rollback()
                logger.error(f"Error saving track template: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def delete_track_template(self, lob_name: str, track_name: str, deleted_by: str) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE API_NFT_TRACK_TEMPLATE
                    SET IS_ACTIVE = 'N', UPDATED_BY = :by, UPDATED_DATE = SYSDATE
                    WHERE LOB_NAME = :l AND TRACK_NAME = :t
                """, {'by': deleted_by, 'l': lob_name, 't': track_name})
                conn.commit()
                return {'success': True, 'message': f"Template for {lob_name}/{track_name} deleted"}
            except Exception as e:
                conn.rollback()
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    # =========================================================
    # TEST REGISTRATION
    # =========================================================

    def register_test(self, data: Dict) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO API_NFT_TEST_REGISTRATION
                        (RUN_ID, PC_RUN_ID, LOB_NAME, TRACK_NAME, TEST_NAME, TEST_TYPE,
                         ENVIRONMENT, RELEASE_NAME, PEAK_VUSERS, RAMP_UP_MINUTES,
                         PLANNED_DURATION_HRS, JENKINS_BUILD, TEMPLATE_ID,
                         REGISTERED_BY, REGISTRATION_DATE, NOTES)
                    VALUES (:run_id, :pc_run_id, :lob_name, :track_name, :test_name, :test_type,
                            :environment, :release_name, :peak_vusers, :ramp_up,
                            :planned_hrs, :jenkins_build, :template_id,
                            :registered_by, SYSDATE, :notes)
                """, {
                    'run_id': data['run_id'], 'pc_run_id': data['pc_run_id'],
                    'lob_name': data['lob_name'], 'track_name': data['track_name'],
                    'test_name': data['test_name'], 'test_type': data.get('test_type'),
                    'environment': data.get('environment', 'PERF'),
                    'release_name': data.get('release_name'),
                    'peak_vusers': data.get('peak_vusers'),
                    'ramp_up': data.get('ramp_up_minutes'),
                    'planned_hrs': data.get('planned_duration_hrs'),
                    'jenkins_build': data.get('jenkins_build'),
                    'template_id': data.get('template_id'),
                    'registered_by': data['registered_by'],
                    'notes': data.get('notes')
                })
                conn.commit()
                logger.info(f"Test registered: {data['run_id']} / PC {data['pc_run_id']}")
                return {'success': True, 'run_id': data['run_id'],
                        'message': f"Test registered successfully. Run ID: {data['run_id']}"}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False,
                            'error': f"PC_RUN_ID '{data['pc_run_id']}' is already registered"}
                logger.error(f"Error registering test: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_recent_registrations(self, lob_name: Optional[str] = None,
                                 limit: int = 20) -> List[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                params: Dict[str, Any] = {'limit': limit}
                sql = """
                    SELECT REG_ID, RUN_ID, PC_RUN_ID, LOB_NAME, TRACK_NAME, TEST_NAME,
                           TEST_TYPE, ENVIRONMENT, RELEASE_NAME, PEAK_VUSERS,
                           JENKINS_BUILD, REGISTERED_BY, REGISTRATION_DATE, NOTES
                    FROM API_NFT_TEST_REGISTRATION
                """
                if lob_name:
                    sql += " WHERE LOB_NAME = :lob_name"
                    params['lob_name'] = lob_name
                sql += " ORDER BY REGISTRATION_DATE DESC FETCH FIRST :limit ROWS ONLY"
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = ['reg_id', 'run_id', 'pc_run_id', 'lob_name', 'track_name',
                           'test_name', 'test_type', 'environment', 'release_name',
                           'peak_vusers', 'jenkins_build', 'registered_by',
                           'registration_date', 'notes']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['registration_date'] = d['registration_date'].isoformat() if d['registration_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error getting recent registrations: {e}")
                return []
            finally:
                cursor.close()

    def get_registration_by_run_id(self, run_id: str) -> Optional[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT REG_ID, RUN_ID, PC_RUN_ID, LOB_NAME, TRACK_NAME, TEST_NAME,
                           TEST_TYPE, ENVIRONMENT, RELEASE_NAME, PEAK_VUSERS,
                           RAMP_UP_MINUTES, PLANNED_DURATION_HRS, JENKINS_BUILD,
                           TEMPLATE_ID, REGISTERED_BY, REGISTRATION_DATE, NOTES
                    FROM API_NFT_TEST_REGISTRATION
                    WHERE RUN_ID = :run_id
                """, {'run_id': run_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'reg_id': row[0], 'run_id': row[1], 'pc_run_id': row[2],
                    'lob_name': row[3], 'track_name': row[4], 'test_name': row[5],
                    'test_type': row[6], 'environment': row[7], 'release_name': row[8],
                    'peak_vusers': row[9], 'ramp_up_minutes': row[10],
                    'planned_duration_hrs': row[11], 'jenkins_build': row[12],
                    'template_id': row[13], 'registered_by': row[14],
                    'registration_date': row[15].isoformat() if row[15] else None,
                    'notes': row[16]
                }
            except Exception as e:
                logger.error(f"Error getting registration by run_id: {e}")
                return None
            finally:
                cursor.close()

    # =========================================================
    # RELEASE REPORTS
    # =========================================================

    def save_release_report(self, data: Dict) -> Dict:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                html_size_kb = len(data.get('report_html', '').encode('utf-8')) // 1024
                cursor.execute("""
                    INSERT INTO API_NFT_RELEASE_REPORTS
                        (RUN_ID, PC_RUN_ID, LOB_NAME, RELEASE_NAME, TEST_TYPE,
                         TEST_NAME, TRACK_NAME, REPORT_HTML, REPORT_SIZE_KB,
                         OVERALL_STATUS, PASS_RATE_PCT, PEAK_VUSERS,
                         AVG_RESPONSE_MS, P95_RESPONSE_MS,
                         TOTAL_TRANSACTIONS, FAILED_TRANSACTIONS,
                         IS_ACTIVE, SAVED_BY, SAVED_DATE, NOTES)
                    VALUES (:run_id, :pc_run_id, :lob_name, :release_name, :test_type,
                            :test_name, :track_name, :report_html, :report_size_kb,
                            :overall_status, :pass_rate_pct, :peak_vusers,
                            :avg_response_ms, :p95_response_ms,
                            :total_transactions, :failed_transactions,
                            'Y', :saved_by, SYSDATE, :notes)
                """, {
                    'run_id': data['run_id'], 'pc_run_id': data['pc_run_id'],
                    'lob_name': data['lob_name'], 'release_name': data['release_name'],
                    'test_type': data['test_type'], 'test_name': data.get('test_name'),
                    'track_name': data.get('track_name'),
                    'report_html': data['report_html'],
                    'report_size_kb': html_size_kb,
                    'overall_status': data.get('overall_status'),
                    'pass_rate_pct': data.get('pass_rate_pct'),
                    'peak_vusers': data.get('peak_vusers'),
                    'avg_response_ms': data.get('avg_response_ms'),
                    'p95_response_ms': data.get('p95_response_ms'),
                    'total_transactions': data.get('total_transactions'),
                    'failed_transactions': data.get('failed_transactions'),
                    'saved_by': data['saved_by'],
                    'notes': data.get('notes')
                })
                conn.commit()
                logger.info(f"Release report saved: {data['run_id']} / {data['release_name']} / {data['test_type']}")
                return {'success': True,
                        'message': f"Report saved to release table. Size: {html_size_kb} KB",
                        'report_size_kb': html_size_kb}
            except Exception as e:
                conn.rollback()
                if 'unique constraint' in str(e).lower():
                    return {'success': False,
                            'error': f"Report for run '{data['run_id']}' with type '{data['test_type']}' already saved"}
                logger.error(f"Error saving release report: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                cursor.close()

    def get_release_reports(self, lob_name: str, release_name: Optional[str] = None,
                            limit: int = 50) -> List[Dict]:
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                params: Dict[str, Any] = {'lob_name': lob_name, 'limit': limit}
                sql = """
                    SELECT REPORT_ID, RUN_ID, PC_RUN_ID, LOB_NAME, RELEASE_NAME,
                           TEST_TYPE, TEST_NAME, TRACK_NAME, REPORT_SIZE_KB,
                           OVERALL_STATUS, PASS_RATE_PCT, PEAK_VUSERS,
                           AVG_RESPONSE_MS, P95_RESPONSE_MS,
                           TOTAL_TRANSACTIONS, FAILED_TRANSACTIONS,
                           SAVED_BY, SAVED_DATE, NOTES
                    FROM API_NFT_RELEASE_REPORTS
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                """
                if release_name:
                    sql += " AND RELEASE_NAME = :release_name"
                    params['release_name'] = release_name
                sql += " ORDER BY SAVED_DATE DESC FETCH FIRST :limit ROWS ONLY"
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                columns = ['report_id', 'run_id', 'pc_run_id', 'lob_name', 'release_name',
                           'test_type', 'test_name', 'track_name', 'report_size_kb',
                           'overall_status', 'pass_rate_pct', 'peak_vusers',
                           'avg_response_ms', 'p95_response_ms',
                           'total_transactions', 'failed_transactions',
                           'saved_by', 'saved_date', 'notes']
                result = []
                for row in rows:
                    d = dict(zip(columns, row))
                    d['saved_date'] = d['saved_date'].isoformat() if d['saved_date'] else None
                    result.append(d)
                return result
            except Exception as e:
                logger.error(f"Error getting release reports: {e}")
                return []
            finally:
                cursor.close()

    def get_release_report_html(self, report_id: int) -> Optional[str]:
        """Fetch the full HTML CLOB for a specific report."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT REPORT_HTML FROM API_NFT_RELEASE_REPORTS
                    WHERE REPORT_ID = :report_id AND IS_ACTIVE = 'Y'
                """, {'report_id': report_id})
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0].read() if hasattr(row[0], 'read') else str(row[0])
                return None
            except Exception as e:
                logger.error(f"Error fetching report HTML: {e}")
                return None
            finally:
                cursor.close()

    # =========================================================
    # CONFIG LOOKUP BY PRIMARY KEY (for test-connection routes)
    # =========================================================


    def get_active_lobs(self) -> List[Dict]:
        """
        Get all active LOBs with their tracks from API_LOB_MASTER.
        Used by public pre-login endpoint — no auth required.
        Groups by LOB_NAME and collects all TRACK_NAMEs.
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT LOB_NAME, TRACK_NAME, DATABASE_NAME, IS_ACTIVE
                    FROM API_LOB_MASTER
                    WHERE IS_ACTIVE = 'Y'
                    ORDER BY LOB_NAME, TRACK_NAME
                """)
                rows = cursor.fetchall()
                # Group by LOB_NAME
                lob_map = {}
                for row in rows:
                    lob_name = row[0]
                    track = row[1]
                    db_name = row[2]
                    if lob_name not in lob_map:
                        lob_map[lob_name] = {
                            'lob_name': lob_name,
                            'tracks': [],
                            'databases': [],
                            'is_active': row[3],
                        }
                    if track and track not in lob_map[lob_name]['tracks']:
                        lob_map[lob_name]['tracks'].append(track)
                    if db_name and db_name not in lob_map[lob_name]['databases']:
                        lob_map[lob_name]['databases'].append(db_name)
                return list(lob_map.values())
            except Exception as e:
                logger.error(f"Error fetching active LOBs: {e}")
                return []
            finally:
                cursor.close()

    def get_kibana_config_by_id(self, kibana_config_id: int) -> Optional[Dict]:
        """Get a single Kibana config by primary key."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT KIBANA_CONFIG_ID, LOB_NAME, TRACK_NAME, KIBANA_URL,
                           USERNAME, TOKEN_ENV_VAR, AUTH_TYPE,
                           DASHBOARD_ID, DISPLAY_NAME, TIME_FIELD,
                           LAST_TEST_STATUS, CREATED_DATE
                    FROM API_NFT_KIBANA_CONFIG
                    WHERE KIBANA_CONFIG_ID = :config_id
                """, {'config_id': kibana_config_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'kibana_config_id': row[0], 'lob_name': row[1],
                    'track_name': row[2], 'kibana_url': row[3],
                    'username': row[4], 'token_env_var': row[5],
                    'auth_type': row[6] or 'apikey', 'dashboard_id': row[7],
                    'display_name': row[8], 'time_field': row[9] or '@timestamp',
                    'last_test_status': row[10],
                    'created_date': row[11].isoformat() if row[11] else None,
                }
            finally:
                cursor.close()

    def get_pc_config_by_id(self, pc_config_id: int) -> Optional[Dict]:
        """Get a single PC config by primary key."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT PC_CONFIG_ID, LOB_NAME, TRACK_NAME, PC_URL, PC_PORT,
                           USERNAME, PASS_ENV_VAR, DOMAIN, PROJECT_NAME,
                           DISPLAY_NAME, DURATION_FORMAT, COOKIE_FLAG,
                           REPORT_TIMEOUT_SEC, LAST_RUN_ID, LAST_TEST_STATUS
                    FROM API_NFT_PC_CONFIG
                    WHERE PC_CONFIG_ID = :config_id
                """, {'config_id': pc_config_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'pc_config_id': row[0], 'lob_name': row[1],
                    'track_name': row[2], 'pc_url': row[3],
                    'pc_port': row[4] or 443, 'username': row[5],
                    'pass_env_var': row[6], 'domain': row[7] or 'DEFAULT',
                    'project_name': row[8], 'display_name': row[9],
                    'duration_format': row[10] or 'HM',
                    'cookie_flag': row[11] or '-b',
                    'report_timeout_sec': row[12] or 300,
                    'last_run_id': row[13], 'last_test_status': row[14],
                }
            finally:
                cursor.close()

    def get_db_config_by_id(self, db_config_id: int) -> Optional[Dict]:
        """Get a single Oracle DB config by primary key."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT DB_CONFIG_ID, LOB_NAME, DISPLAY_NAME,
                           HOST, PORT, SERVICE_NAME, USERNAME, PASS_ENV_VAR,
                           USE_CYBERARK, ALLOWED_OPERATIONS
                    FROM API_NFT_DB_CONFIG
                    WHERE DB_CONFIG_ID = :config_id
                """, {'config_id': db_config_id})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'db_config_id': row[0], 'lob_name': row[1],
                    'display_name': row[2], 'host': row[3],
                    'port': row[4] or 1521, 'service_name': row[5],
                    'username': row[6], 'pass_env_var': row[7],
                    'use_cyberark': row[8] == 'Y',
                    'allowed_operations': row[9],
                }
            finally:
                cursor.close()

    def get_appd_config_by_lob(self, lob_name: str) -> Optional[Dict]:
        """Get AppD config for a LOB."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT APPD_CONFIG_ID, LOB_NAME, CONTROLLER_URL, ACCOUNT_NAME,
                           TOKEN_ENV_VAR, DEFAULT_NODE_COUNT, LAST_TEST_STATUS
                    FROM API_NFT_APPD_CONFIG
                    WHERE LOB_NAME = :lob_name AND IS_ACTIVE = 'Y'
                    ORDER BY CREATED_DATE DESC
                    FETCH FIRST 1 ROW ONLY
                """, {'lob_name': lob_name})
                row = cursor.fetchone()
                if not row:
                    return None
                return {
                    'appd_config_id': row[0], 'lob_name': row[1],
                    'controller_url': row[2], 'account_name': row[3],
                    'token_env_var': row[4],
                    'default_node_count': row[5] or 3,
                    'last_test_status': row[6],
                }
            finally:
                cursor.close()

    def update_config_test_status(self, table: str, pk_col: str,
                                   pk_val: int, status: str) -> None:
        """Update LAST_TEST_STATUS on any NFT config table."""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    f"UPDATE {table} SET LAST_TEST_STATUS = :status, "
                    f"UPDATED_DATE = SYSDATE WHERE {pk_col} = :pk_val",
                    {'status': status, 'pk_val': pk_val}
                )
                conn.commit()
            finally:
                cursor.close()

