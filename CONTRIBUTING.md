# Contributing to Engine Core

Thank you for your interest in contributing to Engine Core! We welcome contributions from the community.

## Development Setup

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/engine-agi/engine-core.git
cd engine-core

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run black .
poetry run isort .
poetry run flake8 .
```

## Development Workflow

### 1. Choose an Issue

- Check [GitHub Issues](https://github.com/engine-agi/engine-core/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

We follow [Conventional Commits](https://conventionalcommits.org/) format.

### 5. Create Pull Request

- Push your branch to GitHub
- Create a Pull Request with a clear description
- Reference any related issues

## Code Style

### Python Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

### Commit Messages

Follow Conventional Commits:

```
feat: add new agent configuration option
fix: resolve workflow execution timeout
docs: update API reference
test: add integration tests for team coordination
refactor: simplify agent builder pattern
```

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Files: `snake_case.py`

## Testing

### Running Tests

```bash
# All tests
poetry run pytest

# Specific test file
poetry run pytest tests/unit/test_agent_builder.py

# With coverage
poetry run pytest --cov=engine_core --cov-report=html

# Integration tests only
poetry run pytest tests/integration/
```

### Writing Tests

- Use `pytest` framework
- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Follow naming: `test_*.py` and `test_*` functions

Example:

```python
def test_agent_creation():
    agent = AgentBuilder() \
        .with_id("test_agent") \
        .with_model("claude-3.5-sonnet") \
        .build()

    assert agent.id == "test_agent"
    assert agent.model == "claude-3.5-sonnet"
```

## Documentation

### Updating Docs

- Documentation is in the `docs/` folder
- Use Markdown format
- Keep examples up-to-date
- Test code examples manually

### API Documentation

- Add type hints to all public functions
- Include docstrings for classes and methods
- Update API reference when adding new features

## Architecture Guidelines

### Builder Pattern

All core entities use the Builder pattern:

```python
# Good
agent = AgentBuilder() \
    .with_id("agent_id") \
    .with_model("claude-3.5-sonnet") \
    .build()

# Avoid
agent = Agent(id="agent_id", model="claude-3.5-sonnet")
```

### Async First

Prefer async methods for I/O operations:

```python
# Good
async def execute_workflow(self, context):
    result = await self.agent.process(context)
    return result

# Use sync wrappers when needed
def execute(self, context):
    return asyncio.run(self.execute_async(context))
```

### Error Handling

Use custom exceptions and provide meaningful error messages:

```python
class AgentConfigurationError(ValueError):
    """Raised when agent configuration is invalid."""
    pass

# Usage
if not agent.stack:
    raise AgentConfigurationError("Agent must have at least one technology in stack")
```

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages follow conventional format
- [ ] No sensitive information committed

### PR Description

Include:
- What changes were made
- Why the changes were needed
- How to test the changes
- Screenshots/videos for UI changes
- Breaking changes (if any)

### Review Process

- At least one maintainer review required
- CI checks must pass
- All conversations resolved
- Squash commits if requested

## Community

- 💬 [Discord Server](https://discord.gg/engine-framework)
- 📧 [GitHub Discussions](https://github.com/engine-agi/engine-core/discussions)
- 🐛 [Issue Tracker](https://github.com/engine-agi/engine-core/issues)

## License

By contributing to Engine Core, you agree that your contributions will be licensed under the MIT License.
