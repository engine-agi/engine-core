# Agent Configuration Guide

This guide covers all 11 configurable modules of Engine Core agents, with detailed explanations and examples.

## Agent Builder Overview

All agents are created using the `AgentBuilder` with a fluent interface:

```python
from engine_core import AgentBuilder

agent = AgentBuilder() \
    .with_id("my_agent") \
    .with_model("claude-3.5-sonnet") \
    .with_name("My Agent") \
    .with_speciality("General Purpose") \
    .build()
```

## Core Modules (Required)

### 1. ID (`with_id`)
Unique identifier for the agent. Must be unique within a system.

```python
agent = AgentBuilder() \
    .with_id("code_reviewer")  # Required, unique identifier
    .build()
```

**Best Practices:**
- Use descriptive, URL-safe names
- Include context (e.g., `frontend_reviewer`, `api_designer`)
- Keep under 50 characters

### 2. Model (`with_model`)
AI model to power the agent. Currently supports Claude models.

```python
agent = AgentBuilder() \
    .with_id("assistant") \
    .with_model("claude-3.5-sonnet")  # Required
    .build()
```

**Supported Models:**
- `"claude-3.5-sonnet"` - Most capable model
- `"claude-3-haiku"` - Fast, lightweight
- `"claude-3-sonnet"` - Balanced performance/cost

### 3. Stack (`with_stack`)
Technology skills and competencies. Defines what the agent can do.

```python
agent = AgentBuilder() \
    .with_id("fullstack_dev") \
    .with_model("claude-3.5-sonnet") \
    .with_stack([  # Required, at least one technology
        "python",
        "javascript",
        "react",
        "fastapi",
        "postgresql",
        "testing"
    ]) \
    .build()
```

**Common Stack Items:**
- Languages: `python`, `javascript`, `typescript`, `java`, `go`
- Frameworks: `fastapi`, `django`, `react`, `vue`, `spring`
- Databases: `postgresql`, `mysql`, `mongodb`, `redis`
- Tools: `docker`, `kubernetes`, `aws`, `testing`, `ci-cd`

## Identity Modules (Recommended)

### 4. Name (`with_name`)
Human-readable name for the agent.

```python
agent = AgentBuilder() \
    .with_id("senior_dev") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["python", "architecture"]) \
    .with_name("Senior Python Developer")  # Recommended
    .build()
```

### 5. Speciality (`with_speciality`)
Specific area of expertise.

```python
agent = AgentBuilder() \
    .with_id("security_expert") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["security", "python", "cryptography"]) \
    .with_name("Security Specialist") \
    .with_speciality("Application Security & Cryptography")  # Recommended
    .build()
```

### 6. Persona (`with_persona`)
Behavioral description that guides the agent's responses.

```python
agent = AgentBuilder() \
    .with_id("mentor") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["python", "teaching"]) \
    .with_name("Code Mentor") \
    .with_speciality("Python Education") \
    .with_persona("Patient, encouraging mentor who explains concepts clearly and provides constructive feedback")  # Recommended
    .build()
```

## Integration Modules (Optional)

### 7. Tools (`with_tools`)
External tools and integrations the agent can access.

```python
agent = AgentBuilder() \
    .with_id("devops_agent") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["devops", "infrastructure"]) \
    .with_tools(["github", "docker", "kubernetes", "aws"])  # Optional
    .build()
```

**Available Tools:**
- `"github"` - GitHub API integration
- `"docker"` - Container management
- `"kubernetes"` - Orchestration
- `"aws"` - Cloud services
- `"slack"` - Communication
- `"jira"` - Project management

### 8. Protocol (`with_protocol`)
Behavior protocol that defines how the agent operates.

```python
agent = AgentBuilder() \
    .with_id("analyst") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["analysis", "python"]) \
    .with_protocol("analysis_first")  # Optional
    .build()
```

**Built-in Protocols:**
- `"analysis_first"` - Always analyze before acting
- `"implementation_focused"` - Jump straight to solutions
- `"teaching_mode"` - Explain concepts thoroughly
- `"review_mode"` - Focus on quality and best practices

### 9. Workflow (`with_workflow`)
Default workflow template for this agent.

```python
agent = AgentBuilder() \
    .with_id("tester") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["testing", "python"]) \
    .with_workflow("tdd_workflow")  # Optional
    .build()
```

**Built-in Workflows:**
- `"tdd_workflow"` - Test-Driven Development
- `"agile_workflow"` - Agile development process
- `"research_workflow"` - Research and analysis
- `"review_workflow"` - Code review process

## Memory & Organization (Optional)

### 10. Book (`with_book`)
Memory system for persistent knowledge and context.

```python
agent = AgentBuilder() \
    .with_id("researcher") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["research", "analysis"]) \
    .with_book("research_memory")  # Optional
    .build()
```

**Book Types:**
- `"project_memory"` - Project-specific knowledge
- `"domain_memory"` - Domain expertise
- `"personal_memory"` - Agent's own learning
- `"shared_memory"` - Team-shared knowledge

### 11. Team (`with_team`)
Default team membership for this agent.

