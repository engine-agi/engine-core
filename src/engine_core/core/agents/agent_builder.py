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
Agent Builder - Core Agent System with Fluent Interface.

The AgentBuilder provides a fluent interface for creating and configuring
Engine Framework agents with all 11 modules. It handles validation,
AI model integration, and execution engine setup.

Based on Engine Framework Agent architecture with:
- Builder Pattern for fluent configuration
- Actor Model for agent isolation
- AI model integration (OpenAI, Claude, local models)
- Protocol and workflow integration
- Tool capability management

Key Features:
- Minimal configuration (3 required fields: id, model, stack)
- Complete configuration (11 modules with full customization)
- Runtime validation and constraint checking
- AI model abstraction layer
- Execution context management
- Memory and tool integration
"""
import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ...models.agent import Agent
    from ...models.book import Book
    from ...models.protocol import Protocol
    from ...models.tool import Tool
    from ...models.workflow import Workflow


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    STOPPED = "stopped"


class ModelProvider(Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class AgentExecutionContext:
    """Context for agent execution."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    parent_context: Optional['AgentExecutionContext'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'request_id': self.request_id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'metadata': self.metadata,
            'started_at': self.started_at.isoformat()
        }


@dataclass
class AgentMessage:
    """Message structure for agent communication."""
    content: str
    role: str = "user"  # user, assistant, system
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'content': self.content,
            'role': self.role,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }


class AIModelInterface(ABC):
    """Abstract interface for AI model integration."""

    @abstractmethod
    async def generate_response(
        self,
        messages: List[AgentMessage],
        context: AgentExecutionContext,
        **kwargs
    ) -> AgentMessage:
        """Generate response from AI model."""
        pass

    @abstractmethod
    async def validate_model_config(self, config: Dict[str, Any]) -> bool:
        """Validate model configuration."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and capabilities."""
        pass


class OpenAIModelAdapter(AIModelInterface):
    """OpenAI model adapter."""

    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.config = kwargs

    async def generate_response(
        self,
        messages: List[AgentMessage],
        context: AgentExecutionContext,
        **kwargs
    ) -> AgentMessage:
        """Generate response using OpenAI API."""
        # In real implementation, would call OpenAI API
        # For now, return a mock response
        return AgentMessage(
            content=f"OpenAI {self.model_name} response to: {messages[-1].content}",
            role="assistant",
            context={'model': self.model_name, 'provider': 'openai'}
        )

    async def validate_model_config(self, config: Dict[str, Any]) -> bool:
        """Validate OpenAI model configuration."""
        required_fields = ['model_name']
        return all(field in config for field in required_fields)

    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        return {
            'provider': 'openai',
            'model': self.model_name,
            'capabilities': ['text_generation', 'conversation', 'function_calling'],
            'context_window': 128000 if 'gpt-4' in self.model_name else 4096
        }


