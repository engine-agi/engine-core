"""
Tool model for Engine Framework.

Tools provide external integrations for agents and teams, including:
- API integrations (REST, GraphQL)
- CLI tool executions
- MCP (Model Context Protocol) servers
- Database connections
- File system operations
- Custom plugin integrations

Based on Engine Framework data model specification.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, CheckConstraint, Column, Index, Integer, String, Text,
    JSON as JSONB
)
from sqlalchemy.orm import validates

from .base import SQLAlchemyBaseModel
import json
import re

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .agent import Agent
    from .team import Team


class ToolType:
    """Tool integration types."""
    API = "api"
    CLI = "cli"
    MCP = "mcp"
    DATABASE = "database"
    FILESYSTEM = "filesystem"
    CUSTOM = "custom"


class ToolStatus:
    """Tool status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class Tool(SQLAlchemyBaseModel):
    """
    Tool entity - external integrations and capabilities for agents.

    Tools extend agent capabilities by providing interfaces to external
    systems, APIs, command-line utilities, and custom integrations.
    They support plugin architecture and capability discovery.

    Key features:
    - Multiple integration types (API, CLI, MCP, custom)
    - Dynamic capability discovery and validation
    - Authentication and rate limiting support
    - Command mapping and parameter validation
    - Health monitoring and error handling
    """

    __tablename__ = "tools"

    # Basic tool information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable tool name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Tool purpose, capabilities, and usage instructions"
    )

    # Tool classification
    type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Tool integration type (api, cli, mcp, database, filesystem, custom)"
    )

    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Tool category (e.g., 'development', 'communication', 'data', 'analysis')"
    )

    version = Column(
        String(50),
        nullable=True,
        comment="Tool version information"
    )

    # Tool status and health
    status = Column(
        String(50),
        nullable=False,
        default=ToolStatus.ACTIVE,
        index=True,
        comment="Tool operational status"
    )

    # Tool configuration and connection
    connection_config = Column(
        JSONB,
        nullable=False,
        comment="Connection configuration (URLs, paths, credentials)"
    )

    authentication = Column(
        JSONB,
        nullable=True,
        comment="Authentication configuration and credentials"
    )

    # Tool capabilities and commands
    capabilities = Column(
        JSONB,
        nullable=True,
        comment="Tool capabilities and supported operations"
    )

    commands = Column(
        JSONB,
        nullable=True,
        comment="Available commands with parameters and mappings"
    )

    # Rate limiting and quotas
    rate_limits = Column(
        JSONB,
        nullable=True,
        comment="Rate limiting configuration and current usage"
    )

    # Tool validation and testing
    health_check = Column(
        JSONB,
        nullable=True,
        comment="Health check configuration and last results"
    )

    # Usage statistics
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of tool invocations"
    )

    success_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of successful tool invocations"
    )

    last_used_at = Column(
        String(50),
        nullable=True,
        comment="Timestamp of last tool usage"
    )

    # Error tracking
    error_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of tool errors"
    )

    last_error = Column(
        JSONB,
        nullable=True,
        comment="Details of last error encountered"
    )

    # Tool-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    tool_metadata = Column(
        JSONB,
        nullable=True,
        comment="Tool-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    def __init__(self, **kwargs):
        """Initialize tool with validation."""
        # Set defaults
        if 'status' not in kwargs:
            kwargs['status'] = ToolStatus.ACTIVE
        if 'usage_count' not in kwargs:
            kwargs['usage_count'] = 0
        if 'success_count' not in kwargs:
            kwargs['success_count'] = 0
        if 'error_count' not in kwargs:
            kwargs['error_count'] = 0

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Tool(id='{self.id}', name='{self.name}', type='{self.type}')>"

    # === VALIDATION METHODS ===

    @validates('id')
    def validate_id(self, key: str, value: str) -> str:
        """Validate tool ID format."""
        if not value:
            raise ValueError("Tool ID is required")

        # Must be alphanumeric with underscores, 2-100 characters
        if not re.match(r'^[a-zA-Z0-9_]{2,100}$', value):
            raise ValueError(
                "Tool ID must be 2-100 characters, containing only "
                "letters, numbers, and underscores"
            )

        return value.lower()

    @validates('name')
    def validate_name(self, key: str, value: str) -> str:
        """Validate tool name."""
        if not value or not value.strip():
            raise ValueError("Tool name is required")

        if len(value.strip()) > 255:
            raise ValueError("Tool name cannot exceed 255 characters")

        return value.strip()

    @validates('type')
    def validate_type(self, key: str, value: str) -> str:
        """Validate tool type."""
        valid_types = [ToolType.API, ToolType.CLI, ToolType.MCP,
                      ToolType.DATABASE, ToolType.FILESYSTEM, ToolType.CUSTOM]

        if value not in valid_types:
            raise ValueError(f"Tool type must be one of: {', '.join(valid_types)}")

        return value

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate tool status."""
        valid_statuses = [ToolStatus.ACTIVE, ToolStatus.INACTIVE, ToolStatus.ERROR,
                         ToolStatus.TESTING, ToolStatus.DEPRECATED]

        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        return value

    @validates('connection_config')
    def validate_connection_config(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Validate connection configuration."""
        if not isinstance(value, dict):
            raise ValueError("Connection config must be a dictionary")

        # Type-specific validations
        tool_type = getattr(self, 'type')
        if tool_type == ToolType.API:
            if 'base_url' not in value:
                raise ValueError("API tools must have 'base_url' in connection config")

        elif tool_type == ToolType.CLI:
            if 'executable_path' not in value and 'command' not in value:
                raise ValueError(
                    "CLI tools must have 'executable_path' or 'command' in connection config")

        elif tool_type == ToolType.MCP:
            if 'server_path' not in value:
                raise ValueError(
                    "MCP tools must have 'server_path' in connection config")

        elif tool_type == ToolType.DATABASE:
            if 'connection_string' not in value:
                raise ValueError(
                    "Database tools must have 'connection_string' in connection config")

        return value

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool data before creating/updating."""
        validated = data.copy()

        # Required fields
        if 'id' not in validated or not validated['id']:
            raise ValueError("Tool ID is required")

        if 'name' not in validated or not validated['name']:
            raise ValueError("Tool name is required")

        if 'type' not in validated or not validated['type']:
            raise ValueError("Tool type is required")

        if 'connection_config' not in validated or not validated['connection_config']:
            raise ValueError("Tool connection config is required")

        # Validate commands structure if present
        if 'commands' in validated and validated['commands']:
            if not isinstance(validated['commands'], list):
                raise ValueError("Commands must be a list")

            for i, command in enumerate(validated['commands']):
                if not isinstance(command, dict):
                    raise ValueError(f"Command {i} must be a dictionary")

                if 'name' not in command:
                    raise ValueError(f"Command {i} must have a name")

        return validated

    # === TOOL CAPABILITY MANAGEMENT ===

    def add_capability(self, name: str, description: str, **kwargs) -> None:
        """Add capability to tool."""
        capabilities = getattr(self, 'capabilities') or {}
        if not capabilities:
            capabilities = {}

        capabilities[name] = {
            'description': description,
            'added_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        setattr(self, 'capabilities', capabilities)

    def remove_capability(self, name: str) -> None:
        """Remove capability from tool."""
        capabilities = getattr(self, 'capabilities') or {}
        if capabilities and name in capabilities:
            del capabilities[name]
            setattr(self, 'capabilities', capabilities)

    def has_capability(self, name: str) -> bool:
        """Check if tool has specific capability."""
        capabilities = getattr(self, 'capabilities') or {}
        return capabilities is not None and name in capabilities

    def get_capabilities(self) -> List[str]:
        """Get list of all tool capabilities."""
        capabilities = getattr(self, 'capabilities') or {}
        return list(capabilities.keys()) if capabilities else []

    # === COMMAND MANAGEMENT ===

    def add_command(
        self,
        name: str,
        description: str,
        parameters: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """Add command to tool."""
        commands = getattr(self, 'commands') or []
        if not commands:
            commands = []

        # Check for duplicate command names
        existing_names = [cmd['name'] for cmd in commands if isinstance(cmd, dict)]
        if name in existing_names:
            raise ValueError(f"Command '{name}' already exists")

        command = {
            'name': name,
            'description': description,
            'parameters': parameters or [],
            **kwargs
        }

        commands.append(command)
        setattr(self, 'commands', commands)

    def remove_command(self, name: str) -> None:
        """Remove command from tool."""
        commands = getattr(self, 'commands') or []
        if commands:
            commands = [cmd for cmd in commands
                       if not (isinstance(cmd, dict) and cmd.get('name') == name)]
            setattr(self, 'commands', commands)

    def get_command(self, name: str) -> Optional[Dict[str, Any]]:
        """Get command by name."""
        commands = getattr(self, 'commands') or []
        if commands:
            for command in commands:
                if isinstance(command, dict) and command.get('name') == name:
                    return command
        return None

    def has_command(self, name: str) -> bool:
        """Check if tool has specific command."""
        return self.get_command(name) is not None

    # === HEALTH AND MONITORING ===

    def update_health_check(self, status: str, details: Dict[str, Any]) -> None:
        """Update tool health check results."""
        health_check = {
            'status': status,
            'details': details,
            'checked_at': datetime.utcnow().isoformat(),
            'previous_status': getattr(self, 'health_check', {}).get('status') if getattr(self, 'health_check') else None
        }
        setattr(self, 'health_check', health_check)

        # Update tool status based on health check
        if status == 'healthy':
            setattr(self, 'status', ToolStatus.ACTIVE)
        elif status == 'error':
            setattr(self, 'status', ToolStatus.ERROR)
        elif status == 'unreachable':
            setattr(self, 'status', ToolStatus.INACTIVE)

    def is_healthy(self) -> bool:
        """Check if tool is healthy based on last health check."""
        health_check = getattr(self, 'health_check')
        if not health_check:
            return getattr(self, 'status') == ToolStatus.ACTIVE

        return health_check.get('status') == 'healthy'

    def get_success_rate(self) -> Optional[float]:
        """Calculate tool success rate."""
        usage_count = getattr(self, 'usage_count', 0)
        if usage_count > 0:
            success_count = getattr(self, 'success_count', 0)
            return success_count / usage_count
        return None

    # === USAGE TRACKING ===

    def record_usage(self, success: bool = True, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Record tool usage statistics."""
        self.usage_count += 1

        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error_details:
                self.last_error = {
                    'details': error_details,
                    'timestamp': datetime.utcnow().isoformat()
                }

        self.last_used_at = datetime.utcnow().isoformat()

    def reset_statistics(self) -> None:
        """Reset tool usage statistics."""
        self.usage_count = 0
        self.success_count = 0
        self.error_count = 0
        self.last_error = None

    # === RATE LIMITING ===

    def set_rate_limit(self, requests_per_minute: int, requests_per_hour: Optional[int] = None) -> None:
        """Set rate limiting configuration."""
        rate_limits = getattr(self, 'rate_limits') or {}
        if not rate_limits:
            rate_limits = {}

        rate_limits.update({
            'requests_per_minute': requests_per_minute,
            'requests_per_hour': requests_per_hour,
            'current_usage': {
                'minute': 0,
                'hour': 0,
                'reset_minute': datetime.utcnow().isoformat(),
                'reset_hour': datetime.utcnow().isoformat()
            }
        })
        setattr(self, 'rate_limits', rate_limits)

    def check_rate_limit(self) -> tuple[bool, Optional[str]]:
        """Check if rate limit allows current request."""
        rate_limits = getattr(self, 'rate_limits')
        if not rate_limits:
            return True, None

        # Simplified rate limiting check
        # In real implementation, this would use proper time-window tracking
        current_usage = rate_limits.get('current_usage', {})

        minute_limit = rate_limits.get('requests_per_minute')
        if minute_limit and current_usage.get('minute', 0) >= minute_limit:
            return False, "Rate limit exceeded: requests per minute"

        hour_limit = rate_limits.get('requests_per_hour')
        if hour_limit and current_usage.get('hour', 0) >= hour_limit:
            return False, "Rate limit exceeded: requests per hour"

        return True, None

    # === TOOL SUMMARY AND INFORMATION ===

    def get_tool_summary(self) -> Dict[str, Any]:
        """Get tool summary information."""
        capabilities = getattr(self, 'capabilities') or {}
        commands = getattr(self, 'commands') or []
        rate_limits = getattr(self, 'rate_limits')
        created_at = getattr(self, 'created_at')
        updated_at = getattr(self, 'updated_at')

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'category': self.category,
            'version': self.version,
            'status': self.status,
            'capabilities_count': len(capabilities) if capabilities else 0,
            'capabilities': self.get_capabilities(),
            'commands_count': len(commands) if commands else 0,
            'usage_count': self.usage_count,
            'success_rate': self.get_success_rate(),
            'is_healthy': self.is_healthy(),
            'has_rate_limits': rate_limits is not None,
            'last_used_at': self.last_used_at,
            'created_at': created_at.isoformat() if created_at else None,
            'updated_at': updated_at.isoformat() if updated_at else None
        }

    # === FACTORY METHODS FOR COMMON TOOLS ===

    @classmethod
    def create_github_tool(cls) -> "Tool":
        """Create GitHub API integration tool."""
        return cls(
            id='github_integration',
            name='GitHub Integration',
            type=ToolType.API,
            category='development',
            description='GitHub API integration for repository management',
            connection_config={
                'base_url': 'https://api.github.com',
                'authentication_type': 'token'
            },
            capabilities={
                'repository_management': {'description': 'Create, read, update repositories'},
                'pull_requests': {'description': 'Manage pull requests'},
                'issues': {'description': 'Manage issues and discussions'},
                'actions': {'description': 'Trigger and monitor GitHub Actions'}
            },
            commands=[
                {
                    'name': 'create_repository',
                    'description': 'Create new GitHub repository',
                    'endpoint': '/user/repos',
                    'method': 'POST',
                    'parameters': ['name', 'description', 'private']
                },
                {
                    'name': 'create_pull_request',
                    'description': 'Create pull request',
                    'endpoint': '/repos/{owner}/{repo}/pulls',
                    'method': 'POST',
                    'parameters': ['title', 'body', 'head', 'base']
                }
            ]
        )

    @classmethod
    def create_vscode_tool(cls) -> "Tool":
        """Create VS Code MCP server tool."""
        return cls(
            id='vscode_extension',
            name='VS Code Extension',
            type=ToolType.MCP,
            category='development',
            description='VS Code MCP server for development environment integration',
            connection_config={
                'server_path': '/usr/local/bin/vscode-mcp-server',
                'capabilities': ['file_operations', 'terminal_commands', 'debugging']
            },
            capabilities={
                'file_operations': {'description': 'Create, read, write, delete files'},
                'terminal_commands': {'description': 'Execute terminal commands'},
                'debugging': {'description': 'Start and control debugging sessions'}
            },
            commands=[
                {
                    'name': 'create_file',
                    'description': 'Create new file with content',
                    'mcp_method': 'create_file',
                    'parameters': ['path', 'content']
                },
                {
                    'name': 'run_command',
                    'description': 'Execute terminal command',
                    'mcp_method': 'run_command',
                    'parameters': ['command', 'working_directory']
                }
            ]
        )

    @classmethod
    def create_database_tool(cls, db_type: str = "postgresql") -> "Tool":
        """Create database integration tool."""
        return cls(
            id=f'{db_type}_database',
            name=f'{db_type.title()} Database',
            type=ToolType.DATABASE,
            category='data',
            description=f'{db_type.title()} database integration for data operations',
            connection_config={
                'connection_string': f'{db_type}://user:pass@localhost:5432/dbname',
                'pool_size': 10,
                'timeout': 30
            },
            capabilities={
                'query_execution': {'description': 'Execute SQL queries'},
                'schema_management': {'description': 'Manage database schema'},
                'data_migration': {'description': 'Handle data migrations'}
            },
            commands=[
                {
                    'name': 'execute_query',
                    'description': 'Execute SQL query',
                    'parameters': ['query', 'parameters']
                },
                {
                    'name': 'create_table',
                    'description': 'Create database table',
                    'parameters': ['table_name', 'schema']
                }
            ]
        )


# Database indexes and constraints can be added later when SQLAlchemy setup is complete
