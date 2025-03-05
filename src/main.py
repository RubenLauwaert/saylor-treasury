"""
Saylor Treasury - Main Application
---------------------------------
This is the main entry point for the Saylor Treasury application.
It starts the daemon process that automatically updates Bitcoin data regularly.
"""

from services.daemon import setup_logging, run_daemon
import logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Run the daemon process
    run_daemon()
