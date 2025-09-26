# Agent Builder
from datetime import datetime
from typing import Any, Dict, List, Optional

"""
from typing import Set, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from typing import Optional, List, Dict, Any
Agent Builder - Simplified Implementation for Independent Operation
"""
import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class AgentState(Enum):
    """Agent execution states"""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Message structure for agent communication"""

    id: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class AgentExecutionContext:
    """Context for agent execution"""

    agent_id: str
    task: str
    state: AgentState
    messages: List[AgentMessage]
    start_time: datetime
    end_time: Optional[datetime] = None


class AIModelInterface:
    """Mock AI model interface for independent operation"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Mock response generation"""
        return f"Mock response from {self.model_name}: {prompt[:50]}..."


class AgentExecutionEngine:
    """Actor Model implementation for agent execution"""

    def __init__(self, agent_id: str, ai_model: AIModelInterface):
        self.agent_id = agent_id
        self.ai_model = ai_model
        self.state = AgentState.IDLE
        self.messages: List[AgentMessage] = []

    async def execute_task(self, task: str) -> AgentExecutionContext:
        """Execute a task using the agent"""
        self.state = AgentState.RUNNING
        start_time = datetime.now()

        context = AgentExecutionContext(
            agent_id=self.agent_id,
            task=task,
            state=self.state,
            messages=self.messages.copy(),
            start_time=start_time,
        )

        try:
            # Generate response using AI model
            response = await self.ai_model.generate_response(task)

            # Create response message
            message = AgentMessage(
                id=str(uuid.uuid4()),
                content=response,
                timestamp=datetime.now(),
                metadata={"type": "response", "model": self.ai_model.model_name},
            )

            self.messages.append(message)
            context.messages = self.messages.copy()
            context.state = AgentState.COMPLETED
            context.end_time = datetime.now()

        except Exception as e:
            context.state = AgentState.ERROR
            context.end_time = datetime.now()
            error_message = AgentMessage(
                id=str(uuid.uuid4()),
                content=f"Error: {str(e)}",
                timestamp=datetime.now(),
                metadata={"type": "error"},
            )
            self.messages.append(error_message)
            context.messages = self.messages.copy()

        self.state = context.state
        return context


@dataclass
class BuiltAgent:
    """Wrapper for a built agent with execution capabilities"""

    id: str
    name: Optional[str]
    model: str
    speciality: Optional[str]
    persona: Optional[str]
    stack: List[str]
    tools: List[str]
    protocol: Optional[str]
    workflow: Optional[str]
    book: Optional[str]
    execution_engine: AgentExecutionEngine

    async def execute(self, task: str) -> AgentExecutionContext:
        """Execute a task with this agent"""
        return await self.execution_engine.execute_task(task)


class AgentBuilder:
    """Builder pattern for creating agents with fluent interface"""

    def __init__(self):
        self._id: Optional[str] = None
        self._name: Optional[str] = None
        self._model: str = "claude-3.5-sonnet"  # default
        self._speciality: Optional[str] = None
        self._persona: Optional[str] = None
        self._stack: List[str] = []
        self._tools: List[str] = []
        self._protocol: Optional[str] = None
        self._workflow: Optional[str] = None
        self._book: Optional[str] = None

    def with_id(self, agent_id: str) -> "AgentBuilder":
        """Set agent ID (required)"""
        self._id = agent_id
        return self

    def with_name(self, name: str) -> "AgentBuilder":
        """Set agent name"""
        self._name = name
        return self

    def with_model(self, model: str) -> "AgentBuilder":
        """Set AI model (required)"""
        self._model = model
        return self

    def with_speciality(self, speciality: str) -> "AgentBuilder":
        """Set agent speciality"""
        self._speciality = speciality
        return self

    def with_persona(self, persona: str) -> "AgentBuilder":
        """Set agent persona"""
        self._persona = persona
        return self

    def with_stack(self, stack: List[str]) -> "AgentBuilder":
        """Set technology stack"""
        self._stack = stack
        return self

    def with_tools(self, tools: List[str]) -> "AgentBuilder":
        """Set available tools"""
        self._tools = tools
        return self

    def with_protocol(self, protocol: str) -> "AgentBuilder":
        """Set agent protocol"""
        self._protocol = protocol
        return self

    def with_workflow(self, workflow: str) -> "AgentBuilder":
        """Set agent workflow"""
        self._workflow = workflow
        return self

    def with_book(self, book: str) -> "AgentBuilder":
        """Set agent book/memory"""
        self._book = book
        return self

    def build(self) -> BuiltAgent:
        """Build the agent with validation"""
        if not self._id:
            raise ValueError("Agent ID is required")

        if not self._model:
            raise ValueError("AI model is required")

        # Create AI model interface
        ai_model = AIModelInterface(self._model)

        # Create execution engine
        execution_engine = AgentExecutionEngine(self._id, ai_model)

        # Build the agent
        agent = BuiltAgent(
            id=self._id,
            name=self._name,
            model=self._model,
            speciality=self._speciality,
            persona=self._persona,
            stack=self._stack,
            tools=self._tools,
            protocol=self._protocol,
            workflow=self._workflow,
            book=self._book,
            execution_engine=execution_engine,
        )

        return agent
