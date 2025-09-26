# Workflow Design Guide

This guide covers how to design and orchestrate complex workflows using Engine Core's Pregel-based workflow engine.

## Workflow Builder Overview

Workflows are created using the `WorkflowBuilder` with a fluent interface:

```python
from engine_core import WorkflowBuilder

workflow = WorkflowBuilder() \
    .with_id("my_workflow") \
    .with_name("My Workflow") \
    .add_agent_vertex("step1", agent, "Task description") \
    .add_team_vertex("step2", team, "Team task description") \
    .add_edge("step1", "step2") \
    .build()
```

## Pregel-Based Execution Model

Engine Core workflows are based on the Pregel model:

- **Vertices**: Individual tasks or processing steps
- **Edges**: Dependencies between tasks
- **Supersteps**: Parallel execution rounds
- **Messages**: Data passed between vertices

```python
# Example Pregel workflow
workflow = WorkflowBuilder() \
    .with_id("data_processing") \
    .add_vertex("ingest", agent1, "Ingest raw data") \
    .add_vertex("validate", agent2, "Validate data quality") \
    .add_vertex("transform", agent3, "Transform data") \
    .add_vertex("analyze", agent4, "Analyze results") \
    .add_edge("ingest", "validate") \
    .add_edge("validate", "transform") \
    .add_edge("transform", "analyze") \
    .build()
```

## Vertex Types

### Agent Vertices

Execute tasks with individual agents:

```python
workflow = WorkflowBuilder() \
    .with_id("agent_workflow") \
    .add_agent_vertex("research", researcher_agent, "Research the topic thoroughly") \
    .add_agent_vertex("write", writer_agent, "Write comprehensive article") \
    .add_agent_vertex("edit", editor_agent, "Edit and polish the content") \
    .add_edge("research", "write") \
    .add_edge("write", "edit") \
    .build()
```

### Team Vertices

Execute tasks with coordinated teams:

```python
workflow = WorkflowBuilder() \
    .with_id("team_workflow") \
    .add_team_vertex("design", design_team, "Design system architecture collaboratively") \
    .add_team_vertex("implement", dev_team, "Implement features in parallel") \
    .add_team_vertex("test", qa_team, "Comprehensive testing and validation") \
    .add_edge("design", "implement") \
    .add_edge("implement", "test") \
    .build()
```

### Mixed Vertices

Combine agents and teams in the same workflow:

```python
workflow = WorkflowBuilder() \
    .with_id("mixed_workflow") \
    .add_agent_vertex("plan", project_manager, "Create project plan") \
    .add_team_vertex("develop", dev_team, "Develop features") \
    .add_agent_vertex("review", tech_lead, "Technical review") \
    .add_team_vertex("test", qa_team, "Quality assurance") \
    .add_agent_vertex("deploy", devops_agent, "Deploy to production") \
    .add_edge("plan", "develop") \
    .add_edge("develop", "review") \
    .add_edge("review", "test") \
    .add_edge("test", "deploy") \
    .build()
```

## Workflow Patterns

### Sequential Workflow

Tasks execute one after another:

```python
sequential = WorkflowBuilder() \
    .with_id("sequential_workflow") \
    .add_agent_vertex("step1", agent, "First task") \
    .add_agent_vertex("step2", agent, "Second task") \
    .add_agent_vertex("step3", agent, "Third task") \
    .add_edge("step1", "step2") \
    .add_edge("step2", "step3") \
    .build()
```

### Parallel Workflow

Independent tasks execute simultaneously:

```python
parallel = WorkflowBuilder() \
    .with_id("parallel_workflow") \
    .add_agent_vertex("task1", agent1, "Task 1") \
    .add_agent_vertex("task2", agent2, "Task 2") \
    .add_agent_vertex("task3", agent3, "Task 3") \
    .add_agent_vertex("merge", agent4, "Merge results") \
    .add_edge("task1", "merge") \
    .add_edge("task2", "merge") \
    .add_edge("task3", "merge") \
    .build()
```

### Diamond Workflow

Conditional branching and merging:

