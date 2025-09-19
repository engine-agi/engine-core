"""
Workflow Engine - Pregel-based Computational Graph Execution.

The WorkflowEngine implements the Pregel computational model for distributed
graph processing, adapted for AI agent orchestration and workflow execution.

Key Features:
- Pregel computational model (supersteps, message passing, vertex computation)
- DAG validation and cycle detection
- Vertex-based computation with agent assignment
- Edge-based message passing and data flow
- Superstep coordination and synchronization
- Fault tolerance and recovery mechanisms
- Performance monitoring and optimization

Architecture:
- Vertices represent computational units (agents, teams, or atomic operations)
- Edges represent data dependencies and message passing
- Supersteps coordinate distributed computation phases
- Global coordinator manages execution state and synchronization

Based on Google's Pregel paper and adapted for Engine Framework.
"""

from typing import Dict, Any, List, Optional, Union, Set, Tuple, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
from datetime import datetime
import json
import logging
from collections import defaultdict, deque

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ...models.workflow import Workflow, WorkflowVertex, WorkflowEdge
    from ..agents.agent_builder import BuiltAgent
    from ..teams.team_builder import BuiltTeam

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow execution states."""
    IDLE = "idle"
    VALIDATING = "validating"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VertexState(Enum):
    """Vertex execution states."""
    PENDING = "pending"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MessageType(Enum):
    """Message types for vertex communication."""
    DATA = "data"
    CONTROL = "control"
    ERROR = "error"
    COMPLETION = "completion"


@dataclass
class WorkflowMessage:
    """Message passed between vertices."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.DATA
    sender_vertex_id: str = ""
    receiver_vertex_id: str = ""
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    superstep: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'type': self.type.value,
            'sender_vertex_id': self.sender_vertex_id,
            'receiver_vertex_id': self.receiver_vertex_id,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'superstep': self.superstep
        }


@dataclass
class WorkflowExecutionContext:
    """Context for workflow execution."""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    parent_execution_id: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    timeout_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'execution_id': self.execution_id,
            'workflow_id': self.workflow_id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'parent_execution_id': self.parent_execution_id,
            'input_data': self.input_data,
            'global_variables': self.global_variables,
            'metadata': self.metadata,
            'started_at': self.started_at.isoformat(),
            'timeout_seconds': self.timeout_seconds
        }


@dataclass
class VertexExecutionResult:
    """Result of vertex execution."""
    vertex_id: str
    status: VertexState
    output_data: Any = None
    messages: List[WorkflowMessage] = field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'vertex_id': self.vertex_id,
            'status': self.status.value,
            'output_data': self.output_data,
            'messages': [msg.to_dict() for msg in self.messages],
            'execution_time': self.execution_time,
            'error': self.error,
            'metadata': self.metadata
        }


class VertexComputation(ABC):
    """Abstract base class for vertex computation logic."""
    
    @abstractmethod
    async def compute(
        self,
        vertex_id: str,
        input_data: Any,
        messages: List[WorkflowMessage],
        context: WorkflowExecutionContext
    ) -> VertexExecutionResult:
        """Execute vertex computation."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get list of dependency vertex IDs."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate vertex configuration."""
        pass


