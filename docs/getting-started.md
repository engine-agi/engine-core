# Getting Started with Engine Core

Welcome to Engine Core! This guide will help you get started with building AI agent orchestration systems.

## Prerequisites

- Python 3.11 or higher
- Basic understanding of Python async/await
- Familiarity with AI concepts (optional but helpful)

## Installation

```bash
pip install engine-core
```

## Your First Agent

Let's create a simple AI agent that can help with coding tasks.

```python
from engine_core import AgentBuilder

# Create your first agent
agent = AgentBuilder() \
    .with_id("code_helper") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Code Helper") \
    .with_speciality("Python Development") \
    .with_persona("A helpful coding assistant that writes clean, efficient Python code") \
    .with_stack(["python", "debugging", "best-practices"]) \
    .build()

print(f"Agent created: {agent.name}")
print(f"Speciality: {agent.speciality}")
print(f"Tech Stack: {agent.stack}")
```

## Understanding Agent Modules

Engine Core agents have 11 configurable modules:

| Module | Purpose | Example |
|--------|---------|---------|
| **id** | Unique identifier | `"code_helper"` |
| **model** | AI model to use | `"claude-3.5-sonnet"` |
| **name** | Human-readable name | `"Code Helper"` |
| **speciality** | Area of expertise | `"Python Development"` |
| **persona** | Behavioral description | `"Helpful coding assistant..."` |
| **stack** | Technology skills | `["python", "debugging"]` |
| **tools** | External tool access | `["github", "vscode"]` |
| **protocol** | Behavior protocol | `"analysis_first"` |
| **workflow** | Default workflow | `"tdd_workflow"` |
| **book** | Memory system | `"project_memory"` |
| **team** | Team membership | `"dev_team"` |

## Creating a Team

Teams allow multiple agents to work together.

```python
from engine_core import AgentBuilder, TeamBuilder
from engine_core.core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole

# Create team members
architect = AgentBuilder() \
    .with_id("architect") \
    .with_model("claude-3.5-sonnet") \
    .with_name("System Architect") \
    .with_speciality("System Design") \
    .build()

developer = AgentBuilder() \
    .with_id("developer") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Developer") \
    .with_speciality("Implementation") \
    .build()

# Create a collaborative team
team = TeamBuilder() \
    .with_id("dev_team") \
    .with_name("Development Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("architect", TeamMemberRole.MEMBER, ["design", "architecture"]) \
    .add_member("developer", TeamMemberRole.MEMBER, ["coding", "testing"]) \
    .build({
        "architect": architect,
        "developer": developer
    })

print(f"Team created: {team.name}")
print(f"Members: {team.member_count}")
print(f"Strategy: {team.coordination_strategy}")
```

## Building Workflows

Workflows orchestrate complex agent interactions using a Pregel-based model.

```python
from engine_core import WorkflowBuilder

# Create a development workflow
workflow = WorkflowBuilder() \
    .with_id("development_workflow") \
    .with_name("Software Development Process") \
    .add_team_vertex("planning", team, "Analyze requirements and create technical specifications") \
    .add_team_vertex("implementation", team, "Write clean, tested code according to specifications") \
    .add_team_vertex("review", team, "Code review and quality assurance") \
    .add_edge("planning", "implementation") \
    .add_edge("implementation", "review") \
    .build()

print(f"Workflow created: {workflow.name}")
print(f"Steps: {workflow.vertex_count}")
print(f"Connections: {workflow.edge_count}")
```

## Executing Workflows

```python
import asyncio

async def main():
    # Define the task context
    context = {
        "project": "Build a REST API",
        "requirements": [
            "User authentication",
            "CRUD operations for resources",
            "Input validation",
            "Error handling"
        ],
        "technologies": ["FastAPI", "SQLAlchemy", "PostgreSQL"],
        "deadline": "2 weeks"
    }

    print("🚀 Starting workflow execution...")
    result = await workflow.execute_async(context)
    print(f"✅ Workflow completed: {result}")

# Run the workflow
asyncio.run(main())
```

## Next Steps

Now that you have the basics, explore these advanced topics:

1. **[Agent Configuration](agent-configuration.md)** - Deep dive into all 11 agent modules
2. **[Team Coordination](team-coordination.md)** - Different coordination strategies
3. **[Workflow Design](workflow-design.md)** - Advanced Pregel-based orchestration
4. **[Tool Integration](tool-integration.md)** - Connecting external APIs and services
5. **[Protocol System](protocol-system.md)** - Customizing agent behavior
6. **[Memory Management](memory-management.md)** - Using the Book system

## Examples Repository

Check out the [engine-examples](https://github.com/engine-agi/engine-examples) repository for complete, runnable examples:

- Basic agent creation and configuration
- Team coordination patterns
- Complex workflow orchestration
- Tool integration examples
- Production deployment patterns

## Need Help?

- 📚 [Full Documentation](https://engine-framework.readthedocs.io/)
- 💬 [Discord Community](https://discord.gg/engine-framework)
- 🐛 [GitHub Issues](https://github.com/engine-agi/engine-core/issues)

Happy building! 🚀