```python
diamond = WorkflowBuilder() \
    .with_id("diamond_workflow") \
    .add_agent_vertex("analyze", agent, "Analyze requirements") \
    .add_agent_vertex("web", agent1, "Build web interface") \
    .add_agent_vertex("api", agent2, "Build API") \
    .add_agent_vertex("mobile", agent3, "Build mobile app") \
    .add_agent_vertex("integrate", agent4, "Integrate all components") \
    .add_edge("analyze", "web") \
    .add_edge("analyze", "api") \
    .add_edge("analyze", "mobile") \
    .add_edge("web", "integrate") \
    .add_edge("api", "integrate") \
    .add_edge("mobile", "integrate") \
    .build()
```

### Iterative Workflow

Tasks that can repeat based on conditions:

```python
iterative = WorkflowBuilder() \
    .with_id("iterative_workflow") \
    .add_agent_vertex("design", agent, "Create initial design") \
    .add_agent_vertex("review", reviewer, "Review design") \
    .add_agent_vertex("revise", agent, "Revise based on feedback") \
    .add_agent_vertex("approve", approver, "Final approval") \
    .add_edge("design", "review") \
    .add_edge("review", "revise") \
    .add_edge("review", "approve") \
    .add_edge("revise", "review")  # Loop back for revisions \
    .build()
```

## Advanced Workflow Features

### Conditional Edges

Execute different paths based on results:

```python
conditional = WorkflowBuilder() \
    .with_id("conditional_workflow") \
    .add_agent_vertex("check_quality", qa_agent, "Check code quality") \
    .add_agent_vertex("pass_path", deploy_agent, "Deploy to production") \
    .add_agent_vertex("fail_path", dev_agent, "Fix issues and retry") \
    .add_conditional_edge("check_quality", "pass_path", lambda result: result.get("quality_score", 0) > 8) \
    .add_conditional_edge("check_quality", "fail_path", lambda result: result.get("quality_score", 0) <= 8) \
    .build()
```

### Error Handling

Handle failures gracefully:

```python
robust = WorkflowBuilder() \
    .with_id("robust_workflow") \
    .add_agent_vertex("process", agent, "Process data") \
    .add_agent_vertex("success", agent, "Handle success") \
    .add_agent_vertex("error", agent, "Handle error") \
    .add_edge("process", "success") \
    .add_error_edge("process", "error") \
    .build()
```

### Timeouts and Retries

Configure execution parameters:

```python
reliable = WorkflowBuilder() \
    .with_id("reliable_workflow") \
    .add_agent_vertex("unreliable_task", agent, "Unreliable task") \
    .with_timeout(300) \
    .with_retries(3) \
    .with_retry_delay(10) \
    .build()
```

## Complete Workflow Examples

### Software Development Pipeline

```python
from engine_core import AgentBuilder, TeamBuilder, WorkflowBuilder
from engine_core.core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole

# Create agents
pm = AgentBuilder().with_id("pm").with_model("claude-3.5-sonnet").with_name("Product Manager").build()
architect = AgentBuilder().with_id("architect").with_model("claude-3.5-sonnet").with_name("Architect").build()
dev1 = AgentBuilder().with_id("dev1").with_model("claude-3.5-sonnet").with_name("Developer 1").build()
dev2 = AgentBuilder().with_id("dev2").with_model("claude-3.5-sonnet").with_name("Developer 2").build()
qa = AgentBuilder().with_id("qa").with_model("claude-3.5-sonnet").with_name("QA Engineer").build()
devops = AgentBuilder().with_id("devops").with_model("claude-3.5-sonnet").with_name("DevOps").build()

# Create teams
dev_team = TeamBuilder() \
    .with_id("dev_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.PARALLEL) \
    .add_member("dev1", TeamMemberRole.MEMBER, ["python", "backend"]) \
    .add_member("dev2", TeamMemberRole.MEMBER, ["javascript", "frontend"]) \
    .build({"dev1": dev1, "dev2": dev2})

qa_team = TeamBuilder() \
    .with_id("qa_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("qa", TeamMemberRole.MEMBER, ["testing", "automation"]) \
    .build({"qa": qa})

# Create development pipeline workflow
pipeline = WorkflowBuilder() \
    .with_id("dev_pipeline") \
    .with_name("Complete Software Development Pipeline") \
    .add_agent_vertex("requirements", pm, "Gather and analyze requirements") \
    .add_agent_vertex("architecture", architect, "Design system architecture") \
    .add_team_vertex("implementation", dev_team, "Implement features in parallel") \
    .add_team_vertex("testing", qa_team, "Comprehensive testing and validation") \
    .add_agent_vertex("deployment", devops, "Deploy to production environment") \
    .add_agent_vertex("monitoring", devops, "Setup monitoring and alerting") \
    .add_edge("requirements", "architecture") \
    .add_edge("architecture", "implementation") \
    .add_edge("implementation", "testing") \
    .add_edge("testing", "deployment") \
    .add_edge("deployment", "monitoring") \
    .build()

print(f"Pipeline created with {pipeline.vertex_count} steps")
```

