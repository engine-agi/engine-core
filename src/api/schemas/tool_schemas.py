# Tool Schemas for API
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# This module contains Pydantic schemas for tool-related API operations


class MCPToolConfigSchema(BaseModel):
    """Schema for MCP tool configuration."""

    server_url: str = Field(..., description="MCP server URL")
    protocol_version: str = Field(..., description="Protocol version")
    capabilities: List[str] = Field(
        default_factory=list, description="Tool capabilities"
    )
    connection_config: Dict[str, Any] = Field(
        default_factory=dict, description="Connection configuration"
    )
    authentication: Dict[str, Any] = Field(
        default_factory=dict, description="Authentication configuration"
    )


class CLIToolConfigSchema(BaseModel):
    """Schema for CLI tool configuration."""

    executable_path: str = Field(..., description="Executable path")
    default_args: List[str] = Field(
        default_factory=list, description="Default arguments"
    )
    environment_variables: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    working_directory: str = Field(..., description="Working directory")
    timeout_seconds: int = Field(default=30, description="Timeout in seconds")
    shell_required: bool = Field(default=False, description="Shell required flag")


class APIToolConfigSchema(BaseModel):
    """Schema for API tool configuration."""

    base_url: str = Field(..., description="Base URL")
    authentication_type: AuthenticationType = Field(
        ..., description="Authentication type"
    )
    authentication_config: Dict[str, Any] = Field(
        default_factory=dict, description="Authentication configuration"
    )
    default_headers: Dict[str, str] = Field(
        default_factory=dict, description="Default headers"
    )
    rate_limit_config: Dict[str, Any] = Field(
        default_factory=dict, description="Rate limit configuration"
    )
    timeout_seconds: int = Field(default=30, description="Timeout in seconds")
    verify_ssl: bool = Field(default=True, description="SSL verification flag")


class ToolHealthSchema(BaseModel):
    """Schema for tool health status."""

    tool_id: str = Field(..., description="Tool ID")
    status: str = Field(..., description="Health status")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    health_data: Dict[str, Any] = Field(default_factory=dict, description="Health data")
    error_message: Optional[str] = Field(default=None, description="Error message")


class ToolCreateSchema(BaseModel):
    """Schema for creating a new tool."""

    name: str = Field(..., description="Tool name")
    tool_type: ToolType = Field(..., description="Tool type")
    version: str = Field(..., description="Tool version")
    description: str = Field(..., description="Tool description")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Tool configuration"
    )
    health_check_enabled: bool = Field(default=True, description="Health check enabled")


class ToolUpdateSchema(BaseModel):
    """Schema for updating an existing tool."""

    name: Optional[str] = Field(default=None, description="Tool name")
    version: Optional[str] = Field(default=None, description="Tool version")
    description: Optional[str] = Field(default=None, description="Tool description")
    configuration: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool configuration"
    )
    health_check_enabled: Optional[bool] = Field(
        default=None, description="Health check enabled"
    )
    active: Optional[bool] = Field(default=None, description="Tool active status")


class ToolResponseSchema(BaseModel):
    """Schema for tool response data."""

    id: str = Field(..., description="Tool ID")
    name: str = Field(..., description="Tool name")
    tool_type: ToolType = Field(..., description="Tool type")
    version: str = Field(..., description="Tool version")
    description: str = Field(..., description="Tool description")
    active: bool = Field(default=True, description="Tool active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
