"""


Shared Types module for Engine Framework.

This module contains common types, enumerations, and base classes used across
all Engine Framework components.
"""

from .engine_types import (
    # Status enumerations
    AgentStatus,
    TeamStatus,
    WorkflowStatus,
    ExecutionMode,
    ProtocolStatus,
    ToolStatus,
    ToolType,
    BookStatus,
    ProjectStatus,
    LogLevel,
    CoordinationStrategy,

    # Base classes
    EngineError,

    # Utility classes
    PaginationParams,
    SearchFilters,
    ExecutionContext,

    # Type aliases
    AgentId,
    TeamId,
    WorkflowId,
    ProtocolId,
    ToolId,
    BookId,
    ProjectId,
    UserId,

    # Constants
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DEFAULT_TIMEOUT,
    MAX_TIMEOUT,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_TAGS_PER_ITEM,
    MAX_ITEMS_PER_PAGE,
)

__all__ = [
    # Status enumerations
    "AgentStatus",
    "TeamStatus",
    "WorkflowStatus",
    "ExecutionMode",
    "ProtocolStatus",
    "ToolStatus",
    "ToolType",
    "BookStatus",
    "ProjectStatus",
    "LogLevel",
    "CoordinationStrategy",

    # Base classes
    "EngineError",

    # Utility classes
    "PaginationParams",
    "SearchFilters",
    "ExecutionContext",

    # Type aliases
    "AgentId",
    "TeamId",
    "WorkflowId",
    "ProtocolId",
    "ToolId",
    "BookId",
    "ProjectId",
    "UserId",

    # Constants
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DEFAULT_TIMEOUT",
    "MAX_TIMEOUT",
    "MAX_NAME_LENGTH",
    "MAX_DESCRIPTION_LENGTH",
    "MAX_TAGS_PER_ITEM",
    "MAX_ITEMS_PER_PAGE",
]
