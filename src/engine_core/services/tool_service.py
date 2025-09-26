"""
Tool Service - Business Logic Layer for Tool Management and Execution.

The ToolService provides comprehensive tool lifecycle management functionality,
including tool registration, capability discovery, execution orchestration,
performance monitoring, and integration with the core tool system components.

Key Features:
- Tool lifecycle management (register, configure, monitor, unregister)
- Capability discovery and validation
- Execution orchestration with security and resource management
- Plugin system for extensible tool integrations
- Performance analytics and usage statistics
- Template management for common tool configurations
- Real-time execution monitoring and control
- Integration with other Engine Framework services

Architecture:
- Repository pattern for tool persistence
- Service layer for business logic coordination
- Integration with ToolExecutor for secure execution
"""
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..core.tools import (
    ToolBuilder, ToolConfiguration, ToolCapability, ToolInterface,
    ToolType, ToolExecutionMode, ToolStatus, PermissionLevel,
    ExecutionEnvironment, ToolExecutionRequest, ToolExecutionResult,
    ToolHealthCheck, ToolRegistry, APITool, CLITool, MCPTool, PluginTool
)

from ..core.tools.tool_executor import (
    ToolExecutor, ExecutionContext, ExecutionMetrics, ResourceLimits,
    SecurityPolicy, SecurityManager, ResourceManager, CacheManager,
    ExecutionQueue, ExecutionPriority, ExecutionStatus,
    create_tool_executor
)
import asyncio
import importlib
import json
import logging
import os
import tempfile
import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import Field

# Type checking imports
if TYPE_CHECKING:
    from ..models.tool import Tool
    from .agent_service import AgentService
    from .workflow_service import WorkflowService

# Core imports
from ..core.tools import (
    ToolBuilder, ToolConfiguration, ToolCapability, ToolInterface,
    ToolType, ToolExecutionMode, ToolStatus, PermissionLevel,
    ExecutionEnvironment, ToolExecutionRequest, ToolExecutionResult,
    ToolHealthCheck, ToolRegistry, APITool, CLITool, MCPTool, PluginTool
)

from ..core.tools.tool_executor import (
    ToolExecutor, ExecutionContext, ExecutionMetrics, ResourceLimits,
    SecurityPolicy, SecurityManager, ResourceManager, CacheManager,
    ExecutionQueue, ExecutionPriority, ExecutionStatus,
    create_tool_executor
)

logger = logging.getLogger(__name__)


class ToolServiceError(Exception):
    """Base exception for tool service errors."""
    pass


class ToolNotFoundError(ToolServiceError):
    """Tool not found error."""
    pass


class ToolRegistrationError(ToolServiceError):
    """Tool registration error."""
    pass


class ToolExecutionError(ToolServiceError):
    """Tool execution error."""
    pass


@dataclass
class ToolCreateRequest:
    """Request for creating/registering a new tool."""
    tool_id: str
    name: str
    tool_type: ToolType
    version: str = "1.0.0"
    description: str = ""

    # Configuration
    endpoint: Optional[str] = None
    authentication: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    retry_attempts: int = 3

    # Execution settings
    execution_mode: ToolExecutionMode = ToolExecutionMode.SYNCHRONOUS
    execution_environment: ExecutionEnvironment = ExecutionEnvironment.SANDBOX
    max_concurrent_executions: int = 5

    # Security
    required_permissions: Set[PermissionLevel] = field(default_factory=set)
    allowed_users: Set[str] = field(default_factory=set)
    allowed_projects: Set[str] = field(default_factory=set)

    # Capabilities and metadata
    capabilities: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Plugin-specific
    plugin_class: Optional[str] = None
    plugin_config: Dict[str, Any] = field(default_factory=dict)

    # MCP-specific
    mcp_server_path: Optional[str] = None
    mcp_args: List[str] = field(default_factory=list)
    mcp_env: Dict[str, str] = field(default_factory=dict)

    # Service settings
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    is_active: bool = True


@dataclass
class ToolUpdateRequest:
    """Request for updating tool configuration."""
    name: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    timeout_seconds: Optional[int] = None
    retry_attempts: Optional[int] = None
    execution_mode: Optional[ToolExecutionMode] = None
    max_concurrent_executions: Optional[int] = None
    capabilities: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


