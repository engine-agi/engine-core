"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime
from typing import Optional, List, Dict, Any
Engine Types - Common types and enumerations for the Engine Framework.

This module defines shared types, enumerations, and base classes used across
all Engine Framework components. It provides type safety and consistency
for status tracking, error handling, and data validation.

Key Components:
- Status enumerations for all pillars
- Base error classes
- Common data types
- Type aliases and constants
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# Status Enumerations
class AgentStatus(str, Enum):
    """Agent execution and lifecycle status."""

    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    ERROR = "error"
    DISABLED = "disabled"


class TeamStatus(str, Enum):
    """Team coordination status."""

    FORMING = "forming"
    ACTIVE = "active"
    EXECUTING = "executing"
    DISBANDED = "disbanded"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    DRAFT = "draft"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ExecutionMode(str, Enum):
    """Workflow execution modes."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


class ProtocolStatus(str, Enum):
    """Protocol validation status."""

    DRAFT = "draft"
    VALID = "valid"
    INVALID = "invalid"
    ACTIVE = "active"


class ToolStatus(str, Enum):
    """Tool availability status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ToolType(str, Enum):
    """Tool integration types."""

    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    MCP = "mcp"
    WEBHOOK = "webhook"


class BookStatus(str, Enum):
    """Book lifecycle status."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class LogLevel(str, Enum):
    """Logging levels for observability."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CoordinationStrategy(str, Enum):
    """Team coordination strategies."""

    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    PARALLEL = "parallel"


# Base Error Classes
class EngineError(Exception):
    """
    Base exception for all Engine Framework errors.

    Provides structured error information for better debugging and error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None,
        recoverable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "ENGINE_ERROR"
        self.details = details or {}
        self.component = component or "unknown"
        self.recoverable = recoverable
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "component": self.component,
            "details": self.details,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


# Common Data Types
class PaginationParams:
    """Parameters for paginated requests."""

    def __init__(
        self,
        page: int = 1,
        limit: int = 50,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ):
        self.page = max(1, page)
        self.limit = max(1, min(100, limit))  # Max 100 items per page
        self.offset = (self.page - 1) * self.limit
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()

        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "asc"


class SearchFilters:
    """Common search and filtering parameters."""

    def __init__(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
    ):
        self.query = query
        self.tags = tags or []
        self.status = status
        self.created_after = created_after
        self.created_before = created_before
        self.updated_after = updated_after
        self.updated_before = updated_before


class ExecutionContext:
    """Context information for execution operations."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.user_id = user_id
        self.project_id = project_id
        self.session_id = session_id
        self.correlation_id = correlation_id
        self.metadata = metadata or {}
        self.start_time = datetime.now(timezone.utc)

    def get_duration(self) -> float:
        """Get execution duration in seconds."""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "user_id": self.user_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat(),
            "duration": self.get_duration(),
        }


# Type Aliases
AgentId = str
TeamId = str
WorkflowId = str
ProtocolId = str
ToolId = str
BookId = str
ProjectId = str
UserId = str

# Constants
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100
DEFAULT_TIMEOUT = 300  # 5 minutes
MAX_TIMEOUT = 3600  # 1 hour

# Validation Constants
MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 1000
MAX_TAGS_PER_ITEM = 10
MAX_ITEMS_PER_PAGE = 100
