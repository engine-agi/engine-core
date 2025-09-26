#!/usr/bin/env python3
"""
Integration test for WorkflowBuilder with agents and teams.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)


async def test_workflow_with_agents():
    """Test WorkflowBuilder with mock agents and teams."""
    print("🧪 Testing WorkflowBuilder with Agents and Teams")

    try:
        from datetime import datetime

        from engine_core.core.agents.agent_builder import (
            AgentExecutionContext,
            AgentMessage,
        )
        from engine_core.core.workflows import WorkflowBuilder

        # Create mock agent
        mock_agent = MagicMock()
        mock_agent.id = "test_agent"
        mock_agent.model = "claude-3.5-sonnet"

        # Create mock execution context
        mock_message = MagicMock(spec=AgentMessage)
        mock_message.content = "Agent completed analysis successfully"

        mock_context = MagicMock(spec=AgentExecutionContext)
        mock_context.messages = [mock_message]
        mock_context.agent_id = "test_agent"
        mock_context.task = "Analyze data"
        mock_context.state = MagicMock()
        mock_context.start_time = datetime.utcnow()

        # Mock the execute method
        mock_agent.execute = AsyncMock(return_value=mock_context)

        # Create mock team
        mock_team = MagicMock()
        mock_team.id = "test_team"

        # Build workflow with agent and team
        workflow = (
            WorkflowBuilder()
            .with_id("integration_test_workflow")
            .with_name("Integration Test Workflow")
            .add_agent_vertex(
                "data_analysis",
                mock_agent,
                "Analyze the provided data and extract insights",
                output_targets=["report_generation"],
            )
            .add_function_vertex(
                "report_generation",
                lambda: {"report": "Analysis complete"},
                dependencies=["data_analysis"],
            )
            .add_edge("data_analysis", "report_generation")
            .build()
        )

        print("✅ Workflow with agent built successfully!")
        print(f"   Workflow ID: {workflow.id}")
        print(f"   Vertices: {workflow.vertex_count}")
        print(f"   Edges: {workflow.edge_count}")

        # Validate workflow
        is_valid, errors = workflow.validate()
        print(f"   Valid: {is_valid}")
        if errors:
            print(f"   Errors: {errors}")
            return False

        print("✅ Workflow validation passed!")

        # Test workflow stats
        stats = workflow.get_stats()
        print(
            f"   Stats: {stats['vertex_count']} vertices, {stats['edge_count']} edges"
        )

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_factory_methods():
    """Test WorkflowBuilder factory methods."""
    print("\n🏭 Testing Factory Methods")

    try:
        from engine_core.core.workflows import WorkflowBuilder

        # Create mock components
        mock_agent = MagicMock()
        mock_agent.id = "agent1"

        mock_team = MagicMock()
        mock_team.id = "team1"

        async def export_func():
            return "exported"

        # Test data processing pipeline
        pipeline = WorkflowBuilder.data_processing_pipeline(
            "test_pipeline", mock_agent, mock_team, export_func
        )

        workflow = pipeline.build()
        print("✅ Data processing pipeline created!")
        print(f"   Vertices: {workflow.vertex_count}, Edges: {workflow.edge_count}")

        return True

    except Exception as e:
        print(f"❌ Factory method test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio

    success1 = asyncio.run(test_workflow_with_agents())
    success2 = asyncio.run(test_factory_methods())

    if success1 and success2:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
