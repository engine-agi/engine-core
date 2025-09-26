# Engine Core Framework
# AI Agent Orchestration System - Core Components

__version__ = "1.0.0"
__author__ = "Engine Framework Team"
__description__ = "Core framework for AI agent orchestration"

# Core imports - only import what doesn't require database connections
from .core.agents import AgentBuilder
from .core.teams import TeamBuilder
from .core.workflows import WorkflowBuilder, WorkflowEngine
from .core.tools import ToolBuilder, ToolExecutor
from .core.book import BookBuilder
from .core.protocols import ProtocolBuilder
from .core.workflows.workflow_engine import WorkflowState
from .core.book.book_builder import ContentType, AccessLevel, ContentStatus, SearchScope, SearchQuery
from .core.teams.team_builder import TeamCoordinationStrategy, TeamMemberRole
from .core.protocols.protocol import IntentCategory, CommandType, ContextScope, CommandContext

__all__ = [
    'AgentBuilder',
    'TeamBuilder',
    'WorkflowBuilder',
    'WorkflowEngine',
    'ToolBuilder',
    'ToolExecutor',
    'BookBuilder',
    'ProtocolBuilder',
    'WorkflowState',
    'ContentType',
    'AccessLevel',
    'ContentStatus',
    'SearchScope',
    'SearchQuery',
    'TeamCoordinationStrategy',
    'TeamMemberRole',
    'IntentCategory',
    'CommandType',
    'ContextScope',
    'CommandContext',
    '__version__'
]