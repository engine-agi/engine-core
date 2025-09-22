# Engine Core Usage Guide

[![PyPI version](https://badge.fury.io/py/engine-core.svg)](https://pypi.org/project/engine-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/engine-core.svg)](https://pypi.org/project/engine-core/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Complete usage guide for Engine Core** - AI Agent Orchestration Framework

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Agent Creation](#-agent-creation)
- [Team Coordination](#-team-coordination)
- [Workflow Orchestration](#-workflow-orchestration)
- [Complete Integration](#-complete-integration)
- [Architecture Overview](#-architecture-overview)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Use Cases](#-use-cases)

---

## 🚀 Quick Start

### Basic Agent Creation

```python
from engine_core import AgentBuilder

# Create a simple agent
agent = AgentBuilder() \
    .with_id("code_assistant") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Code Assistant") \
    .with_speciality("Python Development") \
    .with_stack(["python", "javascript", "testing"]) \
    .build()

print(f"Agent created: {agent.name}")
```

### Team Coordination

```python
from engine_core import AgentBuilder, TeamBuilder
from engine_core.core.teams.team_builder import TeamCoordinationStrategy

# Create multiple agents
senior_dev = AgentBuilder() \
    .with_id("senior_dev") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Senior Developer") \
    .with_speciality("Architecture & Design") \
    .build()

junior_dev = AgentBuilder() \
    .with_id("junior_dev") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Junior Developer") \
    .with_speciality("Implementation") \
    .build()

# Create a hierarchical team
team = TeamBuilder() \
    .with_id("dev_team") \
    .with_name("Development Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL) \
    .add_leader("senior_dev") \
    .add_member("junior_dev", TeamMemberRole.MEMBER, ["python", "testing"]) \
    .build({"senior_dev": senior_dev, "junior_dev": junior_dev})

print(f"Team created with {team.member_count} members")
```

### Workflow Orchestration

```python
from engine_core import WorkflowBuilder

# Create a workflow using the team
workflow = WorkflowBuilder() \
    .with_id("development_pipeline") \
    .with_name("Development Pipeline") \
    .add_team_vertex("analysis", team, "Analyze requirements and create technical specification") \
    .add_team_vertex("implementation", team, "Implement the solution according to specifications") \
    .add_team_vertex("testing", team, "Write and execute comprehensive tests") \
    .add_team_vertex("documentation", team, "Create documentation and deployment guides") \
    .add_edge("analysis", "implementation") \
    .add_edge("implementation", "testing") \
    .add_edge("testing", "documentation") \
    .build()

print(f"Workflow created with {workflow.vertex_count} steps and {workflow.edge_count} connections")
```

---

## 🤖 Agent Creation

### Minimal Configuration (3 required fields)

```python
agent = AgentBuilder()
    .with_id("agent_id")
    .with_model("claude-3.5-sonnet")
    .with_stack(["python"])
    .build()
```

### Complete Configuration (11 modules)

```python
agent = AgentBuilder()
    .with_id("senior_dev")
    .with_model("claude-3.5-sonnet")
    .with_name("Senior Developer")
    .with_speciality("Full-Stack Development")
    .with_persona("Experienced, methodical")
    .with_stack(["python", "react", "postgresql"])
    .with_tools(["github", "vscode"])
    .with_protocol("analysis_first")
    .with_workflow("tdd_workflow")
    .with_book("project_memory")
    .build()
```

### Agent Modules

| Module | Purpose | Example |
|--------|---------|---------|
| **ID** | Unique identifier | `"senior_dev"` |
| **Model** | AI model to use | `"claude-3.5-sonnet"` |
| **Name** | Display name | `"Senior Developer"` |
| **Speciality** | Domain expertise | `"Full-Stack Development"` |
| **Persona** | Behavioral traits | `"Experienced, methodical"` |
| **Stack** | Technology skills | `["python", "react", "postgresql"]` |
| **Tools** | External integrations | `["github", "vscode"]` |
| **Protocol** | Behavior commands | `"analysis_first"` |
| **Workflow** | Process templates | `"tdd_workflow"` |
| **Book** | Memory system | `"project_memory"` |

---

## 👥 Team Coordination

### Coordination Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Hierarchical** | Leader oversees members | Traditional management |
| **Collaborative** | Equal participation | Creative brainstorming |
| **Parallel** | Independent execution | High-throughput tasks |

### Team Creation Example

```python
from engine_core.core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole

# Create collaborative team
team = TeamBuilder() \
    .with_id("design_team") \
    .with_name("UX/UI Design Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("ux_designer", TeamMemberRole.MEMBER, ["design", "user-research"]) \
    .add_member("ui_developer", TeamMemberRole.MEMBER, ["frontend", "prototyping"]) \
    .add_member("creative_director", TeamMemberRole.MEMBER, ["strategy", "branding"]) \
    .build(agent_dict)
```

### Team Hierarchy Override

Team protocols/workflows override individual agent settings:

```python
# Agent has individual workflow
agent.workflow = "solo_workflow"

# Team overrides with collaborative workflow
team.workflow = "team_workflow"
# Agent will use team_workflow in team context
```

---

## ⚡ Workflow Orchestration

### Pregel-Based Execution

Workflows follow the Pregel model with vertices (computation steps) and edges (data flow):

```python
workflow = WorkflowBuilder() \
    .with_id("data_pipeline") \
    .add_vertex("extract", agent, "Extract data from sources") \
    .add_vertex("transform", agent, "Clean and transform data") \
    .add_vertex("load", agent, "Load into destination") \
    .add_edge("extract", "transform") \
    .add_edge("transform", "load") \
    .build()
```

### Vertex Types

- **Agent Vertex**: Single agent execution
- **Team Vertex**: Team coordination execution
- **Conditional Vertex**: Branching logic
- **Parallel Vertex**: Concurrent execution

### Execution Context

```python
context = {
    "input_data": dataset,
    "transform_rules": rules,
    "output_format": "json"
}

result = await workflow.execute_async(context)
```

---

## 🔗 Complete Integration

### Full-Stack Development Example

```python
import asyncio
from engine_core import AgentBuilder, TeamBuilder, WorkflowBuilder
from engine_core.core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole

async def main():
    # Create specialized agents
    architect = AgentBuilder() \
        .with_id("architect") \
        .with_model("claude-3.5-sonnet") \
        .with_name("System Architect") \
        .with_speciality("System Design & Architecture") \
        .with_persona("Experienced architect focused on scalable, maintainable systems") \
        .with_stack(["system-design", "scalability", "security"]) \
        .build()

    developer = AgentBuilder() \
        .with_id("developer") \
        .with_model("claude-3.5-sonnet") \
        .with_name("Backend Developer") \
        .with_speciality("Python Backend Development") \
        .with_persona("Skilled developer who writes clean, efficient code") \
        .with_stack(["python", "fastapi", "sqlalchemy", "testing"]) \
        .build()

    tester = AgentBuilder() \
        .with_id("tester") \
        .with_model("claude-3.5-sonnet") \
        .with_name("QA Engineer") \
        .with_speciality("Quality Assurance & Testing") \
        .with_persona("Detail-oriented tester ensuring software quality") \
        .with_stack(["testing", "automation", "performance"]) \
        .build()

    # Create collaborative team
    team = TeamBuilder() \
        .with_id("fullstack_team") \
        .with_name("Full-Stack Development Team") \
        .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
        .add_member("architect", TeamMemberRole.MEMBER, ["design", "architecture"]) \
        .add_member("developer", TeamMemberRole.MEMBER, ["backend", "api"]) \
        .add_member("tester", TeamMemberRole.MEMBER, ["testing", "qa"]) \
        .build({
            "architect": architect,
            "developer": developer,
            "tester": tester
        })

    # Create complex workflow
    workflow = WorkflowBuilder() \
        .with_id("webapp_development") \
        .with_name("Web Application Development Workflow") \
        .add_team_vertex("requirements", team, "Gather and analyze project requirements") \
        .add_team_vertex("design", team, "Create system design and database schema") \
        .add_team_vertex("backend_api", team, "Implement REST API with FastAPI") \
        .add_team_vertex("frontend_ui", team, "Create responsive user interface") \
        .add_team_vertex("integration", team, "Integrate frontend with backend") \
        .add_team_vertex("testing_qa", team, "Comprehensive testing and quality assurance") \
        .add_team_vertex("deployment", team, "Prepare for production deployment") \
        .add_edge("requirements", "design") \
        .add_edge("design", "backend_api") \
        .add_edge("design", "frontend_ui") \
        .add_edge("backend_api", "integration") \
        .add_edge("frontend_ui", "integration") \
        .add_edge("integration", "testing_qa") \
        .add_edge("testing_qa", "deployment") \
        .build()

    # Execute workflow with context
    context = {
        "project_name": "E-commerce Platform",
        "technologies": ["FastAPI", "React", "PostgreSQL"],
        "requirements": "Build a scalable e-commerce platform with user authentication, product catalog, shopping cart, and payment integration"
    }

    print("🚀 Starting workflow execution...")
    result = await workflow.execute_async(context)
    print(f"✅ Workflow completed: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🏗️ Architecture Overview

### 6 Core Pillars

Engine Core is built on 6 independent pillars that interconnect seamlessly:

| Pillar | Purpose | Key Features |
|--------|---------|--------------|
| **🧠 Agents** | Individual AI instances | 11 configurable modules, model abstraction, tool integration |
| **👥 Teams** | Coordinated groups | Hierarchical/Collaborative/Parallel strategies, task distribution |
| **⚡ Workflows** | Process orchestration | Pregel-based execution, graph flows, async processing |
| **🔧 Tools** | External integrations | Plugin system, API clients, CLI tools, MCP support |
| **📋 Protocols** | Behavior commands | Semantic commands, consistent behavior, extensible |
| **📚 Book** | Memory management | Hierarchical storage, semantic search, persistent memory |

### Design Principles

- **🔧 Builder Pattern**: Fluent builders for all components
- **🎭 Actor Model**: Isolated execution with message passing
- **⚡ Pregel Model**: Graph-based workflow computation
- **🔌 Plugin System**: Extensible integrations
- **🚀 Async-First**: Performance-optimized async operations
- **🧪 Test-Driven**: Comprehensive coverage with integration tests

### Performance Characteristics

- **Concurrent Agents**: Support for 1000+ simultaneous agents
- **Response Times**: <100ms API response times
- **Workflow Execution**: Complex workflows complete in seconds
- **Real-time Updates**: Live dashboard synchronization

---

## ⚙️ Configuration

### Environment Variables

```bash
# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/engine

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance
MAX_CONCURRENT_AGENTS=100
WORKFLOW_TIMEOUT=300
```

### Configuration Files

Engine supports YAML and JSON configuration:

```yaml
# config.yaml
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

### Advanced Configuration

```python
from engine_core.config import EngineConfig

config = EngineConfig(
    database_url="postgresql://...",
    redis_url="redis://...",
    max_concurrent_agents=200,
    workflow_timeout=600,
    log_level="DEBUG"
)

# Apply configuration
engine_core.configure(config)
```

---

## 🧪 Testing

### Test Categories

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/

# All tests with coverage
pytest --cov=engine_core --cov-report=html
```

### Test Structure

```
tests/
├── unit/           # Individual component tests
├── integration/    # End-to-end workflow tests
├── performance/    # Load and stress tests
└── fixtures/       # Test data and mocks
```

### Writing Tests

```python
import pytest
from engine_core import AgentBuilder

def test_agent_creation():
    agent = AgentBuilder() \
        .with_id("test_agent") \
        .with_model("claude-3.5-sonnet") \
        .build()

    assert agent.id == "test_agent"
    assert agent.model == "claude-3.5-sonnet"

@pytest.mark.asyncio
async def test_workflow_execution():
    # Test async workflow execution
    workflow = create_test_workflow()
    result = await workflow.execute_async(test_context)
    assert result["status"] == "completed"
```

---

## 🎯 Use Cases

### 🤖 AI Agent Development

```python
# Specialized domain agents
code_reviewer = AgentBuilder() \
    .with_id("code_reviewer") \
    .with_speciality("Code Quality & Security") \
    .with_stack(["security", "best-practices", "testing"]) \
    .build()

data_analyst = AgentBuilder() \
    .with_id("data_analyst") \
    .with_speciality("Data Science & Analytics") \
    .with_stack(["python", "pandas", "machine-learning"]) \
    .build()
```

### 👥 Team Orchestration

```python
# Cross-functional teams
product_team = TeamBuilder() \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("product_manager", role=TeamMemberRole.LEADER) \
    .add_member("designer", role=TeamMemberRole.MEMBER) \
    .add_member("developer", role=TeamMemberRole.MEMBER) \
    .build()
```

### ⚙️ Automation Systems

```python
# DevOps automation
deployment_workflow = WorkflowBuilder() \
    .add_vertex("build", ci_agent, "Build application") \
    .add_vertex("test", qa_agent, "Run test suite") \
    .add_vertex("deploy", devops_agent, "Deploy to production") \
    .add_edge("build", "test") \
    .add_edge("test", "deploy") \
    .build()
```

### 🔧 Tool Integration

```python
# External service integration
agent_with_tools = AgentBuilder() \
    .with_tools(["github", "slack", "jira"]) \
    .with_protocol("integration_protocol") \
    .build()
```

### 📊 Data Processing

```python
# ETL pipelines
data_workflow = WorkflowBuilder() \
    .add_vertex("extract", etl_agent, "Extract from sources") \
    .add_vertex("transform", ml_agent, "Apply ML transformations") \
    .add_vertex("load", storage_agent, "Load to warehouse") \
    .build()
```

### 🎮 Game Development

```python
# NPC behavior systems
npc_agent = AgentBuilder() \
    .with_speciality("Game AI & Behavior") \
    .with_persona("Adaptive game character") \
    .with_protocol("game_behavior") \
    .build()
```

---

## 📚 Additional Resources

- **[Getting Started](docs/getting-started.md)** - Setup and first steps
- **[Agent Configuration](docs/agent-configuration.md)** - All 11 modules explained
- **[Team Coordination](docs/team-coordination.md)** - Advanced strategies
- **[Workflow Design](docs/workflow-design.md)** - Pregel patterns
- **[Tool Integration](docs/tool-integration.md)** - Plugin system
- **[Protocol System](docs/protocol-system.md)** - Command sets
- **[Memory Management](docs/memory-management.md)** - Book system
- **[API Reference](docs/api-reference.md)** - Complete API docs

---

**Engine Framework** - Making AI Agent Orchestration Simple, Powerful, and Production-Ready 🚀