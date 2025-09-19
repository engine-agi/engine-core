# Engine Core

[![PyPI version](https://badge.fury.io/py/engine-core.svg)](https://pypi.org/project/engine-core/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Engine Framework Core** - The heart of the AI Agent Orchestration System.

## 🚀 Features

- **6 Core Pillars**: Agents, Teams, Workflows, Tools, Protocols, Book
- **REST API**: Complete HTTP interface for all functionality
- **Async Architecture**: Built on asyncio for high performance
- **Type Safety**: Full Pydantic models and validation
- **Database Integration**: PostgreSQL + Redis support

## 📦 Installation

```bash
pip install engine-core
```

## 🏗️ Architecture

```
engine/
├── core/              # 6 pillars implementation
│   ├── agents/       # Agent management
│   ├── teams/        # Team coordination
│   ├── workflows/    # Pregel-based orchestration
│   ├── tools/        # External integrations
│   ├── protocols/    # Command protocols
│   └── book/         # Memory system
├── api/              # REST API endpoints
└── shared/           # Common types and utilities
```

## 🔧 Usage

```python
from engine.core.agents import AgentBuilder
from engine.api.main import app

# Create an agent
agent = AgentBuilder() \
    .with_id("my-agent") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["python", "web"]) \
    .build()

# Start the API server
uvicorn engine.api.main:app --host 0.0.0.0 --port 8000
```

## 📚 Documentation

- [API Reference](https://engine-agi.github.io/engine-core/)
- [Getting Started](https://engine-agi.github.io/engine-core/getting-started)
- [Examples](https://github.com/engine-agi/engine-examples)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Part of the Engine Framework** | [engine-agi](https://github.com/engine-agi)