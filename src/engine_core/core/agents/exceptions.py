"""
Engine Framework Exceptions - Custom exceptions for the Engine Framework.

This module defines all custom exceptions used throughout the Engine Framework
for proper error handling and debugging. Exceptions are organized by component
and include detailed error messages and context.

Based on Engine Framework error handling patterns and best practices.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class EngineException(Exception):
    """
    Base exception for all Engine Framework errors.

    Provides common functionality for error handling, logging, and debugging.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None,
        recoverable: bool = False,
    ):
        """
        Initialize Engine exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error context and data
            component: Component where error occurred
            recoverable: Whether the error is recoverable
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "ENGINE_ERROR"
        self.details = details or {}
        self.component = component or "unknown"
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "component": self.component,
            "details": self.details,
            "recoverable": self.recoverable,
            "exception_type": self.__class__.__name__,
        }

    def __str__(self) -> str:
        """String representation with error code."""
        return f"[{self.error_code}] {self.message}"


# Agent-related exceptions
class AgentException(EngineException):
    """Base exception for agent-related errors."""

    pass


class AgentConfigurationError(AgentException):
    """Raised when agent configuration is invalid."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code="AGENT_CONFIG_ERROR",
            component="agent",
            details={"field": field, "value": value, "suggestions": suggestions or []},
        )


class AgentExecutionError(AgentException):
    """Raised when agent execution fails."""

    def __init__(
        self,
        message: str,
        task: Optional[str] = None,
        execution_time: Optional[float] = None,
        retry_count: Optional[int] = None,
    ):
        super().__init__(
            message=message,
            error_code="AGENT_EXECUTION_ERROR",
            component="agent",
            details={
                "task": task,
                "execution_time": execution_time,
                "retry_count": retry_count,
            },
        )


class AgentNotFoundError(AgentException):
    """Raised when requested agent is not found."""

    def __init__(self, agent_id: str, project_id: Optional[str] = None):
        super().__init__(
            message=f"Agent '{agent_id}' not found",
            error_code="AGENT_NOT_FOUND",
            component="agent",
            details={"agent_id": agent_id, "project_id": project_id},
        )


class AgentStateError(AgentException):
    """Raised when agent is in invalid state for operation."""

    def __init__(
        self,
        agent_id: str,
        current_state: str,
        required_state: Optional[str] = None,
        operation: Optional[str] = None,
    ):
        super().__init__(
            message=f"Agent '{agent_id}' is in invalid state for operation",
            error_code="AGENT_STATE_ERROR",
            component="agent",
            details={
                "agent_id": agent_id,
                "current_state": current_state,
                "required_state": required_state,
                "operation": operation,
            },
        )


# Builder-related exceptions
class BuilderException(EngineException):
    """Base exception for builder-related errors."""

    pass


class BuilderConfigurationError(BuilderException):
    """Raised when builder configuration is invalid."""

    def __init__(
        self,
        message: str,
        builder_type: str,
        missing_fields: Optional[List[str]] = None,
        invalid_fields: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            error_code="BUILDER_CONFIG_ERROR",
            component="builder",
            details={
                "builder_type": builder_type,
                "missing_fields": missing_fields or [],
                "invalid_fields": invalid_fields or {},
            },
        )


class BuilderValidationError(BuilderException):
    """Raised when builder validation fails."""

    def __init__(
        self,
        message: str,
        builder_type: str,
        validation_errors: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code="BUILDER_VALIDATION_ERROR",
            component="builder",
            details={
                "builder_type": builder_type,
                "validation_errors": validation_errors or [],
            },
        )


# Protocol-related exceptions
class ProtocolException(EngineException):
    """Base exception for protocol-related errors."""

    pass


class ProtocolNotFoundError(ProtocolException):
    """Raised when requested protocol is not found."""

    def __init__(self, protocol_id: str):
        super().__init__(
            message=f"Protocol '{protocol_id}' not found",
            error_code="PROTOCOL_NOT_FOUND",
            component="protocol",
            details={"protocol_id": protocol_id},
        )


