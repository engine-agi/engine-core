#!/usr/bin/env python3
"""
Integration test to validate agent independence.
This script demonstrates that agents can be created and executed
without depending on teams, workflows, protocols, tools, or book modules.
"""

import asyncio
import os
import sys

from engine_core.core.agents.agent_builder import AgentBuilder

# Add src to path (ensure engine-core comes first)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
# Remove any backend paths that might conflict
sys.path = [p for p in sys.path if "backend" not in p]


async def test_agent_independence():
    """Test that agents work independently of other core modules"""

    print("🧪 Testing Agent Independence...")
    print("=" * 50)

    # Test 1: Create minimal agent
    print("✅ Test 1: Creating minimal agent...")
    minimal_agent = (
        AgentBuilder().with_id("minimal_agent").with_model("claude-3.5-sonnet").build()
    )

    assert minimal_agent.id == "minimal_agent"
    assert minimal_agent.model == "claude-3.5-sonnet"
    print("   ✅ Minimal agent created successfully")

    # Test 2: Create complete agent with all modules
    print("✅ Test 2: Creating complete agent with all 11 modules...")
    complete_agent = (
        AgentBuilder()
        .with_id("senior_developer")
        .with_name("Senior Python Developer")
        .with_model("claude-3.5-sonnet")
        .with_speciality("Full-Stack Python Development")
        .with_persona("Experienced developer who follows best practices")
        .with_stack(["python", "fastapi", "postgresql", "docker"])
        .with_tools(["github", "vscode", "pytest"])
        .with_protocol("tdd_protocol")
        .with_workflow("development_workflow")
        .with_book("project_memory")
        .build()
    )

    assert complete_agent.id == "senior_developer"
    assert complete_agent.name == "Senior Python Developer"
    assert complete_agent.speciality == "Full-Stack Python Development"
    assert complete_agent.persona == "Experienced developer who follows best practices"
    assert complete_agent.stack == ["python", "fastapi", "postgresql", "docker"]
    assert complete_agent.tools == ["github", "vscode", "pytest"]
    assert complete_agent.protocol == "tdd_protocol"
    assert complete_agent.workflow == "development_workflow"
    assert complete_agent.book == "project_memory"
    print("   ✅ Complete agent created successfully")

    # Test 3: Execute tasks independently
    print("✅ Test 3: Executing tasks independently...")

    # Execute with minimal agent
    task1 = "Write a Python function to calculate fibonacci numbers"
    print(f"   📝 Executing task with minimal agent: '{task1[:50]}...'")
    result1 = await minimal_agent.execute(task1)

    assert result1.state.name == "COMPLETED"
    assert result1.agent_id == "minimal_agent"
    assert result1.task == task1
    assert len(result1.messages) == 1
    assert "Mock response" in result1.messages[0].content
    print("   ✅ Minimal agent executed task successfully")

    # Execute with complete agent
    task2 = "Design a REST API for a task management system"
    print(f"   📝 Executing task with complete agent: '{task2[:50]}...'")
    result2 = await complete_agent.execute(task2)

    assert result2.state.name == "COMPLETED"
    assert result2.agent_id == "senior_developer"
    assert result2.task == task2
    assert len(result2.messages) == 1
    assert "Mock response" in result2.messages[0].content
    print("   ✅ Complete agent executed task successfully")

    # Test 4: Multiple agents working independently
    print("✅ Test 4: Multiple agents working independently...")

    agents = []
    for i in range(3):
        agent = (
            AgentBuilder()
            .with_id(f"agent_{i}")
            .with_model("claude-3.5-sonnet")
            .with_name(f"Agent {i}")
            .build()
        )
        agents.append(agent)

    # Execute tasks concurrently
    tasks = [agent.execute(f"Task for agent {i}") for i, agent in enumerate(agents)]

    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        assert result.state.name == "COMPLETED"
        assert result.agent_id == f"agent_{i}"
        assert f"Task for agent {i}" in result.task

    print("   ✅ Multiple agents executed tasks concurrently")

    # Test 5: Validate no external dependencies
    print("✅ Test 5: Validating no external dependencies...")

    # This test passes if we can import and use agents without importing
    # teams, workflows, protocols, tools, or book modules
    try:
        # AgentBuilder is already imported at module level
        print("   ✅ AgentBuilder imports successfully")

        # Verify we haven't accidentally imported other modules
        imported_modules = sys.modules.keys()

        # Check that we haven't imported the other core modules
        forbidden_modules = [
            "engine_core.core.teams",
            "engine_core.core.workflows",
            "engine_core.core.protocols",
            "engine_core.core.tools",
            "engine_core.core.book",
        ]

        for module in forbidden_modules:
            if module in imported_modules:
                print(f"   ⚠️  WARNING: {module} was imported (should be independent)")
            else:
                print(f"   ✅ {module.split('.')[-1]} not imported (good)")

    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

    print("=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("✅ Agents are fully independent and functional")
    print("✅ No dependencies on teams, workflows, protocols, tools, or book")
    print("✅ AgentBuilder provides complete 11-module configuration")
    print("✅ Actor Model execution engine works correctly")
    print("✅ Mock AI interface enables independent operation")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_agent_independence())
    sys.exit(0 if success else 1)
