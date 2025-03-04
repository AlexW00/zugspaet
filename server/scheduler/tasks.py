import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from server.core.data_fetcher import fetch_data, fetch_eva_numbers
from server.core.data_importer import import_data

logger = logging.getLogger(__name__)


def run_data_fetch():
    """Run the data fetch process."""
    logger.info("Starting scheduled data fetch process...")
    try:
        logger.info("Fetching new data...")
        save_folder = fetch_data()
        if save_folder:
            logger.info(
                f"Data fetch completed successfully. Data saved to {save_folder}"
            )
        else:
            logger.error("Data fetch failed")
    except Exception as e:
        logger.error(f"Unexpected error during data fetch process: {str(e)}")


def run_data_import():
    """Run the data import process."""
    logger.info("Starting scheduled import process...")
    try:
        logger.info("Importing data to database...")
        processed_dates = import_data()
        if processed_dates:
            logger.info(f"Successfully processed dates: {', '.join(processed_dates)}")
        else:
            logger.info("No new dates to process")
    except Exception as e:
        logger.error(f"Unexpected error during data import process: {str(e)}")


def run_eva_list_update():
    """Run the EVA list update process."""
    logger.info("Starting scheduled EVA list update process...")
    try:
        if fetch_eva_numbers():
            logger.info("EVA list update completed successfully")
        else:
            logger.error("EVA list update failed")
    except Exception as e:
        logger.error(f"Unexpected error during EVA list update process: {str(e)}")


def init_scheduler():
    """Initialize and start the task scheduler."""
    scheduler = BackgroundScheduler()

    # Schedule data fetch every 15 minutes
    scheduler.add_job(
        run_data_fetch,
        trigger=CronTrigger(minute="*/15"),
        id="data_fetch",
        name="Fetch train data every 15 minutes",
    )

    # Schedule data import every 15 minutes, 5 minutes after fetch
    scheduler.add_job(
        run_data_import,
        trigger=CronTrigger(minute="5,20,35,50"),
        id="data_import",
        name="Import train data every 15 minutes",
    )

    # Schedule EVA list update once per day at 3 AM
    scheduler.add_job(
        run_eva_list_update,
        trigger=CronTrigger(hour=3),
        id="eva_update",
        name="Update EVA list daily at 3 AM",
    )

    scheduler.start()
    logger.info("Scheduler started successfully")
    return scheduler
