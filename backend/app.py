from dotenv import load_dotenv
load_dotenv()  # <-- This loads your .env file

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.quote import router as quote_router
from backend.routes.runs import router as runs_router
from backend.core.logging_config import setup_logging, get_logger
from backend.core.middleware import RequestLoggingMiddleware
from backend.core.exceptions import (
    RentalAIException,
    rentalai_exception_handler,
    general_exception_handler,
)

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "logs/rentalai.log")
setup_logging(log_level=log_level, log_file=log_file, enable_json=True)

logger = get_logger(__name__)

app = FastAPI(
    title="RentalAI Copilot API",
    description="Autonomous quoting system for the equipment rental industry",
    version="1.0.0",
)

# Add exception handlers
app.add_exception_handler(RentalAIException, rentalai_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add request logging middleware (before CORS so it logs all requests)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "https://glorious-disco-977rvwx4vvp7fx99v-4200.app.github.dev"
    ],
    allow_origin_regex=r"https://.*\.app\.github\.dev$",  # for Codespaces
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(quote_router)
app.include_router(runs_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("RentalAI Copilot API starting up")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_file}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RentalAI Copilot API shutting down")

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "RentalAI Copilot API"}
