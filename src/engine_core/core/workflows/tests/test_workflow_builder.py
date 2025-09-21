"""
Unit Tests for WorkflowBuilder - Fluent Interface for Pregel-based Workflows.

Tests cover:
- WorkflowBuilder fluent interface and validation
- BuiltWorkflow execution capabilities
- Integration with agents and teams
- DAG validation and cycle detection
- Vertex and edge management
- Error handling and edge cases

Test Categories:
- Builder Pattern: Fluent interface, validation, configuration
- Vertex Management: Agent, team, and function vertices
- Edge Management: Dependencies, cycles, validation
- Workflow Execution: Pregel model, message passing, results
- Integration: Agent/team coordination, data flow
- Error Handling: Invalid configurations, execution failures
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, List

# Import workflow components
from src.engine_core.core.workflows.workflow_builder import (
    WorkflowBuilder,
    BuiltWorkflow,
    WorkflowVertexConfig,
    WorkflowEdgeConfig
)

# Import dependencies for testing
from src.engine_core.core.agents.agent_builder import BuiltAgent, AgentExecutionContext
from src.engine_core.core.teams.team_builder import BuiltTeam


class TestWorkflowBuilder:
    """Test WorkflowBuilder fluent interface and validation."""

    def test_builder_initialization(self):
        """Test builder initializes with empty configuration."""
        builder = WorkflowBuilder()

        assert builder.config['id'] is None
        assert builder.config['name'] is None
        assert builder.vertices == []
        assert builder.edges == []
        assert builder._validation_errors == []

    def test_with_id_required(self):
        """Test workflow ID is required."""
        builder = WorkflowBuilder()

        # Should fail without ID
        assert not builder.validate()
        assert "Workflow ID is required" in builder.get_validation_errors()

        # Should pass with ID
        builder.with_id("test_workflow")
        assert builder.config['id'] == "test_workflow"

    def test_with_name_and_description(self):
        """Test optional name and description configuration."""
        builder = WorkflowBuilder() \
            .with_id("test_workflow") \
            .with_name("Test Workflow") \
            .with_description("A test workflow")

        assert builder.config['name'] == "Test Workflow"
        assert builder.config['description'] == "A test workflow"

    def test_with_metadata(self):
        """Test metadata configuration."""
        metadata = {"version": "1.0", "author": "test"}
        builder = WorkflowBuilder() \
            .with_id("test_workflow") \
            .with_metadata(metadata)

        assert builder.config['metadata'] == metadata

    def test_invalid_metadata(self):
        """Test invalid metadata raises error."""
        builder = WorkflowBuilder() \
            .with_id("test_workflow")

        # Manually set invalid metadata to test validation
        builder.config['metadata'] = "invalid"  # Should be dict

        assert not builder.validate()
        assert "Metadata must be a dictionary" in builder.get_validation_errors()

    def test_duplicate_vertex_ids(self):
        """Test duplicate vertex IDs are rejected."""
        builder = WorkflowBuilder().with_id("test_workflow")

        # Mock function for testing
        async def dummy_func():
            return "result"

        # Add first vertex
        builder.add_function_vertex("vertex1", dummy_func)
        assert len(builder.vertices) == 1

        # Try to add duplicate vertex
        builder.add_function_vertex("vertex1", dummy_func)
        assert not builder.validate()
        assert "Vertex ID 'vertex1' already exists" in builder.get_validation_errors()

    def test_duplicate_edges(self):
        """Test duplicate edges are rejected."""
        builder = WorkflowBuilder().with_id("test_workflow")

        async def dummy_func():
            return "result"

        # Add vertices
        builder.add_function_vertex("v1", dummy_func)
        builder.add_function_vertex("v2", dummy_func)

        # Add first edge
        builder.add_edge("v1", "v2")
        assert len(builder.edges) == 1

        # Try to add duplicate edge
        builder.add_edge("v1", "v2")
        assert not builder.validate()
        assert "Edge from 'v1' to 'v2' already exists" in builder.get_validation_errors()

    def test_invalid_edge_vertices(self):
        """Test edges with non-existent vertices are rejected."""
        builder = WorkflowBuilder().with_id("test_workflow")

        async def dummy_func():
            return "result"

        # Add only one vertex
        builder.add_function_vertex("v1", dummy_func)

        # Try to add edge to non-existent vertex
        builder.add_edge("v1", "v2")
        assert not builder.validate()
        assert "Target vertex 'v2' does not exist" in builder.get_validation_errors()

    def test_empty_workflow_validation(self):
        """Test workflow with no vertices fails validation."""
        builder = WorkflowBuilder().with_id("test_workflow")

        assert not builder.validate()
        assert "Workflow must have at least one vertex" in builder.get_validation_errors()

    def test_workflow_with_multiple_vertices_no_edges_warning(self):
        """Test workflow with multiple vertices but no edges gets warning."""
        builder = WorkflowBuilder().with_id("test_workflow")

        async def dummy_func():
            return "result"

        builder.add_function_vertex("v1", dummy_func)
        builder.add_function_vertex("v2", dummy_func)

        # Should still validate but with warning
        assert builder.validate()  # Basic validation passes
        # Note: The warning about edges is not a hard failure in current implementation


class TestWorkflowBuilderVertices:
    """Test vertex management in WorkflowBuilder."""

    def test_add_function_vertex(self):
        """Test adding function-based vertices."""
        builder = WorkflowBuilder().with_id("test_workflow")

        async def process_data(data):
            return f"Processed: {data}"

        builder.add_function_vertex(
            "process_vertex",
            process_data,
            dependencies=["input"],
            output_targets=["output"],
            config={"timeout": 30}
        )

        assert len(builder.vertices) == 1
        vertex = builder.vertices[0]
        assert vertex.vertex_id == "process_vertex"
        assert vertex.dependencies == ["input"]
        assert vertex.config["timeout"] == 30

    def test_add_agent_vertex(self):
        """Test adding agent-based vertices."""
        builder = WorkflowBuilder().with_id("test_workflow")

        # Mock agent
        mock_agent = MagicMock(spec=BuiltAgent)
        mock_agent.id = "test_agent"

        builder.add_agent_vertex(
            "agent_vertex",
            mock_agent,
            "Analyze the data and provide insights",
            dependencies=["data_loader"],
            output_targets=["analyzer"],
            config={"model": "claude-3.5-sonnet"}
        )

        assert len(builder.vertices) == 1
        vertex = builder.vertices[0]
        assert vertex.vertex_id == "agent_vertex"
        assert vertex.config["agent_id"] == "test_agent"
        assert vertex.config["instruction"] == "Analyze the data and provide insights"

    def test_add_team_vertex(self):
        """Test adding team-based vertices."""
        builder = WorkflowBuilder().with_id("test_workflow")

        # Mock team
        mock_team = MagicMock(spec=BuiltTeam)
        mock_team.id = "test_team"

        tasks = [
            {"description": "Validate data", "requirements": ["validation"]},
            {"description": "Transform data", "requirements": ["transformation"]}
        ]

        builder.add_team_vertex(
            "team_vertex",
            mock_team,
            tasks,
            dependencies=["input"],
            output_targets=["processed"],
            config={"coordination": "parallel"}
        )

        assert len(builder.vertices) == 1
        vertex = builder.vertices[0]
        assert vertex.vertex_id == "team_vertex"
        assert vertex.config["team_id"] == "test_team"
        assert vertex.config["tasks"] == tasks


class TestWorkflowBuilderEdges:
    """Test edge management in WorkflowBuilder."""

    def test_add_edge_updates_dependencies(self):
        """Test adding edges updates vertex dependencies."""
        builder = WorkflowBuilder().with_id("test_workflow")

        async def dummy_func():
            return "result"

        # Add vertices
        builder.add_function_vertex("v1", dummy_func)
        builder.add_function_vertex("v2", dummy_func)
        builder.add_function_vertex("v3", dummy_func)

        # Add edges
        builder.add_edge("v1", "v2")
        builder.add_edge("v2", "v3")

        # Check dependencies
        v1 = next(v for v in builder.vertices if v.vertex_id == "v1")
        v2 = next(v for v in builder.vertices if v.vertex_id == "v2")
        v3 = next(v for v in builder.vertices if v.vertex_id == "v3")

        assert v1.dependents == ["v2"]
        assert v2.dependencies == ["v1"]
        assert v2.dependents == ["v3"]
        assert v3.dependencies == ["v2"]

    def test_edge_metadata(self):
        """Test edge metadata is stored correctly."""
        builder = WorkflowBuilder().with_id("test_workflow")

        async def dummy_func():
            return "result"

        builder.add_function_vertex("v1", dummy_func)
        builder.add_function_vertex("v2", dummy_func)

        metadata = {"data_type": "json", "priority": "high"}
        builder.add_edge("v1", "v2", metadata=metadata)

        assert len(builder.edges) == 1
        edge = builder.edges[0]
        assert edge.metadata == metadata


class TestBuiltWorkflow:
    """Test BuiltWorkflow execution and capabilities."""

    @pytest.fixture
    def mock_workflow_engine(self):
        """Create mock workflow engine."""
        engine = MagicMock()
        engine.state = MagicMock()
        engine.state.value = "READY"
        engine.vertices = {"v1": MagicMock(), "v2": MagicMock()}
        engine.edges = {"v1": ["v2"]}
        engine.get_workflow_stats.return_value = {
            "total_vertices": 2,
            "total_edges": 1,
            "execution_time": 0.0
        }
        return engine

    @pytest.fixture
    def built_workflow(self, mock_workflow_engine):
        """Create built workflow for testing."""
        config = {
            'id': 'test_workflow',
            'name': 'Test Workflow',
            'description': 'A test workflow',
            'version': '1.0.0',
            'metadata': {}
        }
        return BuiltWorkflow(config, mock_workflow_engine)

    def test_built_workflow_properties(self, built_workflow):
        """Test built workflow properties."""
        assert built_workflow.id == "test_workflow"
        assert built_workflow.name == "Test Workflow"
        assert built_workflow.vertex_count == 2
        assert built_workflow.edge_count == 1

    @pytest.mark.asyncio
    async def test_execute_workflow(self, built_workflow, mock_workflow_engine):
        """Test workflow execution."""
        # Mock execution result
        mock_workflow_engine.execute_workflow.return_value = {
            "status": "completed",
            "results": {"v1": "result1", "v2": "result2"}
        }

        result = await built_workflow.execute()

        assert result["status"] == "completed"
        assert result["results"]["v1"] == "result1"
        mock_workflow_engine.execute_workflow.assert_called_once()

    def test_workflow_stats(self, built_workflow):
        """Test workflow statistics."""
        stats = built_workflow.get_stats()

        assert stats["workflow_id"] == "test_workflow"
        assert stats["vertex_count"] == 2
        assert stats["edge_count"] == 1
        assert "created_at" in stats

    def test_workflow_validation(self, built_workflow, mock_workflow_engine):
        """Test workflow validation."""
        mock_workflow_engine.validate_workflow.return_value = (True, [])

        is_valid, errors = built_workflow.validate()
        assert is_valid
        assert errors == []

    def test_to_dict(self, built_workflow):
        """Test workflow serialization."""
        data = built_workflow.to_dict()

        assert data["config"]["id"] == "test_workflow"
        assert data["vertex_count"] == 2
        assert data["edge_count"] == 1
        assert "stats" in data


class TestWorkflowBuilderFactoryMethods:
    """Test WorkflowBuilder factory methods and templates."""

    def test_data_processing_pipeline_template(self):
        """Test data processing pipeline template."""
        # Mock agents and team
        mock_agent1 = MagicMock(spec=BuiltAgent)
        mock_agent1.id = "data_agent"

        mock_team = MagicMock(spec=BuiltTeam)
        mock_team.id = "processing_team"

        async def export_func():
            return "exported"

        builder = WorkflowBuilder.data_processing_pipeline(
            "data_pipeline",
            mock_agent1,
            mock_team,
            export_func
        )

        # Should have 3 vertices and 2 edges
        assert len(builder.vertices) == 3
        assert len(builder.edges) == 2

        # Check vertex IDs
        vertex_ids = [v.vertex_id for v in builder.vertices]
        assert "data_ingestion" in vertex_ids
        assert "data_processing" in vertex_ids
        assert "data_export" in vertex_ids

    def test_ml_training_pipeline_template(self):
        """Test ML training pipeline template."""
        mock_team = MagicMock(spec=BuiltTeam)
        mock_team.id = "prep_team"

        mock_agent = MagicMock(spec=BuiltAgent)
        mock_agent.id = "training_agent"

        async def eval_func():
            return {"accuracy": 0.95}

        builder = WorkflowBuilder.ml_training_pipeline(
            "ml_pipeline",
            mock_team,
            mock_agent,
            eval_func
        )

        assert len(builder.vertices) == 3
        assert len(builder.edges) == 2

    def test_sequential_workflow_template(self):
        """Test sequential workflow template."""
        # Create properly typed mock agents
        mock_agents = []
        for i in range(3):
            agent = MagicMock()
            agent.id = f"agent{i+1}"
            mock_agents.append(agent)

        instructions = [
            "Step 1: Analyze data",
            "Step 2: Process results",
            "Step 3: Generate report"
        ]

        # Use type ignore for this test since we're using mocks
        builder = WorkflowBuilder.sequential_workflow(  # type: ignore
            "sequential_workflow",
            mock_agents,
            instructions
        )

        assert len(builder.vertices) == 3
        assert len(builder.edges) == 2

        # Check sequential dependencies
        edges = [(e.from_vertex, e.to_vertex) for e in builder.edges]
        assert ("step_1", "step_2") in edges
        assert ("step_2", "step_3") in edges


class TestWorkflowBuilderIntegration:
    """Integration tests for WorkflowBuilder with real components."""

    @pytest.mark.asyncio
    async def test_build_and_execute_simple_workflow(self):
        """Test building and executing a simple workflow."""
        # Create mock agent
        mock_agent = MagicMock(spec=BuiltAgent)
        mock_agent.id = "test_agent"
        mock_agent.model = "claude-3.5-sonnet"

        # Mock agent execution
        mock_context = MagicMock(spec=AgentExecutionContext)
        mock_context.messages = [MagicMock(content="Agent result")]
        mock_agent.execute = AsyncMock(return_value=mock_context)

        # Build workflow
        builder = WorkflowBuilder() \
            .with_id("simple_workflow") \
            .with_name("Simple Test Workflow") \
            .add_agent_vertex("agent_task", mock_agent, "Execute test task")

        workflow = builder.build()

        # Execute workflow
        result = await workflow.execute()

        # Verify execution
        mock_agent.execute.assert_called_once()
        assert isinstance(result, dict)

    def test_workflow_builder_error_handling(self):
        """Test error handling in workflow building."""
        builder = WorkflowBuilder()

        # Test building without required ID
        with pytest.raises(ValueError, match="Workflow validation failed"):
            builder.build()

        # Test with invalid configuration
        builder.with_id("test")
        # Manually set invalid metadata to test validation
        builder.config['metadata'] = "invalid"
        with pytest.raises(ValueError, match="Workflow validation failed"):
            builder.build()


# === Test Utilities ===

def create_mock_agent(agent_id: str, model: str = "claude-3.5-sonnet") -> BuiltAgent:
    """Create mock agent for testing."""
    agent = MagicMock(spec=BuiltAgent)
    agent.id = agent_id
    agent.model = model
    return agent


def create_mock_team(team_id: str) -> BuiltTeam:
    """Create mock team for testing."""
    team = MagicMock(spec=BuiltTeam)
    team.id = team_id
    return team


async def dummy_processing_function(data: Dict[str, Any]) -> Dict[str, Any]:
    """Dummy processing function for testing."""
    return {"processed": True, "input": data}


# === Run Tests ===

if __name__ == "__main__":
    # Run basic validation tests
    print("🧪 Running WorkflowBuilder Tests")
    print("=" * 40)

    try:
        # Test builder initialization
        builder = WorkflowBuilder()
        print("✅ Builder initialization: PASSED")

        # Test required fields
        assert not builder.validate()
        print("✅ Validation without ID: PASSED")

        # Test with ID
        builder.with_id("test_workflow")
        assert builder.config['id'] == "test_workflow"
        print("✅ ID configuration: PASSED")

        # Test function vertex
        async def test_func():
            return "test"

        builder.add_function_vertex("test_vertex", test_func)
        assert len(builder.vertices) == 1
        print("✅ Function vertex addition: PASSED")

        # Test build
        workflow = builder.build()
        assert workflow.id == "test_workflow"
        print("✅ Workflow build: PASSED")

        print("\n🎉 All basic tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise