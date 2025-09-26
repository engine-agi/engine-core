"""
Tests for Protocol Builder and Semantic Command Processing.

Tests cover:
- ProtocolBuilder fluent interface and configuration
- BuiltProtocol functionality
- Semantic command parsing and intent recognition
- Command validation and execution planning
- Integration with agents and tools
"""

from unittest.mock import AsyncMock, Mock

import pytest

from engine_core.core.protocols.protocol import (
    CommandContext,
    CommandIntent,
    CommandType,
    ContextScope,
    ExecutionPlan,
    IntentCategory,
    IntentRecognizer,
    ParsedCommand,
    PatternBasedIntentRecognizer,
    ProtocolParser,
)
from engine_core.core.protocols.protocol_builder import (
    BuiltProtocol,
    ProtocolBuilder,
    ProtocolConfiguration,
)


class TestProtocolBuilder:
    """Test ProtocolBuilder functionality."""

    def test_builder_initialization(self):
        """Test builder initializes with default configuration."""
        builder = ProtocolBuilder()
        assert builder._config.id == ""
        assert builder._config.supported_intents == list(IntentCategory)
        assert builder._config.default_scope == ContextScope.SESSION

    def test_with_id(self):
        """Test setting protocol ID."""
        builder = ProtocolBuilder()
        result = builder.with_id("test_protocol")
        assert result is builder
        assert builder._config.id == "test_protocol"

    def test_with_id_empty_raises_error(self):
        """Test empty ID raises ValueError."""
        builder = ProtocolBuilder()
        with pytest.raises(ValueError, match="Protocol ID cannot be empty"):
            builder.with_id("")

    def test_with_name_and_description(self):
        """Test setting name and description."""
        builder = ProtocolBuilder()
        builder.with_name("Test Protocol").with_description("A test protocol")
        assert builder._config.name == "Test Protocol"
        assert builder._config.description == "A test protocol"

    def test_with_supported_intents(self):
        """Test setting supported intents."""
        builder = ProtocolBuilder()
        intents = [IntentCategory.ANALYZE, IntentCategory.GENERATE]
        builder.with_supported_intents(intents)
        assert builder._config.supported_intents == intents

    def test_with_default_scope(self):
        """Test setting default scope."""
        builder = ProtocolBuilder()
        builder.with_default_scope(ContextScope.PROJECT)
        assert builder._config.default_scope == ContextScope.PROJECT

    def test_with_strict_validation(self):
        """Test enabling strict validation."""
        builder = ProtocolBuilder()
        builder.with_strict_validation(True)
        assert builder._config.strict_validation is True

    def test_with_learning_enabled(self):
        """Test enabling learning."""
        builder = ProtocolBuilder()
        builder.with_learning_enabled(True)
        assert builder._config.enable_learning is True

    def test_with_confidence_threshold(self):
        """Test setting confidence threshold."""
        builder = ProtocolBuilder()
        builder.with_confidence_threshold(0.8)
        assert builder._config.confidence_threshold == 0.8

    def test_with_confidence_threshold_invalid(self):
        """Test invalid confidence threshold raises error."""
        builder = ProtocolBuilder()
        with pytest.raises(
            ValueError, match="Confidence threshold must be between 0.0 and 1.0"
        ):
            builder.with_confidence_threshold(1.5)

    def test_with_max_execution_time(self):
        """Test setting max execution time."""
        builder = ProtocolBuilder()
        builder.with_max_execution_time(300)
        assert builder._config.max_execution_time == 300

    def test_with_max_execution_time_negative_raises_error(self):
        """Test negative execution time raises error."""
        builder = ProtocolBuilder()
        with pytest.raises(ValueError, match="Max execution time must be non-negative"):
            builder.with_max_execution_time(-1)

    def test_with_retry_attempts(self):
        """Test setting retry attempts."""
        builder = ProtocolBuilder()
        builder.with_retry_attempts(5)
        assert builder._config.retry_attempts == 5

    def test_with_metadata(self):
        """Test adding metadata."""
        builder = ProtocolBuilder()
        builder.with_metadata("key", "value")
        assert builder._config.metadata["key"] == "value"

    def test_build_without_id_raises_error(self):
        """Test building without ID raises error."""
        builder = ProtocolBuilder()
        with pytest.raises(ValueError, match="Protocol ID is required"):
            builder.build()

    def test_build_basic_protocol(self):
        """Test building a basic protocol."""
        protocol = ProtocolBuilder().with_id("test_protocol").build()

        assert isinstance(protocol, BuiltProtocol)
        assert protocol.id == "test_protocol"
        assert isinstance(protocol.configuration, ProtocolConfiguration)
        assert isinstance(protocol.parser, ProtocolParser)

    def test_create_basic_protocol_classmethod(self):
        """Test create_basic_protocol classmethod."""
        protocol = ProtocolBuilder.create_basic_protocol("basic_test")
        assert protocol.id == "basic_test"
        assert protocol.name == "Basic Protocol basic_test"

    def test_create_basic_protocol_with_name(self):
        """Test create_basic_protocol with custom name."""
        protocol = ProtocolBuilder.create_basic_protocol("basic_test", "Custom Name")
        assert protocol.id == "basic_test"
        assert protocol.name == "Custom Name"

    def test_create_analysis_protocol(self):
        """Test create_analysis_protocol classmethod."""
        protocol = ProtocolBuilder.create_analysis_protocol("analysis_test")
        assert protocol.id == "analysis_test"
        assert protocol.name == "Analysis Protocol analysis_test"
        assert protocol.configuration.supported_intents == [
            IntentCategory.ANALYZE,
            IntentCategory.QUERY,
            IntentCategory.READ,
        ]
        assert protocol.configuration.default_scope == ContextScope.PROJECT
        assert protocol.configuration.strict_validation is True

    def test_create_generation_protocol(self):
        """Test create_generation_protocol classmethod."""
        protocol = ProtocolBuilder.create_generation_protocol("generation_test")
        assert protocol.id == "generation_test"
        assert protocol.name == "Generation Protocol generation_test"
        assert protocol.configuration.supported_intents == [
            IntentCategory.GENERATE,
            IntentCategory.CREATE,
            IntentCategory.TRANSFORM,
        ]
        assert protocol.configuration.default_scope == ContextScope.WORKFLOW
        assert protocol.configuration.enable_learning is True

    def test_create_coordination_protocol(self):
        """Test create_coordination_protocol classmethod."""
        protocol = ProtocolBuilder.create_coordination_protocol("coordination_test")
        assert protocol.id == "coordination_test"
        assert protocol.name == "Coordination Protocol coordination_test"
        assert protocol.configuration.supported_intents == [
            IntentCategory.COORDINATE,
            IntentCategory.EXECUTE,
            IntentCategory.CONTROL,
        ]
        assert protocol.configuration.default_scope == ContextScope.TEAM
        assert protocol.configuration.max_execution_time == 600
        assert protocol.configuration.retry_attempts == 5


