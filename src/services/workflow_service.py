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
Workflow Service - Business Logic Layer for Workflow Management.

The WorkflowService provides comprehensive workflow management functionality,
including CRUD operations, execution orchestration, monitoring, optimization,
and integration with the core WorkflowEngine (Pregel-based).

Key Features:
- Workflow lifecycle management (create, update, delete, version control)
- Execution orchestration and monitoring
- Graph validation and optimization
- Performance analytics and statistics
- Template management and reusability
- Integration with Agent and Team services
- Real-time execution tracking
- Error handling and recovery

Architecture:
- Repository pattern for data persistence
- Service layer for business logic
- Integration with WorkflowEngine for execution
- Event-driven updates for real-time monitoring
- Caching for performance optimization

Dependencies:
- WorkflowEngine (core execution)
- AgentService (agent management)
- TeamService (team coordination)
- Database models (Workflow, WorkflowVertex, WorkflowEdge, WorkflowExecution)
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

# SQLAlchemy imports

# Type checking imports
if TYPE_CHECKING:
    from ..models.agent import Agent
    from ..models.team import Team
    from ..models.workflow import (
        Workflow,
        WorkflowEdge,
        WorkflowExecution,
        WorkflowExecutionStatus,
        WorkflowTemplate,
        WorkflowVersion,
        WorkflowVertex,
    )
    from .agent_service import AgentService
    from .team_service import TeamService

# Core imports
    WorkflowEngine, WorkflowExecutionContext, WorkflowState,
    VertexState, WorkflowMessage, VertexExecutionResult,
    AgentVertexComputation, TeamVertexComputation, AtomicVertexComputation,
    create_agent_vertex, create_team_vertex, create_function_vertex
)

logger = logging.getLogger(__name__)


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""
    pass


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""
    pass


class WorkflowNotFoundError(Exception):
    """Raised when workflow is not found."""
    pass


@dataclass
class WorkflowCreateRequest:
    """Request for creating a new workflow."""
    name: str
    description: str = ""
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    vertices: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    template_id: Optional[str] = None
    is_template: bool = False


@dataclass
class WorkflowUpdateRequest:
    """Request for updating an existing workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    vertices: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


@dataclass
class WorkflowExecutionRequest:
    """Request for executing a workflow."""
    workflow_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    context_overrides: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: Optional[int] = None
    priority: int = 0
    scheduled_at: Optional[datetime] = None


@dataclass
class WorkflowSearchCriteria:
    """Criteria for searching workflows."""
    name_pattern: Optional[str] = None
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
class WorkflowAnalytics:
    """Workflow performance analytics."""
    workflow_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    median_execution_time: float = 0.0
    min_execution_time: float = 0.0
    max_execution_time: float = 0.0
    last_execution_at: Optional[datetime] = None
    error_rate: float = 0.0
    vertex_statistics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    performance_trends: List[Dict[str, Any]] = field(default_factory=list)


class WorkflowRepository(ABC):
    """Abstract repository interface for workflow data persistence."""

    @abstractmethod
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> 'Workflow':
        """Create a new workflow."""
        pass

    @abstractmethod
    async def get_workflow_by_id(self, workflow_id: str) -> Optional['Workflow']:
        """Get workflow by ID."""
        pass

    @abstractmethod
    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional['Workflow']:
        """Update workflow."""
        pass

    @abstractmethod
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow."""
        pass

    @abstractmethod
    async def search_workflows(self, criteria: WorkflowSearchCriteria) -> List['Workflow']:
        """Search workflows by criteria."""
        pass

    @abstractmethod
    async def get_workflow_versions(self, workflow_id: str) -> List['WorkflowVersion']:
        """Get workflow versions."""
        pass

    @abstractmethod
    async def create_workflow_execution(self, execution_data: Dict[str, Any]) -> 'WorkflowExecution':
        """Create workflow execution record."""
        pass

    @abstractmethod
    async def update_workflow_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> Optional['WorkflowExecution']:
        """Update workflow execution."""
        pass

    @abstractmethod
    async def get_workflow_executions(
        self,
        workflow_id: str,
        limit: int = 50
    ) -> List['WorkflowExecution']:
        """Get workflow executions."""
        pass

    @abstractmethod
    async def get_execution_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """Get execution analytics for workflow."""
        pass


