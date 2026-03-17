
-- Run this ONCE to backfill all existing users with no LOB access
-- Safe to re-run (uses MERGE so no duplicates)

DECLARE
    v_count NUMBER := 0;
BEGIN
    FOR u IN (
        -- Users who have NO active LOB access at all
        SELECT DISTINCT a.USERNAME
        FROM API_AUTH_USERS a
        WHERE a.IS_ACTIVE = 'Y'
          AND NOT EXISTS (
              SELECT 1 FROM API_NFT_USER_LOB_ACCESS l
              WHERE l.USERNAME = a.USERNAME AND l.IS_ACTIVE = 'Y'
          )
    ) LOOP
        FOR l IN (
            SELECT DISTINCT LOB_NAME FROM API_LOB_MASTER WHERE IS_ACTIVE = 'Y'
        ) LOOP
            MERGE INTO API_NFT_USER_LOB_ACCESS t
            USING (SELECT u.USERNAME AS un, l.LOB_NAME AS ln FROM DUAL) s
            ON (t.USERNAME = s.un AND t.LOB_NAME = s.ln)
            WHEN MATCHED THEN
                UPDATE SET IS_ACTIVE = 'Y', UPDATED_DATE = SYSDATE
            WHEN NOT MATCHED THEN
                INSERT (USERNAME, LOB_NAME, GRANTED_BY,
                        IS_ACTIVE, CREATED_DATE, UPDATED_DATE)
                VALUES (u.USERNAME, l.LOB_NAME, 'SYSTEM_BACKFILL',
                        'Y', SYSDATE, SYSDATE);
            v_count := v_count + 1;
        END LOOP;
    END LOOP;
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Backfill complete. ' || v_count || ' LOB grants inserted.');
END;
/

-- Verify
SELECT u.USERNAME, u.ROLE,
       LISTAGG(l.LOB_NAME, ', ') WITHIN GROUP (ORDER BY l.LOB_NAME) AS LOB_ACCESS,
       COUNT(l.LOB_NAME) AS LOB_COUNT
FROM API_AUTH_USERS u
LEFT JOIN API_NFT_USER_LOB_ACCESS l
    ON u.USERNAME = l.USERNAME AND l.IS_ACTIVE = 'Y'
WHERE u.IS_ACTIVE = 'Y'
GROUP BY u.USERNAME, u.ROLE
ORDER BY u.USERNAME;
