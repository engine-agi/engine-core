"""
Agents API Router
Handles agent lifecycle management within projects including CRUD operations
and task execution.

This router provides endpoints for managing agents within the context of
specific projects.
Agents are AI-powered entities configured with specific models, tools, and capabilities.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_user
from src.api.websocket import EventType, get_event_broadcaster
from src.core.project_service import ProjectService
from src.engine_core.engine_types import EngineError
from src.services.agent_service import (
    AgentCreateRequest,
    AgentService,
    AgentUpdateRequest,
)


class AgentSummary(BaseModel):
    """Agent summary for list responses"""

    id: str
    name: Optional[str] = None
    model: str
    speciality: Optional[str] = None
    stack: List[str] = Field(default_factory=list)
    status: str
    created_at: datetime


class AgentCreate(BaseModel):
    """Agent creation request model"""

    id: str = Field(
        ..., min_length=1, max_length=50, description="Unique agent identifier"
    )
    name: Optional[str] = Field(
        None, max_length=100, description="Human-readable agent name"
    )
    model: str = Field(..., description="AI model to use for this agent")
    speciality: Optional[str] = Field(
        None, max_length=200, description="Agent's area of expertise"
    )
    persona: Optional[str] = Field(
        None, max_length=500, description="Agent's personality and behavior"
    )
    stack: List[str] = Field(
        default_factory=list, description="Technology stack expertise"
    )
    tools: List[str] = Field(
        default_factory=list, description="Available tools and integrations"
    )
    protocol_id: Optional[str] = Field(
        None, description="Protocol for behavior patterns"
    )
    workflow_id: Optional[str] = Field(None, description="Associated workflow")
    book_id: Optional[str] = Field(None, description="Knowledge base reference")


class AgentUpdate(BaseModel):
    """Agent update request model"""

    name: Optional[str] = Field(
        None, max_length=100, description="Human-readable agent name"
    )
    model: Optional[str] = Field(None, description="AI model to use for this agent")
    speciality: Optional[str] = Field(
        None, max_length=200, description="Agent's area of expertise"
    )
    persona: Optional[str] = Field(
        None, max_length=500, description="Agent's personality and behavior"
    )
    stack: Optional[List[str]] = Field(None, description="Technology stack expertise")
    tools: Optional[List[str]] = Field(
        None, description="Available tools and integrations"
    )
    protocol_id: Optional[str] = Field(
        None, description="Protocol for behavior patterns"
    )
    workflow_id: Optional[str] = Field(None, description="Associated workflow")
    book_id: Optional[str] = Field(None, description="Knowledge base reference")


class AgentResponse(BaseModel):
    """Agent detailed response model"""

    id: str
    name: Optional[str]
    model: str
    speciality: Optional[str]
    persona: Optional[str]
    stack: List[str]
    tools: List[str]
    protocol_id: Optional[str]
    workflow_id: Optional[str]
    book_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class AgentListResponse(BaseModel):
    """Agent list response model"""

    agents: List[AgentSummary]
    total: int


class TaskExecution(BaseModel):
    """Task execution request model"""

    task: str = Field(
        ..., min_length=1, max_length=1000, description="Task description"
    )
    context: Optional[str] = Field(
        None, max_length=2000, description="Additional context for the task"
    )
    timeout_seconds: int = Field(
        default=300, ge=30, le=3600, description="Task timeout in seconds"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Additional parameters"
    )


class ExecutionResponse(BaseModel):
    """Task execution response model"""

    execution_id: str
    status: str
    started_at: datetime
    estimated_completion: Optional[datetime] = None


# Create router instance
router = APIRouter(
    prefix="/projects/{project_id}/agents",
    tags=["agents"],
    responses={
        404: {"description": "Project or agent not found"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    },
)


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    project_id: str = Path(..., description="Project ID"),
    status: Optional[str] = Query(None, description="Filter by agent status"),
    model: Optional[str] = Query(None, description="Filter by AI model"),
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(),
    project_service: ProjectService = Depends(),
):
    """
    List all agents in a project.

    Returns all agents associated with the specified project. Supports
    filtering by status and AI model.

    Path Parameters:
    - project_id: The ID of the project

    Query Parameters:
    - status: Filter agents by status(optional)
    - model: Filter agents by AI model(optional)
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get agents for the project
        agents_data = await agent_service.list_agents(
            project_id=project_id, skip=0, limit=100
        )

        # Convert to response format
        agents = [
            AgentSummary(
                id=agent["id"],
                name=agent.get("name"),
                model=agent["model"],
                speciality=agent.get("specialty"),
                # Note: using "specialty" not "speciality"
                stack=agent.get("stack", []),
                status=agent.get("status", "unknown"),
                created_at=datetime.fromisoformat(agent["created_at"])
                if isinstance(agent.get("created_at"), str)
                else agent.get("created_at", datetime.utcnow()),
            )
            for agent in agents_data
        ]

        return AgentListResponse(agents=agents, total=len(agents))

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=AgentResponse)
async def create_agent(
    project_id: str = Path(..., description="Project ID"),
    agent_data: AgentCreate = Body(...),
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster: Any = Depends(get_event_broadcaster),
):
    """
    Create a new agent in a project.

    Creates a new AI agent with the specified configuration. The agent
    will be associated with the project and can be used for task execution.

    Path Parameters:
    - project_id: The ID of the project

    Body Parameters:
    - id: Unique agent identifier(required)
    - name: Human - readable name(optional)
    - model: AI model to use(required)
    - speciality: Area of expertise(optional)
    - persona: Personality description(optional)
    - stack: Technology stack list(optional)
    - tools: Available tools list(optional)
    - protocol_id: Behavior protocol(optional)
    - workflow_id: Associated workflow(optional)
    - book_id: Knowledge base(optional)
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if agent ID already exists in project
        try:
            existing_agent = await agent_service.get_agent(agent_data.id)
            if existing_agent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent with ID '{agent_data.id}' already exists in project",
                )
        except Exception:
            # Agent doesn't exist, which is fine for creation
            pass

        # Validate AI model is allowed in project
        if agent_data.model not in project.get("allowed_models", []):
            raise HTTPException(
                status_code=400,
                detail=f"Model '{agent_data.model}' not allowed in this project",
            )

        # Check agent limit (simplified for now)
        # TODO: Implement proper agent counting
        # current_agent_count = await agent_service.count_agents(project_id)
        # max_agents = project.get("max_agents", 50)
        # if current_agent_count >= max_agents:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Project has reached maximum agent limit of {max_agents}"
        #     )

        # Create the agent
        create_request = AgentCreateRequest(
            id=agent_data.id,
            name=agent_data.name,
            model=agent_data.model,
            specialty=agent_data.speciality,  # Note: using "specialty" not "speciality"
            persona=agent_data.persona,
            stack=agent_data.stack,
            tools=agent_data.tools,
            protocol_id=agent_data.protocol_id,
            workflow_id=agent_data.workflow_id,
            book_id=agent_data.book_id,
            project_id=project_id,
            created_by=current_user["id"],
        )

        agent = await agent_service.create_agent(create_request)

        # Prepare response
        response = AgentResponse(
            id=agent["id"],
            name=agent.get("name"),
            model=agent["model"],
            speciality=agent.get("specialty"),
            # Note: using "specialty" not "speciality"
            persona=agent.get("persona"),
            stack=agent.get("stack", []),
            tools=agent.get("tools", []),
            protocol_id=agent.get("protocol_id"),
            workflow_id=agent.get("workflow_id"),
            book_id=agent.get("book_id"),
            status=agent.get("status", "unknown"),
            created_at=datetime.fromisoformat(agent["created_at"])
            if isinstance(agent.get("created_at"), str)
            else agent.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(agent["updated_at"])
            if agent.get("updated_at") and isinstance(agent.get("updated_at"), str)
            else None,
        )

        # Broadcast agent creation event
        await event_broadcaster.broadcast_event(
            event_type=EventType.AGENT_CREATED,
            data={
                "project_id": project_id,
                "agent_id": agent["id"],
                "agent_name": agent.get("name"),
                "model": agent["model"],
            },
            user_id=current_user["id"],
        )

        return response

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    project_id: str = Path(..., description="Project ID"),
    agent_id: str = Path(..., description="Agent ID"),
    agent_data: AgentUpdate = Body(...),
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster: Any = Depends(get_event_broadcaster),
):
    """
    Update an existing agent.

    Updates the configuration of an existing agent. Only provided fields
    will be updated, others remain unchanged.

    Path Parameters:
    - project_id: The ID of the project
    - agent_id: The ID of the agent to update
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify agent exists
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Validate model if being changed
        if agent_data.model and agent_data.model not in project.get(
            "allowed_models", []
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Model '{agent_data.model}' not allowed in this project",
            )

        # Update the agent
        update_request = AgentUpdateRequest(
            name=agent_data.name,
            specialty=agent_data.speciality,  # Note: using "specialty" not "speciality"
            persona=agent_data.persona,
            tools=agent_data.tools,
            protocol_id=agent_data.protocol_id,
            workflow_id=agent_data.workflow_id,
            book_id=agent_data.book_id,
        )

        updated_agent = await agent_service.update_agent(
            agent_id=agent_id, request=update_request, updated_by=current_user["id"]
        )

        # Prepare response
        response = AgentResponse(
            id=updated_agent["id"],
            name=updated_agent.get("name"),
            model=updated_agent["model"],
            # Note: using "specialty" not "speciality"
            speciality=updated_agent.get("specialty"),
            persona=updated_agent.get("persona"),
            stack=updated_agent.get("stack", []),
            tools=updated_agent.get("tools", []),
            protocol_id=updated_agent.get("protocol_id"),
            workflow_id=updated_agent.get("workflow_id"),
            book_id=updated_agent.get("book_id"),
            status=updated_agent.get("status", "unknown"),
            created_at=datetime.fromisoformat(updated_agent["created_at"])
            if isinstance(updated_agent.get("created_at"), str)
            else updated_agent.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(updated_agent["updated_at"])
            if updated_agent.get("updated_at")
            and isinstance(updated_agent.get("updated_at"), str)
            else None,
        )

        # Broadcast agent update event
        await event_broadcaster.broadcast_event(
            event_type=EventType.AGENT_UPDATED,
            data={
                "project_id": project_id,
                "agent_id": agent_id,
                "changes": agent_data.model_dump(exclude_unset=True),
            },
            user_id=current_user["id"],
        )

        return response

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{agent_id}")
async def delete_agent(
    project_id: str = Path(..., description="Project ID"),
    agent_id: str = Path(..., description="Agent ID"),
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster: Any = Depends(get_event_broadcaster),
):
    """
    Delete an agent.

    Permanently removes an agent from the project. This action cannot be undone.

    Path Parameters:
    - project_id: The ID of the project
    - agent_id: The ID of the agent to delete
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify agent exists
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Check if agent is currently executing tasks (simplified for now)
        # TODO: Implement proper execution tracking
        # if await agent_service.has_running_executions(project_id, agent_id):
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Cannot delete agent with running executions"
        #     )

        # Delete the agent
        await agent_service.delete_agent(agent_id)

        # Broadcast agent deletion event
        await event_broadcaster.broadcast_event(
            event_type=EventType.AGENT_DELETED,
            data={
                "project_id": project_id,
                "agent_id": agent_id,
                "agent_name": agent.get("name"),
            },
            user_id=current_user["id"],
        )

        return {"success": True, "message": "Agent deleted successfully"}

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{agent_id}/execute", response_model=ExecutionResponse)
async def execute_task(
    project_id: str = Path(..., description="Project ID"),
    agent_id: str = Path(..., description="Agent ID"),
    execution_data: TaskExecution = Body(...),
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster: Any = Depends(get_event_broadcaster),
):
    """
    Execute a task with an agent.

    Submits a task for execution by the specified agent. The execution
    runs asynchronously and can be monitored via WebSocket events.

    Path Parameters:
    - project_id: The ID of the project
    - agent_id: The ID of the agent to execute the task

    Body Parameters:
    - task: Task description(required, 1 - 1000 characters)
    - context: Additional context(optional, max 2000 characters)
    - timeout_seconds: Task timeout(default: 300, range: 30 - 3600)
    - parameters: Additional parameters(optional)
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify agent exists and is active
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if agent.get("status") != "active":
            raise HTTPException(
                status_code=400,
                detail=f"Agent is not active (status: {agent.get('status', 'unknown')})",
            )

        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        # Start task execution (simplified for now)
        # TODO: Implement proper task execution
        execution = {
            "id": execution_id,
            "status": "pending",
            "started_at": datetime.utcnow(),
            "estimated_completion": datetime.utcnow()
            + timedelta(seconds=execution_data.timeout_seconds),
        }

        # Prepare response
        response = ExecutionResponse(
            execution_id=execution["id"],
            status=execution["status"],
            started_at=execution["started_at"],
            estimated_completion=execution["estimated_completion"],
        )

        # Broadcast execution started event
        await event_broadcaster.broadcast_event(
            event_type=EventType.AGENT_EXECUTION_STARTED,
            data={
                "project_id": project_id,
                "agent_id": agent_id,
                "execution_id": execution["id"],
                "task": execution_data.task,
            },
            user_id=current_user["id"],
        )

        return response

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for agents
@router.get("/health")
async def agents_health():
    """Health check endpoint for agents service"""
    return {
        "service": "agents",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }
