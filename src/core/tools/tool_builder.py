"""
from abc import abstractmethod
from typing import Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime
from typing import Optional, List, Dict, Any
Tool System Core - Tool Integration Architecture.

The Tool System provides a comprehensive framework for integrating external tools,
APIs, command-line interfaces, and Model Context Protocol (MCP) servers into
the Engine Framework. It enables agents and workflows to interact with external
systems through a unified, pluggable architecture.

Key Features:
- ToolBuilder for declarative tool configuration
- Plugin system for extensible tool integrations
- Unified interface for APIs, CLI tools, and MCP servers
- Tool capability discovery and validation
- Execution routing and result handling
- Security and permission management
- Performance monitoring and caching
- Tool composition and chaining

Architecture:
- Abstract ToolInterface for consistency
- Specialized implementations for different tool types
- ToolRegistry for discovery and management
- ToolExecutor for secure execution
- Plugin architecture for extensibility
- Event-driven tool monitoring

Dependencies:
- External tool APIs and systems
- MCP protocol for model context servers
- Security framework for safe execution
- Async execution for performance
"""
import asyncio
import importlib
import json
import logging
import os
import subprocess
import tempfile
import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Types of tools supported by the system."""
    API = "api"
    CLI = "cli"
    MCP = "mcp"  # Model Context Protocol
    PLUGIN = "plugin"
    FUNCTION = "function"
    WORKFLOW = "workflow"
    COMPOSITE = "composite"


class ToolExecutionMode(Enum):
    """Tool execution modes."""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    STREAMING = "streaming"
    BATCH = "batch"


class ToolStatus(Enum):
    """Tool availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    DEPRECATED = "deprecated"


class PermissionLevel(Enum):
    """Tool permission levels."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    RESTRICTED = "restricted"


class ExecutionEnvironment(Enum):
    """Tool execution environments."""
    SANDBOX = "sandbox"
    CONTAINER = "container"
    HOST = "host"
    REMOTE = "remote"


@dataclass
class ToolCapability:
    """Defines a tool's capability or function."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: Set[str] = field(default_factory=set)
    execution_time_estimate: Optional[float] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolConfiguration:
    """Tool configuration settings."""
    tool_id: str
    name: str
    tool_type: ToolType
    version: str = "1.0.0"
    description: str = ""

    # Connection settings
    endpoint: Optional[str] = None
    authentication: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    retry_attempts: int = 3

    # Execution settings
    execution_mode: ToolExecutionMode = ToolExecutionMode.SYNCHRONOUS
    execution_environment: ExecutionEnvironment = ExecutionEnvironment.SANDBOX
    max_concurrent_executions: int = 5
    rate_limit_requests_per_minute: Optional[int] = None

    # Security settings
    required_permissions: Set[PermissionLevel] = field(default_factory=set)
    allowed_users: Set[str] = field(default_factory=set)
    allowed_projects: Set[str] = field(default_factory=set)
    sandbox_restrictions: Dict[str, Any] = field(default_factory=dict)

    # Capabilities and metadata
    capabilities: List[ToolCapability] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Plugin-specific configuration
    plugin_class: Optional[str] = None
    plugin_config: Dict[str, Any] = field(default_factory=dict)

    # MCP-specific configuration
    mcp_server_path: Optional[str] = None
    mcp_args: List[str] = field(default_factory=list)
    mcp_env: Dict[str, str] = field(default_factory=dict)


