from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routes import entities
from .dependencies import get_api_key
import logging

# Set up logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("API starting up")
    yield
    # Shutdown code
    logger.info("API shutting down")


# Create FastAPI app
app = FastAPI(
    title="BitcoinTradfi API",
    description="API for accessing Bitcoin Treasury data",
    version="0.1.0",
    # Require authentication for all routes
    # dependencies=[Depends(get_api_key)],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(entities.router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to the BitcoinTradfi API",
        "docs": "/docs",
        "endpoints": {
            "entities": "/entities",
            "entity_by_ticker": "/entities/{ticker}",
        },
    }