### Research and Analysis Workflow

```python
# Create research agents
researcher = AgentBuilder().with_id("researcher").with_model("claude-3.5-sonnet").with_name("Researcher").build()
analyst = AgentBuilder().with_id("analyst").with_model("claude-3.5-sonnet").with_name("Data Analyst").build()
writer = AgentBuilder().with_id("writer").with_model("claude-3.5-sonnet").with_name("Technical Writer").build()

# Create research team
research_team = TeamBuilder() \
    .with_id("research_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("researcher", TeamMemberRole.MEMBER, ["research", "literature"]) \
    .add_member("analyst", TeamMemberRole.MEMBER, ["analysis", "statistics"]) \
    .add_member("writer", TeamMemberRole.MEMBER, ["writing", "documentation"]) \
    .build({"researcher": researcher, "analyst": analyst, "writer": writer})

# Create research workflow
research_workflow = WorkflowBuilder() \
    .with_id("research_workflow") \
    .with_name("Research and Publication Workflow") \
    .add_team_vertex("literature_review", research_team, "Conduct comprehensive literature review") \
    .add_team_vertex("data_collection", research_team, "Collect and prepare data") \
    .add_team_vertex("analysis", research_team, "Perform statistical analysis") \
    .add_team_vertex("interpretation", research_team, "Interpret results and draw conclusions") \
    .add_team_vertex("writing", research_team, "Write research paper") \
    .add_team_vertex("peer_review", research_team, "Internal peer review") \
    .add_team_vertex("revision", research_team, "Revise based on feedback") \
    .add_team_vertex("publication", research_team, "Prepare for publication") \
    .add_edge("literature_review", "data_collection") \
    .add_edge("data_collection", "analysis") \
    .add_edge("analysis", "interpretation") \
    .add_edge("interpretation", "writing") \
    .add_edge("writing", "peer_review") \
    .add_edge("peer_review", "revision") \
    .add_edge("revision", "publication") \
    .build()
```

### E-commerce Platform Development

