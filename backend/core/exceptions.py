"""
Custom exceptions and error handling for RentalAI Copilot.

Provides standardized error responses and custom exception types.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class RentalAIException(Exception):
    """Base exception class for RentalAI Copilot."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RentalAIException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class DatabaseError(RentalAIException):
    """Raised when database operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ResourceNotFoundError(RentalAIException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} with ID {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": str(resource_id)},
        )


class AIServiceError(RentalAIException):
    """Raised when AI/LLM service calls fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AI_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class QuoteGenerationError(RentalAIException):
    """Raised when quote generation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="QUOTE_GENERATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ConfigurationError(RentalAIException):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


async def rentalai_exception_handler(
    request: Request, exc: RentalAIException
) -> JSONResponse:
    """
    Global exception handler for RentalAI custom exceptions.

    Converts custom exceptions to standardized JSON error responses.
    """
    error_response = ErrorResponse(
        error=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unexpected errors.

    Catches all unhandled exceptions and returns a standardized error response.
    """
    error_response = ErrorResponse(
        error="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
        details={"exception_type": type(exc).__name__} if isinstance(exc, Exception) else None,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(exclude_none=True),
    )