class MockWorkflowRepository(WorkflowRepository):
    """Mock repository implementation for development/testing."""

    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.executions: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, List[Dict[str, Any]]] = {}

    async def create_workflow(self, workflow_data: Dict[str, Any]) -> 'Workflow':
        """Create a new workflow."""
        workflow_id = workflow_data.get('id', str(uuid.uuid4()))
        workflow_data['id'] = workflow_id
        workflow_data['created_at'] = datetime.utcnow()
        workflow_data['updated_at'] = datetime.utcnow()
        workflow_data['version'] = 1

        self.workflows[workflow_id] = workflow_data.copy()

        # Initialize versions
        self.versions[workflow_id] = [workflow_data.copy()]

        # Return mock workflow object
        class MockWorkflow:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockWorkflow(workflow_data)

    async def get_workflow_by_id(self, workflow_id: str) -> Optional['Workflow']:
        """Get workflow by ID."""
        if workflow_id not in self.workflows:
            return None

        class MockWorkflow:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockWorkflow(self.workflows[workflow_id])

    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional['Workflow']:
        """Update workflow."""
        if workflow_id not in self.workflows:
            return None

        # Create new version
        current_data = self.workflows[workflow_id].copy()
        current_data.update(updates)
        current_data['updated_at'] = datetime.utcnow()
        current_data['version'] = current_data.get('version', 1) + 1

        self.workflows[workflow_id] = current_data

        # Add to versions
        if workflow_id not in self.versions:
            self.versions[workflow_id] = []
        self.versions[workflow_id].append(current_data.copy())

        class MockWorkflow:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockWorkflow(current_data)

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            if workflow_id in self.versions:
                del self.versions[workflow_id]
            # Also delete executions
            executions_to_delete = [
                eid for eid, exec_data in self.executions.items()
                if exec_data.get('workflow_id') == workflow_id
            ]
            for eid in executions_to_delete:
                del self.executions[eid]
            return True
        return False

    async def search_workflows(self, criteria: WorkflowSearchCriteria) -> List['Workflow']:
        """Search workflows by criteria."""
        results = []

        for workflow_id, workflow_data in self.workflows.items():
            # Apply filters
            if criteria.name_pattern and criteria.name_pattern not in workflow_data.get('name', ''):
                continue
            if criteria.project_id and workflow_data.get('project_id') != criteria.project_id:
                continue
            if criteria.user_id and workflow_data.get('user_id') != criteria.user_id:
                continue
            if criteria.is_template is not None and workflow_data.get('is_template') != criteria.is_template:
                continue
            if criteria.is_active is not None and workflow_data.get('is_active') != criteria.is_active:
                continue
            if criteria.tags:
                workflow_tags = set(workflow_data.get('tags', []))
                if not set(criteria.tags).issubset(workflow_tags):
                    continue

            class MockWorkflow:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)

            results.append(MockWorkflow(workflow_data))

        # Apply pagination
        return results[criteria.offset:criteria.offset + criteria.limit]

    async def get_workflow_versions(self, workflow_id: str) -> List['WorkflowVersion']:
        """Get workflow versions."""
        versions = self.versions.get(workflow_id, [])

        class MockWorkflowVersion:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return [MockWorkflowVersion(v) for v in versions]

    async def create_workflow_execution(self, execution_data: Dict[str, Any]) -> 'WorkflowExecution':
        """Create workflow execution record."""
        execution_id = execution_data.get('id', str(uuid.uuid4()))
        execution_data['id'] = execution_id
        execution_data['created_at'] = datetime.utcnow()
        execution_data['status'] = 'created'

        self.executions[execution_id] = execution_data.copy()

        class MockWorkflowExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockWorkflowExecution(execution_data)

    async def update_workflow_execution(
        self,
        execution_id: str,
        updates: Dict[str, Any]
    ) -> Optional['WorkflowExecution']:
        """Update workflow execution."""
        if execution_id not in self.executions:
            return None

        self.executions[execution_id].update(updates)
        self.executions[execution_id]['updated_at'] = datetime.utcnow()

        class MockWorkflowExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockWorkflowExecution(self.executions[execution_id])

    async def get_workflow_executions(
        self,
        workflow_id: str,
        limit: int = 50
    ) -> List['WorkflowExecution']:
        """Get workflow executions."""
        executions = [
            exec_data for exec_data in self.executions.values()
            if exec_data.get('workflow_id') == workflow_id
        ]

        # Sort by created_at descending
        executions.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)

        class MockWorkflowExecution:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return [MockWorkflowExecution(e) for e in executions[:limit]]

    async def get_execution_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """Get execution analytics for workflow."""
        executions = [
            exec_data for exec_data in self.executions.values()
            if exec_data.get('workflow_id') == workflow_id
        ]

        if not executions:
            return {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_execution_time': 0.0,
                'error_rate': 0.0
            }

        successful = sum(1 for e in executions if e.get('status') == 'completed')
        failed = sum(1 for e in executions if e.get('status') == 'failed')

        execution_times = [
            e.get('execution_time', 0.0) for e in executions
            if e.get('execution_time') is not None
        ]

        return {
            'total_executions': len(executions),
            'successful_executions': successful,
            'failed_executions': failed,
            'average_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0.0,
            'error_rate': failed / len(executions) if executions else 0.0,
            'last_execution_at': max(e.get('created_at', datetime.min) for e in executions)
        }


