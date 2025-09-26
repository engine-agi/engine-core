"""
Observability API Router
Handles project observability including structured logs and real-time metrics.

This router provides endpoints for monitoring project activities through comprehensive
logging and metrics collection across all engine components.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.api.dependencies import get_current_user
from src.core.project_service import ProjectService
from src.engine_core.api.schemas.enums import LogLevel
from src.engine_core.engine_types import EngineError


class LogEntry(BaseModel):
    """Log entry model"""

    id: str
    level: str
    message: str
    entity_type: str
    entity_id: str
    action: str
    timestamp: datetime
    duration_ms: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None


class ProjectMetrics(BaseModel):
    """Project metrics summary"""

    agents: Dict[str, int]
    teams: Dict[str, int]
    workflows: Dict[str, int]
    success_rate: float
    average_response_time: float
    total_requests: int
    error_count: int
    last_updated: datetime


class PerformanceMetrics(BaseModel):
    """Performance metrics model"""

    cpu_usage: float
    memory_usage: float
    active_connections: int
    requests_per_second: float
    average_latency_ms: float


class LogsResponse(BaseModel):
    """Logs response model"""

    logs: List[LogEntry]
    total: int
    page: int
    limit: int


class MetricsResponse(BaseModel):
    """Metrics response model"""

    project_metrics: ProjectMetrics
    performance_metrics: PerformanceMetrics


# Create router instance
router = APIRouter(
    prefix="/projects/{project_id}",
    tags=["observability"],
    responses={
        404: {"description": "Project not found"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
    },
)


@router.get("/logs", response_model=LogsResponse)
async def get_project_logs(
    project_id: str,
    level: Optional[str] = Query(None, description="Log level filter"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(None, description="Filter by specific entity"),
    start_time: Optional[datetime] = Query(None, description="Start timestamp filter"),
    end_time: Optional[datetime] = Query(None, description="End timestamp filter"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    current_user: dict = Depends(get_current_user),
    observability_service=Depends(),
    project_service: ProjectService = Depends(),
) -> LogsResponse:
    """
    Get logs for a project.

    Returns structured logs for all activities within the project, with support
    for filtering by level, entity, time range, and pagination.

    Query Parameters:
    - level: Filter by log level (debug, info, warning, error, critical)
    - entity_type: Filter by entity type (agent, team, workflow, tool, etc.)
    - entity_id: Filter by specific entity ID
    - start_time: Start timestamp for time-based filtering
    - end_time: End timestamp for time-based filtering
    - limit: Maximum number of results (default: 100, max: 1000)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate log level if provided
        if level:
            try:
                LogLevel(level.upper())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid log level: {level}"
                )

        # Set default time range if not provided (last 24 hours)
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()

        # Validate time range
        if start_time > end_time:
            raise HTTPException(
                status_code=400, detail="start_time cannot be after end_time"
            )

        # Get logs with filters
        logs_result = await observability_service.get_logs(
            project_id=project_id,
            level_filter=level.upper() if level else None,
            entity_type_filter=entity_type,
            entity_id_filter=entity_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )

        # Convert to response format
        logs = [
            LogEntry(
                id=log.get("id", ""),
                level=log.get("level", "info").lower(),
                message=log.get("message", ""),
                entity_type=log.get("entity_type", ""),
                entity_id=log.get("entity_id", ""),
                action=log.get("action", ""),
                timestamp=log.get("timestamp", ""),
                duration_ms=log.get("duration_ms"),
                additional_data=log.get("additional_data", {}),
            )
            for log in logs_result.logs
        ]

        # Calculate page number
        page = (offset // limit) + 1

        return LogsResponse(logs=logs, total=logs_result.total, page=page, limit=limit)

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as _:  # noqa: F841
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics", response_model=MetricsResponse)
async def get_project_metrics(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    observability_service=Depends(),
    project_service: ProjectService = Depends(),
):
    """
    Get real-time metrics for a project.

    Returns comprehensive metrics including agent status, team activities,
    workflow executions, success rates, and performance indicators.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get project metrics
        project_metrics_data = await observability_service.get_project_metrics(
            project_id
        )

        # Get performance metrics
        performance_metrics_data = await observability_service.get_performance_metrics(
            project_id
        )

        # Prepare response
        project_metrics = ProjectMetrics(
            agents={
                "total": project_metrics_data.agents.total,
                "active": project_metrics_data.agents.active,
                "idle": project_metrics_data.agents.idle,
                "processing": project_metrics_data.agents.processing,
                "error": project_metrics_data.agents.error,
            },
            teams={
                "total": project_metrics_data.teams.total,
                "active": project_metrics_data.teams.active,
                "executing": project_metrics_data.teams.executing,
                "disbanded": project_metrics_data.teams.disbanded,
            },
            workflows={
                "total": project_metrics_data.workflows.total,
                "running": project_metrics_data.workflows.running,
                "completed": project_metrics_data.workflows.completed,
                "failed": project_metrics_data.workflows.failed,
                "paused": project_metrics_data.workflows.paused,
            },
            success_rate=project_metrics_data.success_rate,
            average_response_time=project_metrics_data.average_response_time,
            total_requests=project_metrics_data.total_requests,
            error_count=project_metrics_data.error_count,
            last_updated=project_metrics_data.last_updated or datetime.utcnow(),
        )

        performance_metrics = PerformanceMetrics(
            cpu_usage=performance_metrics_data.cpu_usage,
            memory_usage=performance_metrics_data.memory_usage,
            active_connections=performance_metrics_data.active_connections,
            requests_per_second=performance_metrics_data.requests_per_second,
            average_latency_ms=performance_metrics_data.average_latency_ms,
        )

        return MetricsResponse(
            project_metrics=project_metrics, performance_metrics=performance_metrics
        )

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as _:  # noqa: F841
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def project_health(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    observability_service=Depends(),
    project_service: ProjectService = Depends(),
):
    """
    Get project health status.

    Returns overall health status of the project including component status,
    error rates, and system availability.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get health status
        health_data = await observability_service.get_project_health(project_id)

        return {
            "project_id": project_id,
            "status": health_data.status,
            "components": {
                "agents": {
                    "status": health_data.components.agents.status,
                    "healthy_count": health_data.components.agents.healthy_count,
                    "total_count": health_data.components.agents.total_count,
                },
                "teams": {
                    "status": health_data.components.teams.status,
                    "healthy_count": health_data.components.teams.healthy_count,
                    "total_count": health_data.components.teams.total_count,
                },
                "workflows": {
                    "status": health_data.components.workflows.status,
                    "healthy_count": health_data.components.workflows.healthy_count,
                    "total_count": health_data.components.workflows.total_count,
                },
                "tools": {
                    "status": health_data.components.tools.status,
                    "healthy_count": health_data.components.tools.healthy_count,
                    "total_count": health_data.components.tools.total_count,
                },
            },
            "error_rate": health_data.error_rate,
            "availability": health_data.availability,
            "last_updated": health_data.last_updated,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as _:  # noqa: F841
        raise HTTPException(status_code=500, detail="Internal server error")


# Stream real-time metrics endpoint
@router.get("/metrics/stream")
async def stream_project_metrics(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    observability_service=Depends(),
    project_service: ProjectService = Depends(),
):
    """
    Stream real-time project metrics.

    Provides a streaming endpoint for real-time metrics updates.
    Clients should use WebSocket connections for live updates.
    """
    try:
        # Verify project exists and user has access
        project = await project_service.get_project(project_id, current_user["id"])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Return streaming connection info
        return {
            "message": "Use WebSocket connection for real-time metrics streaming",
            "websocket_url": f"ws://localhost:8000/ws/projects/{project_id}",
            "supported_events": [
                "AGENT_STATUS_CHANGED",
                "TEAM_EXECUTION_STARTED",
                "WORKFLOW_COMPLETED",
                "METRICS_UPDATED",
            ],
            "instructions": "Subscribe to 'metrics' event type for real-time updates",
        }

    except HTTPException:
        raise
    except EngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as _:  # noqa: F841
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for observability service
@router.get("/observability/health")
async def observability_health():
    """Health check endpoint for observability service"""
    return {
        "service": "observability",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": [
            "structured_logging",
            "real_time_metrics",
            "performance_monitoring",
            "health_checks",
            "websocket_streaming",
        ],
    }
