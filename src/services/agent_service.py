"""
Agent Service Layer - Business Logic for Agent Management.

The AgentService provides high-level business logic for agent management,
including CRUD operations, validation, execution orchestration, and 
integration with protocols, workflows, tools, and memory systems.

Key Features:
- Repository pattern for data access
- Business logic validation 
- Agent lifecycle management
- Protocol and workflow integration
- Tool capability management
- Memory/book integration
- Execution monitoring and stats
- Error handling and recovery

Architecture:
- Service Layer (this) -> Repository Layer -> Models -> Database
- Integration with Core Agent System (AgentBuilder)
- Event-driven updates and notifications
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid
import logging

# Import core agent system
from ..core.agents.agent_builder import (
    AgentBuilder, BuiltAgent, AgentExecutionContext, AgentMessage, AgentState
)

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from ..models.agent import Agent
    from ..models.project import Project
    from ..models.protocol import Protocol
    from ..models.workflow import Workflow
    from ..models.book import Book
    from ..models.tool import Tool
    from ..models.infrastructure import User

logger = logging.getLogger(__name__)


class AgentServiceError(Exception):
    """Base exception for agent service errors."""
    pass


class AgentNotFoundError(AgentServiceError):
    """Agent not found error."""
    pass


class AgentValidationError(AgentServiceError):
    """Agent validation error."""
    pass


class AgentExecutionError(AgentServiceError):
    """Agent execution error."""
    pass


@dataclass
class AgentCreateRequest:
    """Request model for creating agents."""
    id: str
    model: str
    stack: List[str]
    name: Optional[str] = None
    specialty: Optional[str] = None
    persona: Optional[str] = None
    tools: Optional[List[str]] = None
    protocol_id: Optional[str] = None
    workflow_id: Optional[str] = None
    book_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None
    created_by: Optional[str] = None


@dataclass
class AgentUpdateRequest:
    """Request model for updating agents."""
    name: Optional[str] = None
    specialty: Optional[str] = None
    persona: Optional[str] = None
    tools: Optional[List[str]] = None
    protocol_id: Optional[str] = None
    workflow_id: Optional[str] = None
    book_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    model_config: Optional[Dict[str, Any]] = None


@dataclass
class AgentExecutionRequest:
    """Request model for agent execution."""
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    timeout_seconds: Optional[int] = 30


@dataclass
class AgentExecutionResponse:
    """Response model for agent execution."""
    request_id: str
    agent_id: str
    message: AgentMessage
    context: AgentExecutionContext
    execution_time: float
    status: str
    error: Optional[str] = None


class AgentRepository(ABC):
    """Abstract repository interface for agent data access."""
    
    @abstractmethod
    async def create(self, agent_data: Dict[str, Any]) -> 'Agent':
        """Create new agent in database."""
        pass
    
    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional['Agent']:
        """Get agent by ID."""
        pass
    
    @abstractmethod
    async def get_by_project_id(self, project_id: str) -> List['Agent']:
        """Get agents by project ID."""
        pass
    
    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List['Agent']:
        """List all agents with pagination."""
        pass
    
    @abstractmethod
    async def update(self, agent_id: str, update_data: Dict[str, Any]) -> Optional['Agent']:
        """Update agent."""
        pass
    
    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """Delete agent."""
        pass
    
    @abstractmethod
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List['Agent']:
        """Search agents by query and filters."""
        pass


class MockAgentRepository(AgentRepository):
    """Mock repository implementation for testing and development."""
    
    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
    
    async def create(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new agent in mock storage."""
        agent_id = agent_data['id']
        agent_data['created_at'] = datetime.utcnow().isoformat()
        agent_data['updated_at'] = datetime.utcnow().isoformat()
        self._agents[agent_id] = agent_data
        return agent_data
    
    async def get_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID from mock storage."""
        return self._agents.get(agent_id)
    
    async def get_by_project_id(self, project_id: str) -> List[Dict[str, Any]]:
        """Get agents by project ID from mock storage."""
        return [
            agent for agent in self._agents.values()
            if agent.get('project_id') == project_id
        ]
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all agents with pagination from mock storage."""
        agents = list(self._agents.values())
        return agents[skip:skip + limit]
    
    async def update(self, agent_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent in mock storage."""
        if agent_id not in self._agents:
            return None
        
        self._agents[agent_id].update(update_data)
        self._agents[agent_id]['updated_at'] = datetime.utcnow().isoformat()
        return self._agents[agent_id]
    
    async def delete(self, agent_id: str) -> bool:
        """Delete agent from mock storage."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False
    
    async def search(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search agents in mock storage."""
        results = []
        for agent in self._agents.values():
            # Simple text search in name, specialty, and stack
            searchable_text = f"{agent.get('name', '')} {agent.get('specialty', '')} {' '.join(agent.get('stack', []))}"
            if query.lower() in searchable_text.lower():
                results.append(agent)
        
        # Apply filters if provided
        if filters:
            filtered_results = []
            for agent in results:
                match = True
                for key, value in filters.items():
                    if key in agent and agent[key] != value:
                        match = False
                        break
                if match:
                    filtered_results.append(agent)
            results = filtered_results
        
        return results


class AgentService:
    """
    Service layer for agent management and execution.
    
    Provides high-level business logic for:
    - Agent CRUD operations
    - Agent execution and monitoring  
    - Integration with protocols, workflows, tools
    - Memory management and context tracking
    - Validation and error handling
    """
    
    def __init__(self, repository: Optional[AgentRepository] = None):
        """Initialize agent service."""
        self.repository = repository or MockAgentRepository()
        self._active_agents: Dict[str, BuiltAgent] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
        
        # Service configuration
        self.config = {
            'max_active_agents': 100,
            'default_execution_timeout': 30,
            'max_conversation_length': 100,
            'cleanup_interval_minutes': 60
        }
    
    # === CRUD OPERATIONS ===
    
    async def create_agent(self, request: AgentCreateRequest) -> Dict[str, Any]:
        """Create new agent with validation."""
        try:
            # Validate request
            await self._validate_create_request(request)
            
            # Prepare agent data
            agent_data = {
                'id': request.id,
                'model': request.model,
                'stack': request.stack,
                'name': request.name,
                'specialty': request.specialty,
                'persona': request.persona,
                'tools': request.tools or [],
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
            agent = await self.repository.create(agent_data)
            
            logger.info(f"Created agent {request.id}", extra={
                'agent_id': request.id,
                'model': request.model,
                'created_by': request.created_by
            })
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {request.id}: {str(e)}")
            raise AgentServiceError(f"Failed to create agent: {str(e)}")
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        try:
            agent = await self.repository.get_by_id(agent_id)
            if not agent:
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            
            return agent
            
        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {str(e)}")
            raise AgentServiceError(f"Failed to get agent: {str(e)}")
    
    async def update_agent(
        self,
        agent_id: str,
        request: AgentUpdateRequest,
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update existing agent."""
        try:
            # Check if agent exists
            existing_agent = await self.get_agent(agent_id)
            if not existing_agent:
                raise AgentNotFoundError(f"Agent {agent_id} not found")
            
            # Prepare update data
            update_data = {}
            
            if request.name is not None:
                update_data['name'] = request.name
            if request.specialty is not None:
                update_data['specialty'] = request.specialty
            if request.persona is not None:
                update_data['persona'] = request.persona
            if request.tools is not None:
                update_data['tools'] = request.tools
            if request.protocol_id is not None:
                update_data['protocol_id'] = request.protocol_id
            if request.workflow_id is not None:
                update_data['workflow_id'] = request.workflow_id
            if request.book_id is not None:
                update_data['book_id'] = request.book_id
            if request.metadata is not None:
                update_data['metadata'] = request.metadata
            if request.model_config is not None:
                update_data['model_config'] = request.model_config
            
            update_data['updated_by'] = updated_by
            
            # Update in database
            updated_agent = await self.repository.update(agent_id, update_data)
            
            # Invalidate cached agent if exists
            if agent_id in self._active_agents:
                del self._active_agents[agent_id]
            
            logger.info(f"Updated agent {agent_id}", extra={
                'agent_id': agent_id,
                'updated_by': updated_by
            })
            
            return updated_agent
            
        except (AgentNotFoundError, AgentServiceError):
            raise
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {str(e)}")
            raise AgentServiceError(f"Failed to update agent: {str(e)}")
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete agent."""
        try:
            # Remove from active agents if exists
            if agent_id in self._active_agents:
                del self._active_agents[agent_id]
            
            # Remove execution stats if exists
            if agent_id in self._execution_stats:
                del self._execution_stats[agent_id]
            
            # Delete from database
            deleted = await self.repository.delete(agent_id)
            
            if deleted:
                logger.info(f"Deleted agent {agent_id}")
            else:
                logger.warning(f"Agent {agent_id} not found for deletion")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
            raise AgentServiceError(f"Failed to delete agent: {str(e)}")
    
    async def list_agents(
        self,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List agents with optional project filter."""
        try:
            if project_id:
                agents = await self.repository.get_by_project_id(project_id)
                return agents[skip:skip + limit]
            else:
                return await self.repository.list_all(skip, limit)
                
        except Exception as e:
            logger.error(f"Failed to list agents: {str(e)}")
            raise AgentServiceError(f"Failed to list agents: {str(e)}")
    
    # === AGENT EXECUTION ===
    
    async def execute_agent(
        self,
        agent_id: str,
        request: AgentExecutionRequest
    ) -> AgentExecutionResponse:
        """Execute agent with message."""
        start_time = datetime.utcnow()
        
        try:
            # Get or create built agent
            built_agent = await self._get_or_create_built_agent(agent_id)
            
            # Create execution context
            context = AgentExecutionContext(
                session_id=request.session_id,
                user_id=request.user_id,
                project_id=request.project_id,
                metadata=request.context or {}
            )
            
            # Execute with timeout
            timeout = request.timeout_seconds or self.config['default_execution_timeout']
            
            try:
                response_message = await asyncio.wait_for(
                    built_agent.execute(request.message, context),
                    timeout=timeout
                )
                
                # Update execution stats
                await self._update_execution_stats(agent_id, success=True)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                return AgentExecutionResponse(
                    request_id=context.request_id,
                    agent_id=agent_id,
                    message=response_message,
                    context=context,
                    execution_time=execution_time,
                    status="success"
                )
                
            except asyncio.TimeoutError:
                await self._update_execution_stats(agent_id, success=False)
                raise AgentExecutionError(f"Agent execution timed out after {timeout} seconds")
            
        except (AgentNotFoundError, AgentExecutionError):
            raise
        except Exception as e:
            await self._update_execution_stats(agent_id, success=False)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Agent execution failed for {agent_id}: {str(e)}")
            
            return AgentExecutionResponse(
                request_id=str(uuid.uuid4()),
                agent_id=agent_id,
                message=AgentMessage(content=f"Execution failed: {str(e)}", role="system"),
                context=AgentExecutionContext(),
                execution_time=execution_time,
                status="error",
                error=str(e)
            )
    
    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get agent execution statistics."""
        try:
            agent = await self.get_agent(agent_id)
            
            # Get built agent stats if active
            built_agent_stats = None
            if agent_id in self._active_agents:
                built_agent_stats = self._active_agents[agent_id].get_stats()
            
            # Get service-level stats
            service_stats = self._execution_stats.get(agent_id, {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_execution_time': 0.0,
                'last_execution_at': None
            })
            
            return {
                'agent_id': agent_id,
                'agent_info': {
                    'name': agent.get('name'),
                    'model': agent.get('model'),
                    'status': agent.get('status'),
                    'created_at': agent.get('created_at'),
                    'last_executed_at': agent.get('last_executed_at')
                },
                'service_stats': service_stats,
                'execution_engine_stats': built_agent_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for agent {agent_id}: {str(e)}")
            raise AgentServiceError(f"Failed to get agent stats: {str(e)}")
    
    # === SEARCH AND DISCOVERY ===
    
    async def search_agents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search agents by query and filters."""
        try:
            return await self.repository.search(query, filters or {})
            
        except Exception as e:
            logger.error(f"Failed to search agents: {str(e)}")
            raise AgentServiceError(f"Failed to search agents: {str(e)}")
    
    # === PRIVATE METHODS ===
    
    async def _validate_create_request(self, request: AgentCreateRequest) -> None:
        """Validate agent create request."""
        # Check if agent ID already exists
        existing_agent = await self.repository.get_by_id(request.id)
        if existing_agent:
            raise AgentValidationError(f"Agent with ID {request.id} already exists")
        
        # Validate using AgentBuilder
        try:
            builder = (AgentBuilder()
                .with_id(request.id)
                .with_model(request.model)
                .with_stack(request.stack))
            
            if request.name:
                builder = builder.with_name(request.name)
            if request.specialty:
                builder.with_speciality(request.specialty)
            if request.persona:
                builder.with_persona(request.persona)
            if request.tools:
                builder.with_tools(request.tools)
            if request.metadata:
                builder.with_metadata(request.metadata)
            
            if not builder.validate():
                errors = builder.get_validation_errors()
                raise AgentValidationError(f"Validation failed: {', '.join(errors)}")
                
        except Exception as e:
            raise AgentValidationError(f"Agent configuration invalid: {str(e)}")
    
    async def _get_or_create_built_agent(self, agent_id: str) -> BuiltAgent:
        """Get or create built agent for execution."""
        if agent_id in self._active_agents:
            return self._active_agents[agent_id]
        
        # Get agent data from repository
        agent_data = await self.get_agent(agent_id)
        
        if agent_data is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")
        
        # Create built agent using AgentBuilder
        builder = (AgentBuilder()
            .with_id(agent_data['id'])
            .with_model(agent_data['model'])
            .with_stack(agent_data['stack']))
        
        if agent_data.get('name'):
            builder = builder.with_name(agent_data['name'])
        if agent_data.get('specialty'):
            builder = builder.with_speciality(agent_data['specialty'])
        if agent_data.get('persona'):
            builder.with_persona(agent_data['persona'])
        if agent_data.get('tools'):
            builder.with_tools(agent_data['tools'])
        if agent_data.get('metadata'):
            builder.with_metadata(agent_data['metadata'])
        
        # Add model config if exists
        if agent_data.get('model_config'):
            builder.with_model_config(**agent_data['model_config'])
        
        built_agent = builder.build()
        
        # Cache agent (with size limit)
        if len(self._active_agents) >= self.config['max_active_agents']:
            # Remove oldest agent (simple LRU)
            oldest_id = next(iter(self._active_agents))
            del self._active_agents[oldest_id]
        
        self._active_agents[agent_id] = built_agent
        
        return built_agent
    
    async def _update_execution_stats(self, agent_id: str, success: bool) -> None:
        """Update agent execution statistics."""
        if agent_id not in self._execution_stats:
            self._execution_stats[agent_id] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_execution_time': 0.0,
                'last_execution_at': None
            }
        
        stats = self._execution_stats[agent_id]
        stats['total_executions'] += 1
        stats['last_execution_at'] = datetime.utcnow().isoformat()
        
        if success:
            stats['successful_executions'] += 1
        else:
            stats['failed_executions'] += 1
        
        # Update agent in database
        await self.repository.update(agent_id, {
            'execution_count': stats['total_executions'],
            'last_executed_at': stats['last_execution_at']
        })


# === CONVENIENCE FUNCTIONS ===

def create_agent_service(repository: Optional[AgentRepository] = None) -> AgentService:
    """Create agent service with optional custom repository."""
    return AgentService(repository)


# === EXAMPLE USAGE ===

async def example_usage():
    """Example usage of AgentService."""
    
    # Create service
    service = create_agent_service()
    
    # Create agent
    create_request = AgentCreateRequest(
        id="example_agent",
        model="gpt-3.5-turbo",
        stack=["python"],
        name="Example Agent",
        specialty="General Assistant"
    )
    
    agent = await service.create_agent(create_request)
    print(f"Created agent: {agent['id']}")
    
    # Execute agent
    execution_request = AgentExecutionRequest(
        message="Hello, can you help me with Python?",
        user_id="user123"
    )
    
    response = await service.execute_agent(agent['id'], execution_request)
    print(f"Agent response: {response.message.content}")
    
    # Get stats
    stats = await service.get_agent_stats(agent['id'])
    print(f"Agent stats: {stats}")


if __name__ == "__main__":
    # Run example usage
    import asyncio
    asyncio.run(example_usage())
