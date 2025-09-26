"""
Unit tests for AgentBuilder - Minimal Configuration Tests
"""

import os

# Import the classes we need to test
import sys

import pytest

from engine_core.core.agents.agent_builder import (
    AgentBuilder,
    AgentExecutionContext,
    AgentExecutionEngine,
    AgentState,
    AIModelInterface,
    BuiltAgent,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


class TestAgentBuilderMinimal:
    """Test AgentBuilder with minimal configuration (id and model only)"""

    def test_agent_builder_creation(self):
        """Test that AgentBuilder can be instantiated"""
        builder = AgentBuilder()
        assert builder is not None
        assert isinstance(builder, AgentBuilder)

    def test_minimal_agent_build(self):
        """Test building an agent with minimal required fields"""
        agent = (
            AgentBuilder().with_id("test_agent").with_model("claude-3.5-sonnet").build()
        )

        assert agent is not None
        assert isinstance(agent, BuiltAgent)
        assert agent.id == "test_agent"
        assert agent.model == "claude-3.5-sonnet"
        assert agent.name is None
        assert agent.speciality is None
        assert agent.persona is None
        assert agent.stack == []
        assert agent.tools == []
        assert agent.protocol is None
        assert agent.workflow is None
        assert agent.book is None
        assert isinstance(agent.execution_engine, AgentExecutionEngine)

    def test_agent_build_without_id_fails(self):
        """Test that building an agent without ID raises ValueError"""
        with pytest.raises(ValueError, match="Agent ID is required"):
            AgentBuilder().with_model("claude-3.5-sonnet").build()

    def test_agent_build_without_model_uses_default(self):
        """Test that building an agent without explicit model uses default"""
        agent = AgentBuilder().with_id("test_agent").build()

        assert agent.model == "claude-3.5-sonnet"

    def test_agent_builder_fluent_interface(self):
        """Test that AgentBuilder methods return self for chaining"""
        builder = AgentBuilder()

        # Test method chaining
        result = (
            builder.with_id("test_agent")
            .with_name("Test Agent")
            .with_model("gpt-4")
            .with_speciality("Testing")
        )

        assert result is builder  # Should return self

    def test_agent_with_all_optional_fields(self):
        """Test building an agent with all optional fields set"""
        agent = (
            AgentBuilder()
            .with_id("full_agent")
            .with_name("Full Test Agent")
            .with_model("claude-3.5-sonnet")
            .with_speciality("Full Stack Development")
            .with_persona("Experienced developer")
            .with_stack(["python", "react", "postgresql"])
            .with_tools(["github", "vscode"])
            .with_protocol("tdd_protocol")
            .with_workflow("development_workflow")
            .with_book("project_memory")
            .build()
        )

        assert agent.id == "full_agent"
        assert agent.name == "Full Test Agent"
        assert agent.speciality == "Full Stack Development"
        assert agent.persona == "Experienced developer"
        assert agent.stack == ["python", "react", "postgresql"]
        assert agent.tools == ["github", "vscode"]
        assert agent.protocol == "tdd_protocol"
        assert agent.workflow == "development_workflow"
        assert agent.book == "project_memory"


class TestAIModelInterface:
    """Test the mock AI model interface"""

    def test_ai_model_creation(self):
        """Test AIModelInterface instantiation"""
        model = AIModelInterface("claude-3.5-sonnet")
        assert model.model_name == "claude-3.5-sonnet"

    @pytest.mark.asyncio
    async def test_ai_model_generate_response(self):
        """Test mock response generation"""
        model = AIModelInterface("test-model")
        response = await model.generate_response("Hello world")

        assert "Mock response from test-model" in response
        assert "Hello world" in response


class TestAgentExecutionEngine:
    """Test the AgentExecutionEngine"""

    def test_execution_engine_creation(self):
        """Test AgentExecutionEngine instantiation"""
        ai_model = AIModelInterface("test-model")
        engine = AgentExecutionEngine("test_agent", ai_model)

        assert engine.agent_id == "test_agent"
        assert engine.ai_model is ai_model
        assert engine.state == AgentState.IDLE
        assert engine.messages == []

    @pytest.mark.asyncio
    async def test_agent_execution(self):
        """Test agent task execution"""
        ai_model = AIModelInterface("test-model")
        engine = AgentExecutionEngine("test_agent", ai_model)

        context = await engine.execute_task("Test task")

        assert isinstance(context, AgentExecutionContext)
        assert context.agent_id == "test_agent"
        assert context.task == "Test task"
        assert context.state == AgentState.COMPLETED
        assert context.start_time is not None
        assert context.end_time is not None
        assert len(context.messages) == 1
        assert "Mock response" in context.messages[0].content


class TestBuiltAgent:
    """Test the BuiltAgent wrapper"""

    def test_built_agent_creation(self):
        """Test BuiltAgent instantiation"""
        ai_model = AIModelInterface("test-model")
        engine = AgentExecutionEngine("test_agent", ai_model)

        agent = BuiltAgent(
            id="test_agent",
            name="Test Agent",
            model="test-model",
            speciality="testing",
            persona="test persona",
            stack=["python"],
            tools=["pytest"],
            protocol="test_protocol",
            workflow="test_workflow",
            book="test_book",
            execution_engine=engine,
        )

        assert agent.id == "test_agent"
        assert agent.name == "Test Agent"
        assert agent.model == "test-model"
        assert agent.speciality == "testing"
        assert agent.persona == "test persona"
        assert agent.stack == ["python"]
        assert agent.tools == ["pytest"]
        assert agent.protocol == "test_protocol"
        assert agent.workflow == "test_workflow"
        assert agent.book == "test_book"
        assert agent.execution_engine is engine

    @pytest.mark.asyncio
    async def test_built_agent_execute(self):
        """Test BuiltAgent execution method"""
        ai_model = AIModelInterface("test-model")
        engine = AgentExecutionEngine("test_agent", ai_model)

        agent = BuiltAgent(
            id="test_agent",
            name=None,
            model="test-model",
            speciality=None,
            persona=None,
            stack=[],
            tools=[],
            protocol=None,
            workflow=None,
            book=None,
            execution_engine=engine,
        )

        context = await agent.execute("Test task")

        assert isinstance(context, AgentExecutionContext)
        assert context.agent_id == "test_agent"
        assert context.task == "Test task"
        assert context.state == AgentState.COMPLETED


class TestAgentBuilderComplete:
    """Test AgentBuilder with complete configuration (all 11 modules)"""

    def test_complete_agent_configuration(self):
        """Test building an agent with all 11 configurable modules"""
        agent = (
            AgentBuilder()
            .with_id("senior_dev")
            .with_name("Senior Developer")
            .with_model("claude-3.5-sonnet")
            .with_speciality("Full-Stack Development")
            .with_persona("Experienced, methodical developer")
            .with_stack(["python", "typescript", "react", "postgresql"])
            .with_tools(["github", "vscode", "docker"])
            .with_protocol("analysis_first")
            .with_workflow("tdd_workflow")
            .with_book("project_memory")
            .build()
        )

        # Verify all fields are set correctly
        assert agent.id == "senior_dev"
        assert agent.name == "Senior Developer"
        assert agent.model == "claude-3.5-sonnet"
        assert agent.speciality == "Full-Stack Development"
        assert agent.persona == "Experienced, methodical developer"
        assert agent.stack == ["python", "typescript", "react", "postgresql"]
        assert agent.tools == ["github", "vscode", "docker"]
        assert agent.protocol == "analysis_first"
        assert agent.workflow == "tdd_workflow"
        assert agent.book == "project_memory"

    def test_agent_independence_validation(self):
        """Test that agents work independently without external dependencies"""
        # This test validates that agents can be created and executed
        # without depending on teams, workflows, protocols, tools, or book modules

        agent = AgentBuilder().with_id("independent_agent").with_model("gpt-4").build()

        # Agent should be able to execute tasks independently
        # (This would fail if there were circular imports or missing dependencies)
        assert agent.id == "independent_agent"
        assert agent.model == "gpt-4"
        assert agent.execution_engine is not None

    @pytest.mark.asyncio
    async def test_agent_execution_with_context(self):
        """Test agent execution maintains proper context and state"""
        agent = (
            AgentBuilder()
            .with_id("context_test_agent")
            .with_name("Context Test Agent")
            .with_model("claude-3.5-sonnet")
            .with_speciality("Testing")
            .build()
        )

        # Execute a task
        context = await agent.execute("Analyze this code for bugs")

        # Verify execution context
        assert context.agent_id == "context_test_agent"
        assert context.task == "Analyze this code for bugs"
        assert context.state == AgentState.COMPLETED
        assert context.start_time <= context.end_time
        assert len(context.messages) >= 1

        # Verify the response contains expected mock content
        response_message = context.messages[0]
        assert "Mock response from claude-3.5-sonnet" in response_message.content
        assert "Analyze this code for bugs" in response_message.content
        assert response_message.metadata["type"] == "response"
        assert response_message.metadata["model"] == "claude-3.5-sonnet"

    def test_agent_builder_method_order_independence(self):
        """Test that builder methods can be called in any order"""
        # Call methods in different order
        agent1 = (
            AgentBuilder()
            .with_model("gpt-4")
            .with_id("agent1")
            .with_name("Agent 1")
            .build()
        )

        agent2 = (
            AgentBuilder()
            .with_name("Agent 2")
            .with_id("agent2")
            .with_model("claude-3.5-sonnet")
            .build()
        )

        assert agent1.id == "agent1"
        assert agent1.model == "gpt-4"
        assert agent1.name == "Agent 1"

        assert agent2.id == "agent2"
        assert agent2.model == "claude-3.5-sonnet"
        assert agent2.name == "Agent 2"

    def test_agent_builder_reuse(self):
        """Test that AgentBuilder can be reused to create multiple agents"""
        builder = AgentBuilder()

        # Create first agent
        agent1 = (
            builder.with_id("agent1").with_model("gpt-4").with_name("Agent One").build()
        )

        # Create second agent with same builder (should reset state)
        agent2 = (
            builder.with_id("agent2")
            .with_model("claude-3.5-sonnet")
            .with_name("Agent Two")
            .build()
        )

        assert agent1.id == "agent1"
        assert agent1.model == "gpt-4"
        assert agent1.name == "Agent One"

        assert agent2.id == "agent2"
        assert agent2.model == "claude-3.5-sonnet"
        assert agent2.name == "Agent Two"

    def test_agent_validation_edge_cases(self):
        """Test agent validation with edge cases"""
        # Test with valid non-empty model
        agent = (
            AgentBuilder()
            .with_id("valid_id")
            .with_model("some_model")
            .with_name("")
            .with_speciality("")
            .with_persona("")
            .build()
        )

        assert agent.id == "valid_id"
        assert agent.model == "some_model"
        assert agent.name == ""
        assert agent.speciality == ""
        assert agent.persona == ""

        # Test that empty model fails
        with pytest.raises(ValueError, match="AI model is required"):
            AgentBuilder().with_id("test").with_model("").build()

    @pytest.mark.asyncio
    async def test_agent_execution_error_handling(self):
        """Test agent execution error handling"""
        agent = (
            AgentBuilder().with_id("error_test_agent").with_model("error_model").build()
        )

        # Execute task (mock will still succeed, but we test the structure)
        context = await agent.execute("Test error handling")

        # Should complete successfully (mock doesn't actually error)
        assert context.state == AgentState.COMPLETED
        assert context.end_time is not None
        assert len(context.messages) == 1

    def test_agent_state_enum_values(self):
        """Test that AgentState enum has correct values"""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.COMPLETED.value == "completed"
        assert AgentState.ERROR.value == "error"

        # Test that all expected states exist
        states = [state.value for state in AgentState]
        assert "idle" in states
        assert "running" in states
        assert "completed" in states
        assert "error" in states
