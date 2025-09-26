"""
Unit tests for TeamBuilder - Essential Tests
"""

import os

# Import the classes we need to test
import sys

import pytest

from engine_core.core.teams.team_builder import (
    BuiltTeam,
    CollaborativeStrategy,
    CoordinationStrategy,
    HierarchicalStrategy,
    ParallelStrategy,
    TeamBuilder,
    TeamCoordinationStrategy,
    TeamMember,
    TeamMemberRole,
    TeamTask,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


class TestTeamBuilderEssential:
    """Essential TeamBuilder tests"""

    def test_team_builder_creation(self):
        """Test that TeamBuilder can be instantiated"""
        builder = TeamBuilder()
        assert builder is not None
        assert isinstance(builder, TeamBuilder)

    def test_minimal_team_build(self):
        """Test building a team with minimal required fields"""
        team = (
            TeamBuilder()
            .with_id("test_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1")
            .build()
        )

        assert team is not None
        assert isinstance(team, BuiltTeam)
        assert team.id == "test_team"
        assert (
            team.coordination_strategy == TeamCoordinationStrategy.COLLABORATIVE.value
        )
        assert team.member_count == 1

    def test_team_validation_fails_without_id(self):
        """Test that team validation fails without ID"""
        builder = TeamBuilder().add_member("agent1")

        with pytest.raises(ValueError, match="Team ID is required"):
            builder.build()

    def test_team_validation_fails_without_members(self):
        """Test that team validation fails without members"""
        builder = TeamBuilder().with_id("test_team")

        with pytest.raises(ValueError, match="Team must have at least one member"):
            builder.build()

    def test_hierarchical_requires_leader(self):
        """Test that hierarchical strategy requires a leader"""
        builder = (
            TeamBuilder()
            .with_id("hierarchical_team")
            .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL)
            .add_member("agent1", role=TeamMemberRole.MEMBER)
        )

        with pytest.raises(
            ValueError, match="Hierarchical strategy requires a team leader"
        ):
            builder.build()

    def test_hierarchical_with_leader_valid(self):
        """Test that hierarchical strategy with leader is valid"""
        team = (
            TeamBuilder()
            .with_id("hierarchical_team")
            .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL)
            .add_leader("leader_agent")
            .add_member("agent1")
            .build()
        )

        assert team is not None

    def test_unique_agent_ids(self):
        """Test that agent IDs must be unique"""
        builder = (
            TeamBuilder()
            .with_id("duplicate_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1")
            .add_member("agent1")
        )  # Duplicate

        with pytest.raises(ValueError, match="Agent IDs must be unique within team"):
            builder.build()


class TestBuiltTeamEssential:
    """Essential BuiltTeam tests"""

    def test_built_team_properties(self):
        """Test BuiltTeam property access"""
        team = (
            TeamBuilder()
            .with_id("built_team")
            .with_name("Built Team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1")
            .build()
        )

        assert team.id == "built_team"
        assert team.name == "Built Team"
        assert team.member_count == 1

    def test_built_team_stats(self):
        """Test BuiltTeam statistics"""
        team = (
            TeamBuilder()
            .with_id("stats_team")
            .with_name("Stats Team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1")
            .add_member("agent2")
            .build()
        )

        stats = team.get_stats()

        assert stats["team_id"] == "stats_team"
        assert stats["team_name"] == "Stats Team"
        assert (
            stats["coordination_strategy"]
            == TeamCoordinationStrategy.COLLABORATIVE.value
        )
        assert stats["member_count"] == 2


class TestTeamDataClasses:
    """Test team data classes"""

    def test_team_member_creation(self):
        """Test TeamMember creation"""
        member = TeamMember(
            agent_id="test_agent",
            role=TeamMemberRole.LEADER,
            capabilities=["leadership", "coding"],
            priority=0,
            max_concurrent_tasks=2,
        )

        assert member.agent_id == "test_agent"
        assert member.role == TeamMemberRole.LEADER
        assert member.capabilities == ["leadership", "coding"]
        assert member.priority == 0
        assert member.max_concurrent_tasks == 2

    def test_team_task_creation(self):
        """Test TeamTask creation"""
        from datetime import datetime

        task = TeamTask(
            id="task_123",
            description="Test task",
            requirements=["python", "testing"],
            assigned_to="agent1",
            dependencies=["task_456"],
        )

        assert task.id == "task_123"
        assert task.description == "Test task"
        assert task.requirements == ["python", "testing"]
        assert task.assigned_to == "agent1"
        assert task.dependencies == ["task_456"]
        assert task.status == "pending"
        assert isinstance(task.created_at, datetime)


class TestCoordinationStrategies:
    """Test coordination strategy classes"""

    def test_hierarchical_strategy_creation(self):
        """Test HierarchicalStrategy instantiation"""
        strategy = HierarchicalStrategy()
        assert strategy is not None
        assert isinstance(strategy, CoordinationStrategy)

    def test_collaborative_strategy_creation(self):
        """Test CollaborativeStrategy instantiation"""
        strategy = CollaborativeStrategy()
        assert strategy is not None
        assert isinstance(strategy, CoordinationStrategy)

    def test_parallel_strategy_creation(self):
        """Test ParallelStrategy instantiation"""
        strategy = ParallelStrategy()
        assert strategy is not None
        assert isinstance(strategy, CoordinationStrategy)
