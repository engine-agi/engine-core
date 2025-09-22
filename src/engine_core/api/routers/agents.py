"""
Agents API Router - Engine Framework Agent Management.

This router provides comprehensive agent management endpoints including CRUD operations,
configuration management, and execution capabilities.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from datetime import datetime

from ..schemas.agent_schemas import (
    AgentCreateSchema,
    AgentUpdateSchema,
    AgentResponseSchema,
    AgentListResponseSchema,
    AgentHealthSchema,
    AgentMetricsSchema
)
from ..schemas.base_schemas import BaseResponseSchema, ErrorResponseSchema
from ...core.agents import AgentBuilder, Agent

# Create router instance
router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={
        404: {"description": "Agent not found"},
        400: {"description": "Invalid request data"},
        500: {"description": "Internal server error"},
    }
)

# In-memory storage for demo purposes (would be replaced with proper persistence)
_agents_storage: Dict[str, Agent] = {}


def get_agent_or_404(agent_id: str) -> Agent:
    """Get agent by ID or raise 404."""
    if agent_id not in _agents_storage:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return _agents_storage[agent_id]


@router.post("/", response_model=AgentResponseSchema)
async def create_agent(agent_data: AgentCreateSchema = Body(...)):
    """Create a new agent."""
    try:
        # Create agent using AgentBuilder
        agent = (AgentBuilder()
            .with_id(f"agent_{len(_agents_storage) + 1}")
            .with_name(agent_data.name)
            .with_model(agent_data.model)
            .with_speciality(agent_data.speciality)
            .with_persona(agent_data.persona)
            .with_stack(agent_data.stack)
            .with_tools(agent_data.tools)
            .build())

        # Store agent
        _agents_storage[agent.id] = agent

        return AgentResponseSchema(
            id=agent.id,
            name=agent.name,
            model=agent.model,
            speciality=agent.speciality,
            persona=agent.persona,
            stack=agent.stack,
            tools=agent.tools,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            protocol_id=agent_data.protocol_id,
            workflow_id=agent_data.workflow_id,
            book_id=agent_data.book_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("/", response_model=AgentListResponseSchema)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of agents to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of agents to return")
):
    """List all agents."""
    try:
        agents = list(_agents_storage.values())[skip:skip + limit]

        agent_responses = []
        for agent in agents:
            agent_responses.append(AgentResponseSchema(
                id=agent.id,
                name=agent.name,
                model=agent.model,
                speciality=agent.speciality,
                persona=agent.persona,
                stack=agent.stack,
                tools=agent.tools,
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                protocol_id=None,
                workflow_id=None,
                book_id=None
            ))

        return AgentListResponseSchema(
            success=True,
            message="Agents retrieved successfully",
            timestamp=datetime.utcnow(),
            agents=agent_responses,
            pagination={
                "skip": skip,
                "limit": limit,
                "total": len(_agents_storage)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/{agent_id}", response_model=AgentResponseSchema)
async def get_agent(agent_id: str = Path(..., description="Agent ID")):
    """Get a specific agent by ID."""
    try:
        agent = get_agent_or_404(agent_id)

        return AgentResponseSchema(
            id=agent.id,
            name=agent.name,
            model=agent.model,
            speciality=agent.speciality,
            persona=agent.persona,
            stack=agent.stack,
            tools=agent.tools,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            protocol_id=None,
            workflow_id=None,
            book_id=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")


@router.put("/{agent_id}", response_model=AgentResponseSchema)
async def update_agent(
    agent_id: str = Path(..., description="Agent ID"),
    agent_data: AgentUpdateSchema = Body(...)
):
    """Update an agent."""
    try:
        agent = get_agent_or_404(agent_id)

        # Update fields if provided
        if agent_data.name is not None:
            agent.name = agent_data.name
        if agent_data.model is not None:
            agent.model = agent_data.model
        if agent_data.speciality is not None:
            agent.speciality = agent_data.speciality
        if agent_data.persona is not None:
            agent.persona = agent_data.persona
        if agent_data.stack is not None:
            agent.stack = agent_data.stack
        if agent_data.tools is not None:
            agent.tools = agent_data.tools

        return AgentResponseSchema(
            id=agent.id,
            name=agent.name,
            model=agent.model,
            speciality=agent.speciality,
            persona=agent.persona,
            stack=agent.stack,
            tools=agent.tools,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            protocol_id=None,
            workflow_id=None,
            book_id=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")


@router.delete("/{agent_id}", response_model=BaseResponseSchema)
async def delete_agent(agent_id: str = Path(..., description="Agent ID")):
    """Delete an agent."""
    try:
        agent = get_agent_or_404(agent_id)

        # Remove from storage
        del _agents_storage[agent_id]

        return BaseResponseSchema(
            success=True,
            message=f"Agent {agent_id} deleted successfully",
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


@router.get("/{agent_id}/health", response_model=AgentHealthSchema)
async def get_agent_health(agent_id: str = Path(..., description="Agent ID")):
    """Get agent health status."""
    try:
        agent = get_agent_or_404(agent_id)

        return AgentHealthSchema(
            agent_id=agent.id,
            status="healthy",
            last_seen=datetime.utcnow(),
            metrics={
                "uptime": 3600,  # Mock uptime
                "tasks_completed": 42,
                "active": True
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent health: {str(e)}")


@router.get("/health")
async def agents_health():
    """Health check endpoint for agents service."""
    return {
        "service": "agents",
        "status": "healthy",
        "agents_count": len(_agents_storage),
        "timestamp": datetime.utcnow().isoformat()
    }