"""Contract tests for Engine Core public API."""

import pytest

from engine_core import (
    AgentBuilder,
    BookBuilder,
    ProtocolBuilder,
    TeamBuilder,
    ToolBuilder,
    WorkflowBuilder,
    WorkflowEngine,
    __version__,
)


class TestCorePublicAPIContract:
    """Test contracts for Engine Core public API."""

    @pytest.mark.contract
    def test_version_contract(self):
        """Test version contract."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

    @pytest.mark.contract
    def test_agent_builder_contract(self):
        """Test AgentBuilder contract."""
        builder = AgentBuilder()
        assert builder is not None

        # Test required methods exist
        required_methods = ["with_id", "with_model", "with_stack", "build"]
        for method in required_methods:
            assert hasattr(builder, method), f"AgentBuilder missing {method}"

        # Test can build minimal agent
        agent = (
            builder
            .with_id("test_agent")
            .with_model("test_model")
            .with_stack(["python"])
            .build()
        )
        assert agent is not None
        assert agent.id == "test_agent"

    @pytest.mark.contract
    def test_team_builder_contract(self):
        """Test TeamBuilder contract."""
        builder = TeamBuilder()
        assert builder is not None

        required_methods = ["with_id", "add_member", "with_coordination_strategy", "build"]
        for method in required_methods:
            assert hasattr(builder, method), f"TeamBuilder missing {method}"

    @pytest.mark.contract
    def test_workflow_builder_contract(self):
        """Test WorkflowBuilder contract."""
        builder = WorkflowBuilder()
        assert builder is not None

        required_methods = ["with_id", "add_agent_vertex", "add_edge", "build"]
        for method in required_methods:
            assert hasattr(builder, method), f"WorkflowBuilder missing {method}"

    @pytest.mark.contract
    def test_book_builder_contract(self):
        """Test BookBuilder contract."""
        builder = BookBuilder()
        assert builder is not None

        required_methods = ["with_id", "add_chapter", "add_page", "build"]
        for method in required_methods:
            assert hasattr(builder, method), f"BookBuilder missing {method}"

    @pytest.mark.contract
    def test_protocol_builder_contract(self):
        """Test ProtocolBuilder contract."""
        builder = ProtocolBuilder()
        assert builder is not None

        required_methods = ["with_id", "add_command", "with_context_scope", "build"]
        for method in required_methods:
            assert hasattr(builder, method), f"ProtocolBuilder missing {method}"

    @pytest.mark.contract
    def test_tool_builder_contract(self):
        """Test ToolBuilder contract."""
        builder = ToolBuilder()
        assert builder is not None

        required_methods = ["with_id", "with_name", "with_capability", "build"]
        for method in required_methods:
            assert hasattr(builder, method), f"ToolBuilder missing {method}"

    @pytest.mark.contract
    def test_workflow_engine_contract(self):
        """Test WorkflowEngine contract."""
        engine = WorkflowEngine()
        assert engine is not None

        required_methods = ["add_vertex", "add_edge", "validate_workflow", "execute_workflow"]
        for method in required_methods:
            assert hasattr(engine, method), f"WorkflowEngine missing {method}"