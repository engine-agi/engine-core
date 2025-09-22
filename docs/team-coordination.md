# Team Coordination Guide

This guide covers how to create and manage teams of agents in Engine Core, including different coordination strategies and best practices.

## Team Builder Overview

Teams are created using the `TeamBuilder` with a fluent interface:

```python
from engine_core import AgentBuilder, TeamBuilder
from engine_core.core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole

# Create agents first
agent1 = AgentBuilder().with_id("agent1").with_model("claude-3.5-sonnet").build()
agent2 = AgentBuilder().with_id("agent2").with_model("claude-3.5-sonnet").build()

# Create team
team = TeamBuilder() \
    .with_id("my_team") \
    .with_name("My Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("agent1", TeamMemberRole.MEMBER, ["skill1"]) \
    .add_member("agent2", TeamMemberRole.MEMBER, ["skill2"]) \
    .build({"agent1": agent1, "agent2": agent2})
```

## Coordination Strategies

Engine Core supports three coordination strategies:

### 1. Hierarchical Strategy

**Best for:** Structured workflows, clear leadership, complex projects

```python
hierarchical_team = TeamBuilder() \
    .with_id("dev_team") \
    .with_name("Development Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL) \
    .add_leader("senior_dev") \
    .add_member("junior_dev1", TeamMemberRole.MEMBER, ["python", "testing"]) \
    .add_member("junior_dev2", TeamMemberRole.MEMBER, ["javascript", "react"]) \
    .build(agent_dict)
```

**How it works:**
- Leader makes final decisions and coordinates work
- Members execute tasks assigned by the leader
- Clear chain of command and responsibility
- Leader can override member decisions

**Use cases:**
- Software development teams
- Project management
- Quality assurance processes

### 2. Collaborative Strategy

**Best for:** Creative work, brainstorming, peer review

```python
collaborative_team = TeamBuilder() \
    .with_id("design_team") \
    .with_name("Design Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("ux_designer", TeamMemberRole.MEMBER, ["ux", "prototyping"]) \
    .add_member("ui_designer", TeamMemberRole.MEMBER, ["ui", "branding"]) \
    .add_member("researcher", TeamMemberRole.MEMBER, ["user-research", "analytics"]) \
    .build(agent_dict)
```

**How it works:**
- All members participate equally in decision making
- Consensus-based approach
- Members can suggest, review, and modify each other's work
- No single leader - democratic process

**Use cases:**
- Design and creative work
- Research and analysis
- Brainstorming sessions
- Code review processes

### 3. Parallel Strategy

**Best for:** Independent tasks, high throughput, repetitive work

```python
parallel_team = TeamBuilder() \
    .with_id("testing_team") \
    .with_name("Testing Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.PARALLEL) \
    .add_member("unit_tester", TeamMemberRole.MEMBER, ["unit-testing"]) \
    .add_member("integration_tester", TeamMemberRole.MEMBER, ["integration-testing"]) \
    .add_member("performance_tester", TeamMemberRole.MEMBER, ["performance-testing"]) \
    .build(agent_dict)
```

**How it works:**
- Members work independently on separate tasks
- No coordination between members
- Maximum parallelism and throughput
- Results aggregated at the end

**Use cases:**
- Automated testing
- Data processing
- Batch operations
- Independent code reviews

## Team Member Roles

### Leader Role
```python
team = TeamBuilder() \
    .with_id("team") \
    .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL) \
    .add_leader("team_lead")  # Only one leader allowed
    .build(agent_dict)
```

**Responsibilities:**
- Coordinate team activities
- Make final decisions
- Assign tasks to members
- Resolve conflicts
- Ensure quality standards

### Member Role
```python
team = TeamBuilder() \
    .with_id("team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("member_id", TeamMemberRole.MEMBER, ["skill1", "skill2"])
    .build(agent_dict)
```

**Responsibilities:**
- Execute assigned tasks
- Participate in collaborative processes
- Provide feedback and suggestions
- Follow team protocols

## Skill-Based Task Assignment

Teams can assign tasks based on member skills:

```python
# Create team with diverse skills
team = TeamBuilder() \
    .with_id("fullstack_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL) \
    .add_leader("tech_lead") \
    .add_member("backend_dev", TeamMemberRole.MEMBER, ["python", "fastapi", "postgresql"]) \
    .add_member("frontend_dev", TeamMemberRole.MEMBER, ["javascript", "react", "typescript"]) \
    .add_member("devops", TeamMemberRole.MEMBER, ["docker", "kubernetes", "aws"]) \
    .build(agent_dict)

# Tasks will be routed to appropriate members based on required skills
backend_task = {"task": "Implement API endpoint", "skills": ["python", "fastapi"]}
frontend_task = {"task": "Create React component", "skills": ["javascript", "react"]}
```