class AgentVertexComputation(VertexComputation):
    """Vertex computation using an AI agent."""
    
    def __init__(self, agent: 'BuiltAgent', config: Dict[str, Any]):
        self.agent = agent
        self.config = config
        self.dependencies = config.get('dependencies', [])
    
    async def compute(
        self,
        vertex_id: str,
        input_data: Any,
        messages: List[WorkflowMessage],
        context: WorkflowExecutionContext
    ) -> VertexExecutionResult:
        """Execute agent-based computation."""
        start_time = datetime.utcnow()
        
        try:
            # Prepare agent input from messages and data
            agent_input = self._prepare_agent_input(input_data, messages, context)
            
            # Create agent execution context
            from ..agents.agent_builder import AgentExecutionContext
            agent_context = AgentExecutionContext(
                session_id=context.session_id,
                user_id=context.user_id,
                project_id=context.project_id,
                metadata={
                    'workflow_execution_id': context.execution_id,
                    'vertex_id': vertex_id,
                    'workflow_context': context.metadata
                }
            )
            
            # Execute agent
            response = await self.agent.execute(agent_input, agent_context)
            
            # Process agent response and create output messages
            output_messages = self._create_output_messages(
                vertex_id, response, context.execution_id
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VertexExecutionResult(
                vertex_id=vertex_id,
                status=VertexState.COMPLETED,
                output_data=response.content,
                messages=output_messages,
                execution_time=execution_time,
                metadata={'agent_id': self.agent.id, 'model': self.agent.model}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VertexExecutionResult(
                vertex_id=vertex_id,
                status=VertexState.FAILED,
                error=str(e),
                execution_time=execution_time,
                metadata={'agent_id': self.agent.id}
            )
    
    def get_dependencies(self) -> List[str]:
        """Get dependency vertex IDs."""
        return self.dependencies
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate agent vertex configuration."""
        required_fields = ['agent_id']
        return all(field in config for field in required_fields)
    
    def _prepare_agent_input(
        self,
        input_data: Any,
        messages: List[WorkflowMessage],
        context: WorkflowExecutionContext
    ) -> str:
        """Prepare input text for agent execution."""
        
        # Extract instruction from config
        instruction = self.config.get('instruction', 'Process the following input:')
        
        # Combine input data
        input_parts = [instruction]
        
        if input_data:
            input_parts.append(f"Input Data: {json.dumps(input_data, default=str)}")
        
        # Add messages from dependencies
        if messages:
            message_content = []
            for msg in messages:
                if msg.type == MessageType.DATA:
                    message_content.append(f"From {msg.sender_vertex_id}: {msg.content}")
            
            if message_content:
                input_parts.append("Previous Results:")
                input_parts.extend(message_content)
        
        # Add global variables if relevant
        if context.global_variables:
            relevant_vars = {
                k: v for k, v in context.global_variables.items()
                if k in self.config.get('required_variables', [])
            }
            if relevant_vars:
                input_parts.append(f"Variables: {json.dumps(relevant_vars, default=str)}")
        
        return "\n\n".join(input_parts)
    
    def _create_output_messages(
        self,
        vertex_id: str,
        agent_response: Any,
        execution_id: str
    ) -> List[WorkflowMessage]:
        """Create output messages from agent response."""
        
        # Get output targets from config
        output_targets = self.config.get('output_targets', [])
        
        messages = []
        for target in output_targets:
            message = WorkflowMessage(
                type=MessageType.DATA,
                sender_vertex_id=vertex_id,
                receiver_vertex_id=target,
                content=agent_response.content,
                metadata={
                    'execution_id': execution_id,
                    'agent_response': True
                }
            )
            messages.append(message)
        
        return messages


class TeamVertexComputation(VertexComputation):
    """Vertex computation using a team of agents."""
    
    def __init__(self, team: 'BuiltTeam', config: Dict[str, Any]):
        self.team = team
        self.config = config
        self.dependencies = config.get('dependencies', [])
    
    async def compute(
        self,
        vertex_id: str,
        input_data: Any,
        messages: List[WorkflowMessage],
        context: WorkflowExecutionContext
    ) -> VertexExecutionResult:
        """Execute team-based computation."""
        start_time = datetime.utcnow()
        
        try:
            # Prepare team tasks from input and messages
            tasks = self._prepare_team_tasks(input_data, messages, context)
            
            # Create team execution context
            from ..teams.team_builder import TeamExecutionContext
            team_context = TeamExecutionContext(
                project_id=context.project_id,
                user_id=context.user_id,
                session_id=context.session_id,
                workflow_id=context.workflow_id,
                metadata={
                    'workflow_execution_id': context.execution_id,
                    'vertex_id': vertex_id
                }
            )
            
            # Execute team tasks
            completed_tasks = await self.team.execute_tasks(tasks, team_context)
            
            # Process results and create output messages
            output_data = self._process_team_results(completed_tasks)
            output_messages = self._create_output_messages(
                vertex_id, output_data, context.execution_id
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VertexExecutionResult(
                vertex_id=vertex_id,
                status=VertexState.COMPLETED,
                output_data=output_data,
                messages=output_messages,
                execution_time=execution_time,
                metadata={
                    'team_id': self.team.id,
                    'tasks_completed': len(completed_tasks),
                    'coordination_strategy': self.team.coordination_strategy
                }
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VertexExecutionResult(
                vertex_id=vertex_id,
                status=VertexState.FAILED,
                error=str(e),
                execution_time=execution_time,
                metadata={'team_id': self.team.id}
            )
    
    def get_dependencies(self) -> List[str]:
        """Get dependency vertex IDs."""
        return self.dependencies
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate team vertex configuration."""
        required_fields = ['team_id', 'tasks']
        return all(field in config for field in required_fields)
    
    def _prepare_team_tasks(
        self,
        input_data: Any,
        messages: List[WorkflowMessage],
        context: WorkflowExecutionContext
    ) -> List[Any]:
        """Prepare tasks for team execution."""
        from ..teams.team_builder import TeamTask
        
        task_configs = self.config.get('tasks', [])
        tasks = []
        
        for task_config in task_configs:
            task = TeamTask(
                id=task_config.get('id', str(uuid.uuid4())),
                description=task_config['description'],
                requirements=task_config.get('requirements', []),
                dependencies=task_config.get('dependencies', []),
                context={
                    'input_data': input_data,
                    'messages': [msg.to_dict() for msg in messages],
                    'workflow_context': context.to_dict()
                }
            )
            tasks.append(task)
        
        return tasks
    
    def _process_team_results(self, completed_tasks: List[Any]) -> Dict[str, Any]:
        """Process team execution results."""
        results = {}
        
        for task in completed_tasks:
            results[task.id] = {
                'description': task.description,
                'result': task.result,
                'status': task.status,
                'assigned_to': task.assigned_to,
                'execution_time': (
                    task.completed_at - task.started_at
                ).total_seconds() if task.started_at and task.completed_at else 0
            }
        
        return {
            'tasks': results,
            'summary': f"Completed {len(completed_tasks)} tasks",
            'total_tasks': len(completed_tasks)
        }
    
    def _create_output_messages(
        self,
        vertex_id: str,
        output_data: Dict[str, Any],
        execution_id: str
    ) -> List[WorkflowMessage]:
        """Create output messages from team results."""
        
        output_targets = self.config.get('output_targets', [])
        
        messages = []
        for target in output_targets:
            message = WorkflowMessage(
                type=MessageType.DATA,
                sender_vertex_id=vertex_id,
                receiver_vertex_id=target,
                content=output_data,
                metadata={
                    'execution_id': execution_id,
                    'team_execution': True
                }
            )
            messages.append(message)
        
        return messages


class AtomicVertexComputation(VertexComputation):
    """Vertex computation for atomic operations (functions, scripts, etc.)."""
    
    def __init__(self, operation: Callable, config: Dict[str, Any]):
        self.operation = operation
        self.config = config
        self.dependencies = config.get('dependencies', [])
    
    async def compute(
        self,
        vertex_id: str,
        input_data: Any,
        messages: List[WorkflowMessage],
        context: WorkflowExecutionContext
    ) -> VertexExecutionResult:
        """Execute atomic operation."""
        start_time = datetime.utcnow()
        
        try:
            # Prepare operation input
            operation_input = self._prepare_operation_input(input_data, messages, context)
            
            # Execute operation (async or sync)
            if asyncio.iscoroutinefunction(self.operation):
                result = await self.operation(operation_input)
            else:
                result = self.operation(operation_input)
            
            # Create output messages
            output_messages = self._create_output_messages(
                vertex_id, result, context.execution_id
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VertexExecutionResult(
                vertex_id=vertex_id,
                status=VertexState.COMPLETED,
                output_data=result,
                messages=output_messages,
                execution_time=execution_time,
                metadata={'operation_type': 'atomic'}
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return VertexExecutionResult(
                vertex_id=vertex_id,
                status=VertexState.FAILED,
                error=str(e),
                execution_time=execution_time,
                metadata={'operation_type': 'atomic'}
            )
    
    def get_dependencies(self) -> List[str]:
        """Get dependency vertex IDs."""
        return self.dependencies
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate atomic operation configuration."""
        return True  # Minimal validation for atomic operations
    
    def _prepare_operation_input(
        self,
        input_data: Any,
        messages: List[WorkflowMessage],
        context: WorkflowExecutionContext
    ) -> Dict[str, Any]:
        """Prepare input for atomic operation."""
        return {
            'input_data': input_data,
            'messages': [msg.to_dict() for msg in messages],
            'context': context.to_dict(),
            'config': self.config
        }
    
    def _create_output_messages(
        self,
        vertex_id: str,
        result: Any,
        execution_id: str
    ) -> List[WorkflowMessage]:
        """Create output messages from operation result."""
        
        output_targets = self.config.get('output_targets', [])
        
        messages = []
        for target in output_targets:
            message = WorkflowMessage(
                type=MessageType.DATA,
                sender_vertex_id=vertex_id,
                receiver_vertex_id=target,
                content=result,
                metadata={
                    'execution_id': execution_id,
                    'atomic_operation': True
                }
            )
            messages.append(message)
        
        return messages


class WorkflowVertex:
    """Workflow vertex representation."""
    
    def __init__(
        self,
        vertex_id: str,
        computation: VertexComputation,
        config: Dict[str, Any]
    ):
        self.id = vertex_id
        self.computation = computation
        self.config = config
        self.state = VertexState.PENDING
        self.input_messages: List[WorkflowMessage] = []
        self.output_messages: List[WorkflowMessage] = []
        self.result: Optional[VertexExecutionResult] = None
        self.dependencies: Set[str] = set(computation.get_dependencies())
        self.dependents: Set[str] = set()
    
    async def execute(
        self,
        input_data: Any,
        context: WorkflowExecutionContext
    ) -> VertexExecutionResult:
        """Execute vertex computation."""
        self.state = VertexState.EXECUTING
        
        try:
            self.result = await self.computation.compute(
                self.id, input_data, self.input_messages, context
            )
            
            self.state = self.result.status
            self.output_messages = self.result.messages
            
            return self.result
            
        except Exception as e:
            self.result = VertexExecutionResult(
                vertex_id=self.id,
                status=VertexState.FAILED,
                error=str(e)
            )
            self.state = VertexState.FAILED
            return self.result
    
    def add_input_message(self, message: WorkflowMessage) -> None:
        """Add input message to vertex."""
        self.input_messages.append(message)
    
    def get_output_messages(self) -> List[WorkflowMessage]:
        """Get output messages from vertex."""
        return self.output_messages.copy()
    
    def is_ready(self, completed_vertices: Set[str]) -> bool:
        """Check if vertex is ready to execute."""
        return (
            self.state == VertexState.PENDING and
            self.dependencies.issubset(completed_vertices)
        )


class WorkflowEngine:
    """
    Pregel-based workflow execution engine.
    
    Implements the Pregel computational model for distributed graph processing,
    adapted for AI agent orchestration and workflow execution.
    
    Key Components:
    - Vertices: Computational units (agents, teams, operations)
    - Edges: Data flow and dependencies
    - Supersteps: Synchronized computation phases
    - Message passing: Inter-vertex communication
    
    Execution Flow:
    1. Graph validation and DAG verification
    2. Topological sorting and execution planning
    3. Superstep-based execution with synchronization
    4. Message passing and state updates
    5. Termination detection and result collection
    """
    
    def __init__(self):
        """Initialize workflow engine."""
        self.vertices: Dict[str, WorkflowVertex] = {}
        self.edges: Dict[str, List[str]] = defaultdict(list)  # vertex_id -> [dependent_vertex_ids]
        self.state = WorkflowState.IDLE
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0
        }
    
    def add_vertex(
        self,
        vertex_id: str,
        computation: VertexComputation,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add vertex to workflow."""
        if vertex_id in self.vertices:
            raise ValueError(f"Vertex {vertex_id} already exists")
        
        vertex_config = config or {}
        vertex = WorkflowVertex(vertex_id, computation, vertex_config)
        self.vertices[vertex_id] = vertex
    
    def add_edge(self, from_vertex_id: str, to_vertex_id: str) -> None:
        """Add edge between vertices."""
        if from_vertex_id not in self.vertices:
            raise ValueError(f"Source vertex {from_vertex_id} not found")
        if to_vertex_id not in self.vertices:
            raise ValueError(f"Target vertex {to_vertex_id} not found")
        
        # Add to adjacency list
        self.edges[from_vertex_id].append(to_vertex_id)
        
        # Update vertex relationships
        self.vertices[to_vertex_id].dependencies.add(from_vertex_id)
        self.vertices[from_vertex_id].dependents.add(to_vertex_id)
    
    def validate_workflow(self) -> Tuple[bool, List[str]]:
        """Validate workflow graph (DAG check, connectivity, etc.)."""
        errors = []
        
        # Check for empty workflow
        if not self.vertices:
            errors.append("Workflow has no vertices")
            return False, errors
        
        # Check for cycles (DAG validation)
        if self._has_cycles():
            errors.append("Workflow contains cycles (not a DAG)")
        
        # Check for disconnected components
        if self._has_disconnected_components():
            errors.append("Workflow has disconnected components")
        
        # Validate vertex configurations
        for vertex_id, vertex in self.vertices.items():
            if not vertex.computation.validate_config(vertex.config):
                errors.append(f"Invalid configuration for vertex {vertex_id}")
        
        return len(errors) == 0, errors
    
    def _has_cycles(self) -> bool:
        """Check if graph has cycles using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {vertex_id: WHITE for vertex_id in self.vertices}
        
        def dfs(vertex_id: str) -> bool:
            if colors[vertex_id] == GRAY:
                return True  # Back edge found (cycle)
            
            if colors[vertex_id] == BLACK:
                return False  # Already processed
            
            colors[vertex_id] = GRAY
            
            for neighbor in self.edges.get(vertex_id, []):
                if dfs(neighbor):
                    return True
            
            colors[vertex_id] = BLACK
            return False
        
        for vertex_id in self.vertices:
            if colors[vertex_id] == WHITE:
                if dfs(vertex_id):
                    return True
        
        return False
    
    def _has_disconnected_components(self) -> bool:
        """Check if graph has disconnected components."""
        if not self.vertices:
            return False
        
        # Find all reachable vertices from any starting vertex
        start_vertex = next(iter(self.vertices))
        visited = set()
        queue = deque([start_vertex])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            
            visited.add(current)
            
            # Add both outgoing and incoming neighbors
            for neighbor in self.edges.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
            
            # Add incoming neighbors
            for vertex_id, neighbors in self.edges.items():
                if current in neighbors and vertex_id not in visited:
                    queue.append(vertex_id)
        
        return len(visited) < len(self.vertices)
    
    def get_execution_order(self) -> List[List[str]]:
        """Get execution order using topological sort (by levels)."""
        # Calculate in-degrees
        in_degree = {vertex_id: 0 for vertex_id in self.vertices}
        
        for vertex_id in self.vertices:
            for neighbor in self.edges.get(vertex_id, []):
                in_degree[neighbor] += 1
        
        # Level-wise topological sort
        levels = []
        current_level = [vertex_id for vertex_id, degree in in_degree.items() if degree == 0]
        
        while current_level:
            levels.append(current_level.copy())
            next_level = []
            
            for vertex_id in current_level:
                for neighbor in self.edges.get(vertex_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)
            
            current_level = next_level
        
        return levels
    
    async def execute_workflow(
        self,
        context: WorkflowExecutionContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute workflow using Pregel model."""
        start_time = datetime.utcnow()
        
        try:
            self.state = WorkflowState.VALIDATING
            
            # Validate workflow
            is_valid, errors = self.validate_workflow()
            if not is_valid:
                raise ValueError(f"Workflow validation failed: {', '.join(errors)}")
            
            self.state = WorkflowState.PLANNING
            
            # Get execution order
            execution_levels = self.get_execution_order()
            if not execution_levels:
                raise ValueError("No executable vertices found")
            
            self.state = WorkflowState.EXECUTING
            
            # Execute vertices level by level (supersteps)
            completed_vertices = set()
            all_results = {}
            
            for superstep, level in enumerate(execution_levels):
                logger.info(f"Executing superstep {superstep} with vertices: {level}")
                
                # Execute vertices in current level concurrently
                level_results = await self._execute_superstep(
                    level, completed_vertices, context, input_data or {}
                )
                
                # Process results and pass messages
                for vertex_id, result in level_results.items():
                    all_results[vertex_id] = result
                    
                    if result.status == VertexState.COMPLETED:
                        completed_vertices.add(vertex_id)
                        
                        # Send messages to dependent vertices
                        await self._propagate_messages(vertex_id, result)
                    else:
                        # Handle failed vertex
                        logger.error(f"Vertex {vertex_id} failed: {result.error}")
                        self.state = WorkflowState.FAILED
                        raise RuntimeError(f"Vertex {vertex_id} execution failed: {result.error}")
            
            self.state = WorkflowState.COMPLETED
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update stats
            self.execution_stats['total_executions'] += 1
            self.execution_stats['successful_executions'] += 1
            self.execution_stats['average_execution_time'] = (
                (self.execution_stats['average_execution_time'] * 
                 (self.execution_stats['successful_executions'] - 1) + execution_time) / 
                self.execution_stats['successful_executions']
            )
            
            # Compile final results
            return {
                'execution_id': context.execution_id,
                'status': 'completed',
                'execution_time': execution_time,
                'vertices_executed': len(completed_vertices),
                'supersteps': len(execution_levels),
                'results': {vid: result.to_dict() for vid, result in all_results.items()},
                'final_outputs': self._collect_final_outputs(all_results)
            }
            
        except Exception as e:
            self.state = WorkflowState.FAILED
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.execution_stats['total_executions'] += 1
            self.execution_stats['failed_executions'] += 1
            
            logger.error(f"Workflow execution failed: {str(e)}")
            
            return {
                'execution_id': context.execution_id,
                'status': 'failed',
                'execution_time': execution_time,
                'error': str(e),
                'results': {}
            }
    
    async def _execute_superstep(
        self,
        vertex_ids: List[str],
        completed_vertices: Set[str],
        context: WorkflowExecutionContext,
        input_data: Dict[str, Any]
    ) -> Dict[str, VertexExecutionResult]:
        """Execute vertices in a superstep concurrently."""
        
        # Filter vertices that are actually ready
        ready_vertices = [
            vid for vid in vertex_ids 
            if self.vertices[vid].is_ready(completed_vertices)
        ]
        
        if not ready_vertices:
            return {}
        
        # Create execution coroutines
        execution_tasks = []
        for vertex_id in ready_vertices:
            vertex = self.vertices[vertex_id]
            task = asyncio.create_task(
                vertex.execute(input_data.get(vertex_id), context),
                name=f"vertex_{vertex_id}"
            )
            execution_tasks.append((vertex_id, task))
        
        # Execute all vertices concurrently
        results = {}
        for vertex_id, task in execution_tasks:
            try:
                result = await task
                results[vertex_id] = result
            except Exception as e:
                results[vertex_id] = VertexExecutionResult(
                    vertex_id=vertex_id,
                    status=VertexState.FAILED,
                    error=str(e)
                )
        
        return results
    
    async def _propagate_messages(
        self,
        sender_vertex_id: str,
        result: VertexExecutionResult
    ) -> None:
        """Propagate messages from completed vertex to dependent vertices."""
        
        for message in result.messages:
            receiver_vertex_id = message.receiver_vertex_id
            
            if receiver_vertex_id in self.vertices:
                self.vertices[receiver_vertex_id].add_input_message(message)
            else:
                logger.warning(f"Message target vertex {receiver_vertex_id} not found")
    
    def _collect_final_outputs(self, all_results: Dict[str, VertexExecutionResult]) -> Dict[str, Any]:
        """Collect final outputs from leaf vertices."""
        final_outputs = {}
        
        # Find leaf vertices (vertices with no dependents)
        leaf_vertices = [
            vid for vid, vertex in self.vertices.items()
            if not vertex.dependents
        ]
        
        for vertex_id in leaf_vertices:
            if vertex_id in all_results:
                result = all_results[vertex_id]
                if result.status == VertexState.COMPLETED:
                    final_outputs[vertex_id] = result.output_data
        
        return final_outputs
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        return {
            'vertex_count': len(self.vertices),
            'edge_count': sum(len(neighbors) for neighbors in self.edges.values()),
            'current_state': self.state.value,
            'execution_stats': self.execution_stats,
            'vertices': {
                vid: {
                    'state': vertex.state.value,
                    'dependencies': list(vertex.dependencies),
                    'dependents': list(vertex.dependents)
                }
                for vid, vertex in self.vertices.items()
            }
        }
    
    def reset(self) -> None:
        """Reset workflow for new execution."""
        self.state = WorkflowState.IDLE
        
        for vertex in self.vertices.values():
            vertex.state = VertexState.PENDING
            vertex.input_messages.clear()
            vertex.output_messages.clear()
            vertex.result = None


# === CONVENIENCE FUNCTIONS ===

def create_agent_vertex(
    vertex_id: str,
    agent: 'BuiltAgent',
    instruction: str,
    dependencies: Optional[List[str]] = None,
    output_targets: Optional[List[str]] = None
) -> Tuple[str, VertexComputation, Dict[str, Any]]:
    """Create agent-based vertex configuration."""
    
    config = {
        'agent_id': agent.id,
        'instruction': instruction,
        'dependencies': dependencies or [],
        'output_targets': output_targets or []
    }
    
    computation = AgentVertexComputation(agent, config)
    
    return vertex_id, computation, config


def create_team_vertex(
    vertex_id: str,
    team: 'BuiltTeam',
    tasks: List[Dict[str, Any]],
    dependencies: Optional[List[str]] = None,
    output_targets: Optional[List[str]] = None
) -> Tuple[str, VertexComputation, Dict[str, Any]]:
    """Create team-based vertex configuration."""
    
    config = {
        'team_id': team.id,
        'tasks': tasks,
        'dependencies': dependencies or [],
        'output_targets': output_targets or []
    }
    
    computation = TeamVertexComputation(team, config)
    
    return vertex_id, computation, config


def create_function_vertex(
    vertex_id: str,
    operation: Callable,
    dependencies: Optional[List[str]] = None,
    output_targets: Optional[List[str]] = None,
    **operation_config
) -> Tuple[str, VertexComputation, Dict[str, Any]]:
    """Create function-based vertex configuration."""
    
    config = {
        'dependencies': dependencies or [],
        'output_targets': output_targets or [],
        **operation_config
    }
    
    computation = AtomicVertexComputation(operation, config)
    
    return vertex_id, computation, config


# === EXAMPLE USAGE ===

async def example_usage():
    """Example usage of WorkflowEngine."""
    
    # Create workflow engine
    engine = WorkflowEngine()
    
    # Example atomic operation
    async def data_processing(input_data):
        """Example data processing function."""
        data = input_data.get('input_data', {})
        return {'processed': True, 'count': len(str(data))}
    
    # Add vertices
    vertex_id, computation, config = create_function_vertex(
        'data_processor',
        data_processing,
        output_targets=['final_output']
    )
    engine.add_vertex(vertex_id, computation, config)
    
    # Add final output vertex
    async def final_output_op(input_data):
        return {'final_result': input_data}
    
    vertex_id2, computation2, config2 = create_function_vertex(
        'final_output',
        final_output_op,
        dependencies=['data_processor']
    )
    engine.add_vertex(vertex_id2, computation2, config2)
    
    # Add edge
    engine.add_edge('data_processor', 'final_output')
    
    # Validate and execute
    is_valid, errors = engine.validate_workflow()
    print(f"Workflow valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    
    # Execute workflow
    context = WorkflowExecutionContext(
        workflow_id="example_workflow",
        input_data={'test': 'data'}
    )
    
    result = await engine.execute_workflow(context, {'data_processor': {'sample': 'input'}})
    print(f"Execution result: {json.dumps(result, indent=2, default=str)}")
    
    # Get stats
    stats = engine.get_workflow_stats()
    print(f"Workflow stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    # Run example usage
    import asyncio
    asyncio.run(example_usage())
