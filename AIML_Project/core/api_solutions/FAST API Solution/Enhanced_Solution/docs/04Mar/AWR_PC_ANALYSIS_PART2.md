# 🎯 Complete Implementation Guide - Part 2: AWR Parser & API

## 📝 PART 4: AWR HTML Parser

### File: `monitoring/awr/parser.py`

```python
"""
AWR HTML Report Parser
Extracts metrics from Oracle AWR HTML reports
"""
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class AWRParser:
    """Parse AWR HTML reports and extract metrics"""
    
    def __init__(self, html_content: str):
        """Initialize parser with HTML content"""
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.parsed_data = {}
    
    def parse(self) -> Dict:
        """Parse entire AWR report"""
        try:
            logger.info("Starting AWR report parsing")
            
            result = {
                'header': self.parse_header(),
                'load_profile': self.parse_load_profile(),
                'instance_efficiency': self.parse_instance_efficiency(),
                'top_sql': self.parse_top_sql_by_elapsed(),
                'top_sql_by_cpu': self.parse_top_sql_by_cpu(),
                'wait_events': self.parse_wait_events(),
                'system_stats': self.parse_system_stats(),
                'time_model_stats': self.parse_time_model_stats()
            }
            
            logger.info("AWR report parsing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing AWR report: {e}", exc_info=True)
            raise
    
    def parse_header(self) -> Dict:
        """Extract report header information"""
        header = {
            'db_name': '',
            'instance_name': '',
            'host_name': '',
            'snapshot_begin': 0,
            'snapshot_end': 0,
            'snapshot_begin_time': None,
            'snapshot_end_time': None,
            'elapsed_time_minutes': 0,
            'db_time_minutes': 0
        }
        
        try:
            # Find all text content
            text = self.soup.get_text()
            
            # DB Name
            db_match = re.search(r'DB\s+Name[:\s]+(\w+)', text, re.IGNORECASE)
            if db_match:
                header['db_name'] = db_match.group(1)
            
            # Instance Name
            inst_match = re.search(r'Instance[:\s]+(\w+)', text, re.IGNORECASE)
            if inst_match:
                header['instance_name'] = inst_match.group(1)
            
            # Host Name
            host_match = re.search(r'Host[:\s]+([^\s]+)', text)
            if host_match:
                header['host_name'] = host_match.group(1)
            
            # Snapshot IDs
            snap_begin_match = re.search(r'Begin\s+Snap[:\s]+(\d+)', text, re.IGNORECASE)
            if snap_begin_match:
                header['snapshot_begin'] = int(snap_begin_match.group(1))
            
            snap_end_match = re.search(r'End\s+Snap[:\s]+(\d+)', text, re.IGNORECASE)
            if snap_end_match:
                header['snapshot_end'] = int(snap_end_match.group(1))
            
            # Elapsed Time
            elapsed_match = re.search(r'Elapsed[:\s]+([\d.]+)\s*\(mins\)', text, re.IGNORECASE)
            if elapsed_match:
                header['elapsed_time_minutes'] = float(elapsed_match.group(1))
            
            # DB Time
            db_time_match = re.search(r'DB\s+Time[:\s]+([\d.]+)', text, re.IGNORECASE)
            if db_time_match:
                header['db_time_minutes'] = float(db_time_match.group(1))
                
        except Exception as e:
            logger.warning(f"Error parsing header: {e}")
        
        return header
    
    def parse_load_profile(self) -> Dict:
        """Parse Load Profile section"""
        load_profile = {}
        
        try:
            # Find Load Profile table
            for table in self.soup.find_all('table'):
                text = table.get_text()
                if 'Load Profile' in text or 'Per Second' in text:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            metric = cols[0].get_text().strip()
                            value_text = cols[1].get_text().strip()
                            value = self._extract_number(value_text)
                            if value is not None:
                                load_profile[metric] = value
        except Exception as e:
            logger.warning(f"Error parsing load profile: {e}")
        
        return load_profile
    
    def parse_instance_efficiency(self) -> Dict:
        """Parse Instance Efficiency Percentages"""
        efficiency = {}
        
        try:
            for table in self.soup.find_all('table'):
                text = table.get_text()
                if 'Instance Efficiency' in text or 'Hit %' in text:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            metric = cols[0].get_text().strip()
                            value_text = cols[1].get_text().strip()
                            
                            # Extract percentage
                            pct_match = re.search(r'([\d.]+)\s*%', value_text)
                            if pct_match:
                                efficiency[metric] = float(pct_match.group(1))
        except Exception as e:
            logger.warning(f"Error parsing instance efficiency: {e}")
        
        return efficiency
    
    def parse_top_sql_by_elapsed(self, limit: int = 10) -> List[Dict]:
        """Parse Top SQL by Elapsed Time"""
        top_sql = []
        
        try:
            for table in self.soup.find_all('table'):
                caption = table.find('caption')
                if caption and 'SQL ordered by Elapsed Time' in caption.get_text():
                    rows = table.find_all('tr')
                    
                    # Skip header row
                    data_rows = [r for r in rows if r.find('td')]
                    
                    for i, row in enumerate(data_rows[:limit]):
                        cols = row.find_all('td')
                        if len(cols) >= 6:
                            try:
                                sql_entry = {
                                    'rank': i + 1,
                                    'elapsed_time_sec': self._extract_number(cols[0].get_text()),
                                    'executions': int(self._extract_number(cols[1].get_text()) or 0),
                                    'elapsed_per_exec': self._extract_number(cols[2].get_text()),
                                    'cpu_time_sec': self._extract_number(cols[3].get_text()),
                                    'buffer_gets': int(self._extract_number(cols[4].get_text()) or 0),
                                    'sql_id': cols[5].get_text().strip()
                                }
                                top_sql.append(sql_entry)
                            except Exception as e:
                                logger.debug(f"Error parsing SQL row: {e}")
                                continue
        except Exception as e:
            logger.warning(f"Error parsing top SQL by elapsed: {e}")
        
        return top_sql
    
    def parse_top_sql_by_cpu(self, limit: int = 10) -> List[Dict]:
        """Parse Top SQL by CPU Time"""
        top_sql = []
        
        try:
            for table in self.soup.find_all('table'):
                caption = table.find('caption')
                if caption and 'SQL ordered by CPU Time' in caption.get_text():
                    rows = table.find_all('tr')
                    data_rows = [r for r in rows if r.find('td')]
                    
                    for i, row in enumerate(data_rows[:limit]):
                        cols = row.find_all('td')
                        if len(cols) >= 5:
                            try:
                                sql_entry = {
                                    'rank': i + 1,
                                    'cpu_time_sec': self._extract_number(cols[0].get_text()),
                                    'executions': int(self._extract_number(cols[1].get_text()) or 0),
                                    'cpu_per_exec': self._extract_number(cols[2].get_text()),
                                    'elapsed_time_sec': self._extract_number(cols[3].get_text()),
                                    'sql_id': cols[4].get_text().strip()
                                }
                                top_sql.append(sql_entry)
                            except Exception as e:
                                logger.debug(f"Error parsing CPU SQL row: {e}")
                                continue
        except Exception as e:
            logger.warning(f"Error parsing top SQL by CPU: {e}")
        
        return top_sql
    
    def parse_wait_events(self, limit: int = 10) -> List[Dict]:
        """Parse Top Wait Events"""
        wait_events = []
        
        try:
            for table in self.soup.find_all('table'):
                caption = table.find('caption')
                if caption and 'Top' in caption.get_text() and 'Wait Events' in caption.get_text():
                    rows = table.find_all('tr')
                    data_rows = [r for r in rows if r.find('td')]
                    
                    for i, row in enumerate(data_rows[:limit]):
                        cols = row.find_all('td')
                        if len(cols) >= 5:
                            try:
                                event = {
                                    'rank': i + 1,
                                    'event_name': cols[0].get_text().strip(),
                                    'waits': int(self._extract_number(cols[1].get_text()) or 0),
                                    'total_wait_time_sec': self._extract_number(cols[2].get_text()),
                                    'avg_wait_ms': self._extract_number(cols[3].get_text()),
                                    'percent_db_time': self._extract_number(cols[4].get_text()),
                                    'event_class': self._classify_wait_event(cols[0].get_text().strip())
                                }
                                wait_events.append(event)
                            except Exception as e:
                                logger.debug(f"Error parsing wait event row: {e}")
                                continue
        except Exception as e:
            logger.warning(f"Error parsing wait events: {e}")
        
        return wait_events
    
    def parse_system_stats(self) -> Dict:
        """Parse System Statistics"""
        stats = {}
        
        try:
            for table in self.soup.find_all('table'):
                caption = table.find('caption')
                if caption and 'Operating System Statistics' in caption.get_text():
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            stat_name = cols[0].get_text().strip()
                            stat_value = self._extract_number(cols[1].get_text())
                            if stat_value is not None:
                                stats[stat_name] = stat_value
        except Exception as e:
            logger.warning(f"Error parsing system stats: {e}")
        
        return stats
    
    def parse_time_model_stats(self) -> Dict:
        """Parse Time Model Statistics"""
        stats = {}
        
        try:
            for table in self.soup.find_all('table'):
                caption = table.find('caption')
                if caption and 'Time Model Statistics' in caption.get_text():
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            stat_name = cols[0].get_text().strip()
                            stat_value = self._extract_number(cols[1].get_text())
                            if stat_value is not None:
                                stats[stat_name] = stat_value
        except Exception as e:
            logger.warning(f"Error parsing time model stats: {e}")
        
        return stats
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        try:
            # Remove commas and extract number
            clean_text = text.replace(',', '').strip()
            match = re.search(r'[\d.]+', clean_text)
            if match:
                return float(match.group())
        except:
            pass
        return None
    
    def _classify_wait_event(self, event_name: str) -> str:
        """Classify wait event by category"""
        event_lower = event_name.lower()
        
        if 'db file' in event_lower or 'direct path' in event_lower:
            return 'User I/O'
        elif 'log file' in event_lower:
            return 'System I/O'
        elif 'latch' in event_lower:
            return 'Concurrency'
        elif 'enq:' in event_lower or 'enqueue' in event_lower:
            return 'Application'
        elif 'cpu' in event_lower:
            return 'CPU'
        elif 'network' in event_lower or 'sql*net' in event_lower:
            return 'Network'
        else:
            return 'Other'
```

