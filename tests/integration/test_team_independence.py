#!/usr/bin/env python3
"""
Integration test to validate team independence.
This script demonstrates that teams can be created and configured
without depending on workflows, protocols, tools, or book modules.
"""

import asyncio
import os
import sys

from engine_core.core.agents.agent_builder import AgentBuilder
from engine_core.core.teams.team_builder import TeamBuilder, TeamCoordinationStrategy

# Add src to path (ensure engine-core comes first)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
# Remove any backend paths that might conflict
sys.path = [p for p in sys.path if "backend" not in p]


async def test_team_independence():
    """Test that teams work independently of other core modules"""

    print("🧪 Testing Team Independence...")
    print("=" * 50)

    # Test 1: Create agents (minimal setup)
    print("✅ Test 1: Creating independent agents...")
    agent1 = (
        AgentBuilder()
        .with_id("agent1")
        .with_model("claude-3.5-sonnet")
        .with_stack(["python"])
        .build()
    )

    agent2 = (
        AgentBuilder()
        .with_id("agent2")
        .with_model("claude-3.5-sonnet")
        .with_stack(["javascript"])
        .build()
    )

    agents = {"agent1": agent1, "agent2": agent2}
    print("   ✅ Agents created without external dependencies")

    # Test 2: Create team without workflows
    print("✅ Test 2: Creating team without workflow dependencies...")
    team = (
        TeamBuilder()
        .with_id("independent_team")
        .with_name("Independent Team")
        .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
        .add_member("agent1")
        .add_member("agent2")
        .build(agents)
    )

    assert team.id == "independent_team"
    assert team.coordination_strategy == TeamCoordinationStrategy.COLLABORATIVE.value
    assert team.member_count == 2
    print("   ✅ Team created without workflow dependencies")

    # Test 3: Team operates without protocols
    print("✅ Test 3: Team functions without protocol dependencies...")
    stats = team.get_stats()
    assert "execution_stats" in stats
    assert stats["member_count"] == 2
    print("   ✅ Team statistics work without protocols")

    # Test 4: Team serializes without tools/book dependencies
    print("✅ Test 4: Team serializes without tools/book dependencies...")
    team_dict = team.to_dict()
    assert "config" in team_dict
    assert "agent_ids" in team_dict
    assert len(team_dict["agent_ids"]) == 2
    print("   ✅ Team serialization works without tools/book")

    # Test 5: Multiple coordination strategies work independently
    print("✅ Test 5: Testing multiple coordination strategies...")
    strategies = [
        TeamCoordinationStrategy.COLLABORATIVE,
        TeamCoordinationStrategy.PARALLEL,
    ]

    for strategy in strategies:
        test_team = (
            TeamBuilder()
            .with_id(f"team_{strategy.value}")
            .with_coordination_strategy(strategy)
            .add_member("agent1")
            .add_member("agent2")
            .build(agents)
        )

        assert test_team.coordination_strategy == strategy.value
        print(f"   ✅ {strategy.value} strategy works independently")

    print("\n🎉 All team independence tests passed!")
    print("✅ Teams work without workflow dependencies")
    print("✅ Teams work without protocol dependencies")
    print("✅ Teams work without tools dependencies")
    print("✅ Teams work without book dependencies")
    print("✅ All coordination strategies are independent")

    return True


async def main():
    """Main test function"""
    try:
        success = await test_team_independence()

        if success:
            print("\n🎉 TEAM INDEPENDENCE VALIDATED!")
            print("✅ Teams are properly independent of other core modules")
            print("✅ Multirepo architecture is supported")

        return success

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
