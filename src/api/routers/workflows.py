"""
Workflows API Router
Handles workflow management and execution within projects based on Pregel computational model.

This router provides endpoints for managing workflows which define directed acyclic graphs
of tasks to be executed by agents. Workflows use the Pregel model for distributed computation.
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from ..websocket import get_event_broadcaster, EventType
from ...shared_types.engine_types import EngineError, WorkflowStatus, ExecutionMode
from ...core.workflow_service import WorkflowService
from ...core.project_service import ProjectService
from ...core.agent_service import AgentService
from ...auth.auth_service import get_current_user


class WorkflowVertex(BaseModel):
    """Workflow vertex (node) definition"""
    id: str = Field(..., description="Unique vertex identifier")
    name: str = Field(..., description="Human-readable vertex name")
    agent_id: str = Field(..., description="Agent responsible for this vertex")
    task_description: str = Field(..., description="Description of task to perform")
    dependencies: List[str] = Field(default_factory=list, description="List of prerequisite vertex IDs")
    priority: int = Field(default=1, ge=1, description="Execution priority")
    timeout_seconds: int = Field(default=300, ge=30, le=3600, description="Task timeout")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")


class WorkflowEdge(BaseModel):
    """Workflow edge (connection) definition"""
    from_vertex_id: str = Field(..., description="Source vertex ID")
    to_vertex_id: str = Field(..., description="Target vertex ID")
    condition: Optional[str] = Field(None, description="Condition for edge traversal")
    data_mapping: Optional[Dict[str, str]] = Field(None, description="Data flow mapping")


class WorkflowSummary(BaseModel):
    """Workflow summary for list responses"""
    id: str
    name: str
    execution_mode: str
    vertex_count: int
    edge_count: int
    status: str
    created_at: datetime


class WorkflowCreate(BaseModel):
    """Workflow creation request model"""
    id: str = Field(..., min_length=1, max_length=50, description="Unique workflow identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable workflow name")
    execution_mode: str = Field("mixed", description="Execution mode (sequential, parallel, mixed)")
    vertices: List[WorkflowVertex] = Field(..., min_items=1, description="List of workflow vertices")
    edges: List[WorkflowEdge] = Field(default_factory=list, description="List of workflow edges")
    description: Optional[str] = Field(None, max_length=500, description="Workflow description")


class WorkflowUpdate(BaseModel):
    """Workflow update request model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    execution_mode: Optional[str] = Field(None)
    vertices: Optional[List[WorkflowVertex]] = Field(None)
    edges: Optional[List[WorkflowEdge]] = Field(None)
    description: Optional[str] = Field(None, max_length=500)


class WorkflowResponse(BaseModel):
    """Workflow detailed response model"""
    id: str
    name: str
    execution_mode: str
    vertices: List[WorkflowVertex]
    edges: List[WorkflowEdge]
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    vertex_count: int
    edge_count: int


class WorkflowListResponse(BaseModel):
    """Workflow list response model"""
    workflows: List[WorkflowSummary]
    total: int


