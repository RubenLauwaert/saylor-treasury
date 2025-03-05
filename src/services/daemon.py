import schedule
import time
import logging
import colorlog


def setup_logging():
    # Define custom log levels
    DB_UPDATE = 25  # Between INFO (20) and WARNING (30)
    DATABASE = 26  # Just after DB_UPDATE

    # Add level names
    logging.addLevelName(DB_UPDATE, "DB_UPDATE")
    logging.addLevelName(DATABASE, "DATABASE")

    # Add methods to the logger class for these custom levels
    def db_update(self, message, *args, **kwargs):
        if self.isEnabledFor(DB_UPDATE):
            self._log(DB_UPDATE, message, args, **kwargs)

    def database(self, message, *args, **kwargs):
        if self.isEnabledFor(DATABASE):
            self._log(DATABASE, message, args, **kwargs)

    # Add the methods to the Logger class
    logging.Logger.db_update = db_update
    logging.Logger.database = database

    log_colors = {
        "DEBUG": "white",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
        "DATABASE": "blue",  # Regular blue for database operations
        "DB_UPDATE": "bold_blue",  # Bold blue for database updates
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

    # Set level to DATABASE or DB_UPDATE level depending on which is lower
    # This ensures both custom levels will be shown
    root_logger.setLevel(min(DATABASE, DB_UPDATE))


def run_daemon():
    # schedule.every().day.at("01:00").do()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    setup_logging()
    print("Daemon started")
    run_daemon()
