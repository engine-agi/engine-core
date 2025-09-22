"""
Project Service Layer - Business Logic for Project Management.

The ProjectService provides high-level business logic for project management,
including CRUD operations, validation, model management, and integration
with agents, teams, workflows, and other engine components.

Key Features:
- Repository pattern for data access
- Business logic validation
- Project lifecycle management
- Model validation and management
- Resource quota management
- User access control
- Project statistics and monitoring
- Error handling and recovery

Architecture:
- Service Layer (this) -> Repository Layer -> Models -> Database
- Integration with all Engine Framework components
- Event-driven updates and notifications
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid
import logging

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ..models.project import Project
    from ..models.infrastructure import User

logger = logging.getLogger(__name__)


class ProjectServiceError(Exception):
    """Base exception for project service errors."""
    pass


class ProjectNotFoundError(ProjectServiceError):
    """Raised when a project is not found."""
    pass


class ProjectValidationError(ProjectServiceError):
    """Raised when project validation fails."""
    pass


class ProjectOperationError(ProjectServiceError):
    """Raised when a project operation fails."""
    pass


@dataclass
class ProjectLimits:
    """Project resource limits."""
    max_agents: int = 100
    max_teams: int = 20
    max_workflows: int = 50
    max_tools: int = 200
    max_books: int = 10
    max_storage_gb: float = 10.0


class ProjectService:
    """
    Service for managing projects in the Engine Framework.

    Provides business logic for project lifecycle management, validation,
    and integration with other engine components.
    """

    def __init__(self):
        """Initialize the project service."""
        self.logger = logging.getLogger(__name__)

    async def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID with access control.

        Args:
            project_id: The project ID
            user_id: The user ID for access control

        Returns:
            Project data or None if not found/not accessible
        """
        try:
            # TODO: Implement actual project retrieval from database
            # For now, return a mock project for testing
            if project_id.startswith("project_"):
                return {
                    "id": project_id,
                    "name": f"Project {project_id}",
                    "description": f"Mock project {project_id}",
                    "owner_id": user_id,
                    "allowed_models": ["claude-3.5-sonnet", "gpt-4"],
                    "max_agents": 50,
                    "max_teams": 10,
                    "max_workflows": 25,
                    "max_tools": 100,
                    "max_books": 5,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            return None
        except Exception as e:
            self.logger.error(f"Error getting project {project_id}: {str(e)}")
            raise ProjectOperationError(f"Failed to get project: {str(e)}")

    async def list_projects(self, user_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List projects accessible by a user.

        Args:
            user_id: The user ID
            skip: Number of projects to skip
            limit: Maximum number of projects to return

        Returns:
            List of project summaries
        """
        try:
            # TODO: Implement actual project listing from database
            # For now, return mock projects for testing
            projects = []
            for i in range(min(limit, 5)):  # Return up to 5 mock projects
                projects.append({
                    "id": f"project_{i+1}",
                    "name": f"Project {i+1}",
                    "description": f"Mock project {i+1}",
                    "owner_id": user_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
            return projects
        except Exception as e:
            self.logger.error(f"Error listing projects for user {user_id}: {str(e)}")
            raise ProjectOperationError(f"Failed to list projects: {str(e)}")

    async def create_project(
        self,
        name: str,
        description: str,
        owner_id: str,
        allowed_models: List[str],
        limits: Optional[ProjectLimits] = None
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            owner_id: Owner user ID
            allowed_models: List of allowed AI models
            limits: Resource limits for the project

        Returns:
            Created project data
        """
        try:
            # TODO: Implement actual project creation in database
            project_id = f"project_{uuid.uuid4().hex[:8]}"
            project = {
                "id": project_id,
                "name": name,
                "description": description,
                "owner_id": owner_id,
                "allowed_models": allowed_models,
                "max_agents": limits.max_agents if limits else 50,
                "max_teams": limits.max_teams if limits else 10,
                "max_workflows": limits.max_workflows if limits else 25,
                "max_tools": limits.max_tools if limits else 100,
                "max_books": limits.max_books if limits else 5,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            return project
        except Exception as e:
            self.logger.error(f"Error creating project: {str(e)}")
            raise ProjectOperationError(f"Failed to create project: {str(e)}")

    async def update_project(
        self,
        project_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing project.

        Args:
            project_id: The project ID
            user_id: The user ID (for access control)
            updates: Fields to update

        Returns:
            Updated project data
        """
        try:
            # TODO: Implement actual project update in database
            project = await self.get_project(project_id, user_id)
            if not project:
                raise ProjectNotFoundError(f"Project {project_id} not found")

            # Apply updates
            for key, value in updates.items():
                if key in project:
                    project[key] = value

            project["updated_at"] = datetime.utcnow()
            return project
        except ProjectNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {str(e)}")
            raise ProjectOperationError(f"Failed to update project: {str(e)}")

    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: The project ID
            user_id: The user ID (for access control)

        Returns:
            True if deleted successfully
        """
        try:
            # TODO: Implement actual project deletion from database
            project = await self.get_project(project_id, user_id)
            if not project:
                raise ProjectNotFoundError(f"Project {project_id} not found")

            # TODO: Check if project has active resources before deletion
            return True
        except ProjectNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {str(e)}")
            raise ProjectOperationError(f"Failed to delete project: {str(e)}")

    async def validate_model(self, model_name: str) -> bool:
        """
        Validate if an AI model is supported.

        Args:
            model_name: The model name to validate

        Returns:
            True if model is supported
        """
        # TODO: Implement actual model validation against supported models list
        supported_models = [
            "claude-3.5-sonnet",
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-haiku",
            "claude-3-sonnet"
        ]
        return model_name in supported_models

    async def get_project_stats(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get project statistics.

        Args:
            project_id: The project ID
            user_id: The user ID

        Returns:
            Project statistics
        """
        try:
            project = await self.get_project(project_id, user_id)
            if not project:
                raise ProjectNotFoundError(f"Project {project_id} not found")

            # TODO: Implement actual statistics calculation
            return {
                "project_id": project_id,
                "agent_count": 0,
                "team_count": 0,
                "workflow_count": 0,
                "tool_count": 0,
                "book_count": 0,
                "total_executions": 0,
                "active_executions": 0,
                "storage_used_gb": 0.0,
                "last_activity": datetime.utcnow()
            }
        except ProjectNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting project stats {project_id}: {str(e)}")
            raise ProjectOperationError(f"Failed to get project stats: {str(e)}")