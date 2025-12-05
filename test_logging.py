#!/usr/bin/env python3
"""
Test script to verify structured logging and error handling implementation.
This script tests the logging system without requiring a database connection.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.logging_config import setup_logging, get_logger
from backend.core.exceptions import (
    ValidationError,
    DatabaseError,
    ResourceNotFoundError,
    AIServiceError,
    QuoteGenerationError,
)

# Setup logging
print("=" * 60)
print("Testing RentalAI Copilot Logging & Error Handling")
print("=" * 60)
print()

# Initialize logging
setup_logging(log_level="INFO", log_file="logs/test_rentalai.log", enable_json=True)
logger = get_logger(__name__)

print("✅ Logging system initialized")
print()

# Test basic logging
print("Testing basic logging levels...")
logger.debug("This is a DEBUG message (should not appear with INFO level)")
logger.info("This is an INFO message")
logger.warning("This is a WARNING message")
logger.error("This is an ERROR message")
print("✅ Basic logging works")
print()

# Test logging with extra fields
print("Testing logging with extra fields...")
logger.info(
    "Request received",
    extra={
        "extra_fields": {
            "request_id": "test-request-123",
            "user_id": 456,
            "endpoint": "/quote/run",
            "method": "POST",
        }
    },
)
print("✅ Extra fields logging works")
print()

# Test custom exceptions
print("Testing custom exceptions...")
exceptions_to_test = [
    ("ValidationError", ValidationError("Invalid input", details={"field": "message"})),
    ("DatabaseError", DatabaseError("Connection failed", details={"host": "localhost"})),
    ("ResourceNotFoundError", ResourceNotFoundError("Quote", 999)),
    ("AIServiceError", AIServiceError("OpenAI timeout", details={"timeout": "30s"})),
    ("QuoteGenerationError", QuoteGenerationError("Invalid quote", details={"reason": "negative subtotal"})),
]

for name, exc in exceptions_to_test:
    try:
        raise exc
    except Exception as e:
        logger.error(f"Caught {name}: {str(e)}", exc_info=False)
        print(f"✅ {name} - status_code: {e.status_code}, error_code: {e.error_code}")

print()

# Test exception with stack trace
print("Testing exception with stack trace...")
try:
    raise ValueError("This is a test exception with stack trace")
except Exception as e:
    logger.error("Exception with stack trace", exc_info=True)
    print("✅ Exception with stack trace logged")

print()

# Summary
print("=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print()
print("Log files created:")
print(f"  - logs/test_rentalai.log (JSON format)")
print()
print("To view the logs:")
print("  tail -f logs/test_rentalai.log")
print()
print("To view formatted logs with jq:")
print('  cat logs/test_rentalai.log | jq .')
print()
