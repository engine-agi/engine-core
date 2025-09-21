"""
Unit Tests for ToolBuilder - Tool Integration Architecture.

Tests cover:
- ToolBuilder fluent interface and validation
- Tool configuration creation and validation
- Plugin system extensibility
- Tool execution interfaces
- API integration capabilities
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

# Import tool components
from src.engine_core.core.tools.tool_builder import (
    ToolBuilder,
    ToolConfiguration,
    ToolType,
    ToolExecutionMode,
    ExecutionEnvironment,
    PermissionLevel,
    ToolCapability
)


class TestToolBuilder:
    """Test ToolBuilder fluent interface and validation."""

    def test_builder_initialization(self):
        """Test builder initializes with default values."""
        builder = ToolBuilder()

        assert builder._tool_id is None
        assert builder._name is None
        assert builder._tool_type is None
        assert builder._version == "1.0.0"
        assert builder._description == ""
        assert builder._timeout_seconds == 30

    def test_with_id_and_name(self):
        """Test setting tool ID and name."""
        builder = ToolBuilder()

        result = builder.with_id("test_tool").with_name("Test Tool")

        assert result._tool_id == "test_tool"
        assert result._name == "Test Tool"
        assert result is builder  # Fluent interface

    def test_with_type(self):
        """Test setting tool type."""
        builder = ToolBuilder()

        result = builder.with_type(ToolType.API)

        assert result._tool_type == ToolType.API

    def test_build_minimal_tool(self):
        """Test building a minimal tool configuration."""
        builder = ToolBuilder()

        config = (builder
                 .with_id("minimal_tool")
                 .with_name("Minimal Tool")
                 .with_type(ToolType.API)
                 .build())

        assert isinstance(config, ToolConfiguration)
        assert config.tool_id == "minimal_tool"
        assert config.name == "Minimal Tool"
        assert config.tool_type == ToolType.API
        assert config.version == "1.0.0"

    def test_build_fails_without_required_fields(self):
        """Test build fails when required fields are missing."""
        builder = ToolBuilder()

        # Missing ID
        with pytest.raises(ValueError, match="Tool ID is required"):
            builder.with_name("Test").with_type(ToolType.API).build()

        # Reset builder for next test
        builder.reset()

        # Missing name
        with pytest.raises(ValueError, match="Tool name is required"):
            builder.with_id("test").with_type(ToolType.API).build()

        # Reset builder for next test
        builder.reset()

        # Missing type
        with pytest.raises(ValueError, match="Tool type is required"):
            builder.with_id("test").with_name("Test").build()

    def test_with_endpoint_and_authentication(self):
        """Test setting endpoint and authentication."""
        builder = ToolBuilder()

        auth = {"type": "bearer", "token": "secret"}
        headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}

        config = (builder
                 .with_id("api_tool")
                 .with_name("API Tool")
                 .with_type(ToolType.API)
                 .with_endpoint("https://api.example.com/v1")
                 .with_authentication(auth)
                 .with_headers(headers)
                 .build())

        assert config.endpoint == "https://api.example.com/v1"
        assert config.authentication == auth
        assert config.headers == headers

    def test_with_execution_settings(self):
        """Test setting execution configuration."""
        builder = ToolBuilder()

        config = (builder
                 .with_id("exec_tool")
                 .with_name("Execution Tool")
                 .with_type(ToolType.CLI)
                 .with_execution_mode(ToolExecutionMode.ASYNCHRONOUS)
                 .with_execution_environment(ExecutionEnvironment.SANDBOX)
                 .with_timeout(60)
                 .with_concurrent_executions(10)
                 .build())

        assert config.execution_mode == ToolExecutionMode.ASYNCHRONOUS
        assert config.execution_environment == ExecutionEnvironment.SANDBOX
        assert config.timeout_seconds == 60
        assert config.max_concurrent_executions == 10

    def test_with_security_settings(self):
        """Test setting security and permission configuration."""
        builder = ToolBuilder()

        permissions = {PermissionLevel.READ_ONLY, PermissionLevel.READ_WRITE}
        users = {"user1", "user2"}
        projects = {"project1"}

        config = (builder
                 .with_id("secure_tool")
                 .with_name("Secure Tool")
                 .with_type(ToolType.API)
                 .with_permissions(permissions)
                 .with_allowed_users(users)
                 .with_allowed_projects(projects)
                 .build())

        assert config.required_permissions == permissions
        assert config.allowed_users == users
        assert config.allowed_projects == projects

    def test_with_capabilities(self):
        """Test adding tool capabilities."""
        builder = ToolBuilder()

        capability = ToolCapability(
            name="get_data",
            description="Retrieve data from API",
            input_schema={"type": "object", "properties": {"id": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"data": {"type": "object"}}},
            metadata={"http_method": "GET", "endpoint": "/data/{id}"}
        )

        config = (builder
                 .with_id("capability_tool")
                 .with_name("Capability Tool")
                 .with_type(ToolType.API)
                 .with_capabilities([capability])
                 .build())

        assert len(config.capabilities) == 1
        assert config.capabilities[0].name == "get_data"
        assert config.capabilities[0].metadata["http_method"] == "GET"

    def test_with_plugin_configuration(self):
        """Test plugin-specific configuration."""
        builder = ToolBuilder()

        plugin_config = {"model": "gpt-4", "temperature": 0.7}

        config = (builder
                 .with_id("plugin_tool")
                 .with_name("Plugin Tool")
                 .with_type(ToolType.PLUGIN)
                 .with_plugin_class("engine_core.tools.plugins.OpenAIPlugin")
                 .with_plugin_config(plugin_config)
                 .build())

        assert config.plugin_class == "engine_core.tools.plugins.OpenAIPlugin"
        assert config.plugin_config == plugin_config

    def test_with_mcp_configuration(self):
        """Test MCP server configuration."""
        builder = ToolBuilder()

        config = (builder
                 .with_id("mcp_tool")
                 .with_name("MCP Tool")
                 .with_type(ToolType.MCP)
                 .with_mcp_server("/usr/local/bin/mcp-server", args=["--port", "8080"], env={"DEBUG": "1"})
                 .build())

        assert config.mcp_server_path == "/usr/local/bin/mcp-server"
        assert config.mcp_args == ["--port", "8080"]
        assert config.mcp_env == {"DEBUG": "1"}

    def test_builder_reset(self):
        """Test builder reset functionality."""
        builder = ToolBuilder()

        # Configure builder
        builder.with_id("test").with_name("Test").with_type(ToolType.API)

        # Reset
        builder.reset()

        # Check reset state
        assert builder._tool_id is None
        assert builder._name is None
        assert builder._tool_type is None

    def test_with_tags_and_metadata(self):
        """Test setting tags and metadata."""
        builder = ToolBuilder()

        tags = ["api", "external", "data"]
        metadata = {"version": "2.0", "author": "team", "category": "integration"}

        config = (builder
                 .with_id("tagged_tool")
                 .with_name("Tagged Tool")
                 .with_type(ToolType.API)
                 .with_tags(tags)
                 .with_metadata(metadata)
                 .build())

        assert config.tags == tags
        assert config.metadata == metadata


class TestToolConfiguration:
    """Test ToolConfiguration data structure."""

    def test_tool_configuration_creation(self):
        """Test creating tool configuration directly."""
        config = ToolConfiguration(
            tool_id="direct_config",
            name="Direct Config Tool",
            tool_type=ToolType.API,
            version="2.0.0",
            description="Directly created configuration",
            endpoint="https://api.example.com",
            timeout_seconds=45,
            capabilities=[]
        )

        assert config.tool_id == "direct_config"
        assert config.name == "Direct Config Tool"
        assert config.tool_type == ToolType.API
        assert config.version == "2.0.0"
        assert config.endpoint == "https://api.example.com"
        assert config.timeout_seconds == 45

    def test_tool_configuration_defaults(self):
        """Test default values in tool configuration."""
        config = ToolConfiguration(
            tool_id="defaults_test",
            name="Defaults Test",
            tool_type=ToolType.CLI
        )

        assert config.version == "1.0.0"
        assert config.description == ""
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.execution_mode == ToolExecutionMode.SYNCHRONOUS
        assert config.execution_environment == ExecutionEnvironment.SANDBOX
        assert config.max_concurrent_executions == 5
        assert len(config.capabilities) == 0
        assert len(config.tags) == 0
        assert isinstance(config.metadata, dict)


class TestToolCapability:
    """Test ToolCapability structure."""

    def test_capability_creation(self):
        """Test creating tool capability."""
        capability = ToolCapability(
            name="process_data",
            description="Process input data",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "string"},
                    "format": {"type": "string", "enum": ["json", "xml"]}
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "object"},
                    "status": {"type": "string"}
                }
            },
            required_permissions={"read", "write"},
            execution_time_estimate=2.5,
            metadata={"http_method": "POST", "endpoint": "/process"}
        )

        assert capability.name == "process_data"
        assert capability.description == "Process input data"
        assert capability.input_schema["required"] == ["data"]
        assert capability.execution_time_estimate == 2.5
        assert capability.metadata["http_method"] == "POST"


class TestToolEnums:
    """Test tool-related enumerations."""

    def test_tool_type_enum(self):
        """Test ToolType enumeration."""
        assert ToolType.API.value == "api"
        assert ToolType.CLI.value == "cli"
        assert ToolType.MCP.value == "mcp"
        assert ToolType.PLUGIN.value == "plugin"
        assert ToolType.FUNCTION.value == "function"
        assert ToolType.WORKFLOW.value == "workflow"
        assert ToolType.COMPOSITE.value == "composite"

    def test_execution_mode_enum(self):
        """Test ToolExecutionMode enumeration."""
        assert ToolExecutionMode.SYNCHRONOUS.value == "synchronous"
        assert ToolExecutionMode.ASYNCHRONOUS.value == "asynchronous"
        assert ToolExecutionMode.STREAMING.value == "streaming"
        assert ToolExecutionMode.BATCH.value == "batch"

    def test_execution_environment_enum(self):
        """Test ExecutionEnvironment enumeration."""
        # Note: These would need to be defined in the actual enum
        # This is a placeholder test
        pass

    def test_permission_level_enum(self):
        """Test PermissionLevel enumeration."""
        # Note: These would need to be defined in the actual enum
        # This is a placeholder test
        pass


# === Integration Tests ===

class TestToolBuilderIntegration:
    """Integration tests for ToolBuilder with real scenarios."""

    def test_api_tool_builder(self):
        """Test building a complete API tool."""
        builder = ToolBuilder()

        config = (builder
                 .with_id("github_api_tool")
                 .with_name("GitHub API Tool")
                 .with_description("Tool for interacting with GitHub API")
                 .with_type(ToolType.API)
                 .with_endpoint("https://api.github.com")
                 .with_authentication({"type": "bearer", "token": "ghp_..."})
                 .with_headers({"Accept": "application/vnd.github.v3+json"})
                 .with_timeout(30)
                 .with_retry_attempts(3)
                 .with_execution_mode(ToolExecutionMode.ASYNCHRONOUS)
                 .with_concurrent_executions(10)
                 .with_rate_limit(5000)  # 5000 requests per minute
                 .with_permissions({PermissionLevel.READ_ONLY})
                 .with_tags(["api", "github", "version-control"])
                 .with_metadata({"provider": "github", "api_version": "v3"})
                 .build())

        assert config.tool_id == "github_api_tool"
        assert config.endpoint == "https://api.github.com"
        assert config.execution_mode == ToolExecutionMode.ASYNCHRONOUS
        assert config.rate_limit_requests_per_minute == 5000
        assert "github" in config.tags
        assert config.metadata["provider"] == "github"

    def test_cli_tool_builder(self):
        """Test building a CLI tool."""
        builder = ToolBuilder()

        config = (builder
                 .with_id("docker_cli_tool")
                 .with_name("Docker CLI Tool")
                 .with_description("Tool for Docker container management")
                 .with_type(ToolType.CLI)
                 .with_execution_environment(ExecutionEnvironment.SANDBOX)
                 .with_sandbox_restrictions({
                     "allowed_commands": ["docker", "ps", "images", "logs"],
                     "forbidden_flags": ["--privileged", "--network=host"]
                 })
                 .with_permissions({PermissionLevel.READ_WRITE})
                 .with_tags(["cli", "docker", "containers"])
                 .build())

        assert config.tool_type == ToolType.CLI
        assert config.execution_environment == ExecutionEnvironment.SANDBOX
        assert "docker" in config.sandbox_restrictions["allowed_commands"]
        assert PermissionLevel.READ_WRITE in config.required_permissions

    def test_plugin_tool_builder(self):
        """Test building a plugin tool."""
        builder = ToolBuilder()

        config = (builder
                 .with_id("openai_plugin_tool")
                 .with_name("OpenAI Plugin Tool")
                 .with_description("Tool for OpenAI API integration")
                 .with_type(ToolType.PLUGIN)
                 .with_plugin_class("engine_core.tools.plugins.OpenAIPlugin")
                 .with_plugin_config({
                     "model": "gpt-4",
                     "temperature": 0.7,
                     "max_tokens": 2000
                 })
                 .with_permissions({PermissionLevel.READ_ONLY})
                 .with_tags(["ai", "openai", "nlp"])
                 .build())

        assert config.tool_type == ToolType.PLUGIN
        assert "OpenAIPlugin" in config.plugin_class
        assert config.plugin_config["model"] == "gpt-4"
        assert "ai" in config.tags


# === Run Tests ===

if __name__ == "__main__":
    # Run basic validation tests
    print("🧪 Running ToolBuilder Tests")
    print("=" * 40)

    try:
        # Test basic builder
        builder = ToolBuilder()
        print("✅ Builder creation: PASSED")

        # Test fluent interface
        builder.with_id("test").with_name("Test").with_type(ToolType.API)
        print("✅ Fluent interface: PASSED")

        # Test build
        config = builder.build()
        print("✅ Tool build: PASSED")
        print(f"   Tool ID: {config.tool_id}")
        print(f"   Type: {config.tool_type.value}")

        # Test capability
        capability = ToolCapability(
            name="test_cap",
            description="Test capability",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )
        print("✅ Capability creation: PASSED")

        # Test enums
        print(f"   Tool types: {len([t for t in ToolType])}")
        print(f"   Execution modes: {len([m for m in ToolExecutionMode])}")

        print("\n🎉 All basic tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()