## Complete Team Examples

### Software Development Team

```python
from engine_core import AgentBuilder, TeamBuilder
from engine_core.core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole

# Create specialized agents
product_manager = AgentBuilder() \
    .with_id("pm") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Product Manager") \
    .with_speciality("Product Strategy") \
    .with_stack(["product", "strategy", "requirements"]) \
    .build()

architect = AgentBuilder() \
    .with_id("architect") \
    .with_model("claude-3.5-sonnet") \
    .with_name("System Architect") \
    .with_speciality("System Design") \
    .with_stack(["architecture", "scalability", "security"]) \
    .build()

senior_dev = AgentBuilder() \
    .with_id("senior_dev") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Senior Developer") \
    .with_speciality("Full-Stack Development") \
    .with_stack(["python", "javascript", "react", "fastapi", "postgresql"]) \
    .build()

qa_engineer = AgentBuilder() \
    .with_id("qa") \
    .with_model("claude-3.5-sonnet") \
    .with_name("QA Engineer") \
    .with_speciality("Quality Assurance") \
    .with_stack(["testing", "automation", "performance"]) \
    .build()

# Create hierarchical development team
dev_team = TeamBuilder() \
    .with_id("development_team") \
    .with_name("Full-Stack Development Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL) \
    .add_leader("architect") \
    .add_member("senior_dev", TeamMemberRole.MEMBER, ["python", "javascript", "backend", "frontend"]) \
    .add_member("qa", TeamMemberRole.MEMBER, ["testing", "quality"]) \
    .build({
        "pm": product_manager,
        "architect": architect,
        "senior_dev": senior_dev,
        "qa": qa_engineer
    })

print(f"Team created: {dev_team.name}")
print(f"Strategy: {dev_team.coordination_strategy}")
print(f"Members: {dev_team.member_count}")
```

### Research Team

```python
# Create research agents
researcher1 = AgentBuilder() \
    .with_id("researcher1") \
    .with_model("claude-3.5-sonnet") \
    .with_name("AI Researcher") \
    .with_speciality("Machine Learning Research") \
    .with_stack(["machine-learning", "python", "tensorflow"]) \
    .build()

researcher2 = AgentBuilder() \
    .with_id("researcher2") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Data Scientist") \
    .with_speciality("Statistical Analysis") \
    .with_stack(["statistics", "r", "python", "pandas"]) \
    .build()

reviewer = AgentBuilder() \
    .with_id("reviewer") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Peer Reviewer") \
    .with_speciality("Academic Review") \
    .with_stack(["academic-writing", "statistics", "methodology"]) \
    .build()

# Create collaborative research team
research_team = TeamBuilder() \
    .with_id("research_team") \
    .with_name("AI Research Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("researcher1", TeamMemberRole.MEMBER, ["ml", "experiments"]) \
    .add_member("researcher2", TeamMemberRole.MEMBER, ["data-analysis", "statistics"]) \
    .add_member("reviewer", TeamMemberRole.MEMBER, ["review", "validation"]) \
    .build({
        "researcher1": researcher1,
        "researcher2": researcher2,
        "reviewer": reviewer
    })
```

### Operations Team

```python
# Create operations agents
monitor = AgentBuilder() \
    .with_id("monitor") \
    .with_model("claude-3.5-sonnet") \
    .with_name("System Monitor") \
    .with_speciality("System Monitoring") \
    .with_stack(["monitoring", "alerts", "metrics"]) \
    .build()

incident_responder = AgentBuilder() \
    .with_id("incident") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Incident Responder") \
    .with_speciality("Incident Management") \
    .with_stack(["incident-response", "troubleshooting", "communication"]) \
    .build()

capacity_planner = AgentBuilder() \
    .with_id("capacity") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Capacity Planner") \
    .with_speciality("Resource Planning") \
    .with_stack(["capacity-planning", "forecasting", "optimization"]) \
    .build()

# Create parallel operations team
ops_team = TeamBuilder() \
    .with_id("operations_team") \
    .with_name("DevOps Operations Team") \
    .with_coordination_strategy(TeamCoordinationStrategy.PARALLEL) \
    .add_member("monitor", TeamMemberRole.MEMBER, ["monitoring"]) \
    .add_member("incident", TeamMemberRole.MEMBER, ["incidents"]) \
    .add_member("capacity", TeamMemberRole.MEMBER, ["planning"]) \
    .build({
        "monitor": monitor,
        "incident": incident_responder,
        "capacity": capacity_planner
    })
```

## Team Task Execution

### Executing Tasks with Teams

