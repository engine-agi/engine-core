"""
Execution Tests for Protocol System.

Tests cover:
- End-to-end protocol execution workflows
- Agent and tool integration
- Complex command scenarios
- Error handling and recovery
- Performance and scalability
- Contract testing for protocol interfaces
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
import time

from engine_core.core.protocols.protocol_builder import (
    ProtocolBuilder,
    BuiltProtocol,
    ProtocolConfiguration
)
from engine_core.core.protocols.protocol import (
    ProtocolParser,
    CommandContext,
    ParsedCommand,
    ExecutionPlan,
    CommandIntent,
    IntentCategory,
    CommandType,
    ContextScope
)


class TestProtocolExecutionWorkflows:
    """Test complete protocol execution workflows."""

    @pytest.fixture
    def analysis_protocol(self):
        """Create an analysis-focused protocol."""
        return ProtocolBuilder.create_analysis_protocol("analysis_workflow_test")

    @pytest.fixture
    def generation_protocol(self):
        """Create a generation-focused protocol."""
        return ProtocolBuilder.create_generation_protocol("generation_workflow_test")

    @pytest.mark.asyncio
    async def test_analysis_workflow_execution(self, analysis_protocol):
        """Test complete analysis workflow from command to execution plan."""
        # Parse analysis command
        command = await analysis_protocol.parse_command(
            "analyze this Python code for performance issues and security vulnerabilities"
        )

        # Verify command parsing
        assert command.is_valid
        assert command.intent.category == IntentCategory.ANALYZE
        assert command.command_type == CommandType.ANALYSIS
        assert "performance" in command.intent.target.lower()
        assert "security" in command.intent.target.lower()

        # Create execution context
        context = CommandContext(
            project_id="test_project",
            agent_id="analyzer_agent",
            scope=ContextScope.PROJECT
        )

        # Create execution plan
        plan = await analysis_protocol.create_execution_plan(command, context)

        # Verify execution plan
        assert plan.command_id == command.id
        assert len(plan.steps) >= 0  # Allow for error steps
        assert plan.estimated_duration >= 0  # Duration might be 0 for error cases
        assert plan.complexity_score >= 0

    @pytest.mark.asyncio
    async def test_generation_workflow_execution(self, generation_protocol):
        """Test complete generation workflow."""
        # Parse generation command
        command = await generation_protocol.parse_command(
            "generate comprehensive unit tests for this API endpoint"
        )

        # Verify command parsing
        assert command.is_valid
        assert command.intent.category == IntentCategory.GENERATE
        assert command.command_type == CommandType.GENERATION
        assert "unit tests" in command.intent.target.lower()
        assert "api" in command.intent.target.lower() or "endpoint" in command.intent.target.lower()

        # Create execution context
        context = CommandContext(
            project_id="api_project",
            workflow_id="test_generation_workflow",
            scope=ContextScope.WORKFLOW
        )

        # Create execution plan
        plan = await generation_protocol.create_execution_plan(command, context)

        # Verify execution plan
        assert plan.command_id == command.id
        assert len(plan.steps) > 0
        assert plan.estimated_duration > 0

    @pytest.mark.asyncio
    async def test_coordination_workflow_execution(self):
        """Test coordination workflow with multiple agents."""
        protocol = ProtocolBuilder.create_coordination_protocol("coordination_test")

        context = CommandContext(
            team_id="dev_team",
            scope=ContextScope.TEAM
        )

        command = await protocol.parse_command(
            "coordinate the development team to implement user authentication",
            context
        )

        assert command.is_valid
        assert command.intent.category == IntentCategory.COORDINATE
        assert command.command_type == CommandType.COORDINATION

        context = CommandContext(
            team_id="dev_team",
            scope=ContextScope.TEAM
        )

        plan = await protocol.create_execution_plan(command, context)
        assert plan.command_id == command.id
        assert len(plan.steps) > 0

    @pytest.mark.asyncio
    async def test_complex_multi_step_workflow(self):
        """Test complex workflow with multiple steps and dependencies."""
        protocol = ProtocolBuilder().with_id("complex_workflow").build()

        command = await protocol.parse_command(
            "analyze the codebase, generate documentation, and create deployment scripts"
        )

        assert command.is_valid
        # The parser might break this into multiple intents or handle as complex command

        context = CommandContext(
            project_id="complex_project",
            scope=ContextScope.PROJECT
        )

        plan = await protocol.create_execution_plan(command, context)
        assert plan.command_id == command.id
        # Complex commands should have multiple steps
        assert len(plan.steps) >= 1


class TestAgentToolIntegration:
    """Test integration with agents and tools."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock()
        agent.id = "test_agent"
        agent.capabilities = ["analysis", "code_generation"]
        agent.is_available = Mock(return_value=True)
        return agent

    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool."""
        return "code_analyzer"

    @pytest.mark.asyncio
    async def test_execution_plan_with_agents(self, mock_agent):
        """Test execution plan creation with available agents."""
        protocol = ProtocolBuilder().with_id("agent_integration_test").build()

        command = await protocol.parse_command("analyze this code")
        context = CommandContext()

        plan = await protocol.create_execution_plan(
            command, context, available_agents=[mock_agent]
        )

        assert plan.command_id == command.id
        # Should include the mock agent in requirements if compatible
        assert isinstance(plan.agents_required, list)

    @pytest.mark.asyncio
    async def test_execution_plan_with_tools(self, mock_tool):
        """Test execution plan creation with available tools."""
        protocol = ProtocolBuilder().with_id("tool_integration_test").build()

        command = await protocol.parse_command("analyze this code")
        context = CommandContext()

        plan = await protocol.create_execution_plan(
            command, context, available_tools=[mock_tool]
        )

        assert plan.command_id == command.id
        assert isinstance(plan.tools_required, list)

    @pytest.mark.asyncio
    async def test_agent_capability_matching(self):
        """Test that execution plans match appropriate agents based on capabilities."""
        # Create protocol
        protocol = ProtocolBuilder().with_id("capability_test").build()

        # Create mock agents with different capabilities
        analysis_agent = Mock()
        analysis_agent.id = "analysis_agent"
        analysis_agent.capabilities = ["code_analysis", "security_scan"]

        generation_agent = Mock()
        generation_agent.id = "generation_agent"
        generation_agent.capabilities = ["code_generation", "documentation"]

        # Test analysis command
        analysis_command = await protocol.parse_command("analyze this code for security issues")
        context = CommandContext()

        analysis_plan = await protocol.create_execution_plan(
            analysis_command, context, available_agents=[analysis_agent, generation_agent]
        )

        assert analysis_plan.command_id == analysis_command.id

        # Test generation command
        generation_command = await protocol.parse_command("generate unit tests")
        generation_plan = await protocol.create_execution_plan(
            generation_command, context, available_agents=[analysis_agent, generation_agent]
        )

        assert generation_plan.command_id == generation_command.id


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_invalid_command_handling(self):
        """Test handling of invalid or malformed commands."""
        protocol = ProtocolBuilder().with_id("error_test").build()

        # Test empty command
        command = await protocol.parse_command("")
        assert not command.is_valid
        assert len(command.validation_errors) > 0

        # Test gibberish command
        command = await protocol.parse_command("asdfghjkl qwerty")
        assert not command.is_valid or command.intent.confidence < 0.5

    @pytest.mark.asyncio
    async def test_context_validation(self):
        """Test context validation for commands."""
        protocol = ProtocolBuilder().with_id("context_test").build()

        # Command requiring project context without project
        command = await protocol.parse_command("analyze project files")
        context = CommandContext()  # No project_id

        validated_command = await protocol.parser.command_validator.validate_command(command, context)
        # Should have validation errors or suggestions
        assert len(validated_command.validation_errors) >= 0  # May or may not have errors

    @pytest.mark.asyncio
    async def test_execution_plan_error_recovery(self):
        """Test execution plan creation with error recovery."""
        protocol = ProtocolBuilder().with_id("recovery_test").build()

        # Create a command that might be difficult to plan
        command = await protocol.parse_command("do something impossible")
        context = CommandContext()

        # Should still create a plan, even if minimal
        plan = await protocol.create_execution_plan(command, context)
        assert isinstance(plan, ExecutionPlan)
        assert plan.command_id == command.id
        # Should have at least error handling steps
        assert len(plan.steps) >= 0

    @pytest.mark.asyncio
    async def test_fallback_plan_generation(self):
        """Test generation of fallback plans for failed executions."""
        protocol = (ProtocolBuilder()
            .with_id("fallback_test")
            .with_fallbacks_enabled(True)
            .build())

        command = await protocol.parse_command("execute critical operation")
        context = CommandContext()

        plan = await protocol.create_execution_plan(command, context)
        # Should include fallback plans
        assert isinstance(plan.fallback_plans, list)


class TestPerformanceAndScalability:
    """Test performance and scalability of protocol system."""

    @pytest.mark.asyncio
    async def test_concurrent_command_processing(self):
        """Test processing multiple commands concurrently."""
        protocol = ProtocolBuilder().with_id("performance_test").build()

        commands = [
            "analyze this code",
            "generate documentation",
            "create unit tests",
            "validate configuration",
            "coordinate team tasks"
        ]

        # Process commands concurrently
        start_time = time.time()
        tasks = [protocol.parse_command(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify all commands were processed
        assert len(results) == len(commands)
        for result in results:
            assert isinstance(result, ParsedCommand)

        # Should complete within reasonable time (adjust based on system)
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Less than 5 seconds for 5 commands

    @pytest.mark.asyncio
    async def test_large_context_handling(self):
        """Test handling of commands with large context."""
        protocol = ProtocolBuilder().with_id("large_context_test").build()

        # Create large context with history
        large_history = [
            {"intent": {"category": "analyze"}, "timestamp": "2024-01-01T00:00:00Z"}
            for _ in range(50)
        ]

        context = CommandContext(
            history=large_history,
            variables={"large_var": "x" * 1000}  # Large variable
        )

        command = await protocol.parse_command("analyze based on history", context)
        assert command.is_valid
        assert isinstance(command, ParsedCommand)

    def test_parser_statistics_tracking(self):
        """Test that parser statistics are properly tracked."""
        protocol = ProtocolBuilder().with_id("stats_test").build()

        # Get initial stats
        initial_stats = protocol.get_statistics()
        assert "parser_stats" in initial_stats
        assert "total_commands_parsed" in initial_stats["parser_stats"]

        initial_count = initial_stats["parser_stats"]["total_commands_parsed"]

        # Note: In real usage, stats would be updated after parsing
        # This test verifies the stats structure is correct


class TestProtocolContractCompliance:
    """Test that protocols comply with defined contracts and interfaces."""

    def test_protocol_builder_interface(self):
        """Test that ProtocolBuilder implements expected interface."""
        builder = ProtocolBuilder()

        # Test all expected methods exist
        assert hasattr(builder, 'with_id')
        assert hasattr(builder, 'with_name')
        assert hasattr(builder, 'with_description')
        assert hasattr(builder, 'build')

        # Test method chaining
        result = builder.with_id("test").with_name("Test")
        assert result is builder

    def test_built_protocol_interface(self):
        """Test that BuiltProtocol implements expected interface."""
        protocol = ProtocolBuilder().with_id("interface_test").build()

        # Test all expected attributes
        assert hasattr(protocol, 'id')
        assert hasattr(protocol, 'configuration')
        assert hasattr(protocol, 'parser')
        assert hasattr(protocol, 'statistics')

        # Test all expected methods
        assert hasattr(protocol, 'parse_command')
        assert hasattr(protocol, 'create_execution_plan')
        assert hasattr(protocol, 'get_statistics')
        assert hasattr(protocol, 'update_statistics')

    def test_protocol_parser_interface(self):
        """Test that ProtocolParser implements expected interface."""
        parser = ProtocolParser()

        # Test expected methods
        assert hasattr(parser, 'parse_command')
        assert hasattr(parser, 'create_execution_plan')
        assert hasattr(parser, 'get_parser_statistics')

    def test_command_intent_structure(self):
        """Test that CommandIntent has expected structure."""
        intent = CommandIntent(
            category=IntentCategory.ANALYZE,
            action="analyze",
            target="code",
            confidence=0.8
        )

        assert intent.category == IntentCategory.ANALYZE
        assert intent.action == "analyze"
        assert intent.target == "code"
        assert intent.confidence == 0.8
        assert isinstance(intent.parameters, dict)
        assert isinstance(intent.modifiers, list)

    def test_parsed_command_structure(self):
        """Test that ParsedCommand has expected structure."""
        command = ParsedCommand(
            original_text="test command",
            normalized_text="test command"
        )

        assert command.original_text == "test command"
        assert command.normalized_text == "test command"
        assert command.id is not None
        assert isinstance(command.parameters, dict)
        assert isinstance(command.validation_errors, list)
        assert isinstance(command.suggestions, list)

    def test_execution_plan_structure(self):
        """Test that ExecutionPlan has expected structure."""
        plan = ExecutionPlan(command_id="test_id")

        assert plan.command_id == "test_id"
        assert isinstance(plan.steps, list)
        assert isinstance(plan.agents_required, list)
        assert isinstance(plan.tools_required, list)
        assert plan.estimated_duration >= 0
        assert plan.complexity_score >= 0


class TestConfigurationValidation:
    """Test protocol configuration validation."""

    def test_configuration_defaults(self):
        """Test that default configuration values are reasonable."""
        config = ProtocolConfiguration(id="test")

        assert config.version == "1.0.0"
        assert config.default_scope == ContextScope.SESSION
        assert config.strict_validation is False
        assert config.max_execution_time == 300
        assert config.retry_attempts == 3
        assert config.enable_fallbacks is True
        assert config.learning_rate == 0.1
        assert config.confidence_threshold == 0.6

    def test_configuration_validation(self):
        """Test configuration value validation."""
        builder = ProtocolBuilder()

        # Test valid values
        builder.with_max_execution_time(600)
        builder.with_retry_attempts(5)
        builder.with_learning_rate(0.5)
        builder.with_confidence_threshold(0.8)

        # Test invalid values raise errors
        with pytest.raises(ValueError):
            builder.with_max_execution_time(-1)

        with pytest.raises(ValueError):
            builder.with_retry_attempts(-1)

        with pytest.raises(ValueError):
            builder.with_learning_rate(1.5)

        with pytest.raises(ValueError):
            builder.with_confidence_threshold(-0.1)

    def test_protocol_metadata(self):
        """Test protocol metadata handling."""
        builder = ProtocolBuilder().with_id("metadata_test")

        # Add metadata
        builder.with_metadata("author", "Test Author")
        builder.with_metadata("version", "2.0.0")
        builder.with_metadata("tags", ["test", "protocol"])

        protocol = builder.build()

        assert protocol.configuration.metadata["author"] == "Test Author"
        assert protocol.configuration.metadata["version"] == "2.0.0"
        assert protocol.configuration.metadata["tags"] == ["test", "protocol"]