"""
Logging utility for monitoring system
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Global logger registry
_loggers = {}

def setup_logger(name: str, 
                log_file: Optional[str] = None, 
                level: str = 'INFO',
                console: bool = True,
                file_mode: str = 'a') -> logging.Logger:
    """
    Setup and configure a logger
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Whether to output to console
        file_mode: File mode ('a' for append, 'w' for write)
        
    Returns:
        Configured logger instance
    """
    # Return existing logger if already configured
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode=file_mode)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    # Store in registry
    _loggers[name] = logger
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    else:
        # Create a new logger if it doesn't exist
        return setup_logger(name)

class LoggerContext:
    """Context manager for temporary logger configuration"""
    
    def __init__(self, logger_name: str, level: str):
        self.logger_name = logger_name
        self.new_level = level
        self.old_level = None
        
    def __enter__(self):
        logger = get_logger(self.logger_name)
        self.old_level = logger.level
        logger.setLevel(getattr(logging, self.new_level.upper()))
        return logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = get_logger(self.logger_name)
        logger.setLevel(self.old_level)

def log_exception(logger: logging.Logger, message: str, exception: Exception):
    """
    Log an exception with full traceback
    
    Args:
        logger: Logger instance
        message: Custom message
        exception: Exception to log
    """
    logger.error(f"{message}: {str(exception)}", exc_info=True)

def create_test_logger(test_run_id: str, base_dir: str = './logs') -> logging.Logger:
    """
    Create a logger specific to a test run
    
    Args:
        test_run_id: Test run identifier
        base_dir: Base directory for log files
        
    Returns:
        Configured logger
    """
    log_dir = Path(base_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{test_run_id}_{timestamp}.log"
    
    return setup_logger(
        name=f"TestRun_{test_run_id}",
        log_file=str(log_file),
        level='INFO',
        console=True,
        file_mode='w'
    )

# Example usage functions
def log_section(logger: logging.Logger, title: str, width: int = 80):
    """Log a section header"""
    logger.info("=" * width)
    logger.info(title.center(width))
    logger.info("=" * width)

def log_subsection(logger: logging.Logger, title: str, width: int = 80):
    """Log a subsection header"""
    logger.info("-" * width)
    logger.info(title)
    logger.info("-" * width)

def log_progress(logger: logging.Logger, current: int, total: int, prefix: str = "Progress"):
    """Log progress information"""
    percentage = (current / total) * 100
    logger.info(f"{prefix}: {current}/{total} ({percentage:.1f}%)")

def log_metric(logger: logging.Logger, metric_name: str, value, unit: str = ""):
    """Log a metric value"""
    if unit:
        logger.info(f"  {metric_name}: {value} {unit}")
    else:
        logger.info(f"  {metric_name}: {value}")

def log_status(logger: logging.Logger, status: str, message: str):
    """Log status with emoji/symbol"""
    symbols = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ',
        'running': '→'
    }
    symbol = symbols.get(status.lower(), '•')
    logger.info(f"{symbol} {message}")
    