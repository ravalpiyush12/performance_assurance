"""
Performance Center Database Operations
Includes test registration and all PC-related database interactions
"""
import cx_Oracle
from typing import List, Dict, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class PCDatabase:
    """Handle PC database operations including test registration"""
    
    def __init__(self, connection_pool):
        """
        Initialize PC database handler
        
        Args:
            connection_pool: Oracle connection pool
        """
        self.pool = connection_pool
        logger.info("PC Database handler initialized")
    
    # ==========================================
    # RUN_MASTER Operations (Test Registration)
    # ==========================================
    
    def create_master_run(
        self,
        run_id: str,
        pc_run_id: str,
        lob_name: str,
        track: Optional[str] = None,
        test_name: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> bool:
        """
        Create entry in RUN_MASTER (Test Registration)
        
        Args:
            run_id: Master run ID
            pc_run_id: PC run ID
            lob_name: Line of Business
            track: Track name
            test_name: Test name
            created_by: Who registered
            
        Returns:
            True if created, False if already exists
        """
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO RUN_MASTER (
                    RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                    TEST_STATUS, CREATED_BY
                ) VALUES (
                    :run_id, :pc_run_id, :lob_name, :track, :test_name,
                    'INITIATED', :created_by
                )
            """, {
                'run_id': run_id,
                'pc_run_id': pc_run_id,
                'lob_name': lob_name,
                'track': track,
                'test_name': test_name,
                'created_by': created_by
            })
            
            conn.commit()
            logger.info(f"Created RUN_MASTER entry: {run_id}")
            return True
            
        except cx_Oracle.IntegrityError:
            # Run already exists
            conn.rollback()
            logger.info(f"RUN_MASTER entry already exists: {run_id}")
            return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating RUN_MASTER: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_next_sequence_for_pc_run(self, pc_run_id: str) -> int:
        """Get next sequence number for today's runs with same PC_RUN_ID"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            today = date.today()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM RUN_MASTER 
                WHERE PC_RUN_ID = :pc_run_id 
                  AND TRUNC(CREATED_DATE) = :today
            """, {'pc_run_id': pc_run_id, 'today': today})
            
            count = cursor.fetchone()[0]
            return count + 1
            
        finally:
            cursor.close()
            conn.close()
    
    def update_run_status(
        self,
        run_id: str,
        status: str,
        end_time: Optional[datetime] = None
    ):
        """Update run status"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            if end_time:
                cursor.execute("""
                    UPDATE RUN_MASTER
                    SET TEST_STATUS = :status,
                        TEST_END_TIME = :end_time,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {
                    'status': status,
                    'end_time': end_time,
                    'run_id': run_id
                })
            else:
                cursor.execute("""
                    UPDATE RUN_MASTER
                    SET TEST_STATUS = :status,
                        UPDATED_DATE = SYSDATE
                    WHERE RUN_ID = :run_id
                """, {
                    'status': status,
                    'run_id': run_id
                })
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating run status: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def update_run_start_time(self, run_id: str, start_time: datetime):
        """Update test start time"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE RUN_MASTER
                SET TEST_START_TIME = :start_time,
                    UPDATED_DATE = SYSDATE
                WHERE RUN_ID = :run_id
            """, {
                'start_time': start_time,
                'run_id': run_id
            })
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating start time: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_latest_test_run(self) -> Optional[Dict]:
        """Get the most recently created test run"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                    TEST_STATUS, TEST_START_TIME, CREATED_DATE
                FROM RUN_MASTER
                ORDER BY CREATED_DATE DESC
                FETCH FIRST 1 ROW ONLY
            """)
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'run_id': row[0],
                'pc_run_id': row[1],
                'lob_name': row[2],
                'track': row[3],
                'test_name': row[4],
                'test_status': row[5],
                'test_start_time': row[6].isoformat() if row[6] else None,
                'created_date': row[7].isoformat() if row[7] else None
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_test_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent test run registrations"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                    TEST_STATUS, TEST_START_TIME, CREATED_DATE
                FROM RUN_MASTER
                ORDER BY CREATED_DATE DESC
                FETCH FIRST :limit ROWS ONLY
            """, {'limit': limit})
            
            runs = []
            for row in cursor.fetchall():
                runs.append({
                    'run_id': row[0],
                    'pc_run_id': row[1],
                    'lob_name': row[2],
                    'track': row[3],
                    'test_name': row[4],
                    'test_status': row[5],
                    'test_start_time': row[6].isoformat() if row[6] else None,
                    'created_date': row[7].isoformat() if row[7] else None
                })
            
            return runs
            
        finally:
            cursor.close()
            conn.close()
    
    def get_master_run_by_pc_id(self, pc_run_id: str) -> Optional[Dict]:
        """Get master run by PC Run ID"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    RUN_ID, PC_RUN_ID, LOB_NAME, TRACK, TEST_NAME,
                    TEST_STATUS, TEST_START_TIME, CREATED_DATE
                FROM RUN_MASTER
                WHERE PC_RUN_ID = :pc_run_id
                ORDER BY CREATED_DATE DESC
                FETCH FIRST 1 ROW ONLY
            """, {'pc_run_id': pc_run_id})
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'run_id': row[0],
                'pc_run_id': row[1],
                'lob_name': row[2],
                'track': row[3],
                'test_name': row[4],
                'test_status': row[5],
                'test_start_time': row[6].isoformat() if row[6] else None,
                'created_date': row[7].isoformat() if row[7] else None
            }
            
        finally:
            cursor.close()
            conn.close()
    
    # ==========================================
    # PC Test Operations
    # ==========================================
    
    def save_pc_test_run(
        self,
        run_id: str,
        pc_run_id: str,
        pc_url: str,
        pc_domain: str,
        pc_project: str,
        test_status: str,
        collation_status: str,
        test_set_name: Optional[str] = None,
        test_instance_id: Optional[str] = None
    ) -> int:
        """Save PC test run details"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO PC_TEST_RUNS (
                    PC_TEST_ID, RUN_ID, PC_RUN_ID, PC_URL,
                    PC_DOMAIN, PC_PROJECT, TEST_SET_NAME, TEST_INSTANCE_ID,
                    TEST_STATUS, COLLATION_STATUS, REPORT_FETCHED
                ) VALUES (
                    PC_TEST_SEQ.NEXTVAL, :run_id, :pc_run_id, :pc_url,
                    :domain, :project, :test_set, :test_instance,
                    :test_status, :collation_status, 'N'
                ) RETURNING PC_TEST_ID INTO :test_id
            """, {
                'run_id': run_id,
                'pc_run_id': pc_run_id,
                'pc_url': pc_url,
                'domain': pc_domain,
                'project': pc_project,
                'test_set': test_set_name,
                'test_instance': test_instance_id,
                'test_status': test_status,
                'collation_status': collation_status,
                'test_id': cursor.var(cx_Oracle.NUMBER)
            })
            
            test_id = int(cursor.getvalue()[0])
            conn.commit()
            
            logger.info(f"✓ Saved PC test run: {test_id} for RUN_ID: {run_id}")
            return test_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving PC test run: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()
    
    def update_pc_test_status(
        self,
        pc_test_id: int,
        test_status: str,
        collation_status: str,
        report_fetched: bool = False
    ):
        """Update PC test run status"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE PC_TEST_RUNS
                SET TEST_STATUS = :test_status,
                    COLLATION_STATUS = :collation_status,
                    REPORT_FETCHED = :report_fetched,
                    UPDATED_DATE = SYSDATE
                WHERE PC_TEST_ID = :test_id
            """, {
                'test_status': test_status,
                'collation_status': collation_status,
                'report_fetched': 'Y' if report_fetched else 'N',
                'test_id': pc_test_id
            })
            
            conn.commit()
            logger.info(f"✓ Updated PC test status: {pc_test_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating PC test status: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_lr_transactions(
        self,
        run_id: str,
        pc_run_id: str,
        transactions: List[Dict]
    ):
        """Save LoadRunner transaction results"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            for trans in transactions:
                cursor.execute("""
                    INSERT INTO LR_TRANSACTION_RESULTS (
                        TRANSACTION_ID, RUN_ID, PC_RUN_ID, TRANSACTION_NAME,
                        MINIMUM_TIME, AVERAGE_TIME, MAXIMUM_TIME,
                        STD_DEVIATION, PERCENTILE_90, PERCENTILE_95, PERCENTILE_99,
                        PASS_COUNT, FAIL_COUNT, STOP_COUNT, TOTAL_COUNT,
                        PASS_PERCENTAGE, THROUGHPUT_TPS
                    ) VALUES (
                        LR_TRANSACTION_SEQ.NEXTVAL, :run_id, :pc_run_id, :name,
                        :min, :avg, :max,
                        :std, :p90, :p95, :p99,
                        :pass, :fail, :stop, :total,
                        :pass_pct, :tps
                    )
                """, {
                    'run_id': run_id,
                    'pc_run_id': pc_run_id,
                    'name': trans['transaction_name'],
                    'min': trans['minimum_time'],
                    'avg': trans['average_time'],
                    'max': trans['maximum_time'],
                    'std': trans['std_deviation'],
                    'p90': trans['percentile_90'],
                    'p95': trans.get('percentile_95'),
                    'p99': trans.get('percentile_99'),
                    'pass': trans['pass_count'],
                    'fail': trans['fail_count'],
                    'stop': trans['stop_count'],
                    'total': trans['total_count'],
                    'pass_pct': trans['pass_percentage'],
                    'tps': trans.get('throughput_tps')
                })
            
            conn.commit()
            logger.info(f"✓ Saved {len(transactions)} LR transactions for RUN_ID: {run_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving LR transactions: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
            conn.close()
    
    def get_lr_transactions(self, run_id: str) -> List[Dict]:
        """Get LoadRunner transactions for a run"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    TRANSACTION_NAME, MINIMUM_TIME, AVERAGE_TIME, MAXIMUM_TIME,
                    STD_DEVIATION, PERCENTILE_90, PERCENTILE_95, PERCENTILE_99,
                    PASS_COUNT, FAIL_COUNT, STOP_COUNT, TOTAL_COUNT,
                    PASS_PERCENTAGE, THROUGHPUT_TPS
                FROM LR_TRANSACTION_RESULTS
                WHERE RUN_ID = :run_id
                ORDER BY AVERAGE_TIME DESC
            """, {'run_id': run_id})
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'transaction_name': row[0],
                    'minimum_time': float(row[1]),
                    'average_time': float(row[2]),
                    'maximum_time': float(row[3]),
                    'std_deviation': float(row[4]),
                    'percentile_90': float(row[5]),
                    'percentile_95': float(row[6]) if row[6] else None,
                    'percentile_99': float(row[7]) if row[7] else None,
                    'pass_count': int(row[8]),
                    'fail_count': int(row[9]),
                    'stop_count': int(row[10]),
                    'total_count': int(row[11]),
                    'pass_percentage': float(row[12]),
                    'throughput_tps': float(row[13]) if row[13] else None
                })
            
            logger.info(f"Retrieved {len(transactions)} transactions for RUN_ID: {run_id}")
            return transactions
            
        finally:
            cursor.close()
            conn.close()
    
    def get_pc_test_by_run_id(self, run_id: str) -> Optional[Dict]:
        """Get PC test details by run ID"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    PC_TEST_ID, PC_RUN_ID, PC_URL, PC_DOMAIN, PC_PROJECT,
                    TEST_STATUS, COLLATION_STATUS, REPORT_FETCHED,
                    CREATED_DATE
                FROM PC_TEST_RUNS
                WHERE RUN_ID = :run_id
                ORDER BY CREATED_DATE DESC
                FETCH FIRST 1 ROW ONLY
            """, {'run_id': run_id})
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'pc_test_id': row[0],
                'pc_run_id': row[1],
                'pc_url': row[2],
                'pc_domain': row[3],
                'pc_project': row[4],
                'test_status': row[5],
                'collation_status': row[6],
                'report_fetched': row[7] == 'Y',
                'created_date': row[8].isoformat() if row[8] else None
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def get_pc_test_by_pc_run_id(self, pc_run_id: str) -> Optional[Dict]:
        """Get PC test details by PC run ID"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    PC_TEST_ID, RUN_ID, PC_URL, PC_DOMAIN, PC_PROJECT,
                    TEST_STATUS, COLLATION_STATUS, REPORT_FETCHED,
                    CREATED_DATE
                FROM PC_TEST_RUNS
                WHERE PC_RUN_ID = :pc_run_id
                ORDER BY CREATED_DATE DESC
                FETCH FIRST 1 ROW ONLY
            """, {'pc_run_id': pc_run_id})
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                'pc_test_id': row[0],
                'run_id': row[1],
                'pc_url': row[2],
                'pc_domain': row[3],
                'pc_project': row[4],
                'test_status': row[5],
                'collation_status': row[6],
                'report_fetched': row[7] == 'Y',
                'created_date': row[8].isoformat() if row[8] else None
            }
            
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_pc_tests(self, limit: int = 10) -> List[Dict]:
        """Get recent PC test runs"""
        conn = self.pool.acquire()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    pt.PC_TEST_ID, pt.RUN_ID, pt.PC_RUN_ID,
                    rm.LOB_NAME, rm.TRACK, rm.TEST_NAME,
                    pt.TEST_STATUS, pt.COLLATION_STATUS,
                    pt.CREATED_DATE
                FROM PC_TEST_RUNS pt
                LEFT JOIN RUN_MASTER rm ON pt.RUN_ID = rm.RUN_ID
                ORDER BY pt.CREATED_DATE DESC
                FETCH FIRST :limit ROWS ONLY
            """, {'limit': limit})
            
            tests = []
            for row in cursor.fetchall():
                tests.append({
                    'pc_test_id': row[0],
                    'run_id': row[1],
                    'pc_run_id': row[2],
                    'lob_name': row[3],
                    'track': row[4],
                    'test_name': row[5],
                    'test_status': row[6],
                    'collation_status': row[7],
                    'created_date': row[8].isoformat() if row[8] else None
                })
            
            return tests
            
        finally:
            cursor.close()
            conn.close()
