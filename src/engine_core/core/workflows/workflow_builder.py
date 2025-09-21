"""
Workflow Builder - Fluent Interface for Pregel-based Workflows.

The WorkflowBuilder provides a fluent interface for creating and configuring
Engine Framework workflows with Pregel-based execution, vertex orchestration,
and graph-based computation.

Based on Engine Framework Workflow architecture with:
- Builder Pattern for fluent configuration
- Pregel computational model (supersteps, message passing)
- Vertex-based computation (agents, teams, operations)
- Edge-based data flow and dependencies
- DAG validation and cycle detection

Key Features:
- Fluent interface for workflow construction
- Multiple vertex types (agent, team, atomic operations)
- Automatic DAG validation
- Pregel-based execution with supersteps
- Message passing between vertices
- Integration with agents and teams

Usage:
    # Create workflow with agents and teams
    workflow = WorkflowBuilder() \\
        .with_id("data_processing_pipeline") \\
        .with_name("Data Processing Pipeline") \\
        .add_agent_vertex("data_ingest", agent1, "Ingest data from source") \\
        .add_team_vertex("data_process", team1, [task1, task2]) \\
        .add_function_vertex("data_export", export_function) \\
        .add_edge("data_ingest", "data_process") \\
        .add_edge("data_process", "data_export") \\
        .build()
"""

from typing import Dict, Any, List, Optional, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# Import workflow engine components
from .workflow_engine import (
    WorkflowEngine,
    VertexComputation,
    AgentVertexComputation,
    TeamVertexComputation,
    AtomicVertexComputation,
    WorkflowExecutionContext,
    WorkflowState
)

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ..agents.agent_builder import BuiltAgent
    from ..teams.team_builder import BuiltTeam


@dataclass
class WorkflowVertexConfig:
    """Configuration for a workflow vertex."""
    vertex_id: str
    computation: VertexComputation
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)


