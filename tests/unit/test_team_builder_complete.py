"""
Unit tests for TeamBuilder - Complete Team System
"""

import os

# Import the classes we need to test
import sys
from unittest.mock import MagicMock

import pytest

from engine_core.core.teams.team_builder import (
    BuiltTeam,
    CollaborativeStrategy,
    CoordinationStrategy,
    HierarchicalStrategy,
    ParallelStrategy,
    TeamBuilder,
    TeamCoordinationStrategy,
    TeamExecutionContext,
    TeamExecutionEngine,
    TeamExecutionMode,
    TeamMember,
    TeamMemberRole,
    TeamState,
    TeamTask,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

# Import agent classes for integration (optional)
# from engine_core.core.agents.agent_builder import (
#     AgentBuilder,
#     BuiltAgent,
#     AgentExecutionContext as AgentExecContext
# )

# Define mock classes for testing
BuiltAgent = MagicMock


class TestTeamBuilderMinimal:
    """Test TeamBuilder with minimal configuration"""

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
        assert team.name is None  # Name defaults to None when not specified
        assert (
            team.coordination_strategy == TeamCoordinationStrategy.COLLABORATIVE.value
        )
        assert team.member_count == 1

    def test_team_with_name(self):
        """Test team with custom name"""
        team = (
            TeamBuilder()
            .with_id("test_team")
            .with_name("My Test Team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1")
            .build()
        )

        assert team.name == "My Test Team"

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


class TestTeamBuilderConfiguration:
    """Test TeamBuilder configuration methods"""

    def test_coordination_strategies(self):
        """Test all coordination strategies"""
        strategies = [
            TeamCoordinationStrategy.COLLABORATIVE,
            TeamCoordinationStrategy.PARALLEL,
        ]

        for strategy in strategies:
            team = (
                TeamBuilder()
                .with_id(f"team_{strategy.value}")
                .with_coordination_strategy(strategy)
                .add_member("agent1")
                .build()
            )

            assert team.coordination_strategy == strategy.value

    def test_execution_modes(self):
        """Test execution modes"""
        modes = [
            TeamExecutionMode.SYNCHRONOUS,
            TeamExecutionMode.ASYNCHRONOUS,
            TeamExecutionMode.MIXED,
        ]

        for mode in modes:
            team = (
                TeamBuilder()
                .with_id(f"team_{mode.value}")
                .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
                .with_execution_mode(mode)
                .add_member("agent1")
                .build()
            )

            assert team.config["execution_mode"] == mode.value

    def test_member_roles(self):
        """Test member roles"""
        roles = [
            TeamMemberRole.LEADER,
            TeamMemberRole.MEMBER,
            TeamMemberRole.REVIEWER,
            TeamMemberRole.COORDINATOR,
            TeamMemberRole.SPECIALIST,
        ]

        for role in roles:
            team = (
                TeamBuilder()
                .with_id(f"team_{role.value}")
                .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
                .add_member("agent1", role=role)
                .build()
            )

            members = team.config["members"]
            assert len(members) == 1
            assert members[0]["role"] == role.value

    def test_member_capabilities(self):
        """Test member capabilities"""
        capabilities = ["python", "javascript", "testing"]

        team = (
            TeamBuilder()
            .with_id("capability_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1", capabilities=capabilities)
            .build()
        )

        members = team.config["members"]
        assert members[0]["capabilities"] == capabilities

    def test_member_priority(self):
        """Test member priority"""
        team = (
            TeamBuilder()
            .with_id("priority_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1", priority=5)
            .add_member("agent2", priority=1)
            .build()
        )

        members = team.config["members"]
        assert members[0]["priority"] == 5
        assert members[1]["priority"] == 1

    def test_max_concurrent_tasks(self):
        """Test max concurrent tasks"""
        team = (
            TeamBuilder()
            .with_id("concurrent_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1", max_concurrent_tasks=3)
            .build()
        )

        members = team.config["members"]
        assert members[0]["max_concurrent_tasks"] == 3


class TestTeamBuilderValidation:
    """Test TeamBuilder validation"""

    def test_hierarchical_requires_leader(self):
        """Test that hierarchical strategy requires a leader"""
        builder = (
            TeamBuilder()
            .with_id("hierarchical_team")
            .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL)
            .add_member("agent1", role=TeamMemberRole.MEMBER)
            .add_member("agent2", role=TeamMemberRole.MEMBER)
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
            .add_member("agent1")
            .add_member("agent1")
        )  # Duplicate

        with pytest.raises(ValueError, match="Agent IDs must be unique within team"):
            builder.build()

    def test_validation_error_collection(self):
        """Test that multiple validation errors are collected"""
        builder = TeamBuilder()  # No ID, no members

        assert not builder.validate()
        errors = builder.get_validation_errors()

        assert len(errors) >= 2  # Should have at least ID and members errors
        assert any("Team ID is required" in error for error in errors)
        assert any("Team must have at least one member" in error for error in errors)


