"""
Scheduled Daily Discovery for AppDynamics
Runs discovery for all active LOBs on a schedule
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/appd_discovery_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
DISCOVERY_SCHEDULE_TIME = os.getenv('APPD_DISCOVERY_TIME', '02:00')  # Default 2 AM
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', None)


def run_discovery_for_all_lobs():
    """
    Run discovery for all active LOBs
    Called by scheduler
    """
    logger.info("=" * 60)
    logger.info("Starting scheduled AppDynamics discovery")
    logger.info("=" * 60)
    
    try:
        # Get all active LOBs from API or database
        # For now, configure LOBs here
        lobs_to_discover = get_active_lobs()
        
        if not lobs_to_discover:
            logger.warning("No active LOBs configured for discovery")
            return
        
        logger.info(f"Discovering LOBs: {', '.join(lobs_to_discover)}")
        
        # Call discovery API
        response = requests.post(
            f"{API_BASE_URL}/api/v1/monitoring/appd/discovery/run",
            json={"lob_names": lobs_to_discover},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ Discovery initiated successfully")
            logger.info(f"  Task ID: {data.get('task_id')}")
            logger.info(f"  LOBs: {', '.join(data.get('lob_names', []))}")
            
            # Send success notification if configured
            if NOTIFICATION_EMAIL:
                send_notification(
                    subject="AppD Discovery Success",
                    message=f"Discovery completed for LOBs: {', '.join(lobs_to_discover)}"
                )
        else:
            logger.error(f"✗ Discovery failed: HTTP {response.status_code}")
            logger.error(f"  Response: {response.text}")
            
            # Send failure notification
            if NOTIFICATION_EMAIL:
                send_notification(
                    subject="AppD Discovery Failed",
                    message=f"Discovery failed with status {response.status_code}: {response.text}",
                    is_error=True
                )
                
    except requests.exceptions.Timeout:
        logger.error("✗ Discovery request timed out")
        if NOTIFICATION_EMAIL:
            send_notification(
                subject="AppD Discovery Timeout",
                message="Discovery request timed out after 30 seconds",
                is_error=True
            )
    except Exception as e:
        logger.error(f"✗ Discovery failed with exception: {str(e)}", exc_info=True)
        if NOTIFICATION_EMAIL:
            send_notification(
                subject="AppD Discovery Exception",
                message=f"Discovery failed with exception: {str(e)}",
                is_error=True
            )
    
    logger.info("=" * 60)


def get_active_lobs():
    """
    Get list of active LOBs to discover
    
    Options:
    1. From environment variable
    2. From API call to get LOBs
    3. Hardcoded list
    
    Returns:
        List of LOB names
    """
    # Option 1: From environment
    lobs_env = os.getenv('APPD_LOBS_TO_DISCOVER', '')
    if lobs_env:
        return [lob.strip() for lob in lobs_env.split(',') if lob.strip()]
    
    # Option 2: From API (if you have an endpoint)
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/monitoring/appd/lobs",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return [lob['lob_name'] for lob in data.get('lobs', [])]
    except:
        pass
    
    # Option 3: Hardcoded fallback
    return ['Retail', 'Banking']


def send_notification(subject, message, is_error=False):
    """
    Send email notification
    
    Args:
        subject: Email subject
        message: Email message
        is_error: Whether this is an error notification
    """
    try:
        # Implement your notification logic here
        # Options:
        # 1. SMTP email
        # 2. Slack webhook
        # 3. Microsoft Teams webhook
        # 4. PagerDuty
        
        logger.info(f"Notification: {subject} - {message}")
        
        # Example SMTP implementation:
        """
        import smtplib
        from email.mime.text import MIMEText
        
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = 'noreply@company.com'
        msg['To'] = NOTIFICATION_EMAIL
        
        s = smtplib.SMTP('smtp.company.com')
        s.send_message(msg)
        s.quit()
        """
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


def test_discovery():
    """Test discovery manually"""
    logger.info("Running test discovery...")
    run_discovery_for_all_lobs()


def main():
    """Main scheduler function"""
    logger.info("AppDynamics Discovery Scheduler Starting...")
    logger.info(f"API Base URL: {API_BASE_URL}")
    logger.info(f"Scheduled Time: {DISCOVERY_SCHEDULE_TIME}")
    logger.info(f"LOBs: {', '.join(get_active_lobs())}")
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Parse schedule time
    hour, minute = DISCOVERY_SCHEDULE_TIME.split(':')
    
    # Add job - runs daily at specified time
    scheduler.add_job(
        run_discovery_for_all_lobs,
        trigger=CronTrigger(hour=int(hour), minute=int(minute)),
        id='appd_daily_discovery',
        name='AppDynamics Daily Discovery',
        replace_existing=True
    )
    
    logger.info(f"✓ Scheduler configured to run daily at {DISCOVERY_SCHEDULE_TIME}")
    logger.info("Press Ctrl+C to exit")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test mode - run once
        test_discovery()
    else:
        # Scheduler mode
        main()


"""
Usage:

1. Install dependencies:
   pip install apscheduler requests python-dotenv

2. Configure .env.local:
   API_BASE_URL=http://localhost:8000
   APPD_DISCOVERY_TIME=02:00
   APPD_LOBS_TO_DISCOVER=Retail,Banking
   NOTIFICATION_EMAIL=team@company.com

3. Run scheduler:
   python schedule_daily_discovery.py

4. Test run:
   python schedule_daily_discovery.py test

5. Run as systemd service:
   
   Create /etc/systemd/system/appd-discovery.service:
   
   [Unit]
   Description=AppDynamics Discovery Scheduler
   After=network.target
   
   [Service]
   Type=simple
   User=your_user
   WorkingDirectory=/path/to/project
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/python schedule_daily_discovery.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   
   Then:
   sudo systemctl daemon-reload
   sudo systemctl enable appd-discovery
   sudo systemctl start appd-discovery
   sudo systemctl status appd-discovery

6. Or use cron:
   0 2 * * * cd /path/to/project && /path/to/venv/bin/python schedule_daily_discovery.py test >> /var/log/appd_discovery.log 2>&1
"""