"""
Tools API Router
Handles tool integration management within projects including API, CLI, and MCP server integrations.

This router provides endpoints for managing external tool integrations that agents
can use to interact with APIs, command-line tools, and MCP servers.
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from datetime import datetime

from ..websocket import get_event_broadcaster, EventType
from ...shared_types.engine_types import EngineError, ToolStatus, ToolType
from ...core.tool_service import ToolService
from ...core.project_service import ProjectService
from ...auth.auth_service import get_current_user


class ToolAuthentication(BaseModel):
    """Tool authentication configuration"""
    type: str = Field(..., description="Authentication type (api_key, oauth_token, basic_auth)")
    token: Optional[str] = Field(None, description="Authentication token")
    username: Optional[str] = Field(None, description="Username for basic auth")
    password: Optional[str] = Field(None, description="Password for basic auth")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers")


class ToolConfig(BaseModel):
    """Tool interface configuration"""
    base_url: Optional[str] = Field(None, description="Base URL for API tools")
    version: Optional[str] = Field(None, description="API version")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Request timeout")
    retries: int = Field(default=3, ge=0, le=10, description="Number of retries")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")


class ToolSummary(BaseModel):
    """Tool summary for list responses"""
    id: str
    name: str
    description: Optional[str]
    tool_type: str
    status: str
    created_at: datetime
    command_count: int


class ToolCreate(BaseModel):
    """Tool creation request model"""
    id: str = Field(..., min_length=1, max_length=50, description="Unique tool identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Human-readable tool name")
    description: Optional[str] = Field(None, max_length=500, description="Tool description")
    tool_type: str = Field(..., description="Tool type (api, cli, mcp_server)")
    interface_config: ToolConfig = Field(..., description="Tool interface configuration")
    authentication: Optional[ToolAuthentication] = Field(None, description="Authentication configuration")
    available_commands: List[str] = Field(default_factory=list, description="Available commands/operations")
    rate_limits: Optional[Dict[str, int]] = Field(None, description="Rate limiting configuration")


class ToolUpdate(BaseModel):
    """Tool update request model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    interface_config: Optional[ToolConfig] = Field(None)
    authentication: Optional[ToolAuthentication] = Field(None)
    available_commands: Optional[List[str]] = Field(None)
    rate_limits: Optional[Dict[str, int]] = Field(None)


class ToolResponse(BaseModel):
    """Tool detailed response model"""
    id: str
    name: str
    description: Optional[str]
    tool_type: str
    interface_config: ToolConfig
    authentication: Optional[ToolAuthentication]
    available_commands: List[str]
    rate_limits: Optional[Dict[str, int]]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    command_count: int


class ToolListResponse(BaseModel):
    """Tool list response model"""
    tools: List[ToolSummary]
    total: int