class TestTeamBuilderConvenienceMethods:
    """Test TeamBuilder convenience methods"""

    def test_add_leader_convenience(self):
        """Test add_leader convenience method"""
        team = (
            TeamBuilder().with_id("convenience_team").add_leader("leader_agent").build()
        )

        members = team.config["members"]
        assert len(members) == 1
        assert members[0]["role"] == TeamMemberRole.LEADER.value
        assert members[0]["priority"] == 0  # Leader gets highest priority

    def test_add_reviewer_convenience(self):
        """Test add_reviewer convenience method"""
        team = (
            TeamBuilder()
            .with_id("reviewer_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_reviewer("reviewer_agent")
            .build()
        )

        members = team.config["members"]
        assert len(members) == 1
        assert members[0]["role"] == TeamMemberRole.REVIEWER.value


class TestTeamBuilderFactoryMethods:
    """Test TeamBuilder factory methods"""

    def test_development_team_factory(self):
        """Test development team factory"""
        builder = TeamBuilder.development_team(
            team_id="dev_team", leader_id="lead_dev", member_ids=["dev1", "dev2"]
        )

        team = builder.build()

        assert team.id == "dev_team"
        assert team.name == "Development Team"
        assert team.coordination_strategy == TeamCoordinationStrategy.HIERARCHICAL.value

        members = team.config["members"]
        assert len(members) == 3

        # Check leader
        leader = next(m for m in members if m["agent_id"] == "lead_dev")
        assert leader["role"] == TeamMemberRole.LEADER.value
        assert "leadership" in leader["capabilities"]

        # Check members
        member1 = next(m for m in members if m["agent_id"] == "dev1")
        assert member1["role"] == TeamMemberRole.MEMBER.value
        assert "programming" in member1["capabilities"]

    def test_analysis_team_factory(self):
        """Test analysis team factory"""
        builder = TeamBuilder.analysis_team(
            team_id="analysis_team", analyst_ids=["analyst1", "analyst2"]
        )

        team = builder.build()

        assert team.id == "analysis_team"
        assert team.name == "Analysis Team"
        assert (
            team.coordination_strategy == TeamCoordinationStrategy.COLLABORATIVE.value
        )

        members = team.config["members"]
        assert len(members) == 2

        for member in members:
            assert member["role"] == TeamMemberRole.MEMBER.value
            assert "data_analysis" in member["capabilities"]

    def test_parallel_processing_team_factory(self):
        """Test parallel processing team factory"""
        builder = TeamBuilder.parallel_processing_team(
            team_id="parallel_team", processor_ids=["proc1", "proc2"]
        )

        team = builder.build()

        assert team.id == "parallel_team"
        assert team.name == "Parallel Processing Team"
        assert team.coordination_strategy == TeamCoordinationStrategy.PARALLEL.value
        assert team.config["execution_mode"] == TeamExecutionMode.ASYNCHRONOUS.value

        members = team.config["members"]
        assert len(members) == 2

        for member in members:
            assert member["role"] == TeamMemberRole.MEMBER.value
            assert member["max_concurrent_tasks"] == 3


class TestBuiltTeam:
    """Test BuiltTeam functionality"""

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
        assert "created_at" in stats
        assert "execution_stats" in stats

    def test_built_team_to_dict(self):
        """Test BuiltTeam serialization"""
        team = (
            TeamBuilder()
            .with_id("dict_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1")
            .build()
        )

        team_dict = team.to_dict()

        assert "config" in team_dict
        assert "agent_ids" in team_dict
        assert "stats" in team_dict
        assert "created_at" in team_dict

    def test_add_agent_to_team(self):
        """Test adding agents to built team"""
        team = (
            TeamBuilder()
            .with_id("add_agent_team")
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
            .add_member("agent1")
            .build()
        )

        # Create mock agent
        mock_agent = MagicMock(spec=BuiltAgent)
        mock_agent.id = "agent1"

        team.add_agent("agent1", mock_agent)

        assert "agent1" in team.agents
        assert team.agents["agent1"] == mock_agent


class TestTeamExecutionEngine:
    """Test TeamExecutionEngine functionality"""

    def test_execution_engine_creation(self):
        """Test TeamExecutionEngine instantiation"""
        config = {
            "id": "engine_team",
            "coordination_strategy": TeamCoordinationStrategy.HIERARCHICAL.value,
            "members": [{"agent_id": "agent1", "role": "leader"}],
        }

        agents = {}
        engine = TeamExecutionEngine(config, agents)

        assert engine.team_config == config
        assert engine.agents == agents
        assert engine.state == TeamState.IDLE
        assert len(engine.members) == 1

    def test_execution_engine_member_loading(self):
        """Test loading team members"""
        config = {
            "id": "member_team",
            "coordination_strategy": TeamCoordinationStrategy.HIERARCHICAL.value,
            "members": [
                {
                    "agent_id": "leader_agent",
                    "role": "leader",
                    "capabilities": ["leadership"],
                    "priority": 0,
                },
                {
                    "agent_id": "member_agent",
                    "role": "member",
                    "capabilities": ["coding"],
                    "priority": 1,
                },
            ],
        }

        agents = {}
        engine = TeamExecutionEngine(config, agents)

        assert len(engine.members) == 2

        leader = next(m for m in engine.members if m.agent_id == "leader_agent")
        assert leader.role == TeamMemberRole.LEADER
        assert "leadership" in leader.capabilities

        member = next(m for m in engine.members if m.agent_id == "member_agent")
        assert member.role == TeamMemberRole.MEMBER
        assert "coding" in member.capabilities

    def test_strategy_selection(self):
        """Test coordination strategy selection"""
        strategies = {
            "hierarchical": HierarchicalStrategy,
            "collaborative": CollaborativeStrategy,
            "parallel": ParallelStrategy,
        }

        for strategy_name, strategy_class in strategies.items():
            config = {
                "id": f"{strategy_name}_team",
                "coordination_strategy": strategy_name,
                "members": [{"agent_id": "agent1", "role": "member"}],
            }

            engine = TeamExecutionEngine(config, {})
            assert isinstance(engine.coordination_strategy, strategy_class)

    def test_team_stats(self):
        """Test team statistics"""
        config = {
            "id": "stats_team",
            "coordination_strategy": "hierarchical",
            "members": [{"agent_id": "agent1", "role": "member"}],
        }

        engine = TeamExecutionEngine(config, {})

        stats = engine.get_team_stats()

        assert stats["team_id"] == "stats_team"
        assert stats["current_state"] == TeamState.IDLE.value
        assert stats["member_count"] == 1
        assert stats["coordination_strategy"] == "hierarchical"
        assert stats["execution_history"] == []


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

    def test_team_member_to_dict(self):
        """Test TeamMember serialization"""
        member = TeamMember(
            agent_id="test_agent", role=TeamMemberRole.MEMBER, capabilities=["python"]
        )

        member_dict = member.to_dict()

        assert member_dict["agent_id"] == "test_agent"
        assert member_dict["role"] == "member"
        assert member_dict["capabilities"] == ["python"]
        assert member_dict["priority"] == 1  # default
        assert member_dict["max_concurrent_tasks"] == 1  # default

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

    def test_team_execution_context_creation(self):
        """Test TeamExecutionContext creation"""
        from datetime import datetime

        context = TeamExecutionContext(
            execution_id="exec_123", project_id="proj_123", user_id="user_123"
        )

        assert context.execution_id == "exec_123"
        assert context.project_id == "proj_123"
        assert context.user_id == "user_123"
        assert isinstance(context.started_at, datetime)

    def test_team_execution_context_to_dict(self):
        """Test TeamExecutionContext serialization"""
        context = TeamExecutionContext(execution_id="exec_123", project_id="proj_123")

        context_dict = context.to_dict()

        assert context_dict["execution_id"] == "exec_123"
        assert context_dict["project_id"] == "proj_123"
        assert "started_at" in context_dict


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

    def test_task_assignment_hierarchical(self):
        """Test task assignment in hierarchical strategy"""
        members = [
            TeamMember(agent_id="leader", role=TeamMemberRole.LEADER),
            TeamMember(
                agent_id="member1", role=TeamMemberRole.MEMBER, capabilities=["python"]
            ),
            TeamMember(
                agent_id="member2",
                role=TeamMemberRole.MEMBER,
                capabilities=["javascript"],
            ),
        ]

        tasks = [
            TeamTask(id="task1", description="Python task", requirements=["python"]),
            TeamTask(id="task2", description="JS task", requirements=["javascript"]),
        ]

        strategy = HierarchicalStrategy()
        assignments = strategy.assign_tasks(tasks, members)

        # Leader should not be assigned tasks directly
        assert "leader" not in assignments or len(assignments["leader"]) == 0

        # Tasks should be assigned to capable members
        assert len(assignments) > 0

    def test_task_assignment_collaborative(self):
        """Test task assignment in collaborative strategy"""
        members = [
            TeamMember(agent_id="member1", role=TeamMemberRole.MEMBER),
            TeamMember(agent_id="member2", role=TeamMemberRole.MEMBER),
        ]

        tasks = [
            TeamTask(id="task1", description="Task 1"),
            TeamTask(id="task2", description="Task 2"),
        ]

        strategy = CollaborativeStrategy()
        assignments = strategy.assign_tasks(tasks, members)

        # All members should have assignments
        assert len(assignments) == 2
        assert all(len(tasks) > 0 for tasks in assignments.values())

    def test_task_assignment_parallel(self):
        """Test task assignment in parallel strategy"""
        members = [
            TeamMember(agent_id="member1", role=TeamMemberRole.MEMBER),
            TeamMember(agent_id="member2", role=TeamMemberRole.MEMBER),
        ]

        tasks = [
            TeamTask(id="task1", description="Task 1"),
            TeamTask(id="task2", description="Task 2"),
            TeamTask(id="task3", description="Task 3"),
            TeamTask(id="task4", description="Task 4"),
        ]

        strategy = ParallelStrategy()
        assignments = strategy.assign_tasks(tasks, members)

        # Tasks should be distributed across members
        total_assigned = sum(len(task_list) for task_list in assignments.values())
        assert total_assigned == 4