class TestBuiltProtocol:
    """Test BuiltProtocol functionality."""

    @pytest.fixture
    def built_protocol(self):
        """Create a test protocol."""
        return ProtocolBuilder().with_id("test_protocol").build()

    def test_protocol_properties(self, built_protocol):
        """Test protocol property access."""
        assert built_protocol.id == "test_protocol"
        assert built_protocol.name == "test_protocol"
        assert built_protocol.description == "Protocol test_protocol"

    def test_protocol_with_name_description(self):
        """Test protocol with custom name and description."""
        protocol = (
            ProtocolBuilder()
            .with_id("test_protocol")
            .with_name("Custom Name")
            .with_description("Custom Description")
            .build()
        )

        assert protocol.name == "Custom Name"
        assert protocol.description == "Custom Description"

    @pytest.mark.asyncio
    async def test_parse_command(self, built_protocol):
        """Test command parsing."""
        command = await built_protocol.parse_command("analyze this code")
        assert isinstance(command, ParsedCommand)
        assert command.original_text == "analyze this code"
        assert command.intent is not None

    @pytest.mark.asyncio
    async def test_create_execution_plan(self, built_protocol):
        """Test execution plan creation."""
        command = await built_protocol.parse_command("analyze this code")
        context = CommandContext()

        plan = await built_protocol.create_execution_plan(command, context)
        assert isinstance(plan, ExecutionPlan)
        assert plan.command_id == command.id

    def test_get_statistics(self, built_protocol):
        """Test getting protocol statistics."""
        stats = built_protocol.get_statistics()
        assert isinstance(stats, dict)
        assert "parser_stats" in stats

    def test_update_statistics(self, built_protocol):
        """Test updating protocol statistics."""
        built_protocol.update_statistics("test_key", "test_value")
        assert built_protocol.statistics["test_key"] == "test_value"