@dataclass
class ToolSearchCriteria:
    """Criteria for searching tools."""
    name_pattern: Optional[str] = None
    tool_type: Optional[ToolType] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    is_active: Optional[bool] = None
    status: Optional[ToolStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


@dataclass
class ToolAnalytics:
    """Tool performance analytics."""
    tool_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    median_execution_time: float = 0.0
    capability_usage: Dict[str, int] = field(default_factory=dict)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)
    performance_trends: List[Dict[str, Any]] = field(default_factory=list)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    last_execution_at: Optional[datetime] = None
    health_status: ToolStatus = ToolStatus.AVAILABLE


@dataclass
class ToolTemplate:
    """Template for common tool configurations."""
    template_id: str
    name: str
    description: str
    tool_type: ToolType
    configuration_template: Dict[str, Any] = field(default_factory=dict)
    capability_templates: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0


class ToolRepository(ABC):
    """Abstract repository interface for tool data persistence."""

    @abstractmethod
    async def create_tool(self, tool_data: Dict[str, Any]) -> 'Tool':
        """Create a new tool record."""
        pass

    @abstractmethod
    async def get_tool_by_id(self, tool_id: str) -> Optional['Tool']:
        """Get tool by ID."""
        pass

    @abstractmethod
    async def update_tool(self, tool_id: str, updates: Dict[str, Any]) -> Optional['Tool']:
        """Update tool record."""
        pass

    @abstractmethod
    async def delete_tool(self, tool_id: str) -> bool:
        """Delete tool record."""
        pass

    @abstractmethod
    async def search_tools(self, criteria: ToolSearchCriteria) -> List['Tool']:
        """Search tools by criteria."""
        pass

    @abstractmethod
    async def create_tool_execution(self, execution_data: Dict[str, Any]) -> 'ToolExecution':
        """Create tool execution record."""
        pass

    @abstractmethod
    async def update_tool_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> Optional['ToolExecution']:
        """Update tool execution record."""
        pass

    @abstractmethod
    async def get_tool_executions(
        self,
        tool_id: str,
        limit: int = 50
    ) -> List['ToolExecution']:
        """Get tool execution history."""
        pass

    @abstractmethod
    async def get_tool_analytics(self, tool_id: str) -> Dict[str, Any]:
        """Get tool analytics data."""
        pass

    @abstractmethod
    async def create_tool_template(self, template_data: Dict[str, Any]) -> ToolTemplate:
        """Create tool template."""
        pass

    @abstractmethod
    async def get_tool_templates(self, tool_type: Optional[ToolType] = None) -> List[ToolTemplate]:
        """Get tool templates."""
        pass