---

## 📝 PART 5: AWR Analyzer

### File: `monitoring/awr/analyzer.py`

```python
"""
AWR Report Analyzer
Identifies performance concerns from parsed AWR data
"""
from typing import List, Dict
from .models import AWRConcern, ConcernSeverity, ConcernCategory
import logging

logger = logging.getLogger(__name__)

class AWRAnalyzer:
    """Analyze AWR metrics and identify performance concerns"""
    
    # Performance thresholds
    THRESHOLDS = {
        'buffer_cache_hit_ratio': 90.0,
        'library_cache_hit_ratio': 95.0,
        'soft_parse_ratio': 90.0,
        'execute_to_parse_ratio': 90.0,
        'latch_hit_ratio': 99.0,
        'elapsed_per_exec_ms': 1000.0,
        'cpu_per_exec_ms': 500.0,
        'disk_reads_per_exec': 10000,
        'wait_time_percent': 10.0,
        'db_cpu_ratio': 70.0
    }
    
    def __init__(self, parsed_data: Dict):
        self.data = parsed_data
        self.concerns: List[AWRConcern] = []
    
    def analyze(self) -> List[AWRConcern]:
        """Run all analysis checks"""
        logger.info("Starting AWR analysis")
        
        self.check_instance_efficiency()
        self.check_top_sql()
        self.check_wait_events()
        self.check_parse_ratios()
        self.check_time_model()
        
        logger.info(f"Analysis complete. Found {len(self.concerns)} concerns")
        return self.concerns
    
    def check_instance_efficiency(self):
        """Check instance efficiency metrics"""
        efficiency = self.data.get('instance_efficiency', {})
        
        # Buffer Cache Hit Ratio
        buffer_hit = efficiency.get('Buffer Hit %', 
                                   efficiency.get('Buffer Cache Hit Ratio', 100))
        if buffer_hit < self.THRESHOLDS['buffer_cache_hit_ratio']:
            self.concerns.append(AWRConcern(
                category=ConcernCategory.INSTANCE_EFFICIENCY,
                concern_type='LOW_BUFFER_HIT_RATIO',
                severity=ConcernSeverity.WARNING,
                title='Low Buffer Cache Hit Ratio',
                description=f'Buffer cache hit ratio is {buffer_hit:.2f}%, below recommended threshold of {self.THRESHOLDS["buffer_cache_hit_ratio"]}%',
                metric_name='Buffer Cache Hit Ratio',
                metric_value=buffer_hit,
                threshold_value=self.THRESHOLDS['buffer_cache_hit_ratio'],
                recommendation='Consider increasing DB_CACHE_SIZE parameter. Review top SQL for excessive physical reads. Check for full table scans.'
            ))
        
        # Library Cache Hit Ratio
        lib_hit = efficiency.get('Library Hit %', 
                                efficiency.get('Library Cache Hit Ratio', 100))
        if lib_hit < self.THRESHOLDS['library_cache_hit_ratio']:
            severity = ConcernSeverity.CRITICAL if lib_hit < 90 else ConcernSeverity.WARNING
            self.concerns.append(AWRConcern(
                category=ConcernCategory.INSTANCE_EFFICIENCY,
                concern_type='LOW_LIBRARY_HIT_RATIO',
                severity=severity,
                title='Low Library Cache Hit Ratio',
                description=f'Library cache hit ratio is {lib_hit:.2f}%, indicating high parse overhead',
                metric_name='Library Cache Hit Ratio',
                metric_value=lib_hit,
                threshold_value=self.THRESHOLDS['library_cache_hit_ratio'],
                recommendation='Increase SHARED_POOL_SIZE. Ensure application uses bind variables. Review cursor_sharing parameter.'
            ))
        
        # Soft Parse Ratio
        soft_parse = efficiency.get('Soft Parse %', 100)
        if soft_parse < self.THRESHOLDS['soft_parse_ratio']:
            self.concerns.append(AWRConcern(
                category=ConcernCategory.INSTANCE_EFFICIENCY,
                concern_type='EXCESSIVE_HARD_PARSING',
                severity=ConcernSeverity.CRITICAL,
                title='Excessive Hard Parsing Detected',
                description=f'Soft parse ratio is only {soft_parse:.2f}%, indicating significant hard parsing activity',
                metric_name='Soft Parse Ratio',
                metric_value=soft_parse,
                threshold_value=self.THRESHOLDS['soft_parse_ratio'],
                recommendation='URGENT: Modify application to use bind variables. Hard parsing causes severe CPU overhead and scalability issues.'
            ))
    
    def check_top_sql(self):
        """Analyze top SQL statements"""
        top_sql = self.data.get('top_sql', [])
        
        for sql in top_sql[:5]:  # Check top 5
            sql_id = sql.get('sql_id', 'UNKNOWN')
            elapsed_per_exec = sql.get('elapsed_per_exec', 0)
            buffer_gets = sql.get('buffer_gets', 0)
            executions = sql.get('executions', 1)
            
            # Convert to milliseconds if needed
            elapsed_ms = elapsed_per_exec * 1000 if elapsed_per_exec < 10 else elapsed_per_exec
            
            # Check for slow SQL
            if elapsed_ms > self.THRESHOLDS['elapsed_per_exec_ms']:
                severity = ConcernSeverity.CRITICAL if elapsed_ms > 5000 else ConcernSeverity.WARNING
                self.concerns.append(AWRConcern(
                    category=ConcernCategory.TOP_SQL,
                    concern_type='SLOW_SQL_EXECUTION',
                    severity=severity,
                    title=f'Slow SQL Statement: {sql_id}',
                    description=f'SQL {sql_id} takes average of {elapsed_ms:.2f}ms per execution with {executions:,} executions',
                    metric_name='Elapsed Time Per Execution',
                    metric_value=elapsed_ms,
                    threshold_value=self.THRESHOLDS['elapsed_per_exec_ms'],
                    recommendation='Review execution plan. Check for missing indexes. Consider SQL tuning or query rewrite.',
                    sql_id=sql_id
                ))
            
            # Check for high logical reads
            if executions > 0:
                gets_per_exec = buffer_gets / executions
                if gets_per_exec > self.THRESHOLDS['disk_reads_per_exec']:
                    self.concerns.append(AWRConcern(
                        category=ConcernCategory.TOP_SQL,
                        concern_type='HIGH_LOGICAL_READS',
                        severity=ConcernSeverity.WARNING,
                        title=f'High Buffer Gets: {sql_id}',
                        description=f'SQL {sql_id} performs {gets_per_exec:,.0f} buffer gets per execution',
                        metric_name='Buffer Gets Per Execution',
                        metric_value=gets_per_exec,
                        threshold_value=self.THRESHOLDS['disk_reads_per_exec'],
                        recommendation='Check for full table scans. Review indexes. Consider partitioning for large tables.',
                        sql_id=sql_id
                    ))
    
    def check_wait_events(self):
        """Analyze wait events"""
        wait_events = self.data.get('wait_events', [])
        
        for event in wait_events[:5]:  # Top 5 events
            event_name = event.get('event_name', '')
            percent_db_time = event.get('percent_db_time', 0)
            
            if percent_db_time > self.THRESHOLDS['wait_time_percent']:
                severity, concern_type, recommendation = self._categorize_wait_event(
                    event_name, percent_db_time
                )
                
                self.concerns.append(AWRConcern(
                    category=ConcernCategory.WAIT_EVENTS,
                    concern_type=concern_type,
                    severity=severity,
                    title=f'High Wait Time: {event_name}',
                    description=f'{event_name} represents {percent_db_time:.2f}% of total database time',
                    metric_name='Percent of DB Time',
                    metric_value=percent_db_time,
                    threshold_value=self.THRESHOLDS['wait_time_percent'],
                    recommendation=recommendation
                ))
    
    def check_parse_ratios(self):
        """Check parse-related metrics"""
        load_profile = self.data.get('load_profile', {})
        
        # Execute to Parse ratio
        exec_to_parse = load_profile.get('Execute to Parse %', 100)
        if exec_to_parse < self.THRESHOLDS['execute_to_parse_ratio']:
            self.concerns.append(AWRConcern(
                category=ConcernCategory.SYSTEM_STATS,
                concern_type='HIGH_PARSE_RATIO',
                severity=ConcernSeverity.WARNING,
                title='High Parse to Execute Ratio',
                description=f'Execute to Parse ratio is {exec_to_parse:.2f}%, indicating excessive parsing',
                metric_name='Execute to Parse %',
                metric_value=exec_to_parse,
                threshold_value=self.THRESHOLDS['execute_to_parse_ratio'],
                recommendation='Use connection pooling. Keep cursors open for reuse. Enable session_cached_cursors.'
            ))
    
    def check_time_model(self):
        """Check time model statistics"""
        time_model = self.data.get('time_model_stats', {})
        
        db_cpu = time_model.get('DB CPU', 0)
        db_time = time_model.get('DB time', 1)
        
        if db_time > 0:
            cpu_ratio = (db_cpu / db_time) * 100
            
            if cpu_ratio > self.THRESHOLDS['db_cpu_ratio']:
                self.concerns.append(AWRConcern(
                    category=ConcernCategory.SYSTEM_STATS,
                    concern_type='HIGH_CPU_USAGE',
                    severity=ConcernSeverity.WARNING,
                    title='High CPU Utilization',
                    description=f'CPU usage is {cpu_ratio:.2f}% of database time',
                    metric_name='DB CPU Ratio',
                    metric_value=cpu_ratio,
                    threshold_value=self.THRESHOLDS['db_cpu_ratio'],
                    recommendation='Review top SQL by CPU time. Check for inefficient queries or missing indexes.'
                ))
    
    def _categorize_wait_event(self, event_name: str, percent: float):
        """Categorize wait event and provide recommendation"""
        event_lower = event_name.lower()
        
        severity = ConcernSeverity.CRITICAL if percent > 30 else ConcernSeverity.WARNING
        
        if 'db file sequential read' in event_lower:
            return severity, 'IO_SEQUENTIAL_READ', 'Check for index range scans on large tables. Consider SSD storage. Review top SQL.'
        elif 'db file scattered read' in event_lower:
            return severity, 'IO_SCATTERED_READ', 'Full table scans detected. Add indexes. Consider parallel query. Check table statistics.'
        elif 'log file sync' in event_lower:
            return severity, 'LOG_FILE_SYNC', 'Slow commit times. Check disk I/O for redo logs. Consider faster storage or log file multiplexing.'
        elif 'latch' in event_lower:
            return severity, 'LATCH_CONTENTION', 'Latch contention detected. Review application for hot blocks. Consider RAC or partitioning.'
        elif 'enq:' in event_lower or 'enqueue' in event_lower:
            return severity, 'ENQUEUE_CONTENTION', 'Lock contention found. Optimize transaction design. Reduce lock hold times.'
        elif 'cpu' in event_lower:
            return severity, 'CPU_WAIT', 'High CPU waits. Review top SQL by CPU. Check for runaway queries.'
        else:
            return severity, 'OTHER_WAIT', f'Investigate {event_name} wait event. Check Oracle documentation for specific tuning.'
    
    def get_summary(self) -> Dict:
        """Get analysis summary"""
        critical = sum(1 for c in self.concerns if c.severity == ConcernSeverity.CRITICAL)
        warning = sum(1 for c in self.concerns if c.severity == ConcernSeverity.WARNING)
        info = sum(1 for c in self.concerns if c.severity == ConcernSeverity.INFO)
        
        return {
            'total_concerns': len(self.concerns),
            'critical_concerns': critical,
            'warning_concerns': warning,
            'info_concerns': info,
            'top_concerns': [c.dict() for c in self.concerns[:5]]
        }
```

**Continue to Part 3 with Database operations and API routes...**