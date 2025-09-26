# Base Schemas for API
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# This module contains base schemas used across all API endpoints


class BaseResponseSchema(BaseModel):
    """Base response schema with common fields."""

    success: bool = Field(default=True, description="Operation success status")
    message: Optional[str] = Field(default=None, description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PaginationSchema(BaseModel):
    """Pagination schema for list responses."""

    page: int = Field(ge=1, description="Current page number")
    size: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")

    @property
    def pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.size - 1) // self.size

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


class FilterSchema(BaseModel):
    """Filter schema for query parameters."""

    field: str = Field(..., description="Field to filter on")
    operator: str = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")
    case_sensitive: bool = Field(default=False, description="Case sensitivity flag")

    @validator("operator")
    def validate_operator(cls, v):
        """Validate filter operator."""
        valid_operators = [
            "equals",
            "not_equals",
            "contains",
            "not_contains",
            "starts_with",
            "ends_with",
            "greater_than",
            "less_than",
            "greater_than_or_equal",
            "less_than_or_equal",
            "in",
            "not_in",
        ]
        if v not in valid_operators:
            raise ValueError(f"Invalid operator: {v}")
        return v


class SortSchema(BaseModel):
    """Sort schema for query parameters."""

    field: str = Field(..., description="Field to sort by")
    direction: str = Field(..., description="Sort direction")

    @validator("direction")
    def validate_direction(cls, v):
        """Validate sort direction."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Direction must be 'asc' or 'desc'")
        return v.lower()


class ErrorResponseSchema(BaseResponseSchema):
    """Error response schema."""

    success: bool = Field(default=False, description="Always false for errors")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class ValidationErrorSchema(BaseModel):
    """Validation error details schema."""

    field: str = Field(..., description="Field with validation error")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value provided")


class HealthCheckSchema(BaseModel):
    """Health check response schema."""

    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: Optional[int] = Field(default=None, description="Service uptime in seconds")
    checks: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed health checks"
    )