class MockToolRepository(ToolRepository):
    """Mock repository implementation for development/testing."""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.executions: Dict[str, Dict[str, Any]] = {}
        self.templates: Dict[str, ToolTemplate] = {}

        # Create default templates
        self._create_default_templates()

    async def create_tool(self, tool_data: Dict[str, Any]) -> 'Tool':
        """Create a new tool record."""
        tool_id = tool_data.get('id', str(uuid.uuid4()))
        tool_data['id'] = tool_id
        tool_data['created_at'] = datetime.utcnow()
        tool_data['updated_at'] = datetime.utcnow()
        tool_data['execution_count'] = 0

        self.tools[tool_id] = tool_data.copy()

        class MockTool:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockTool(tool_data)

    async def get_tool_by_id(self, tool_id: str) -> Optional['Tool']:
        """Get tool by ID."""
        if tool_id not in self.tools:
            return None

        class MockTool:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockTool(self.tools[tool_id])

    async def update_tool(self, tool_id: str, updates: Dict[str, Any]) -> Optional['Tool']:
        """Update tool record."""
        if tool_id not in self.tools:
            return None

        self.tools[tool_id].update(updates)
        self.tools[tool_id]['updated_at'] = datetime.utcnow()

        class MockTool:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockTool(self.tools[tool_id])

    async def delete_tool(self, tool_id: str) -> bool:
        """Delete tool record."""
        if tool_id in self.tools:
            del self.tools[tool_id]
            # Delete related executions
            executions_to_delete = [
                eid for eid, exec_data in self.executions.items()
                if exec_data.get('tool_id') == tool_id
            ]
            for eid in executions_to_delete:
                del self.executions[eid]
            return True
        return False

    async def search_tools(self, criteria: ToolSearchCriteria) -> List['Tool']:
        """Search tools by criteria."""
        results = []

        for tool_id, tool_data in self.tools.items():
            # Apply filters
            if criteria.name_pattern and criteria.name_pattern not in tool_data.get('name', ''):
                continue
            if criteria.tool_type and tool_data.get('tool_type') != criteria.tool_type.value:
                continue
            if criteria.project_id and tool_data.get('project_id') != criteria.project_id:
                continue
            if criteria.user_id and tool_data.get('user_id') != criteria.user_id:
                continue
            if criteria.is_active is not None and tool_data.get('is_active') != criteria.is_active:
                continue
            if criteria.tags:
                tool_tags = set(tool_data.get('tags', []))
                if not set(criteria.tags).issubset(tool_tags):
                    continue

            class MockTool:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)

            results.append(MockTool(tool_data))

        return results[criteria.offset:criteria.offset + criteria.limit]

    async def create_tool_execution(self, execution_data: Dict[str, Any]) -> 'ToolExecution':
        """Create tool execution record."""
        execution_id = execution_data.get('id', str(uuid.uuid4()))
        execution_data['id'] = execution_id
        execution_data['created_at'] = datetime.utcnow()

        self.executions[execution_id] = execution_data.copy()

        class MockToolExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockToolExecution(execution_data)

    async def update_tool_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> Optional['ToolExecution']:
        """Update tool execution record."""
        if execution_id not in self.executions:
            return None

        self.executions[execution_id].update(updates)
        self.executions[execution_id]['updated_at'] = datetime.utcnow()

        class MockToolExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockToolExecution(self.executions[execution_id])

    async def get_tool_executions(
        self,
        tool_id: str,
        limit: int = 50
    ) -> List['ToolExecution']:
        """Get tool execution history."""
        executions = [
            exec_data for exec_data in self.executions.values()
            if exec_data.get('tool_id') == tool_id
        ]

        executions.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)

        class MockToolExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return [MockToolExecution(e) for e in executions[:limit]]

    async def get_tool_analytics(self, tool_id: str) -> Dict[str, Any]:
        """Get tool analytics data."""
        executions = [
            exec_data for exec_data in self.executions.values()
            if exec_data.get('tool_id') == tool_id
        ]

        if not executions:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_execution_time': 0.0
            }

        successful = sum(1 for e in executions if e.get('status') == 'success')
        failed = sum(1 for e in executions if e.get('status') in ['error', 'failed'])

        execution_times = [
            e.get('execution_time', 0.0) for e in executions
            if e.get('execution_time') is not None
        ]

        return {
            'total_executions': len(executions),
            'successful_executions': successful,
            'failed_executions': failed,
            'average_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0.0,
            'last_execution_at': max(e.get('created_at', datetime.min) for e in executions)
        }

    async def create_tool_template(self, template_data: Dict[str, Any]) -> ToolTemplate:
        """Create tool template."""
        template = ToolTemplate(**template_data)
        self.templates[template.template_id] = template
        return template

    async def get_tool_templates(self, tool_type: Optional[ToolType] = None) -> List[ToolTemplate]:
        """Get tool templates."""
        templates = list(self.templates.values())

        if tool_type:
            templates = [t for t in templates if t.tool_type == tool_type]

        return templates

    def _create_default_templates(self):
        """Create default tool templates."""
        # GitHub API template
        github_template = ToolTemplate(
            template_id="github_api_template",
            name="GitHub API Tool",
            description="Template for GitHub API integration",
            tool_type=ToolType.API,
            configuration_template={
                "endpoint": "https://api.github.com",
                "headers": {"Accept": "application/vnd.github.v3+json"},
                "authentication": {"type": "token", "token": "<GITHUB_TOKEN>"}
            },
            capability_templates=[
                {
                    "name": "get_repository",
                    "description": "Get repository information",
                    "input_schema": {
                        "type": "object",
                        "required": ["owner", "repo"],
                        "properties": {
                            "owner": {"type": "string"},
                            "repo": {"type": "string"}
                        }
                    },
                    "metadata": {"http_method": "GET", "endpoint": "repos/{owner}/{repo}"}
                }
            ],
            tags=["api", "github", "version_control"]
        )
        self.templates[github_template.template_id] = github_template

        # Git CLI template
        git_template = ToolTemplate(
            template_id="git_cli_template",
            name="Git CLI Tool",
            description="Template for Git command-line integration",
            tool_type=ToolType.CLI,
            configuration_template={
                "executable": "git",
                "execution_environment": "sandbox"
            },
            capability_templates=[
                {
                    "name": "status",
                    "description": "Get git status",
                    "metadata": {"command_template": "status --porcelain"}
                },
                {
                    "name": "log",
                    "description": "Get git log",
                    "metadata": {"command_template": "log --oneline -n {count}"}
                }
            ],
            tags=["cli", "git", "version_control"]
        )
        self.templates[git_template.template_id] = git_template


