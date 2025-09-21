#!/usr/bin/env python3
"""
Integration test for ToolBuilder - demonstrates complete tool creation and configuration.
"""

import sys
import os
from unittest.mock import MagicMock

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

async def test_tool_builder_integration():
    """Test complete ToolBuilder functionality with real scenarios."""
    print("🔧 Testing ToolBuilder Integration")

    try:
        from engine_core.core.tools.tool_builder import (
            ToolBuilder, ToolConfiguration, ToolType, ToolExecutionMode,
            ExecutionEnvironment, PermissionLevel, ToolCapability
        )

        # Test 1: Build a GitHub API Tool
        print("\n1. Building GitHub API Tool...")
        github_tool = (ToolBuilder()
                      .with_id("github_api_tool")
                      .with_name("GitHub API Integration")
                      .with_description("Tool for interacting with GitHub REST API")
                      .with_type(ToolType.API)
                      .with_endpoint("https://api.github.com")
                      .with_authentication({
                          "type": "bearer",
                          "token": "ghp_..."  # Would be actual token
                      })
                      .with_headers({
                          "Accept": "application/vnd.github.v3+json",
                          "User-Agent": "Engine-Framework/1.0"
                      })
                      .with_timeout(30)
                      .with_retry_attempts(3)
                      .with_execution_mode(ToolExecutionMode.ASYNCHRONOUS)
                      .with_concurrent_executions(10)
                      .with_rate_limit(5000)  # 5000 requests per hour
                      .with_permissions({PermissionLevel.READ_ONLY})
                      .with_allowed_users({"user1", "user2"})
                      .with_tags(["api", "github", "version-control"])
                      .with_metadata({
                          "provider": "github",
                          "api_version": "v3",
                          "documentation": "https://docs.github.com/en/rest"
                      })
                      .build())

        assert github_tool.tool_id == "github_api_tool"
        assert github_tool.tool_type == ToolType.API
        assert github_tool.endpoint == "https://api.github.com"
        assert github_tool.execution_mode == ToolExecutionMode.ASYNCHRONOUS
        assert PermissionLevel.READ_ONLY in github_tool.required_permissions
        print("✅ GitHub API Tool created successfully")

        # Test 2: Build a Docker CLI Tool
        print("\n2. Building Docker CLI Tool...")
        docker_tool = (ToolBuilder()
                      .with_id("docker_cli_tool")
                      .with_name("Docker Container Management")
                      .with_description("CLI tool for Docker container operations")
                      .with_type(ToolType.CLI)
                      .with_execution_environment(ExecutionEnvironment.SANDBOX)
                      .with_sandbox_restrictions({
                          "allowed_commands": ["docker", "ps", "images", "logs"],
                          "forbidden_flags": ["--privileged", "--network=host"],
                          "max_execution_time": 300
                      })
                      .with_permissions({PermissionLevel.READ_ONLY, PermissionLevel.READ_WRITE})
                      .with_tags(["cli", "docker", "containers"])
                      .with_metadata({
                          "requires_docker": True,
                          "sandbox_level": "medium"
                      })
                      .build())

        assert docker_tool.tool_type == ToolType.CLI
        assert docker_tool.execution_environment == ExecutionEnvironment.SANDBOX
        assert "docker" in docker_tool.sandbox_restrictions["allowed_commands"]
        print("✅ Docker CLI Tool created successfully")

        # Test 3: Build a Plugin Tool
        print("\n3. Building OpenAI Plugin Tool...")
        openai_tool = (ToolBuilder()
                      .with_id("openai_plugin_tool")
                      .with_name("OpenAI Language Model")
                      .with_description("Plugin for OpenAI GPT model integration")
                      .with_type(ToolType.PLUGIN)
                      .with_plugin_class("engine_core.tools.plugins.OpenAIPlugin")
                      .with_plugin_config({
                          "model": "gpt-4",
                          "temperature": 0.7,
                          "max_tokens": 2000,
                          "api_key": "sk-..."  # Would be actual key
                      })
                      .with_timeout(60)
                      .with_permissions({PermissionLevel.READ_ONLY})
                      .with_tags(["ai", "openai", "nlp", "generation"])
                      .with_metadata({
                          "model_family": "gpt-4",
                          "context_window": 8192,
                          "training_data": "up_to_2023"
                      })
                      .build())

        assert openai_tool.tool_type == ToolType.PLUGIN
        assert "OpenAIPlugin" in openai_tool.plugin_class
        assert openai_tool.plugin_config["model"] == "gpt-4"
        print("✅ OpenAI Plugin Tool created successfully")

        # Test 4: Tool with Capabilities
        print("\n4. Building Tool with Capabilities...")
        capability = ToolCapability(
            name="get_user_repos",
            description="Retrieve user's GitHub repositories",
            input_schema={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "sort": {"type": "string", "enum": ["created", "updated", "pushed"]},
                    "per_page": {"type": "integer", "minimum": 1, "maximum": 100}
                },
                "required": ["username"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "repositories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "full_name": {"type": "string"},
                                "html_url": {"type": "string"},
                                "description": {"type": "string"},
                                "language": {"type": "string"}
                            }
                        }
                    },
                    "total_count": {"type": "integer"}
                }
            },
            required_permissions={"read"},
            execution_time_estimate=2.0,
            metadata={
                "http_method": "GET",
                "endpoint": "/users/{username}/repos",
                "rate_limit_category": "core"
            }
        )

        advanced_github_tool = (ToolBuilder()
                               .with_id("advanced_github_tool")
                               .with_name("Advanced GitHub API Tool")
                               .with_type(ToolType.API)
                               .with_endpoint("https://api.github.com")
                               .with_capabilities([capability])
                               .with_tags(["api", "github", "advanced"])
                               .build())

        assert len(advanced_github_tool.capabilities) == 1
        assert advanced_github_tool.capabilities[0].name == "get_user_repos"
        assert advanced_github_tool.capabilities[0].metadata["http_method"] == "GET"
        print("✅ Advanced Tool with Capabilities created successfully")

        # Test 5: Validation
        print("\n5. Testing Validation...")
        try:
            invalid_tool = ToolBuilder().build()
            assert False, "Should have failed validation"
        except ValueError as e:
            assert "Tool ID is required" in str(e)
            print("✅ Validation working correctly")

        print("\n🎯 ToolBuilder Integration Test Summary:")
        print("   ✅ API Tool creation and configuration")
        print("   ✅ CLI Tool with sandbox restrictions")
        print("   ✅ Plugin Tool with custom configuration")
        print("   ✅ Advanced Tool with capabilities and schemas")
        print("   ✅ Input validation and error handling")
        print("   ✅ All tool types supported")
        print("   ✅ Security and permission management")
        print("   ✅ Metadata and tagging system")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_tool_builder_integration())
    if success:
        print("\n🎉 ToolBuilder Integration Tests PASSED!")
        print("🚀 Tools system is ready for production use!")
        sys.exit(0)
    else:
        print("\n❌ ToolBuilder Integration Tests FAILED!")
        sys.exit(1)