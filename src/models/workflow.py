"""
Workflow models for Engine Framework.

Implements Pregel-based workflow system with vertices and edges.
Workflows define computational graphs where:
- Vertices represent computation units (assigned to agents)
- Edges represent data flow and dependencies
- Supersteps coordinate parallel execution
- Message passing enables communication between vertices

Based on Engine Framework data model specification and Pregel algorithm.
"""

from typing import Dict, Any, List, Optional, Union, Set, TYPE_CHECKING
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship, validates, backref
from datetime import datetime
import re
import uuid
import networkx as nx  # For graph validation
from enum import Enum

from .base import BaseModel, StringIdentifierMixin, ConfigurationMixin, ValidationMixin, TimestampMixin

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .project import Project
    from .agent import Agent
    from .team import Team


class WorkflowExecutionMode(str, Enum):
    """Workflow execution modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel" 
    CONDITIONAL = "conditional"
    HYBRID = "hybrid"


class WorkflowStatus(str, Enum):
    """Workflow status values."""
    DRAFT = "draft"
    VALIDATED = "validated"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkflowVertexType(str, Enum):
    """Workflow vertex types."""
    ANALYSIS = "analysis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    COORDINATION = "coordination"
    CUSTOM = "custom"


class WorkflowVertexStatus(str, Enum):
    """Workflow vertex execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Workflow(BaseModel, StringIdentifierMixin, ConfigurationMixin, ValidationMixin, TimestampMixin):
    """
    Workflow entity - defines computational graph for agent execution.
    
    Workflows implement the Pregel computational model:
    - Vertices (computation units) execute in supersteps
    - Messages pass between vertices along edges
    - Synchronization barriers coordinate parallel execution
    - Graph algorithms determine execution order and dependencies
    
    Key features:
    - DAG validation ensures acyclic execution flow
    - Multiple execution modes (sequential, parallel, conditional)
    - Vertex-to-agent assignment for distributed computation
    - Real-time execution monitoring and state management
    """
    
    __tablename__ = "workflows"

    # Basic workflow information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable workflow name"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Workflow purpose, steps, and expected outcomes"
    )
    
    # Workflow classification
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Workflow category (e.g., 'development', 'analysis', 'coordination')"
    )
    
    version = Column(
        String(50),
        nullable=False,
        default="1.0",
        comment="Workflow version for change management"
    )
    
    # Workflow execution configuration
    execution_mode = Column(
        String(50),
        nullable=False,
        default=WorkflowExecutionMode.SEQUENTIAL.value,
        index=True,
        comment="Workflow execution mode"
    )
    
    max_parallel_vertices = Column(
        Integer,
        nullable=True,
        default=5,
        comment="Maximum vertices that can execute in parallel"
    )
    
    timeout = Column(
        Integer,
        nullable=True,
        comment="Workflow timeout in seconds"
    )
    
    # Workflow status and lifecycle
    status = Column(
        String(50),
        nullable=False,
        default=WorkflowStatus.DRAFT.value,
        index=True,
        comment="Workflow lifecycle status"
    )
    
    # Project and team associations
    project_id = Column(
        String(255),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Project this workflow belongs to"
    )
    
    team_id = Column(
        String(255),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Team responsible for workflow execution"
    )
    
    # Workflow validation and graph properties
    is_dag = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether workflow forms a valid DAG (Directed Acyclic Graph)"
    )
    
    vertex_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of vertices in workflow"
    )
    
    edge_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of edges in workflow"
    )
    
    # Execution statistics
    total_executions = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of workflow executions"
    )
    
    successful_executions = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of successful executions"
    )
    
    average_execution_time = Column(
        Float,
        nullable=True,
        comment="Average execution time in seconds"
    )
    
    # Graph metadata and analysis
    graph_metrics = Column(
        JSONB,
        nullable=True,
        comment="Graph analysis metrics (depth, width, complexity)"
    )

    # Workflow-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    workflow_metadata = Column(
        JSONB,
        nullable=True,
        comment="Workflow-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None
    
    # === RELATIONSHIPS ===
    
    # One-to-many relationships with vertices and edges
    vertices = relationship("WorkflowVertex", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    
    # Foreign key relationships
    project = relationship("Project", back_populates="workflows")
    team = relationship("Team", back_populates="workflows")

    def __init__(self, **kwargs):
        """Initialize workflow with validation."""
        # Set defaults
        if 'execution_mode' not in kwargs:
            kwargs['execution_mode'] = WorkflowExecutionMode.SEQUENTIAL.value
        if 'status' not in kwargs:
            kwargs['status'] = WorkflowStatus.DRAFT.value
        if 'version' not in kwargs:
            kwargs['version'] = '1.0'
        if 'max_parallel_vertices' not in kwargs:
            kwargs['max_parallel_vertices'] = 5
            
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Workflow(id='{self.id}', name='{self.name}', vertices={self.vertex_count})>"

    # === VALIDATION METHODS ===

    @validates('id')
    def validate_id(self, key: str, value: str) -> str:
        """Validate workflow ID format."""
        if not value:
            raise ValueError("Workflow ID is required")
        
        # Must be alphanumeric with underscores/hyphens, 2-100 characters
        if not re.match(r'^[a-zA-Z0-9_-]{2,100}$', value):
            raise ValueError(
                "Workflow ID must be 2-100 characters, containing only "
                "letters, numbers, underscores, and hyphens"
            )
        
        return value.lower()

    @validates('name')
    def validate_name(self, key: str, value: str) -> str:
        """Validate workflow name."""
        if not value or not value.strip():
            raise ValueError("Workflow name is required")
        
        if len(value.strip()) > 255:
            raise ValueError("Workflow name cannot exceed 255 characters")
        
        return value.strip()

    @validates('execution_mode')
    def validate_execution_mode(self, key: str, value: str) -> str:
        """Validate execution mode."""
        valid_modes = [mode.value for mode in WorkflowExecutionMode]
        
        if value not in valid_modes:
            raise ValueError(f"Execution mode must be one of: {', '.join(valid_modes)}")
        
        return value

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate workflow status."""
        valid_statuses = [status.value for status in WorkflowStatus]
        
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return value

    @validates('max_parallel_vertices')
    def validate_max_parallel_vertices(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate maximum parallel vertices."""
        if value is not None:
            if not isinstance(value, int) or value < 1 or value > 100:
                raise ValueError("Max parallel vertices must be an integer between 1 and 100")
        return value

    @validates('timeout')
    def validate_timeout(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate workflow timeout."""
        if value is not None:
            if not isinstance(value, int) or value < 1:
                raise ValueError("Timeout must be a positive integer (seconds)")
        return value

    # === GRAPH OPERATIONS AND VALIDATION ===

    def validate_dag(self) -> tuple[bool, List[str]]:
        """Validate that workflow forms a valid DAG."""
        if not self.vertices or len(self.vertices) == 0:
            return True, []  # Empty graph is valid DAG
        
        errors = []
        
        # Create NetworkX graph for validation
        G = nx.DiGraph()
        
        # Add vertices
        for vertex in self.vertices:
            G.add_node(vertex.id)
        
        # Add edges
        for edge in self.edges:
            G.add_edge(edge.source_id, edge.target_id)
        
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                errors.append(f"Workflow contains cycles: {cycles}")
                return False, errors
        except nx.NetworkXError as e:
            errors.append(f"Graph validation error: {str(e)}")
            return False, errors
        
        # Additional validations
        
        # Check for isolated vertices (except single-vertex workflows)
        if len(self.vertices) > 1:
            isolated = []
            for v in G.nodes():
                degree = G.degree(v)
                if degree == 0:
                    isolated.append(v)
            if isolated:
                errors.append(f"Isolated vertices found: {isolated}")
        
        # Check for vertices with no outgoing edges (should have at least one sink)
        sinks = [v for v in G.nodes() if G.out_degree(v) == 0]
        if not sinks:
            errors.append("Workflow must have at least one sink vertex (no outgoing edges)")
        
        # Check for vertices with no incoming edges (should have at least one source)
        sources = [v for v in G.nodes() if G.in_degree(v) == 0]
        if not sources:
            errors.append("Workflow must have at least one source vertex (no incoming edges)")
        
        return len(errors) == 0, errors

    def update_graph_metrics(self) -> None:
        """Update graph analysis metrics."""
        if not self.vertices:
            self.graph_metrics = {
                'depth': 0,
                'width': 0,
                'complexity': 0,
                'critical_path_length': 0,
                'parallelism_potential': 0
            }
            return
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
        for vertex in self.vertices:
            G.add_node(vertex.id, weight=vertex.estimated_duration or 1)
        
        for edge in self.edges:
            G.add_edge(edge.source_id, edge.target_id)
        
        # Calculate metrics
        try:
            # Graph depth (longest path)
            depth = nx.dag_longest_path_length(G) if nx.is_directed_acyclic_graph(G) else 0
            
            # Graph width (maximum vertices at same level)
            levels = {}
            if nx.is_directed_acyclic_graph(G):
                for node in nx.topological_sort(G):
                    level = max([levels.get(pred, -1) for pred in G.predecessors(node)], default=-1) + 1
                    levels[node] = level
                
                level_counts = {}
                for level in levels.values():
                    level_counts[level] = level_counts.get(level, 0) + 1
                
                width = max(level_counts.values()) if level_counts else 1
            else:
                width = len(self.vertices)
            
            # Complexity (edges/vertices ratio)
            complexity = len(self.edges) / len(self.vertices) if len(self.vertices) > 0 else 0
            
            # Critical path length (weighted longest path)
            critical_path_length = 0
            if nx.is_directed_acyclic_graph(G):
                try:
                    path = nx.dag_longest_path(G, weight='weight')
                    # Safely calculate path length
                    if isinstance(path, (list, tuple)) and len(path) > 0:
                        weights = []
                        for node in path:
                            try:
                                node_data = G.nodes[node]
                                weight = node_data.get('weight', 1)
                                if isinstance(weight, (int, float)):
                                    weights.append(weight)
                            except (KeyError, TypeError):
                                weights.append(1)  # Default weight
                        critical_path_length = sum(weights) if weights else depth
                    else:
                        critical_path_length = depth
                except (nx.NetworkXError, TypeError, AttributeError):
                    critical_path_length = depth
            
            # Parallelism potential (1 - depth/vertices)
            parallelism_potential = 1 - (depth / len(self.vertices)) if len(self.vertices) > 0 else 0
            
            self.graph_metrics = {
                'depth': depth,
                'width': width,
                'complexity': round(complexity, 2),
                'critical_path_length': critical_path_length,
                'parallelism_potential': round(parallelism_potential, 2),
                'is_dag': nx.is_directed_acyclic_graph(G),
                'node_count': G.number_of_nodes(),
                'edge_count': G.number_of_edges(),
                'calculated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.graph_metrics = {
                'error': f"Failed to calculate metrics: {str(e)}",
                'calculated_at': datetime.utcnow().isoformat()
            }

    def get_execution_order(self) -> List[List[str]]:
        """Get execution order as list of supersteps (parallel groups)."""
        if not self.vertices:
            return []
        
        execution_mode = getattr(self, 'execution_mode', WorkflowExecutionMode.SEQUENTIAL.value)
        
        if execution_mode == WorkflowExecutionMode.SEQUENTIAL.value:
            # Sequential execution - topological sort
            G = nx.DiGraph()
            for vertex in self.vertices:
                G.add_node(vertex.id)
            for edge in self.edges:
                G.add_edge(edge.source_id, edge.target_id)
            
            if nx.is_directed_acyclic_graph(G):
                return [[node] for node in nx.topological_sort(G)]
            else:
                return [[vertex.id] for vertex in self.vertices]  # Fallback
        
        elif execution_mode == WorkflowExecutionMode.PARALLEL.value:
            # Parallel execution - group by dependency levels
            G = nx.DiGraph()
            for vertex in self.vertices:
                G.add_node(vertex.id)
            for edge in self.edges:
                G.add_edge(edge.source_id, edge.target_id)
            
            if not nx.is_directed_acyclic_graph(G):
                return [[vertex.id] for vertex in self.vertices]  # Fallback
            
            # Group vertices by level (distance from sources)
            levels = {}
            for node in nx.topological_sort(G):
                level = max([levels.get(pred, -1) for pred in G.predecessors(node)], default=-1) + 1
                levels[node] = level
            
            # Group by level for parallel execution
            level_groups = {}
            for node, level in levels.items():
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(node)
            
            return [level_groups[level] for level in sorted(level_groups.keys())]
        
        else:
            # Conditional/hybrid - default to sequential
            return self.get_execution_order()  # Recursively call with sequential logic

    # === WORKFLOW MANAGEMENT ===

    def add_vertex(self, vertex_data: Dict[str, Any]) -> "WorkflowVertex":
        """Add vertex to workflow."""
        vertex = WorkflowVertex(workflow_id=self.id, **vertex_data)
        # In real implementation, this would add to session
        # self.vertices.append(vertex)
        self.vertex_count += 1
        return vertex

    def add_edge(self, source_id: str, target_id: str, **edge_data) -> "WorkflowEdge":
        """Add edge to workflow."""
        edge = WorkflowEdge(
            workflow_id=self.id,
            source_id=source_id,
            target_id=target_id,
            **edge_data
        )
        # In real implementation, this would add to session
        # self.edges.append(edge)
        self.edge_count += 1
        return edge

    def update_execution_stats(self, execution_time: float, success: bool = True) -> None:
        """Update workflow execution statistics."""
        self.total_executions += 1
        
        if success:
            self.successful_executions += 1
        
        # Update average execution time
        if self.average_execution_time is None:
            self.average_execution_time = execution_time
        else:
            total_time = self.average_execution_time * (self.total_executions - 1) + execution_time
            self.average_execution_time = total_time / self.total_executions
        
        self.last_executed_at = datetime.utcnow()

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get workflow summary information."""
        is_valid_dag, errors = self.validate_dag()
        
        total_executions = getattr(self, 'total_executions', 0)
        successful_executions = getattr(self, 'successful_executions', 0)
        created_at = getattr(self, 'created_at', None)
        updated_at = getattr(self, 'updated_at', None)
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'execution_mode': self.execution_mode,
            'vertex_count': self.vertex_count,
            'edge_count': self.edge_count,
            'is_valid_dag': is_valid_dag,
            'validation_errors': errors,
            'graph_metrics': self.graph_metrics,
            'total_executions': total_executions,
            'success_rate': (successful_executions / total_executions 
                           if total_executions > 0 else None),
            'average_execution_time': self.average_execution_time,
            'created_at': created_at.isoformat() if created_at else None,
            'updated_at': updated_at.isoformat() if updated_at else None
        }


class WorkflowVertex(BaseModel, StringIdentifierMixin, ConfigurationMixin):
    """
    Workflow vertex - represents a computation unit in the workflow graph.
    
    Vertices are assigned to agents and execute specific tasks within
    the workflow. They receive messages from predecessor vertices,
    perform computation, and send results to successor vertices.
    """
    
    __tablename__ = "workflow_vertices"

    # Basic vertex information
    name = Column(
        String(255),
        nullable=False,
        comment="Human-readable vertex name"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Vertex purpose and functionality"
    )
    
    # Vertex type and classification
    type = Column(
        String(50),
        nullable=False,
        default=WorkflowVertexType.CUSTOM.value,
        comment="Vertex type defining its role in workflow"
    )
    
    # Workflow association
    workflow_id = Column(
        String(255),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Workflow this vertex belongs to"
    )
    
    # Agent assignment
    agent_id = Column(
        String(255),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Agent assigned to execute this vertex"
    )
    
    # Execution configuration
    estimated_duration = Column(
        Integer,
        nullable=True,
        comment="Estimated execution duration in seconds"
    )
    
    timeout = Column(
        Integer,
        nullable=True,
        comment="Vertex timeout in seconds"
    )
    
    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of retry attempts if execution fails"
    )
    
    # Vertex execution state
    status = Column(
        String(50),
        nullable=False,
        default=WorkflowVertexStatus.PENDING.value,
        comment="Current vertex execution status"
    )
    
    # Input/output configuration
    input_channels = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Input channels this vertex accepts"
    )
    
    output_channels = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Output channels this vertex produces"
    )
    
    # Pregel algorithm support
    superstep = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Current superstep in Pregel execution"
    )
    
    messages = Column(
        JSONB,
        nullable=True,
        comment="Messages received/sent in current superstep"
    )
    
    # Execution results and metadata
    execution_data = Column(
        JSONB,
        nullable=True,
        comment="Execution results and intermediate data"
    )

    # Vertex-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    vertex_metadata = Column(
        JSONB,
        nullable=True,
        comment="Vertex-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None
    
    # === RELATIONSHIPS ===
    
    workflow = relationship("Workflow", back_populates="vertices")
    agent = relationship("Agent", back_populates="vertices")

    def __repr__(self) -> str:
        return f"<WorkflowVertex(id='{self.id}', workflow='{self.workflow_id}', agent='{self.agent_id}')>"

    # === VALIDATION ===

    @validates('type')
    def validate_type(self, key: str, value: str) -> str:
        """Validate vertex type."""
        valid_types = [vtype.value for vtype in WorkflowVertexType]
        
        if value not in valid_types:
            raise ValueError(f"Vertex type must be one of: {', '.join(valid_types)}")
        
        return value

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate vertex status."""
        valid_statuses = [status.value for status in WorkflowVertexStatus]
        
        if value not in valid_statuses:
            raise ValueError(f"Vertex status must be one of: {', '.join(valid_statuses)}")
        
        return value


class WorkflowEdge(BaseModel, ConfigurationMixin):
    """
    Workflow edge - represents data flow and dependencies between vertices.
    
    Edges define the execution order and data passing between vertices
    in the workflow graph. They support conditional execution and
    message filtering.
    """
    
    __tablename__ = "workflow_edges"

    # Edge endpoints
    source_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Source vertex ID"
    )
    
    target_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Target vertex ID"
    )
    
    # Workflow association
    workflow_id = Column(
        String(255),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Workflow this edge belongs to"
    )
    
    # Edge properties
    condition = Column(
        String(500),
        nullable=True,
        comment="Conditional expression for edge traversal"
    )
    
    weight = Column(
        Float,
        default=1.0,
        nullable=False,
        comment="Edge weight for graph algorithms"
    )
    
    # Data transformation
    data_transformation = Column(
        JSONB,
        nullable=True,
        comment="Data transformation rules for messages passing through edge"
    )
    
    # Edge metadata
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether edge is active in workflow execution"
    )

    # Edge-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    edge_metadata = Column(
        JSONB,
        nullable=True,
        comment="Edge-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    # === RELATIONSHIPS ===
    
    workflow = relationship("Workflow", back_populates="edges")

    def __repr__(self) -> str:
        return f"<WorkflowEdge(source='{self.source_id}', target='{self.target_id}', workflow='{self.workflow_id}')>"


# Database indexes for performance
Index('idx_workflow_status_mode', Workflow.status, Workflow.execution_mode)
Index('idx_workflow_project_status', Workflow.project_id, Workflow.status)
Index('idx_workflow_team_status', Workflow.team_id, Workflow.status)

Index('idx_vertex_workflow_status', WorkflowVertex.workflow_id, WorkflowVertex.status)
Index('idx_vertex_agent_status', WorkflowVertex.agent_id, WorkflowVertex.status)
Index('idx_vertex_superstep', WorkflowVertex.workflow_id, WorkflowVertex.superstep)

Index('idx_edge_workflow_source', WorkflowEdge.workflow_id, WorkflowEdge.source_id)
Index('idx_edge_workflow_target', WorkflowEdge.workflow_id, WorkflowEdge.target_id)

# Unique constraints
UniqueConstraint(
    WorkflowVertex.workflow_id, WorkflowVertex.id,
    name='uq_vertex_workflow_id'
)

UniqueConstraint(
    WorkflowEdge.workflow_id, WorkflowEdge.source_id, WorkflowEdge.target_id,
    name='uq_edge_workflow_source_target'
)

# Database constraints
CheckConstraint(
    Workflow.execution_mode.in_([mode.value for mode in WorkflowExecutionMode]),
    name='ck_workflow_execution_mode_valid'
)

CheckConstraint(
    Workflow.status.in_([status.value for status in WorkflowStatus]),
    name='ck_workflow_status_valid'
)

CheckConstraint(
    WorkflowVertex.type.in_([vtype.value for vtype in WorkflowVertexType]),
    name='ck_vertex_type_valid'
)

CheckConstraint(
    WorkflowVertex.status.in_([status.value for status in WorkflowVertexStatus]),
    name='ck_vertex_status_valid'
)

CheckConstraint(
    Workflow.successful_executions <= Workflow.total_executions,
    name='ck_workflow_executions_consistent'
)

CheckConstraint(
    Workflow.vertex_count >= 0,
    name='ck_workflow_vertex_count_non_negative'
)

CheckConstraint(
    Workflow.edge_count >= 0,
    name='ck_workflow_edge_count_non_negative'
)


class WorkflowExecutionStatus(str, Enum):
    """Workflow execution status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkflowExecution(BaseModel, StringIdentifierMixin, TimestampMixin):
    """
    Workflow execution record - tracks historical workflow runs.

    Stores persistent execution history including status, timing,
    results, and metadata for auditing and analytics purposes.
    """

    __tablename__ = "workflow_executions"

    # Execution identification
    execution_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique execution identifier"
    )

    # Workflow association
    workflow_id = Column(
        String(255),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Workflow that was executed"
    )

    # Execution metadata
    workflow_version = Column(
        String(50),
        nullable=True,
        comment="Version of workflow at execution time"
    )

    workflow_name = Column(
        String(255),
        nullable=True,
        comment="Name of workflow at execution time"
    )

    # Execution status and lifecycle
    status = Column(
        String(50),
        nullable=False,
        default=WorkflowExecutionStatus.PENDING.value,
        index=True,
        comment="Current execution status"
    )

    # Timing information
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When execution started"
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When execution completed"
    )

    duration_seconds = Column(
        Float,
        nullable=True,
        comment="Total execution duration in seconds"
    )

    # Execution results
    success = Column(
        Boolean,
        nullable=True,
        comment="Whether execution was successful"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if execution failed"
    )

    error_details = Column(
        JSONB,
        nullable=True,
        comment="Detailed error information"
    )

    # Execution context and inputs
    input_data = Column(
        JSONB,
        nullable=True,
        comment="Input data provided to workflow"
    )

    output_data = Column(
        JSONB,
        nullable=True,
        comment="Output data produced by workflow"
    )

    execution_context = Column(
        JSONB,
        nullable=True,
        comment="Execution context and environment details"
    )

    # Vertex execution tracking
    vertex_results = Column(
        JSONB,
        nullable=True,
        comment="Results from individual vertex executions"
    )

    vertex_execution_order = Column(
        ARRAY(String(255)),
        nullable=True,
        comment="Order in which vertices were executed"
    )

    # Performance metrics
    total_vertices = Column(
        Integer,
        nullable=True,
        comment="Total number of vertices executed"
    )

    completed_vertices = Column(
        Integer,
        nullable=True,
        comment="Number of vertices that completed successfully"
    )

    failed_vertices = Column(
        Integer,
        nullable=True,
        comment="Number of vertices that failed"
    )

    # Resource usage
    resource_usage = Column(
        JSONB,
        nullable=True,
        comment="Resource usage statistics (CPU, memory, etc.)"
    )

    # User and project context
    user_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="User who initiated the execution"
    )

    project_id = Column(
        String(255),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Project context for the execution"
    )

    # Execution configuration
    timeout_seconds = Column(
        Integer,
        nullable=True,
        comment="Configured timeout for execution"
    )

    priority = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Execution priority (higher numbers = higher priority)"
    )

    # Additional metadata
    execution_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional execution metadata"
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    project = relationship("Project", back_populates="workflow_executions")

    def __init__(self, **kwargs):
        """Initialize workflow execution with defaults."""
        # Set execution_id if not provided
        if 'execution_id' not in kwargs and 'id' not in kwargs:
            kwargs['execution_id'] = f"exec_{uuid.uuid4().hex[:16]}"

        # Set default status
        if 'status' not in kwargs:
            kwargs['status'] = WorkflowExecutionStatus.PENDING.value

        # Set default priority
        if 'priority' not in kwargs:
            kwargs['priority'] = 0

        super().__init__(**kwargs)

    @property
    def is_completed(self) -> bool:
        """Check if execution is in a terminal state."""
        return self.status in [
            WorkflowExecutionStatus.COMPLETED.value,
            WorkflowExecutionStatus.FAILED.value,
            WorkflowExecutionStatus.CANCELLED.value,
            WorkflowExecutionStatus.TIMEOUT.value
        ]

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        # Use getattr to safely access SQLAlchemy columns
        status = getattr(self, 'status', None)
        success = getattr(self, 'success', None)
        return status == WorkflowExecutionStatus.COMPLETED.value and success is True

    def mark_started(self) -> None:
        """Mark execution as started."""
        self.status = WorkflowExecutionStatus.RUNNING.value
        self.started_at = datetime.utcnow()

    def mark_completed(self, success: bool = True, output_data: Optional[Dict[str, Any]] = None,
                      error_message: Optional[str] = None) -> None:
        """Mark execution as completed."""
        self.completed_at = datetime.utcnow()
        self.success = success

        if output_data is not None:
            self.output_data = output_data

        if error_message is not None:
            self.error_message = error_message

        started_at = getattr(self, 'started_at', None)
        if started_at:
            self.duration_seconds = (self.completed_at - started_at).total_seconds()

        if success:
            self.status = WorkflowExecutionStatus.COMPLETED.value
        else:
            self.status = WorkflowExecutionStatus.FAILED.value

    def mark_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark execution as failed."""
        self.status = WorkflowExecutionStatus.FAILED.value
        self.success = False
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

        if error_details:
            self.error_details = error_details

        started_at = getattr(self, 'started_at', None)
        completed_at = getattr(self, 'completed_at', None)
        if started_at and completed_at:
            self.duration_seconds = (completed_at - started_at).total_seconds()

    def __repr__(self) -> str:
        return f"<WorkflowExecution(id='{self.id}', execution_id='{self.execution_id}', workflow='{self.workflow_id}', status='{self.status}')>"


# Add relationship to Workflow model
Workflow.executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

# Add relationship to Project model (assuming it exists)
try:
    from .project import Project
    Project.workflow_executions = relationship("WorkflowExecution", back_populates="project")
except ImportError:
    # Project model may not be imported yet
    pass


# Constraints for WorkflowExecution
CheckConstraint(
    WorkflowExecution.priority >= -10,
    name='ck_execution_priority_range'
)

CheckConstraint(
    WorkflowExecution.priority <= 10,
    name='ck_execution_priority_range_upper'
)

# Note: Duration and vertex count constraints removed due to SQLAlchemy column access issues
# These should be validated at the application level instead
