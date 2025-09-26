"""
Team Builder - Core Team System with Coordination Strategies.

The TeamBuilder provides a fluent interface for creating and configuring
Engine Framework teams with agent orchestration, coordination strategies,
and hierarchical management.

Based on Engine Framework Team architecture with:
- Builder Pattern for fluent configuration
- Coordination strategies (hierarchical, collaborative, parallel)
- Agent orchestration and member management
- Workflow integration and execution context
- Communication protocols and task distribution

Key Features:
- Multiple coordination strategies
- Hierarchical team structures with roles
- Agent assignment and capability matching
- Task distribution and execution monitoring
- Communication protocols between agents
- Integration with workflows and protocols
"""
import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from pydantic import Field

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ...models.agent import Agent
    from ...models.book import Book
    from ...models.protocol import Protocol
    from ...models.team import Team
    from ...models.workflow import Workflow
    # Agent system imports for type hints
    from ...core.agents.agent_builder import BuiltAgent, AgentExecutionContext
class TeamCoordinationStrategy(Enum):
    """Team coordination strategies."""
    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    EXPERT_REVIEW = "expert_review"


class TeamMemberRole(Enum):
    """Team member roles."""
    LEADER = "leader"
    MEMBER = "member"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"


class TeamExecutionMode(Enum):
    """Team execution modes."""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    MIXED = "mixed"