@dataclass
class WorkflowEdgeConfig:
    """Configuration for a workflow edge."""
    from_vertex: str
    to_vertex: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowBuilder:
    """
    Fluent interface builder for Engine Framework workflows.

    Provides a clean, chainable API for configuring workflows with Pregel-based
    execution, vertex orchestration, and graph-based computation.

    Usage:
        # Basic workflow with agents
        workflow = WorkflowBuilder() \\
            .with_id("analysis_workflow") \\
            .with_name("Data Analysis Workflow") \\
            .add_agent_vertex("data_loader", agent1, "Load data from database") \\
            .add_agent_vertex("analyzer", agent2, "Analyze loaded data") \\
            .add_edge("data_loader", "analyzer") \\
            .build()

        # Complex workflow with teams and functions
        workflow = WorkflowBuilder() \\
            .with_id("ml_pipeline") \\
            .with_name("ML Pipeline") \\
            .add_team_vertex("data_prep", prep_team, prep_tasks) \\
            .add_agent_vertex("model_train", ml_agent, "Train ML model") \\
            .add_function_vertex("model_eval", evaluate_model) \\
            .add_edge("data_prep", "model_train") \\
            .add_edge("model_train", "model_eval") \\
            .build()
    """

    def __init__(self):
        """Initialize builder with empty configuration."""
        self.config = {
            'id': None,
            'name': None,
            'description': None,
            'version': '1.0.0',
            'metadata': {}
        }

        self.vertices: List[WorkflowVertexConfig] = []
        self.edges: List[WorkflowEdgeConfig] = []
        self._validation_errors: List[str] = []

    # === REQUIRED CONFIGURATION ===

    def with_id(self, workflow_id: str) -> 'WorkflowBuilder':
        """Set workflow ID (required)."""
        if not workflow_id or not isinstance(workflow_id, str):
            self._validation_errors.append("Workflow ID must be a non-empty string")
            return self

        self.config['id'] = workflow_id
        return self

    def with_name(self, name: str) -> 'WorkflowBuilder':
        """Set workflow name."""
        self.config['name'] = name
        return self

    def with_description(self, description: str) -> 'WorkflowBuilder':
        """Set workflow description."""
        self.config['description'] = description
        return self

    def with_version(self, version: str) -> 'WorkflowBuilder':
        """Set workflow version."""
        self.config['version'] = version
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> 'WorkflowBuilder':
        """Set workflow metadata."""
        if not isinstance(metadata, dict):
            self._validation_errors.append("Metadata must be a dictionary")
            return self

        self.config['metadata'] = metadata
        return self

    # === VERTEX MANAGEMENT ===

    def add_agent_vertex(
        self,
        vertex_id: str,
        agent: 'BuiltAgent',
        instruction: str,
        dependencies: Optional[List[str]] = None,
        output_targets: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowBuilder':
        """Add agent-based vertex to workflow."""

        # Check for duplicate vertex IDs
        if any(v.vertex_id == vertex_id for v in self.vertices):
            self._validation_errors.append(f"Vertex ID '{vertex_id}' already exists")
            return self

        vertex_config = {
            'agent_id': agent.id,
            'instruction': instruction,
            'dependencies': dependencies or [],
            'output_targets': output_targets or [],
            **(config or {})
        }

        computation = AgentVertexComputation(agent, vertex_config)
        vertex = WorkflowVertexConfig(
            vertex_id=vertex_id,
            computation=computation,
            config=vertex_config,
            dependencies=dependencies or []
        )

        self.vertices.append(vertex)
        return self

    def add_team_vertex(
        self,
        vertex_id: str,
        team: 'BuiltTeam',
        tasks: List[Dict[str, Any]],
        dependencies: Optional[List[str]] = None,
        output_targets: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowBuilder':
        """Add team-based vertex to workflow."""

        # Check for duplicate vertex IDs
        if any(v.vertex_id == vertex_id for v in self.vertices):
            self._validation_errors.append(f"Vertex ID '{vertex_id}' already exists")
            return self

        vertex_config = {
            'team_id': team.id,
            'tasks': tasks,
            'dependencies': dependencies or [],
            'output_targets': output_targets or [],
            **(config or {})
        }

        computation = TeamVertexComputation(team, vertex_config)
        vertex = WorkflowVertexConfig(
            vertex_id=vertex_id,
            computation=computation,
            config=vertex_config,
            dependencies=dependencies or []
        )

        self.vertices.append(vertex)
        return self

    def add_function_vertex(
        self,
        vertex_id: str,
        operation: Callable,
        dependencies: Optional[List[str]] = None,
        output_targets: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowBuilder':
        """Add function-based vertex to workflow."""

        # Check for duplicate vertex IDs
        if any(v.vertex_id == vertex_id for v in self.vertices):
            self._validation_errors.append(f"Vertex ID '{vertex_id}' already exists")
            return self

        vertex_config = {
            'dependencies': dependencies or [],
            'output_targets': output_targets or [],
            **(config or {})
        }

        computation = AtomicVertexComputation(operation, vertex_config)
        vertex = WorkflowVertexConfig(
            vertex_id=vertex_id,
            computation=computation,
            config=vertex_config,
            dependencies=dependencies or []
        )

        self.vertices.append(vertex)
        return self

    # === EDGE MANAGEMENT ===

    def add_edge(
        self,
        from_vertex: str,
        to_vertex: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowBuilder':
        """Add edge between vertices."""

        # Validate vertices exist
        from_exists = any(v.vertex_id == from_vertex for v in self.vertices)
        to_exists = any(v.vertex_id == to_vertex for v in self.vertices)

        if not from_exists:
            self._validation_errors.append(f"Source vertex '{from_vertex}' does not exist")
            return self

        if not to_exists:
            self._validation_errors.append(f"Target vertex '{to_vertex}' does not exist")
            return self

        # Check for duplicate edges
        if any(e.from_vertex == from_vertex and e.to_vertex == to_vertex for e in self.edges):
            self._validation_errors.append(f"Edge from '{from_vertex}' to '{to_vertex}' already exists")
            return self

        edge = WorkflowEdgeConfig(
            from_vertex=from_vertex,
            to_vertex=to_vertex,
            metadata=metadata or {}
        )

        self.edges.append(edge)

        # Update vertex dependents
        for vertex in self.vertices:
            if vertex.vertex_id == from_vertex:
                vertex.dependents.append(to_vertex)
            elif vertex.vertex_id == to_vertex:
                vertex.dependencies.append(from_vertex)

        return self

    # === VALIDATION ===

    def validate(self) -> bool:
        """Validate workflow configuration."""
        self._validation_errors.clear()

        # Check required fields
        if not self.config.get('id'):
            self._validation_errors.append("Workflow ID is required")

        # Check for vertices
        if not self.vertices:
            self._validation_errors.append("Workflow must have at least one vertex")

        # Check for edges (optional, but warn if no edges)
        if not self.edges and len(self.vertices) > 1:
            self._validation_errors.append("Workflow with multiple vertices should have edges")

        # Validate vertex configurations
        for vertex in self.vertices:
            if not vertex.computation.validate_config(vertex.config):
                self._validation_errors.append(f"Invalid configuration for vertex '{vertex.vertex_id}'")

        # Check for cycles (would be validated by WorkflowEngine)
        # This is a basic check - full DAG validation happens in WorkflowEngine

        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        return self._validation_errors.copy()

    # === BUILD METHODS ===

    def build(self) -> 'BuiltWorkflow':
        """Build and return configured workflow."""
        if not self.validate():
            raise ValueError(f"Workflow validation failed: {', '.join(self._validation_errors)}")

        # Create workflow engine
        engine = WorkflowEngine()

        # Add vertices to engine
        for vertex in self.vertices:
            engine.add_vertex(vertex.vertex_id, vertex.computation, vertex.config)

        # Add edges to engine
        for edge in self.edges:
            engine.add_edge(edge.from_vertex, edge.to_vertex)

        # Create built workflow
        built_workflow = BuiltWorkflow(
            config=self.config.copy(),
            engine=engine
        )

        return built_workflow

    # === FACTORY METHODS ===

    @classmethod
    def data_processing_pipeline(
        cls,
        workflow_id: str,
        data_agent: 'BuiltAgent',
        processing_team: 'BuiltTeam',
        export_function: Callable
    ) -> 'WorkflowBuilder':
        """Create data processing pipeline template."""

        processing_tasks = [
            {"description": "Clean and validate data", "requirements": ["data_processing"]},
            {"description": "Transform data format", "requirements": ["data_transformation"]},
            {"description": "Aggregate results", "requirements": ["aggregation"]}
        ]

        builder = cls() \
            .with_id(workflow_id) \
            .with_name("Data Processing Pipeline") \
            .add_agent_vertex(
                "data_ingestion",
                data_agent,
                "Ingest and validate raw data from sources"
            ) \
            .add_team_vertex(
                "data_processing",
                processing_team,
                processing_tasks,
                dependencies=["data_ingestion"]
            ) \
            .add_function_vertex(
                "data_export",
                export_function,
                dependencies=["data_processing"]
            ) \
            .add_edge("data_ingestion", "data_processing") \
            .add_edge("data_processing", "data_export")

        return builder

    @classmethod
    def ml_training_pipeline(
        cls,
        workflow_id: str,
        data_prep_team: 'BuiltTeam',
        training_agent: 'BuiltAgent',
        evaluation_function: Callable
    ) -> 'WorkflowBuilder':
        """Create ML training pipeline template."""

        prep_tasks = [
            {"description": "Prepare training data", "requirements": ["data_preparation"]},
            {"description": "Feature engineering", "requirements": ["feature_engineering"]}
        ]

        builder = cls() \
            .with_id(workflow_id) \
            .with_name("ML Training Pipeline") \
            .add_team_vertex("data_preparation", data_prep_team, prep_tasks) \
            .add_agent_vertex(
                "model_training",
                training_agent,
                "Train ML model with prepared data",
                dependencies=["data_preparation"]
            ) \
            .add_function_vertex(
                "model_evaluation",
                evaluation_function,
                dependencies=["model_training"]
            ) \
            .add_edge("data_preparation", "model_training") \
            .add_edge("model_training", "model_evaluation")

        return builder

    @classmethod
    def sequential_workflow(
        cls,
        workflow_id: str,
        agents: List['BuiltAgent'],
        instructions: List[str]
    ) -> 'WorkflowBuilder':
        """Create sequential workflow with multiple agents."""

        if len(agents) != len(instructions):
            raise ValueError("Number of agents must match number of instructions")

        builder = cls() \
            .with_id(workflow_id) \
            .with_name("Sequential Workflow")

        previous_vertex = None

        for i, (agent, instruction) in enumerate(zip(agents, instructions)):
            vertex_id = f"step_{i+1}"

            builder.add_agent_vertex(
                vertex_id,
                agent,
                instruction,
                dependencies=[previous_vertex] if previous_vertex else None,
                output_targets=[f"step_{i+2}"] if i < len(agents) - 1 else None
            )

            if previous_vertex:
                builder.add_edge(previous_vertex, vertex_id)

            previous_vertex = vertex_id

        return builder


class BuiltWorkflow:
    """
    Built workflow with execution capabilities.

    Represents a fully configured workflow ready for execution using
    the Pregel computational model.
    """

    def __init__(self, config: Dict[str, Any], engine: WorkflowEngine):
        self.config = config
        self.engine = engine
        self.created_at = datetime.utcnow()

    @property
    def id(self) -> str:
        """Get workflow ID."""
        return self.config['id']

    @property
    def name(self) -> str:
        """Get workflow name (or ID if no name set)."""
        return self.config.get('name', self.config['id'])

    @property
    def state(self) -> WorkflowState:
        """Get current workflow state."""
        return self.engine.state

    @property
    def vertex_count(self) -> int:
        """Get number of vertices in workflow."""
        return len(self.engine.vertices)

    @property
    def edge_count(self) -> int:
        """Get number of edges in workflow."""
        return sum(len(neighbors) for neighbors in self.engine.edges.values())

    async def execute(
        self,
        input_data: Optional[Dict[str, Any]] = None,
        context: Optional[WorkflowExecutionContext] = None
    ) -> Dict[str, Any]:
        """Execute workflow using Pregel model."""

        if context is None:
            context = WorkflowExecutionContext(
                workflow_id=self.id,
                input_data=input_data or {}
            )

        return await self.engine.execute_workflow(context, input_data)

    async def execute_with_context(
        self,
        context: WorkflowExecutionContext
    ) -> Dict[str, Any]:
        """Execute workflow with custom execution context."""
        return await self.engine.execute_workflow(context)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate workflow graph."""
        return self.engine.validate_workflow()

    def get_execution_order(self) -> List[List[str]]:
        """Get execution order by levels."""
        return self.engine.get_execution_order()

    def get_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        return {
            'workflow_id': self.id,
            'workflow_name': self.name,
            'created_at': self.created_at.isoformat(),
            'vertex_count': self.vertex_count,
            'edge_count': self.edge_count,
            'current_state': self.state.value,
            'engine_stats': self.engine.get_workflow_stats()
        }

    def reset(self) -> None:
        """Reset workflow for new execution."""
        self.engine.reset()

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary representation."""
        return {
            'config': self.config,
            'vertex_count': self.vertex_count,
            'edge_count': self.edge_count,
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'stats': self.get_stats()
        }


# === CONVENIENCE FUNCTIONS ===

async def execute_workflow_quick(
    workflow: BuiltWorkflow,
    input_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Quick workflow execution with default context."""
    return await workflow.execute(input_data)


def validate_workflow_graph(workflow: BuiltWorkflow) -> tuple[bool, List[str]]:
    """Validate workflow graph structure."""
    return workflow.validate()


# === EXAMPLE USAGE ===

async def example_usage():
    """Example usage of WorkflowBuilder."""

    print("🧪 WorkflowBuilder Example Usage")
    print("=" * 40)

    # Note: This is a mock example - in real usage, you would have actual agents and teams

    # Create mock agent and team for demonstration
    from unittest.mock import MagicMock

    mock_agent = MagicMock()
    mock_agent.id = "demo_agent"

    mock_team = MagicMock()
    mock_team.id = "demo_team"

    # Create simple function for demonstration
    async def demo_function(input_data):
        return {"result": "Demo function executed", "input": input_data}

    try:
        # Build workflow with mock components
        workflow = WorkflowBuilder() \
            .with_id("demo_workflow") \
            .with_name("Demo Workflow") \
            .add_function_vertex("start", demo_function) \
            .build()

        print("✅ Workflow created successfully")
        print(f"   ID: {workflow.id}")
        print(f"   Name: {workflow.name}")
        print(f"   Vertices: {workflow.vertex_count}")
        print(f"   Edges: {workflow.edge_count}")

        # Validate workflow
        is_valid, errors = workflow.validate()
        print(f"   Valid: {is_valid}")
        if errors:
            print(f"   Errors: {errors}")

        # Get stats
        stats = workflow.get_stats()
        print(f"   Stats: {stats['vertex_count']} vertices, {stats['edge_count']} edges")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run example usage
    import asyncio
    asyncio.run(example_usage())