```python
# Create specialized agents
ux_designer = AgentBuilder().with_id("ux").with_model("claude-3.5-sonnet").with_name("UX Designer").build()
ui_designer = AgentBuilder().with_id("ui").with_model("claude-3.5-sonnet").with_name("UI Designer").build()
backend_dev = AgentBuilder().with_id("backend").with_model("claude-3.5-sonnet").with_name("Backend Developer").build()
frontend_dev = AgentBuilder().with_id("frontend").with_model("claude-3.5-sonnet").with_name("Frontend Developer").build()
fullstack_dev = AgentBuilder().with_id("fullstack").with_model("claude-3.5-sonnet").with_name("Full-Stack Developer").build()

# Create teams
design_team = TeamBuilder() \
    .with_id("design_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("ux", TeamMemberRole.MEMBER, ["ux", "user-research"]) \
    .add_member("ui", TeamMemberRole.MEMBER, ["ui", "prototyping"]) \
    .build({"ux": ux_designer, "ui": ui_designer})

dev_team = TeamBuilder() \
    .with_id("dev_team") \
    .with_coordination_strategy(TeamCoordinationStrategy.PARALLEL) \
    .add_member("backend", TeamMemberRole.MEMBER, ["python", "fastapi", "postgresql"]) \
    .add_member("frontend", TeamMemberRole.MEMBER, ["react", "typescript", "redux"]) \
    .add_member("fullstack", TeamMemberRole.MEMBER, ["integration", "deployment"]) \
    .build({"backend": backend_dev, "frontend": frontend_dev, "fullstack": fullstack_dev})

# Create e-commerce development workflow
ecommerce_workflow = WorkflowBuilder() \
    .with_id("ecommerce_development") \
    .with_name("E-commerce Platform Development") \
    .add_team_vertex("market_research", design_team, "Research market and user needs") \
    .add_team_vertex("design", design_team, "Create UX/UI designs and prototypes") \
    .add_team_vertex("backend_api", dev_team, "Build REST API and database") \
    .add_team_vertex("frontend_app", dev_team, "Build React frontend application") \
    .add_team_vertex("payment_integration", dev_team, "Integrate payment processing") \
    .add_team_vertex("testing", dev_team, "End-to-end testing and validation") \
    .add_team_vertex("deployment", dev_team, "Production deployment and monitoring") \
    .add_edge("market_research", "design") \
    .add_edge("design", "backend_api") \
    .add_edge("design", "frontend_app") \
    .add_edge("backend_api", "payment_integration") \
    .add_edge("frontend_app", "payment_integration") \
    .add_edge("payment_integration", "testing") \
    .add_edge("testing", "deployment") \
    .build()
```

## Workflow Execution

### Synchronous Execution

```python
# Execute workflow synchronously
result = workflow.execute(context)
print(f"Workflow completed: {result}")
```

### Asynchronous Execution

```python
import asyncio

async def main():
    # Execute workflow asynchronously
    result = await workflow.execute_async(context)
    print(f"Async workflow completed: {result}")

asyncio.run(main())
```

### Execution with Callbacks

```python
def on_step_complete(step_id, result):
    print(f"Step {step_id} completed: {result}")

def on_workflow_complete(final_result):
    print(f"Workflow finished: {final_result}")

# Execute with progress callbacks
result = workflow.execute_with_callbacks(
    context,
    on_step_complete=on_step_complete,
    on_complete=on_workflow_complete
)
```

## Monitoring and Debugging

### Workflow Status

```python
# Check workflow status
print(f"Workflow ID: {workflow.id}")
print(f"Vertices: {workflow.vertex_count}")
print(f"Edges: {workflow.edge_count}")
print(f"Status: {workflow.status}")

# Get execution history
history = workflow.get_execution_history()
for step in history:
    print(f"Step {step['id']}: {step['status']} ({step['duration']}s)")
```

### Error Handling

```python
try:
    result = await workflow.execute_async(context)
except WorkflowExecutionError as e:
    print(f"Workflow failed: {e}")
    print(f"Failed step: {e.failed_step}")
    print(f"Error details: {e.details}")

    # Retry from failed step
    result = await workflow.retry_from_step(e.failed_step)
```

### Performance Monitoring

```python
# Get performance metrics
metrics = workflow.get_performance_metrics()
print(f"Total execution time: {metrics['total_time']}s")
print(f"Average step time: {metrics['avg_step_time']}s")
print(f"Parallelization factor: {metrics['parallelization']}")

# Identify bottlenecks
bottlenecks = workflow.identify_bottlenecks()
for step_id, duration in bottlenecks:
    print(f"Bottleneck: {step_id} took {duration}s")
```

## Best Practices

### 1. Design for Parallelism

