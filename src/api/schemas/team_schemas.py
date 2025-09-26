# Team Schemas for API
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .base_schemas import BaseResponseSchema
from .enums import RelationshipType, TeamCoordinationStrategy

# This module contains Pydantic schemas for team-related API operations


class TeamMemberSchema(BaseModel):
    """Schema for team member information."""

    agent_id: str = Field(..., description="Agent ID")
    role: str = Field(..., description="Member role")
    hierarchy_level: int = Field(ge=1, le=10, description="Hierarchy level")
    permissions: List[str] = Field(
        default_factory=list, description="Member permissions"
    )
    workload_percentage: float = Field(
        ge=0.0, le=100.0, description="Workload percentage"
    )
    joined_at: datetime = Field(
        default_factory=datetime.utcnow, description="Join date"
    )

    @field_validator("workload_percentage")
    @classmethod
    def validate_workload(cls, v):
        """Validate workload percentage."""
        if v < 0 or v > 100:
            raise ValueError("Workload must be between 0 and 100")
        return v


class CoordinationStrategySchema(BaseModel):
    """Schema for team coordination strategy."""

    strategy_type: TeamCoordinationStrategy = Field(..., description="Strategy type")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Strategy configuration"
    )
    priority: int = Field(default=1, ge=1, le=10, description="Strategy priority")


class TeamHierarchySchema(BaseModel):
    """Schema for team hierarchy relationships."""

    parent_agent_id: str = Field(..., description="Parent agent ID")
    child_agent_id: str = Field(..., description="Child agent ID")
    relationship_type: RelationshipType = Field(..., description="Relationship type")
    hierarchy_level: int = Field(ge=1, le=10, description="Hierarchy level")


class TeamCreateSchema(BaseModel):
    """Schema for creating a new team."""

    name: str = Field(..., min_length=1, max_length=255, description="Team name")
    description: str = Field(
        ..., min_length=1, max_length=1000, description="Team description"
    )
    coordination_strategy: TeamCoordinationStrategy = Field(
        ..., description="Coordination strategy"
    )
    max_members: int = Field(default=10, ge=1, le=50, description="Maximum members")
    access_control: List[str] = Field(
        default_factory=list, description="Access control rules"
    )
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Additional configuration"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate team name."""
        if not v.strip():
            raise ValueError("Team name cannot be empty")
        return v.strip()


class TeamUpdateSchema(BaseModel):
    """Schema for updating an existing team."""

    name: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="Team name"
    )
    description: Optional[str] = Field(
        default=None, min_length=1, max_length=1000, description="Team description"
    )
    coordination_strategy: Optional[TeamCoordinationStrategy] = Field(
        default=None, description="Coordination strategy"
    )
    max_members: Optional[int] = Field(
        default=None, ge=1, le=50, description="Maximum members"
    )
    access_control: Optional[List[str]] = Field(
        default=None, description="Access control rules"
    )
    configuration: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional configuration"
    )
    active: Optional[bool] = Field(default=None, description="Team active status")


class TeamResponseSchema(BaseModel):
    """Schema for team response data."""

    id: str = Field(..., description="Team ID")
    name: str = Field(..., description="Team name")
    description: str = Field(..., description="Team description")
    coordination_strategy: TeamCoordinationStrategy = Field(
        ..., description="Coordination strategy"
    )
    max_members: int = Field(..., description="Maximum members")
    active: bool = Field(default=True, description="Team active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    member_count: int = Field(default=0, description="Current member count")


class TeamListResponseSchema(BaseResponseSchema):
    """Schema for team list response."""

    teams: List[TeamResponseSchema] = Field(..., description="List of teams")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")


class TeamMetricsSchema(BaseModel):
    """Schema for team performance metrics."""

    team_id: str = Field(..., description="Team ID")
    period: str = Field(..., description="Metrics period")
    total_tasks: int = Field(default=0, description="Total tasks")
    completed_tasks: int = Field(default=0, description="Completed tasks")
    average_response_time: float = Field(
        default=0.0, description="Average response time"
    )
    collaboration_score: float = Field(default=0.0, description="Collaboration score")
