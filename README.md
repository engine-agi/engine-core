# Engine Core

[![PyPI version](https://badge.fury.io/py/engine-core.svg)](https://pypi.org/project/engine-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/engine-core.svg)](https://pypi.org/project/engine-core/)
[![License](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
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

### 🚀 Quick Install (Recommended)

```bash
pip install engine-core
```

**That's it!** Engine Core v1.0.0 is now available on PyPI and ready to use.

### 📋 Requirements

- **Python**: 3.11 or higher
- **Optional Dependencies**:
  - PostgreSQL (for data persistence)
  - Redis (for workflow caching and pub/sub)

### 🔧 Alternative Installation Methods

```bash
# From source (development)
git clone https://github.com/engine-agi/engine-core.git
cd engine-core
pip install -e .

# With optional dependencies
pip install engine-core[postgres,redis]

# Development installation with all tools
pip install -e ".[dev]"
```

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

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

### 📋 Dual Licensing

**Engine Framework** uses a dual licensing model:

- **AGPL-3.0**: For open-source usage, community contributions, and non-commercial projects
- **Commercial License**: For enterprise deployments, proprietary integrations, and commercial products

### 📞 Commercial Licensing

For commercial usage or if you need a different license:
- Contact: [licensing@engine-framework.com](mailto:licensing@engine-framework.com)
- Enterprise features and support available
- Custom deployment options

See the [LICENSE](LICENSE) file and [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL) for details.

## 🆘 Support

- 📧 [GitHub Issues](https://github.com/engine-agi/engine-core/issues)
- 💬 [Discord Community](https://discord.gg/engine-framework)
- 📚 [Documentation](https://engine-framework.readthedocs.io/)
- 🐛 [Bug Reports](https://github.com/engine-agi/engine-core/issues/new?template=bug_report.md)
- 💡 [Feature Requests](https://github.com/engine-agi/engine-core/issues/new?template=feature_request.md)

---

**Engine Framework** - Making AI Agent Orchestration Simple, Powerful, and Production-Ready 🚀