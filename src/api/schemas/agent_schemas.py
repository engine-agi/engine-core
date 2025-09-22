# Agent Schemas for API
# This module contains Pydantic schemas for agent-related API operations

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .base_schemas import BaseResponseSchema
from .enums import AgentStatus, ProficiencyLevel, AuthenticationType, ContentType


class AgentStackItemSchema(BaseModel):
    """Schema for agent technology stack item."""
    technology: str = Field(..., description="Technology name")
    version: str = Field(..., description="Technology version")
    proficiency_level: ProficiencyLevel = Field(..., description="Proficiency level")
    years_experience: int = Field(ge=0, le=50, description="Years of experience")

    @validator('technology')
    def validate_technology(cls, v):
        """Validate technology name."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Technology name cannot be empty")
        return v.strip()


class AgentToolSchema(BaseModel):
    """Schema for agent tool configuration."""
    tool_id: str = Field(..., description="Tool ID")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Tool configuration")
    enabled: bool = Field(default=True, description="Tool enabled status")


class AgentConfigSchema(BaseModel):
    """Schema for agent configuration."""
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    config_type: str = Field(..., description="Configuration type")
    description: Optional[str] = Field(default=None, description="Configuration description")


class AgentCreateSchema(BaseModel):
    """Schema for creating a new agent."""
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    model: str = Field(..., description="AI model to use")
    speciality: str = Field(..., min_length=1, max_length=500, description="Agent speciality")
    persona: str = Field(..., min_length=1, max_length=1000, description="Agent persona description")
    stack: List[str] = Field(default_factory=list, description="Technology stack")
    tools: List[str] = Field(default_factory=list, description="Tool identifiers")
    protocol_id: Optional[str] = Field(default=None, description="Protocol ID")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID")
    book_id: Optional[str] = Field(default=None, description="Book ID")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")

    @validator('name')
    def validate_name(cls, v):
        """Validate agent name."""
        if not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v.strip()

    @validator('model')
    def validate_model(cls, v):
        """Validate AI model."""
        valid_models = [
            "claude-3.5-sonnet", "gpt-4", "gpt-3.5-turbo",
            "claude-3-opus", "llama-2-70b", "mistral-7b"
        ]
        if v not in valid_models:
            raise ValueError(f"Invalid model: {v}")
        return v


class AgentUpdateSchema(BaseModel):
    """Schema for updating an existing agent."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Agent name")
    model: Optional[str] = Field(default=None, description="AI model to use")
    speciality: Optional[str] = Field(default=None, min_length=1, max_length=500, description="Agent speciality")
    persona: Optional[str] = Field(default=None, min_length=1, max_length=1000, description="Agent persona description")
    stack: Optional[List[str]] = Field(default=None, description="Technology stack")
    tools: Optional[List[str]] = Field(default=None, description="Tool identifiers")
    protocol_id: Optional[str] = Field(default=None, description="Protocol ID")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID")
    book_id: Optional[str] = Field(default=None, description="Book ID")
    configuration: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")
    active: Optional[bool] = Field(default=None, description="Agent active status")


class AgentResponseSchema(BaseModel):
    """Schema for agent response data."""
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    model: str = Field(..., description="AI model")
    speciality: str = Field(..., description="Agent speciality")
    persona: str = Field(..., description="Agent persona")
    stack: List[str] = Field(default_factory=list, description="Technology stack")
    tools: List[str] = Field(default_factory=list, description="Tool identifiers")
    active: bool = Field(default=True, description="Agent active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    protocol_id: Optional[str] = Field(default=None, description="Protocol ID")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID")
    book_id: Optional[str] = Field(default=None, description="Book ID")


class AgentListResponseSchema(BaseResponseSchema):
    """Schema for agent list response."""
    agents: List[AgentResponseSchema] = Field(..., description="List of agents")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")


class AgentHealthSchema(BaseModel):
    """Schema for agent health status."""
    agent_id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="Health status")
    last_seen: Optional[datetime] = Field(default=None, description="Last seen timestamp")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Health metrics")


class AgentMetricsSchema(BaseModel):
    """Schema for agent performance metrics."""
    agent_id: str = Field(..., description="Agent ID")
    period: str = Field(..., description="Metrics period")
    tasks_completed: int = Field(default=0, description="Tasks completed")
    average_response_time: float = Field(default=0.0, description="Average response time")
    success_rate: float = Field(default=0.0, description="Success rate")
    error_rate: float = Field(default=0.0, description="Error rate")


class AgentLogSchema(BaseModel):
    """Schema for agent activity logs."""
    id: str = Field(..., description="Log ID")
    agent_id: str = Field(..., description="Agent ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Log context")


class AgentBackupSchema(BaseModel):
    """Schema for agent backup data."""
    agent_id: str = Field(..., description="Agent ID")
    backup_date: datetime = Field(default_factory=datetime.utcnow, description="Backup date")
    version: str = Field(..., description="Agent version")
    data: Dict[str, Any] = Field(..., description="Backup data")
    checksum: str = Field(..., description="Backup checksum")