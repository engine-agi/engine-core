"""
from abc import abstractmethod
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime
from typing import Optional, List, Dict, Any
Observability Service Layer - Business Logic for Monitoring and Logging.

The ObservabilityService provides high-level business logic for project observability,
including structured logging, real-time metrics collection, performance monitoring,
and health status tracking across all engine components.

Key Features:
- Structured logging with correlation IDs
- Real-time metrics collection and aggregation
- Performance monitoring and alerting
- Health status tracking for all components
- Log filtering and search capabilities
- Metrics aggregation and reporting
- WebSocket streaming for real-time updates

Architecture:
- Service Layer (this) -> Repository Layer -> Models -> Database
- Integration with all Engine Framework components
- Event-driven metrics collection
- Configurable retention policies
"""
import asyncio
import logging
import uuid
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    pass  # Remove model imports that don't exist yet

logger = logging.getLogger(__name__)


class ObservabilityServiceError(Exception):
    """Base exception for observability service errors."""
    pass


class LogNotFoundError(ObservabilityServiceError):
    """Raised when a log entry is not found."""
    pass


class MetricsCollectionError(ObservabilityServiceError):
    """Raised when metrics collection fails."""
    pass


@dataclass
class LogFilter:
    """Filter criteria for log queries."""
    level: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@dataclass
class LogResult:
    """Result of a log query."""
    logs: List[Dict[str, Any]]
    total: int
    has_more: bool


@dataclass
class AgentMetrics:
    """Agent-related metrics."""
    total: int = 0
    active: int = 0
    idle: int = 0
    processing: int = 0
    error: int = 0


@dataclass
class TeamMetrics:
    """Team-related metrics."""
    total: int = 0
    active: int = 0
    executing: int = 0
    disbanded: int = 0


@dataclass
class WorkflowMetrics:
    """Workflow-related metrics."""
    total: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    paused: int = 0


@dataclass
class ProjectMetricsData:
    """Comprehensive project metrics."""
    agents: AgentMetrics
    teams: TeamMetrics
    workflows: WorkflowMetrics
    success_rate: float = 0.0
    average_response_time: float = 0.0
    total_requests: int = 0
    error_count: int = 0
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


