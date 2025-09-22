"""
Example Plugin for Tool System - Calculator Plugin.

This plugin demonstrates how to create custom tool plugins that can be
loaded dynamically by the Tool System.
"""

from typing import Dict, Any, List, Optional
from engine_core.core.tools.tool_builder import ToolCapability


class CalculatorPlugin:
    """A simple calculator plugin for demonstration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the calculator plugin."""
        self.config = config
        self.precision = config.get('precision', 2)

    async def initialize(self):
        """Initialize the plugin."""
        print(f"Calculator plugin initialized with precision {self.precision}")

    async def get_capabilities(self) -> List[ToolCapability]:
        """Get plugin capabilities."""
        return [
            ToolCapability(
                name="add",
                description="Add two numbers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "number"}
                    }
                }
            ),
            ToolCapability(
                name="subtract",
                description="Subtract two numbers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "number"}
                    }
                }
            ),
            ToolCapability(
                name="multiply",
                description="Multiply two numbers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "number"}
                    }
                }
            ),
            ToolCapability(
                name="divide",
                description="Divide two numbers",
                input_schema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    },
                    "required": ["a", "b"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "number"}
                    }
                }
            )
        ]

    async def add(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add two numbers."""
        a = parameters['a']
        b = parameters['b']
        result = round(a + b, self.precision)
        return {"result": result}

    async def subtract(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Subtract two numbers."""
        a = parameters['a']
        b = parameters['b']
        result = round(a - b, self.precision)
        return {"result": result}

    async def multiply(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Multiply two numbers."""
        a = parameters['a']
        b = parameters['b']
        result = round(a * b, self.precision)
        return {"result": result}

    async def divide(self, parameters: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Divide two numbers."""
        a = parameters['a']
        b = parameters['b']
        if b == 0:
            raise ValueError("Division by zero")
        result = round(a / b, self.precision)
        return {"result": result}

    async def health_check(self) -> bool:
        """Check plugin health."""
        return True

    async def cleanup(self):
        """Clean up plugin resources."""
        pass