class ProtocolExecutionError(ProtocolException):
    """Raised when protocol execution fails."""

    def __init__(
        self,
        message: str,
        protocol_id: str,
        command: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="PROTOCOL_EXECUTION_ERROR",
            component="protocol",
            details={
                "protocol_id": protocol_id,
                "command": command,
                "context": context,
            },
        )


class ProtocolValidationError(ProtocolException):
    """Raised when protocol validation fails."""

    def __init__(
        self,
        message: str,
        protocol_id: str,
        validation_errors: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code="PROTOCOL_VALIDATION_ERROR",
            component="protocol",
            details={
                "protocol_id": protocol_id,
                "validation_errors": validation_errors or [],
            },
        )


# Workflow-related exceptions
class WorkflowException(EngineException):
    """Base exception for workflow-related errors."""

    pass


class WorkflowNotFoundError(WorkflowException):
    """Raised when requested workflow is not found."""

    def __init__(self, workflow_id: str):
        super().__init__(
            message=f"Workflow '{workflow_id}' not found",
            error_code="WORKFLOW_NOT_FOUND",
            component="workflow",
            details={"workflow_id": workflow_id},
        )


class WorkflowExecutionError(WorkflowException):
    """Raised when workflow execution fails."""

    def __init__(
        self,
        message: str,
        workflow_id: str,
        vertex_id: Optional[str] = None,
        edge_id: Optional[str] = None,
        execution_state: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="WORKFLOW_EXECUTION_ERROR",
            component="workflow",
            details={
                "workflow_id": workflow_id,
                "vertex_id": vertex_id,
                "edge_id": edge_id,
                "execution_state": execution_state,
            },
        )