@dataclass
class PerformanceMetricsData:
    """System performance metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_connections: int = 0
    requests_per_second: float = 0.0
    average_latency_ms: float = 0.0
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


@dataclass
class ComponentHealth:
    """Health status of a component."""
    status: str = "unknown"  # "healthy", "degraded", "unhealthy", "unknown"
    healthy_count: int = 0
    total_count: int = 0
    error_rate: float = 0.0


@dataclass
class ComponentsHealth:
    """Health status of all components."""
    agents: ComponentHealth
    teams: ComponentHealth
    workflows: ComponentHealth
    tools: ComponentHealth


@dataclass
class ProjectHealthData:
    """Overall project health status."""
    components: ComponentsHealth
    status: str = "unknown"  # "healthy", "degraded", "unhealthy"
    error_rate: float = 0.0
    availability: float = 0.0
    last_updated: Optional[datetime] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class ObservabilityRepository(ABC):
    """Abstract repository interface for observability data access."""

    @abstractmethod
    async def save_log_entry(self, log_data: Dict[str, Any]) -> str:
        """Save a log entry to the database."""
        pass

    @abstractmethod
    async def get_logs(self, project_id: str, filter_criteria: LogFilter) -> LogResult:
        """Get logs with filtering and pagination."""
        pass

    @abstractmethod
    async def get_project_metrics(self, project_id: str) -> ProjectMetricsData:
        """Get current project metrics."""
        pass

    @abstractmethod
    async def get_performance_metrics(self, project_id: str) -> PerformanceMetricsData:
        """Get current performance metrics."""
        pass

    @abstractmethod
    async def get_project_health(self, project_id: str) -> ProjectHealthData:
        """Get project health status."""
        pass

    @abstractmethod
    async def update_metrics(self,
                             project_id: str,
                             metrics_type: str,
                             data: Dict[str,
                                        Any]) -> None:
        """Update metrics data."""
        pass


class MockObservabilityRepository(ObservabilityRepository):
    """Mock repository implementation for testing and development."""

    def __init__(self):
        self._logs: Dict[str, List[Dict[str, Any]]] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}

    async def save_log_entry(self, log_data: Dict[str, Any]) -> str:
        """Save a log entry to mock storage."""
        project_id = log_data.get('project_id', 'default')
        if project_id not in self._logs:
            self._logs[project_id] = []

        log_id = str(uuid.uuid4())
        log_data['id'] = log_id
        log_data['timestamp'] = datetime.utcnow().isoformat()

        self._logs[project_id].append(log_data)
        return log_id

    async def get_logs(self, project_id: str, filter_criteria: LogFilter) -> LogResult:
        """Get logs from mock storage with filtering."""
        if project_id not in self._logs:
            return LogResult(logs=[], total=0, has_more=False)

        logs = self._logs[project_id]

        # Apply filters
        filtered_logs = []
        for log in logs:
            if filter_criteria.level and log.get('level') != filter_criteria.level:
                continue
            if filter_criteria.entity_type and log.get(
                    'entity_type') != filter_criteria.entity_type:
                continue
            if filter_criteria.entity_id and log.get(
                    'entity_id') != filter_criteria.entity_id:
                continue

            timestamp_str = log.get('timestamp')
            if timestamp_str is not None:
                if filter_criteria.start_time and timestamp_str < filter_criteria.start_time.isoformat():
                    continue
                if filter_criteria.end_time and timestamp_str > filter_criteria.end_time.isoformat():
                    continue

            filtered_logs.append(log)

        # Sort by timestamp (most recent first)
        filtered_logs.sort(key=lambda x: x['timestamp'], reverse=True)

        # Apply pagination
        total = len(filtered_logs)
        start_idx = filter_criteria.offset
        end_idx = start_idx + filter_criteria.limit
        paginated_logs = filtered_logs[start_idx:end_idx]

        return LogResult(
            logs=paginated_logs,
            total=total,
            has_more=end_idx < total
        )

    async def get_project_metrics(self, project_id: str) -> ProjectMetricsData:
        """Get mock project metrics."""
        return ProjectMetricsData(
            agents=AgentMetrics(total=5, active=3, idle=1, processing=1),
            teams=TeamMetrics(total=2, active=1, executing=1),
            workflows=WorkflowMetrics(total=10, running=2, completed=7, failed=1),
            success_rate=0.85,
            average_response_time=2.5,
            total_requests=1000,
            error_count=150
        )

    async def get_performance_metrics(self, project_id: str) -> PerformanceMetricsData:
        """Get mock performance metrics."""
        return PerformanceMetricsData(
            cpu_usage=45.2,
            memory_usage=67.8,
            active_connections=12,
            requests_per_second=8.5,
            average_latency_ms=125.3
        )

    async def get_project_health(self, project_id: str) -> ProjectHealthData:
        """Get mock project health data."""
        return ProjectHealthData(
            status="healthy",
            components=ComponentsHealth(
                agents=ComponentHealth(
                    status="healthy",
                    healthy_count=4,
                    total_count=5,
                    error_rate=0.05),
                teams=ComponentHealth(
                    status="healthy",
                    healthy_count=2,
                    total_count=2,
                    error_rate=0.0),
                workflows=ComponentHealth(
                    status="degraded",
                    healthy_count=8,
                    total_count=10,
                    error_rate=0.15),
                tools=ComponentHealth(
                    status="healthy",
                    healthy_count=15,
                    total_count=15,
                    error_rate=0.02)),
            error_rate=0.08,
            availability=0.95)

    async def update_metrics(self,
                             project_id: str,
                             metrics_type: str,
                             data: Dict[str,
                                        Any]) -> None:
        """Update mock metrics data."""
        if project_id not in self._metrics:
            self._metrics[project_id] = {}
        self._metrics[project_id][metrics_type] = data


class ObservabilityService:
    """
    Service layer for observability and monitoring.

    Provides comprehensive observability features including:
    - Structured logging with filtering and search
    - Real-time metrics collection and aggregation
    - Performance monitoring and alerting
    - Health status tracking and reporting
    - WebSocket streaming for live updates
    """

    def __init__(self, repository: Optional[ObservabilityRepository] = None):
        """Initialize observability service."""
        self.repository = repository or MockObservabilityRepository()
        self.logger = logging.getLogger(__name__)

    async def log_event(
        self,
        project_id: str,
        level: str,
        message: str,
        entity_type: str,
        entity_id: str,
        action: str,
        duration_ms: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log an event with structured data.

        Args:
            project_id: The project ID
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            entity_type: Type of entity (agent, team, workflow, etc.)
            entity_id: ID of the entity
            action: Action performed
            duration_ms: Duration in milliseconds (optional)
            additional_data: Additional structured data (optional)
            user_id: User ID who triggered the event (optional)

        Returns:
            Log entry ID
        """
        try:
            log_data = {
                'project_id': project_id,
                'level': level.upper(),
                'message': message,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'action': action,
                'duration_ms': duration_ms,
                'additional_data': additional_data or {},
                'user_id': user_id,
                'correlation_id': str(uuid.uuid4())
            }

            log_id = await self.repository.save_log_entry(log_data)

            # Log to system logger as well
            log_level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }

            system_logger = logging.getLogger(f"project.{project_id}")
            system_logger.log(
                log_level_map.get(level.upper(), logging.INFO),
                f"[{entity_type}:{entity_id}] {action}: {message}",
                extra={'correlation_id': log_data['correlation_id']}
            )

            return log_id

        except Exception as e:
            self.logger.error(f"Failed to log event: {str(e)}")
            raise ObservabilityServiceError(f"Failed to log event: {str(e)}")

    async def get_logs(
        self,
        project_id: str,
        level_filter: Optional[str] = None,
        entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> LogResult:
        """
        Get logs with filtering and pagination.

        Args:
            project_id: The project ID
            level_filter: Filter by log level
            entity_type_filter: Filter by entity type
            entity_id_filter: Filter by entity ID
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            LogResult with logs and metadata
        """
        try:
            filter_criteria = LogFilter(
                level=level_filter,
                entity_type=entity_type_filter,
                entity_id=entity_id_filter,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                offset=offset
            )

            return await self.repository.get_logs(project_id, filter_criteria)

        except Exception as e:
            self.logger.error(f"Failed to get logs for project {project_id}: {str(e)}")
            raise ObservabilityServiceError(f"Failed to get logs: {str(e)}")

    async def get_project_metrics(self, project_id: str) -> ProjectMetricsData:
        """
        Get current project metrics.

        Args:
            project_id: The project ID

        Returns:
            Current project metrics
        """
        try:
            return await self.repository.get_project_metrics(project_id)

        except Exception as e:
            self.logger.error(
                f"Failed to get project metrics for {project_id}: {
                    str(e)}")
            raise MetricsCollectionError(f"Failed to get project metrics: {str(e)}")

    async def get_performance_metrics(self, project_id: str) -> PerformanceMetricsData:
        """
        Get current performance metrics.

        Args:
            project_id: The project ID

        Returns:
            Current performance metrics
        """
        try:
            return await self.repository.get_performance_metrics(project_id)

        except Exception as e:
            self.logger.error(
                f"Failed to get performance metrics for {project_id}: {
                    str(e)}")
            raise MetricsCollectionError(f"Failed to get performance metrics: {str(e)}")

    async def get_project_health(self, project_id: str) -> ProjectHealthData:
        """
        Get project health status.

        Args:
            project_id: The project ID

        Returns:
            Current project health status
        """
        try:
            return await self.repository.get_project_health(project_id)

        except Exception as e:
            self.logger.error(
                f"Failed to get project health for {project_id}: {
                    str(e)}")
            raise ObservabilityServiceError(f"Failed to get project health: {str(e)}")

    async def update_component_metrics(
        self,
        project_id: str,
        component_type: str,
        component_id: str,
        metrics_data: Dict[str, Any]
    ) -> None:
        """
        Update metrics for a specific component.

        Args:
            project_id: The project ID
            component_type: Type of component (agent, team, workflow, etc.)
            component_id: ID of the component
            metrics_data: Metrics data to update
        """
        try:
            metrics_key = f"{component_type}:{component_id}"
            await self.repository.update_metrics(project_id, metrics_key, metrics_data)

        except Exception as e:
            self.logger.error(
                f"Failed to update metrics for {component_type}:{component_id}: {
                    str(e)}")
            raise MetricsCollectionError(
                f"Failed to update component metrics: {str(e)}")

    async def get_component_logs(
        self,
        project_id: str,
        component_type: str,
        component_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get logs for a specific component.

        Args:
            project_id: The project ID
            component_type: Type of component
            component_id: ID of the component
            limit: Maximum number of log entries

        Returns:
            List of log entries for the component
        """
        try:
            result = await self.get_logs(
                project_id=project_id,
                entity_type_filter=component_type,
                entity_id_filter=component_id,
                limit=limit
            )
            return result.logs

        except Exception as e:
            self.logger.error(
                f"Failed to get component logs for {component_type}:{component_id}: {
                    str(e)}")
            raise ObservabilityServiceError(f"Failed to get component logs: {str(e)}")

    async def get_error_summary(
        self,
        project_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get error summary for a project.

        Args:
            project_id: The project ID
            start_time: Start time for error analysis
            end_time: End time for error analysis

        Returns:
            Error summary statistics
        """
        try:
            # Get error logs
            error_logs = await self.get_logs(
                project_id=project_id,
                level_filter="ERROR",
                start_time=start_time,
                end_time=end_time,
                limit=1000
            )

            # Analyze errors by component
            error_by_component = {}
            error_by_type = {}

            for log in error_logs.logs:
                component_key = f"{log['entity_type']}:{log['entity_id']}"
                error_by_component[component_key] = error_by_component.get(
                    component_key, 0) + 1

                error_type = log.get('additional_data', {}).get('error_type', 'unknown')
                error_by_type[error_type] = error_by_type.get(error_type, 0) + 1

            return {
                'total_errors': error_logs.total,
                'errors_by_component': error_by_component,
                'errors_by_type': error_by_type,
                'time_range': {
                    'start': start_time.isoformat() if start_time else None,
                    'end': end_time.isoformat() if end_time else None
                }
            }

        except Exception as e:
            self.logger.error(
                f"Failed to get error summary for project {project_id}: {
                    str(e)}")
            raise ObservabilityServiceError(f"Failed to get error summary: {str(e)}")
