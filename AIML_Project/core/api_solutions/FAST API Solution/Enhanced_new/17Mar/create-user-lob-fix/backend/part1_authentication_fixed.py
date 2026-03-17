"""
REPLACE in: Auth/authentication_fixed.py
CLASS: AuthenticationManager

Find the existing create_user() method and replace it entirely with this.
"""
import oracledb

    def create_user(self, username: str, email: str, password: str,
                    full_name: str, role: str = 'performance_engineer',
                    created_by: str = 'admin',
                    lob_names: list = None) -> dict:
        """
        Create a new user and auto-grant LOB access.
        lob_names: list of LOB names, None/'ALL' = grant all active LOBs.
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        hashed = self.pwd_context.hash(password)

        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            try:
                # Step 1: Insert user
                user_id_var = cursor.var(oracledb.NUMBER)
                cursor.execute("""
                    INSERT INTO API_AUTH_USERS (
                        USERNAME, EMAIL, PASSWORD_HASH, FULL_NAME, ROLE,
                        IS_ACTIVE, MFA_ENABLED, FAILED_ATTEMPTS,
                        CREATED_BY, CREATED_DATE
                    ) VALUES (
                        :username, :email, :password_hash, :full_name, :role,
                        'Y', 'N', 0, :created_by, SYSDATE
                    ) RETURNING USER_ID INTO :user_id_out
                """, {
                    'username':      username,
                    'email':         email,
                    'password_hash': hashed,
                    'full_name':     full_name,
                    'role':          role,
                    'created_by':    created_by,
                    'user_id_out':   user_id_var,
                })
                user_id = int(user_id_var.getvalue()[0])

                # Step 2: Determine LOBs to grant
                # None or ['ALL'] = grant ALL active LOBs
                if not lob_names or lob_names == ['ALL']:
                    cursor.execute("""
                        SELECT DISTINCT LOB_NAME FROM API_LOB_MASTER
                        WHERE IS_ACTIVE = 'Y' ORDER BY LOB_NAME
                    """)
                    lobs_to_grant = [row[0] for row in cursor.fetchall()]
                else:
                    lobs_to_grant = [l for l in lob_names if l and l != 'ALL']

                # Step 3: Grant LOB access (MERGE = safe to re-run)
                for lob_name in lobs_to_grant:
                    try:
                        cursor.execute("""
                            MERGE INTO API_NFT_USER_LOB_ACCESS t
                            USING (SELECT :username AS un,
                                          :lob_name AS ln FROM DUAL) s
                            ON (t.USERNAME = s.un AND t.LOB_NAME = s.ln)
                            WHEN MATCHED THEN
                                UPDATE SET IS_ACTIVE    = 'Y',
                                           GRANTED_BY   = :granted_by,
                                           UPDATED_DATE = SYSDATE
                            WHEN NOT MATCHED THEN
                                INSERT (USERNAME, LOB_NAME, GRANTED_BY,
                                        IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
                                VALUES (:username, :lob_name, :granted_by,
                                        'Y', SYSDATE, SYSDATE)
                        """, {
                            'username':   username,
                            'lob_name':   lob_name,
                            'granted_by': created_by,
                        })
                    except Exception as lob_err:
                        logger.warning(f"LOB grant skipped {username}/{lob_name}: {lob_err}")

                conn.commit()

                # Step 4: Audit
                logger.info(f"User created: {username} role={role} lobs={lobs_to_grant}")
                try:
                    self._log_audit(username=created_by, action='CREATE_USER',
                                    resource_id=str(user_id), success='Y')
                except Exception:
                    pass

                return {
                    'success':      True,
                    'user_id':      user_id,
                    'username':     username,
                    'role':         role,
                    'lobs_granted': lobs_to_grant,
                    'lob_count':    len(lobs_to_grant),
                    'message':      f"User created with access to {len(lobs_to_grant)} LOB(s)"
                }

            except Exception as e:
                conn.rollback()
                logger.error(f"Create user error: {e}", exc_info=True)
                if 'ORA-00001' in str(e) or 'unique constraint' in str(e).lower():
                    raise ValueError(f"Username '{username}' already exists")
                raise
            finally:
                cursor.close()