```python
agent = AgentBuilder() \
    .with_id("frontend_dev") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["javascript", "react"]) \
    .with_team("frontend_team")  # Optional
    .build()
```

## Complete Configuration Examples

### Minimal Agent (3 required modules)

```python
minimal_agent = AgentBuilder() \
    .with_id("basic_agent") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["general"]) \
    .build()
```

### Full-Featured Agent (All 11 modules)

```python
full_agent = AgentBuilder() \
    .with_id("senior_architect") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Senior System Architect") \
    .with_speciality("Enterprise System Architecture") \
    .with_persona("Experienced architect who designs scalable, maintainable systems with focus on business value") \
    .with_stack([
        "system-architecture",
        "scalability",
        "microservices",
        "cloud-architecture",
        "security",
        "performance"
    ]) \
    .with_tools(["aws", "kubernetes", "terraform", "github"]) \
    .with_protocol("analysis_first") \
    .with_workflow("architecture_workflow") \
    .with_book("architecture_patterns") \
    .with_team("architecture_team") \
    .build()
```

### Specialized Agents

#### Code Reviewer
```python
code_reviewer = AgentBuilder() \
    .with_id("code_reviewer") \
    .with_model("claude-3.5-sonnet") \
    .with_name("Senior Code Reviewer") \
    .with_speciality("Code Quality & Best Practices") \
    .with_persona("Meticulous reviewer who ensures code quality, security, and maintainability") \
    .with_stack(["python", "javascript", "code-quality", "security", "testing"]) \
    .with_tools(["github", "eslint", "pytest"]) \
    .with_protocol("review_mode") \
    .with_workflow("review_workflow") \
    .build()
```

#### DevOps Engineer
```python
devops_agent = AgentBuilder() \
    .with_id("devops_engineer") \
    .with_model("claude-3.5-sonnet") \
    .with_name("DevOps Engineer") \
    .with_speciality("Infrastructure & Deployment") \
    .with_persona("Infrastructure expert who automates deployment and ensures system reliability") \
    .with_stack(["docker", "kubernetes", "aws", "terraform", "ci-cd", "monitoring"]) \
    .with_tools(["docker", "kubernetes", "aws-cli", "terraform"]) \
    .with_protocol("implementation_focused") \
    .with_workflow("devops_workflow") \
    .build()
```

#### QA Engineer
```python
qa_engineer = AgentBuilder() \
    .with_id("qa_engineer") \
    .with_model("claude-3.5-sonnet") \
    .with_name("QA Engineer") \
    .with_speciality("Quality Assurance & Testing") \
    .with_persona("Detail-oriented tester who finds bugs and ensures software quality") \
    .with_stack(["testing", "automation", "performance", "security-testing"]) \
    .with_tools(["selenium", "pytest", "jmeter", "owasp"]) \
    .with_protocol("analysis_first") \
    .with_workflow("testing_workflow") \
    .build()
```

## Configuration Best Practices

### 1. Start Minimal, Add as Needed
```python
# Start with basics
agent = AgentBuilder() \
    .with_id("basic_agent") \
    .with_model("claude-3.5-sonnet") \
    .with_stack(["general"]) \
    .build()

# Add more configuration as requirements grow
agent = agent.with_name("Enhanced Agent").with_speciality("General Tasks")
```

### 2. Use Descriptive IDs and Names
```python
# Good
agent = AgentBuilder() \
    .with_id("frontend_react_developer") \
    .with_name("React Frontend Developer") \
    .build()

# Avoid
agent = AgentBuilder() \
    .with_id("agent1") \
    .with_name("Agent") \
    .build()
```

### 3. Stack Should Match Capabilities
```python
# Good - stack matches what the agent can actually do
developer = AgentBuilder() \
    .with_id("python_developer") \
    .with_stack(["python", "fastapi", "sqlalchemy", "testing"]) \
    .build()

# Avoid - stack doesn't match agent capabilities
developer = AgentBuilder() \
    .with_id("python_developer") \
    .with_stack(["python", "react", "kubernetes", "machine-learning"]) \
    .build()
```

### 4. Persona Guides Behavior
```python
# Good - persona provides clear behavioral guidance
mentor = AgentBuilder() \
    .with_persona("Patient teacher who explains concepts step-by-step and encourages questions") \
    .build()

# Avoid - too vague
agent = AgentBuilder() \
    .with_persona("helpful") \
    .build()
```

## Validation and Error Handling

Engine Core validates agent configurations:

```python
try:
    agent = AgentBuilder() \
        .with_id("invalid_agent") \
        .with_model("invalid-model") \
        .build()
except ValueError as e:
    print(f"Configuration error: {e}")
```

Common validation errors:
- Missing required modules (id, model, stack)
- Invalid model names
- Empty stack arrays
- Malformed tool names

## Next Steps

- **[Team Coordination](team-coordination.md)** - Working with multiple agents
- **[Workflow Design](workflow-design.md)** - Orchestrating complex processes
- **[Tool Integration](tool-integration.md)** - Connecting external services
- **[Protocol System](protocol-system.md)** - Customizing agent behavior