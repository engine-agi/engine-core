#!/usr/bin/env python3
"""
Test script for WorkflowBuilder functionality.
"""

import os
import sys

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)


async def test_workflow_builder():
    """Test WorkflowBuilder basic functionality."""
    print("🧪 Testing WorkflowBuilder")

    try:
        from engine_core.core.workflows import WorkflowBuilder

        # Test basic builder
        builder = WorkflowBuilder()
        builder = builder.with_id("test_workflow").with_name("Test Workflow")

        # Add function vertex
        async def dummy_func():
            return {"result": "success"}

        builder = builder.add_function_vertex("test_vertex", dummy_func)

        # Build workflow
        workflow = builder.build()

        print("✅ WorkflowBuilder test passed!")
        print(f"   Workflow ID: {workflow.id}")
        print(f"   Vertices: {workflow.vertex_count}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio

    success = asyncio.run(test_workflow_builder())
    sys.exit(0 if success else 1)
