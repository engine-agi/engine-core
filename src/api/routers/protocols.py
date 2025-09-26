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
Protocols API Router
Handles protocol management within projects including semantic command definitions.

This router provides endpoints for managing behavior protocols that define
semantic commands for agent and team coordination patterns.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field


class ProtocolCommand(BaseModel):
    """Protocol semantic command definition"""
    name: str = Field(..., min_length=1, max_length=50, description="Command name")
    definition: str = Field(..., min_length=1, max_length=500,
                            description="Semantic command definition")
    priority: int = Field(default=1, ge=1, description="Command priority")
    required: bool = Field(default=False, description="Whether command is required")
    context_keywords: List[str] = Field(
        default_factory=list,
        description="Context keywords for command activation")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional command parameters")


class ProtocolSummary(BaseModel):
    """Protocol summary for list responses"""
    id: str
    name: str
    description: Optional[str]
    command_count: int
    status: str
    created_at: datetime


class ProtocolCreate(BaseModel):
    """Protocol creation request model"""
    id: str = Field(..., min_length=1, max_length=50,
                    description="Unique protocol identifier")
    name: str = Field(..., min_length=1, max_length=100,
                      description="Human-readable protocol name")
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Protocol description")
    commands: List[ProtocolCommand] = Field(...,
                                            description="List of semantic commands")
    execution_order: List[str] = Field(
        default_factory=list,
        description="Command execution order")


