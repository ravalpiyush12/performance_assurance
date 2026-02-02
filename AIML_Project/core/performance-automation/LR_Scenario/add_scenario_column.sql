-- Add SCENARIO_NAME column to existing PC_TEST_RUNS table

-- Check if column already exists
DECLARE
    v_column_exists NUMBER;
BEGIN
    SELECT COUNT(*)
    INTO v_column_exists
    FROM user_tab_columns
    WHERE table_name = 'PC_TEST_RUNS'
    AND column_name = 'SCENARIO_NAME';
    
    IF v_column_exists = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE PC_TEST_RUNS ADD SCENARIO_NAME VARCHAR2(255)';
        DBMS_OUTPUT.PUT_LINE('✓ Added SCENARIO_NAME column to PC_TEST_RUNS');
    ELSE
        DBMS_OUTPUT.PUT_LINE('✓ SCENARIO_NAME column already exists');
    END IF;
END;
/

-- Verify the column was added
SELECT column_name, data_type, data_length, nullable
FROM user_tab_columns
WHERE table_name = 'PC_TEST_RUNS'
ORDER BY column_id;

-- Update existing records with default scenario name (optional)
UPDATE PC_TEST_RUNS
SET SCENARIO_NAME = 'Test_' || TEST_ID
WHERE SCENARIO_NAME IS NULL;

COMMIT;

-- Show sample data
SELECT RUN_ID, TEST_ID, SCENARIO_NAME, BUILD_NUMBER, RUN_DATE, TEST_STATUS
FROM PC_TEST_RUNS
ORDER BY RUN_DATE DESC
FETCH FIRST 10 ROWS ONLY;
