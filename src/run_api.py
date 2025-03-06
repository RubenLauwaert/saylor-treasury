#!/usr/bin/env python3
"""
Script to run the BitcoinTradfi API server.
"""
import uvicorn
from services.daemon import setup_logging
import os
import logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def main():
    # Get host and port from environment or use defaults
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))

    logger.daemon(f"Starting API server at {host}:{port}")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