class TeamState(Enum):
    """Team execution states."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class TeamMember:
    """Team member configuration."""
    agent_id: str
    role: TeamMemberRole = TeamMemberRole.MEMBER
    capabilities: List[str] = field(default_factory=list)
    priority: int = 1  # 1 = highest priority
    max_concurrent_tasks: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'capabilities': self.capabilities,
            'priority': self.priority,
            'max_concurrent_tasks': self.max_concurrent_tasks,
            'metadata': self.metadata
        }


@dataclass
class TeamTask:
    """Team task definition."""
    id: str
    description: str
    requirements: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None  # agent_id
    dependencies: List[str] = field(default_factory=list)  # other task_ids
    status: str = "pending"
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'description': self.description,
            'requirements': self.requirements,
            'assigned_to': self.assigned_to,
            'dependencies': self.dependencies,
            'status': self.status,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result
        }


@dataclass
class TeamExecutionContext:
    """Context for team execution."""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parent_context: Optional['TeamExecutionContext'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'execution_id': self.execution_id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'workflow_id': self.workflow_id,
            'metadata': self.metadata,
            'started_at': self.started_at.isoformat()
        }


class CoordinationStrategy(ABC):
    """Abstract base class for team coordination strategies."""

    @abstractmethod
    async def coordinate_execution(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember],
        agents: Dict[str, Any],
        context: TeamExecutionContext
    ) -> List[TeamTask]:
        """Coordinate team execution for given tasks."""
        pass

    @abstractmethod
    def assign_tasks(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember]
    ) -> Dict[str, List[TeamTask]]:
        """Assign tasks to team members."""
        pass


class HierarchicalStrategy(CoordinationStrategy):
    """Hierarchical coordination strategy with leader-member structure."""

    async def coordinate_execution(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember],
        agents: Dict[str, Any],
        context: TeamExecutionContext
    ) -> List[TeamTask]:
        """Coordinate execution hierarchically."""

        # Find team leader
        leader = next((m for m in members if m.role == TeamMemberRole.LEADER), None)
        if not leader:
            raise ValueError("Hierarchical strategy requires a team leader")

        # Leader plans the execution
        leader_agent = agents[leader.agent_id]

        planning_message = f"""
        As team leader, plan the execution of these tasks:
        {[task.description for task in tasks]}

        Team members available:
        {[f"{m.agent_id} ({m.role.value})" for m in members]}

        Provide execution plan and task assignments.
        """

        planning_context = AgentExecutionContext(
            session_id=context.session_id,
            user_id=context.user_id,
            project_id=context.project_id,
            metadata={'phase': 'planning', 'team_coordination': 'hierarchical'}
        )

        plan_response = await leader_agent.execute(planning_message, planning_context)

        # Assign tasks based on leader's plan
        task_assignments = self.assign_tasks(tasks, members)

        # Execute tasks with hierarchy
        completed_tasks = []

        for agent_id, agent_tasks in task_assignments.items():
            if agent_id == leader.agent_id:
                continue  # Leader reviews, doesn't execute directly

            agent = agents[agent_id]

            for task in agent_tasks:
                task.assigned_to = agent_id
                task.started_at = datetime.utcnow()
                task.status = "executing"

                execution_context = AgentExecutionContext(
                    session_id=context.session_id,
                    user_id=context.user_id,
                    project_id=context.project_id,
                    metadata={
                        'task_id': task.id,
                        'coordination_strategy': 'hierarchical',
                        'assigned_by': leader.agent_id
                    }
                )

                try:
                    result = await agent.execute(task.description, execution_context)
                    task.result = result.content
                    task.status = "completed"
                    task.completed_at = datetime.utcnow()

                    # Leader reviews the result
                    review_message = f"""
                    Review this completed task:
                    Task: {task.description}
                    Result: {task.result}

                    Approve or request changes.
                    """

                    review_response = await leader_agent.execute(review_message, execution_context)

                    if "approve" in review_response.content.lower():
                        completed_tasks.append(task)
                    else:
                        task.status = "needs_revision"
                        task.result = f"Needs revision: {review_response.content}"

                except Exception as e:
                    task.status = "failed"
                    task.result = f"Error: {str(e)}"
                    task.completed_at = datetime.utcnow()

        return completed_tasks

    def assign_tasks(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember]
    ) -> Dict[str, List[TeamTask]]:
        """Assign tasks based on member capabilities and priority."""
        assignments = {member.agent_id: []
            for member in members if member.role != TeamMemberRole.LEADER}

        # Sort tasks by dependencies (simple topological sort)
        available_tasks = [t for t in tasks if not t.dependencies]

        for task in available_tasks:
            # Find best match based on capabilities
            best_member = None
            best_score = 0

            for member in members:
                if member.role == TeamMemberRole.LEADER:
                    continue

                # Calculate capability match score
                score = len(set(task.requirements) & set(member.capabilities))
                # Higher priority = lower number = higher score
                score += (10 - member.priority)

                if score > best_score:
                    best_score = score
                    best_member = member

            if best_member:
                assignments[best_member.agent_id].append(task)

        return assignments


class CollaborativeStrategy(CoordinationStrategy):
    """Collaborative coordination strategy with equal participation."""

    async def coordinate_execution(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember],
        agents: Dict[str, Any],
        context: TeamExecutionContext
    ) -> List[TeamTask]:
        """Coordinate execution collaboratively."""

        # All agents discuss the tasks first
        discussion_messages = []

        for member in members:
            agent = agents[member.agent_id]

            discussion_prompt = f"""
            Collaborate with team to plan these tasks:
            {[task.description for task in tasks]}

            Your capabilities: {member.capabilities}
            Team members: {[m.agent_id for m in members]}

            Suggest task assignments and approach.
            """

            discussion_context = AgentExecutionContext(
                session_id=context.session_id,
                user_id=context.user_id,
                project_id=context.project_id,
                metadata={'phase': 'collaboration', 'member_id': member.agent_id}
            )

            response = await agent.execute(discussion_prompt, discussion_context)
            discussion_messages.append({
                'agent_id': member.agent_id,
                'message': response.content
            })

        # Assign tasks based on collaborative discussion
        task_assignments = self.assign_tasks(tasks, members)

        # Execute with peer review
        completed_tasks = []

        for task in tasks:
            # Find assigned agent
            assigned_member = None
            for member in members:
                if task.assigned_to == member.agent_id:
                    assigned_member = member
                    break

            if not assigned_member:
                continue

            agent = agents[assigned_member.agent_id]

            task.started_at = datetime.utcnow()
            task.status = "executing"

            try:
                # Execute task
                execution_context = AgentExecutionContext(
                    session_id=context.session_id,
                    user_id=context.user_id,
                    project_id=context.project_id,
                    metadata={
    'task_id': task.id,
     'coordination_strategy': 'collaborative'}
                )

                result = await agent.execute(task.description, execution_context)
                task.result = result.content

                # Peer review from other members
                reviewers = [
    m for m in members if m.agent_id != assigned_member.agent_id]
                reviews = []

                for reviewer in reviewers[:2]:  # Limit to 2 reviewers
                    reviewer_agent = agents[reviewer.agent_id]

                    review_prompt = f"""
                    Peer review this task result:
                    Task: {task.description}
                    Result: {task.result}

                    Provide feedback and approval/rejection.
                    """

                    review_response = await reviewer_agent.execute(review_prompt, execution_context)
                    reviews.append(review_response.content)

                # Check if majority approves
                approvals = sum(1 for review in reviews if "approve" in review.lower())

                if approvals > len(reviews) / 2:
                    task.status = "completed"
                    task.completed_at = datetime.utcnow()
                    completed_tasks.append(task)
                else:
                    task.status = "needs_revision"
                    task.result = f"Peer review feedback: {'; '.join(reviews)}"

            except Exception as e:
                task.status = "failed"
                task.result = f"Error: {str(e)}"
                task.completed_at = datetime.utcnow()

        return completed_tasks

    def assign_tasks(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember]
    ) -> Dict[str, List[TeamTask]]:
        """Assign tasks based on collaborative preferences."""
        assignments = {member.agent_id: [] for member in members}

        # Round-robin assignment with capability consideration
        member_index = 0

        for task in tasks:
            # Find members with matching capabilities
            capable_members = [
                m for m in members
                if not task.requirements or set(task.requirements) & set(m.capabilities)
            ]

            if capable_members:
                # Assign to member with fewest current tasks
                member = min(capable_members,
     key=lambda m: len(assignments[m.agent_id]))
            else:
                # Fallback to round-robin
                member = members[member_index % len(members)]
                member_index += 1

            assignments[member.agent_id].append(task)
            task.assigned_to = member.agent_id

        return assignments


class ParallelStrategy(CoordinationStrategy):
    """Parallel coordination strategy for independent task execution."""

    async def coordinate_execution(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember],
        agents: Dict[str, Any],
        context: TeamExecutionContext
    ) -> List[TeamTask]:
        """Coordinate execution in parallel."""

        # Assign tasks to members
        task_assignments = self.assign_tasks(tasks, members)

        # Execute all tasks in parallel
        async def execute_agent_tasks(agent_id: str,
     agent_tasks: List[TeamTask]) -> List[TeamTask]:
            agent = agents[agent_id]
            completed = []

            # Execute tasks for this agent in parallel (up to max_concurrent_tasks)
            member = next(m for m in members if m.agent_id == agent_id)
            semaphore = asyncio.Semaphore(member.max_concurrent_tasks)

            async def execute_single_task(task: TeamTask) -> TeamTask:
                async with semaphore:
                    task.assigned_to = agent_id
                    task.started_at = datetime.utcnow()
                    task.status = "executing"

                    try:
                        execution_context = AgentExecutionContext(
                            session_id=context.session_id,
                            user_id=context.user_id,
                            project_id=context.project_id,
                            metadata={
    'task_id': task.id,
     'coordination_strategy': 'parallel'}
                        )

                        result = await agent.execute(task.description, execution_context)
                        task.result = result.content
                        task.status = "completed"
                        task.completed_at = datetime.utcnow()

                    except Exception as e:
                        task.status = "failed"
                        task.result = f"Error: {str(e)}"
                        task.completed_at = datetime.utcnow()

                    return task

            # Execute all tasks for this agent in parallel
            task_coroutines = [execute_single_task(task) for task in agent_tasks]
            completed = await asyncio.gather(*task_coroutines, return_exceptions=True)

            # Filter out exceptions
            return [task for task in completed if isinstance(task, TeamTask)]

        # Execute all agents in parallel
        agent_coroutines = [
            execute_agent_tasks(agent_id, agent_tasks)
            for agent_id, agent_tasks in task_assignments.items()
            if agent_tasks
        ]

        results = await asyncio.gather(*agent_coroutines, return_exceptions=True)

        # Flatten results
        completed_tasks = []
        for result in results:
            if isinstance(result, list):
                completed_tasks.extend(result)

        return completed_tasks

    def assign_tasks(
        self,
        tasks: List[TeamTask],
        members: List[TeamMember]
    ) -> Dict[str, List[TeamTask]]:
        """Assign tasks for parallel execution."""
        assignments = {member.agent_id: [] for member in members}

        # Distribute tasks evenly across members
        for i, task in enumerate(tasks):
            member = members[i % len(members)]
            assignments[member.agent_id].append(task)
            task.assigned_to = member.agent_id

        return assignments


class TeamExecutionEngine:
    """Team execution engine with coordination strategies."""

    def __init__(self, team_config: Dict[str, Any], agents: Dict[str, Any]):
        self.team_config = team_config
        self.agents = agents
        self.state = TeamState.IDLE
        self.members: List[TeamMember] = []
        self.coordination_strategy: CoordinationStrategy = self._create_strategy()
        self.execution_history: List[Dict[str, Any]] = []

        # Load team members
        self._load_members()

    def _load_members(self) -> None:
        """Load team members from configuration."""
        members_data = self.team_config.get('members', [])

        for member_data in members_data:
            member = TeamMember(
                agent_id=member_data['agent_id'],
                role=TeamMemberRole(member_data.get('role', 'member')),
                capabilities=member_data.get('capabilities', []),
                priority=member_data.get('priority', 1),
                max_concurrent_tasks=member_data.get('max_concurrent_tasks', 1),
                metadata=member_data.get('metadata', {})
            )
            self.members.append(member)

    def _create_strategy(self) -> CoordinationStrategy:
        """Create coordination strategy based on configuration."""
        strategy_name = self.team_config.get('coordination_strategy', 'hierarchical')

        if strategy_name == 'hierarchical':
            return HierarchicalStrategy()
        elif strategy_name == 'collaborative':
            return CollaborativeStrategy()
        elif strategy_name == 'parallel':
            return ParallelStrategy()
        else:
            return HierarchicalStrategy()  # Default

    async def execute_tasks(
        self,
        tasks: List[TeamTask],
        context: TeamExecutionContext
    ) -> List[TeamTask]:
        """Execute tasks using team coordination."""

        self.state = TeamState.PLANNING

        try:
            # Execute using coordination strategy
            self.state = TeamState.EXECUTING
            completed_tasks = await self.coordination_strategy.coordinate_execution(
                tasks, self.members, self.agents, context
            )

            self.state = TeamState.COMPLETED

            # Record execution history
            execution_record = {
                'execution_id': context.execution_id,
                'tasks_count': len(tasks),
                'completed_count': len(completed_tasks),
                'strategy': self.team_config.get('coordination_strategy'),
                'started_at': context.started_at.isoformat(),
                'completed_at': datetime.utcnow().isoformat()
            }

            self.execution_history.append(execution_record)

            return completed_tasks

        except Exception as e:
            self.state = TeamState.ERROR
            raise e

    def get_team_stats(self) -> Dict[str, Any]:
        """Get team execution statistics."""
        return {
            'team_id': self.team_config.get('id'),
            'current_state': self.state.value,
            'member_count': len(self.members),
            'coordination_strategy': self.team_config.get('coordination_strategy'),
            'execution_history': self.execution_history,
            'members': [member.to_dict() for member in self.members]
        }


class TeamBuilder:
    """
    Fluent interface builder for Engine Framework teams.

    Provides a clean, chainable API for configuring teams with coordination
    strategies, member management, and agent orchestration.

    Usage:
        # Basic hierarchical team
        team = TeamBuilder()\\
            .with_id("dev_team")\\
            .with_name("Development Team")\\
            .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL)\\
            .add_member("lead_agent", TeamMemberRole.LEADER)\\
            .add_member("dev1_agent", TeamMemberRole.MEMBER)\\
            .add_member("dev2_agent", TeamMemberRole.MEMBER)\\
            .build()

        # Collaborative team with capabilities
        team = TeamBuilder()\\
            .with_id("analysis_team")\\
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)\\
            .add_member("analyst1", TeamMemberRole.MEMBER, ["data_analysis", "sql"])\\
            .add_member("analyst2", TeamMemberRole.MEMBER, ["visualization", "python"])\\
            .add_member("reviewer", TeamMemberRole.REVIEWER, ["quality_check"])\\
            .build()
    """

    def __init__(self):
        """Initialize builder with empty configuration."""
        self.config = {
            'id': None,
            'name': None,
            'description': None,
            'coordination_strategy': TeamCoordinationStrategy.HIERARCHICAL.value,
            'execution_mode': TeamExecutionMode.SYNCHRONOUS.value,
            'members': [],
            'metadata': {}
        }

        self._validation_errors: List[str] = []

    # === REQUIRED CONFIGURATION ===

    def with_id(self, team_id: str) -> 'TeamBuilder':
        """Set team ID (required)."""
        if not team_id or not isinstance(team_id, str):
            self._validation_errors.append("Team ID must be a non-empty string")
            return self

        self.config['id'] = team_id
        return self

    def with_name(self, name: str) -> 'TeamBuilder':
        """Set team name."""
        self.config['name'] = name
        return self

    def with_description(self, description: str) -> 'TeamBuilder':
        """Set team description."""
        self.config['description'] = description
        return self

    # === COORDINATION STRATEGY ===

    def with_coordination_strategy(
    self, strategy: TeamCoordinationStrategy) -> 'TeamBuilder':
        """Set team coordination strategy."""
        self.config['coordination_strategy'] = strategy.value
        return self

    def with_execution_mode(self, mode: TeamExecutionMode) -> 'TeamBuilder':
        """Set team execution mode."""
        self.config['execution_mode'] = mode.value
        return self

    # === MEMBER MANAGEMENT ===

    def add_member(
        self,
        agent_id: str,
        role: TeamMemberRole = TeamMemberRole.MEMBER,
        capabilities: Optional[List[str]] = None,
        priority: int = 1,
        max_concurrent_tasks: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'TeamBuilder':
        """Add team member."""

        member_config = {
            'agent_id': agent_id,
            'role': role.value,
            'capabilities': capabilities or [],
            'priority': priority,
            'max_concurrent_tasks': max_concurrent_tasks,
            'metadata': metadata or {}
        }

        self.config['members'].append(member_config)
        return self

    def add_leader(
        self,
        agent_id: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'TeamBuilder':
        """Add team leader (convenience method)."""
        return self.add_member(
    agent_id,
    TeamMemberRole.LEADER,
    capabilities,
    priority=0,
     metadata=metadata)

    def add_reviewer(
        self,
        agent_id: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'TeamBuilder':
        """Add team reviewer (convenience method)."""
        return self.add_member(
    agent_id,
    TeamMemberRole.REVIEWER,
    capabilities,
     metadata=metadata)

    # === METADATA ===

    def with_metadata(self, metadata: Dict[str, Any]) -> 'TeamBuilder':
        """Set team metadata."""
        if not isinstance(metadata, dict):
            self._validation_errors.append("Metadata must be a dictionary")
            return self

        self.config['metadata'] = metadata
        return self

    # === VALIDATION ===

    def validate(self) -> bool:
        """Validate team configuration."""
        self._validation_errors.clear()

        # Check required fields
        if not self.config.get('id'):
            self._validation_errors.append("Team ID is required")

        # Check team has members
        if not self.config.get('members'):
            self._validation_errors.append("Team must have at least one member")

        # Check hierarchical strategy has leader
        if self.config.get(
            'coordination_strategy') == TeamCoordinationStrategy.HIERARCHICAL.value:
            has_leader = any(
                member['role'] == TeamMemberRole.LEADER.value
                for member in self.config.get('members', [])
            )
            if not has_leader:
                self._validation_errors.append(
                    "Hierarchical strategy requires a team leader")

        # Validate member agent IDs are unique
        agent_ids = [member['agent_id'] for member in self.config.get('members', [])]
        if len(agent_ids) != len(set(agent_ids)):
            self._validation_errors.append("Agent IDs must be unique within team")

        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> List[str]:
        """Get current validation errors."""
        return self._validation_errors.copy()

    # === BUILD METHODS ===

    def build(self, agents: Optional[Dict[str, Any]] = None) -> 'BuiltTeam':
        """Build and return configured team."""
        if not self.validate():
            raise ValueError(
    f"Team validation failed: {
        ', '.join(
            self._validation_errors)}")

        # Create built team
        built_team = BuiltTeam(
            config=self.config.copy(),
            agents=agents or {}
        )

        return built_team

    # === FACTORY METHODS ===

    @classmethod
    def development_team(cls, team_id: str, leader_id: str,
                         member_ids: List[str]) -> 'TeamBuilder':
        """Create development team template."""
        builder = cls()\
            .with_id(team_id)\
            .with_name("Development Team")\
            .with_coordination_strategy(TeamCoordinationStrategy.HIERARCHICAL)\
            .add_leader(leader_id, ["leadership", "code_review", "architecture"])

        for member_id in member_ids:
            builder.add_member(member_id, TeamMemberRole.MEMBER, ["programming", "testing"])

        return builder

    @classmethod
    def analysis_team(cls, team_id: str, analyst_ids: List[str]) -> 'TeamBuilder':
        """Create analysis team template."""
        builder = cls() \
            .with_id(team_id) \
            .with_name("Analysis Team") \
            .with_coordination_strategy(TeamCoordinationStrategy.COLLABORATIVE)

        for i, analyst_id in enumerate(analyst_ids):
            capabilities = ["data_analysis", "statistics", "visualization"]
            builder.add_member(analyst_id, TeamMemberRole.MEMBER, capabilities, priority=i+1)

        return builder

    @classmethod
    def parallel_processing_team(cls, team_id: str, processor_ids: List[str]) -> 'TeamBuilder':
        """Create parallel processing team template."""
        builder = cls() \
            .with_id(team_id) \
            .with_name("Parallel Processing Team") \
            .with_coordination_strategy(TeamCoordinationStrategy.PARALLEL) \
            .with_execution_mode(TeamExecutionMode.ASYNCHRONOUS)

        for processor_id in processor_ids:
            builder.add_member(processor_id, TeamMemberRole.MEMBER,
                             capabilities=["processing"], max_concurrent_tasks=3)

        return builder


class BuiltTeam:
    """
    Built team with execution capabilities.

    Represents a fully configured team ready for task execution.
    """

    def __init__(self, config: Dict[str, Any], agents: Dict[str, Any]):
        self.config = config
        self.agents = agents
        self.execution_engine = TeamExecutionEngine(config, agents)
        self.created_at = datetime.utcnow()

    @property
    def id(self) -> str:
        """Get team ID."""
        return self.config['id']

    @property
    def name(self) -> str:
        """Get team name (or ID if no name set)."""
        return self.config.get('name', self.config['id'])

    @property
    def coordination_strategy(self) -> str:
        """Get coordination strategy."""
        return self.config['coordination_strategy']

    @property
    def member_count(self) -> int:
        """Get number of team members."""
        return len(self.config.get('members', []))

    def add_agent(self, agent_id: str, agent: Any) -> None:
        """Add agent to team."""
        self.agents[agent_id] = agent

    async def execute_tasks(
        self,
        tasks: List[TeamTask],
        context: Optional[TeamExecutionContext] = None
    ) -> List[TeamTask]:
        """Execute tasks using team coordination."""
        if context is None:
            context = TeamExecutionContext()

        return await self.execution_engine.execute_tasks(tasks, context)

    async def execute_task(
        self,
        task_description: str,
        requirements: Optional[List[str]] = None,
        context: Optional[TeamExecutionContext] = None
    ) -> TeamTask:
        """Execute single task."""
        task = TeamTask(
            id=str(uuid.uuid4()),
            description=task_description,
            requirements=requirements or []
        )

        completed_tasks = await self.execute_tasks([task], context)
        return completed_tasks[0] if completed_tasks else task

    def get_stats(self) -> Dict[str, Any]:
        """Get team statistics."""
        return {
            'team_id': self.id,
            'team_name': self.name,
            'coordination_strategy': self.coordination_strategy,
            'member_count': self.member_count,
            'created_at': self.created_at.isoformat(),
            'execution_stats': self.execution_engine.get_team_stats()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert team to dictionary representation."""
        return {
            'config': self.config,
            'agent_ids': list(self.agents.keys()),
            'stats': self.get_stats(),
            'created_at': self.created_at.isoformat()
        }


