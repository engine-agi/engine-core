"""
from abc import abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from datetime import datetime
from typing import Optional, List, Dict, Any
Protocol Service - Business Logic Layer for Protocol Management.

The ProtocolService provides comprehensive protocol management functionality,
including command processing, execution orchestration, context management,
and integration with the core ProtocolParser system.

Key Features:
- Protocol lifecycle management (create, update, delete, versioning)
- Command processing and execution orchestration
- Context management and session tracking
- Agent and team coordination for protocol execution
- Performance analytics and usage statistics
- Template management and reusability
- Real-time execution monitoring
- Error handling and recovery mechanisms

Architecture:
- Repository pattern for protocol persistence
- Service layer for business logic coordination
- Integration with ProtocolParser for command processing
- Event-driven updates for real-time monitoring
- Caching for performance optimization

Dependencies:
- ProtocolParser (core command processing)
- AgentService (agent management and execution)
- TeamService (team coordination)
- WorkflowService (workflow orchestration)
- Database models (Protocol, ProtocolExecution, ProtocolSession)
"""
import asyncio
import json
import logging
import uuid
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

# Type checking imports
if TYPE_CHECKING:
    from ..models.agent import Agent
    from ..models.protocol import Protocol, ProtocolExecution, ProtocolSession
    from ..models.team import Team
    from .agent_service import AgentService
    from .team_service import TeamService
    from .workflow_service import WorkflowService

# Core imports
    ProtocolParser, ParsedCommand, CommandContext, ExecutionPlan,
    CommandType, IntentCategory, ContextScope, CommandPriority,
    create_protocol_parser
)

logger = logging.getLogger(__name__)


class ProtocolExecutionStatus(Enum):
    """Protocol execution status."""
    PENDING = "pending"
    PARSING = "parsing"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ProtocolType(Enum):
    """Types of protocols."""
    INTERACTIVE = "interactive"
    BATCH = "batch"
    WORKFLOW = "workflow"
    TEMPLATE = "template"
    SYSTEM = "system"


