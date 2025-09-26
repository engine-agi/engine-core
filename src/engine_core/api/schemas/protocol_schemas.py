# Protocol Schemas for API
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import CommandType, ParameterType, ProtocolType

# This module contains Pydantic schemas for protocol-related API operations


class ProtocolCommandSchema(BaseModel):
    """Schema for protocol command."""

    command_name: str = Field(..., description="Command name")
    command_type: CommandType = Field(..., description="Command type")
    description: str = Field(..., description="Command description")
    semantic_patterns: List[str] = Field(
        default_factory=list, description="Semantic patterns"
    )
    execution_order: int = Field(..., description="Execution order")
    required_parameters: List[str] = Field(
        default_factory=list, description="Required parameters"
    )
    optional_parameters: List[str] = Field(
        default_factory=list, description="Optional parameters"
    )
    timeout_seconds: int = Field(default=300, description="Timeout in seconds")


class CommandParameterSchema(BaseModel):
    """Schema for command parameter."""

    parameter_name: str = Field(..., description="Parameter name")
    parameter_type: ParameterType = Field(..., description="Parameter type")
    required: bool = Field(default=True, description="Required flag")
    description: str = Field(..., description="Parameter description")
    validation_rules: Dict[str, Any] = Field(
        default_factory=dict, description="Validation rules"
    )
    default_value: Any = Field(default=None, description="Default value")


class ProtocolExecutionSchema(BaseModel):
    """Schema for protocol execution."""

    protocol_id: str = Field(..., description="Protocol ID")
    execution_id: str = Field(..., description="Execution ID")
    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Execution status")
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Start time"
    )
    input_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Input parameters"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Execution context"
    )
    progress_percentage: float = Field(default=0.0, description="Progress percentage")


class ProtocolCreateSchema(BaseModel):
    """Schema for creating a new protocol."""

    name: str = Field(..., description="Protocol name")
    description: str = Field(..., description="Protocol description")
    version: str = Field(..., description="Protocol version")
    protocol_type: ProtocolType = Field(..., description="Protocol type")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Protocol configuration"
    )


class ProtocolUpdateSchema(BaseModel):
    """Schema for updating an existing protocol."""

    name: Optional[str] = Field(default=None, description="Protocol name")
    description: Optional[str] = Field(default=None, description="Protocol description")
    version: Optional[str] = Field(default=None, description="Protocol version")
    configuration: Optional[Dict[str, Any]] = Field(
        default=None, description="Protocol configuration"
    )
    active: Optional[bool] = Field(default=None, description="Protocol active status")


class ProtocolResponseSchema(BaseModel):
    """Schema for protocol response data."""

    id: str = Field(..., description="Protocol ID")
    name: str = Field(..., description="Protocol name")
    description: str = Field(..., description="Protocol description")
    version: str = Field(..., description="Protocol version")
    protocol_type: ProtocolType = Field(..., description="Protocol type")
    active: bool = Field(default=True, description="Protocol active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
