# Engine Core

[![PyPI version](https://badge.fury.io/py/engine-core.svg)](https://pypi.org/project/engine-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/engine-core.svg)](https://pypi.org/project/engine-core/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**Engine Framework Core** - AI Agent Orchestration System

Engine Core is the foundational framework for building AI agent orchestration systems based on Pregel and Actor Model principles. It provides the essential components for creating, coordinating, and managing AI agents in complex workflows.

## Features

- **Agent System**: Configurable AI agents with 11 customizable modules
- **Team Coordination**: Hierarchical agent groups with advanced coordination strategies
- **Workflow Engine**: Pregel-based process orchestration for complex agent interactions
- **Tool Integration**: Extensible plugin system for external integrations (APIs, CLI, MCP)
- **Protocol System**: Semantic command sets for consistent agent behavior
- **Memory System**: Hierarchical memory management with semantic search capabilities

## Installation

```bash
pip install engine-core
```

## Quick Start

```python
from engine_core import AgentBuilder, WorkflowBuilder

# Create an agent
agent = AgentBuilder()
    .with_id("assistant")
    .with_model("claude-3.5-sonnet")
    .with_stack(["python", "analysis"])
    .build()

# Create a workflow
workflow = WorkflowBuilder()
    .with_id("analysis_workflow")
    .add_vertex("analyze", agent="assistant")
    .build()

# Execute
result = workflow.execute({"task": "Analyze this code"})
```

## Architecture

Engine Core follows a modular architecture with 6 independent pillars:

- **Agents**: Individual AI agent instances
- **Teams**: Coordinated agent groups
- **Workflows**: Process orchestration (Pregel-based)
- **Tools**: External integrations
- **Protocols**: Behavior command sets
- **Book**: Memory and knowledge management

## Documentation

- [Full Documentation](https://engine-framework.readthedocs.io/)
- [API Reference](https://engine-framework.readthedocs.io/api/)
- [Examples](https://github.com/engine-agi/engine-examples)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [GitHub Issues](https://github.com/engine-agi/engine-core/issues)
- [Discord Community](https://discord.gg/engine-framework)
- [Documentation](https://engine-framework.readthedocs.io/)