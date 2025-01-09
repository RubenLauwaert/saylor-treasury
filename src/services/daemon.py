import schedule
import time
import logging
import colorlog
from services.update_db import add_new_entities, update_sec_filings_for_all_companies

def setup_logging():
    log_colors = {
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }

    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors=log_colors,
        secondary_log_colors={},
        style='%'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def run_daemon():
    schedule.every().day.at("00:00").do(add_new_companies)
    schedule.every().day.at("01:00").do(update_sec_filings_for_all_companies)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    setup_logging()
    print("Daemon started")
    run_daemon()