class WorkflowValidationError(WorkflowException):
    """Raised when workflow validation fails."""

    def __init__(
        self,
        message: str,
        workflow_id: str,
        validation_errors: Optional[List[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code="WORKFLOW_VALIDATION_ERROR",
            component="workflow",
            details={
                "workflow_id": workflow_id,
                "validation_errors": validation_errors or [],
            },
        )


# Tool-related exceptions
class ToolException(EngineException):
    """Base exception for tool-related errors."""

    pass


class ToolNotFoundError(ToolException):
    """Raised when requested tool is not found."""

    def __init__(self, tool_id: str):
        super().__init__(
            message=f"Tool '{tool_id}' not found",
            error_code="TOOL_NOT_FOUND",
            component="tool",
            details={"tool_id": tool_id},
        )


class ToolExecutionError(ToolException):
    """Raised when tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_id: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        stderr: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="TOOL_EXECUTION_ERROR",
            component="tool",
            details={
                "tool_id": tool_id,
                "command": command,
                "exit_code": exit_code,
                "stderr": stderr,
            },
        )


class ToolConfigurationError(ToolException):
    """Raised when tool configuration is invalid."""

    def __init__(
        self,
        message: str,
        tool_id: str,
        config_field: Optional[str] = None,
        config_value: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="TOOL_CONFIG_ERROR",
            component="tool",
            details={
                "tool_id": tool_id,
                "config_field": config_field,
                "config_value": config_value,
            },
        )


# Book/Memory-related exceptions
class BookException(EngineException):
    """Base exception for book/memory-related errors."""

    pass


class BookNotFoundError(BookException):
    """Raised when requested book is not found."""

    def __init__(self, book_id: str):
        super().__init__(
            message=f"Book '{book_id}' not found",
            error_code="BOOK_NOT_FOUND",
            component="book",
            details={"book_id": book_id},
        )


class BookOperationError(BookException):
    """Raised when book operation fails."""

    def __init__(
        self,
        message: str,
        book_id: str,
        operation: str,
        chapter_id: Optional[str] = None,
        page_id: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="BOOK_OPERATION_ERROR",
            component="book",
            details={
                "book_id": book_id,
                "operation": operation,
                "chapter_id": chapter_id,
                "page_id": page_id,
            },
        )


# Team-related exceptions
class TeamException(EngineException):
    """Base exception for team-related errors."""

    pass


class TeamNotFoundError(TeamException):
    """Raised when requested team is not found."""

    def __init__(self, team_id: str):
        super().__init__(
            message=f"Team '{team_id}' not found",
            error_code="TEAM_NOT_FOUND",
            component="team",
            details={"team_id": team_id},
        )


class TeamCoordinationError(TeamException):
    """Raised when team coordination fails."""

    def __init__(
        self,
        message: str,
        team_id: str,
        agent_id: Optional[str] = None,
        coordination_strategy: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="TEAM_COORDINATION_ERROR",
            component="team",
            details={
                "team_id": team_id,
                "agent_id": agent_id,
                "coordination_strategy": coordination_strategy,
            },
        )


# Project-related exceptions
class ProjectException(EngineException):
    """Base exception for project-related errors."""

    pass


class ProjectNotFoundError(ProjectException):
    """Raised when requested project is not found."""

    def __init__(self, project_id: str):
        super().__init__(
            message=f"Project '{project_id}' not found",
            error_code="PROJECT_NOT_FOUND",
            component="project",
            details={"project_id": project_id},
        )


class ProjectOperationError(ProjectException):
    """Raised when project operation fails."""

    def __init__(
        self,
        message: str,
        project_id: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="PROJECT_OPERATION_ERROR",
            component="project",
            details={
                "project_id": project_id,
                "operation": operation,
                **(details or {}),
            },
        )


# Configuration and validation exceptions
class ConfigurationException(EngineException):
    """Base exception for configuration-related errors."""

    pass


class ValidationError(ConfigurationException):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            component="validation",
            details={"field": field, "value": value, "expected_type": expected_type},
        )


class ConfigurationLoadError(ConfigurationException):
    """Raised when configuration loading fails."""

    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        config_format: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="CONFIG_LOAD_ERROR",
            component="configuration",
            details={"config_path": config_path, "config_format": config_format},
        )


# AI/Model-related exceptions
class ModelException(EngineException):
    """Base exception for AI model-related errors."""

    pass


class ModelNotFoundError(ModelException):
    """Raised when requested AI model is not available."""

    def __init__(self, model_name: str, available_models: Optional[List[str]] = None):
        super().__init__(
            message=f"AI model '{model_name}' not found or not available",
            error_code="MODEL_NOT_FOUND",
            component="model",
            details={
                "model_name": model_name,
                "available_models": available_models or [],
            },
        )


class ModelExecutionError(ModelException):
    """Raised when AI model execution fails."""

    def __init__(
        self,
        message: str,
        model_name: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        api_error: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="MODEL_EXECUTION_ERROR",
            component="model",
            details={
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "api_error": api_error,
            },
        )


class ModelRateLimitError(ModelException):
    """Raised when AI model rate limit is exceeded."""

    def __init__(
        self, message: str, model_name: str, retry_after: Optional[int] = None
    ):
        super().__init__(
            message=message,
            error_code="MODEL_RATE_LIMIT",
            component="model",
            recoverable=True,
            details={"model_name": model_name, "retry_after": retry_after},
        )


# Utility functions for error handling
def format_error_chain(exc: Exception) -> str:
    """
    Format a chain of exceptions for logging.

    Args:
        exc: The exception to format

    Returns:
        Formatted error string
    """
    errors = []
    current = exc

    while current:
        if isinstance(current, EngineException):
            errors.append(f"{current.error_code}: {current.message}")
        else:
            errors.append(f"{current.__class__.__name__}: {str(current)}")

        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )

    return " | ".join(errors)


def create_error_response(exc: Exception) -> Dict[str, Any]:
    """
    Create a standardized error response from an exception.

    Args:
        exc: The exception to convert

    Returns:
        Error response dictionary
    """
    if isinstance(exc, EngineException):
        return {
            "success": False,
            "error": exc.to_dict(),
            "timestamp": json.dumps(None),  # Will be set by response handler
        }

    return {
        "success": False,
        "error": {
            "error_code": "UNKNOWN_ERROR",
            "message": str(exc),
            "component": "unknown",
            "details": {},
            "exception_type": exc.__class__.__name__,
        },
        "timestamp": json.dumps(None),
    }
