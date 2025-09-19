# Workflow Schemas for API
# This module contains Pydantic schemas for workflow-related API operations

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID

from .base_schemas import BaseResponseSchema
from .enums import WorkflowStatus, VertexType, EdgeType


class WorkflowVertexSchema(BaseModel):
    """Schema for workflow vertex."""
    vertex_id: str = Field(..., description="Vertex ID")
    agent_id: str = Field(..., description="Agent ID")
    vertex_type: VertexType = Field(..., description="Vertex type")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Vertex configuration")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="Input schema")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="Output schema")


class WorkflowEdgeSchema(BaseModel):
    """Schema for workflow edge."""
    source_vertex_id: str = Field(..., description="Source vertex ID")
    target_vertex_id: str = Field(..., description="Target vertex ID")
    edge_type: EdgeType = Field(..., description="Edge type")
    condition: Dict[str, Any] = Field(default_factory=dict, description="Edge condition")
    weight: float = Field(default=1.0, description="Edge weight")


class WorkflowExecutionSchema(BaseModel):
    """Schema for workflow execution."""
    workflow_id: str = Field(..., description="Workflow ID")
    execution_id: str = Field(..., description="Execution ID")
    status: WorkflowStatus = Field(..., description="Execution status")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Start time")


class ExecutionLogSchema(BaseModel):
    """Schema for execution log."""
    execution_id: str = Field(..., description="Execution ID")
    vertex_id: str = Field(..., description="Vertex ID")
    log_level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Log metadata")


class WorkflowCreateSchema(BaseModel):
    """Schema for creating a new workflow."""
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    workflow_type: str = Field(..., description="Workflow type")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Workflow configuration")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")


class WorkflowUpdateSchema(BaseModel):
    """Schema for updating an existing workflow."""
    name: Optional[str] = Field(default=None, description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    configuration: Optional[Dict[str, Any]] = Field(default=None, description="Workflow configuration")
    tags: Optional[List[str]] = Field(default=None, description="Workflow tags")
    active: Optional[bool] = Field(default=None, description="Workflow active status")


class WorkflowResponseSchema(BaseModel):
    """Schema for workflow response data."""
    id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    workflow_type: str = Field(..., description="Workflow type")
    active: bool = Field(default=True, description="Workflow active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")