class WorkflowService:
    """
    Service layer for workflow management and execution orchestration.

    Provides comprehensive workflow lifecycle management including:
    - CRUD operations with validation
    - Execution orchestration using WorkflowEngine
    - Performance monitoring and analytics
    - Template management and versioning
    - Integration with Agent and Team services
    - Real-time execution tracking
    """

    def __init__(
        self,
        repository: WorkflowRepository,
        agent_service: Optional['AgentService'] = None,
        team_service: Optional['TeamService'] = None
    ):
        """Initialize workflow service."""
        self.repository = repository
        self.agent_service = agent_service
        self.team_service = team_service
        self.active_executions: Dict[str, WorkflowEngine] = {}
        self.execution_callbacks: Dict[str, List[Callable]] = {}

        # Performance cache
        self._analytics_cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Statistics
        self.service_stats = {
            'total_workflows_created': 0,
            'total_executions_started': 0,
            'total_executions_completed': 0,
            'total_execution_failures': 0,
            'average_service_response_time': 0.0
        }

    # === CRUD Operations ===

    async def create_workflow(self, request: WorkflowCreateRequest) -> 'Workflow':
        """Create a new workflow with validation."""
        start_time = datetime.utcnow()

        try:
            # Validate request
            await self._validate_create_request(request)

            # Prepare workflow data
            workflow_data = {
                'name': request.name,
                'description': request.description,
                'project_id': request.project_id,
                'user_id': request.user_id,
                'tags': request.tags,
                'metadata': request.metadata,
                'vertices': request.vertices,
                'edges': request.edges,
                'template_id': request.template_id,
                'is_template': request.is_template,
                'is_active': True,
                'execution_count': 0
            }

            # Validate workflow graph
            await self._validate_workflow_graph(workflow_data)

            # Create workflow
            workflow = await self.repository.create_workflow(workflow_data)

            # Update stats
            self.service_stats['total_workflows_created'] += 1

            # Update response time stats
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time_stats(response_time)

            logger.info(f"Created workflow {workflow.id}: {workflow.name}")
            return workflow

        except Exception as e:
            logger.error(f"Failed to create workflow: {str(e)}")
            raise WorkflowValidationError(f"Workflow creation failed: {str(e)}")

    async def get_workflow(self, workflow_id: str) -> 'Workflow':
        """Get workflow by ID."""
        workflow = await self.repository.get_workflow_by_id(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
        return workflow

    async def update_workflow(self, workflow_id: str, request: WorkflowUpdateRequest) -> 'Workflow':
        """Update workflow with validation."""
        start_time = datetime.utcnow()

        try:
            # Check if workflow exists
            existing = await self.get_workflow(workflow_id)

            # Prepare updates
            updates = {}
            if request.name is not None:
                updates['name'] = request.name
            if request.description is not None:
                updates['description'] = request.description
            if request.tags is not None:
                updates['tags'] = request.tags
            if request.metadata is not None:
                updates['metadata'] = request.metadata
            if request.vertices is not None:
                updates['vertices'] = request.vertices
            if request.edges is not None:
                updates['edges'] = request.edges
            if request.is_active is not None:
                updates['is_active'] = request.is_active

            # Validate graph if vertices/edges changed
            if request.vertices is not None or request.edges is not None:
                temp_workflow_data = {
                    'vertices': request.vertices or existing.vertices,
                    'edges': request.edges or existing.edges
                }
                await self._validate_workflow_graph(temp_workflow_data)

            # Update workflow
            workflow = await self.repository.update_workflow(workflow_id, updates)
            if not workflow:
                raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

            # Update response time stats
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_response_time_stats(response_time)

            logger.info(f"Updated workflow {workflow_id}")
            return workflow

        except WorkflowNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update workflow {workflow_id}: {str(e)}")
            raise WorkflowValidationError(f"Workflow update failed: {str(e)}")

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow and related executions."""
        try:
            # Check if workflow has active executions
            if workflow_id in self.active_executions:
                raise WorkflowExecutionError(
                    f"Cannot delete workflow {workflow_id} with active execution")

            # Delete workflow
            success = await self.repository.delete_workflow(workflow_id)
            if success:
                # Clear cache
                if workflow_id in self._analytics_cache:
                    del self._analytics_cache[workflow_id]
                logger.info(f"Deleted workflow {workflow_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {str(e)}")
            raise

    async def search_workflows(self, criteria: WorkflowSearchCriteria) -> List['Workflow']:
        """Search workflows by criteria."""
        try:
            workflows = await self.repository.search_workflows(criteria)
            logger.debug(f"Found {len(workflows)} workflows matching criteria")
            return workflows
        except Exception as e:
            logger.error(f"Workflow search failed: {str(e)}")
            raise

    # === Execution Operations ===

    async def execute_workflow(
        self,
        request: WorkflowExecutionRequest
    ) -> Dict[str, Any]:
        """Execute workflow using WorkflowEngine."""
        start_time = datetime.utcnow()
        execution_id = str(uuid.uuid4())

        try:
            # Get workflow
            workflow = await self.get_workflow(request.workflow_id)
            if not workflow.is_active:
                raise WorkflowExecutionError(
                    f"Workflow {request.workflow_id} is not active")

            # Create execution context
            context = WorkflowExecutionContext(
                execution_id=execution_id,
                workflow_id=request.workflow_id,
                project_id=workflow.project_id,
                user_id=workflow.user_id,
                input_data=request.input_data,
                timeout_seconds=request.timeout_seconds,
                **request.context_overrides
            )

            # Create execution record
            execution_data = {
                'workflow_id': request.workflow_id,
                'execution_id': execution_id,
                'status': 'running',
                'input_data': request.input_data,
                'context': context.to_dict(),
                'started_at': start_time,
                'priority': request.priority
            }
            await self.repository.create_workflow_execution(execution_data)

            # Build and execute workflow
            engine = await self._build_workflow_engine(workflow)
            self.active_executions[execution_id] = engine

            # Update stats
            self.service_stats['total_executions_started'] += 1

            try:
                # Execute workflow
                result = await engine.execute_workflow(context, request.input_data)

                # Update execution record
                execution_updates = {
                    'status': result['status'],
                    'completed_at': datetime.utcnow(),
                    'execution_time': result['execution_time'],
                    'result': result,
                    'vertices_executed': result.get('vertices_executed', 0),
                    'supersteps': result.get('supersteps', 0)
                }

                if result['status'] == 'completed':
                    self.service_stats['total_executions_completed'] += 1
                else:
                    self.service_stats['total_execution_failures'] += 1
                    execution_updates['error_message'] = result.get(
                        'error', 'Unknown error')

                await self.repository.update_workflow_execution(execution_id, execution_updates)

                # Clear cache for analytics
                if request.workflow_id in self._analytics_cache:
                    del self._analytics_cache[request.workflow_id]

                logger.info(
                    f"Workflow {request.workflow_id} execution {execution_id} {result['status']}")
                return result

            finally:
                # Clean up active execution
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]

        except Exception as e:
            # Update execution record with failure
            try:
                execution_updates = {
                    'status': 'failed',
                    'completed_at': datetime.utcnow(),
                    'execution_time': (datetime.utcnow() - start_time).total_seconds(),
                    'error_message': str(e)
                }
                await self.repository.update_workflow_execution(execution_id, execution_updates)
            except:
                pass  # Don't fail on update failure

            # Update stats
            self.service_stats['total_execution_failures'] += 1

            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            logger.error(f"Workflow execution {execution_id} failed: {str(e)}")
            raise WorkflowExecutionError(f"Execution failed: {str(e)}")

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current execution status."""
        try:
            # Check if execution is active
            if execution_id in self.active_executions:
                engine = self.active_executions[execution_id]
                stats = engine.get_workflow_stats()
                return {
                    'execution_id': execution_id,
                    'status': 'running',
                    'is_active': True,
                    'engine_stats': stats
                }

            # Get from database
            # Note: This would need to query executions by execution_id
            # For now, return not found
            return {
                'execution_id': execution_id,
                'status': 'not_found',
                'is_active': False
            }

        except Exception as e:
            logger.error(f"Failed to get execution status {execution_id}: {str(e)}")
            raise

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel active workflow execution."""
        try:
            if execution_id in self.active_executions:
                # For now, just remove from active executions
                # In a full implementation, this would signal the engine to stop
                del self.active_executions[execution_id]

                # Update execution record
                execution_updates = {
                    'status': 'cancelled',
                    'completed_at': datetime.utcnow()
                }
                await self.repository.update_workflow_execution(execution_id, execution_updates)

                logger.info(f"Cancelled execution {execution_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {str(e)}")
            raise

    # === Analytics and Monitoring ===

    async def get_workflow_analytics(self, workflow_id: str) -> WorkflowAnalytics:
        """Get comprehensive workflow analytics."""
        try:
            # Check cache
            cache_key = f"analytics_{workflow_id}"
            if cache_key in self._analytics_cache:
                cached_data, cached_time = self._analytics_cache[cache_key]
                if (datetime.utcnow() - cached_time).total_seconds() < self._cache_ttl:
                    return cached_data

            # Get analytics from repository
            analytics_data = await self.repository.get_execution_analytics(workflow_id)

            # Create analytics object
            analytics = WorkflowAnalytics(
                workflow_id=workflow_id,
                **analytics_data
            )

            # Cache result
            self._analytics_cache[cache_key] = (analytics, datetime.utcnow())

            return analytics

        except Exception as e:
            logger.error(
                f"Failed to get analytics for workflow {workflow_id}: {str(e)}")
            raise

    async def get_workflow_executions(
        self,
        workflow_id: str,
        limit: int = 50
    ) -> List['WorkflowExecution']:
        """Get workflow execution history."""
        try:
            executions = await self.repository.get_workflow_executions(workflow_id, limit)
            return executions
        except Exception as e:
            logger.error(
                f"Failed to get executions for workflow {workflow_id}: {str(e)}")
            raise

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service-level statistics."""
        return {
            'service_stats': self.service_stats,
            'active_executions': len(self.active_executions),
            'cache_size': len(self._analytics_cache),
            'uptime': datetime.utcnow().isoformat()  # Would track actual uptime
        }

    # === Template Management ===

    async def create_template_from_workflow(
        self,
        workflow_id: str,
        template_name: str,
        template_description: str = ""
    ) -> 'Workflow':
        """Create a reusable template from existing workflow."""
        try:
            # Get source workflow
            workflow = await self.get_workflow(workflow_id)

            # Create template request
            template_request = WorkflowCreateRequest(
                name=template_name,
                description=template_description,
                project_id=workflow.project_id,
                user_id=workflow.user_id,
                tags=workflow.tags + ['template'],
                metadata={**workflow.metadata, 'source_workflow_id': workflow_id},
                vertices=workflow.vertices,
                edges=workflow.edges,
                is_template=True
            )

            # Create template
            template = await self.create_workflow(template_request)
            logger.info(f"Created template {template.id} from workflow {workflow_id}")
            return template

        except Exception as e:
            logger.error(
                f"Failed to create template from workflow {workflow_id}: {str(e)}")
            raise

    async def create_workflow_from_template(
        self,
        template_id: str,
        workflow_name: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> 'Workflow':
        """Create workflow from template with customizations."""
        try:
            # Get template
            template = await self.get_workflow(template_id)
            if not template.is_template:
                raise WorkflowValidationError(
                    f"Workflow {template_id} is not a template")

            # Apply customizations
            vertices = template.vertices.copy()
            edges = template.edges.copy()
            metadata = template.metadata.copy()

            if customizations:
                if 'vertices' in customizations:
                    vertices.extend(customizations['vertices'])
                if 'edges' in customizations:
                    edges.extend(customizations['edges'])
                if 'metadata' in customizations:
                    metadata.update(customizations['metadata'])

            # Create workflow request
            workflow_request = WorkflowCreateRequest(
                name=workflow_name,
                description=f"Created from template: {template.name}",
                project_id=template.project_id,
                user_id=template.user_id,
                tags=template.tags,
                metadata=metadata,
                vertices=vertices,
                edges=edges,
                template_id=template_id,
                is_template=False
            )

            # Create workflow
            workflow = await self.create_workflow(workflow_request)
            logger.info(f"Created workflow {workflow.id} from template {template_id}")
            return workflow

        except Exception as e:
            logger.error(
                f"Failed to create workflow from template {template_id}: {str(e)}")
            raise

    # === Private Helper Methods ===

    async def _validate_create_request(self, request: WorkflowCreateRequest) -> None:
        """Validate workflow create request."""
        if not request.name or not request.name.strip():
            raise WorkflowValidationError("Workflow name is required")

        if len(request.name) > 255:
            raise WorkflowValidationError("Workflow name too long (max 255 characters)")

        if not request.vertices:
            raise WorkflowValidationError("Workflow must have at least one vertex")

        # Validate vertex configurations
        for vertex in request.vertices:
            if 'id' not in vertex or 'type' not in vertex:
                raise WorkflowValidationError(
                    "Each vertex must have 'id' and 'type' fields")

        # Validate edge configurations
        vertex_ids = {v['id'] for v in request.vertices}
        for edge in request.edges:
            if 'from' not in edge or 'to' not in edge:
                raise WorkflowValidationError(
                    "Each edge must have 'from' and 'to' fields")
            if edge['from'] not in vertex_ids:
                raise WorkflowValidationError(
                    f"Edge references unknown source vertex: {edge['from']}")
            if edge['to'] not in vertex_ids:
                raise WorkflowValidationError(
                    f"Edge references unknown target vertex: {edge['to']}")

    async def _validate_workflow_graph(self, workflow_data: Dict[str, Any]) -> None:
        """Validate workflow graph structure."""
        try:
            # Create temporary engine for validation
            engine = WorkflowEngine()

            # Add vertices and edges
            for vertex_data in workflow_data.get('vertices', []):
                # Create dummy computation for validation
                async def dummy_computation(input_data):
                    return input_data

                vertex_id, computation, config = create_function_vertex(
                    vertex_data['id'],
                    dummy_computation,
                    dependencies=vertex_data.get('dependencies', [])
                )
                engine.add_vertex(vertex_id, computation, config)

            for edge_data in workflow_data.get('edges', []):
                engine.add_edge(edge_data['from'], edge_data['to'])

            # Validate
            is_valid, errors = engine.validate_workflow()
            if not is_valid:
                raise WorkflowValidationError(
                    f"Invalid workflow graph: {', '.join(errors)}")

        except Exception as e:
            if isinstance(e, WorkflowValidationError):
                raise
            raise WorkflowValidationError(f"Graph validation failed: {str(e)}")

    async def _build_workflow_engine(self, workflow: 'Workflow') -> WorkflowEngine:
        """Build WorkflowEngine from workflow definition."""
        engine = WorkflowEngine()

        try:
            # Add vertices
            for vertex_data in workflow.vertices:
                vertex_type = vertex_data['type']
                vertex_id = vertex_data['id']
                config = vertex_data.get('config', {})

                if vertex_type == 'agent':
                    # Get agent
                    agent_id = config.get('agent_id')
                    if not agent_id or not self.agent_service:
                        raise WorkflowExecutionError(
                            f"Agent {agent_id} not found for vertex {vertex_id}")

                    agent = await self.agent_service.get_agent(agent_id)
                    instruction = config.get('instruction', 'Process the input data')

                    vertex_id, computation, vertex_config = create_agent_vertex(
                        vertex_id, agent, instruction,
                        dependencies=config.get('dependencies', []),
                        output_targets=config.get('output_targets', [])
                    )

                elif vertex_type == 'team':
                    # Get team
                    team_id = config.get('team_id')
                    if not team_id or not self.team_service:
                        raise WorkflowExecutionError(
                            f"Team {team_id} not found for vertex {vertex_id}")

                    team = await self.team_service.get_team(team_id)
                    tasks = config.get('tasks', [])

                    vertex_id, computation, vertex_config = create_team_vertex(
                        vertex_id, team, tasks,
                        dependencies=config.get('dependencies', []),
                        output_targets=config.get('output_targets', [])
                    )

                elif vertex_type == 'function':
                    # Create function vertex with provided operation
                    operation_code = config.get('operation', 'return input_data')

                    # Create function from code string (simplified)
                    async def dynamic_operation(input_data):
                        # In a real implementation, this would safely execute the code
                        return {'result': 'processed', 'input': input_data}

                    vertex_id, computation, vertex_config = create_function_vertex(
                        vertex_id, dynamic_operation,
                        dependencies=config.get('dependencies', []),
                        output_targets=config.get('output_targets', [])
                    )

                else:
                    raise WorkflowExecutionError(f"Unknown vertex type: {vertex_type}")

                engine.add_vertex(vertex_id, computation, vertex_config)

            # Add edges
            for edge_data in workflow.edges:
                engine.add_edge(edge_data['from'], edge_data['to'])

            return engine

        except Exception as e:
            logger.error(f"Failed to build workflow engine: {str(e)}")
            raise WorkflowExecutionError(f"Failed to build workflow: {str(e)}")

    def _update_response_time_stats(self, response_time: float) -> None:
        """Update service response time statistics."""
        current_avg = self.service_stats['average_service_response_time']
        total_requests = (
            self.service_stats['total_workflows_created'] +
            self.service_stats['total_executions_started']
        )

        if total_requests > 0:
            self.service_stats['average_service_response_time'] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )


# === FACTORY FUNCTION ===

def create_workflow_service(
    agent_service: Optional['AgentService'] = None,
    team_service: Optional['TeamService'] = None,
    repository: Optional[WorkflowRepository] = None
) -> WorkflowService:
    """Create WorkflowService with default dependencies."""
    if repository is None:
        repository = MockWorkflowRepository()

    return WorkflowService(
        repository=repository,
        agent_service=agent_service,
        team_service=team_service
    )


# === EXAMPLE USAGE ===

async def example_workflow_service_usage():
    """Example usage of WorkflowService."""

    # Create service
    service = create_workflow_service()

    # Create a simple workflow
    create_request = WorkflowCreateRequest(
        name="Data Processing Pipeline",
        description="Process data through multiple stages",
        vertices=[
            {
                'id': 'input',
                'type': 'function',
                'config': {
                    'operation': 'return {"processed": True, "data": input_data}',
                    'output_targets': ['output']
                }
            },
            {
                'id': 'output',
                'type': 'function',
                'config': {
                    'operation': 'return {"final": input_data}',
                    'dependencies': ['input']
                }
            }
        ],
        edges=[
            {'from': 'input', 'to': 'output'}
        ]
    )

    # Create workflow
    workflow = await service.create_workflow(create_request)
    print(f"Created workflow: {workflow.id}")

    # Execute workflow
    execution_request = WorkflowExecutionRequest(
        workflow_id=workflow.id,
        input_data={'test': 'data'}
    )

    result = await service.execute_workflow(execution_request)
    print(f"Execution result: {json.dumps(result, indent=2, default=str)}")

    # Get analytics
    analytics = await service.get_workflow_analytics(workflow.id)
    print(f"Analytics: Total executions = {analytics.total_executions}")

    # Get service stats
    stats = service.get_service_statistics()
    print(f"Service stats: {json.dumps(stats, indent=2, default=str)}")


class PostgreSQLWorkflowExecutionRepository(WorkflowRepository):
    """PostgreSQL implementation of workflow execution repository."""

    def __init__(self, session_factory):
        """
        Initialize repository with database session factory.

        Args:
            session_factory: Async SQLAlchemy session factory
        """
        self.session_factory = session_factory

    async def create_workflow_execution(self, execution_data: Dict[str, Any]) -> 'WorkflowExecution':
        """Create workflow execution record."""
        async with self.session_factory() as session:
            execution = WorkflowExecution(**execution_data)
            session.add(execution)
            await session.commit()
            await session.refresh(execution)
            return execution

    async def get_workflow_execution(self, execution_id: str) -> Optional['WorkflowExecution']:
        """Get workflow execution by ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.execution_id == execution_id)
            )
            return result.scalar_one_or_none()

    async def update_workflow_execution(
        self, execution_id: str, updates: Dict[str, Any]
    ) -> Optional['WorkflowExecution']:
        """Update workflow execution."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.execution_id == execution_id)
            )
            execution = result.scalar_one_or_none()

            if execution:
                for key, value in updates.items():
                    if hasattr(execution, key):
                        setattr(execution, key, value)

                execution.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(execution)

            return execution

    async def get_workflow_executions(
        self, workflow_id: str, limit: int = 50, offset: int = 0
    ) -> List['WorkflowExecution']:
        """Get workflow executions for a workflow."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(WorkflowExecution)
                .where(WorkflowExecution.workflow_id == workflow_id)
                .order_by(WorkflowExecution.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def get_executions_by_status(
        self, status: str, limit: int = 50
    ) -> List['WorkflowExecution']:
        """Get executions by status."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(WorkflowExecution)
                .where(WorkflowExecution.status == status)
                .order_by(WorkflowExecution.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_execution_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """Get execution analytics for workflow."""
        async with self.session_factory() as session:
            # Get all executions for the workflow
            result = await session.execute(
                select(WorkflowExecution)
                .where(WorkflowExecution.workflow_id == workflow_id)
            )
            executions = list(result.scalars().all())

            if not executions:
                return {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'success_rate': 0.0,
                    'average_duration': 0.0,
                    'last_execution_at': None
                }

            total = len(executions)
            successful = sum(1 for e in executions if e.is_successful)
            failed = total - successful

            durations = [
                e.duration_seconds for e in executions if e.duration_seconds is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            last_execution = max(executions, key=lambda e: e.created_at)

            return {
                'total_executions': total,
                'successful_executions': successful,
                'failed_executions': failed,
                'success_rate': successful / total if total > 0 else 0.0,
                'average_duration': avg_duration,
                'last_execution_at': last_execution.created_at
            }

    async def delete_old_executions(self, days_old: int = 90) -> int:
        """Delete executions older than specified days. Returns count deleted."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        async with self.session_factory() as session:
            result = await session.execute(
                select(WorkflowExecution)
                .where(WorkflowExecution.created_at < cutoff_date)
            )
            old_executions = list(result.scalars().all())

            count = len(old_executions)
            for execution in old_executions:
                await session.delete(execution)

            await session.commit()
            return count


class WorkflowExecutionService:
    """
    Service for managing workflow execution persistence and analytics.

    Provides business logic for creating, updating, and querying workflow
    executions stored in PostgreSQL. Integrates with the workflow engine
    to persist execution history and provide analytics.
    """

    def __init__(self, execution_repository: WorkflowRepository):
        """
        Initialize service with execution repository.

        Args:
            execution_repository: Repository for workflow execution data
        """
        self.execution_repository = execution_repository

    async def create_execution(
        self,
        workflow_id: str,
        workflow_name: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowExecution':
        """
        Create a new workflow execution record.

        Args:
            workflow_id: ID of the workflow being executed
            workflow_name: Name of the workflow (for display)
            user_id: ID of the user initiating execution
            project_id: ID of the project context
            input_data: Input data for the workflow
            execution_metadata: Additional execution metadata

        Returns:
            Created WorkflowExecution instance
        """
        execution_data = {
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'user_id': user_id,
            'project_id': project_id,
            'input_data': input_data or {},
            'execution_metadata': execution_metadata or {},
            'status': WorkflowExecutionStatus.PENDING.value
        }

        return await self.execution_repository.create_workflow_execution(execution_data)

    async def start_execution(self, execution_id: str) -> Optional['WorkflowExecution']:
        """
        Mark execution as started.

        Args:
            execution_id: Execution ID to start

        Returns:
            Updated execution or None if not found
        """
        updates = {
            'status': WorkflowExecutionStatus.RUNNING.value,
            'started_at': datetime.utcnow()
        }
        return await self.execution_repository.update_workflow_execution(execution_id, updates)

    async def complete_execution(
        self,
        execution_id: str,
        success: bool = True,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        vertex_results: Optional[Dict[str, Any]] = None
    ) -> Optional['WorkflowExecution']:
        """
        Mark execution as completed.

        Args:
            execution_id: Execution ID to complete
            success: Whether execution was successful
            output_data: Output data from execution
            error_message: Error message if failed
            vertex_results: Results from individual vertices

        Returns:
            Updated execution or None if not found
        """
        updates = {
            'success': success,
            'output_data': output_data,
            'error_message': error_message,
            'vertex_results': vertex_results,
            'completed_at': datetime.utcnow()
        }

        if success:
            updates['status'] = WorkflowExecutionStatus.COMPLETED.value
        else:
            updates['status'] = WorkflowExecutionStatus.FAILED.value

        execution = await self.execution_repository.update_workflow_execution(execution_id, updates)

        # Calculate duration if we have start and end times
        if execution:
            started_at = getattr(execution, 'started_at', None)
            completed_at = getattr(execution, 'completed_at', None)
            if started_at and completed_at:
                duration = (completed_at - started_at).total_seconds()
                await self.execution_repository.update_workflow_execution(
                    execution_id, {'duration_seconds': duration}
                )

        return execution

    async def fail_execution(
        self,
        execution_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Optional['WorkflowExecution']:
        """
        Mark execution as failed.

        Args:
            execution_id: Execution ID to fail
            error_message: Error message
            error_details: Detailed error information

        Returns:
            Updated execution or None if not found
        """
        updates = {
            'status': WorkflowExecutionStatus.FAILED.value,
            'success': False,
            'error_message': error_message,
            'error_details': error_details,
            'completed_at': datetime.utcnow()
        }

        execution = await self.execution_repository.update_workflow_execution(execution_id, updates)

        # Calculate duration if we have start time
        if execution:
            started_at = getattr(execution, 'started_at', None)
            completed_at = getattr(execution, 'completed_at', None)
            if started_at and completed_at:
                duration = (completed_at - started_at).total_seconds()
                await self.execution_repository.update_workflow_execution(
                    execution_id, {'duration_seconds': duration}
                )

        return execution

    async def get_execution(self, execution_id: str) -> Optional['WorkflowExecution']:
        """
        Get execution by ID.

        Args:
            execution_id: Execution ID to retrieve

        Returns:
            Execution instance or None if not found
        """
        # This method would need to be added to the abstract repository
        # For now, return None
        return None

    async def get_workflow_executions(
        self,
        workflow_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List['WorkflowExecution']:
        """
        Get executions for a workflow.

        Args:
            workflow_id: Workflow ID
            limit: Maximum number of executions to return
            offset: Number of executions to skip

        Returns:
            List of executions
        """
        # This method needs to be added to the abstract repository
        # For now, return empty list
        return []

    async def get_execution_analytics(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get execution analytics for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Analytics dictionary
        """
        return await self.execution_repository.get_execution_analytics(workflow_id)

    async def get_recent_executions(self, limit: int = 10) -> List['WorkflowExecution']:
        """
        Get recent executions across all workflows.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of recent executions
        """
        # This would need to be implemented in the repository
        # For now, return empty list
        return []

    async def cleanup_old_executions(self, days_old: int = 90) -> int:
        """
        Clean up old execution records.

        Args:
            days_old: Delete executions older than this many days

        Returns:
            Number of executions deleted
        """
        # This method would need to be added to the abstract repository
        # For now, return 0
        return 0


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_workflow_service_usage())
