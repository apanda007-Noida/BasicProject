import os
import sys
import time
import logging
import datetime
# pyrefly: ignore [missing-import]
import schedule

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingestion.scraper import run_scraper

# Set up logging for scheduler
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Scheduler) %(message)s",
    handlers=[
        logging.FileHandler("logs/scheduler.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def get_local_time_for_ist_10am():
    """
    Calculate the local system time corresponding to 10:00 AM IST (04:30 UTC).
    This ensures that regardless of host system timezone, it fires at the correct moment.
    """
    # 10:00 AM IST is 04:30 AM UTC
    target_utc = datetime.time(4, 30)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    target_utc_dt = datetime.datetime.combine(now_utc.date(), target_utc, tzinfo=datetime.timezone.utc)
    
    # Convert to local timezone
    target_local_dt = target_utc_dt.astimezone()
    local_time_str = target_local_dt.strftime("%H:%M")
    
    logging.info(f"Target time: 10:00 AM IST (04:30 AM UTC) -> Local System Time: {local_time_str} ({target_local_dt.tzinfo})")
    return local_time_str

def job():
    logging.info("Scheduled job triggered: Starting mutual fund scraping...")
    try:
        success_count = run_scraper()
        logging.info(f"Scheduled job completed. Scraped {success_count} pages.")
    except Exception as e:
        logging.error(f"Error during scheduled scraper run: {e}")

def main():
    logging.info("Starting Daily Ingestion Scheduler Service")
    
    # Compute local target time
    local_time_str = get_local_time_for_ist_10am()
    
    # Schedule the job daily
    schedule.every().day.at(local_time_str).do(job)
    logging.info(f"Scraper scheduled daily at {local_time_str} local time.")
    
    # Run once immediately on start for initial data load / verification
    logging.info("Running initial scraping run on scheduler startup...")
    job()
    
    logging.info("Scheduler service is running. Waiting for scheduled triggers...")
    try:
        while True:
            schedule.run_pending()
            time.sleep(10) # check every 10 seconds
    except KeyboardInterrupt:
        logging.info("Scheduler service stopped by user.")
    except Exception as e:
        logging.critical(f"Scheduler service crashed: {e}")

if __name__ == "__main__":
    main()
