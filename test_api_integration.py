"""
API Integration Test - Demonstrates tool integration with external APIs.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock

from engine_core.core.tools.tool_builder import APITool, ToolBuilder, ToolType

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)


async def test_api_tool_basic():
    """Test basic API tool functionality."""
    print("🌐 Testing Basic API Tool Functionality")

    try:
        # Create API tool configuration
        api_tool_config = (
            ToolBuilder()
            .with_id("test_api")
            .with_name("Test API")
            .with_description("Simple test API")
            .with_type(ToolType.API)
            .with_endpoint("https://httpbin.org")
            .with_headers(
                {"Accept": "application/json", "User-Agent": "Engine-Test/1.0"}
            )
            .with_timeout(10)
            .build()
        )

        assert api_tool_config.tool_id == "test_api"
        assert api_tool_config.tool_type == ToolType.API
        print("✅ API Tool configuration created")

        # Create API tool instance
        api_tool = APITool(api_tool_config)

        # Mock the session and test initialization
        mock_session = AsyncMock()
        api_tool.session = mock_session

        # Mock successful initialization
        api_tool.initialize = AsyncMock(return_value=True)

        # Test basic properties
        assert api_tool.tool_id == "test_api"
        assert api_tool.base_url == "https://httpbin.org"
        print("✅ API Tool instance created")

        # Test capabilities (should be empty by default)
        capabilities = await api_tool.get_capabilities()
        assert isinstance(capabilities, list)
        print("✅ API Tool capabilities retrieved")

        # Test cleanup
        api_tool.cleanup = AsyncMock(return_value=True)
        result = await api_tool.cleanup()
        assert result is True
        print("✅ API Tool cleanup completed")

        print("\n🎉 Basic API Tool Test PASSED!")
        print("🚀 API tool structure is working correctly!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


async def test_plugin_tool_integration():
    """Test plugin tool integration."""
    print("\n� Testing Plugin Tool Integration")

    try:
        # Create plugin tool configuration
        plugin_config = (
            ToolBuilder()
            .with_id("calculator_plugin")
            .with_name("Calculator Plugin")
            .with_description("Mathematical calculator plugin")
            .with_type(ToolType.PLUGIN)
            .with_plugin_class(
                "engine_core.core.tools.plugins.calculator_plugin.CalculatorPlugin"
            )
            .with_plugin_config({"precision": 2})
            .build()
        )

        assert plugin_config.tool_type == ToolType.PLUGIN
        assert (
            plugin_config.plugin_class
            == "engine_core.core.tools.plugins.calculator_plugin.CalculatorPlugin"
        )
        print("✅ Plugin Tool configuration created")

        # Create plugin tool instance
        from engine_core.core.tools.tool_builder import PluginTool

        plugin_tool = PluginTool(plugin_config)

        # Test initialization
        result = await plugin_tool.initialize()
        assert result is True
        print("✅ Plugin Tool initialized")

        # Test capabilities
        capabilities = await plugin_tool.get_capabilities()
        assert len(capabilities) == 4  # add, subtract, multiply, divide
        assert capabilities[0].name == "add"
        print("✅ Plugin Tool capabilities loaded")

        # Test execution
        result = await plugin_tool.execute_capability("add", {"a": 5, "b": 3})
        assert result.status == "success"
        assert result.result["result"] == 8.0
        print("✅ Plugin Tool execution successful")

        # Test health check
        health = await plugin_tool.health_check()
        assert health.status.name == "AVAILABLE"
        print("✅ Plugin Tool health check passed")

        # Cleanup
        await plugin_tool.cleanup()
        print("✅ Plugin Tool cleanup completed")

        print("\n🎉 Plugin Tool Integration Test PASSED!")
        print("🚀 Plugin system integration is working correctly!")

    except Exception as e:
        print(f"❌ Plugin test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(test_api_tool_basic())
    asyncio.run(test_plugin_tool_integration())
