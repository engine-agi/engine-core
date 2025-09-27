"""




SQLAlchemy models package initialization.

This module exports all SQLAlchemy models for the Engine Framework.
Models are organized by domain:

- Base: Common base classes and mixins
- Core Entities: Project, Agent, Team, Workflow, Protocol, Tool, Book
- Infrastructure: User, Session, Log

Usage:
    from models import Project, Agent, Team
    from models.base import BaseModel
"""


# Base classes and mixins
from pydantic import BaseModel
from .base import (
    StringIdentifierMixin,
    ConfigurationMixin,
    ValidationMixin,
)

# Core domain models
from .project import Project
from .agent import Agent
from .team import Team
from .workflow import Workflow, WorkflowVertex, WorkflowEdge
from .protocol import Protocol
from .tool import Tool
from .book import Book, BookChapter, BookPage

# Infrastructure models
from .infrastructure import User, Session, Log

# Export all models
__all__ = [
    # Base classes
    "StringIdentifierMixin",
    "ConfigurationMixin",
    "ValidationMixin",
    # Core models
    "Project",
    "Agent",
    "Team",
    "Workflow",
    "WorkflowVertex",
    "WorkflowEdge",
    "Protocol",
    "Tool",
    "Book",
    "BookChapter",
    "BookPage",
    # Infrastructure models
    "User",
    "Session",
    "Log",
]