class TestSemanticCommandParsing:
    """Test semantic command parsing functionality."""

    @pytest.fixture
    def parser(self):
        """Create a test parser."""
        return ProtocolParser()

    @pytest.mark.asyncio
    async def test_parse_analysis_command(self, parser):
        """Test parsing analysis commands."""
        command = await parser.parse_command("analyze this Python code")
        assert command.intent.category == IntentCategory.ANALYZE
        assert (
            "python" in command.intent.target.lower()
            or "code" in command.intent.target.lower()
        )
        assert command.command_type == CommandType.ANALYSIS

    @pytest.mark.asyncio
    async def test_parse_generation_command(self, parser):
        """Test parsing generation commands."""
        command = await parser.parse_command("generate a test for this function")
        assert command.intent.category == IntentCategory.GENERATE
        assert "test" in command.intent.target.lower()
        assert command.command_type == CommandType.GENERATION

    @pytest.mark.asyncio
    async def test_parse_query_command(self, parser):
        """Test parsing query commands."""
        command = await parser.parse_command("show me all the agents")
        assert command.intent.category == IntentCategory.READ
        assert "agents" in command.intent.target.lower()
        assert command.command_type == CommandType.QUERY

    @pytest.mark.asyncio
    async def test_parse_coordination_command(self, parser):
        """Test parsing coordination commands."""
        command = await parser.parse_command(
            "coordinate the team to complete this task"
        )
        assert command.intent.category == IntentCategory.COORDINATE
        assert "team" in command.intent.target.lower()
        assert command.command_type == CommandType.COORDINATION

    @pytest.mark.asyncio
    async def test_parse_with_context(self, parser):
        """Test parsing with context."""
        context = CommandContext(
            project_id="test_project", agent_id="test_agent", scope=ContextScope.PROJECT
        )

        command = await parser.parse_command("analyze the current project", context)
        assert command.intent.category == IntentCategory.ANALYZE
        assert "project" in command.intent.target.lower()

    @pytest.mark.asyncio
    async def test_parse_invalid_command(self, parser):
        """Test parsing invalid commands."""
        command = await parser.parse_command("")
        assert not command.is_valid
        assert len(command.validation_errors) > 0

    @pytest.mark.asyncio
    async def test_command_validation(self, parser):
        """Test command validation."""
        # Valid command
        valid_command = await parser.parse_command("analyze this code")
        assert valid_command.is_valid

        # Invalid command
        invalid_command = await parser.parse_command("")
        assert not invalid_command.is_valid
        assert "Command cannot be empty" in invalid_command.validation_errors

    def test_parser_statistics(self, parser):
        """Test parser statistics."""
        stats = parser.get_parser_statistics()
        assert isinstance(stats, dict)
        assert "total_commands_parsed" in stats["parser_stats"]
        assert "supported_intents" in stats


class TestIntentRecognition:
    """Test intent recognition functionality."""

    @pytest.fixture
    def recognizer(self):
        """Create a test intent recognizer."""
        return PatternBasedIntentRecognizer()

    @pytest.mark.asyncio
    async def test_recognize_create_intent(self, recognizer):
        """Test recognizing create intents."""
        context = CommandContext()
        intent = await recognizer.recognize_intent("create a new agent", context)
        assert intent.category == IntentCategory.CREATE
        assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_recognize_analyze_intent(self, recognizer):
        """Test recognizing analyze intents."""
        context = CommandContext()
        intent = await recognizer.recognize_intent(
            "analyze this code for bugs", context
        )
        assert intent.category == IntentCategory.ANALYZE
        assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_recognize_generate_intent(self, recognizer):
        """Test recognizing generate intents."""
        context = CommandContext()
        intent = await recognizer.recognize_intent("generate documentation", context)
        assert intent.category == IntentCategory.GENERATE
        assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_recognize_with_context_history(self, recognizer):
        """Test intent recognition with context history."""
        context = CommandContext()
        context.history = [
            {"intent": {"category": "analyze"}},
            {"intent": {"category": "analyze"}},
        ]

        intent = await recognizer.recognize_intent("check this", context)
        # Should boost confidence for analyze intent due to history
        assert intent.confidence >= 0.1

    def test_supported_intents(self, recognizer):
        """Test getting supported intents."""
        supported = recognizer.get_supported_intents()
        assert IntentCategory.ANALYZE in supported
        assert IntentCategory.GENERATE in supported
        assert IntentCategory.QUERY in supported


