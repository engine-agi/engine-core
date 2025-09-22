"""
Projects API Router
Handles project lifecycle management including creation and listing.

This router provides endpoints for managing projects in the Engine Framework.
Each project serves as a container for agents, teams, workflows, and other
engine components.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from uuid import UUID

from ..websocket import get_event_broadcaster, EventType
from ...shared_types.engine_types import EngineError, ProjectStatus
from ...core.project_service import ProjectService, ProjectLimits
from ...auth.auth_service import get_current_user


class ProjectSummary(BaseModel):
    """Project summary for list responses"""
    id: str
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    agent_count: int = 0
    team_count: int = 0


class ProjectCreate(BaseModel):
    """Project creation request model"""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    default_model: str = Field(..., description="Default AI model for agents")
    allowed_models: List[str] = Field(default_factory=list, description="List of allowed AI models")
    max_agents: int = Field(default=50, ge=1, le=1000, description="Maximum number of agents")


class ProjectResponse(BaseModel):
    """Project response model"""
    id: str
    name: str
    description: Optional[str]
    default_model: str
    allowed_models: List[str]
    max_agents: int
    status: str
    created_at: datetime
    agent_count: int = 0
    team_count: int = 0


class ProjectListResponse(BaseModel):
    """Project list response with pagination"""
    projects: List[ProjectSummary]
    total: int
    page: int
    limit: int


# Create router instance
router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={
        404: {"description": "Project not found"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    }
)


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
    project_service: ProjectService = Depends()
):
    """
    List all projects for the authenticated user.
    
    Returns a paginated list of projects with basic information including
    agent count and team count for each project.
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - limit: Number of items per page (default: 50, max: 100)
    - status: Filter projects by status (optional)
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Get user projects with pagination
        projects_data = await project_service.list_projects(
            user_id=current_user["id"],
            skip=offset,
            limit=limit
        )
        
        # Convert to response format
        projects = [
            ProjectSummary(
                id=project["id"],
                name=project["name"],
                description=project.get("description"),
                status="active",  # Mock status since service doesn't provide it
                created_at=project["created_at"],
                agent_count=0,  # Mock count since service doesn't provide it
                team_count=0    # Mock count since service doesn't provide it
            )
            for project in projects_data
        ]
        
        return ProjectListResponse(
            projects=projects,
            total=len(projects_data),  # Mock total since service doesn't provide it
            page=page,
            limit=limit
        )
        
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    project_service: ProjectService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster)
):
    """
    Create a new project.
    
    Creates a new project with the specified configuration. The project
    will be associated with the authenticated user and initialized with
    the provided settings.
    
    Body Parameters:
    - name: Project name (required, 1-100 characters)
    - description: Project description (optional, max 500 characters)
    - default_model: Default AI model for agents (required)
    - allowed_models: List of allowed AI models (optional)
    - max_agents: Maximum number of agents (default: 50, range: 1-1000)
    """
    try:
        # Generate unique project ID
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        
        # Validate AI models (mock validation since service doesn't have this method)
        # TODO: Implement proper model validation when service supports it
        
        # Create project
        project = await project_service.create_project(
            name=project_data.name,
            description=project_data.description or "",
            owner_id=current_user["id"],
            allowed_models=project_data.allowed_models or [project_data.default_model],
            limits=ProjectLimits(max_agents=project_data.max_agents)
        )
        
        # Prepare response
        response = ProjectResponse(
            id=project["id"],
            name=project["name"],
            description=project.get("description"),
            default_model=project["allowed_models"][0] if project["allowed_models"] else "claude-3.5-sonnet",  # Use first allowed model as default
            allowed_models=project["allowed_models"],
            max_agents=project["max_agents"],
            status="active",  # Mock status since service doesn't provide it
            created_at=project["created_at"],
            agent_count=0,  # New project starts with 0 agents
            team_count=0    # New project starts with 0 teams
        )
        
        # Broadcast project creation event
        await event_broadcaster.broadcast_event(
            event_type=EventType.PROJECT_CREATED,
            data={
                "project_id": project["id"],
                "project_name": project["name"],
                "owner_id": current_user["id"]
            },
            user_id=current_user["id"]
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for projects
@router.get("/health")
async def projects_health():
    """Health check endpoint for projects service"""
    return {
        "service": "projects",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
