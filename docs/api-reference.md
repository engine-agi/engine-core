# API Reference

This document provides a complete API reference for Engine Core.

## Core Classes

### AgentBuilder

The main builder for creating AI agents.

```python
class AgentBuilder:
    def with_id(self, agent_id: str) -> 'AgentBuilder'
    def with_model(self, model: str) -> 'AgentBuilder'
    def with_name(self, name: str) -> 'AgentBuilder'
    def with_speciality(self, speciality: str) -> 'AgentBuilder'
    def with_persona(self, persona: str) -> 'AgentBuilder'
    def with_stack(self, stack: List[str]) -> 'AgentBuilder'
    def with_tools(self, tools: List[str]) -> 'AgentBuilder'
    def with_protocol(self, protocol: str) -> 'AgentBuilder'
    def with_workflow(self, workflow: str) -> 'AgentBuilder'
    def with_book(self, book: str) -> 'AgentBuilder'
    def with_team(self, team: str) -> 'AgentBuilder'
    def build(self) -> BuiltAgent
```

### TeamBuilder

Builder for creating coordinated agent teams.

```python
class TeamBuilder:
    def with_id(self, team_id: str) -> 'TeamBuilder'
    def with_name(self, name: str) -> 'TeamBuilder'
    def with_coordination_strategy(self, strategy: TeamCoordinationStrategy) -> 'TeamBuilder'
    def add_leader(self, agent_id: str) -> 'TeamBuilder'
    def add_member(self, agent_id: str, role: TeamMemberRole, skills: List[str]) -> 'TeamBuilder'
    def build(self, agents: Dict[str, BuiltAgent]) -> BuiltTeam
```

### WorkflowBuilder

Builder for creating Pregel-based workflows.

```python
class WorkflowBuilder:
    def with_id(self, workflow_id: str) -> 'WorkflowBuilder'
    def with_name(self, name: str) -> 'WorkflowBuilder'
    def add_agent_vertex(self, vertex_id: str, agent: BuiltAgent, task: str) -> 'WorkflowBuilder'
    def add_team_vertex(self, vertex_id: str, team: BuiltTeam, task: str) -> 'WorkflowBuilder'
    def add_edge(self, from_vertex: str, to_vertex: str) -> 'WorkflowBuilder'
    def build(self) -> BuiltWorkflow
```

## Enums and Constants

### TeamCoordinationStrategy

```python
class TeamCoordinationStrategy(Enum):
    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    PARALLEL = "parallel"
```

### TeamMemberRole

```python
class TeamMemberRole(Enum):
    LEADER = "leader"
    MEMBER = "member"
```

## Built Classes

### BuiltAgent

Represents a fully configured agent.

```python
class BuiltAgent:
    id: str
    model: str
    name: Optional[str]
    speciality: Optional[str]
    persona: Optional[str]
    stack: List[str]
    tools: Optional[List[str]]
    protocol: Optional[str]
    workflow: Optional[str]
    book: Optional[str]
    team: Optional[str]
```

### BuiltTeam

Represents a fully configured team.

```python
class BuiltTeam:
    id: str
    name: str
    coordination_strategy: TeamCoordinationStrategy
    members: List[TeamMember]
    member_count: int
```

### BuiltWorkflow

Represents a fully configured workflow.

```python
class BuiltWorkflow:
    id: str
    name: str
    vertices: Dict[str, WorkflowVertex]
    edges: List[WorkflowEdge]
    vertex_count: int
    edge_count: int
```

## Execution Methods

### Synchronous Execution

```python
# Execute workflow synchronously
result = workflow.execute(context: Dict[str, Any]) -> Dict[str, Any]
```

### Asynchronous Execution

```python
# Execute workflow asynchronously
result = await workflow.execute_async(context: Dict[str, Any]) -> Dict[str, Any]
```

### Execution with Callbacks

```python
# Execute with progress callbacks
result = workflow.execute_with_callbacks(
    context: Dict[str, Any],
    on_step_complete: Callable[[str, Dict], None],
    on_complete: Callable[[Dict], None]
) -> Dict[str, Any]
```

## Error Classes

### AgentConfigurationError

Raised when agent configuration is invalid.

```python
class AgentConfigurationError(ValueError):
    pass
```

### TeamConfigurationError

Raised when team configuration is invalid.

```python
class TeamConfigurationError(ValueError):
    pass
```

### WorkflowExecutionError

Raised when workflow execution fails.

```python
class WorkflowExecutionError(Exception):
    failed_step: str
    details: Dict[str, Any]
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | None |
| `REDIS_URL` | Redis connection URL | None |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_FORMAT` | Log format (json/text) | json |
| `MAX_CONCURRENT_AGENTS` | Max concurrent agents | 100 |
| `WORKFLOW_TIMEOUT` | Workflow timeout (seconds) | 300 |

### Configuration Files

Engine Core supports YAML and JSON configuration files:

```yaml
engine:
  database:
    url: "postgresql://user:pass@localhost:5432/engine"
  redis:
    url: "redis://localhost:6379"
  logging:
    level: "INFO"
    format: "json"
  performance:
    max_concurrent_agents: 100
    workflow_timeout: 300
```

## Type Hints

All public APIs include comprehensive type hints for better IDE support and static analysis.

```python
from typing import Dict, List, Optional, Any, Callable
from engine_core import AgentBuilder, TeamBuilder, WorkflowBuilder
from engine_core.core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole
```

## Async/Await Support

All execution methods support both synchronous and asynchronous patterns:

```python
# Sync
result = workflow.execute(context)

# Async
result = await workflow.execute_async(context)
```

## Context Passing

Workflows pass context between vertices automatically:

```python
context = {
    "user_id": 123,
    "task": "analyze_code",
    "files": ["main.py", "utils.py"],
    "requirements": ["performance", "security"]
}

result = workflow.execute(context)
# Context is enriched with results from each vertex
```