# Create router instance
router = APIRouter(
    prefix="/projects/{project_id}/tools",
    tags=["tools"],
    responses={
        404: {"description": "Project or tool not found"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    }
)


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    project_id: str = Path(..., description="Project ID"),
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    status: Optional[str] = Query(None, description="Filter by tool status"),
    current_user: dict = Depends(get_current_user),
    tool_service: ToolService = Depends(),
    project_service: ProjectService = Depends()
):
    """List all tools in a project."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get tools for the project
        tools_data = await tool_service.list_tools(
            project_id=project_id,
            tool_type_filter=tool_type,
            status_filter=status
        )
        
        # Convert to response format
        tools = [
            ToolSummary(
                id=tool.id,
                name=tool.name,
                description=tool.description,
                tool_type=tool.tool_type.value,
                status=tool.status.value,
                created_at=tool.created_at,
                command_count=len(tool.available_commands)
            )
            for tool in tools_data
        ]
        
        return ToolListResponse(
            tools=tools,
            total=len(tools)
        )
        
    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ToolResponse)
async def create_tool(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user),
    tool_service: ToolService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster),
    tool_data: ToolCreate = ...
):
    """Create a new tool integration in a project."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if tool ID already exists in project
        existing_tool = await tool_service.get_tool(project_id, tool_data.id)
        if existing_tool:
            raise HTTPException(
                status_code=400,
                detail=f"Tool with ID '{tool_data.id}' already exists in project"
            )
        
        # Validate tool type
        try:
            tool_type = ToolType(tool_data.tool_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tool type: {tool_data.tool_type}"
            )
        
        # Validate tool configuration based on type
        if tool_type == ToolType.API and not tool_data.interface_config.base_url:
            raise HTTPException(
                status_code=400,
                detail="API tools require base_url in interface_config"
            )
        
        # Test tool connection if possible
        if tool_data.authentication:
            connection_test = await tool_service.test_tool_connection(
                tool_type=tool_type,
                interface_config=tool_data.interface_config,
                authentication=tool_data.authentication
            )
            if not connection_test.success:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tool connection test failed: {connection_test.error}"
                )
        
        # Create the tool
        tool = await tool_service.create_tool(
            project_id=project_id,
            id=tool_data.id,
            name=tool_data.name,
            description=tool_data.description,
            tool_type=tool_type,
            interface_config=tool_data.interface_config,
            authentication=tool_data.authentication,
            available_commands=tool_data.available_commands,
            rate_limits=tool_data.rate_limits
        )
        
        # Prepare response (mask sensitive auth data)
        auth_data = tool_data.authentication
        if auth_data and auth_data.token:
            auth_data.token = "***masked***"
        if auth_data and auth_data.password:
            auth_data.password = "***masked***"
        
        response = ToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            tool_type=tool.tool_type.value,
            interface_config=tool_data.interface_config,
            authentication=auth_data,
            available_commands=tool_data.available_commands,
            rate_limits=tool_data.rate_limits,
            status=tool.status.value,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
            command_count=len(tool_data.available_commands)
        )
        
        # Broadcast tool creation event
        await event_broadcaster.broadcast_event(
            event_type=EventType.TOOL_CREATED,
            data={
                "project_id": project_id,
                "tool_id": tool.id,
                "tool_name": tool.name,
                "tool_type": tool.tool_type.value
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


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    project_id: str = Path(..., description="Project ID"),
    tool_id: str = Path(..., description="Tool ID"),
    current_user: dict = Depends(get_current_user),
    tool_service: ToolService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster),
    tool_data: ToolUpdate = ...
):
    """Update an existing tool."""
    try:
        # Verify project and tool exist
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        tool = await tool_service.get_tool(project_id, tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Update the tool
        update_data = tool_data.model_dump(exclude_unset=True)
        updated_tool = await tool_service.update_tool(
            project_id=project_id,
            tool_id=tool_id,
            **update_data
        )
        
        # Prepare response (mask sensitive data)
        auth_data = updated_tool.authentication
        if auth_data and hasattr(auth_data, 'token') and auth_data.token:
            auth_data.token = "***masked***"
        
        response = ToolResponse(
            id=updated_tool.id,
            name=updated_tool.name,
            description=updated_tool.description,
            tool_type=updated_tool.tool_type.value,
            interface_config=updated_tool.interface_config,
            authentication=auth_data,
            available_commands=updated_tool.available_commands,
            rate_limits=updated_tool.rate_limits,
            status=updated_tool.status.value,
            created_at=updated_tool.created_at,
            updated_at=updated_tool.updated_at,
            command_count=len(updated_tool.available_commands)
        )
        
        # Broadcast tool update event
        await event_broadcaster.broadcast_event(
            event_type=EventType.TOOL_UPDATED,
            data={
                "project_id": project_id,
                "tool_id": tool_id,
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


@router.delete("/{tool_id}")
async def delete_tool(
    project_id: str = Path(..., description="Project ID"),
    tool_id: str = Path(..., description="Tool ID"),
    current_user: dict = Depends(get_current_user),
    tool_service: ToolService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster = Depends(get_event_broadcaster)
):
    """Delete a tool integration."""
    try:
        # Verify project and tool exist
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        tool = await tool_service.get_tool(project_id, tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Check if tool is being used by agents
        if await tool_service.is_tool_in_use(project_id, tool_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete tool that is being used by agents"
            )
        
        # Delete the tool
        await tool_service.delete_tool(project_id, tool_id)
        
        # Broadcast tool deletion event
        await event_broadcaster.broadcast_event(
            event_type=EventType.TOOL_DELETED,
            data={
                "project_id": project_id,
                "tool_id": tool_id,
                "tool_name": tool.name
            },
            user_id=current_user["id"]
        )
        
        return {"success": True, "message": "Tool deleted successfully"}
        
    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for tools
@router.get("/health")
async def tools_health():
    """Health check endpoint for tools service"""
    return {
        "service": "tools",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
