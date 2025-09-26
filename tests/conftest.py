"""Shared pytest fixtures and configuration for engine-core."""

import asyncio
import os
import sys
from typing import AsyncGenerator, Generator

import pytest

# Add src to path
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_session() -> AsyncGenerator[None, None]:
    """Async session fixture for tests that need async setup/teardown."""
    yield


@pytest.fixture
def temp_dir(tmp_path) -> str:
    """Provide a temporary directory for tests."""
    return str(tmp_path)


@pytest.fixture
def sample_agent_config() -> dict:
    """Sample agent configuration for testing."""
    return {
        "id": "test-agent",
        "model": "claude-3.5-sonnet",
        "name": "Test Agent",
        "speciality": "Testing",
        "stack": ["python", "pytest"],
        "tools": ["github", "vscode"],
        "protocol": "analysis_first",
        "workflow": "tdd_workflow",
        "book": "test_memory",
    }


@pytest.fixture
def sample_team_config() -> dict:
    """Sample team configuration for testing."""
    return {
        "id": "test-team",
        "name": "Test Team",
        "agents": ["agent1", "agent2"],
        "coordination_strategy": "hierarchical",
        "protocol": "team_protocol",
    }


@pytest.fixture
def sample_workflow_config() -> dict:
    """Sample workflow configuration for testing."""
    return {
        "id": "test-workflow",
        "vertices": [
            {"id": "analysis", "agent": "analyst"},
            {"id": "implementation", "agent": "developer"},
        ],
        "edges": [{"from": "analysis", "to": "implementation"}],
    }