class ToolService:
    """
    Service layer for tool management and execution orchestration.

    Provides comprehensive tool lifecycle management including:
    - Tool registration, configuration, and management
    - Capability discovery and validation
    - Secure execution orchestration
    - Performance monitoring and analytics
    - Template management for reusable configurations
    - Integration with other Engine Framework services
    """

    def __init__(
        self,
        repository: ToolRepository,
        tool_executor: Optional[ToolExecutor] = None,
        agent_service: Optional['AgentService'] = None,
        workflow_service: Optional['WorkflowService'] = None
    ):
        """Initialize tool service."""
        self.repository = repository
        self.tool_executor = tool_executor or create_tool_executor()
        self.agent_service = agent_service
        self.workflow_service = workflow_service

        # Core components
        self.tool_registry = ToolRegistry()
        self.tool_executor.tool_registry = self.tool_registry  # Set registry reference

        # Performance cache
        self._analytics_cache = {}
        self._tool_cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Service statistics
        self.service_stats = {
            'total_tools_registered': 0,
            'total_tools_active': 0,
            'total_executions': 0,
            'total_execution_failures': 0,
            'total_templates_created': 0,
            'average_tool_response_time': 0.0
        }

    # === Tool Lifecycle Management ===

    async def register_tool(self, request: ToolCreateRequest) -> 'Tool':
        """Register a new tool with the system."""
        start_time = datetime.utcnow()

        try:
            # Validate request
            await self._validate_create_request(request)

            # Build tool configuration
            config = await self._build_tool_configuration(request)

            # Register with tool registry
            if not await self.tool_registry.register_tool(config):
                raise ToolRegistrationError(
                    f"Failed to register tool: {request.tool_id}")

            # Create database record
            tool_data = {
                'id': request.tool_id,
                'name': request.name,
                'tool_type': request.tool_type.value,
                'version': request.version,
                'description': request.description,
                'configuration': config.__dict__,
                'project_id': request.project_id,
                'user_id': request.user_id,
                'is_active': request.is_active,
                'tags': request.tags,
                'metadata': request.metadata
            }

            tool = await self.repository.create_tool(tool_data)

            # Update statistics
            self.service_stats['total_tools_registered'] += 1
            if request.is_active:
                self.service_stats['total_tools_active'] += 1

            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time_stats(response_time)

            logger.info(
                f"Registered tool: {request.tool_id} ({request.tool_type.value})")
            return tool

        except Exception as e:
            logger.error(f"Failed to register tool {request.tool_id}: {str(e)}")
            raise ToolRegistrationError(str(e))

    async def get_tool(self, tool_id: str) -> 'Tool':
        """Get tool by ID."""

        # Check cache first
        cache_key = f"tool_{tool_id}"
        if cache_key in self._tool_cache:
            cached_tool, cached_time = self._tool_cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < self._cache_ttl:
                return cached_tool

        # Get from repository
        tool = await self.repository.get_tool_by_id(tool_id)
        if not tool:
            raise ToolNotFoundError(f"Tool {tool_id} not found")

        # Cache result
        self._tool_cache[cache_key] = (tool, datetime.utcnow())

        return tool

    async def update_tool(self, tool_id: str, request: ToolUpdateRequest) -> 'Tool':
        """Update tool configuration."""
        start_time = datetime.utcnow()

        try:
            # Check if tool exists
            existing = await self.get_tool(tool_id)

            # Prepare updates
            updates = {}
            config_updates = {}

            if request.name is not None:
                updates['name'] = request.name
            if request.description is not None:
                updates['description'] = request.description
            if request.endpoint is not None:
                config_updates['endpoint'] = request.endpoint
            if request.authentication is not None:
                config_updates['authentication'] = request.authentication
            if request.headers is not None:
                config_updates['headers'] = request.headers
            if request.timeout_seconds is not None:
                config_updates['timeout_seconds'] = request.timeout_seconds
            if request.retry_attempts is not None:
                config_updates['retry_attempts'] = request.retry_attempts
            if request.execution_mode is not None:
                config_updates['execution_mode'] = request.execution_mode.value
            if request.max_concurrent_executions is not None:
                config_updates['max_concurrent_executions'] = request.max_concurrent_executions
            if request.capabilities is not None:
                config_updates['capabilities'] = [
                    self._dict_to_capability(cap) for cap in request.capabilities
                ]
            if request.tags is not None:
                updates['tags'] = request.tags
            if request.metadata is not None:
                updates['metadata'] = request.metadata
            if request.is_active is not None:
                updates['is_active'] = request.is_active

            # Update configuration if needed
            if config_updates:
                current_config = existing.configuration
                current_config.update(config_updates)
                updates['configuration'] = current_config

                # Update tool registry
                tool = self.tool_registry.get_tool(tool_id)
                if tool:
                    # Re-register tool with updated configuration
                    await self.tool_registry.unregister_tool(tool_id)
                    new_config = self._dict_to_tool_configuration(current_config)
                    await self.tool_registry.register_tool(new_config)

            # Update repository
            tool = await self.repository.update_tool(tool_id, updates)
            if not tool:
                raise ToolNotFoundError(f"Tool {tool_id} not found")

            # Clear cache
            cache_key = f"tool_{tool_id}"
            if cache_key in self._tool_cache:
                del self._tool_cache[cache_key]

            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time_stats(response_time)

            logger.info(f"Updated tool: {tool_id}")
            return tool

        except Exception as e:
            logger.error(f"Failed to update tool {tool_id}: {str(e)}")
            raise ToolServiceError(str(e))

    async def unregister_tool(self, tool_id: str) -> bool:
        """Unregister tool from the system."""
        try:
            # Check if tool exists
            await self.get_tool(tool_id)

            # Unregister from tool registry
            await self.tool_registry.unregister_tool(tool_id)

            # Delete from repository
            success = await self.repository.delete_tool(tool_id)

            if success:
                # Clear cache
                cache_key = f"tool_{tool_id}"
                if cache_key in self._tool_cache:
                    del self._tool_cache[cache_key]

                self.service_stats['total_tools_active'] -= 1
                logger.info(f"Unregistered tool: {tool_id}")

            return success

        except ToolNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_id}: {str(e)}")
            raise ToolServiceError(str(e))

    async def search_tools(self, criteria: ToolSearchCriteria) -> List['Tool']:
        """Search tools by criteria."""
        try:
            tools = await self.repository.search_tools(criteria)
            logger.debug(f"Found {len(tools)} tools matching criteria")
            return tools
        except Exception as e:
            logger.error(f"Tool search failed: {str(e)}")
            raise ToolServiceError(str(e))

    # === Tool Execution Operations ===

    async def execute_tool(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute tool capability with full orchestration."""
        start_time = datetime.utcnow()

        try:
            # Get tool from registry
            tool = self.tool_registry.get_tool(request.tool_id)
            if not tool:
                raise ToolNotFoundError(f"Tool {request.tool_id} not found in registry")

            # Create execution record
            execution_data = {
                'id': request.execution_id or str(uuid.uuid4()),
                'tool_id': request.tool_id,
                'capability_name': request.capability_name,
                'parameters': request.parameters,
                'context': request.context,
                'user_id': request.user_id,
                'project_id': request.project_id,
                'session_id': request.session_id,
                'priority': request.priority,
                'status': ExecutionStatus.QUEUED.value,
                'requested_at': datetime.utcnow()
            }

            execution_record = await self.repository.create_tool_execution(execution_data)

            try:
                # Execute using tool executor
                result = await self.tool_executor.execute_tool(tool, request)

                # Update execution record
                execution_updates = {
                    'status': result.status,
                    'result': result.result,
                    'error': result.error,
                    'execution_time': result.execution_time,
                    'resource_usage': result.resource_usage,
                    'completed_at': datetime.utcnow()
                }

                await self.repository.update_tool_execution(
                    execution_record.id,
                    execution_updates
                )

                # Update statistics
                self.service_stats['total_executions'] += 1
                if result.status != 'success':
                    self.service_stats['total_execution_failures'] += 1

                execution_time = (datetime.utcnow() - start_time).total_seconds()
                self._update_response_time_stats(execution_time)

                logger.info(
                    f"Executed tool {request.tool_id}.{request.capability_name}: "
                    f"{result.status} ({execution_time:.2f}s)"
                )

                return result

            except Exception as e:
                # Update execution record with failure
                execution_updates = {
                    'status': ExecutionStatus.FAILED.value,
                    'error': str(e),
                    'completed_at': datetime.utcnow()
                }
                await self.repository.update_tool_execution(
                    execution_record.id,
                    execution_updates
                )
                raise

        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            self.service_stats['total_execution_failures'] += 1
            raise ToolExecutionError(str(e))

    async def get_tool_capabilities(self, tool_id: str) -> List[ToolCapability]:
        """Get tool capabilities."""
        try:
            tool = self.tool_registry.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"Tool {tool_id} not found")

            capabilities = await tool.get_capabilities()
            return capabilities

        except Exception as e:
            logger.error(f"Failed to get capabilities for tool {tool_id}: {str(e)}")
            raise ToolServiceError(str(e))

    async def health_check_tool(self, tool_id: str) -> ToolHealthCheck:
        """Check tool health status."""
        try:
            tool = self.tool_registry.get_tool(tool_id)
            if not tool:
                raise ToolNotFoundError(f"Tool {tool_id} not found")

            health_check = await tool.health_check()
            return health_check

        except Exception as e:
            logger.error(f"Health check failed for tool {tool_id}: {str(e)}")
            raise ToolServiceError(str(e))

    async def health_check_all_tools(self) -> Dict[str, ToolHealthCheck]:
        """Health check all registered tools."""
        try:
            health_results = await self.tool_registry.health_check_all()
            return health_results
        except Exception as e:
            logger.error(f"Failed to health check all tools: {str(e)}")
            raise ToolServiceError(str(e))

    # === Analytics and Monitoring ===

    async def get_tool_analytics(self, tool_id: str) -> ToolAnalytics:
        """Get comprehensive tool analytics."""
        try:
            # Check cache
            cache_key = f"analytics_{tool_id}"
            if cache_key in self._analytics_cache:
                cached_analytics, cached_time = self._analytics_cache[cache_key]
                if (datetime.utcnow() - cached_time).total_seconds() < self._cache_ttl:
                    return cached_analytics

            # Get analytics from repository
            analytics_data = await self.repository.get_tool_analytics(tool_id)

            # Get current health status
            try:
                health_check = await self.health_check_tool(tool_id)
                health_status = health_check.status
            except:
                health_status = ToolStatus.UNAVAILABLE

            # Create analytics object
            analytics = ToolAnalytics(
                tool_id=tool_id,
                health_status=health_status,
                **analytics_data
            )

            # Cache result
            self._analytics_cache[cache_key] = (analytics, datetime.utcnow())

            return analytics

        except Exception as e:
            logger.error(f"Failed to get analytics for tool {tool_id}: {str(e)}")
            raise ToolServiceError(str(e))

    async def get_tool_executions(
        self,
        tool_id: str,
        limit: int = 50
    ) -> List['ToolExecution']:
        """Get tool execution history."""
        try:
            executions = await self.repository.get_tool_executions(tool_id, limit)
            return executions
        except Exception as e:
            logger.error(f"Failed to get executions for tool {tool_id}: {str(e)}")
            raise ToolServiceError(str(e))

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service-level statistics."""
        executor_stats = self.tool_executor.get_executor_stats()

        return {
            'service_stats': self.service_stats,
            'executor_stats': executor_stats,
            'registered_tools': len(self.tool_registry.tools),
            'cache_size': len(self._analytics_cache) + len(self._tool_cache),
            'uptime': datetime.utcnow().isoformat()
        }

    # === Template Management ===

    async def create_tool_template(
        self,
        template_id: str,
        name: str,
        description: str,
        tool_type: ToolType,
        configuration_template: Dict[str, Any],
        capability_templates: List[Dict[str, Any]] = None,
        tags: List[str] = None,
        user_id: Optional[str] = None
    ) -> ToolTemplate:
        """Create reusable tool template."""
        try:
            template_data = {
                'template_id': template_id,
                'name': name,
                'description': description,
                'tool_type': tool_type,
                'configuration_template': configuration_template,
                'capability_templates': capability_templates or [],
                'tags': tags or [],
                'created_by': user_id,
                'created_at': datetime.utcnow(),
                'usage_count': 0
            }

            template = await self.repository.create_tool_template(template_data)

            self.service_stats['total_templates_created'] += 1

            logger.info(f"Created tool template: {template_id}")
            return template

        except Exception as e:
            logger.error(f"Failed to create tool template: {str(e)}")
            raise ToolServiceError(str(e))

    async def get_tool_templates(
        self,
        tool_type: Optional[ToolType] = None
    ) -> List[ToolTemplate]:
        """Get available tool templates."""
        try:
            templates = await self.repository.get_tool_templates(tool_type)
            return templates
        except Exception as e:
            logger.error(f"Failed to get tool templates: {str(e)}")
            raise ToolServiceError(str(e))

    async def create_tool_from_template(
        self,
        template_id: str,
        tool_id: str,
        name: str,
        customizations: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> 'Tool':
        """Create tool from template with customizations."""
        try:
            # Get template
            templates = await self.get_tool_templates()
            template = next(
                (t for t in templates if t.template_id == template_id), None)

            if not template:
                raise ToolServiceError(f"Template {template_id} not found")

            # Build configuration from template
            config_template = template.configuration_template.copy()
            if customizations:
                config_template.update(customizations)

            # Build capabilities from template
            capabilities = []
            for cap_template in template.capability_templates:
                capabilities.append(cap_template)

            # Create tool request
            tool_request = ToolCreateRequest(
                tool_id=tool_id,
                name=name,
                tool_type=template.tool_type,
                description=f"Created from template: {template.name}",
                **config_template,
                capabilities=capabilities,
                tags=template.tags,
                user_id=user_id,
                project_id=project_id
            )

            # Register tool
            tool = await self.register_tool(tool_request)

            # Update template usage count
            template.usage_count += 1

            logger.info(f"Created tool {tool_id} from template {template_id}")
            return tool

        except Exception as e:
            logger.error(f"Failed to create tool from template {template_id}: {str(e)}")
            raise ToolServiceError(str(e))

    # === Integration Operations ===

    async def get_tools_for_agent(self, agent_id: str) -> List['Tool']:
        """Get tools available to a specific agent."""
        try:
            # This would integrate with agent permissions/configuration
            # For now, return all active tools
            criteria = ToolSearchCriteria(is_active=True, limit=100)
            tools = await self.search_tools(criteria)
            return tools
        except Exception as e:
            logger.error(f"Failed to get tools for agent {agent_id}: {str(e)}")
            raise ToolServiceError(str(e))

    async def get_tools_by_capability(self, capability_name: str) -> List['Tool']:
        """Get tools that support a specific capability."""
        try:
            criteria = ToolSearchCriteria(
                capabilities=[capability_name],
                is_active=True,
                limit=100
            )
            tools = await self.search_tools(criteria)
            return tools
        except Exception as e:
            logger.error(
                f"Failed to get tools by capability {capability_name}: {str(e)}")
            raise ToolServiceError(str(e))

    # === Lifecycle Management ===

    async def start_tool_service(self) -> None:
        """Start the tool service."""
        try:
            await self.tool_executor.start()
            logger.info("Tool service started")
        except Exception as e:
            logger.error(f"Failed to start tool service: {str(e)}")
            raise ToolServiceError(str(e))

    async def stop_tool_service(self) -> None:
        """Stop the tool service."""
        try:
            await self.tool_executor.stop()
            logger.info("Tool service stopped")
        except Exception as e:
            logger.error(f"Failed to stop tool service: {str(e)}")
            raise ToolServiceError(str(e))

    # === Private Helper Methods ===

    async def _validate_create_request(self, request: ToolCreateRequest) -> None:
        """Validate tool create request."""
        if not request.tool_id or not request.tool_id.strip():
            raise ValueError("Tool ID is required")

        if not request.name or not request.name.strip():
            raise ValueError("Tool name is required")

        if len(request.tool_id) > 255:
            raise ValueError("Tool ID too long (max 255 characters)")

        # Check for duplicate tool ID
        existing = await self.repository.get_tool_by_id(request.tool_id)
        if existing:
            raise ValueError(f"Tool with ID {request.tool_id} already exists")

        # Validate tool-type specific requirements
        if request.tool_type == ToolType.API and not request.endpoint:
            raise ValueError("API tools require an endpoint")

        if request.tool_type == ToolType.MCP and not request.mcp_server_path:
            raise ValueError("MCP tools require a server path")

        if request.tool_type == ToolType.PLUGIN and not request.plugin_class:
            raise ValueError("Plugin tools require a plugin class")

    async def _build_tool_configuration(self, request: ToolCreateRequest) -> ToolConfiguration:
        """Build tool configuration from request."""

        # Convert capability dictionaries to ToolCapability objects
        capabilities = [self._dict_to_capability(cap) for cap in request.capabilities]

        # Build configuration
        config = ToolBuilder()\
            .with_id(request.tool_id)\
            .with_name(request.name)\
            .with_type(request.tool_type)\
            .with_version(request.version)\
            .with_description(request.description)\
            .with_endpoint(request.endpoint)\
            .with_authentication(request.authentication)\
            .with_headers(request.headers)\
            .with_timeout(request.timeout_seconds)\
            .with_retry_attempts(request.retry_attempts)\
            .with_execution_mode(request.execution_mode)\
            .with_execution_environment(request.execution_environment)\
            .with_concurrent_executions(request.max_concurrent_executions)\
            .with_permissions(request.required_permissions)\
            .with_allowed_users(request.allowed_users)\
            .with_allowed_projects(request.allowed_projects)\
            .with_capabilities(capabilities)\
            .with_tags(request.tags)\
            .with_metadata(request.metadata)\
            .with_plugin_class(request.plugin_class)\
            .with_plugin_config(request.plugin_config)\
            .with_mcp_server(request.mcp_server_path, request.mcp_args, request.mcp_env)\
            .build()

        return config

    def _dict_to_capability(self, cap_dict: Dict[str, Any]) -> ToolCapability:
        """Convert dictionary to ToolCapability."""
        return ToolCapability(
            name=cap_dict.get('name', ''),
            description=cap_dict.get('description', ''),
            input_schema=cap_dict.get('input_schema', {}),
            output_schema=cap_dict.get('output_schema', {}),
            required_permissions=set(cap_dict.get('required_permissions', [])),
            execution_time_estimate=cap_dict.get('execution_time_estimate'),
            resource_requirements=cap_dict.get('resource_requirements', {}),
            dependencies=cap_dict.get('dependencies', []),
            examples=cap_dict.get('examples', [])
        )

    def _dict_to_tool_configuration(self, config_dict: Dict[str, Any]) -> ToolConfiguration:
        """Convert dictionary to ToolConfiguration."""
        # This would convert configuration dictionary back to ToolConfiguration
        # Implementation would depend on the specific structure
        pass

    def _update_response_time_stats(self, response_time: float) -> None:
        """Update service response time statistics."""
        current_avg = self.service_stats['average_tool_response_time']
        total_ops = (self.service_stats['total_tools_registered'] +
                    self.service_stats['total_executions'])

        if total_ops > 0:
            self.service_stats['average_tool_response_time'] = (
                (current_avg * (total_ops - 1) + response_time) / total_ops
            )


# === FACTORY FUNCTION ===

def create_tool_service(
    repository: Optional[ToolRepository] = None,
    tool_executor: Optional[ToolExecutor] = None,
    agent_service: Optional['AgentService'] = None,
    workflow_service: Optional['WorkflowService'] = None
) -> ToolService:
    """Create ToolService with default dependencies."""
    if repository is None:
        repository = MockToolRepository()

    return ToolService(
        repository=repository,
        tool_executor=tool_executor,
        agent_service=agent_service,
        workflow_service=workflow_service
    )


# === EXAMPLE USAGE ===

async def example_tool_service_usage():
    """Example usage of ToolService."""

    # Create service
    service = create_tool_service()

    # Start service
    await service.start_tool_service()

    try:
        # Register GitHub API tool
        github_request = ToolCreateRequest(
            tool_id="github_api",
            name="GitHub API",
            tool_type=ToolType.API,
            description="GitHub REST API integration",
            endpoint="https://api.github.com",
            headers={"Accept": "application/vnd.github.v3+json"},
            capabilities=[
                {
                    "name": "get_repository",
                    "description": "Get repository information",
                    "input_schema": {
                        "type": "object",
                        "required": ["owner", "repo"],
                        "properties": {
                            "owner": {"type": "string"},
                            "repo": {"type": "string"}
                        }
                    },
                    "metadata": {
                        "http_method": "GET",
                        "endpoint": "repos/{owner}/{repo}"
                    }
                }
            ],
            tags=["api", "github", "version_control"],
            user_id="test_user",
            project_id="test_project"
        )

        tool = await service.register_tool(github_request)
        print(f"Registered tool: {tool.id}")

        # Execute tool capability
        execution_request = ToolExecutionRequest(
            tool_id="github_api",
            capability_name="get_repository",
            parameters={"owner": "microsoft", "repo": "vscode"},
            user_id="test_user",
            project_id="test_project"
        )

        result = await service.execute_tool(execution_request)
        print(f"Execution result: {result.status}")

        # Get tool analytics
        analytics = await service.get_tool_analytics("github_api")
        print(f"Analytics: {analytics.total_executions} executions")

        # Get service statistics
        stats = service.get_service_statistics()
        print(f"Service stats: {json.dumps(stats, indent=2, default=str)}")

        # Create template from tool
        template = await service.create_tool_template(
            template_id="github_template",
            name="GitHub API Template",
            description="Reusable GitHub API configuration",
            tool_type=ToolType.API,
            configuration_template={
                "endpoint": "https://api.github.com",
                "headers": {"Accept": "application/vnd.github.v3+json"}
            },
            tags=["template", "api", "github"]
        )
        print(f"Created template: {template.template_id}")

    finally:
        # Stop service
        await service.stop_tool_service()


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_tool_service_usage())