# === CONVENIENCE FUNCTIONS ===

def create_development_team(team_id: str, leader_id: str, member_ids: List[str], agents: Dict[str, Any]) -> BuiltTeam:
    """Create development team with agents."""
    return TeamBuilder.development_team(team_id, leader_id, member_ids).build(agents)


def create_analysis_team(team_id: str, analyst_ids: List[str], agents: Dict[str, Any]) -> BuiltTeam:
    """Create analysis team with agents."""
    return TeamBuilder.analysis_team(team_id, analyst_ids).build(agents)


def create_parallel_team(team_id: str, processor_ids: List[str], agents: Dict[str, Any]) -> BuiltTeam:
    """Create parallel processing team with agents."""
    return TeamBuilder.parallel_processing_team(team_id, processor_ids).build(agents)


# === EXAMPLE USAGE ===

async def example_usage():
    """Example usage of TeamBuilder."""

    # Mock agents (in real usage, these would be actual BuiltAgent instances)
    agents = {}

    # Create development team
    dev_team = TeamBuilder.development_team(
        team_id="dev_team_01",
        leader_id="senior_dev",
        member_ids=["junior_dev1", "junior_dev2"]
    ).build(agents)

    print(f"Created team: {dev_team.name}")
    print(f"Members: {dev_team.member_count}")
    print(f"Strategy: {dev_team.coordination_strategy}")

    # Create tasks
    tasks = [
        TeamTask(
            id="task_1",
            description="Analyze requirements and create project structure",
            requirements=["architecture", "analysis"]
        ),
        TeamTask(
            id="task_2",
            description="Implement user authentication module",
            requirements=["programming", "security"]
        ),
        TeamTask(
            id="task_3",
            description="Create unit tests for authentication",
            requirements=["testing", "programming"]
        )
    ]

    # Execute tasks (would need real agents)
    # context = TeamExecutionContext(project_id="proj_123")
    # completed_tasks = await dev_team.execute_tasks(tasks, context)
    # print(f"Completed {len(completed_tasks)} tasks")

    # Get stats
    stats = dev_team.get_stats()
    print(f"Team stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    # Run example usage
    import asyncio
    asyncio.run(example_usage())
