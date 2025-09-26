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

# Core domain models

# Infrastructure models

# Export all models
__all__ = [
    # Base classes
    "BaseModel",
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
