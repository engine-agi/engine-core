# Base Schemas for API
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

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

    @field_validator("operator")
    @classmethod
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

    @field_validator("direction")
    @classmethod
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


class MetricsSchema(BaseModel):
    """Metrics response schema."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Metrics timestamp"
    )
    metrics: Dict[str, Any] = Field(..., description="Metrics data")
    tags: Optional[Dict[str, str]] = Field(default=None, description="Metrics tags")


class ConfigSchema(BaseModel):
    """Configuration schema."""

    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    config_type: str = Field(..., description="Configuration value type")
    description: Optional[str] = Field(
        default=None, description="Configuration description"
    )
    required: bool = Field(
        default=False, description="Whether configuration is required"
    )


class AuditLogSchema(BaseModel):
    """Audit log schema."""

    id: str = Field(..., description="Audit log ID")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Log timestamp"
    )
    user_id: Optional[str] = Field(default=None, description="User ID")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    resource_id: Optional[str] = Field(default=None, description="Resource ID")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional details"
    )
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")


class RateLimitSchema(BaseModel):
    """Rate limit schema."""

    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="Reset time")
    retry_after: Optional[int] = Field(default=None, description="Retry after seconds")


class VersionSchema(BaseModel):
    """Version information schema."""

    version: str = Field(..., description="Version string")
    build_date: Optional[datetime] = Field(default=None, description="Build date")
    git_commit: Optional[str] = Field(default=None, description="Git commit hash")
    environment: str = Field(..., description="Environment name")


class NotificationSchema(BaseModel):
    """Notification schema."""

    id: str = Field(..., description="Notification ID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field(default="normal", description="Notification priority")
    read: bool = Field(default=False, description="Read status")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Expiration timestamp"
    )


class SearchQuerySchema(BaseModel):
    """Search query schema."""

    query: str = Field(..., description="Search query string")
    filters: Optional[List[FilterSchema]] = Field(
        default=None, description="Search filters"
    )
    sort: Optional[SortSchema] = Field(default=None, description="Search sorting")
    pagination: Optional[PaginationSchema] = Field(
        default=None, description="Search pagination"
    )


class BulkOperationSchema(BaseModel):
    """Bulk operation schema."""

    operation: str = Field(..., description="Bulk operation type")
    items: List[Dict[str, Any]] = Field(..., description="Items to process")
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Operation options"
    )


class FileUploadSchema(BaseModel):
    """File upload schema."""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File content type")
    size: int = Field(..., description="File size in bytes")
    checksum: Optional[str] = Field(default=None, description="File checksum")


class WebhookSchema(BaseModel):
    """Webhook configuration schema."""

    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to listen for")
    secret: Optional[str] = Field(default=None, description="Webhook secret")
    active: bool = Field(default=True, description="Webhook active status")
    headers: Optional[Dict[str, str]] = Field(
        default=None, description="Custom headers"
    )
