"""
Team Service Layer - Business Logic for Team Management.

The TeamService provides high-level business logic for team management,
including CRUD operations, member coordination, task distribution, and
execution orchestration with workflow integration.

Key Features:
- Repository pattern for data access
- Team lifecycle management
- Member coordination and role management
- Task distribution and execution
- Integration with workflows and protocols
- Performance monitoring and analytics
- Error handling and recovery

Architecture:
- Service Layer (this) -> Repository Layer -> Models -> Database
- Integration with Core Team System (TeamBuilder)
- Agent orchestration and communication
- Workflow execution context management
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid
import logging

# Import core team system
from ..core.teams.team_builder import (
    TeamBuilder, BuiltTeam, TeamExecutionContext, TeamTask, TeamMember,
    TeamCoordinationStrategy, TeamMemberRole, TeamExecutionMode, TeamState
)

# Import agent service for member management
from .agent_service import AgentService, BuiltAgent

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ..models.team import Team
    from ..models.agent import Agent
    from ..models.workflow import Workflow
    from ..models.project import Project
    from ..models.infrastructure import User

logger = logging.getLogger(__name__)


class TeamServiceError(Exception):
    """Base exception for team service errors."""
    pass


class TeamNotFoundError(TeamServiceError):
    """Team not found error."""
    pass


class TeamValidationError(TeamServiceError):
    """Team validation error."""
    pass


class TeamExecutionError(TeamServiceError):
    """Team execution error."""
    pass


class MemberNotFoundError(TeamServiceError):
    """Team member not found error."""
    pass


@dataclass
class TeamCreateRequest:
    """Request model for creating teams."""
    id: str
    name: str
    description: Optional[str] = None
    coordination_strategy: TeamCoordinationStrategy = TeamCoordinationStrategy.HIERARCHICAL
    execution_mode: TeamExecutionMode = TeamExecutionMode.SYNCHRONOUS
    members: List[Dict[str, Any]] = None
    protocol_id: Optional[str] = None
    workflow_id: Optional[str] = None
    book_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None
    created_by: Optional[str] = None
    
    def __post_init__(self):
        if self.members is None:
            self.members = []


@dataclass
class TeamUpdateRequest:
    """Request model for updating teams."""
    name: Optional[str] = None
    description: Optional[str] = None
    coordination_strategy: Optional[TeamCoordinationStrategy] = None
    execution_mode: Optional[TeamExecutionMode] = None
    protocol_id: Optional[str] = None
    workflow_id: Optional[str] = None
    book_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemberAddRequest:
    """Request model for adding team members."""
    agent_id: str
    role: TeamMemberRole = TeamMemberRole.MEMBER
    capabilities: Optional[List[str]] = None
    priority: int = 1
    max_concurrent_tasks: int = 1
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MemberUpdateRequest:
    """Request model for updating team members."""
    role: Optional[TeamMemberRole] = None
    capabilities: Optional[List[str]] = None
    priority: Optional[int] = None
    max_concurrent_tasks: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskExecutionRequest:
    """Request model for team task execution."""
    tasks: List[Dict[str, Any]]  # List of task descriptions and requirements
    context: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    timeout_seconds: Optional[int] = 300  # 5 minutes default
    execution_mode: Optional[str] = None


@dataclass
class TaskExecutionResponse:
    """Response model for team task execution."""
    execution_id: str
    team_id: str
    tasks: List[Dict[str, Any]]  # Completed task details
    context: Dict[str, Any]
    execution_time: float
    status: str
    strategy_used: str
    member_performance: Dict[str, Any]
    error: Optional[str] = None


class TeamRepository(ABC):
    """Abstract repository interface for team data access."""
    
    @abstractmethod
    async def create(self, team_data: Dict[str, Any]) -> 'Team':
        """Create new team in database."""
        pass
    
    @abstractmethod
    async def get_by_id(self, team_id: str) -> Optional['Team']:
        """Get team by ID."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: str) -> List['Team']:
        """Get teams by project ID."""
        pass
    
    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List['Team']:
        """List all teams with pagination."""
        pass
    
    @abstractmethod
    async def update(self, team_id: str, update_data: Dict[str, Any]) -> Optional['Team']:
        """Update team."""
        pass
    
    @abstractmethod
    async def delete(self, team_id: str) -> bool:
        """Delete team."""
        pass
    
    @abstractmethod
    async def add_member(self, team_id: str, member_data: Dict[str, Any]) -> bool:
        """Add member to team."""
        pass
    
    @abstractmethod
    async def remove_member(self, team_id: str, agent_id: str) -> bool:
        """Remove member from team."""
        pass
    
    @abstractmethod
    async def update_member(self, team_id: str, agent_id: str, update_data: Dict[str, Any]) -> bool:
        """Update team member."""
        pass