class TestExecutionPlanning:
    """Test execution planning functionality."""

    @pytest.fixture
    def parser(self):
        """Create a test parser."""
        return ProtocolParser()

    @pytest.mark.asyncio
    async def test_create_execution_plan_basic(self, parser):
        """Test basic execution plan creation."""
        command = await parser.parse_command("analyze this code")
        context = CommandContext()

        plan = await parser.create_execution_plan(command, context)
        assert isinstance(plan, ExecutionPlan)
        assert plan.command_id == command.id
        assert isinstance(plan.steps, list)
        assert plan.estimated_duration >= 0

    @pytest.mark.asyncio
    async def test_execution_plan_with_agents(self, parser):
        """Test execution plan with available agents."""
        # Mock agents
        mock_agent = Mock()
        mock_agent.id = "test_agent"

        command = await parser.parse_command("analyze this code")
        context = CommandContext()

        plan = await parser.create_execution_plan(
            command, context, available_agents=[mock_agent]
        )
        assert isinstance(plan, ExecutionPlan)
        assert plan.command_id == command.id

    @pytest.mark.asyncio
    async def test_execution_plan_complexity(self, parser):
        """Test execution plan complexity calculation."""
        simple_command = await parser.parse_command("show status")
        complex_command = await parser.parse_command(
            "analyze this complex multi-threaded application and generate comprehensive documentation"
        )

        context = CommandContext()
        simple_plan = await parser.create_execution_plan(simple_command, context)
        complex_plan = await parser.create_execution_plan(complex_command, context)

        # Complex command should have higher complexity
        assert complex_plan.complexity_score >= simple_plan.complexity_score


class TestIntegration:
    """Integration tests for protocol system."""

    @pytest.mark.asyncio
    async def test_full_protocol_workflow(self):
        """Test complete protocol workflow from creation to execution."""
        # Create protocol
        protocol = (
            ProtocolBuilder()
            .with_id("integration_test")
            .with_name("Integration Test Protocol")
            .with_supported_intents([IntentCategory.ANALYZE, IntentCategory.GENERATE])
            .build()
        )

        # Parse command
        command = await protocol.parse_command("analyze this Python code")
        assert command.is_valid
        assert command.intent.category == IntentCategory.ANALYZE

        # Create execution plan
        context = CommandContext(project_id="test_project")
        plan = await protocol.create_execution_plan(command, context)
        assert plan.command_id == command.id
        assert len(plan.steps) > 0

        # Check statistics
        stats = protocol.get_statistics()
        assert "parser_stats" in stats

    @pytest.mark.asyncio
    async def test_protocol_with_custom_recognizer(self):
        """Test protocol with custom intent recognizer."""
        # Create mock recognizer
        mock_recognizer = Mock(spec=IntentRecognizer)
        mock_recognizer.recognize_intent = AsyncMock(
            return_value=CommandIntent(
                category=IntentCategory.ANALYZE, action="analyze", confidence=0.9
            )
        )
        mock_recognizer.get_supported_intents = Mock(
            return_value=[IntentCategory.ANALYZE]
        )

        # Create protocol with custom recognizer
        protocol = (
            ProtocolBuilder()
            .with_id("custom_recognizer_test")
            .with_custom_intent_recognizer(mock_recognizer)
            .build()
        )

        # Parse command
        command = await protocol.parse_command("analyze this")
        assert command.intent.category == IntentCategory.ANALYZE
        assert command.intent.confidence == 0.9