class SessionStatus(Enum):
    """Protocol session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class ProtocolCreateRequest:
    """Request for creating a new protocol."""
    name: str
    description: str = ""
    protocol_type: ProtocolType = ProtocolType.INTERACTIVE
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    commands: List[str] = field(default_factory=list)
    context_requirements: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_template: bool = False
    timeout_seconds: Optional[int] = None


@dataclass
class ProtocolUpdateRequest:
    """Request for updating an existing protocol."""
    name: Optional[str] = None
    description: Optional[str] = None
    commands: Optional[List[str]] = None
    context_requirements: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    timeout_seconds: Optional[int] = None


@dataclass
class ProtocolExecutionRequest:
    """Request for executing a protocol."""
    protocol_id: str
    commands: Optional[List[str]] = None  # Override protocol commands
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    priority: CommandPriority = CommandPriority.NORMAL
    timeout_seconds: Optional[int] = None
    async_execution: bool = True


@dataclass
class CommandExecutionRequest:
    """Request for executing a single command."""
    command_text: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    protocol_id: Optional[str] = None
    priority: CommandPriority = CommandPriority.NORMAL
    timeout_seconds: Optional[int] = None


@dataclass
class ProtocolSearchCriteria:
    """Criteria for searching protocols."""
    name_pattern: Optional[str] = None
    protocol_type: Optional[ProtocolType] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_template: Optional[bool] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


@dataclass
class ProtocolAnalytics:
    """Protocol performance analytics."""
    protocol_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    median_execution_time: float = 0.0
    command_success_rates: Dict[str, float] = field(default_factory=dict)
    intent_distribution: Dict[str, int] = field(default_factory=dict)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)
    usage_trends: List[Dict[str, Any]] = field(default_factory=list)
    last_execution_at: Optional[datetime] = None


@dataclass
class SessionSummary:
    """Summary of a protocol session."""
    session_id: str
    protocol_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    command_count: int = 0
    successful_commands: int = 0
    failed_commands: int = 0
    context_variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProtocolRepository(ABC):
    """Abstract repository interface for protocol data persistence."""

    @abstractmethod
    async def create_protocol(self, protocol_data: Dict[str, Any]) -> 'Protocol':
        """Create a new protocol."""
        pass

    @abstractmethod
    async def get_protocol_by_id(self, protocol_id: str) -> Optional['Protocol']:
        """Get protocol by ID."""
        pass

    @abstractmethod
    async def update_protocol(self, protocol_id: str, updates: Dict[str, Any]) -> Optional['Protocol']:
        """Update protocol."""
        pass

    @abstractmethod
    async def delete_protocol(self, protocol_id: str) -> bool:
        """Delete protocol."""
        pass

    @abstractmethod
    async def search_protocols(self, criteria: ProtocolSearchCriteria) -> List['Protocol']:
        """Search protocols by criteria."""
        pass

    @abstractmethod
    async def create_protocol_execution(self, execution_data: Dict[str, Any]) -> 'ProtocolExecution':
        """Create protocol execution record."""
        pass

    @abstractmethod
    async def update_protocol_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> Optional['ProtocolExecution']:
        """Update protocol execution."""
        pass

    @abstractmethod
    async def get_protocol_executions(
        self,
        protocol_id: str,
        limit: int = 50
    ) -> List['ProtocolExecution']:
        """Get protocol executions."""
        pass

    @abstractmethod
    async def create_session(self, session_data: Dict[str, Any]) -> 'ProtocolSession':
        """Create protocol session."""
        pass

    @abstractmethod
    async def get_session_by_id(self, session_id: str) -> Optional['ProtocolSession']:
        """Get session by ID."""
        pass

    @abstractmethod
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional['ProtocolSession']:
        """Update session."""
        pass

    @abstractmethod
    async def get_execution_analytics(self, protocol_id: str) -> Dict[str, Any]:
        """Get execution analytics for protocol."""
        pass


class MockProtocolRepository(ProtocolRepository):
    """Mock repository implementation for development/testing."""

    def __init__(self):
        self.protocols: Dict[str, Dict[str, Any]] = {}
        self.executions: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def create_protocol(self, protocol_data: Dict[str, Any]) -> 'Protocol':
        """Create a new protocol."""
        protocol_id = protocol_data.get('id', str(uuid.uuid4()))
        protocol_data['id'] = protocol_id
        protocol_data['created_at'] = datetime.utcnow()
        protocol_data['updated_at'] = datetime.utcnow()
        protocol_data['version'] = 1

        self.protocols[protocol_id] = protocol_data.copy()

        class MockProtocol:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocol(protocol_data)

    async def get_protocol_by_id(self, protocol_id: str) -> Optional['Protocol']:
        """Get protocol by ID."""
        if protocol_id not in self.protocols:
            return None

        class MockProtocol:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocol(self.protocols[protocol_id])

    async def update_protocol(self, protocol_id: str, updates: Dict[str, Any]) -> Optional['Protocol']:
        """Update protocol."""
        if protocol_id not in self.protocols:
            return None

        self.protocols[protocol_id].update(updates)
        self.protocols[protocol_id]['updated_at'] = datetime.utcnow()
        self.protocols[protocol_id]['version'] = self.protocols[protocol_id].get(
            'version', 1) + 1

        class MockProtocol:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocol(self.protocols[protocol_id])

    async def delete_protocol(self, protocol_id: str) -> bool:
        """Delete protocol."""
        if protocol_id in self.protocols:
            del self.protocols[protocol_id]
            # Delete related executions
            executions_to_delete = [
                eid for eid, exec_data in self.executions.items()
                if exec_data.get('protocol_id') == protocol_id
            ]
            for eid in executions_to_delete:
                del self.executions[eid]
            return True
        return False

    async def search_protocols(self, criteria: ProtocolSearchCriteria) -> List['Protocol']:
        """Search protocols by criteria."""
        results = []

        for protocol_id, protocol_data in self.protocols.items():
            # Apply filters
            if criteria.name_pattern and criteria.name_pattern not in protocol_data.get('name', ''):
                continue
            if criteria.protocol_type and protocol_data.get('protocol_type') != criteria.protocol_type.value:
                continue
            if criteria.project_id and protocol_data.get('project_id') != criteria.project_id:
                continue
            if criteria.user_id and protocol_data.get('user_id') != criteria.user_id:
                continue
            if criteria.is_template is not None and protocol_data.get('is_template') != criteria.is_template:
                continue
            if criteria.is_active is not None and protocol_data.get('is_active') != criteria.is_active:
                continue
            if criteria.tags:
                protocol_tags = set(protocol_data.get('tags', []))
                if not set(criteria.tags).issubset(protocol_tags):
                    continue

            class MockProtocol:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)

            results.append(MockProtocol(protocol_data))

        return results[criteria.offset:criteria.offset + criteria.limit]

    async def create_protocol_execution(self, execution_data: Dict[str, Any]) -> 'ProtocolExecution':
        """Create protocol execution record."""
        execution_id = execution_data.get('id', str(uuid.uuid4()))
        execution_data['id'] = execution_id
        execution_data['created_at'] = datetime.utcnow()
        execution_data['status'] = ProtocolExecutionStatus.PENDING.value

        self.executions[execution_id] = execution_data.copy()

        class MockProtocolExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocolExecution(execution_data)

    async def update_protocol_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> Optional['ProtocolExecution']:
        """Update protocol execution."""
        if execution_id not in self.executions:
            return None

        self.executions[execution_id].update(updates)
        self.executions[execution_id]['updated_at'] = datetime.utcnow()

        class MockProtocolExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocolExecution(self.executions[execution_id])

    async def get_protocol_executions(
        self,
        protocol_id: str,
        limit: int = 50
    ) -> List['ProtocolExecution']:
        """Get protocol executions."""
        executions = [
            exec_data for exec_data in self.executions.values()
            if exec_data.get('protocol_id') == protocol_id
        ]

        executions.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)

        class MockProtocolExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return [MockProtocolExecution(e) for e in executions[:limit]]

    async def create_session(self, session_data: Dict[str, Any]) -> 'ProtocolSession':
        """Create protocol session."""
        session_id = session_data.get('id', str(uuid.uuid4()))
        session_data['id'] = session_id
        session_data['created_at'] = datetime.utcnow()
        session_data['last_activity'] = datetime.utcnow()
        session_data['status'] = SessionStatus.ACTIVE.value

        self.sessions[session_id] = session_data.copy()

        class MockProtocolSession:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocolSession(session_data)

    async def get_session_by_id(self, session_id: str) -> Optional['ProtocolSession']:
        """Get session by ID."""
        if session_id not in self.sessions:
            return None

        class MockProtocolSession:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocolSession(self.sessions[session_id])

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional['ProtocolSession']:
        """Update session."""
        if session_id not in self.sessions:
            return None

        self.sessions[session_id].update(updates)
        self.sessions[session_id]['last_activity'] = datetime.utcnow()

        class MockProtocolSession:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockProtocolSession(self.sessions[session_id])

    async def get_execution_analytics(self, protocol_id: str) -> Dict[str, Any]:
        """Get execution analytics for protocol."""
        executions = [
            exec_data for exec_data in self.executions.values()
            if exec_data.get('protocol_id') == protocol_id
        ]

        if not executions:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_execution_time': 0.0
            }

        successful = sum(1 for e in executions if e.get('status')
                         == ProtocolExecutionStatus.COMPLETED.value)
        failed = sum(1 for e in executions if e.get('status')
                     == ProtocolExecutionStatus.FAILED.value)

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


class ProtocolService:
    """
    Service layer for protocol management and command processing.

    Provides comprehensive protocol lifecycle management including:
    - Protocol CRUD operations with validation
    - Command processing and execution orchestration
    - Session management and context tracking
    - Integration with Agent and Team services
    - Performance monitoring and analytics
    - Template management and versioning
    - Real-time execution tracking
    """

    def __init__(
        self,
        repository: ProtocolRepository,
        protocol_parser: Optional[ProtocolParser] = None,
        agent_service: Optional['AgentService'] = None,
        team_service: Optional['TeamService'] = None,
        workflow_service: Optional['WorkflowService'] = None
    ):
        """Initialize protocol service."""
        self.repository = repository
        self.protocol_parser = protocol_parser or create_protocol_parser()
        self.agent_service = agent_service
        self.team_service = team_service
        self.workflow_service = workflow_service

        # Active sessions and executions
        self.active_sessions: Dict[str, SessionSummary] = {}
        self.active_executions: Dict[str, Dict[str, Any]] = {}

        # Performance cache
        self._analytics_cache = {}
        self._session_cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Statistics
        self.service_stats = {
            'total_protocols_created': 0,
            'total_commands_processed': 0,
            'total_executions_started': 0,
            'total_executions_completed': 0,
            'total_execution_failures': 0,
            'active_sessions_count': 0,
            'average_command_parse_time': 0.0,
            'average_execution_time': 0.0
        }

    # === Protocol CRUD Operations ===

    async def create_protocol(self, request: ProtocolCreateRequest) -> 'Protocol':
        """Create a new protocol with validation."""
        start_time = datetime.utcnow()

        try:
            # Validate request
            await self._validate_create_request(request)

            # Prepare protocol data
            protocol_data = {
                'name': request.name,
                'description': request.description,
                'protocol_type': request.protocol_type.value,
                'project_id': request.project_id,
                'user_id': request.user_id,
                'commands': request.commands,
                'context_requirements': request.context_requirements,
                'tags': request.tags,
                'metadata': request.metadata,
                'is_template': request.is_template,
                'timeout_seconds': request.timeout_seconds,
                'is_active': True,
                'execution_count': 0
            }

            # Validate commands if provided
            if request.commands:
                await self._validate_protocol_commands(request.commands)

            # Create protocol
            protocol = await self.repository.create_protocol(protocol_data)

            # Update stats
            self.service_stats['total_protocols_created'] += 1

            # Update response time stats
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time_stats(response_time)

            logger.info(f"Created protocol {protocol.id}: {protocol.name}")
            return protocol

        except Exception as e:
            logger.error(f"Failed to create protocol: {str(e)}")
            raise

    async def get_protocol(self, protocol_id: str) -> 'Protocol':
        """Get protocol by ID."""
        protocol = await self.repository.get_protocol_by_id(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {protocol_id} not found")
        return protocol

    async def update_protocol(self, protocol_id: str, request: ProtocolUpdateRequest) -> 'Protocol':
        """Update protocol with validation."""
        start_time = datetime.utcnow()

        try:
            # Check if protocol exists
            existing = await self.get_protocol(protocol_id)

            # Prepare updates
            updates = {}
            if request.name is not None:
                updates['name'] = request.name
            if request.description is not None:
                updates['description'] = request.description
            if request.commands is not None:
                # Validate commands
                await self._validate_protocol_commands(request.commands)
                updates['commands'] = request.commands
            if request.context_requirements is not None:
                updates['context_requirements'] = request.context_requirements
            if request.tags is not None:
                updates['tags'] = request.tags
            if request.metadata is not None:
                updates['metadata'] = request.metadata
            if request.is_active is not None:
                updates['is_active'] = request.is_active
            if request.timeout_seconds is not None:
                updates['timeout_seconds'] = request.timeout_seconds

            # Update protocol
            protocol = await self.repository.update_protocol(protocol_id, updates)
            if not protocol:
                raise ValueError(f"Protocol {protocol_id} not found")

            # Clear cache
            if protocol_id in self._analytics_cache:
                del self._analytics_cache[protocol_id]

            # Update response time stats
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time_stats(response_time)

            logger.info(f"Updated protocol {protocol_id}")
            return protocol

        except Exception as e:
            logger.error(f"Failed to update protocol {protocol_id}: {str(e)}")
            raise

    async def delete_protocol(self, protocol_id: str) -> bool:
        """Delete protocol and related data."""
        try:
            # Check if protocol has active executions
            active_executions = [
                eid for eid, exec_data in self.active_executions.items()
                if exec_data.get('protocol_id') == protocol_id
            ]

            if active_executions:
                raise ValueError(
                    f"Cannot delete protocol {protocol_id} with active executions")

            # Delete protocol
            success = await self.repository.delete_protocol(protocol_id)
            if success:
                # Clear cache
                if protocol_id in self._analytics_cache:
                    del self._analytics_cache[protocol_id]
                logger.info(f"Deleted protocol {protocol_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete protocol {protocol_id}: {str(e)}")
            raise

    async def search_protocols(self, criteria: ProtocolSearchCriteria) -> List['Protocol']:
        """Search protocols by criteria."""
        try:
            protocols = await self.repository.search_protocols(criteria)
            logger.debug(f"Found {len(protocols)} protocols matching criteria")
            return protocols
        except Exception as e:
            logger.error(f"Protocol search failed: {str(e)}")
            raise

    # === Command Processing Operations ===

    async def process_command(
        self,
        request: CommandExecutionRequest
    ) -> Dict[str, Any]:
        """Process a single command using protocol parser."""
        start_time = datetime.utcnow()
        execution_id = str(uuid.uuid4())

        try:
            # Create or get session
            session = await self._get_or_create_session(request.session_id, request.context)

            # Create command context
            context = CommandContext(
                user_id=session.user_id,
                session_id=session.session_id,
                project_id=session.project_id,
                variables=session.context_variables,
                history=session.metadata.get('command_history', [])
            )

            # Override context with request data
            if request.context:
                context.variables.update(request.context)

            # Parse command
            parsed_command = await self.protocol_parser.parse_command(request.command_text, context)

            # Update stats
            self.service_stats['total_commands_processed'] += 1
            parse_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_parse_time_stats(parse_time)

            # Create execution record
            execution_data = {
                'id': execution_id,
                'protocol_id': request.protocol_id,
                'session_id': session.session_id,
                'command_text': request.command_text,
                'parsed_command': parsed_command.to_dict(),
                'status': ProtocolExecutionStatus.PARSING.value,
                'priority': request.priority.value,
                'timeout_seconds': request.timeout_seconds
            }

            execution_record = await self.repository.create_protocol_execution(execution_data)

            # Execute command if valid
            if parsed_command.is_valid:
                result = await self._execute_parsed_command(
                    parsed_command, context, execution_id, session
                )
            else:
                result = {
                    'execution_id': execution_id,
                    'status': 'failed',
                    'error': 'Command parsing failed',
                    'errors': parsed_command.validation_errors,
                    'suggestions': parsed_command.suggestions
                }

            # Update session
            await self._update_session_with_command_result(session, parsed_command, result)

            logger.info(
                f"Processed command: {request.command_text[:50]}... -> {result.get('status', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Command processing failed: {str(e)}")
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'command_text': request.command_text
            }

    async def execute_protocol(
        self,
        request: ProtocolExecutionRequest
    ) -> Dict[str, Any]:
        """Execute a complete protocol (sequence of commands)."""
        start_time = datetime.utcnow()
        execution_id = str(uuid.uuid4())

        try:
            # Get protocol
            protocol = await self.get_protocol(request.protocol_id)
            if not protocol.is_active:
                raise ValueError(f"Protocol {request.protocol_id} is not active")

            # Use provided commands or protocol commands
            commands = request.commands or protocol.commands
            if not commands:
                raise ValueError("No commands to execute")

            # Create or get session
            session = await self._get_or_create_session(request.session_id, request.context)

            # Create execution record
            execution_data = {
                'id': execution_id,
                'protocol_id': request.protocol_id,
                'session_id': session.session_id,
                'commands': commands,
                'status': ProtocolExecutionStatus.EXECUTING.value,
                'priority': request.priority.value,
                'timeout_seconds': request.timeout_seconds,
                'async_execution': request.async_execution
            }

            execution_record = await self.repository.create_protocol_execution(execution_data)
            self.active_executions[execution_id] = execution_data

            # Update stats
            self.service_stats['total_executions_started'] += 1

            try:
                if request.async_execution:
                    # Start async execution
                    asyncio.create_task(
                        self._execute_protocol_async(
                            execution_id, protocol, commands, session)
                    )

                    return {
                        'execution_id': execution_id,
                        'status': 'started',
                        'async': True,
                        'protocol_id': request.protocol_id,
                        'command_count': len(commands)
                    }
                else:
                    # Execute synchronously
                    result = await self._execute_protocol_sync(execution_id, protocol, commands, session)
                    return result

            finally:
                # Clean up active execution if sync
                if not request.async_execution and execution_id in self.active_executions:
                    del self.active_executions[execution_id]

        except Exception as e:
            logger.error(f"Protocol execution failed: {str(e)}")

            # Update execution record with failure
            try:
                execution_updates = {
                    'status': ProtocolExecutionStatus.FAILED.value,
                    'completed_at': datetime.utcnow(),
                    'error_message': str(e)
                }
                await self.repository.update_protocol_execution(execution_id, execution_updates)
            except:
                pass

            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'protocol_id': request.protocol_id
            }

    # === Session Management ===

    async def create_session(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        protocol_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SessionSummary:
        """Create a new protocol session."""

        session_id = str(uuid.uuid4())

        session_data = {
            'id': session_id,
            'protocol_id': protocol_id,
            'user_id': user_id,
            'project_id': project_id,
            'context_variables': context or {},
            'metadata': {
                'command_history': [],
                'execution_history': []
            }
        }

        # Create in repository
        db_session = await self.repository.create_session(session_data)

        # Create session summary
        session_summary = SessionSummary(
            session_id=session_id,
            protocol_id=protocol_id,
            user_id=user_id,
            project_id=project_id,
            context_variables=context or {}
        )

        # Cache session
        self.active_sessions[session_id] = session_summary
        self.service_stats['active_sessions_count'] = len(self.active_sessions)

        logger.info(f"Created session {session_id}")
        return session_summary

    async def get_session(self, session_id: str) -> SessionSummary:
        """Get session by ID."""

        # Check cache first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        # Get from repository
        db_session = await self.repository.get_session_by_id(session_id)
        if not db_session:
            raise ValueError(f"Session {session_id} not found")

        # Create session summary
        session_summary = SessionSummary(
            session_id=session_id,
            protocol_id=db_session.protocol_id,
            user_id=db_session.user_id,
            project_id=db_session.project_id,
            status=SessionStatus(db_session.status),
            created_at=db_session.created_at,
            last_activity=db_session.last_activity,
            context_variables=db_session.context_variables,
            metadata=db_session.metadata or {}
        )

        # Cache if active
        if session_summary.status == SessionStatus.ACTIVE:
            self.active_sessions[session_id] = session_summary

        return session_summary

    async def update_session_context(
        self,
        session_id: str,
        context_updates: Dict[str, Any]
    ) -> SessionSummary:
        """Update session context variables."""

        session = await self.get_session(session_id)
        session.context_variables.update(context_updates)
        session.last_activity = datetime.utcnow()

        # Update repository
        updates = {
            'context_variables': session.context_variables,
            'last_activity': session.last_activity
        }
        await self.repository.update_session(session_id, updates)

        # Update cache
        self.active_sessions[session_id] = session

        return session

    async def close_session(self, session_id: str) -> bool:
        """Close a protocol session."""

        try:
            session = await self.get_session(session_id)
            session.status = SessionStatus.COMPLETED

            # Update repository
            updates = {'status': SessionStatus.COMPLETED.value}
            await self.repository.update_session(session_id, updates)

            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                self.service_stats['active_sessions_count'] = len(self.active_sessions)

            logger.info(f"Closed session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to close session {session_id}: {str(e)}")
            return False

    # === Analytics and Monitoring ===

    async def get_protocol_analytics(self, protocol_id: str) -> ProtocolAnalytics:
        """Get comprehensive protocol analytics."""
        try:
            # Check cache
            cache_key = f"analytics_{protocol_id}"
            if cache_key in self._analytics_cache:
                cached_data, cached_time = self._analytics_cache[cache_key]
                if (datetime.utcnow() - cached_time).total_seconds() < self._cache_ttl:
                    return cached_data

            # Get analytics from repository
            analytics_data = await self.repository.get_execution_analytics(protocol_id)

            # Create analytics object
            analytics = ProtocolAnalytics(
                protocol_id=protocol_id,
                **analytics_data
            )

            # Cache result
            self._analytics_cache[cache_key] = (analytics, datetime.utcnow())

            return analytics

        except Exception as e:
            logger.error(
                f"Failed to get analytics for protocol {protocol_id}: {str(e)}")
            raise

    async def get_protocol_executions(
        self,
        protocol_id: str,
        limit: int = 50
    ) -> List['ProtocolExecution']:
        """Get protocol execution history."""
        try:
            executions = await self.repository.get_protocol_executions(protocol_id, limit)
            return executions
        except Exception as e:
            logger.error(
                f"Failed to get executions for protocol {protocol_id}: {str(e)}")
            raise

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        try:
            if execution_id in self.active_executions:
                execution_data = self.active_executions[execution_id]
                return {
                    'execution_id': execution_id,
                    'status': execution_data.get('status', 'unknown'),
                    'is_active': True,
                    'protocol_id': execution_data.get('protocol_id'),
                    'progress': execution_data.get('progress', {})
                }

            return {
                'execution_id': execution_id,
                'status': 'not_found',
                'is_active': False
            }

        except Exception as e:
            logger.error(f"Failed to get execution status {execution_id}: {str(e)}")
            raise

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service-level statistics."""
        parser_stats = self.protocol_parser.get_parser_statistics()

        return {
            'service_stats': self.service_stats,
            'parser_stats': parser_stats['parser_stats'],
            'active_executions': len(self.active_executions),
            'active_sessions': len(self.active_sessions),
            'cache_size': len(self._analytics_cache) + len(self._session_cache),
            'supported_intents': parser_stats.get('supported_intents', []),
            'uptime': datetime.utcnow().isoformat()
        }

    # === Template Management ===

    async def create_template_from_protocol(
        self,
        protocol_id: str,
        template_name: str,
        template_description: str = ""
    ) -> 'Protocol':
        """Create reusable template from existing protocol."""
        try:
            # Get source protocol
            protocol = await self.get_protocol(protocol_id)

            # Create template request
            template_request = ProtocolCreateRequest(
                name=template_name,
                description=template_description,
                protocol_type=ProtocolType.TEMPLATE,
                project_id=protocol.project_id,
                user_id=protocol.user_id,
                commands=protocol.commands,
                context_requirements=protocol.context_requirements,
                tags=protocol.tags + ['template'],
                metadata={**protocol.metadata, 'source_protocol_id': protocol_id},
                is_template=True,
                timeout_seconds=protocol.timeout_seconds
            )

            # Create template
            template = await self.create_protocol(template_request)
            logger.info(f"Created template {template.id} from protocol {protocol_id}")
            return template

        except Exception as e:
            logger.error(
                f"Failed to create template from protocol {protocol_id}: {str(e)}")
            raise

    async def create_protocol_from_template(
        self,
        template_id: str,
        protocol_name: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> 'Protocol':
        """Create protocol from template with customizations."""
        try:
            # Get template
            template = await self.get_protocol(template_id)
            if not template.is_template:
                raise ValueError(f"Protocol {template_id} is not a template")

            # Apply customizations
            commands = template.commands.copy()
            context_requirements = template.context_requirements.copy()
            metadata = template.metadata.copy()

            if customizations:
                if 'commands' in customizations:
                    commands.extend(customizations['commands'])
                if 'context_requirements' in customizations:
                    context_requirements.update(customizations['context_requirements'])
                if 'metadata' in customizations:
                    metadata.update(customizations['metadata'])

            # Create protocol request
            protocol_request = ProtocolCreateRequest(
                name=protocol_name,
                description=f"Created from template: {template.name}",
                protocol_type=ProtocolType.INTERACTIVE,
                project_id=template.project_id,
                user_id=template.user_id,
                commands=commands,
                context_requirements=context_requirements,
                tags=template.tags,
                metadata=metadata,
                is_template=False,
                timeout_seconds=template.timeout_seconds
            )

            # Create protocol
            protocol = await self.create_protocol(protocol_request)
            logger.info(f"Created protocol {protocol.id} from template {template_id}")
            return protocol

        except Exception as e:
            logger.error(
                f"Failed to create protocol from template {template_id}: {str(e)}")
            raise

    # === Private Helper Methods ===

    async def _validate_create_request(self, request: ProtocolCreateRequest) -> None:
        """Validate protocol create request."""
        if not request.name or not request.name.strip():
            raise ValueError("Protocol name is required")

        if len(request.name) > 255:
            raise ValueError("Protocol name too long (max 255 characters)")

        if request.timeout_seconds is not None and request.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")

    async def _validate_protocol_commands(self, commands: List[str]) -> None:
        """Validate protocol commands."""
        if not commands:
            return

        for i, command in enumerate(commands):
            if not command or not command.strip():
                raise ValueError(f"Command {i+1} cannot be empty")

            # Basic syntax validation could be added here
            if len(command) > 10000:  # Arbitrary limit
                raise ValueError(f"Command {i+1} too long (max 10000 characters)")

    async def _get_or_create_session(
        self,
        session_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> SessionSummary:
        """Get existing session or create new one."""

        if session_id:
            try:
                return await self.get_session(session_id)
            except ValueError:
                # Session not found, create new one
                pass

        # Create new session
        return await self.create_session(context=context)

    async def _execute_parsed_command(
        self,
        parsed_command: ParsedCommand,
        context: CommandContext,
        execution_id: str,
        session: SessionSummary
    ) -> Dict[str, Any]:
        """Execute a parsed command."""

        try:
            # Create execution plan
            available_agents = []
            if self.agent_service:
                # Get available agents (simplified)
                all_agents = await self.agent_service.search_agents({})
                available_agents = all_agents[:10]  # Limit for performance

            execution_plan = await self.protocol_parser.create_execution_plan(
                parsed_command, context, available_agents
            )

            # Execute based on command type and plan
            if parsed_command.command_type and execution_plan.agents_required:
                result = await self._execute_with_agents(
                    parsed_command, execution_plan, context
                )
            elif parsed_command.command_type and execution_plan.tools_required:
                result = await self._execute_with_tools(
                    parsed_command, execution_plan, context
                )
            else:
                # Direct execution
                result = await self._execute_direct_command(
                    parsed_command, context
                )

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e)
            }

    async def _execute_with_agents(
        self,
        command: ParsedCommand,
        plan: ExecutionPlan,
        context: CommandContext
    ) -> Dict[str, Any]:
        """Execute command using agents."""

        if not self.agent_service:
            raise ValueError("Agent service not available")

        results = []

        for agent_id in plan.agents_required[:3]:  # Limit to 3 agents
            try:
                # Get agent
                agent = await self.agent_service.get_agent(agent_id)

                # Execute with agent
                from ..core.agents.agent_builder import AgentExecutionContext
                agent_context = AgentExecutionContext(
                    user_id=context.user_id,
                    session_id=context.session_id,
                    project_id=context.project_id,
                    metadata={'command_context': context.to_dict()}
                )

                # Simple command execution
                result = await agent.execute(command.original_text, agent_context)

                results.append({
                    'agent_id': agent_id,
                    'result': result.content,
                    'status': 'completed'
                })

            except Exception as e:
                results.append({
                    'agent_id': agent_id,
                    'error': str(e),
                    'status': 'failed'
                })

        return {
            'status': 'completed',
            'execution_type': 'agent_based',
            'results': results,
            'agents_used': len(results)
        }

    async def _execute_with_tools(
        self,
        command: ParsedCommand,
        plan: ExecutionPlan,
        context: CommandContext
    ) -> Dict[str, Any]:
        """Execute command using tools."""

        # Tool execution would be implemented here
        # For now, return a placeholder
        return {
            'status': 'completed',
            'execution_type': 'tool_based',
            'tools_used': plan.tools_required,
            'result': 'Tool execution completed'
        }

    async def _execute_direct_command(
        self,
        command: ParsedCommand,
        context: CommandContext
    ) -> Dict[str, Any]:
        """Execute command directly."""

        # Direct execution logic based on command type
        result_content = f"Processed command: {command.intent.category.value if command.intent else 'unknown'}"

        if command.intent and command.intent.target:
            result_content += f" on target: {command.intent.target}"

        return {
            'status': 'completed',
            'execution_type': 'direct',
            'result': result_content,
            'intent': command.intent.to_dict() if command.intent else None
        }

    async def _execute_protocol_async(
        self,
        execution_id: str,
        protocol: 'Protocol',
        commands: List[str],
        session: SessionSummary
    ) -> None:
        """Execute protocol asynchronously."""

        try:
            # Update status
            await self.repository.update_protocol_execution(
                execution_id,
                {'status': ProtocolExecutionStatus.EXECUTING.value}
            )

            # Execute commands sequentially
            results = []
            for i, command_text in enumerate(commands):

                # Create command request
                command_request = CommandExecutionRequest(
                    command_text=command_text,
                    session_id=session.session_id,
                    protocol_id=protocol.id
                )

                # Execute command
                command_result = await self.process_command(command_request)
                results.append(command_result)

                # Update progress
                progress = {
                    'completed_commands': i + 1,
                    'total_commands': len(commands),
                    'percentage': ((i + 1) / len(commands)) * 100
                }

                if execution_id in self.active_executions:
                    self.active_executions[execution_id]['progress'] = progress

                # Check for failures
                if command_result.get('status') == 'failed':
                    logger.warning(
                        f"Command failed in protocol {protocol.id}: {command_text}")
                    # Continue or stop based on protocol settings

            # Complete execution
            await self.repository.update_protocol_execution(
                execution_id,
                {
                    'status': ProtocolExecutionStatus.COMPLETED.value,
                    'completed_at': datetime.utcnow(),
                    'results': results,
                    'commands_executed': len(results)
                }
            )

            self.service_stats['total_executions_completed'] += 1

        except Exception as e:
            # Handle execution failure
            await self.repository.update_protocol_execution(
                execution_id,
                {
                    'status': ProtocolExecutionStatus.FAILED.value,
                    'completed_at': datetime.utcnow(),
                    'error_message': str(e)
                }
            )

            self.service_stats['total_execution_failures'] += 1
            logger.error(f"Protocol execution {execution_id} failed: {str(e)}")

        finally:
            # Clean up active execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

    async def _execute_protocol_sync(
        self,
        execution_id: str,
        protocol: 'Protocol',
        commands: List[str],
        session: SessionSummary
    ) -> Dict[str, Any]:
        """Execute protocol synchronously."""

        start_time = datetime.utcnow()

        try:
            results = []

            for command_text in commands:
                command_request = CommandExecutionRequest(
                    command_text=command_text,
                    session_id=session.session_id,
                    protocol_id=protocol.id
                )

                command_result = await self.process_command(command_request)
                results.append(command_result)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Update execution record
            await self.repository.update_protocol_execution(
                execution_id,
                {
                    'status': ProtocolExecutionStatus.COMPLETED.value,
                    'completed_at': datetime.utcnow(),
                    'execution_time': execution_time,
                    'results': results,
                    'commands_executed': len(results)
                }
            )

            self.service_stats['total_executions_completed'] += 1

            return {
                'execution_id': execution_id,
                'status': 'completed',
                'execution_time': execution_time,
                'commands_executed': len(results),
                'results': results,
                'protocol_id': protocol.id
            }

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            await self.repository.update_protocol_execution(
                execution_id,
                {
                    'status': ProtocolExecutionStatus.FAILED.value,
                    'completed_at': datetime.utcnow(),
                    'execution_time': execution_time,
                    'error_message': str(e)
                }
            )

            self.service_stats['total_execution_failures'] += 1

            return {
                'execution_id': execution_id,
                'status': 'failed',
                'execution_time': execution_time,
                'error': str(e),
                'protocol_id': protocol.id
            }

    async def _update_session_with_command_result(
        self,
        session: SessionSummary,
        command: ParsedCommand,
        result: Dict[str, Any]
    ) -> None:
        """Update session with command execution result."""

        # Update session stats
        session.command_count += 1
        if result.get('status') == 'completed':
            session.successful_commands += 1
        else:
            session.failed_commands += 1

        # Add to command history
        if 'command_history' not in session.metadata:
            session.metadata['command_history'] = []

        session.metadata['command_history'].append({
            'command': command.original_text,
            'intent': command.intent.to_dict() if command.intent else None,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Keep only last 100 commands in history
        if len(session.metadata['command_history']) > 100:
            session.metadata['command_history'] = session.metadata['command_history'][-100:]

        # Update last activity
        session.last_activity = datetime.utcnow()

        # Update repository
        updates = {
            'command_count': session.command_count,
            'successful_commands': session.successful_commands,
            'failed_commands': session.failed_commands,
            'metadata': session.metadata,
            'last_activity': session.last_activity
        }

        await self.repository.update_session(session.session_id, updates)

        # Update cache
        self.active_sessions[session.session_id] = session

    def _update_response_time_stats(self, response_time: float) -> None:
        """Update service response time statistics."""
        # Simplified stats update
        pass

    def _update_parse_time_stats(self, parse_time: float) -> None:
        """Update command parse time statistics."""
        current_avg = self.service_stats['average_command_parse_time']
        total_commands = self.service_stats['total_commands_processed']

        if total_commands > 0:
            self.service_stats['average_command_parse_time'] = (
                (current_avg * (total_commands - 1) + parse_time) / total_commands
            )

    # === Router Compatibility Methods ===

    async def list_protocols(self, project_id: str, status_filter: Optional[str] = None) -> List['Protocol']:
        """List protocols for a project (router compatibility method)."""
        try:
            criteria = ProtocolSearchCriteria(
                project_id=project_id,
                is_active=status_filter != "inactive" if status_filter else True
            )
            return await self.search_protocols(criteria)
        except Exception as e:
            logger.error(f"Failed to list protocols for project {project_id}: {str(e)}")
            raise

    async def get_protocol(self, project_id: str, protocol_id: str) -> Optional['Protocol']:
        """Get protocol by project and protocol ID (router compatibility method)."""
        try:
            protocol = await self.get_protocol(protocol_id)
            # Check if protocol belongs to project
            if hasattr(protocol, 'project_id') and protocol.project_id != project_id:
                return None
            return protocol
        except Exception as e:
            logger.error(
                f"Failed to get protocol {protocol_id} for project {project_id}: {str(e)}")
            return None

    async def create_protocol(
        self,
        project_id: str,
        id: str,
        name: str,
        description: Optional[str] = None,
        commands: Optional[List[Dict[str, Any]]] = None,
        execution_order: Optional[List[str]] = None
    ) -> 'Protocol':
        """Create protocol (router compatibility method)."""
        try:
            # Convert commands to string format if needed
            command_strings = []
            if commands:
                for cmd in commands:
                    if isinstance(cmd, dict):
                        command_strings.append(
                            cmd.get('definition', cmd.get('name', '')))
                    else:
                        command_strings.append(str(cmd))

            request = ProtocolCreateRequest(
                name=name,
                description=description or "",
                project_id=project_id,
                user_id=None,  # Will be set by auth
                commands=command_strings,
                metadata={
                    'execution_order': execution_order or [],
                    'original_commands': commands or []
                }
            )

            return await self.create_protocol(request)
        except Exception as e:
            logger.error(f"Failed to create protocol in project {project_id}: {str(e)}")
            raise

    async def update_protocol(
        self,
        project_id: str,
        protocol_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        commands: Optional[List[Dict[str, Any]]] = None,
        execution_order: Optional[List[str]] = None
    ) -> 'Protocol':
        """Update protocol (router compatibility method)."""
        try:
            # Convert commands to string format if needed
            command_strings = None
            if commands:
                command_strings = []
                for cmd in commands:
                    if isinstance(cmd, dict):
                        command_strings.append(
                            cmd.get('definition', cmd.get('name', '')))
                    else:
                        command_strings.append(str(cmd))

            request = ProtocolUpdateRequest(
                name=name,
                description=description,
                commands=command_strings,
                metadata={'execution_order': execution_order} if execution_order else None
            )

            return await self.update_protocol(protocol_id, request)
        except Exception as e:
            logger.error(
                f"Failed to update protocol {protocol_id} in project {project_id}: {str(e)}")
            raise

    async def delete_protocol(self, project_id: str, protocol_id: str) -> bool:
        """Delete protocol (router compatibility method)."""
        try:
            # Check if protocol belongs to project
            protocol = await self.get_protocol(project_id, protocol_id)
            if not protocol:
                return False

            return await self.delete_protocol(protocol_id)
        except Exception as e:
            logger.error(
                f"Failed to delete protocol {protocol_id} from project {project_id}: {str(e)}")
            raise

    async def is_protocol_in_use(self, project_id: str, protocol_id: str) -> bool:
        """Check if protocol is in use (router compatibility method)."""
        try:
            # Check for active executions
            executions = await self.repository.get_protocol_executions(protocol_id, limit=1)
            return len(executions) > 0
        except Exception as e:
            logger.error(
                f"Failed to check if protocol {protocol_id} is in use: {str(e)}")
            return False

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service statistics (non-async for compatibility)."""
        return self.service_stats.copy()


# === FACTORY FUNCTION ===

def create_protocol_service(
    agent_service: Optional['AgentService'] = None,
    team_service: Optional['TeamService'] = None,
    workflow_service: Optional['WorkflowService'] = None,
    repository: Optional[ProtocolRepository] = None,
    protocol_parser: Optional[ProtocolParser] = None
) -> ProtocolService:
    """Create ProtocolService with default dependencies."""
    if repository is None:
        repository = MockProtocolRepository()

    return ProtocolService(
        repository=repository,
        protocol_parser=protocol_parser,
        agent_service=agent_service,
        team_service=team_service,
        workflow_service=workflow_service
    )


# === EXAMPLE USAGE ===

async def example_protocol_service_usage():
    """Example usage of ProtocolService."""

    # Create service
    service = create_protocol_service()

    # Create a protocol
    create_request = ProtocolCreateRequest(
        name="Development Workflow",
        description="Protocol for development tasks",
        commands=[
            "Analyze the current codebase structure",
            "Generate unit tests for critical components",
            "Create documentation for new features"
        ],
        tags=["development", "automation"]
    )

    protocol = await service.create_protocol(create_request)
    print(f"Created protocol: {protocol.id}")

    # Create a session
    session = await service.create_session(
        user_id="test_user",
        project_id="test_project",
        protocol_id=protocol.id
    )
    print(f"Created session: {session.session_id}")

    # Process individual command
    command_request = CommandExecutionRequest(
        command_text="Analyze the main.py file for potential improvements",
        session_id=session.session_id
    )

    result = await service.process_command(command_request)
    print(f"Command result: {result.get('status')}")

    # Execute protocol
    execution_request = ProtocolExecutionRequest(
        protocol_id=protocol.id,
        session_id=session.session_id,
        async_execution=False
    )

    execution_result = await service.execute_protocol(execution_request)
    print(f"Protocol execution: {execution_result.get('status')}")

    # Get analytics
    analytics = await service.get_protocol_analytics(protocol.id)
    print(f"Analytics: {analytics.total_executions} executions")

    # Get service stats
    stats = service.get_service_statistics()
    print(f"Service stats: {json.dumps(stats, indent=2, default=str)}")


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_protocol_service_usage())
