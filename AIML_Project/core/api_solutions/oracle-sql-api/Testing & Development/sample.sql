-- Sample SQL File for Testing Oracle SQL API
-- This file contains various SQL operations for testing

-- Query 1: Get current date and user
SELECT 
    SYSDATE as current_date,
    USER as current_user,
    SYS_CONTEXT('USERENV', 'HOST') as host_name,
    SYS_CONTEXT('USERENV', 'IP_ADDRESS') as ip_address
FROM DUAL;

-- Query 2: Get database version
SELECT * FROM v$version WHERE ROWNUM = 1;

-- Query 3: Sample aggregation
SELECT 
    COUNT(*) as total_objects,
    object_type,
    owner
FROM all_objects
WHERE owner = USER
GROUP BY object_type, owner
ORDER BY total_objects DESC;