class WorkflowExecution(BaseModel):
    """Workflow execution request model"""
    input_data: Dict[str, Any] = Field(..., description="Input data for workflow execution")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional execution parameters")
    timeout_seconds: Optional[int] = Field(None, ge=60, le=7200, description="Total workflow timeout")


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response model"""
    execution_id: str
    workflow_id: str
    status: str
    current_superstep: int
    active_vertices: List[str]
    started_at: datetime
    estimated_completion: Optional[datetime] = None


# Create router instance
router = APIRouter(
    prefix="/projects/{project_id}/workflows",
    tags=["workflows"],
    responses={
        404: {"description": "Project or workflow not found"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    }
)


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    project_id: str = Path(..., description="Project ID"),
    status: Optional[str] = Query(None, description="Filter by workflow status"),
    execution_mode: Optional[str] = Query(None, description="Filter by execution mode"),
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(),
    project_service: ProjectService = Depends()
):
    """
    List all workflows in a project.
    
    Returns all workflows associated with the specified project. Supports
    filtering by status and execution mode.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get workflows for the project
        workflows_data = await workflow_service.list_workflows(
            project_id=project_id,
            status_filter=status,
            execution_mode_filter=execution_mode
        )
        
        # Convert to response format
        workflows = [
            WorkflowSummary(
                id=workflow.id,
                name=workflow.name,
                execution_mode=workflow.execution_mode.value,
                vertex_count=len(workflow.vertices),
                edge_count=len(workflow.edges),
                status=workflow.status.value,
                created_at=workflow.created_at
            )
            for workflow in workflows_data
        ]
        
        return WorkflowListResponse(
            workflows=workflows,
            total=len(workflows)
        )
        
    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(),
    project_service: ProjectService = Depends(),
    agent_service: AgentService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster),
    workflow_data: WorkflowCreate = ...
):
    """
    Create a new workflow in a project.
    
    Creates a new workflow with the specified vertices and edges. All agents
    referenced in vertices must exist in the project.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if workflow ID already exists in project
        existing_workflow = await workflow_service.get_workflow(project_id, workflow_data.id)
        if existing_workflow:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow with ID '{workflow_data.id}' already exists in project"
            )
        
        # Validate execution mode
        try:
            execution_mode = ExecutionMode(workflow_data.execution_mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid execution mode: {workflow_data.execution_mode}"
            )
        
        # Verify all agents exist in the project
        agent_ids = {vertex.agent_id for vertex in workflow_data.vertices}
        for agent_id in agent_ids:
            agent = await agent_service.get_agent(project_id, agent_id)
            if not agent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent '{agent_id}' not found in project"
                )
        
        # Validate vertex dependencies
        vertex_ids = {vertex.id for vertex in workflow_data.vertices}
        for vertex in workflow_data.vertices:
            for dep_id in vertex.dependencies:
                if dep_id not in vertex_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Dependency '{dep_id}' not found in vertices"
                    )
        
        # Validate edges
        for edge in workflow_data.edges:
            if edge.from_vertex_id not in vertex_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Edge source vertex '{edge.from_vertex_id}' not found"
                )
            if edge.to_vertex_id not in vertex_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Edge target vertex '{edge.to_vertex_id}' not found"
                )
        
        # Check for cycles in the graph
        if await workflow_service.has_cycles(workflow_data.vertices, workflow_data.edges):
            raise HTTPException(
                status_code=400,
                detail="Workflow contains cycles - DAG structure required"
            )
        
        # Create the workflow
        workflow = await workflow_service.create_workflow(
            project_id=project_id,
            id=workflow_data.id,
            name=workflow_data.name,
            execution_mode=execution_mode,
            vertices=workflow_data.vertices,
            edges=workflow_data.edges,
            description=workflow_data.description
        )
        
        # Prepare response
        response = WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            execution_mode=workflow.execution_mode.value,
            vertices=workflow_data.vertices,
            edges=workflow_data.edges,
            description=workflow.description,
            status=workflow.status.value,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            vertex_count=len(workflow_data.vertices),
            edge_count=len(workflow_data.edges)
        )
        
        # Broadcast workflow creation event
        await event_broadcaster.broadcast_event(
            event_type=EventType.WORKFLOW_CREATED,
            data={
                "project_id": project_id,
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "vertex_count": len(workflow_data.vertices),
                "edge_count": len(workflow_data.edges)
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


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    project_id: str = Path(..., description="Project ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(),
    project_service: ProjectService = Depends(),
    agent_service: AgentService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster),
    workflow_data: WorkflowUpdate = ...
):
    """
    Update an existing workflow.
    
    Updates the configuration of an existing workflow. Only provided fields
    will be updated, others remain unchanged.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Verify workflow exists
        workflow = await workflow_service.get_workflow(project_id, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Check if workflow is currently executing
        if await workflow_service.has_running_executions(project_id, workflow_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot update workflow with running executions"
            )
        
        # Validate updates (similar to create, but only for changed fields)
        update_data = workflow_data.model_dump(exclude_unset=True)
        
        # Validate execution mode if changed
        if "execution_mode" in update_data:
            try:
                ExecutionMode(update_data["execution_mode"])
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid execution mode: {update_data['execution_mode']}"
                )
        
        # Validate agents if vertices changed
        if "vertices" in update_data:
            agent_ids = {vertex.agent_id for vertex in update_data["vertices"]}
            for agent_id in agent_ids:
                agent = await agent_service.get_agent(project_id, agent_id)
                if not agent:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent '{agent_id}' not found in project"
                    )
        
        # Update the workflow
        updated_workflow = await workflow_service.update_workflow(
            project_id=project_id,
            workflow_id=workflow_id,
            **update_data
        )
        
        # Prepare response
        response = WorkflowResponse(
            id=updated_workflow.id,
            name=updated_workflow.name,
            execution_mode=updated_workflow.execution_mode.value,
            vertices=updated_workflow.vertices,
            edges=updated_workflow.edges,
            description=updated_workflow.description,
            status=updated_workflow.status.value,
            created_at=updated_workflow.created_at,
            updated_at=updated_workflow.updated_at,
            vertex_count=len(updated_workflow.vertices),
            edge_count=len(updated_workflow.edges)
        )
        
        # Broadcast workflow update event
        await event_broadcaster.broadcast_event(
            event_type=EventType.WORKFLOW_UPDATED,
            data={
                "project_id": project_id,
                "workflow_id": workflow_id,
                "changes": update_data
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


@router.delete("/{workflow_id}")
async def delete_workflow(
    project_id: str = Path(..., description="Project ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster)
):
    """
    Delete a workflow.
    
    Permanently removes a workflow from the project. This action cannot be undone.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Verify workflow exists
        workflow = await workflow_service.get_workflow(project_id, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Check if workflow is currently executing
        if await workflow_service.has_running_executions(project_id, workflow_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete workflow with running executions"
            )
        
        # Delete the workflow
        await workflow_service.delete_workflow(project_id, workflow_id)
        
        # Broadcast workflow deletion event
        await event_broadcaster.broadcast_event(
            event_type=EventType.WORKFLOW_DELETED,
            data={
                "project_id": project_id,
                "workflow_id": workflow_id,
                "workflow_name": workflow.name
            },
            user_id=current_user["id"]
        )
        
        return {"success": True, "message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    project_id: str = Path(..., description="Project ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    current_user: dict = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster),
    execution_data: WorkflowExecution = ...
):
    """
    Execute a workflow.
    
    Submits a workflow for execution using the Pregel computational model.
    The workflow will process vertices in supersteps according to the DAG structure.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Verify workflow exists and is active
        workflow = await workflow_service.get_workflow(project_id, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != WorkflowStatus.READY:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow is not active (status: {workflow.status.value})"
            )
        
        # Generate execution ID
        execution_id = f"wf_exec_{uuid.uuid4().hex[:12]}"
        
        # Start workflow execution
        execution = await workflow_service.execute_workflow(
            project_id=project_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            input_data=execution_data.input_data,
            parameters=execution_data.parameters or {},
            timeout_seconds=execution_data.timeout_seconds
        )
        
        # Prepare response
        response = WorkflowExecutionResponse(
            execution_id=execution.id,
            workflow_id=workflow_id,
            status=execution.status.value,
            current_superstep=execution.current_superstep,
            active_vertices=execution.active_vertices,
            started_at=execution.started_at,
            estimated_completion=execution.estimated_completion
        )
        
        # Broadcast execution started event
        await event_broadcaster.broadcast_event(
            event_type=EventType.WORKFLOW_EXECUTION_STARTED,
            data={
                "project_id": project_id,
                "workflow_id": workflow_id,
                "execution_id": execution.id,
                "vertex_count": len(workflow.vertices),
                "input_data": execution_data.input_data
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


# Health check endpoint for workflows
@router.get("/health")
async def workflows_health():
    """Health check endpoint for workflows service"""
    return {
        "service": "workflows",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
