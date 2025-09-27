"""
Protocol Service - Business Logic Layer for Protocol Management.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class ProtocolCreateRequest:
    """Request model for creating a protocol."""

    def __init__(
        self,
        id: str,
        name: str,
        description: Optional[str] = None,
        commands: Optional[List[Dict[str, Any]]] = None,
        execution_order: Optional[List[str]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.commands = commands or []
        self.execution_order = execution_order or []


class ProtocolUpdateRequest:
    """Request model for updating a protocol."""

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        commands: Optional[List[Dict[str, Any]]] = None,
        execution_order: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.commands = commands
        self.execution_order = execution_order


class ProtocolService:
    """Service for protocol management operations."""

    def __init__(self):
        self.protocols: Dict[str, Dict[str, Any]] = {}

    async def list_protocols(
        self, project_id: str, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List protocols for a project."""
        protocols = []
        for protocol in self.protocols.values():
            if protocol.get("project_id") == project_id:
                if status_filter is None or protocol.get("status") == status_filter:
                    protocols.append(protocol)
        return protocols

    async def get_protocol(
        self, project_id: str, protocol_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific protocol."""
        protocol = self.protocols.get(protocol_id)
        if protocol and protocol.get("project_id") == project_id:
            return protocol
        return None

    async def create_protocol(
        self,
        project_id: str,
        id: str,
        name: str,
        description: Optional[str] = None,
        commands: Optional[List[Dict[str, Any]]] = None,
        execution_order: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new protocol."""
        protocol = {
            "id": id,
            "project_id": project_id,
            "name": name,
            "description": description,
            "commands": commands or [],
            "execution_order": execution_order or [],
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": None,
        }
        self.protocols[id] = protocol
        return protocol

    async def update_protocol(
        self, project_id: str, protocol_id: str, **update_data
    ) -> Dict[str, Any]:
        """Update an existing protocol."""
        protocol = self.protocols.get(protocol_id)
        if not protocol or protocol.get("project_id") != project_id:
            raise ValueError("Protocol not found")

        for key, value in update_data.items():
            if value is not None:
                protocol[key] = value
        protocol["updated_at"] = datetime.utcnow()
        return protocol

    async def delete_protocol(self, project_id: str, protocol_id: str) -> None:
        """Delete a protocol."""
        protocol = self.protocols.get(protocol_id)
        if protocol and protocol.get("project_id") == project_id:
            del self.protocols[protocol_id]

    async def is_protocol_in_use(self, project_id: str, protocol_id: str) -> bool:
        """Check if protocol is being used by agents or teams."""
        return False
