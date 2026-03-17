-- =============================================================
-- BACKFILL v2 — correct column names from DESCRIBE output
-- ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY, GRANTED_DATE,
-- IS_ACTIVE, REVOKED_BY, REVOKED_DATE, UPDATED_DATE
-- =============================================================

-- Step 1: Check if sequence exists, create if not
DECLARE
    v_seq_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_seq_count
    FROM USER_SEQUENCES
    WHERE SEQUENCE_NAME = 'API_NFT_ULA_SEQ';

    IF v_seq_count = 0 THEN
        EXECUTE IMMEDIATE
            'CREATE SEQUENCE API_NFT_ULA_SEQ START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Sequence API_NFT_ULA_SEQ created.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence API_NFT_ULA_SEQ already exists.');
    END IF;
END;
/

-- Step 2: Backfill all users with no LOB access
DECLARE
    v_count NUMBER := 0;
    v_id    NUMBER;
BEGIN
    FOR u IN (
        SELECT DISTINCT a.USERNAME
        FROM API_AUTH_USERS a
        WHERE a.IS_ACTIVE = 'Y'
          AND NOT EXISTS (
              SELECT 1 FROM API_NFT_USER_LOB_ACCESS l
              WHERE l.USERNAME = a.USERNAME AND l.IS_ACTIVE = 'Y'
          )
        ORDER BY a.USERNAME
    ) LOOP
        FOR l IN (
            SELECT DISTINCT LOB_NAME
            FROM API_LOB_MASTER
            WHERE IS_ACTIVE = 'Y'
            ORDER BY LOB_NAME
        ) LOOP
            -- Check if row already exists (inactive)
            SELECT COUNT(*) INTO v_id
            FROM API_NFT_USER_LOB_ACCESS
            WHERE USERNAME = u.USERNAME AND LOB_NAME = l.LOB_NAME;

            IF v_id > 0 THEN
                -- Reactivate existing row
                UPDATE API_NFT_USER_LOB_ACCESS
                SET IS_ACTIVE    = 'Y',
                    GRANTED_BY   = 'SYSTEM_BACKFILL',
                    GRANTED_DATE = SYSDATE,
                    REVOKED_BY   = NULL,
                    REVOKED_DATE = NULL,
                    UPDATED_DATE = SYSDATE
                WHERE USERNAME = u.USERNAME AND LOB_NAME = l.LOB_NAME;
            ELSE
                -- Insert new row with sequence
                INSERT INTO API_NFT_USER_LOB_ACCESS (
                    ACCESS_ID, USERNAME, LOB_NAME, GRANTED_BY,
                    GRANTED_DATE, IS_ACTIVE, UPDATED_DATE
                ) VALUES (
                    API_NFT_ULA_SEQ.NEXTVAL,
                    u.USERNAME,
                    l.LOB_NAME,
                    'SYSTEM_BACKFILL',
                    SYSDATE,
                    'Y',
                    SYSDATE
                );
            END IF;
            v_count := v_count + 1;
        END LOOP;
    END LOOP;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Done. ' || v_count || ' LOB grants processed.');
END;
/

-- Step 3: Verify
SELECT
    u.USERNAME,
    u.ROLE,
    LISTAGG(l.LOB_NAME, ', ')
        WITHIN GROUP (ORDER BY l.LOB_NAME) AS LOB_ACCESS,
    COUNT(l.LOB_NAME) AS LOB_COUNT
FROM API_AUTH_USERS u
LEFT JOIN API_NFT_USER_LOB_ACCESS l
    ON u.USERNAME = l.USERNAME AND l.IS_ACTIVE = 'Y'
WHERE u.IS_ACTIVE = 'Y'
GROUP BY u.USERNAME, u.ROLE
ORDER BY u.USERNAME;
