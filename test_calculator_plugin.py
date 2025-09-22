"""
Test Calculator Plugin - Demonstrates plugin system functionality.
"""

import asyncio
import sys
import os

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from engine_core.core.tools.plugins.calculator_plugin import CalculatorPlugin


async def test_calculator_plugin():
    """Test the calculator plugin functionality."""
    print("🧮 Testing Calculator Plugin")

    try:
        # Initialize plugin
        config = {"precision": 2}
        plugin = CalculatorPlugin(config)
        await plugin.initialize()

        # Test capabilities
        capabilities = await plugin.get_capabilities()
        assert len(capabilities) == 4
        assert capabilities[0].name == "add"
        print("✅ Plugin capabilities loaded")

        # Test add operation
        result = await plugin.add({"a": 5, "b": 3})
        assert result["result"] == 8.0
        print("✅ Add operation: 5 + 3 = 8")

        # Test subtract operation
        result = await plugin.subtract({"a": 10, "b": 4})
        assert result["result"] == 6.0
        print("✅ Subtract operation: 10 - 4 = 6")

        # Test multiply operation
        result = await plugin.multiply({"a": 6, "b": 7})
        assert result["result"] == 42.0
        print("✅ Multiply operation: 6 * 7 = 42")

        # Test divide operation
        result = await plugin.divide({"a": 15, "b": 3})
        assert result["result"] == 5.0
        print("✅ Divide operation: 15 / 3 = 5")

        # Test precision
        result = await plugin.add({"a": 1.234, "b": 2.567})
        assert result["result"] == 3.8  # Rounded to 2 decimal places
        print("✅ Precision handling: 1.234 + 2.567 = 3.8")

        # Test health check
        health = await plugin.health_check()
        assert health is True
        print("✅ Health check passed")

        # Test cleanup
        await plugin.cleanup()
        print("✅ Cleanup completed")

        print("\n🎉 Calculator Plugin Test PASSED!")
        print("🚀 Plugin system is working correctly!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(test_calculator_plugin())