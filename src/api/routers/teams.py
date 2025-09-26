"""
from pathlib import Path
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any
Teams API Router
Handles team management and coordination within projects including team creation and project execution.

This router provides endpoints for managing teams of agents within projects. Teams enable
coordinated execution of complex projects through different coordination strategies.
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field


class TeamSummary(BaseModel):
    """Team summary for list responses"""
    id: str
    name: str
    agent_count: int
    status: str
    coordination_strategy: str
    created_at: datetime


class TeamCreate(BaseModel):
    """Team creation request model"""
    id: str = Field(..., min_length=1, max_length=50,
                    description="Unique team identifier")
    name: str = Field(..., min_length=1, max_length=100,
                      description="Human-readable team name")
    agent_ids: List[str] = Field()
    lead_agent_id: Optional[str] = Field(
        None, description="Lead agent ID (must be in agent_ids)")
    coordination_strategy: str = Field(
        "hierarchical", description="Team coordination strategy")
    workflow_id: Optional[str] = Field(None, description="Associated workflow")
    protocol_id: Optional[str] = Field(None, description="Team behavior protocol")


class TeamResponse(BaseModel):
    """Team detailed response model"""
    id: str
    name: str
    agent_ids: List[str]
    lead_agent_id: Optional[str]
    coordination_strategy: str
    workflow_id: Optional[str]
    protocol_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    agent_count: int


class TeamListResponse(BaseModel):
    """Team list response model"""
    teams: List[TeamSummary]
    total: int


class ProjectExecution(BaseModel):
    """Project execution request model"""
    project_description: str = Field(...,
                                     min_length=10,
                                     max_length=2000,
                                     description="Project description")
    requirements: List[str] = Field()
    timeline: Optional[str] = Field(
        None, max_length=100, description="Project timeline")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Additional execution parameters")
    priority: str = Field(
        "normal",
        description="Execution priority (low, normal, high)")


class ProjectExecutionResponse(BaseModel):
    """Project execution response model"""
    execution_id: str
    team_id: str
    status: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    assigned_agents: List[str]


# Create router instance
router = APIRouter(
    prefix="/projects/{project_id}/teams",
    tags=["teams"],
    responses={
        404: {"description": "Project or team not found"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    }
)


@router.get("/", response_model=TeamListResponse)
async def list_teams(project_id: str = Path(...,
                                            description="Project ID"),
                     status: Optional[str] = Query(None,
                                                   description="Filter by team status"),
                     coordination_strategy: Optional[str] = Query(None,
                                                                  description="Filter by coordination strategy"),
                     current_user: dict = Depends(get_current_user),
                     team_service: TeamService = Depends(),
                     project_service: ProjectService = Depends()):
    """
    List all teams in a project.

    Returns all teams associated with the specified project. Supports
    filtering by status and coordination strategy.

    Path Parameters:
    - project_id: The ID of the project

    Query Parameters:
    - status: Filter teams by status (optional)
    - coordination_strategy: Filter by coordination strategy (optional)
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get teams for the project
        teams_data = await team_service.list_teams(
            project_id=project_id
        )

        # Convert to response format
        teams = [
            TeamSummary(
                id=team['id'],
                name=team['name'],
                agent_count=len(team.get('members', [])),
                status=team['status'],
                coordination_strategy=team['coordination_strategy'],
                created_at=team['created_at']
            )
            for team in teams_data
        ]

        return TeamListResponse(
            teams=teams,
            total=len(teams)
        )

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=TeamResponse)
async def create_team(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user),
    team_service: TeamService = Depends(),
    project_service: ProjectService = Depends(),
    agent_service: AgentService = Depends(),
    event_broadcaster=Depends(get_event_broadcaster),
    team_data: TeamCreate = Body(...)
):
    """
    Create a new team in a project.

    Creates a new team with the specified agents and coordination strategy.
    All agents must exist in the project before they can be added to a team.

    Path Parameters:
    - project_id: The ID of the project

    Body Parameters:
    - id: Unique team identifier (required)
    - name: Human-readable name (required)
    - agent_ids: List of agent IDs (required, minimum 2)
    - lead_agent_id: Lead agent ID (optional, must be in agent_ids)
    - coordination_strategy: Coordination strategy (default: hierarchical)
    - workflow_id: Associated workflow (optional)
    - protocol_id: Team protocol (optional)
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if team ID already exists in project
        existing_team = await team_service.get_team(team_data.id)
        if existing_team:
            raise HTTPException(
                status_code=400,
                detail=f"Team with ID '{team_data.id}' already exists in project"
            )

        # Verify all agents exist in the project
        for agent_id in team_data.agent_ids:
            agent = await agent_service.get_agent(agent_id)
            if not agent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent '{agent_id}' not found in project"
                )

        # Validate lead agent if specified
        if team_data.lead_agent_id:
            if team_data.lead_agent_id not in team_data.agent_ids:
                raise HTTPException(
                    status_code=400,
                    detail="Lead agent must be included in agent_ids list"
                )

        # Validate coordination strategy
        try:
            coordination_strategy = TeamCoordinationStrategy(
                team_data.coordination_strategy)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid coordination strategy: {
                    team_data.coordination_strategy}")

        # Create the team
        request = TeamCreateRequest(
            id=team_data.id,
            name=team_data.name,
            project_id=project_id,
            coordination_strategy=coordination_strategy,
            members=[{"agent_id": agent_id} for agent_id in team_data.agent_ids],
            workflow_id=team_data.workflow_id,
            protocol_id=team_data.protocol_id,
            created_by=current_user["id"]
        )

        team = await team_service.create_team(request)

        # Prepare response
        response = TeamResponse(
            id=team['id'],
            name=team['name'],
            agent_ids=[member['agent_id'] for member in team.get('members', [])],
            lead_agent_id=None,  # TODO: implement lead agent logic
            coordination_strategy=team['coordination_strategy'],
            workflow_id=team.get('workflow_id'),
            protocol_id=team.get('protocol_id'),
            status=team['status'],
            created_at=team['created_at'],
            updated_at=team.get('updated_at'),
            agent_count=len(team.get('members', []))
        )

        # Broadcast team creation event
        await event_broadcaster.broadcast_event(
            event_type=EventType.TEAM_CREATED,
            data={
                "project_id": project_id,
                "team_id": team['id'],
                "team_name": team['name'],
                "agent_ids": [member['agent_id'] for member in team.get('members', [])],
                "coordination_strategy": team['coordination_strategy']
            },
            user_id=current_user["id"]
        )

        return response

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{team_id}/execute", response_model=ProjectExecutionResponse)
async def execute_project(
    project_id: str = Path(..., description="Project ID"),
    team_id: str = Path(..., description="Team ID"),
    current_user: dict = Depends(get_current_user),
    team_service: TeamService = Depends(),
    project_service: ProjectService = Depends(),
    agent_service: AgentService = Depends(),
    event_broadcaster=Depends(get_event_broadcaster),
    execution_data: ProjectExecution = Body(...)
):
    """
    Execute a project with a team.

    Submits a complex project for execution by the specified team. The team
    will coordinate agent activities based on its coordination strategy to
    complete all requirements.

    Path Parameters:
    - project_id: The ID of the project
    - team_id: The ID of the team to execute the project

    Body Parameters:
    - project_description: Detailed project description (required)
    - requirements: List of project requirements (required, minimum 1)
    - timeline: Project timeline (optional)
    - parameters: Additional parameters (optional)
    - priority: Execution priority (default: normal)
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify team exists and is active
        team = await team_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if team['status'] != 'active':
            raise HTTPException(
                status_code=400,
                detail=f"Team is not active (status: {team['status']})"
            )

        # Verify all team agents are still active
        agent_ids = [member['agent_id'] for member in team.get('members', [])]
        for agent_id in agent_ids:
            agent = await agent_service.get_agent(agent_id)
            if not agent or agent.get('status') != 'active':
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent '{agent_id}' is not active or not found"
                )

        # Generate execution ID
        execution_id = f"exec_team_{uuid.uuid4().hex[:12]}"

        # Start project execution
        request = TaskExecutionRequest(
            tasks=[{
                'id': f"task_{uuid.uuid4().hex[:8]}",
                'description': execution_data.project_description,
                'requirements': execution_data.requirements,
                'context': {
                    'project_id': project_id,
                    'user_id': current_user["id"],
                    'timeline': execution_data.timeline,
                    'priority': execution_data.priority
                }
            }],
            context={
                'project_id': project_id,
                'user_id': current_user["id"],
                'session_id': f"session_{uuid.uuid4().hex[:12]}"
            },
            workflow_id=None,
            timeout_seconds=300
        )

        execution = await team_service.execute_tasks(team_id, request)

        # Prepare response
        response = ProjectExecutionResponse(
            execution_id=execution.execution_id,
            team_id=team_id,
            status=execution.status,
            started_at=datetime.utcnow(),  # TODO: get from execution
            estimated_completion=None,  # TODO: calculate based on tasks
            assigned_agents=agent_ids
        )

        # Broadcast execution started event
        await event_broadcaster.broadcast_event(
            event_type=EventType.TEAM_EXECUTION_STARTED,
            data={
                "project_id": project_id,
                "team_id": team_id,
                "execution_id": execution.execution_id,
                "project_description": execution_data.project_description,
                "requirements_count": len(execution_data.requirements),
                "agent_ids": agent_ids
            },
            user_id=current_user["id"]
        )

        return response

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for teams
@router.get("/health")
async def teams_health():
    """Health check endpoint for teams service"""
    return {
        "service": "teams",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
