# Engine Core

[![PyPI version](https://badge.fury.io/py/engine-core.svg)](https://pypi.org/project/engine-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/engine-core.svg)](https://pypi.org/project/engine-core/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/engine-agi/engine-core/actions/workflows/tests.yml/badge.svg)](https://github.com/engine-agi/engine-core/actions)

**Engine Framework Core** - AI Agent Orchestration System

A powerful framework for building AI agent orchestration systems based on Pregel and Actor Model principles. Create, coordinate, and manage AI agents in complex workflows with maximum customization.

## ✨ Features

- **🧠 Agent System**: Configurable AI agents with 11 customizable modules
- **👥 Team Coordination**: Hierarchical agent groups with advanced coordination strategies
- **⚡ Workflow Engine**: Pregel-based process orchestration for complex agent interactions
- **🔧 Tool Integration**: Extensible plugin system for external integrations (APIs, CLI, MCP)
- **📋 Protocol System**: Semantic command sets for consistent agent behavior
- **📚 Memory System**: Hierarchical memory management with semantic search capabilities
- **🚀 High Performance**: Async-first architecture supporting 1000+ concurrent agents
- **🔒 Production Ready**: Comprehensive testing, validation, and error handling

## 📦 Installation

```bash
# From PyPI
pip install engine-core

# From source
git clone https://github.com/engine-agi/engine-core.git
cd engine-core
pip install -e .
```

### Requirements

- Python 3.11+
- PostgreSQL (optional, for persistence)
- Redis (optional, for workflows and caching)

## 🚀 Quick Start

```python
from engine_core import AgentBuilder, TeamBuilder, WorkflowBuilder

# Create an agent
agent = AgentBuilder() \
    .with_id("assistant") \
    .with_model("claude-3.5-sonnet") \
    .with_name("AI Assistant") \
    .build()

# Create a team
team = TeamBuilder() \
    .with_id("team") \
    .with_name("Development Team") \
    .add_member("assistant", agent) \
    .build({"assistant": agent})

# Create a workflow
workflow = WorkflowBuilder() \
    .with_id("task") \
    .add_team_vertex("analyze", team, "Analyze the task") \
    .add_team_vertex("implement", team, "Implement the solution") \
    .add_edge("analyze", "implement") \
    .build()

# Execute
import asyncio

async def main():
    result = await workflow.execute_async({"task": "Build a web app"})
    print(result)

asyncio.run(main())
```

## 📚 Documentation

### 📖 Guides

- **[Complete Usage Guide](USAGE.md)** - Detailed examples, architecture, and advanced usage
- **[Getting Started](docs/getting-started.md)** - Step-by-step setup guide
- **[Agent Configuration](docs/agent-configuration.md)** - All 11 agent modules explained
- **[Team Coordination](docs/team-coordination.md)** - Strategies and best practices
- **[Workflow Design](docs/workflow-design.md)** - Pregel-based orchestration patterns
- **[Tool Integration](docs/tool-integration.md)** - Plugin system and custom tools
- **[Protocol System](docs/protocol-system.md)** - Command sets and behavior
- **[Memory Management](docs/memory-management.md)** - Book system usage
- **[API Reference](docs/api-reference.md)** - Complete API documentation

### 💡 Examples

- **[Basic Examples](https://github.com/engine-agi/engine-examples/tree/main/basic)**
- **[Advanced Patterns](https://github.com/engine-agi/engine-examples/tree/main/advanced)**
- **[Integration Examples](https://github.com/engine-agi/engine-examples/tree/main/integration)**

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=engine_core --cov-report=html
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/engine-agi/engine-core.git
cd engine-core
poetry install
poetry run pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 [GitHub Issues](https://github.com/engine-agi/engine-core/issues)
- 💬 [Discord Community](https://discord.gg/engine-framework)
- 📚 [Documentation](https://engine-framework.readthedocs.io/)
- 🐛 [Bug Reports](https://github.com/engine-agi/engine-core/issues/new?template=bug_report.md)
- 💡 [Feature Requests](https://github.com/engine-agi/engine-core/issues/new?template=feature_request.md)

---

**Engine Framework** - Making AI Agent Orchestration Simple, Powerful, and Production-Ready 🚀