```python
# Good - maximizes parallelism
parallel_workflow = WorkflowBuilder() \
    .add_vertex("task1", agent1, "Independent task 1") \
    .add_vertex("task2", agent2, "Independent task 2") \
    .add_vertex("merge", agent3, "Merge results") \
    .add_edge("task1", "merge") \
    .add_edge("task2", "merge") \
    .build()

# Avoid - unnecessary sequential dependencies
sequential_workflow = WorkflowBuilder() \
    .add_vertex("task1", agent1, "Task 1") \
    .add_vertex("task2", agent1, "Task 2 (could be parallel)") \
    .add_edge("task1", "task2") \
    .build()
```

### 2. Handle Errors Gracefully

```python
# Good - error handling and retries
robust_workflow = WorkflowBuilder() \
    .add_vertex("unreliable_task", agent, "May fail") \
    .add_vertex("error_handler", agent, "Handle errors") \
    .add_edge("unreliable_task", "error_handler") \
    .with_timeout(300) \
    .with_retries(3) \
    .build()
```

### 3. Monitor Performance

```python
# Good - performance monitoring
monitored_workflow = WorkflowBuilder() \
    .add_vertex("performance_critical", agent, "Critical task") \
    .with_timeout(60) \
    .with_metrics_enabled(True) \
    .build()

# Check performance after execution
if monitored_workflow.execution_time > 300:
    print("Workflow is running slow, consider optimization")
```

### 4. Use Appropriate Team Sizes

```python
# Good - right-sized teams
small_team = TeamBuilder().with_strategy(TeamCoordinationStrategy.COLLABORATIVE) \
    .add_member("agent1", TeamMemberRole.MEMBER) \
    .add_member("agent2", TeamMemberRole.MEMBER) \
    .build()  # Good for collaboration

large_team = TeamBuilder().with_strategy(TeamCoordinationStrategy.PARALLEL) \
    .add_member("agent1", TeamMemberRole.MEMBER) \
    .add_member("agent2", TeamMemberRole.MEMBER) \
    .add_member("agent3", TeamMemberRole.MEMBER) \
    .add_member("agent4", TeamMemberRole.MEMBER) \
    .build()  # Good for parallel work
```

## Common Patterns

### Map-Reduce Pattern

```python
map_reduce = WorkflowBuilder() \
    .with_id("map_reduce") \
    .add_vertex("split", agent, "Split data into chunks") \
    .add_vertex("map1", agent1, "Process chunk 1") \
    .add_vertex("map2", agent2, "Process chunk 2") \
    .add_vertex("map3", agent3, "Process chunk 3") \
    .add_vertex("reduce", agent4, "Combine results") \
    .add_edge("split", "map1") \
    .add_edge("split", "map2") \
    .add_edge("split", "map3") \
    .add_edge("map1", "reduce") \
    .add_edge("map2", "reduce") \
    .add_edge("map3", "reduce") \
    .build()
```

### Event-Driven Pattern

```python
event_driven = WorkflowBuilder() \
    .with_id("event_driven") \
    .add_vertex("listen", agent, "Listen for events") \
    .add_vertex("process_event", agent, "Process event") \
    .add_vertex("update_state", agent, "Update system state") \
    .add_edge("listen", "process_event") \
    .add_edge("process_event", "update_state") \
    .add_edge("update_state", "listen")  # Loop back \
    .build()
```

### Saga Pattern

```python
saga = WorkflowBuilder() \
    .with_id("saga_pattern") \
    .add_vertex("step1", agent, "Execute step 1") \
    .add_vertex("step2", agent, "Execute step 2") \
    .add_vertex("step3", agent, "Execute step 3") \
    .add_vertex("compensate2", agent, "Undo step 2") \
    .add_vertex("compensate1", agent, "Undo step 1") \
    .add_edge("step1", "step2") \
    .add_edge("step2", "step3") \
    .add_conditional_edge("step3", "compensate2", lambda r: r.get("failed")) \
    .add_edge("compensate2", "compensate1") \
    .build()
```

## Next Steps

- **[Tool Integration](tool-integration.md)** - Connect workflows to external services
- **[Protocol System](protocol-system.md)** - Customize agent behavior in workflows
- **[Memory Management](memory-management.md)** - Persistent workflow state
- **[API Reference](api-reference.md)** - Complete API documentation
