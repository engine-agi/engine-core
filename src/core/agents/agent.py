"""
Agent Core - Main Agent class for Engine Framework.

This module implements the core Agent class with:
- Builder pattern integration (minimal → complete configuration)
- Execution engine with AI model abstraction
- Integration with protocols, workflows, tools, and books
- Actor model principles for isolation and concurrency
- Comprehensive error handling and logging

Based on Engine Framework Agent architecture supporting all 11 modules.
"""

from typing import Dict, Any, List, Optional, Union, Callable, TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
from datetime import datetime
import json
import logging

# Local imports
from .agent_config import AgentConfig, AgentStatus, AgentModel, AgentExecutionConfig
from .agent_builder import AgentBuilder

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ...models.protocol import Protocol
    from ...models.workflow import Workflow
    from ...models.book import Book
    from ...models.tool import Tool

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


class ExecutionResult:
    """Result of agent execution."""

    def __init__(
        self,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: float = 0.0
    ):
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}
        self.execution_time = execution_time
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'metadata': self.metadata,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat()
        }


class Agent:
    """
    Core Agent class for Engine Framework.

    Implements the main agent functionality with:
    - Configuration management (11 modules)
    - AI model execution abstraction
    - Protocol and workflow integration
    - Tool capability management
    - Memory and context handling
    - Actor model principles
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize agent with configuration.

        Args:
            config: Agent configuration with all modules
        """
        self.config = config
        self.id = config.id
        self.state = AgentState.IDLE
        self.execution_config = AgentExecutionConfig()

        # Initialize components
        self._protocol: Optional['Protocol'] = None
        self._workflow: Optional['Workflow'] = None
        self._book: Optional['Book'] = None
        self._tools: List['Tool'] = []

        # Execution tracking
        self.execution_history: List[ExecutionResult] = []
        self.current_task: Optional[asyncio.Task] = None

        # Logging
        self.logger = logging.getLogger(f"agent.{self.id}")

        self.logger.info(f"Agent {self.id} initialized with model {config.model}")

    @classmethod
    def from_builder(cls, builder: AgentBuilder) -> 'Agent':
        """
        Create agent from builder.

        Args:
            builder: Configured agent builder

        Returns:
            Agent: New agent instance
        """
        # For now, create a basic config from builder
        # This will be enhanced when builder is fully implemented
        config = AgentConfig(
            id=getattr(builder, '_id', 'default-agent'),
            model=getattr(builder, '_model', AgentModel.CLAUDE_3_5_SONNET),
            stack=getattr(builder, '_stack', ['python']),
            name=getattr(builder, '_name', None),
            speciality=getattr(builder, '_speciality', None),
            persona=getattr(builder, '_persona', None),
            tools=getattr(builder, '_tools', None),
            protocol_id=None,
            workflow_id=None,
            book_id=None,
            project_id=None
        )
        return cls(config)

    @classmethod
    def create_minimal(
        cls,
        agent_id: str,
        model: AgentModel,
        stack: List[str]
    ) -> 'Agent':
        """
        Create agent with minimal configuration (3 required fields).

        Args:
            agent_id: Unique agent identifier
            model: AI model to use
            stack: Technology stack

        Returns:
            Agent: New agent instance
        """
        config = AgentConfig(
            id=agent_id,
            model=model,
            stack=stack,
            name=None,
            speciality=None,
            persona=None,
            tools=None,
            protocol_id=None,
            workflow_id=None,
            book_id=None,
            project_id=None
        )
        return cls(config)

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ExecutionResult:
        """
        Execute a task with the agent.

        Args:
            task: Task description to execute
            context: Additional context for execution
            **kwargs: Additional execution parameters

        Returns:
            ExecutionResult: Execution result
        """
        start_time = datetime.utcnow()
        self.state = AgentState.THINKING

        try:
            self.logger.info(f"Executing task: {task}")

            # Prepare execution context
            execution_context = self._prepare_execution_context(task, context or {}, **kwargs)

            # Apply protocol if available
            if self._protocol:
                execution_context = self._apply_protocol(execution_context)

            # Execute with AI model
            result = self._execute_with_model(execution_context)

            # Apply workflow if available
            if self._workflow:
                result = self._apply_workflow(result)

            # Store in memory if book is available
            if self._book:
                self._store_in_memory(task, result)

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            final_result = ExecutionResult(
                success=True,
                output=result,
                metadata={'task': task, 'context': execution_context},
                execution_time=execution_time
            )

            self.execution_history.append(final_result)
            self.state = AgentState.IDLE

            self.logger.info(f"Task completed successfully in {execution_time:.2f}s")
            return final_result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ExecutionResult(
                success=False,
                error=str(e),
                metadata={'task': task, 'exception': type(e).__name__},
                execution_time=execution_time
            )

            self.execution_history.append(error_result)
            self.state = AgentState.ERROR

            self.logger.error(f"Task failed: {e}")
            return error_result

    async def _prepare_execution_context(
        self,
        task: str,
        context: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare execution context with agent configuration and tools."""
        execution_context = {
            'task': task,
            'agent_id': self.id,
            'agent_model': self.config.model,
            'agent_stack': self.config.stack,
            'agent_name': self.config.name,
            'agent_speciality': self.config.speciality,
            'agent_persona': self.config.persona,
            'context': context,
            'kwargs': kwargs
        }

        # Add tool capabilities
        if self._tools:
            execution_context['available_tools'] = [
                {'id': tool.id, 'name': tool.name, 'capabilities': tool.capabilities}
                for tool in self._tools
            ]

        # Add memory context if book is available
        if self._book:
            memory_context = self._get_memory_context(task)
            execution_context['memory_context'] = memory_context

        return execution_context

    def _apply_protocol(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply protocol to execution context."""
        if not self._protocol:
            return context

        self.logger.debug("Applying protocol to execution context")
        # Protocol application logic would go here
        # This is a placeholder for the actual protocol implementation
        return context

    def _execute_with_model(self, context: Dict[str, Any]) -> Any:
        """Execute task using the configured AI model."""
        self.state = AgentState.EXECUTING

        # This is a placeholder for AI model integration
        # In a real implementation, this would call the appropriate AI service
        # (OpenAI, Claude, local models, etc.)

        model_name = self.config.model
        task = context['task']

        self.logger.debug(f"Executing with model {model_name}")

        # Simulate AI model execution
        if model_name == AgentModel.CLAUDE_3_5_SONNET:
            result = f"Claude response to: {task}"
        elif model_name == AgentModel.GPT_4:
            result = f"GPT-4 response to: {task}"
        else:
            result = f"Generic AI response to: {task}"

        # Add agent personality if configured
        if self.config.persona:
            result = f"[{self.config.persona}] {result}"

        return result

    def _apply_workflow(self, result: Any) -> Any:
        """Apply workflow processing to result."""
        if not self._workflow:
            return result

        self.logger.debug("Applying workflow processing")
        # Workflow processing logic would go here
        # This is a placeholder for the actual workflow implementation
        return result

    def _store_in_memory(self, task: str, result: Any) -> None:
        """Store execution in memory book."""
        if not self._book:
            return

        self.logger.debug("Storing execution in memory")
        # Memory storage logic would go here
        # This is a placeholder for the actual book implementation

    def _get_memory_context(self, task: str) -> Dict[str, Any]:
        """Retrieve relevant memory context for task."""
        if not self._book:
            return {}

        # Memory retrieval logic would go here
        # This is a placeholder for the actual book implementation
        return {'previous_similar_tasks': []}

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'id': self.id,
            'state': self.state.value,
            'config': self.config.get_config_summary(),
            'execution_count': len(self.execution_history),
            'last_execution': self.execution_history[-1].to_dict() if self.execution_history else None,
            'has_protocol': self._protocol is not None,
            'has_workflow': self._workflow is not None,
            'has_book': self._book is not None,
            'tool_count': len(self._tools)
        }

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update agent configuration."""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.config.updated_at = datetime.utcnow()
        self.logger.info(f"Agent {self.id} configuration updated")

    def shutdown(self) -> None:
        """Shutdown agent and cleanup resources."""
        self.state = AgentState.STOPPED

        if self.current_task and not self.current_task.done():
            self.current_task.cancel()

        self.logger.info(f"Agent {self.id} shutdown complete")

    def __repr__(self) -> str:
        return f"Agent(id='{self.id}', model='{self.config.model}', state='{self.state.value}')"