class MockTeamRepository(TeamRepository):
    """Mock repository implementation for testing and development."""
    
    def __init__(self):
        self._teams: Dict[str, Dict[str, Any]] = {}
    
    async def create(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new team in mock storage."""
        team_id = team_data['id']
        team_data['created_at'] = datetime.utcnow().isoformat()
        team_data['updated_at'] = datetime.utcnow().isoformat()
        self._teams[team_id] = team_data
        return team_data
    
    async def get_by_id(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID from mock storage."""
        return self._teams.get(team_id)
    
    async def get_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """Get teams by project ID from mock storage."""
        return [
            team for team in self._teams.values()
            if team.get('project_id') == project_id
        ]
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all teams with pagination from mock storage."""
        teams = list(self._teams.values())
        return teams[skip:skip + limit]
    
    async def update(self, team_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update team in mock storage."""
        if team_id not in self._teams:
            return None
        
        self._teams[team_id].update(update_data)
        self._teams[team_id]['updated_at'] = datetime.utcnow().isoformat()
        return self._teams[team_id]
    
    async def delete(self, team_id: str) -> bool:
        """Delete team from mock storage."""
        if team_id in self._teams:
            del self._teams[team_id]
            return True
        return False
    
    async def add_member(self, team_id: str, member_data: Dict[str, Any]) -> bool:
        """Add member to team in mock storage."""
        if team_id not in self._teams:
            return False
        
        if 'members' not in self._teams[team_id]:
            self._teams[team_id]['members'] = []
        
        self._teams[team_id]['members'].append(member_data)
        self._teams[team_id]['updated_at'] = datetime.utcnow().isoformat()
        return True
    
    async def remove_member(self, team_id: str, agent_id: str) -> bool:
        """Remove member from team in mock storage."""
        if team_id not in self._teams:
            return False
        
        members = self._teams[team_id].get('members', [])
        original_count = len(members)
        
        self._teams[team_id]['members'] = [
            member for member in members 
            if member.get('agent_id') != agent_id
        ]
        
        if len(self._teams[team_id]['members']) < original_count:
            self._teams[team_id]['updated_at'] = datetime.utcnow().isoformat()
            return True
        
        return False
    
    async def update_member(self, team_id: str, agent_id: str, update_data: Dict[str, Any]) -> bool:
        """Update team member in mock storage."""
        if team_id not in self._teams:
            return False
        
        members = self._teams[team_id].get('members', [])
        
        for member in members:
            if member.get('agent_id') == agent_id:
                member.update(update_data)
                self._teams[team_id]['updated_at'] = datetime.utcnow().isoformat()
                return True
        
        return False


class TeamService:
    """
    Service layer for team management and execution.
    
    Provides high-level business logic for:
    - Team CRUD operations
    - Member management and coordination
    - Task execution orchestration
    - Performance monitoring and analytics
    - Integration with workflows and protocols
    """
    
    def __init__(
        self, 
        repository: Optional[TeamRepository] = None,
        agent_service: Optional[AgentService] = None
    ):
        """Initialize team service."""
        self.repository = repository or MockTeamRepository()
        self.agent_service = agent_service or AgentService()
        self._active_teams: Dict[str, BuiltTeam] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
        
        # Service configuration
        self.config = {
            'max_active_teams': 50,
            'default_execution_timeout': 300,  # 5 minutes
            'max_concurrent_tasks_per_team': 10,
            'cleanup_interval_minutes': 120
        }
    
    # === CRUD OPERATIONS ===
    
    async def create_team(self, request: TeamCreateRequest) -> Dict[str, Any]:
        """Create new team with validation."""
        try:
            # Validate request
            await self._validate_create_request(request)
            
            # Prepare team data
            team_data = {
                'id': request.id,
                'name': request.name,
                'description': request.description,
                'coordination_strategy': request.coordination_strategy.value,
                'execution_mode': request.execution_mode.value,
                'members': request.members,
                'protocol_id': request.protocol_id,
                'workflow_id': request.workflow_id,
                'book_id': request.book_id,
                'metadata': request.metadata or {},
                'project_id': request.project_id,
                'created_by': request.created_by,
                'status': 'active',
                'execution_count': 0,
                'last_executed_at': None
            }
            
            # Create in database
            team = await self.repository.create(team_data)
            
            logger.info(f"Created team {request.id}", extra={
                'team_id': request.id,
                'coordination_strategy': request.coordination_strategy.value,
                'member_count': len(request.members),
                'created_by': request.created_by
            })
            
            return team
            
        except Exception as e:
            logger.error(f"Failed to create team {request.id}: {str(e)}")
            raise TeamServiceError(f"Failed to create team: {str(e)}")
    
    async def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID."""
        try:
            team = await self.repository.get_by_id(team_id)
            if not team:
                raise TeamNotFoundError(f"Team {team_id} not found")
            
            return team
            
        except TeamNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get team {team_id}: {str(e)}")
            raise TeamServiceError(f"Failed to get team: {str(e)}")
    
    async def update_team(
        self,
        team_id: str,
        request: TeamUpdateRequest,
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update existing team."""
        try:
            # Check if team exists
            existing_team = await self.get_team(team_id)
            if not existing_team:
                raise TeamNotFoundError(f"Team {team_id} not found")
            
            # Prepare update data
            update_data = {}
            
            if request.name is not None:
                update_data['name'] = request.name
            if request.description is not None:
                update_data['description'] = request.description
            if request.coordination_strategy is not None:
                update_data['coordination_strategy'] = request.coordination_strategy.value
            if request.execution_mode is not None:
                update_data['execution_mode'] = request.execution_mode.value
            if request.protocol_id is not None:
                update_data['protocol_id'] = request.protocol_id
            if request.workflow_id is not None:
                update_data['workflow_id'] = request.workflow_id
            if request.book_id is not None:
                update_data['book_id'] = request.book_id
            if request.metadata is not None:
                update_data['metadata'] = request.metadata
            
            update_data['updated_by'] = updated_by
            
            # Update in database
            updated_team = await self.repository.update(team_id, update_data)
            
            # Invalidate cached team if exists
            if team_id in self._active_teams:
                del self._active_teams[team_id]
            
            logger.info(f"Updated team {team_id}", extra={
                'team_id': team_id,
                'updated_by': updated_by
            })
            
            return updated_team
            
        except (TeamNotFoundError, TeamServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to update team {team_id}: {str(e)}")
            raise TeamServiceError(f"Failed to update team: {str(e)}")
    
    async def delete_team(self, team_id: str) -> bool:
        """Delete team."""
        try:
            # Remove from active teams if exists
            if team_id in self._active_teams:
                del self._active_teams[team_id]
            
            # Remove execution stats if exists
            if team_id in self._execution_stats:
                del self._execution_stats[team_id]
            
            # Delete from database
            deleted = await self.repository.delete(team_id)
            
            if deleted:
                logger.info(f"Deleted team {team_id}")
            else:
                logger.warning(f"Team {team_id} not found for deletion")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete team {team_id}: {str(e)}")
            raise TeamServiceError(f"Failed to delete team: {str(e)}")
    
    async def list_teams(
        self,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List teams with optional project filter."""
        try:
            if project_id:
                teams = await self.repository.get_by_project_id(project_id)
                return teams[skip:skip + limit]
            else:
                return await self.repository.list_all(skip, limit)
                
        except Exception as e:
            logger.error(f"Failed to list teams: {str(e)}")
            raise TeamServiceError(f"Failed to list teams: {str(e)}")
    
    # === MEMBER MANAGEMENT ===
    
    async def add_member(
        self,
        team_id: str,
        request: MemberAddRequest,
        added_by: Optional[str] = None
    ) -> bool:
        """Add member to team."""
        try:
            # Validate team exists
            team = await self.get_team(team_id)
            if not team:
                raise TeamNotFoundError(f"Team {team_id} not found")
            
            # Validate agent exists
            agent = await self.agent_service.get_agent(request.agent_id)
            if not agent:
                raise TeamValidationError(f"Agent {request.agent_id} not found")
            
            # Check if agent already in team
            existing_members = team.get('members', [])
            if any(member.get('agent_id') == request.agent_id for member in existing_members):
                raise TeamValidationError(f"Agent {request.agent_id} already in team")
            
            # Prepare member data
            member_data = {
                'agent_id': request.agent_id,
                'role': request.role.value,
                'capabilities': request.capabilities or [],
                'priority': request.priority,
                'max_concurrent_tasks': request.max_concurrent_tasks,
                'metadata': request.metadata or {},
                'added_by': added_by,
                'added_at': datetime.utcnow().isoformat()
            }
            
            # Add to database
            success = await self.repository.add_member(team_id, member_data)
            
            if success:
                # Invalidate cached team
                if team_id in self._active_teams:
                    del self._active_teams[team_id]
                
                logger.info(f"Added member {request.agent_id} to team {team_id}")
            
            return success
            
        except (TeamNotFoundError, TeamValidationError, TeamServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to add member to team {team_id}: {str(e)}")
            raise TeamServiceError(f"Failed to add member: {str(e)}")
    
    async def remove_member(self, team_id: str, agent_id: str) -> bool:
        """Remove member from team."""
        try:
            # Validate team exists
            team = await self.get_team(team_id)
            if not team:
                raise TeamNotFoundError(f"Team {team_id} not found")
            
            # Remove from database
            success = await self.repository.remove_member(team_id, agent_id)
            
            if success:
                # Invalidate cached team
                if team_id in self._active_teams:
                    del self._active_teams[team_id]
                
                logger.info(f"Removed member {agent_id} from team {team_id}")
            
            return success
            
        except (TeamNotFoundError, TeamServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to remove member from team {team_id}: {str(e)}")
            raise TeamServiceError(f"Failed to remove member: {str(e)}")
    
    async def update_member(
        self,
        team_id: str,
        agent_id: str,
        request: MemberUpdateRequest
    ) -> bool:
        """Update team member."""
        try:
            # Validate team exists
            team = await self.get_team(team_id)
            if not team:
                raise TeamNotFoundError(f"Team {team_id} not found")
            
            # Prepare update data
            update_data = {}
            
            if request.role is not None:
                update_data['role'] = request.role.value
            if request.capabilities is not None:
                update_data['capabilities'] = request.capabilities
            if request.priority is not None:
                update_data['priority'] = request.priority
            if request.max_concurrent_tasks is not None:
                update_data['max_concurrent_tasks'] = request.max_concurrent_tasks
            if request.metadata is not None:
                update_data['metadata'] = request.metadata
            
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update in database
            success = await self.repository.update_member(team_id, agent_id, update_data)
            
            if success:
                # Invalidate cached team
                if team_id in self._active_teams:
                    del self._active_teams[team_id]
                
                logger.info(f"Updated member {agent_id} in team {team_id}")
            
            return success
            
        except (TeamNotFoundError, TeamServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to update member in team {team_id}: {str(e)}")
            raise TeamServiceError(f"Failed to update member: {str(e)}")
    
    # === TASK EXECUTION ===
    
    async def execute_tasks(
        self,
        team_id: str,
        request: TaskExecutionRequest
    ) -> TaskExecutionResponse:
        """Execute tasks using team coordination."""
        start_time = datetime.utcnow()
        
        try:
            # Get or create built team
            built_team = await self._get_or_create_built_team(team_id)
            
            # Convert request tasks to TeamTask objects
            team_tasks = []
            for i, task_data in enumerate(request.tasks):
                task = TeamTask(
                    id=task_data.get('id', f"task_{i}_{uuid.uuid4().hex[:8]}"),
                    description=task_data['description'],
                    requirements=task_data.get('requirements', []),
                    dependencies=task_data.get('dependencies', []),
                    context=task_data.get('context', {})
                )
                team_tasks.append(task)
            
            # Create execution context
            context = TeamExecutionContext(
                project_id=request.context.get('project_id') if request.context else None,
                user_id=request.context.get('user_id') if request.context else None,
                session_id=request.context.get('session_id') if request.context else None,
                workflow_id=request.workflow_id,
                metadata=request.context or {}
            )
            
            # Execute with timeout
            timeout = request.timeout_seconds or self.config['default_execution_timeout']
            
            try:
                completed_tasks = await asyncio.wait_for(
                    built_team.execute_tasks(team_tasks, context),
                    timeout=timeout
                )
                
                # Update execution stats
                await self._update_execution_stats(team_id, len(team_tasks), len(completed_tasks))
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Convert completed tasks to response format
                response_tasks = [task.to_dict() for task in completed_tasks]
                
                # Get member performance stats
                member_performance = self._calculate_member_performance(completed_tasks)
                
                return TaskExecutionResponse(
                    execution_id=context.execution_id,
                    team_id=team_id,
                    tasks=response_tasks,
                    context=context.to_dict(),
                    execution_time=execution_time,
                    status="success",
                    strategy_used=built_team.coordination_strategy,
                    member_performance=member_performance
                )
                
            except asyncio.TimeoutError:
                await self._update_execution_stats(team_id, len(team_tasks), 0, success=False)
                raise TeamExecutionError(f"Team execution timed out after {timeout} seconds")
            
        except (TeamNotFoundError, TeamExecutionError):
            raise
        except Exception as e:
            await self._update_execution_stats(team_id, len(request.tasks), 0, success=False)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Team execution failed for {team_id}: {str(e)}")
            
            return TaskExecutionResponse(
                execution_id=str(uuid.uuid4()),
                team_id=team_id,
                tasks=[],
                context={},
                execution_time=execution_time,
                status="error",
                strategy_used="unknown",
                member_performance={},
                error=str(e)
            )
    
    async def get_team_stats(self, team_id: str) -> Dict[str, Any]:
        """Get team execution statistics."""
        try:
            team = await self.get_team(team_id)
            
            # Get built team stats if active
            built_team_stats = None
            if team_id in self._active_teams:
                built_team_stats = self._active_teams[team_id].get_stats()
            
            # Get service-level stats
            service_stats = self._execution_stats.get(team_id, {
                'total_executions': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'last_execution_at': None
            })
            
            return {
                'team_id': team_id,
                'team_info': {
                    'name': team.get('name'),
                    'coordination_strategy': team.get('coordination_strategy'),
                    'member_count': len(team.get('members', [])),
                    'status': team.get('status'),
                    'created_at': team.get('created_at'),
                    'last_executed_at': team.get('last_executed_at')
                },
                'service_stats': service_stats,
                'execution_engine_stats': built_team_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for team {team_id}: {str(e)}")
            raise TeamServiceError(f"Failed to get team stats: {str(e)}")
    
    # === PRIVATE METHODS ===
    
    async def _validate_create_request(self, request: TeamCreateRequest) -> None:
        """Validate team create request."""
        # Check if team ID already exists
        existing_team = await self.repository.get_by_id(request.id)
        if existing_team:
            raise TeamValidationError(f"Team with ID {request.id} already exists")
        
        # Validate members exist if provided
        for member_data in request.members:
            agent_id = member_data.get('agent_id')
            if agent_id:
                try:
                    agent = await self.agent_service.get_agent(agent_id)
                    if not agent:
                        raise TeamValidationError(f"Agent {agent_id} not found")
                except Exception:
                    raise TeamValidationError(f"Agent {agent_id} not found")
        
        # Validate using TeamBuilder
        try:
            builder = TeamBuilder() \
                .with_id(request.id) \
                .with_name(request.name) \
                .with_coordination_strategy(request.coordination_strategy) \
                .with_execution_mode(request.execution_mode)
            
            if request.description:
                builder.with_description(request.description)
            if request.metadata:
                builder.with_metadata(request.metadata)
            
            # Add members
            for member_data in request.members:
                builder.add_member(
                    agent_id=member_data['agent_id'],
                    role=TeamMemberRole(member_data.get('role', 'member')),
                    capabilities=member_data.get('capabilities', []),
                    priority=member_data.get('priority', 1),
                    max_concurrent_tasks=member_data.get('max_concurrent_tasks', 1),
                    metadata=member_data.get('metadata', {})
                )
            
            if not builder.validate():
                errors = builder.get_validation_errors()
                raise TeamValidationError(f"Validation failed: {', '.join(errors)}")
                
        except Exception as e:
            raise TeamValidationError(f"Team configuration invalid: {str(e)}")
    
    async def _get_or_create_built_team(self, team_id: str) -> BuiltTeam:
        """Get or create built team for execution."""
        if team_id in self._active_teams:
            return self._active_teams[team_id]
        
        # Get team data from repository
        team_data = await self.get_team(team_id)
        
        # Get agents for team members
        agents = {}
        for member_data in team_data.get('members', []):
            agent_id = member_data['agent_id']
            try:
                # Get agent data and create built agent
                agent_data = await self.agent_service.get_agent(agent_id)
                if agent_data:
                    # This would typically use the agent service to get a BuiltAgent
                    # For now, we'll create a mock
                    from ..core.agents.agent_builder import AgentBuilder
                    built_agent = AgentBuilder() \
                        .with_id(agent_data['id']) \
                        .with_model(agent_data['model']) \
                        .with_stack(agent_data['stack']) \
                        .build()
                    agents[agent_id] = built_agent
            except Exception as e:
                logger.warning(f"Could not load agent {agent_id} for team {team_id}: {str(e)}")
        
        # Create built team using TeamBuilder
        builder = TeamBuilder() \
            .with_id(team_data['id']) \
            .with_name(team_data['name']) \
            .with_coordination_strategy(TeamCoordinationStrategy(team_data['coordination_strategy'])) \
            .with_execution_mode(TeamExecutionMode(team_data['execution_mode']))
        
        if team_data.get('description'):
            builder.with_description(team_data['description'])
        if team_data.get('metadata'):
            builder.with_metadata(team_data['metadata'])
        
        # Add members
        for member_data in team_data.get('members', []):
            builder.add_member(
                agent_id=member_data['agent_id'],
                role=TeamMemberRole(member_data['role']),
                capabilities=member_data.get('capabilities', []),
                priority=member_data.get('priority', 1),
                max_concurrent_tasks=member_data.get('max_concurrent_tasks', 1),
                metadata=member_data.get('metadata', {})
            )
        
        built_team = builder.build(agents)
        
        # Cache team (with size limit)
        if len(self._active_teams) >= self.config['max_active_teams']:
            # Remove oldest team (simple LRU)
            oldest_id = next(iter(self._active_teams))
            del self._active_teams[oldest_id]
        
        self._active_teams[team_id] = built_team
        
        return built_team
    
    async def _update_execution_stats(
        self, 
        team_id: str, 
        total_tasks: int, 
        completed_tasks: int,
        success: bool = True
    ) -> None:
        """Update team execution statistics."""
        if team_id not in self._execution_stats:
            self._execution_stats[team_id] = {
                'total_executions': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'last_execution_at': None
            }
        
        stats = self._execution_stats[team_id]
        stats['total_executions'] += 1
        stats['total_tasks'] += total_tasks
        stats['completed_tasks'] += completed_tasks
        stats['last_execution_at'] = datetime.utcnow().isoformat()
        
        # Calculate success rate
        if stats['total_tasks'] > 0:
            stats['success_rate'] = stats['completed_tasks'] / stats['total_tasks']
        
        # Update team in database
        await self.repository.update(team_id, {
            'execution_count': stats['total_executions'],
            'last_executed_at': stats['last_execution_at']
        })
    
    def _calculate_member_performance(self, completed_tasks: List[TeamTask]) -> Dict[str, Any]:
        """Calculate member performance metrics."""
        performance = {}
        
        for task in completed_tasks:
            if task.assigned_to:
                if task.assigned_to not in performance:
                    performance[task.assigned_to] = {
                        'tasks_completed': 0,
                        'average_time': 0.0,
                        'success_rate': 0.0
                    }
                
                performance[task.assigned_to]['tasks_completed'] += 1
                
                # Calculate execution time if available
                if task.started_at and task.completed_at:
                    start = datetime.fromisoformat(task.started_at.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(task.completed_at.replace('Z', '+00:00'))
                    execution_time = (end - start).total_seconds()
                    
                    # Update average (simple moving average)
                    current_avg = performance[task.assigned_to]['average_time']
                    task_count = performance[task.assigned_to]['tasks_completed']
                    performance[task.assigned_to]['average_time'] = (
                        (current_avg * (task_count - 1) + execution_time) / task_count
                    )
        
        return performance


# === CONVENIENCE FUNCTIONS ===

def create_team_service(
    repository: Optional[TeamRepository] = None,
    agent_service: Optional[AgentService] = None
) -> TeamService:
    """Create team service with optional custom repository and agent service."""
    return TeamService(repository, agent_service)


# === EXAMPLE USAGE ===

async def example_usage():
    """Example usage of TeamService."""
    
    # Create service
    service = create_team_service()
    
    # Create team
    create_request = TeamCreateRequest(
        id="example_team",
        name="Example Team",
        description="A sample development team",
        coordination_strategy=TeamCoordinationStrategy.HIERARCHICAL,
        members=[
            {
                'agent_id': 'lead_agent',
                'role': 'leader',
                'capabilities': ['leadership', 'architecture'],
                'priority': 0
            },
            {
                'agent_id': 'dev_agent1',
                'role': 'member',
                'capabilities': ['programming'],
                'priority': 1
            },
            {
                'agent_id': 'dev_agent2',
                'role': 'member',
                'capabilities': ['programming', 'testing'],
                'priority': 1
            }
        ]
    )
    
    team = await service.create_team(create_request)
    print(f"Created team: {team['id']}")
    
    # Execute tasks
    execution_request = TaskExecutionRequest(
        tasks=[
            {
                'description': 'Design system architecture',
                'requirements': ['architecture', 'leadership']
            },
            {
                'description': 'Implement user authentication',
                'requirements': ['programming']
            },
            {
                'description': 'Write unit tests',
                'requirements': ['programming', 'testing']
            }
        ],
        context={'project_id': 'proj_123'}
    )
    
    # Note: This would fail in real usage without actual agents
    # response = await service.execute_tasks(team['id'], execution_request)
    # print(f"Executed {len(response.tasks)} tasks")
    
    # Get stats
    stats = await service.get_team_stats(team['id'])
    print(f"Team stats: {stats}")


if __name__ == "__main__":
    # Run example usage
    import asyncio
    asyncio.run(example_usage())