class AnthropicModelAdapter(AIModelInterface):
    """Anthropic Claude model adapter."""

    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.config = kwargs

    async def generate_response(
        self,
        messages: List[AgentMessage],
        context: AgentExecutionContext,
        **kwargs
    ) -> AgentMessage:
        """Generate response using Anthropic API."""
        # In real implementation, would call Anthropic API
        return AgentMessage(
            content=f"Claude {self.model_name} response to: {messages[-1].content}",
            role="assistant",
            context={'model': self.model_name, 'provider': 'anthropic'}
        )

    async def validate_model_config(self, config: Dict[str, Any]) -> bool:
        """Validate Anthropic model configuration."""
        required_fields = ['model_name']
        return all(field in config for field in required_fields)

    def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model information."""
        return {
            'provider': 'anthropic',
            'model': self.model_name,
            'capabilities': ['text_generation', 'conversation', 'analysis'],
            'context_window': 200000 if 'claude-3' in self.model_name else 100000
        }


class AgentExecutionEngine:
    """Agent execution engine with Actor Model isolation."""

    def __init__(self, agent_config: Dict[str, Any]):
        self.agent_config = agent_config
        self.state = AgentState.IDLE
        self.model_adapter: Optional[AIModelInterface] = None
        self.conversation_history: List[AgentMessage] = []
        self.execution_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_execution_time': 0.0,
            'average_response_time': 0.0
        }
        self._setup_model_adapter()

    def _setup_model_adapter(self) -> None:
        """Setup AI model adapter based on configuration."""
        model_name = self.agent_config.get('model', '')

        if 'gpt' in model_name.lower() or 'openai' in model_name.lower():
            self.model_adapter = OpenAIModelAdapter(
                model_name=model_name,
                **self.agent_config.get('model_config', {})
            )
        elif 'claude' in model_name.lower() or 'anthropic' in model_name.lower():
            self.model_adapter = AnthropicModelAdapter(
                model_name=model_name,
                **self.agent_config.get('model_config', {})
            )
        else:
            raise ValueError(f"Unsupported model: {model_name}")

    async def execute_request(
        self,
        message: str,
        context: AgentExecutionContext
    ) -> AgentMessage:
        """Execute agent request with full Actor Model isolation."""
        start_time = datetime.utcnow()

        try:
            self.state = AgentState.THINKING
            self.execution_stats['total_requests'] += 1

            # Create user message
            user_message = AgentMessage(
                content=message,
                role="user",
                context=context.to_dict()
            )

            # Add to conversation history
            self.conversation_history.append(user_message)

            # Generate response using AI model
            self.state = AgentState.EXECUTING

            if not self.model_adapter:
                raise RuntimeError("No model adapter configured")

            response = await self.model_adapter.generate_response(
                messages=self.conversation_history[-10:],  # Keep last 10 messages
                context=context
            )

            # Add response to history
            self.conversation_history.append(response)

            # Update stats
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.execution_stats['successful_requests'] += 1
            self.execution_stats['total_execution_time'] += execution_time
            self.execution_stats['average_response_time'] = (
                self.execution_stats['total_execution_time'] /
                self.execution_stats['successful_requests']
            )

            self.state = AgentState.IDLE
            return response

        except Exception as e:
            self.state = AgentState.ERROR
            self.execution_stats['failed_requests'] += 1

            error_response = AgentMessage(
                content=f"Error executing request: {str(e)}",
                role="system",
                context={'error': True, 'exception': str(e)}
            )

            return error_response

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        return {
            'current_state': self.state.value,
            'conversation_length': len(
                self.conversation_history),
            'model_info': self.model_adapter.get_model_info() if self.model_adapter else None,
            **self.execution_stats}

    def reset_conversation(self) -> None:
        """Reset conversation history."""
        self.conversation_history.clear()
        self.state = AgentState.IDLE


class AgentBuilder:
    """
    Fluent interface builder for Engine Framework agents.

    Provides a clean, chainable API for configuring agents with all 11 modules.
    Handles validation, AI model integration, and execution engine setup.

    Usage:
        # Minimal configuration (3 required fields)
        agent = AgentBuilder() \
            .with_id("my_agent") \
            .with_model("gpt-4") \
            .with_stack(["python"]) \
            .build()

        # Complete configuration (11 modules)
        agent = AgentBuilder() \
            .with_id("senior_dev") \
            .with_model("claude-3-sonnet") \
            .with_name("Senior Developer") \
            .with_speciality("Full-Stack Development") \
            .with_persona("Experienced, methodical developer") \
            .with_stack(["python", "react", "postgresql"]) \
            .with_tools(["github", "vscode"]) \
            .with_protocol("analysis_first") \
            .with_workflow("tdd_workflow") \
            .with_book("project_memory") \
            .with_metadata({"department": "engineering"}) \
            .build()
    """

    def __init__(self):
        """Initialize builder with empty configuration."""
        self.config = {
            # Required fields (will be validated)
            'id': None,
            'model': None,
            'stack': None,

            # Optional fields with defaults
            'name': None,
            'specialty': None,
            'persona': None,
            'tools': [],
            'protocol': None,
            'workflow': None,
            'book': None,
            'metadata': {}
        }

        # Internal builder state
        self._execution_engine: Optional[AgentExecutionEngine] = None
        self._validation_errors: List[str] = []

    # === REQUIRED FIELDS ===

    def with_id(self, agent_id: str) -> 'AgentBuilder':
        """Set agent ID (required)."""
        if not agent_id or not isinstance(agent_id, str):
            self._validation_errors.append("Agent ID must be a non-empty string")
            return self

        self.config['id'] = agent_id
        return self

    def with_model(self, model: str) -> 'AgentBuilder':
        """Set AI model (required)."""
        if not model or not isinstance(model, str):
            self._validation_errors.append("Model must be a non-empty string")
            return self

        self.config['model'] = model
        return self

    def with_stack(self, stack: List[str]) -> 'AgentBuilder':
        """Set technology stack (required)."""
        if not stack or not isinstance(
                stack,
                list) or not all(
                isinstance(
                s,
                str) for s in stack):
            self._validation_errors.append("Stack must be a non-empty list of strings")
            return self

        self.config['stack'] = stack
        return self

    # === OPTIONAL FIELDS ===

    def with_name(self, name: str) -> 'AgentBuilder':
        """Set agent display name."""
        self.config['name'] = name
        return self

    def with_speciality(self, specialty: str) -> 'AgentBuilder':
        """Set agent specialty or domain expertise."""
        self.config['specialty'] = specialty
        return self

    def with_persona(self, persona: str) -> 'AgentBuilder':
        """Set agent personality and communication style."""
        self.config['persona'] = persona
        return self

    def with_tools(self, tools: List[str]) -> 'AgentBuilder':
        """Set available tools for agent."""
        if not isinstance(tools, list):
            self._validation_errors.append("Tools must be a list")
            return self

        self.config['tools'] = tools
        return self

    def with_protocol(self, protocol: str) -> 'AgentBuilder':
        """Set agent protocol for behavior patterns."""
        self.config['protocol'] = protocol
        return self

    def with_workflow(self, workflow: str) -> 'AgentBuilder':
        """Set agent workflow for execution patterns."""
        self.config['workflow'] = workflow
        return self

    def with_book(self, book: str) -> 'AgentBuilder':
        """Set agent memory/knowledge book."""
        self.config['book'] = book
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> 'AgentBuilder':
        """Set additional agent metadata."""
        if not isinstance(metadata, dict):
            self._validation_errors.append("Metadata must be a dictionary")
            return self

        self.config['metadata'] = metadata
        return self

    # === ADVANCED CONFIGURATION ===

    def with_model_config(self, **model_config) -> 'AgentBuilder':
        """Set advanced model configuration."""
        if 'model_config' not in self.config:
            self.config['model_config'] = {}

        self.config['model_config'].update(model_config)
        return self

    def with_execution_limits(
        self,
        max_requests_per_minute: int = 60,
        max_conversation_length: int = 100,
        timeout_seconds: int = 30
    ) -> 'AgentBuilder':
        """Set execution limits for agent."""
        self.config['execution_limits'] = {
            'max_requests_per_minute': max_requests_per_minute,
            'max_conversation_length': max_conversation_length,
            'timeout_seconds': timeout_seconds
        }
        return self

    # === VALIDATION ===

    def validate(self) -> bool:
        """Validate agent configuration."""
        self._validation_errors.clear()

        # Check required fields
        required_fields = ['id', 'model', 'stack']
        for field in required_fields:
            if not self.config.get(field):
                self._validation_errors.append(f"Required field '{field}' is missing")

        # Validate ID format
        if self.config.get('id'):
            import re
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]{1,99}$', self.config['id']):
                self._validation_errors.append(
                    "Agent ID must start with a letter and be 2-100 characters, "
                    "containing only letters, numbers, underscores, and hyphens"
                )

        # Validate model format
        if self.config.get('model'):
            supported_models = [
                'gpt-3.5-turbo',
                'gpt-4',
                'gpt-4-turbo',
                'gpt-4o',
                'claude-3-haiku',
                'claude-3-sonnet',
                'claude-3-opus',
                'claude-3.5-sonnet']
            if not any(model in self.config['model'] for model in supported_models):
                self._validation_errors.append(
                    f"Model '{self.config['model']}' is not supported")

        # Validate stack
        if self.config.get('stack'):
            if len(self.config['stack']) == 0:
                self._validation_errors.append("Stack cannot be empty")

            # Validate supported technologies
            supported_technologies = [
                'python',
                'javascript',
                'typescript',
                'java',
                'csharp',
                'cpp',
                'c',
                'go',
                'rust',
                'php',
                'ruby',
                'swift',
                'kotlin',
                'scala',
                'r',
                'matlab',
                'sql',
                'html',
                'css',
                'react',
                'vue',
                'angular',
                'node',
                'express',
                'django',
                'flask',
                'fastapi',
                'spring',
                'dotnet',
                'tensorflow',
                'pytorch',
                'pandas',
                'numpy',
                'scikit-learn',
                'docker',
                'kubernetes',
                'aws',
                'azure',
                'gcp',
                'linux',
                'windows',
                'macos',
                'git',
                'github',
                'gitlab',
                'jenkins',
                'mongodb',
                'postgresql',
                'mysql',
                'redis',
                'graphql',
                'rest',
                'soap',
                'webassembly',
                'wasm']

            for tech in self.config['stack']:
                if tech not in supported_technologies:
                    self._validation_errors.append(
                        f"Technology '{tech}' is not supported")

        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        return self._validation_errors.copy()

    # === BUILD METHODS ===

    def build(self) -> 'BuiltAgent':
        """Build and return configured agent."""
        if not self.validate():
            raise ValueError(
                f"Agent validation failed: {
                    ', '.join(
                        self._validation_errors)}")

        # Create execution engine
        execution_engine = AgentExecutionEngine(self.config)

        # Create built agent wrapper
        built_agent = BuiltAgent(
            config=self.config.copy(),
            execution_engine=execution_engine
        )

        return built_agent

    def build_async(self) -> 'BuiltAgent':
        """Build agent with async validation."""
        # For now, same as build() - in real implementation would validate async
        # resources
        return self.build()

    # === FACTORY METHODS ===

    @classmethod
    def minimal(cls, agent_id: str, model: str, stack: List[str]) -> 'AgentBuilder':
        """Create minimal agent configuration."""
        return cls().with_id(agent_id).with_model(model).with_stack(stack)

    @classmethod
    def senior_developer(cls, agent_id: str) -> 'AgentBuilder':
        """Create senior developer agent template."""
        return cls() \
            .with_id(agent_id) \
            .with_model("claude-3.5-sonnet") \
            .with_name("Senior Developer") \
            .with_speciality("Full-Stack Development") \
            .with_persona("Experienced, methodical, focuses on code quality and best practices") \
            .with_stack(["python", "react", "typescript", "postgresql"]) \
            .with_tools(["github", "vscode", "database"]) \
            .with_protocol("analysis_first")

    @classmethod
    def data_analyst(cls, agent_id: str) -> 'AgentBuilder':
        """Create data analyst agent template."""
        return cls() \
            .with_id(agent_id) \
            .with_model("gpt-4") \
            .with_name("Data Analyst") \
            .with_speciality("Data Analysis and Visualization") \
            .with_persona("Analytical, detail-oriented, excellent at finding insights in data") \
            .with_stack(["python", "pandas", "numpy", "matplotlib", "sql"]) \
            .with_tools(["database", "jupyter", "visualization"])

    @classmethod
    def product_manager(cls, agent_id: str) -> 'AgentBuilder':
        """Create product manager agent template."""
        return cls() \
            .with_id(agent_id) \
            .with_model("gpt-4-turbo") \
            .with_name("Product Manager") \
            .with_speciality("Product Strategy and Requirements") \
            .with_persona("Strategic, user-focused, excellent at translating business needs") \
            .with_stack(["requirements", "strategy", "metrics"]) \
            .with_tools(["documentation", "analysis"])


class BuiltAgent:
    """
    Built agent with execution capabilities.

    Represents a fully configured agent ready for execution.
    Provides the interface for running agent tasks and managing state.
    """

    def __init__(self, config: Dict[str, Any], execution_engine: AgentExecutionEngine):
        self.config = config
        self.execution_engine = execution_engine
        self.created_at = datetime.utcnow()

    @property
    def id(self) -> str:
        """Get agent ID."""
        return self.config['id']

    @property
    def name(self) -> str:
        """Get agent name (or ID if no name set)."""
        return self.config.get('name', self.config['id'])

    @property
    def model(self) -> str:
        """Get agent model."""
        return self.config['model']

    @property
    def stack(self) -> List[str]:
        """Get agent technology stack."""
        return self.config['stack']

    async def execute(
        self,
        message: str,
        context: Optional[AgentExecutionContext] = None
    ) -> AgentMessage:
        """Execute agent with message."""
        if context is None:
            context = AgentExecutionContext()

        return await self.execution_engine.execute_request(message, context)

    async def conversation(
        self,
        messages: List[str],
        context: Optional[AgentExecutionContext] = None
    ) -> List[AgentMessage]:
        """Execute multi-turn conversation."""
        responses = []

        for message in messages:
            response = await self.execute(message, context)
            responses.append(response)

        return responses

    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        return {
            'agent_id': self.id,
            'agent_name': self.name,
            'model': self.model,
            'created_at': self.created_at.isoformat(),
            'execution_stats': self.execution_engine.get_execution_stats()
        }

    def reset(self) -> None:
        """Reset agent conversation state."""
        self.execution_engine.reset_conversation()

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            'config': self.config,
            'stats': self.get_stats(),
            'created_at': self.created_at.isoformat()
        }


# === CONVENIENCE FUNCTIONS ===

def create_minimal_agent(agent_id: str, model: str, stack: List[str]) -> BuiltAgent:
    """Create minimal agent with just required fields."""
    return AgentBuilder.minimal(agent_id, model, stack).build()


def create_senior_developer(agent_id: str) -> BuiltAgent:
    """Create senior developer agent."""
    return AgentBuilder.senior_developer(agent_id).build()


def create_data_analyst(agent_id: str) -> BuiltAgent:
    """Create data analyst agent."""
    return AgentBuilder.data_analyst(agent_id).build()


def create_product_manager(agent_id: str) -> BuiltAgent:
    """Create product manager agent."""
    return AgentBuilder.product_manager(agent_id).build()


# === EXAMPLE USAGE ===

async def example_usage():
    """Example usage of AgentBuilder."""

    # Minimal agent
    minimal_agent = create_minimal_agent(
        agent_id="simple_bot",
        model="gpt-3.5-turbo",
        stack=["python"]
    )

    # Senior developer agent
    senior_dev = create_senior_developer("senior_dev_01")

    # Execute requests
    context = AgentExecutionContext(user_id="user123")

    response1 = await minimal_agent.execute("Hello, how are you?", context)
    print(f"Minimal Agent: {response1.content}")

    response2 = await senior_dev.execute("Review this Python code for best practices", context)
    print(f"Senior Dev: {response2.content}")

    # Get statistics
    stats = senior_dev.get_stats()
    print(f"Senior Dev Stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    # Run example usage
    import asyncio
    asyncio.run(example_usage())