@dataclass
class ToolExecutionRequest:
    """Request for tool execution."""
    tool_id: str
    capability_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    execution_id: Optional[str] = None
    priority: int = 0
    timeout_override: Optional[int] = None
    stream_results: bool = False


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    execution_id: str
    tool_id: str
    capability_name: str
    status: str  # "success", "error", "timeout", "cancelled"
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ToolHealthCheck:
    """Tool health check result."""
    tool_id: str
    status: ToolStatus
    response_time: Optional[float] = None
    last_check: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    capabilities_available: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolInterface(ABC):
    """Abstract interface that all tools must implement."""

    def __init__(self, config: ToolConfiguration):
        """Initialize tool with configuration."""
        self.config = config
        self.tool_id = config.tool_id
        self.name = config.name
        self.tool_type = config.tool_type
        self._execution_count = 0
        self._last_health_check = None
        self._status = ToolStatus.AVAILABLE

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the tool and verify connectivity."""
        pass

    @abstractmethod
    async def execute_capability(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ToolExecutionResult:
        """Execute a specific capability of the tool."""
        pass

    @abstractmethod
    async def health_check(self) -> ToolHealthCheck:
        """Check tool health and availability."""
        pass

    @abstractmethod
    async def get_capabilities(self) -> List[ToolCapability]:
        """Get list of available capabilities."""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """Clean up tool resources."""
        pass

    def get_tool_info(self) -> Dict[str, Any]:
        """Get basic tool information."""
        return {
            'tool_id': self.tool_id,
            'name': self.name,
            'type': self.tool_type.value,
            'version': self.config.version,
            'status': self._status.value,
            'execution_count': self._execution_count,
            'last_health_check': self._last_health_check
        }


class APITool(ToolInterface):
    """Tool implementation for REST API integration."""

    def __init__(self, config: ToolConfiguration):
        """Initialize API tool."""
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.endpoint

    async def initialize(self) -> bool:
        """Initialize HTTP session and verify API connectivity."""
        try:
            # Create HTTP session with configuration
            connector = aiohttp.TCPConnector(
                limit=self.config.max_concurrent_executions)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.config.headers
            )

            # Test connectivity with health check
            health = await self.health_check()
            return health.status == ToolStatus.AVAILABLE

        except Exception as e:
            logger.error(f"Failed to initialize API tool {self.tool_id}: {str(e)}")
            self._status = ToolStatus.ERROR
            return False

    async def execute_capability(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ToolExecutionResult:
        """Execute API capability."""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            if not self.session:
                await self.initialize()

            # Find capability
            capabilities = await self.get_capabilities()
            capability = next(
                (c for c in capabilities if c.name == capability_name), None)

            if not capability:
                raise ValueError(f"Capability '{capability_name}' not found")

            # Validate input parameters
            self._validate_parameters(parameters, capability.input_schema)

            # Build API request
            url, method, payload, headers = await self._build_api_request(
                capability, parameters, context
            )

            # Execute API call
            async with self.session.request(
                method=method,
                url=url,
                json=payload if method in ['POST', 'PUT', 'PATCH'] else None,
                params=payload if method == 'GET' else None,
                headers=headers
            ) as response:

                # Process response
                if response.content_type == 'application/json':
                    result = await response.json()
                else:
                    result = await response.text()

                execution_time = (datetime.utcnow() - start_time).total_seconds()
                self._execution_count += 1

                if response.status < 400:
                    return ToolExecutionResult(
                        execution_id=execution_id,
                        tool_id=self.tool_id,
                        capability_name=capability_name,
                        status="success",
                        result=result,
                        execution_time=execution_time
                    )
                else:
                    return ToolExecutionResult(
                        execution_id=execution_id,
                        tool_id=self.tool_id,
                        capability_name=capability_name,
                        status="error",
                        error=f"API error {response.status}: {result}",
                        execution_time=execution_time
                    )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"API tool execution failed: {str(e)}")

            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.tool_id,
                capability_name=capability_name,
                status="error",
                error=str(e),
                execution_time=execution_time
            )

    async def health_check(self) -> ToolHealthCheck:
        """Check API health."""
        start_time = datetime.utcnow()

        try:
            if not self.session:
                await self.initialize()

            # Simple health check endpoint or base URL
            health_url = f"{self.base_url}/health" if self.base_url else None
            if not health_url:
                health_url = self.base_url

            async with self.session.get(health_url) as response:
                response_time = (datetime.utcnow() - start_time).total_seconds()

                if response.status < 400:
                    self._status = ToolStatus.AVAILABLE
                    capabilities = await self.get_capabilities()

                    return ToolHealthCheck(
                        tool_id=self.tool_id,
                        status=ToolStatus.AVAILABLE,
                        response_time=response_time,
                        capabilities_available=[c.name for c in capabilities]
                    )
                else:
                    self._status = ToolStatus.ERROR
                    return ToolHealthCheck(
                        tool_id=self.tool_id,
                        status=ToolStatus.ERROR,
                        response_time=response_time,
                        error_message=f"HTTP {response.status}"
                    )

        except Exception as e:
            self._status = ToolStatus.UNAVAILABLE
            return ToolHealthCheck(
                tool_id=self.tool_id,
                status=ToolStatus.UNAVAILABLE,
                error_message=str(e)
            )

    async def get_capabilities(self) -> List[ToolCapability]:
        """Get API capabilities from configuration."""
        return self.config.capabilities

    async def cleanup(self) -> bool:
        """Clean up HTTP session."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup API tool {self.tool_id}: {str(e)}")
            return False

    async def _build_api_request(
        self,
        capability: ToolCapability,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> tuple[str, str, Dict[str, Any], Dict[str, str]]:
        """Build API request from capability and parameters."""

        # Default to POST for most API operations
        method = capability.metadata.get('http_method', 'POST')

        # Build URL
        url = self.base_url
        if 'endpoint' in capability.metadata:
            url = f"{url.rstrip('/')}/{capability.metadata['endpoint'].lstrip('/')}"

        # Build payload
        payload = parameters.copy()

        # Add context if needed
        if context and 'include_context' in capability.metadata:
            payload['context'] = context

        # Build headers
        headers = self.config.headers.copy()
        if 'additional_headers' in capability.metadata:
            headers.update(capability.metadata['additional_headers'])

        return url, method, payload, headers

    def _validate_parameters(
        self,
        parameters: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> None:
        """Validate parameters against schema."""
        # Simple validation - in production, use jsonschema
        required = schema.get('required', [])
        for field in required:
            if field not in parameters:
                raise ValueError(f"Required parameter '{field}' missing")


class CLITool(ToolInterface):
    """Tool implementation for command-line interface integration."""

    def __init__(self, config: ToolConfiguration):
        """Initialize CLI tool."""
        super().__init__(config)
        self.executable = config.metadata.get('executable')
        self.base_command = config.metadata.get('base_command', [])

    async def initialize(self) -> bool:
        """Initialize CLI tool and verify executable availability."""
        try:
            # Check if executable is available
            if not self.executable:
                raise ValueError("No executable specified for CLI tool")

            # Test basic command execution
            result = await self._execute_command(['--version'], timeout=5)

            if result.returncode == 0:
                self._status = ToolStatus.AVAILABLE
                return True
            else:
                self._status = ToolStatus.ERROR
                return False

        except Exception as e:
            logger.error(f"Failed to initialize CLI tool {self.tool_id}: {str(e)}")
            self._status = ToolStatus.UNAVAILABLE
            return False

    async def execute_capability(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ToolExecutionResult:
        """Execute CLI capability."""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            # Find capability
            capabilities = await self.get_capabilities()
            capability = next(
                (c for c in capabilities if c.name == capability_name), None)

            if not capability:
                raise ValueError(f"Capability '{capability_name}' not found")

            # Build command
            command = await self._build_command(capability, parameters, context)

            # Execute command
            result = await self._execute_command(
                command,
                timeout=self.config.timeout_seconds
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._execution_count += 1

            if result.returncode == 0:
                return ToolExecutionResult(
                    execution_id=execution_id,
                    tool_id=self.tool_id,
                    capability_name=capability_name,
                    status="success",
                    result={
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'return_code': result.returncode
                    },
                    execution_time=execution_time
                )
            else:
                return ToolExecutionResult(
                    execution_id=execution_id,
                    tool_id=self.tool_id,
                    capability_name=capability_name,
                    status="error",
                    error=f"Command failed with code {
                        result.returncode}: {
                        result.stderr}",
                    execution_time=execution_time)

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"CLI tool execution failed: {str(e)}")

            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.tool_id,
                capability_name=capability_name,
                status="error",
                error=str(e),
                execution_time=execution_time
            )

    async def health_check(self) -> ToolHealthCheck:
        """Check CLI tool health."""
        start_time = datetime.utcnow()

        try:
            # Test basic command execution
            result = await self._execute_command(['--help'], timeout=5)
            response_time = (datetime.utcnow() - start_time).total_seconds()

            if result.returncode == 0 or result.returncode == 1:  # Many tools return 1 for --help
                self._status = ToolStatus.AVAILABLE
                capabilities = await self.get_capabilities()

                return ToolHealthCheck(
                    tool_id=self.tool_id,
                    status=ToolStatus.AVAILABLE,
                    response_time=response_time,
                    capabilities_available=[c.name for c in capabilities]
                )
            else:
                self._status = ToolStatus.ERROR
                return ToolHealthCheck(
                    tool_id=self.tool_id,
                    status=ToolStatus.ERROR,
                    response_time=response_time,
                    error_message=f"Command failed: {result.stderr}"
                )

        except Exception as e:
            self._status = ToolStatus.UNAVAILABLE
            return ToolHealthCheck(
                tool_id=self.tool_id,
                status=ToolStatus.UNAVAILABLE,
                error_message=str(e)
            )

    async def get_capabilities(self) -> List[ToolCapability]:
        """Get CLI capabilities from configuration."""
        return self.config.capabilities

    async def cleanup(self) -> bool:
        """Clean up CLI tool resources."""
        # CLI tools typically don't need cleanup
        return True

    async def _build_command(
        self,
        capability: ToolCapability,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> List[str]:
        """Build CLI command from capability and parameters."""

        command = [self.executable] + self.base_command

        # Add capability-specific command parts
        if 'command_template' in capability.metadata:
            template = capability.metadata['command_template']
            # Simple template substitution
            for key, value in parameters.items():
                template = template.replace(f"{{{key}}}", str(value))
            command.extend(template.split())
        else:
            # Build command from parameters
            for key, value in parameters.items():
                if isinstance(value, bool):
                    if value:
                        command.append(f"--{key}")
                else:
                    command.extend([f"--{key}", str(value)])

        return command

    async def _execute_command(
        self,
        command: List[str],
        timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """Execute command safely."""

        # Create safe execution environment
        env = os.environ.copy()
        if self.config.execution_environment == ExecutionEnvironment.SANDBOX:
            # Limit environment for security
            safe_env = {
                'PATH': env.get('PATH', ''),
                'HOME': env.get('HOME', ''),
                'USER': env.get('USER', ''),
                'LANG': env.get('LANG', 'en_US.UTF-8')
            }
            env = safe_env

        # Execute command
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace')
            )

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds")


class MCPTool(ToolInterface):
    """Tool implementation for Model Context Protocol (MCP) server integration."""

    def __init__(self, config: ToolConfiguration):
        """Initialize MCP tool."""
        super().__init__(config)
        self.server_process = None
        self.server_path = config.mcp_server_path
        self.server_args = config.mcp_args
        self.server_env = config.mcp_env

    async def initialize(self) -> bool:
        """Initialize MCP server connection."""
        try:
            if not self.server_path:
                raise ValueError("No MCP server path specified")

            # Start MCP server process
            env = os.environ.copy()
            env.update(self.server_env)

            self.server_process = await asyncio.create_subprocess_exec(
                self.server_path,
                *self.server_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                env=env
            )

            # Test server responsiveness
            await asyncio.sleep(1)  # Give server time to start

            if self.server_process.returncode is None:
                self._status = ToolStatus.AVAILABLE
                return True
            else:
                self._status = ToolStatus.ERROR
                return False

        except Exception as e:
            logger.error(f"Failed to initialize MCP tool {self.tool_id}: {str(e)}")
            self._status = ToolStatus.UNAVAILABLE
            return False

    async def execute_capability(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ToolExecutionResult:
        """Execute MCP capability."""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            if not self.server_process or self.server_process.returncode is not None:
                await self.initialize()

            # Build MCP request
            mcp_request = {
                "method": capability_name,
                "params": parameters,
                "id": execution_id
            }

            # Send request to MCP server
            request_json = json.dumps(mcp_request) + '\n'
            self.server_process.stdin.write(request_json.encode())
            await self.server_process.stdin.drain()

            # Read response
            response_line = await self.server_process.stdout.readline()
            response_data = json.loads(response_line.decode())

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._execution_count += 1

            if 'error' not in response_data:
                return ToolExecutionResult(
                    execution_id=execution_id,
                    tool_id=self.tool_id,
                    capability_name=capability_name,
                    status="success",
                    result=response_data.get('result'),
                    execution_time=execution_time
                )
            else:
                return ToolExecutionResult(
                    execution_id=execution_id,
                    tool_id=self.tool_id,
                    capability_name=capability_name,
                    status="error",
                    error=response_data['error'],
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"MCP tool execution failed: {str(e)}")

            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.tool_id,
                capability_name=capability_name,
                status="error",
                error=str(e),
                execution_time=execution_time
            )

    async def health_check(self) -> ToolHealthCheck:
        """Check MCP server health."""
        start_time = datetime.utcnow()

        try:
            if not self.server_process or self.server_process.returncode is not None:
                await self.initialize()

            # Test with a basic ping-like request
            ping_request = {
                "method": "ping",
                "params": {},
                "id": "health_check"
            }

            request_json = json.dumps(ping_request) + '\n'
            self.server_process.stdin.write(request_json.encode())
            await self.server_process.stdin.drain()

            # Try to read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    self.server_process.stdout.readline(),
                    timeout=5.0
                )
                response_time = (datetime.utcnow() - start_time).total_seconds()

                self._status = ToolStatus.AVAILABLE
                capabilities = await self.get_capabilities()

                return ToolHealthCheck(
                    tool_id=self.tool_id,
                    status=ToolStatus.AVAILABLE,
                    response_time=response_time,
                    capabilities_available=[c.name for c in capabilities]
                )

            except asyncio.TimeoutError:
                self._status = ToolStatus.ERROR
                return ToolHealthCheck(
                    tool_id=self.tool_id,
                    status=ToolStatus.ERROR,
                    error_message="MCP server not responding"
                )

        except Exception as e:
            self._status = ToolStatus.UNAVAILABLE
            return ToolHealthCheck(
                tool_id=self.tool_id,
                status=ToolStatus.UNAVAILABLE,
                error_message=str(e)
            )

    async def get_capabilities(self) -> List[ToolCapability]:
        """Get MCP server capabilities."""
        return self.config.capabilities

    async def cleanup(self) -> bool:
        """Clean up MCP server process."""
        try:
            if self.server_process and self.server_process.returncode is None:
                self.server_process.terminate()
                await self.server_process.wait()
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup MCP tool {self.tool_id}: {str(e)}")
            return False


class PluginTool(ToolInterface):
    """Tool implementation for plugin-based integrations."""

    def __init__(self, config: ToolConfiguration):
        """Initialize plugin tool."""
        super().__init__(config)
        self.plugin_instance = None
        self.plugin_class_path = config.plugin_class
        self.plugin_config = config.plugin_config

    async def initialize(self) -> bool:
        """Initialize plugin instance."""
        try:
            if not self.plugin_class_path:
                raise ValueError("No plugin class specified")

            # Import and instantiate plugin
            module_path, class_name = self.plugin_class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)

            # Create plugin instance
            self.plugin_instance = plugin_class(self.plugin_config)

            # Initialize plugin if it has an init method
            if hasattr(self.plugin_instance, 'initialize'):
                await self.plugin_instance.initialize()

            self._status = ToolStatus.AVAILABLE
            return True

        except Exception as e:
            logger.error(f"Failed to initialize plugin tool {self.tool_id}: {str(e)}")
            self._status = ToolStatus.UNAVAILABLE
            return False

    async def execute_capability(
        self,
        capability_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> ToolExecutionResult:
        """Execute plugin capability."""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            if not self.plugin_instance:
                await self.initialize()

            # Execute plugin method
            if hasattr(self.plugin_instance, capability_name):
                method = getattr(self.plugin_instance, capability_name)

                if asyncio.iscoroutinefunction(method):
                    result = await method(parameters, context)
                else:
                    result = method(parameters, context)

                execution_time = (datetime.utcnow() - start_time).total_seconds()
                self._execution_count += 1

                return ToolExecutionResult(
                    execution_id=execution_id,
                    tool_id=self.tool_id,
                    capability_name=capability_name,
                    status="success",
                    result=result,
                    execution_time=execution_time
                )
            else:
                raise AttributeError(f"Plugin does not have method '{capability_name}'")

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Plugin tool execution failed: {str(e)}")

            return ToolExecutionResult(
                execution_id=execution_id,
                tool_id=self.tool_id,
                capability_name=capability_name,
                status="error",
                error=str(e),
                execution_time=execution_time
            )

    async def health_check(self) -> ToolHealthCheck:
        """Check plugin health."""
        try:
            if not self.plugin_instance:
                await self.initialize()

            # Use plugin's health check if available
            if hasattr(self.plugin_instance, 'health_check'):
                health_result = self.plugin_instance.health_check()
                if asyncio.iscoroutine(health_result):
                    health_result = await health_result

                return ToolHealthCheck(
                    tool_id=self.tool_id,
                    status=ToolStatus.AVAILABLE if health_result else ToolStatus.ERROR,
                    capabilities_available=[c.name for c in await self.get_capabilities()]
                )
            else:
                # Basic health check - plugin exists and is initialized
                self._status = ToolStatus.AVAILABLE
                return ToolHealthCheck(
                    tool_id=self.tool_id,
                    status=ToolStatus.AVAILABLE,
                    capabilities_available=[c.name for c in await self.get_capabilities()]
                )

        except Exception as e:
            self._status = ToolStatus.UNAVAILABLE
            return ToolHealthCheck(
                tool_id=self.tool_id,
                status=ToolStatus.UNAVAILABLE,
                error_message=str(e)
            )

    async def get_capabilities(self) -> List[ToolCapability]:
        """Get plugin capabilities."""
        if self.plugin_instance and hasattr(self.plugin_instance, 'get_capabilities'):
            plugin_capabilities = self.plugin_instance.get_capabilities()
            if asyncio.iscoroutine(plugin_capabilities):
                plugin_capabilities = await plugin_capabilities
            return plugin_capabilities

        return self.config.capabilities

    async def cleanup(self) -> bool:
        """Clean up plugin resources."""
        try:
            if self.plugin_instance and hasattr(self.plugin_instance, 'cleanup'):
                cleanup_result = self.plugin_instance.cleanup()
                if asyncio.iscoroutine(cleanup_result):
                    await cleanup_result
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup plugin tool {self.tool_id}: {str(e)}")
            return False


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, ToolInterface] = {}
        self.tool_configs: Dict[str, ToolConfiguration] = {}
        self.tool_factories: Dict[ToolType, Type[ToolInterface]] = {
            ToolType.API: APITool,
            ToolType.CLI: CLITool,
            ToolType.MCP: MCPTool,
            ToolType.PLUGIN: PluginTool
        }

    async def register_tool(self, config: ToolConfiguration) -> bool:
        """Register a new tool."""
        try:
            # Get tool factory
            if config.tool_type not in self.tool_factories:
                raise ValueError(f"Unsupported tool type: {config.tool_type}")

            factory = self.tool_factories[config.tool_type]

            # Create tool instance
            tool = factory(config)

            # Initialize tool
            if await tool.initialize():
                self.tools[config.tool_id] = tool
                self.tool_configs[config.tool_id] = config
                logger.info(
                    f"Registered tool: {
                        config.tool_id} ({
                        config.tool_type.value})")
                return True
            else:
                logger.error(f"Failed to initialize tool: {config.tool_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to register tool {config.tool_id}: {str(e)}")
            return False

    async def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool."""
        try:
            if tool_id in self.tools:
                tool = self.tools[tool_id]
                await tool.cleanup()
                del self.tools[tool_id]
                del self.tool_configs[tool_id]
                logger.info(f"Unregistered tool: {tool_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister tool {tool_id}: {str(e)}")
            return False

    def get_tool(self, tool_id: str) -> Optional[ToolInterface]:
        """Get tool by ID."""
        return self.tools.get(tool_id)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [tool.get_tool_info() for tool in self.tools.values()]

    def find_tools_by_capability(self, capability_name: str) -> List[ToolInterface]:
        """Find tools that support a specific capability."""
        matching_tools = []
        for tool in self.tools.values():
            # This would be async in real implementation
            capabilities = tool.config.capabilities
            if any(c.name == capability_name for c in capabilities):
                matching_tools.append(tool)
        return matching_tools

    async def health_check_all(self) -> Dict[str, ToolHealthCheck]:
        """Health check all registered tools."""
        results = {}
        for tool_id, tool in self.tools.items():
            results[tool_id] = await tool.health_check()
        return results


class ToolBuilder:
    """Builder for creating tool configurations."""

    def __init__(self):
        """Initialize tool builder."""
        self.reset()

    def reset(self):
        """Reset builder to initial state."""
        self._tool_id = None
        self._name = None
        self._tool_type = None
        self._version = "1.0.0"
        self._description = ""
        self._endpoint = None
        self._authentication = {}
        self._headers = {}
        self._timeout_seconds = 30
        self._retry_attempts = 3
        self._execution_mode = ToolExecutionMode.SYNCHRONOUS
        self._execution_environment = ExecutionEnvironment.SANDBOX
        self._max_concurrent_executions = 5
        self._rate_limit = None
        self._required_permissions = set()
        self._allowed_users = set()
        self._allowed_projects = set()
        self._sandbox_restrictions = {}
        self._capabilities = []
        self._tags = []
        self._metadata = {}
        self._plugin_class = None
        self._plugin_config = {}
        self._mcp_server_path = None
        self._mcp_args = []
        self._mcp_env = {}
        return self

    def with_id(self, tool_id: str):
        """Set tool ID."""
        self._tool_id = tool_id
        return self

    def with_name(self, name: str):
        """Set tool name."""
        self._name = name
        return self

    def with_type(self, tool_type: ToolType):
        """Set tool type."""
        self._tool_type = tool_type
        return self

    def with_version(self, version: str):
        """Set tool version."""
        self._version = version
        return self

    def with_description(self, description: str):
        """Set tool description."""
        self._description = description
        return self

    def with_endpoint(self, endpoint: str):
        """Set API endpoint."""
        self._endpoint = endpoint
        return self

    def with_authentication(self, auth_config: Dict[str, Any]):
        """Set authentication configuration."""
        self._authentication = auth_config
        return self

    def with_headers(self, headers: Dict[str, str]):
        """Set HTTP headers."""
        self._headers = headers
        return self

    def with_timeout(self, seconds: int):
        """Set timeout in seconds."""
        self._timeout_seconds = seconds
        return self

    def with_retry_attempts(self, attempts: int):
        """Set retry attempts."""
        self._retry_attempts = attempts
        return self

    def with_execution_mode(self, mode: ToolExecutionMode):
        """Set execution mode."""
        self._execution_mode = mode
        return self

    def with_execution_environment(self, environment: ExecutionEnvironment):
        """Set execution environment."""
        self._execution_environment = environment
        return self

    def with_concurrent_executions(self, max_concurrent: int):
        """Set max concurrent executions."""
        self._max_concurrent_executions = max_concurrent
        return self

    def with_rate_limit(self, requests_per_minute: int):
        """Set rate limit."""
        self._rate_limit = requests_per_minute
        return self

    def with_permissions(self, permissions: Set[PermissionLevel]):
        """Set required permissions."""
        self._required_permissions = permissions
        return self

    def with_allowed_users(self, users: Set[str]):
        """Set allowed users."""
        self._allowed_users = users
        return self

    def with_allowed_projects(self, projects: Set[str]):
        """Set allowed projects."""
        self._allowed_projects = projects
        return self

    def with_sandbox_restrictions(self, restrictions: Dict[str, Any]):
        """Set sandbox restrictions."""
        self._sandbox_restrictions = restrictions
        return self

    def add_capability(self, capability: ToolCapability):
        """Add a capability."""
        self._capabilities.append(capability)
        return self

    def with_capabilities(self, capabilities: List[ToolCapability]):
        """Set all capabilities."""
        self._capabilities = capabilities
        return self

    def with_tags(self, tags: List[str]):
        """Set tags."""
        self._tags = tags
        return self

    def with_metadata(self, metadata: Dict[str, Any]):
        """Set metadata."""
        self._metadata = metadata
        return self

    def with_plugin_class(self, class_path: str):
        """Set plugin class path."""
        self._plugin_class = class_path
        return self

    def with_plugin_config(self, config: Dict[str, Any]):
        """Set plugin configuration."""
        self._plugin_config = config
        return self

    def with_mcp_server(self,
                        server_path: str,
                        args: List[str] = None,
                        env: Dict[str,
                                  str] = None):
        """Set MCP server configuration."""
        self._mcp_server_path = server_path
        self._mcp_args = args or []
        self._mcp_env = env or {}
        return self

    def build(self) -> ToolConfiguration:
        """Build tool configuration."""
        if not self._tool_id:
            raise ValueError("Tool ID is required")
        if not self._name:
            raise ValueError("Tool name is required")
        if not self._tool_type:
            raise ValueError("Tool type is required")

        config = ToolConfiguration(
            tool_id=self._tool_id,
            name=self._name,
            tool_type=self._tool_type,
            version=self._version,
            description=self._description,
            endpoint=self._endpoint,
            authentication=self._authentication,
            headers=self._headers,
            timeout_seconds=self._timeout_seconds,
            retry_attempts=self._retry_attempts,
            execution_mode=self._execution_mode,
            execution_environment=self._execution_environment,
            max_concurrent_executions=self._max_concurrent_executions,
            rate_limit_requests_per_minute=self._rate_limit,
            required_permissions=self._required_permissions,
            allowed_users=self._allowed_users,
            allowed_projects=self._allowed_projects,
            sandbox_restrictions=self._sandbox_restrictions,
            capabilities=self._capabilities,
            tags=self._tags,
            metadata=self._metadata,
            plugin_class=self._plugin_class,
            plugin_config=self._plugin_config,
            mcp_server_path=self._mcp_server_path,
            mcp_args=self._mcp_args,
            mcp_env=self._mcp_env
        )

        self.reset()
        return config


# === EXAMPLE TOOL IMPLEMENTATIONS ===

async def example_api_tool():
    """Example API tool configuration."""

    # GitHub API tool
    github_capability = ToolCapability(
        name="get_repository",
        description="Get GitHub repository information",
        input_schema={
            "type": "object",
            "required": ["owner", "repo"],
            "properties": {
                "owner": {"type": "string"},
                "repo": {"type": "string"}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "stars": {"type": "integer"}
            }
        },
        metadata={
            "http_method": "GET",
            "endpoint": "repos/{owner}/{repo}"
        }
    )

    config = ToolBuilder()\
        .with_id("github_api")\
        .with_name("GitHub API")\
        .with_type(ToolType.API)\
        .with_endpoint("https://api.github.com")\
        .with_headers({"Accept": "application/vnd.github.v3+json"})\
        .add_capability(github_capability)\
        .with_tags(["api", "github", "version_control"])\
        .build()

    return config


async def example_cli_tool():
    """Example CLI tool configuration."""

    # Git CLI tool
    git_status_capability = ToolCapability(
        name="status",
        description="Get git repository status",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "return_code": {"type": "integer"}
            }
        },
        metadata={
            "command_template": "status --porcelain"
        }
    )

    config = ToolBuilder()\
        .with_id("git_cli")\
        .with_name("Git CLI")\
        .with_type(ToolType.CLI)\
        .with_metadata({"executable": "git"})\
        .add_capability(git_status_capability)\
        .with_tags(["cli", "git", "version_control"])\
        .build()

    return config


async def example_usage():
    """Example usage of tool system."""

    # Create tool registry
    registry = ToolRegistry()

    # Create and register API tool
    api_config = await example_api_tool()
    await registry.register_tool(api_config)

    # Create and register CLI tool
    cli_config = await example_cli_tool()
    await registry.register_tool(cli_config)

    # List all tools
    tools = registry.list_tools()
    print(f"Registered tools: {len(tools)}")

    # Execute API tool capability
    github_tool = registry.get_tool("github_api")
    if github_tool:
        result = await github_tool.execute_capability(
            "get_repository",
            {"owner": "microsoft", "repo": "vscode"}
        )
        print(f"API result: {result.status}")

    # Execute CLI tool capability
    git_tool = registry.get_tool("git_cli")
    if git_tool:
        result = await git_tool.execute_capability(
            "status",
            {"path": "/path/to/repo"}
        )
        print(f"CLI result: {result.status}")

    # Health check all tools
    health_results = await registry.health_check_all()
    for tool_id, health in health_results.items():
        print(f"Tool {tool_id}: {health.status}")


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_usage())