```python
import asyncio
from engine_core import WorkflowBuilder

# Create workflow using team
workflow = WorkflowBuilder() \
    .with_id("project_workflow") \
    .with_name("Project Development Workflow") \
    .add_team_vertex("planning", dev_team, "Plan project scope and requirements") \
    .add_team_vertex("design", dev_team, "Design system architecture") \
    .add_team_vertex("implementation", dev_team, "Implement features") \
    .add_team_vertex("testing", dev_team, "Test and validate") \
    .add_edge("planning", "design") \
    .add_edge("design", "implementation") \
    .add_edge("implementation", "testing") \
    .build()

# Execute with team coordination
async def main():
    context = {
        "project": "E-commerce API",
        "requirements": ["REST API", "Authentication", "Product management"],
        "technologies": ["FastAPI", "PostgreSQL"]
    }

    result = await workflow.execute_async(context)
    print(f"Team workflow completed: {result}")

asyncio.run(main())
```

## Best Practices

### 1. Choose the Right Strategy

- **Hierarchical**: For complex projects needing clear leadership
- **Collaborative**: For creative work requiring input from all members
- **Parallel**: For independent tasks that can run simultaneously

### 2. Balance Team Size

- **Small teams (2-4 members)**: Better coordination, faster decisions
- **Large teams (5+ members)**: More diverse skills, but coordination overhead

### 3. Define Clear Roles

```python
# Good - clear role definitions
team = TeamBuilder() \
    .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL) \
    .add_leader("architect") \
    .add_member("backend_dev", TeamMemberRole.MEMBER, ["python", "api"]) \
    .add_member("frontend_dev", TeamMemberRole.MEMBER, ["javascript", "ui"]) \
    .build()
```

### 4. Skill-Based Assignment

```python
# Good - skills match task requirements
backend_task = {
    "task": "Implement REST API",
    "required_skills": ["python", "fastapi", "api-design"]
}

frontend_task = {
    "task": "Create user interface",
    "required_skills": ["javascript", "react", "ui-design"]
}
```

### 5. Monitor Team Performance

```python
# Track team metrics
print(f"Team size: {team.member_count}")
print(f"Active members: {len([m for m in team.members if m.is_active])}")
print(f"Completed tasks: {team.completed_tasks_count}")
print(f"Average response time: {team.avg_response_time}")
```

## Common Patterns

### Microservices Team
```python
microservices_team = TeamBuilder() \
    .with_id("microservices_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL) \
    .add_leader("tech_lead") \
    .add_member("api_gateway_dev", TeamMemberRole.MEMBER, ["gateway", "security"]) \
    .add_member("service_dev", TeamMemberRole.MEMBER, ["microservices", "docker"]) \
    .add_member("data_dev", TeamMemberRole.MEMBER, ["databases", "caching"]) \
    .build()
```

### Agile Development Team
```python
agile_team = TeamBuilder() \
    .with_id("agile_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("scrum_master", TeamMemberRole.MEMBER, ["agile", "facilitation"]) \
    .add_member("product_owner", TeamMemberRole.MEMBER, ["product", "backlog"]) \
    .add_member("developers", TeamMemberRole.MEMBER, ["development", "testing"]) \
    .build()
```

### Data Science Team
```python
data_team = TeamBuilder() \
    .with_id("data_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("data_engineer", TeamMemberRole.MEMBER, ["etl", "pipelines"]) \
    .add_member("data_scientist", TeamMemberRole.MEMBER, ["modeling", "statistics"]) \
    .add_member("ml_engineer", TeamMemberRole.MEMBER, ["deployment", "monitoring"]) \
    .build()
```

## Troubleshooting

### Common Issues

**1. Task Assignment Failures**
```python
# Problem: No team member has required skills
task = {"required_skills": ["unknown_skill"]}

# Solution: Check available skills
available_skills = [skill for member in team.members for skill in member.skills]
print(f"Available skills: {available_skills}")
```

**2. Coordination Deadlocks**
```python
# Problem: Collaborative teams can't reach consensus
# Solution: Set timeouts or fallback to hierarchical mode
team = team.with_timeout(300).with_fallback_strategy(TeamCoordinationStrategy.HIERARCHICAL)
```

**3. Performance Issues**
```python
# Problem: Large teams slow down execution
# Solution: Split into smaller sub-teams or use parallel strategy
sub_team1 = TeamBuilder().with_strategy(TeamCoordinationStrategy.PARALLEL)...
sub_team2 = TeamBuilder().with_strategy(TeamCoordinationStrategy.PARALLEL)...
```

## Next Steps

- **[Workflow Design](workflow-design.md)** - Orchestrating complex team processes
- **[Protocol System](protocol-system.md)** - Customizing team behavior
- **[Memory Management](memory-management.md)** - Team-shared knowledge
- **[Tool Integration](tool-integration.md)** - Connecting teams to external services