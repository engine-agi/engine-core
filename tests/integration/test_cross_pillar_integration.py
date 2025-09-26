"""
Basic cross-pillar integration tests for Engine Core.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from engine_core.core.agents.agent_builder import AgentBuilder
from engine_core.core.teams.team_builder import (
    TeamBuilder,
    TeamCoordinationStrategy,
    TeamMemberRole,
)
from engine_core.core.workflows.workflow_builder import WorkflowBuilder


def test_basic_agent_creation():
    """Test basic agent creation."""
    agent = (
        AgentBuilder()
        .with_id("test_agent")
        .with_name("Test Agent")
        .with_model("claude-3.5-sonnet")
        .build()
    )

    assert agent.id == "test_agent"
    assert agent.name == "Test Agent"


def test_basic_team_creation():
    """Test basic team creation."""
    agent = AgentBuilder().with_id("team_agent").with_model("claude-3.5-sonnet").build()

    agents = {"team_agent": agent}

    team = (
        TeamBuilder()
        .with_id("test_team")
        .with_name("Test Team")
        .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL)
        .add_leader("team_agent")
        .build(agents)
    )

    assert team.id == "test_team"
    assert team.member_count == 1


def test_basic_workflow_creation():
    """Test basic workflow creation."""
    agent = (
        AgentBuilder().with_id("workflow_agent").with_model("claude-3.5-sonnet").build()
    )

    workflow = (
        WorkflowBuilder()
        .with_id("test_workflow")
        .with_name("Test Workflow")
        .add_agent_vertex("test_vertex", agent, "Test task")
        .build()
    )

    assert workflow.id == "test_workflow"
    assert workflow.vertex_count == 1


def test_agent_creation_performance():
    """Test performance of agent creation."""
    start_time = time.time()

    agents = []
    for i in range(10):
        agent = (
            AgentBuilder()
            .with_id(f"perf_agent_{i}")
            .with_name(f"Performance Agent {i}")
            .with_model("claude-3.5-sonnet")
            .with_stack(["python"])
            .build()
        )
        agents.append(agent)

    end_time = time.time()
    creation_time = end_time - start_time

    assert creation_time < 1.0
    assert len(agents) == 10


def test_concurrent_agent_creation():
    """Test creating agents concurrently."""

    def create_agent(index: int):
        return (
            AgentBuilder()
            .with_id(f"concurrent_agent_{index}")
            .with_model("claude-3.5-sonnet")
            .build()
        )

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(create_agent, i) for i in range(20)]
        agents = [future.result() for future in as_completed(futures)]

    end_time = time.time()
    total_time = end_time - start_time

    assert len(agents) == 20
    assert total_time < 2.0


def test_cross_pillar_agent_team_workflow_integration():
    """Test complete integration: agent + team + workflow."""
    # Create agents
    senior_agent = (
        AgentBuilder()
        .with_id("senior_dev")
        .with_model("claude-3.5-sonnet")
        .with_name("Senior Developer")
        .with_speciality("Full-Stack Development")
        .build()
    )

    junior_agent = (
        AgentBuilder()
        .with_id("junior_dev")
        .with_model("claude-3.5-sonnet")
        .with_name("Junior Developer")
        .with_speciality("Frontend Development")
        .build()
    )

    # Create team with hierarchical coordination
    team = (
        TeamBuilder()
        .with_id("dev_team")
        .with_name("Development Team")
        .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL)
        .add_leader("senior_dev")
        .add_member("junior_dev", TeamMemberRole.MEMBER, ["python", "javascript"])
        .build({"senior_dev": senior_agent, "junior_dev": junior_agent})
    )

    # Create workflow using team
    workflow = (
        WorkflowBuilder()
        .with_id("dev_pipeline")
        .with_name("Development Pipeline")
        .add_team_vertex("analysis", team, "Analyze requirements")
        .add_team_vertex("implementation", team, "Implement features")
        .add_edge("analysis", "implementation")
        .build()
    )

    # Validate integration
    assert workflow.id == "dev_pipeline"
    assert workflow.vertex_count == 2
    assert workflow.edge_count == 1
    assert team.id == "dev_team"
    assert len(team.agents) == 2
    assert team.coordination_strategy == "hierarchical"


def test_workflow_execution_simulation():
    """Test workflow execution simulation with agents and teams."""
    # Create multiple agents
    agents = []
    for i in range(3):
        agent = (
            AgentBuilder().with_id(f"agent_{i}").with_model("claude-3.5-sonnet").build()
        )
        agents.append(agent)

    # Create collaborative team
    team = (
        TeamBuilder()
        .with_id("collab_team")
        .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)
        .add_member("agent_0", TeamMemberRole.MEMBER, ["python"])
        .add_member("agent_1", TeamMemberRole.MEMBER, ["python"])
        .add_member("agent_2", TeamMemberRole.MEMBER, ["python"])
        .build({f"agent_{i}": agent for i, agent in enumerate(agents)})
    )

    # Create complex workflow
    workflow = (
        WorkflowBuilder()
        .with_id("complex_workflow")
        .add_team_vertex("planning", team, "Plan project")
        .add_team_vertex("development", team, "Develop features")
        .add_team_vertex("testing", team, "Test implementation")
        .add_team_vertex("deployment", team, "Deploy to production")
        .add_edge("planning", "development")
        .add_edge("development", "testing")
        .add_edge("testing", "deployment")
        .build()
    )

    # Validate workflow structure
    assert workflow.vertex_count == 4
    assert workflow.edge_count == 3
    assert team.coordination_strategy == "collaborative"


def test_performance_cross_pillar_operations():
    """Test performance of cross-pillar operations."""
    import time

    start_time = time.time()

    # Create multiple agents concurrently
    agents = []
    for i in range(10):
        agent = (
            AgentBuilder()
            .with_id(f"perf_agent_{i}")
            .with_model("claude-3.5-sonnet")
            .build()
        )
        agents.append(agent)

    # Create teams
    teams = []
    for i in range(3):
        team = (
            TeamBuilder()
            .with_id(f"perf_team_{i}")
            .with_coordination_strategy(TeamCoordinationStrategy.PARALLEL)
            .add_member(f"perf_agent_{i*3}", TeamMemberRole.MEMBER, ["python"])
            .add_member(f"perf_agent_{i*3+1}", TeamMemberRole.MEMBER, ["python"])
            .add_member(f"perf_agent_{i*3+2}", TeamMemberRole.MEMBER, ["python"])
            .build({f"perf_agent_{j}": agents[j] for j in range(10)})
        )
        teams.append(team)

    # Create workflows
    workflows = []
    for i, team in enumerate(teams):
        workflow = (
            WorkflowBuilder()
            .with_id(f"perf_workflow_{i}")
            .add_team_vertex("task1", team, "Task 1")
            .add_team_vertex("task2", team, "Task 2")
            .add_edge("task1", "task2")
            .build()
        )
        workflows.append(workflow)

    end_time = time.time()
    duration = end_time - start_time

    # Performance assertions
    assert duration < 2.0  # Should complete within 2 seconds
    assert len(agents) == 10
    assert len(teams) == 3
    assert len(workflows) == 3
    assert all(w.vertex_count == 2 for w in workflows)