class ProtocolUpdate(BaseModel):
    """Protocol update request model"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    commands: Optional[List[ProtocolCommand]] = Field(default=None)
    execution_order: Optional[List[str]] = Field(default=None)


class ProtocolResponse(BaseModel):
    """Protocol detailed response model"""
    id: str
    name: str
    description: Optional[str]
    commands: List[ProtocolCommand]
    execution_order: List[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    command_count: int


class ProtocolListResponse(BaseModel):
    """Protocol list response model"""
    protocols: List[ProtocolSummary]
    total: int


# Create router instance
router = APIRouter(
    prefix="/projects/{project_id}/protocols",
    tags=["protocols"],
    responses={
        404: {"description": "Project or protocol not found"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    }
)


@router.get("/", response_model=ProtocolListResponse)
async def list_protocols(
    project_id: str = Path(..., description="Project ID"),
    status: Optional[str] = Query(None, description="Filter by protocol status"),
    current_user: dict = Depends(get_current_user),
    protocol_service: ProtocolService = Depends(),
    project_service: ProjectService = Depends()
):
    """List all protocols in a project."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get protocols for the project
        protocols_data = await protocol_service.list_protocols(
            project_id=project_id,
            status_filter=status
        )

        # Convert to response format
        protocols = [
            ProtocolSummary(
                id=protocol.get('id', ''),
                name=protocol.get('name', ''),
                description=protocol.get('description'),
                command_count=len(protocol.get('commands', [])),
                status=protocol.get('status', 'active'),
                created_at=protocol.get('created_at', datetime.utcnow())
            )
            for protocol in protocols_data
        ]

        return ProtocolListResponse(
            protocols=protocols,
            total=len(protocols)
        )

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=ProtocolResponse)
async def create_protocol(
    project_id: str = Path(..., description="Project ID"),
    current_user: dict = Depends(get_current_user),
    protocol_service: ProtocolService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster=Depends(get_event_broadcaster),
    protocol_data: ProtocolCreate = Body(...)
):
    """Create a new protocol in a project."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if protocol ID already exists in project
        existing_protocol = await protocol_service.get_protocol(project_id, protocol_data.id)
        if existing_protocol:
            raise HTTPException(
                status_code=400, detail=f"Protocol with ID '{
                    protocol_data.id}' already exists in project")

        # Validate execution order
        command_names = {cmd.name for cmd in protocol_data.commands}
        for order_name in protocol_data.execution_order:
            if order_name not in command_names:
                raise HTTPException(
                    status_code=400,
                    detail=f"Execution order command '{order_name}' not found in commands")

        # Create the protocol
        protocol = await protocol_service.create_protocol(
            project_id=project_id,
            id=protocol_data.id,
            name=protocol_data.name,
            description=protocol_data.description,
            commands=protocol_data.commands,
            execution_order=protocol_data.execution_order
        )

        # Prepare response
        response = ProtocolResponse(
            id=protocol.get('id', ''),
            name=protocol.get('name', ''),
            description=protocol.get('description'),
            commands=protocol_data.commands,
            execution_order=protocol_data.execution_order,
            status=protocol.get('status', 'active'),
            created_at=protocol.get('created_at', datetime.utcnow()),
            updated_at=protocol.get('updated_at'),
            command_count=len(protocol_data.commands)
        )

        # Broadcast protocol creation event
        await event_broadcaster.broadcast_event(
            event_type=EventType.PROTOCOL_CREATED,
            data={
                "project_id": project_id,
                "protocol_id": protocol.id,
                "protocol_name": protocol.name,
                "command_count": len(protocol_data.commands)
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


@router.put("/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    project_id: str = Path(..., description="Project ID"),
    protocol_id: str = Path(..., description="Protocol ID"),
    current_user: dict = Depends(get_current_user),
    protocol_service: ProtocolService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster=Depends(get_event_broadcaster),
    protocol_data: ProtocolUpdate = Body(...)
):
    """Update an existing protocol."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify protocol exists
        protocol = await protocol_service.get_protocol(project_id, protocol_id)
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found")

        # Update the protocol
        update_data = protocol_data.model_dump(exclude_unset=True)
        updated_protocol = await protocol_service.update_protocol(
            project_id=project_id,
            protocol_id=protocol_id,
            **update_data
        )

        # Prepare response
        response = ProtocolResponse(
            id=updated_protocol.get('id', ''),
            name=updated_protocol.get('name', ''),
            description=updated_protocol.get('description'),
            commands=updated_protocol.get('commands', []),
            execution_order=updated_protocol.get('execution_order', []),
            status=updated_protocol.get('status', 'active'),
            created_at=updated_protocol.get('created_at', datetime.utcnow()),
            updated_at=updated_protocol.get('updated_at'),
            command_count=len(updated_protocol.get('commands', []))
        )

        # Broadcast protocol update event
        await event_broadcaster.broadcast_event(
            event_type=EventType.PROTOCOL_UPDATED,
            data={
                "project_id": project_id,
                "protocol_id": protocol_id,
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


@router.delete("/{protocol_id}")
async def delete_protocol(
    project_id: str = Path(..., description="Project ID"),
    protocol_id: str = Path(..., description="Protocol ID"),
    current_user: dict = Depends(get_current_user),
    protocol_service: ProtocolService = Depends(),
    project_service: ProjectService = Depends(),
    event_broadcaster=Depends(get_event_broadcaster)
):
    """Delete a protocol."""
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify protocol exists
        protocol = await protocol_service.get_protocol(project_id, protocol_id)
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found")

        # Check if protocol is being used by agents or teams
        if await protocol_service.is_protocol_in_use(project_id, protocol_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete protocol that is being used by agents or teams"
            )

        # Delete the protocol
        await protocol_service.delete_protocol(project_id, protocol_id)

        # Broadcast protocol deletion event
        await event_broadcaster.broadcast_event(
            event_type=EventType.PROTOCOL_DELETED,
            data={
                "project_id": project_id,
                "protocol_id": protocol_id,
                "protocol_name": protocol.get('name', '') if isinstance(protocol, dict) else getattr(protocol, 'name', '')
            },
            user_id=current_user["id"]
        )

        return {"success": True, "message": "Protocol deleted successfully"}

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for protocols
@router.get("/health")
async def protocols_health():
    """Health check endpoint for protocols service"""
    return {
        "service": "protocols",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
