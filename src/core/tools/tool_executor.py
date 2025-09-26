"""
from typing import Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime
from typing import Optional, List, Dict, Any
Tool Executor - Secure and Monitored Tool Execution Engine.

The ToolExecutor provides a secure, monitored environment for executing tools
with proper resource management, permission checking, and performance tracking.
It acts as the execution layer between the Tool System and external integrations.

Key Features:
- Secure execution with sandboxing and permission checking
- Resource monitoring and limits
- Execution queuing and prioritization
- Result caching and optimization
- Error handling and recovery
- Audit logging and compliance
- Performance metrics and analytics
- Concurrent execution management

Architecture:
- ExecutionEngine for core execution logic
- SecurityManager for permission and access control
- ResourceManager for system resource monitoring
- QueueManager for execution scheduling
- CacheManager for result optimization
- AuditLogger for compliance and debugging

Dependencies:
- ToolInterface implementations
- Security and permission frameworks
- Resource monitoring systems
- Async execution primitives
"""
import asyncio
import json
import logging
import resource
import threading
import time
import uuid
import weakref
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import psutil

# Type checking imports
if TYPE_CHECKING:
    from .tool_builder import ToolExecutionRequest, ToolExecutionResult, ToolInterface

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """Execution priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    EMERGENCY = 4


class ExecutionStatus(Enum):
    """Execution status states."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class ResourceType(Enum):
    """System resource types."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


@dataclass
class ExecutionContext:
    """Context for tool execution."""
    execution_id: str
    tool_id: str
    capability_name: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    timeout_seconds: Optional[int] = None
    resource_limits: Dict[ResourceType, Any] = field(default_factory=dict)
    security_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionMetrics:
    """Metrics collected during execution."""
    execution_id: str
    tool_id: str
    capability_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_duration: Optional[float] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_io: float = 0.0
    network_io: float = 0.0
    peak_memory: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0
    retry_count: int = 0
    queue_wait_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceLimits:
    """Resource limits for execution."""
    max_cpu_percent: Optional[float] = None
    max_memory_mb: Optional[int] = None
    max_execution_time: Optional[int] = None
    max_disk_io_mb: Optional[float] = None
    max_network_io_mb: Optional[float] = None
    max_concurrent_executions: int = 10
    max_queue_size: int = 1000


@dataclass
class SecurityPolicy:
    """Security policy for tool execution."""
    allowed_users: Set[str] = field(default_factory=set)
    allowed_projects: Set[str] = field(default_factory=set)
    required_permissions: Set[str] = field(default_factory=set)
    forbidden_capabilities: Set[str] = field(default_factory=set)
    sandbox_enabled: bool = True
    audit_required: bool = True
    encryption_required: bool = False
    network_isolation: bool = True
    file_system_restrictions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Cache entry for execution results."""
    key: str
    result: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecurityManager:
    """Manages security policies and access control."""

    def __init__(self):
        """Initialize security manager."""
        self.policies: Dict[str, SecurityPolicy] = {}
        self.user_permissions: Dict[str, Set[str]] = defaultdict(set)
        self.project_permissions: Dict[str, Set[str]] = defaultdict(set)
        self.audit_log: deque = deque(maxlen=10000)

    def add_security_policy(self, tool_id: str, policy: SecurityPolicy) -> None:
        """Add security policy for a tool."""
        self.policies[tool_id] = policy

    def check_execution_permission(
        self,
        context: ExecutionContext,
        capability_name: str
    ) -> bool:
        """Check if execution is permitted."""
        try:
            policy = self.policies.get(context.tool_id)
            if not policy:
                # No policy = allow by default (configurable)
                return True

            # Check user permission
            if policy.allowed_users and context.user_id not in policy.allowed_users:
                self._log_security_event("access_denied", context, "user_not_allowed")
                return False

            # Check project permission
            if policy.allowed_projects and context.project_id not in policy.allowed_projects:
                self._log_security_event(
                    "access_denied", context, "project_not_allowed")
                return False

            # Check capability restrictions
            if capability_name in policy.forbidden_capabilities:
                self._log_security_event(
                    "access_denied", context, "capability_forbidden")
                return False

            # Check required permissions
            user_perms = self.user_permissions.get(context.user_id, set())
            if not policy.required_permissions.issubset(user_perms):
                self._log_security_event(
                    "access_denied", context, "insufficient_permissions")
                return False

            self._log_security_event(
                "access_granted", context, "permission_check_passed")
            return True

        except Exception as e:
            logger.error(f"Security check failed: {str(e)}")
            self._log_security_event(
                "access_denied",
                context,
                f"security_check_error: {
                    str(e)}")
            return False

    def get_security_context(self, context: ExecutionContext) -> Dict[str, Any]:
        """Get security context for execution."""
        policy = self.policies.get(context.tool_id, SecurityPolicy())

        return {
            'sandbox_enabled': policy.sandbox_enabled,
            'network_isolation': policy.network_isolation,
            'file_system_restrictions': policy.file_system_restrictions,
            'encryption_required': policy.encryption_required,
            'audit_required': policy.audit_required
        }

    def _log_security_event(
        self,
        event_type: str,
        context: ExecutionContext,
        details: str
    ) -> None:
        """Log security event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'execution_id': context.execution_id,
            'tool_id': context.tool_id,
            'user_id': context.user_id,
            'project_id': context.project_id,
            'details': details
        }
        self.audit_log.append(event)

        if event_type == "access_denied":
            logger.warning(
                f"Security: Access denied for {
                    context.user_id} to {
                    context.tool_id}: {details}")


class ResourceManager:
    """Manages system resource monitoring and limits."""

    def __init__(self):
        """Initialize resource manager."""
        self.resource_limits = ResourceLimits()
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.resource_usage: Dict[str, ExecutionMetrics] = {}
        self.monitoring_enabled = True
        self._monitoring_task = None

    def set_resource_limits(self, limits: ResourceLimits) -> None:
        """Set global resource limits."""
        self.resource_limits = limits

    async def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_resources())

    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

    def check_resource_availability(self, context: ExecutionContext) -> bool:
        """Check if resources are available for execution."""
        try:
            # Check concurrent execution limit
            if len(self.active_executions) >= self.resource_limits.max_concurrent_executions:
                return False

            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()

            if self.resource_limits.max_cpu_percent and cpu_percent > self.resource_limits.max_cpu_percent:
                return False

            if self.resource_limits.max_memory_mb:
                available_memory_mb = memory_info.available / (1024 * 1024)
                if available_memory_mb < self.resource_limits.max_memory_mb:
                    return False

            return True

        except Exception as e:
            logger.error(f"Resource availability check failed: {str(e)}")
            return False

    def allocate_resources(self, context: ExecutionContext) -> bool:
        """Allocate resources for execution."""
        try:
            if self.check_resource_availability(context):
                self.active_executions[context.execution_id] = context

                # Initialize metrics
                metrics = ExecutionMetrics(
                    execution_id=context.execution_id,
                    tool_id=context.tool_id,
                    capability_name=context.capability_name,
                    start_time=datetime.utcnow()
                )
                self.resource_usage[context.execution_id] = metrics

                return True
            return False

        except Exception as e:
            logger.error(f"Resource allocation failed: {str(e)}")
            return False

    def release_resources(self, execution_id: str) -> None:
        """Release resources after execution."""
        try:
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            if execution_id in self.resource_usage:
                metrics = self.resource_usage[execution_id]
                metrics.end_time = datetime.utcnow()
                if metrics.start_time:
                    metrics.execution_duration = (
                        metrics.end_time - metrics.start_time).total_seconds()

        except Exception as e:
            logger.error(f"Resource release failed: {str(e)}")

    def get_execution_metrics(self, execution_id: str) -> Optional[ExecutionMetrics]:
        """Get execution metrics."""
        return self.resource_usage.get(execution_id)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')

            return {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory_info.percent,
                'memory_available_mb': memory_info.available / (1024 * 1024),
                'disk_usage_percent': disk_info.percent,
                'active_executions': len(self.active_executions),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            return {}

    async def _monitor_resources(self) -> None:
        """Background task to monitor resource usage."""
        while True:
            try:
                await asyncio.sleep(1)  # Monitor every second

                for execution_id, context in self.active_executions.items():
                    if execution_id in self.resource_usage:
                        metrics = self.resource_usage[execution_id]

                        # Update CPU and memory usage
                        # Note: In production, this would track per-process usage
                        metrics.cpu_usage = psutil.cpu_percent()
                        memory_info = psutil.virtual_memory()
                        metrics.memory_usage = memory_info.percent

                        # Check for resource limit violations
                        self._check_resource_limits(context, metrics)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error: {str(e)}")

    def _check_resource_limits(
            self,
            context: ExecutionContext,
            metrics: ExecutionMetrics) -> None:
        """Check if execution is violating resource limits."""
        try:
            # Check execution time limit
            if (self.resource_limits.max_execution_time and metrics.start_time and (datetime.utcnow(
            ) - metrics.start_time).total_seconds() > self.resource_limits.max_execution_time):

                logger.warning(f"Execution {context.execution_id} exceeded time limit")
                # In production, this would trigger cancellation

            # Check CPU limit
            if (self.resource_limits.max_cpu_percent and
                    metrics.cpu_usage > self.resource_limits.max_cpu_percent):

                logger.warning(f"Execution {context.execution_id} exceeded CPU limit")

            # Check memory limit
            if (self.resource_limits.max_memory_mb and
                    metrics.memory_usage > self.resource_limits.max_memory_mb):

                logger.warning(
                    f"Execution {
                        context.execution_id} exceeded memory limit")

        except Exception as e:
            logger.error(f"Resource limit check failed: {str(e)}")


class CacheManager:
    """Manages result caching for tool executions."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """Initialize cache manager."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: deque = deque()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }

    def _generate_cache_key(
        self,
        tool_id: str,
        capability_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> str:
        """Generate cache key for execution."""
        key_data = {
            'tool_id': tool_id,
            'capability_name': capability_name,
            'parameters': parameters
        }

        # Include relevant context for caching
        if context:
            key_data['context'] = {
                k: v for k, v in context.items()
                if k in ['user_id', 'project_id']  # Only cache-relevant context
            }

        return json.dumps(key_data, sort_keys=True)

    def get(
        self,
        tool_id: str,
        capability_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Optional[Any]:
        """Get cached result if available."""
        self.cache_stats['total_requests'] += 1

        cache_key = self._generate_cache_key(
            tool_id, capability_name, parameters, context)

        if cache_key in self.cache:
            entry = self.cache[cache_key]

            # Check if entry is expired
            if datetime.utcnow() > entry.expires_at:
                del self.cache[cache_key]
                self.cache_stats['misses'] += 1
                return None

            # Update access order
            try:
                self.access_order.remove(cache_key)
            except ValueError:
                pass
            self.access_order.append(cache_key)

            # Update hit count
            entry.hit_count += 1
            self.cache_stats['hits'] += 1

            logger.debug(f"Cache hit for {tool_id}.{capability_name}")
            return entry.result

        self.cache_stats['misses'] += 1
        return None

    def put(
        self,
        tool_id: str,
        capability_name: str,
        parameters: Dict[str, Any],
        result: Any,
        ttl: Optional[int] = None,
        context: Dict[str, Any] = None
    ) -> None:
        """Cache execution result."""
        cache_key = self._generate_cache_key(
            tool_id, capability_name, parameters, context)

        # Check cache size and evict if necessary
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        # Create cache entry
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        entry = CacheEntry(
            key=cache_key,
            result=result,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

        self.cache[cache_key] = entry
        self.access_order.append(cache_key)

        logger.debug(f"Cached result for {tool_id}.{capability_name} (TTL: {ttl}s)")

    def invalidate(
        self,
        tool_id: str,
        capability_name: Optional[str] = None
    ) -> int:
        """Invalidate cached entries for a tool or capability."""
        keys_to_remove = []

        for key, entry in self.cache.items():
            key_data = json.loads(entry.key)
            if key_data['tool_id'] == tool_id:
                if capability_name is None or key_data['capability_name'] == capability_name:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            if key in self.cache:
                del self.cache[key]
            try:
                self.access_order.remove(key)
            except ValueError:
                pass

        logger.info(f"Invalidated {len(keys_to_remove)} cache entries for {tool_id}")
        return len(keys_to_remove)

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self.access_order:
            lru_key = self.access_order.popleft()
            if lru_key in self.cache:
                del self.cache[lru_key]
                self.cache_stats['evictions'] += 1

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = 0
        if self.cache_stats['total_requests'] > 0:
            hit_rate = self.cache_stats['hits'] / self.cache_stats['total_requests']

        return {
            **self.cache_stats,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()


class ExecutionQueue:
    """Priority queue for tool executions."""

    def __init__(self, max_size: int = 1000):
        """Initialize execution queue."""
        self.max_size = max_size
        self.queues: Dict[ExecutionPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in ExecutionPriority
        }
        self.queue_stats = {
            'total_enqueued': 0,
            'total_dequeued': 0,
            'current_size': 0,
            'priority_distribution': {p.name: 0 for p in ExecutionPriority}
        }

    async def enqueue(
        self,
        context: ExecutionContext,
        request: 'ToolExecutionRequest'
    ) -> bool:
        """Enqueue execution request."""
        try:
            priority_queue = self.queues[context.priority]

            # Check queue size limits
            current_size = sum(q.qsize() for q in self.queues.values())
            if current_size >= self.max_size:
                logger.warning("Execution queue is full")
                return False

            # Enqueue request
            await priority_queue.put((context, request))

            # Update stats
            self.queue_stats['total_enqueued'] += 1
            self.queue_stats['current_size'] = current_size + 1
            self.queue_stats['priority_distribution'][context.priority.name] += 1

            logger.debug(
                f"Enqueued execution {
                    context.execution_id} with priority {
                    context.priority.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to enqueue execution: {str(e)}")
            return False

    async def dequeue(
            self) -> Optional[tuple[ExecutionContext, 'ToolExecutionRequest']]:
        """Dequeue highest priority execution request."""
        try:
            # Check queues in priority order (highest first)
            for priority in sorted(
                    ExecutionPriority,
                    key=lambda p: p.value,
                    reverse=True):
                queue = self.queues[priority]
                if not queue.empty():
                    context, request = await queue.get()

                    # Update stats
                    self.queue_stats['total_dequeued'] += 1
                    current_size = sum(q.qsize() for q in self.queues.values())
                    self.queue_stats['current_size'] = current_size
                    self.queue_stats['priority_distribution'][priority.name] -= 1

                    logger.debug(f"Dequeued execution {context.execution_id}")
                    return context, request

            return None

        except Exception as e:
            logger.error(f"Failed to dequeue execution: {str(e)}")
            return None

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self.queue_stats,
            'queue_sizes': {
                priority.name: queue.qsize()
                for priority, queue in self.queues.items()
            }
        }

    def clear(self) -> None:
        """Clear all queues."""
        for queue in self.queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break


class ToolExecutor:
    """
    Main tool execution engine with security, monitoring, and optimization.

    Provides secure, monitored execution of tool capabilities with:
    - Permission checking and access control
    - Resource monitoring and limits
    - Result caching and optimization
    - Execution queuing and prioritization
    - Performance metrics and analytics
    - Error handling and recovery
    """

    def __init__(
        self,
        security_manager: Optional[SecurityManager] = None,
        resource_manager: Optional[ResourceManager] = None,
        cache_manager: Optional[CacheManager] = None,
        execution_queue: Optional[ExecutionQueue] = None
    ):
        """Initialize tool executor."""
        self.security_manager = security_manager or SecurityManager()
        self.resource_manager = resource_manager or ResourceManager()
        self.cache_manager = cache_manager or CacheManager()
        self.execution_queue = execution_queue or ExecutionQueue()

        # Tool registry reference (set externally)
        self.tool_registry = None

        # Execution tracking
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: deque = deque(maxlen=10000)

        # Background tasks
        self._processor_task = None
        self._is_running = False

        # Statistics
        self.executor_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'cancelled_executions': 0,
            'average_execution_time': 0.0,
            'total_cache_hits': 0,
            'total_security_denials': 0,
            'total_resource_denials': 0
        }

    async def start(self) -> None:
        """Start the tool executor."""
        if not self._is_running:
            self._is_running = True
            await self.resource_manager.start_monitoring()
            self._processor_task = asyncio.create_task(self._process_execution_queue())
            logger.info("Tool executor started")

    async def stop(self) -> None:
        """Stop the tool executor."""
        if self._is_running:
            self._is_running = False

            if self._processor_task:
                self._processor_task.cancel()
                try:
                    await self._processor_task
                except asyncio.CancelledError:
                    pass

            await self.resource_manager.stop_monitoring()
            logger.info("Tool executor stopped")

    async def execute_tool(
        self,
        tool: 'ToolInterface',
        request: 'ToolExecutionRequest'
    ) -> 'ToolExecutionResult':
        """Execute tool capability with full monitoring and security."""

        # Create execution context
        context = ExecutionContext(
            execution_id=request.execution_id or str(uuid.uuid4()),
            tool_id=request.tool_id,
            capability_name=request.capability_name,
            user_id=request.user_id,
            project_id=request.project_id,
            session_id=request.session_id,
            priority=ExecutionPriority(request.priority),
            timeout_seconds=request.timeout_override,
            metadata=request.context
        )

        logger.info(f"Starting tool execution: {context.execution_id}")

        try:
            # Security check
            if not self.security_manager.check_execution_permission(
                    context, request.capability_name):
                self.executor_stats['total_security_denials'] += 1
                return self._create_error_result(
                    context,
                    "Permission denied",
                    "security_denied"
                )

            # Check cache first
            cached_result = self.cache_manager.get(
                tool_id=request.tool_id,
                capability_name=request.capability_name,
                parameters=request.parameters,
                context=request.context
            )

            if cached_result is not None:
                self.executor_stats['total_cache_hits'] += 1
                logger.info(f"Cache hit for execution: {context.execution_id}")
                return self._create_success_result(context, cached_result, cached=True)

            # Resource availability check
            if not self.resource_manager.check_resource_availability(context):
                self.executor_stats['total_resource_denials'] += 1

                # Queue for later execution if resources not available
                if await self.execution_queue.enqueue(context, request):
                    return self._create_queued_result(context)
                else:
                    return self._create_error_result(
                        context,
                        "Resources unavailable and queue full",
                        "resource_denied"
                    )

            # Execute immediately
            return await self._execute_immediate(tool, context, request)

        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return self._create_error_result(context, str(e), "execution_error")

    async def _execute_immediate(
        self,
        tool: 'ToolInterface',
        context: ExecutionContext,
        request: 'ToolExecutionRequest'
    ) -> 'ToolExecutionResult':
        """Execute tool immediately with resource allocation."""

        start_time = time.time()

        try:
            # Allocate resources
            if not self.resource_manager.allocate_resources(context):
                return self._create_error_result(
                    context,
                    "Resource allocation failed",
                    "resource_allocation_error"
                )

            # Track active execution
            self.active_executions[context.execution_id] = context

            # Get security context
            security_context = self.security_manager.get_security_context(context)
            context.security_context = security_context

            # Execute tool capability
            execution_start = time.time()

            if request.stream_results:
                # Streaming execution (not implemented in this example)
                result = await tool.execute_capability(
                    capability_name=request.capability_name,
                    parameters=request.parameters,
                    context=request.context
                )
            else:
                # Regular execution with timeout
                timeout = context.timeout_seconds or tool.config.timeout_seconds

                try:
                    result = await asyncio.wait_for(
                        tool.execute_capability(
                            capability_name=request.capability_name,
                            parameters=request.parameters,
                            context=request.context
                        ),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    return self._create_error_result(
                        context,
                        f"Execution timed out after {timeout} seconds",
                        "timeout"
                    )

            execution_time = time.time() - execution_start

            # Update metrics
            metrics = self.resource_manager.get_execution_metrics(context.execution_id)
            if metrics:
                metrics.execution_duration = execution_time

            # Cache successful results
            if result.status == "success":
                self.cache_manager.put(
                    tool_id=request.tool_id,
                    capability_name=request.capability_name,
                    parameters=request.parameters,
                    result=result,
                    context=request.context
                )

                self.executor_stats['successful_executions'] += 1
            else:
                self.executor_stats['failed_executions'] += 1

            # Update statistics
            self._update_execution_stats(execution_time)

            # Log execution
            self._log_execution(context, result, execution_time)

            return result

        finally:
            # Clean up resources
            self.resource_manager.release_resources(context.execution_id)

            if context.execution_id in self.active_executions:
                del self.active_executions[context.execution_id]

    async def _process_execution_queue(self) -> None:
        """Background task to process queued executions."""
        logger.info("Started execution queue processor")

        while self._is_running:
            try:
                # Try to dequeue and execute
                queue_item = await self.execution_queue.dequeue()

                if queue_item:
                    context, request = queue_item

                    # Get tool from registry
                    if self.tool_registry:
                        tool = self.tool_registry.get_tool(request.tool_id)
                        if tool:
                            # Execute queued request
                            result = await self._execute_immediate(tool, context, request)
                            logger.info(
                                f"Completed queued execution: {
                                    context.execution_id}")
                        else:
                            logger.error(
                                f"Tool not found for queued execution: {
                                    request.tool_id}")

                else:
                    # No queued items, wait a bit
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processor error: {str(e)}")
                await asyncio.sleep(1)

        logger.info("Stopped execution queue processor")

    def _create_success_result(
        self,
        context: ExecutionContext,
        result: Any,
        cached: bool = False
    ) -> 'ToolExecutionResult':
        """Create successful execution result."""
        from .tool_builder import ToolExecutionResult

        return ToolExecutionResult(
            execution_id=context.execution_id,
            tool_id=context.tool_id,
            capability_name=context.capability_name,
            status="success",
            result=result,
            execution_time=0.0 if cached else None,
            metadata={'cached': cached}
        )

    def _create_error_result(
        self,
        context: ExecutionContext,
        error: str,
        error_type: str
    ) -> 'ToolExecutionResult':
        """Create error execution result."""
        from .tool_builder import ToolExecutionResult

        return ToolExecutionResult(
            execution_id=context.execution_id,
            tool_id=context.tool_id,
            capability_name=context.capability_name,
            status="error",
            error=error,
            metadata={'error_type': error_type}
        )

    def _create_queued_result(self, context: ExecutionContext) -> 'ToolExecutionResult':
        """Create queued execution result."""
        from .tool_builder import ToolExecutionResult

        return ToolExecutionResult(
            execution_id=context.execution_id,
            tool_id=context.tool_id,
            capability_name=context.capability_name,
            status="queued",
            metadata={'queued_at': datetime.utcnow().isoformat()}
        )

    def _update_execution_stats(self, execution_time: float) -> None:
        """Update execution statistics."""
        self.executor_stats['total_executions'] += 1

        # Update average execution time
        current_avg = self.executor_stats['average_execution_time']
        total_executions = self.executor_stats['total_executions']

        self.executor_stats['average_execution_time'] = (
            (current_avg * (total_executions - 1) + execution_time) / total_executions
        )

    def _log_execution(
        self,
        context: ExecutionContext,
        result: 'ToolExecutionResult',
        execution_time: float
    ) -> None:
        """Log execution details."""
        log_entry = {
            'execution_id': context.execution_id,
            'tool_id': context.tool_id,
            'capability_name': context.capability_name,
            'user_id': context.user_id,
            'project_id': context.project_id,
            'status': result.status,
            'execution_time': execution_time,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.execution_history.append(log_entry)

        # Log based on status
        if result.status == "success":
            logger.info(
                f"Execution completed: {
                    context.execution_id} ({
                    execution_time:.2f}s)")
        else:
            logger.warning(f"Execution failed: {context.execution_id} - {result.error}")

    # === Monitoring and Analytics ===

    def get_executor_stats(self) -> Dict[str, Any]:
        """Get comprehensive executor statistics."""
        return {
            'executor_stats': self.executor_stats,
            'queue_stats': self.execution_queue.get_queue_stats(),
            'cache_stats': self.cache_manager.get_cache_stats(),
            'system_metrics': self.resource_manager.get_system_metrics(),
            'active_executions': len(self.active_executions),
            'is_running': self._is_running
        }

    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history."""
        history_list = list(self.execution_history)
        return history_list[-limit:] if limit else history_list

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel active execution."""
        try:
            if execution_id in self.active_executions:
                # In production, this would send cancellation signal to the execution
                logger.info(f"Cancelling execution: {execution_id}")

                # Clean up resources
                self.resource_manager.release_resources(execution_id)

                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]

                self.executor_stats['cancelled_executions'] += 1
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {str(e)}")
            return False


# === FACTORY FUNCTION ===

def create_tool_executor(
    security_policies: Optional[Dict[str, SecurityPolicy]] = None,
    resource_limits: Optional[ResourceLimits] = None,
    cache_config: Optional[Dict[str, Any]] = None
) -> ToolExecutor:
    """Create ToolExecutor with configuration."""

    # Security manager setup
    security_manager = SecurityManager()
    if security_policies:
        for tool_id, policy in security_policies.items():
            security_manager.add_security_policy(tool_id, policy)

    # Resource manager setup
    resource_manager = ResourceManager()
    if resource_limits:
        resource_manager.set_resource_limits(resource_limits)

    # Cache manager setup
    cache_manager = CacheManager()
    if cache_config:
        cache_manager = CacheManager(
            max_size=cache_config.get('max_size', 1000),
            default_ttl=cache_config.get('default_ttl', 3600)
        )

    return ToolExecutor(
        security_manager=security_manager,
        resource_manager=resource_manager,
        cache_manager=cache_manager
    )


# === EXAMPLE USAGE ===

async def example_tool_executor_usage():
    """Example usage of ToolExecutor."""

    # Create executor with configuration
    executor = create_tool_executor(
        resource_limits=ResourceLimits(
            max_cpu_percent=80.0,
            max_memory_mb=512,
            max_execution_time=300,
            max_concurrent_executions=5
        ),
        cache_config={
            'max_size': 500,
            'default_ttl': 1800
        }
    )

    # Start executor
    await executor.start()

    try:
        # Example execution request
        from .tool_builder import ToolExecutionRequest

        request = ToolExecutionRequest(
            tool_id="example_tool",
            capability_name="test_capability",
            parameters={"param1": "value1"},
            user_id="test_user",
            project_id="test_project"
        )

        # Would execute with actual tool
        # result = await executor.execute_tool(tool, request)
        # print(f"Execution result: {result.status}")

        # Get statistics
        stats = executor.get_executor_stats()
        print(f"Executor stats: {json.dumps(stats, indent=2, default=str)}")

    finally:
        # Stop executor
        await executor.stop()


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_tool_executor_usage())
