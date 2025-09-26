"""
from abc import abstractmethod
from typing import Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from typing import Optional, List, Dict, Any
Actor Model implementation for parallel workflow execution.

This module provides actor-based execution for workflows, enabling true parallelism
without the limitations of level-based superstep execution.
"""
import asyncio
import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import Field

    VertexState,
    WorkflowState,
    VertexComputation,
    VertexExecutionResult,
    WorkflowExecutionContext,
    WorkflowMessage
)

logger = logging.getLogger(__name__)


class ActorMessageType(Enum):
    """Types of messages that actors can exchange."""
    EXECUTE = "execute"
    RESULT = "result"
    ERROR = "error"
    COMPLETE = "complete"
    TERMINATE = "terminate"


@dataclass
class ActorMessage:
    """Message exchanged between actors."""
    message_type: ActorMessageType
    sender_id: str
    receiver_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None


class Actor(ABC):
    """Base actor class with message handling capabilities."""

    def __init__(self, actor_id: str):
        self.actor_id = actor_id
        self.mailbox: asyncio.Queue[ActorMessage] = asyncio.Queue()
        self.running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the actor's message processing loop."""
        self.running = True
        self.task = asyncio.create_task(self._message_loop())
        logger.debug(f"Actor {self.actor_id} started")

    async def stop(self) -> None:
        """Stop the actor and cleanup resources."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.debug(f"Actor {self.actor_id} stopped")

    async def send_message(self, message: ActorMessage) -> None:
        """Send a message to this actor."""
        await self.mailbox.put(message)

    async def _message_loop(self) -> None:
        """Main message processing loop."""
        while self.running:
            try:
                message = await self.mailbox.get()
                await self._handle_message(message)
                self.mailbox.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in actor {self.actor_id}: {e}")

    @abstractmethod
    async def _handle_message(self, message: ActorMessage) -> None:
        """Handle incoming messages. Must be implemented by subclasses."""
        pass


class VertexActor(Actor):
    """Actor responsible for executing a single vertex computation."""

    def __init__(
        self,
        vertex_id: str,
        computation: VertexComputation,
        dependencies: Set[str],
        dependents: Set[str]
    ):
        super().__init__(f"vertex_{vertex_id}")
        self.vertex_id = vertex_id
        self.computation = computation
        self.dependencies = dependencies.copy()
        self.dependents = dependents.copy()
        self.pending_dependencies = dependencies.copy()
        self.state = VertexState.PENDING
        self.result: Optional[VertexExecutionResult] = None
        self.coordinator: Optional['WorkflowCoordinatorActor'] = None

    def set_coordinator(self, coordinator: 'WorkflowCoordinatorActor') -> None:
        """Set the workflow coordinator for this vertex."""
        self.coordinator = coordinator

    async def _handle_message(self, message: ActorMessage) -> None:
        """Handle messages for vertex execution."""
        if message.message_type == ActorMessageType.EXECUTE:
            await self._handle_execute(message)
        elif message.message_type == ActorMessageType.TERMINATE:
            await self.stop()
        else:
            logger.warning(
                f"Vertex {self.vertex_id} received unknown message: {message.message_type}")

    async def _handle_execute(self, message: ActorMessage) -> None:
        """Handle execution request."""
        if self.state != VertexState.PENDING:
            return

        input_data = message.payload.get('input_data', {})
        context = message.payload.get('context')

        if not context:
            raise ValueError("Execution context is required")

        try:
            self.state = VertexState.EXECUTING

            # Execute the vertex computation
            result = await self.computation.compute(
                self.vertex_id,
                input_data,
                [],  # messages - will be handled differently in actor model
                context
            )

            self.result = result
            self.state = result.status

            # Notify coordinator of completion
            if self.coordinator:
                await self.coordinator.send_message(ActorMessage(
                    message_type=ActorMessageType.RESULT,
                    sender_id=self.actor_id,
                    receiver_id=self.coordinator.actor_id,
                    payload={
                        'vertex_id': self.vertex_id,
                        'result': result
                    },
                    correlation_id=message.correlation_id
                ))

        except Exception as e:
            logger.error(f"Error executing vertex {self.vertex_id}: {e}")
            self.state = VertexState.FAILED
            self.result = VertexExecutionResult(
                vertex_id=self.vertex_id,
                status=VertexState.FAILED,
                error=str(e)
            )

            # Notify coordinator of error
            if self.coordinator:
                await self.coordinator.send_message(ActorMessage(
                    message_type=ActorMessageType.ERROR,
                    sender_id=self.actor_id,
                    receiver_id=self.coordinator.actor_id,
                    payload={
                        'vertex_id': self.vertex_id,
                        'error': str(e)
                    },
                    correlation_id=message.correlation_id
                ))

    def dependency_satisfied(self, dependency_id: str) -> None:
        """Mark a dependency as satisfied."""
        self.pending_dependencies.discard(dependency_id)

    def is_ready(self) -> bool:
        """Check if vertex is ready to execute."""
        return len(self.pending_dependencies) == 0 and self.state == VertexState.PENDING


class WorkflowCoordinatorActor(Actor):
    """Coordinator actor that manages the entire workflow execution."""

    def __init__(self, workflow_id: str, vertices: Dict[str, VertexActor]):
        super().__init__(f"coordinator_{workflow_id}")
        self.workflow_id = workflow_id
        self.vertices = vertices
        self.completed_vertices: Set[str] = set()
        self.failed_vertices: Set[str] = set()
        self.workflow_state = WorkflowState.EXECUTING
        self.final_result: Optional[Dict[str, Any]] = None
        self.execution_context: Optional[WorkflowExecutionContext] = None

        # Set coordinator reference for all vertices
        for vertex in self.vertices.values():
            vertex.set_coordinator(self)

    async def _handle_message(self, message: ActorMessage) -> None:
        """Handle messages from vertex actors."""
        if message.message_type == ActorMessageType.RESULT:
            await self._handle_vertex_result(message)
        elif message.message_type == ActorMessageType.ERROR:
            await self._handle_vertex_error(message)
        else:
            logger.warning(
                f"Coordinator received unknown message: {message.message_type}")

    async def _handle_vertex_result(self, message: ActorMessage) -> None:
        """Handle successful vertex completion."""
        vertex_id = message.payload['vertex_id']
        result = message.payload['result']

        self.completed_vertices.add(vertex_id)
        logger.info(f"Vertex {vertex_id} completed successfully")

        # Propagate messages to dependent vertices
        await self._propagate_messages(vertex_id, result)

        # Check if workflow is complete
        await self._check_workflow_completion()

    async def _handle_vertex_error(self, message: ActorMessage) -> None:
        """Handle vertex execution error."""
        vertex_id = message.payload['vertex_id']
        error = message.payload['error']

        self.failed_vertices.add(vertex_id)
        logger.error(f"Vertex {vertex_id} failed: {error}")

        # Mark workflow as failed
        self.workflow_state = WorkflowState.FAILED

        # Stop all vertices
        await self._terminate_all_vertices()

    async def _propagate_messages(self, sender_vertex_id: str, result: VertexExecutionResult) -> None:
        """Propagate messages from completed vertex to dependents."""
        for message in result.messages:
            receiver_id = message.receiver_vertex_id
            if receiver_id in self.vertices:
                vertex_actor = self.vertices[receiver_id]
                vertex_actor.dependency_satisfied(sender_vertex_id)

                # Check if receiver is now ready
                if vertex_actor.is_ready():
                    await self._start_vertex(vertex_actor, message.content or {})

    async def _start_vertex(self, vertex_actor: VertexActor, input_data: Dict[str, Any]) -> None:
        """Start execution of a ready vertex."""
        await vertex_actor.send_message(ActorMessage(
            message_type=ActorMessageType.EXECUTE,
            sender_id=self.actor_id,
            receiver_id=vertex_actor.actor_id,
            payload={
                'input_data': input_data,
                'context': self.execution_context
            }
        ))

    async def _check_workflow_completion(self) -> None:
        """Check if the entire workflow has completed."""
        total_vertices = len(self.vertices)
        completed_count = len(self.completed_vertices) + len(self.failed_vertices)

        if completed_count >= total_vertices:
            if self.failed_vertices:
                self.workflow_state = WorkflowState.FAILED
            else:
                self.workflow_state = WorkflowState.COMPLETED
                await self._collect_final_results()

            # Stop all actors
            await self._terminate_all_vertices()

    async def _collect_final_results(self) -> None:
        """Collect final outputs from completed vertices."""
        final_outputs = {}

        # Find leaf vertices (no dependents)
        leaf_vertices = [
            vid for vid, vertex in self.vertices.items()
            if not vertex.dependents
        ]

        for vertex_id in leaf_vertices:
            vertex_actor = self.vertices[vertex_id]
            if vertex_actor.result and vertex_actor.result.status == VertexState.COMPLETED:
                final_outputs[vertex_id] = vertex_actor.result.output_data

        self.final_result = final_outputs

    async def _terminate_all_vertices(self) -> None:
        """Terminate all vertex actors."""
        terminate_tasks = []
        for vertex_actor in self.vertices.values():
            terminate_tasks.append(vertex_actor.send_message(ActorMessage(
                message_type=ActorMessageType.TERMINATE,
                sender_id=self.actor_id,
                receiver_id=vertex_actor.actor_id
            )))

        await asyncio.gather(*terminate_tasks, return_exceptions=True)

    async def execute_workflow(
        self,
        context: WorkflowExecutionContext,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the workflow using actor-based coordination."""
        self.execution_context = context

        # Start all vertex actors
        start_tasks = []
        for vertex_actor in self.vertices.values():
            start_tasks.append(vertex_actor.start())
        await asyncio.gather(*start_tasks)

        # Start execution from vertices with no dependencies
        ready_vertices = [
            vertex for vertex in self.vertices.values()
            if vertex.is_ready()
        ]

        for vertex_actor in ready_vertices:
            vertex_input = input_data.get(vertex_actor.vertex_id, {})
            await self._start_vertex(vertex_actor, vertex_input)

        # Wait for completion
        while self.workflow_state == WorkflowState.EXECUTING:
            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

        # Stop all actors
        stop_tasks = []
        for vertex_actor in self.vertices.values():
            stop_tasks.append(vertex_actor.stop())
        await asyncio.gather(*stop_tasks, return_exceptions=True)

        return {
            'status': self.workflow_state.value,
            'result': self.final_result or {},
            'completed_vertices': list(self.completed_vertices),
            'failed_vertices': list(self.failed_vertices)
        }
