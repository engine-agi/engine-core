"""
Tools API Router
Handles tool integration management within projects including API, CLI, and MCP server integrations.

This router provides endpoints for managing external tool integrations that agents
can use to interact with APIs, command-line tools, and MCP servers.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_user
from src.api.websocket import EventType, get_event_broadcaster
from src.core.project_service import ProjectService
from src.engine_core.engine_types import EngineError, ToolType
from src.services.tool_service import ToolService


class ToolAuthentication(BaseModel):
    """Tool authentication configuration"""

    type: str = Field(
        ..., description="Authentication type (api_key, oauth_token, basic_auth)"
    )
    token: Optional[str] = Field(None, description="Authentication token")
    username: Optional[str] = Field(None, description="Username for basic auth")
    password: Optional[str] = Field(None, description="Password for basic auth")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers")


class ToolConfig(BaseModel):
    """Tool interface configuration"""

    base_url: Optional[str] = Field(None, description="Base URL for API tools")
    version: Optional[str] = Field(None, description="API version")
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Request timeout"
    )
    retries: int = Field(default=3, ge=0, le=10, description="Number of retries")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Additional parameters"
    )


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

    id: str = Field(
        ..., min_length=1, max_length=50, description="Unique tool identifier"
    )
    name: str = Field(
        ..., min_length=1, max_length=100, description="Human-readable tool name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Tool description"
    )
    tool_type: str = Field(..., description="Tool type (api, cli, mcp_server)")
    interface_config: ToolConfig = Field(
        ..., description="Tool interface configuration"
    )
    authentication: Optional[ToolAuthentication] = Field(
        None, description="Authentication configuration"
    )
    available_commands: List[str] = Field(
        default_factory=list, description="Available commands/operations"
    )
    rate_limits: Optional[Dict[str, int]] = Field(
        None, description="Rate limiting configuration"
    )


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
    },
)


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    project_id: str = Path(..., description="Project ID"),
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    status: Optional[str] = Query(None, description="Filter by tool status"),
    current_user: dict = Depends(get_current_user),
    tool_service: ToolService = Depends(),
    project_service: ProjectService = Depends(),
):
    """List all tools in a project."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get tools for the project
        from src.services.tool_service import ToolSearchCriteria

        criteria = ToolSearchCriteria()
        tools_data = await tool_service.search_tools(criteria)

        # Convert to response format
        tools = []
        for tool in tools_data:
            tools.append(
                ToolSummary(
                    id=str(tool.id),
                    name=getattr(tool, "name", "Unknown"),
                    description=getattr(tool, "description", None),
                    tool_type=getattr(tool, "tool_type", "unknown"),
                    status=getattr(tool, "status", "unknown"),
                    created_at=getattr(tool, "created_at", datetime.utcnow()),
                    command_count=0,
                )
            )

        return ToolListResponse(tools=tools, total=len(tools))

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ToolResponse)
async def create_tool(
    tool_data: ToolCreate,
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user),
    tool_service: ToolService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster=Depends(get_event_broadcaster),
):
    """Create a new tool integration in a project."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if tool ID already exists
        try:
            existing_tool = await tool_service.get_tool(tool_data.id)
            if existing_tool:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tool with ID '{tool_data.id}' already exists",
                )
        except:
            pass  # Tool doesn't exist, which is fine

        # Create the tool (mock implementation for now)
        tool = type(
            "MockTool",
            (),
            {
                "id": tool_data.id,
                "name": tool_data.name,
                "description": tool_data.description,
                "tool_type": tool_data.tool_type,
                "created_at": datetime.utcnow(),
                "updated_at": None,
            },
        )()

        # Prepare response
        response = ToolResponse(
            id=str(getattr(tool, "id", tool_data.id)),
            name=getattr(tool, "name", tool_data.name),
            description=getattr(tool, "description", tool_data.description),
            tool_type=getattr(tool, "tool_type", tool_data.tool_type),
            interface_config=tool_data.interface_config,
            authentication=tool_data.authentication,
            available_commands=tool_data.available_commands,
            rate_limits=tool_data.rate_limits,
            status="active",
            created_at=datetime.utcnow(),
            updated_at=None,
            command_count=len(tool_data.available_commands),
        )

        # Broadcast tool creation event
        await event_broadcaster.broadcast_event(
            event_type=EventType.TOOL_STATUS_CHANGED,
            data={
                "project_id": project_id,
                "tool_id": str(getattr(tool, "id", tool_data.id)),
                "tool_name": tool_data.name,
                "action": "created",
            },
            user_id=current_user["id"],
        )

        return response

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
        "timestamp": datetime.utcnow().isoformat(),
    }
