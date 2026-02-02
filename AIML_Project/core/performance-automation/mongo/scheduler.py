import schedule
import time
from mongo_to_excel import MongoToExcelExporter
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mongo_export_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_export():
    """Execute the MongoDB export"""
    logger.info("Starting scheduled MongoDB export")
    
    try:
        exporter = MongoToExcelExporter('mongo_config.json')
        
        if exporter.connect():
            created_files = exporter.export_collections()
            logger.info(f"Export completed successfully. Created {len(created_files)} files")
            exporter.close()
        else:
            logger.error("Failed to connect to MongoDB")
            
    except Exception as e:
        logger.error(f"Error during scheduled export: {str(e)}")

# Schedule the job
schedule.every().day.at("02:00").do(run_export)  # Daily at 2 AM
# schedule.every().monday.at("09:00").do(run_export)  # Weekly on Monday at 9 AM
# schedule.every().hour.do(run_export)  # Every hour

logger.info("Scheduler started. Waiting for scheduled jobs...")

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(60)