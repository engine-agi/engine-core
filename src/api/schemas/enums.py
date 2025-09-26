# Enums for API Schemas
# This module contains all enumeration types used in the API schemas

from enum import Enum


class AgentStatus(str, Enum):
    """Agent status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"


class TeamCoordinationStrategy(str, Enum):
    """Team coordination strategy enumeration."""

    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolType(str, Enum):
    """Tool type enumeration."""

    API = "api"
    CLI = "cli"
    MCP = "mcp"
    WEB = "web"


class ProtocolType(str, Enum):
    """Protocol type enumeration."""

    SEMANTIC = "semantic"
    WORKFLOW = "workflow"
    COMMAND = "command"
    CUSTOM = "custom"


class BookLanguage(str, Enum):
    """Book language enumeration."""

    EN = "en"
    PT = "pt"
    ES = "es"
    FR = "fr"
    DE = "de"


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuthenticationType(str, Enum):
    """Authentication type enumeration."""

    NONE = "none"
    BASIC = "basic"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class ContentType(str, Enum):
    """Content type enumeration."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    XML = "xml"


class ProficiencyLevel(str, Enum):
    """Proficiency level enumeration."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class RelationshipType(str, Enum):
    """Relationship type enumeration."""

    REPORTS_TO = "reports_to"
    COLLABORATES_WITH = "collaborates_with"
    LEADS = "leads"
    SUPPORTS = "supports"


class VertexType(str, Enum):
    """Workflow vertex type enumeration."""

    AGENT_TASK = "agent_task"
    HUMAN_TASK = "human_task"
    SYSTEM_TASK = "system_task"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"


class EdgeType(str, Enum):
    """Workflow edge type enumeration."""

    SEQUENCE = "sequence"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    LOOP = "loop"


class CommandType(str, Enum):
    """Protocol command type enumeration."""

    SEMANTIC = "semantic"
    DIRECT = "direct"
    COMPOSITE = "composite"


class ParameterType(str, Enum):
    """Parameter type enumeration."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


class SearchType(str, Enum):
    """Search type enumeration."""

    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    FUZZY = "fuzzy"
    EXACT = "exact"


class EmbeddingModel(str, Enum):
    """Embedding model enumeration."""

    SENTENCE_TRANSFORMERS = "sentence-transformers/all-mpnet-base-v2"
    OPENAI_ADA = "text-embedding-ada-002"
    COHERE = "embed-multilingual-v2.0"
