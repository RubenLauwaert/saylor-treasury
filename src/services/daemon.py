import schedule
import time
import logging
import colorlog
import asyncio

from services.update_db import DatabaseUpdater


def setup_logging():
    # Define custom log levels
    DATABASE = 25  # For database operations
    DB_UPDATE = 26  # For database updates
    DAEMON = 27  # New level for daemon operations (highest priority)

    # Add level names
    logging.addLevelName(DATABASE, "DATABASE")
    logging.addLevelName(DB_UPDATE, "DB_UPDATE")
    logging.addLevelName(DAEMON, "DAEMON")

    # Add methods to the logger class for these custom levels
    def db_update(self, message, *args, **kwargs):
        if self.isEnabledFor(DB_UPDATE):
            self._log(DB_UPDATE, message, args, **kwargs)

    def database(self, message, *args, **kwargs):
        if self.isEnabledFor(DATABASE):
            self._log(DATABASE, message, args, **kwargs)

    def daemon(self, message, *args, **kwargs):
        if self.isEnabledFor(DAEMON):
            self._log(DAEMON, message, args, **kwargs)

    # Add the methods to the Logger class
    logging.Logger.db_update = db_update
    logging.Logger.database = database
    logging.Logger.daemon = daemon

    log_colors = {
        "DEBUG": "white",
        "INFO": "green",
        "DATABASE": "blue",  # Regular blue for database operations
        "DB_UPDATE": "bold_blue",  # Bold blue for database updates
        "DAEMON": "bold_green",  # Bold green for daemon operations
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }

    formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
        datefmt=None,
        reset=True,
        log_colors=log_colors,
        secondary_log_colors={},
        style="%",
    )

    # Set up the handler and logger
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    # Set the threshold to show all custom levels and above
    # The minimum of all our custom levels is DATABASE
    root_logger.setLevel(DATABASE)  # Now this excludes DATABASE messages


def run_daemon():
    """
    Runs scheduled tasks for database updates in a logical sequence:
    1. Sync new bitcoin entities (hourly)
    2. Sync new bitcoin filings (every 15 minutes)
    3. After new filings are synced, extract XBRL facts and generate AI statements

    When first called, a full update cycle runs immediately, and then the next scheduled
    full update will be adjusted to maintain a reasonable interval.
    """

    # Create database updater
    dbu = DatabaseUpdater()
    logger = logging.getLogger(__name__)

    # Get current time to calculate next run times
    from datetime import datetime, timedelta

    current_time = datetime.now()

    # Function to run the complete update cycle
    async def run_full_update_cycle():
        logger.daemon("Starting full update cycle")
        # Step 1: Find new bitcoin-related entities
        await dbu.sync_bitcoin_entities()
        # Step 2: Get new filings for all existing entities
        await dbu.sync_bitcoin_filings()
        # Step 3: Extract structured XBRL data from 10-Q filings
        await dbu.sync_tenq_xbrl_facts()
        # Step 4: Generate AI insights from filings
        await dbu.sync_gen_ai_statements()
        logger.daemon("Completed full update cycle")

    # Function to run just the filings update and dependent processes
    async def run_filings_update():
        logger.daemon("Starting filings update cycle")
        # Step 1: Get new filings for all existing entities
        await dbu.sync_bitcoin_filings()
        # Step 2: Extract structured XBRL data from 10-Q filings
        await dbu.sync_tenq_xbrl_facts()
        # Step 3: Generate AI insights from filings
        await dbu.sync_gen_ai_statements()
        logger.daemon("Completed filings update cycle")

    # Run full update cycle immediately when daemon starts
    logger.daemon("Daemon started - running initial full update cycle")
    asyncio.run(run_full_update_cycle())
    logger.daemon("Initial update complete - setting up scheduled tasks")

    # Determine appropriate times for next scheduled runs
    minutes_to_hour = 60 - current_time.minute

    # If we're within 30 minutes of the top of the hour, skip the next hourly update
    # and wait for the following hour to avoid duplicate work
    if minutes_to_hour <= 30:
        # Skip the immediate hourly update, schedule for the next hour
        next_full_update_hour = (current_time.hour + 2) % 24  # Skip one hour
        logger.daemon(
            f"Next full cycle scheduled at {next_full_update_hour}:00 (skipping {(current_time.hour + 1) % 24}:00)"
        )
        schedule.every().day.at(f"{next_full_update_hour:02d}:00").do(
            lambda: asyncio.run(run_full_update_cycle())
        )

        # Then resume normal hourly schedule
        for hour in range(
            (current_time.hour + 3) % 24, (current_time.hour + 3) % 24 + 24, 1
        ):
            schedule.every().day.at(f"{hour % 24:02d}:00").do(
                lambda: asyncio.run(run_full_update_cycle())
            )
    else:
        # Normal hourly scheduling starting from next hour
        for hour in range(
            (current_time.hour + 1) % 24, (current_time.hour + 1) % 24 + 24, 1
        ):
            schedule.every().day.at(f"{hour % 24:02d}:00").do(
                lambda: asyncio.run(run_full_update_cycle())
            )

    # Calculate appropriate times for filing updates (avoiding immediate duplicates)
    next_update_times = []
    for minute in [15, 30, 45, 60]:
        # If we just finished and the next scheduled time is too close (within 10 min), skip it
        next_minute = (current_time.minute + minute) % 60
        next_hour = current_time.hour + (
            1 if minute == 60 or current_time.minute + minute >= 60 else 0
        )

        if minute - current_time.minute % 15 > 10:  # If more than 10 minutes away
            next_update_times.append(f"{next_hour % 24:02d}:{next_minute:02d}")

    # Schedule filings-only update cycles at calculated times
    for update_time in next_update_times:
        logger.daemon(f"Scheduling filing update at {update_time}")
        schedule.every().day.at(update_time).do(
            lambda: asyncio.run(run_filings_update())
        )

    # Then schedule the regular 15-minute interval updates for subsequent days
    for hour in range(0, 24):
        for minute in [0, 15, 30, 45]:
            time_str = f"{hour:02d}:{minute:02d}"
            if time_str not in next_update_times:  # Avoid duplicates
                schedule.every().day.at(time_str).do(
                    lambda: asyncio.run(
                        run_full_update_cycle() if minute == 0 else run_filings_update()
                    )
                )

    # Log daemon started with DAEMON level
    logger.daemon("Database update daemon started - running scheduled tasks")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


# if __name__ == "__main__":
#     setup_logging()
#     logger = logging.getLogger(__name__)
#     logger.daemon("Daemon started")
#     run_daemon()
