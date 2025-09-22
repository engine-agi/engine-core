"""
Tests for engine_types.py - Shared types and enumerations.

Tests serialization, validation, and compatibility of shared types.
"""

import pytest
import json
from datetime import datetime, timezone
from engine_core.engine_types import (
    AgentStatus, TeamStatus, WorkflowStatus, ExecutionMode,
    ProtocolStatus, ToolStatus, ToolType, BookStatus,
    ProjectStatus, LogLevel, CoordinationStrategy,
    EngineError, PaginationParams, SearchFilters, ExecutionContext,
    AgentId, TeamId, WorkflowId, ProtocolId, ToolId, BookId,
    ProjectId, UserId,
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, DEFAULT_TIMEOUT, MAX_TIMEOUT,
    MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH, MAX_TAGS_PER_ITEM, MAX_ITEMS_PER_PAGE
)


class TestStatusEnums:
    """Test all status enumerations."""

    def test_agent_status_values(self):
        """Test AgentStatus enum values."""
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.ACTIVE == "active"
        assert AgentStatus.PROCESSING == "processing"
        assert AgentStatus.ERROR == "error"
        assert AgentStatus.DISABLED == "disabled"

    def test_team_status_values(self):
        """Test TeamStatus enum values."""
        assert TeamStatus.FORMING == "forming"
        assert TeamStatus.ACTIVE == "active"
        assert TeamStatus.EXECUTING == "executing"
        assert TeamStatus.DISBANDED == "disbanded"

    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.DRAFT == "draft"
        assert WorkflowStatus.READY == "ready"
        assert WorkflowStatus.EXECUTING == "executing"
        assert WorkflowStatus.COMPLETED == "completed"
        assert WorkflowStatus.FAILED == "failed"
        assert WorkflowStatus.PAUSED == "paused"


class TestEnumSerialization:
    """Test serialization/deserialization of enums."""

    def test_agent_status_json_serialization(self):
        """Test AgentStatus JSON serialization."""
        status = AgentStatus.ACTIVE
        json_str = json.dumps(status.value)
        deserialized = json.loads(json_str)
        assert deserialized == "active"
        reconstructed = AgentStatus(deserialized)
        assert reconstructed == status


class TestEngineError:
    """Test EngineError class."""

    def test_basic_error_creation(self):
        """Test basic error creation."""
        error = EngineError("Test error")
        assert error.message == "Test error"
        assert error.error_code == "ENGINE_ERROR"
        assert error.component == "unknown"
        assert error.recoverable is False
        assert error.details == {}
        assert isinstance(error.timestamp, datetime)

    def test_error_to_dict(self):
        """Test error serialization to dict."""
        error = EngineError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"test": "data"},
            component="test",
            recoverable=True
        )
        error_dict = error.to_dict()

        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["component"] == "test"
        assert error_dict["details"] == {"test": "data"}
        assert error_dict["recoverable"] is True
        assert "timestamp" in error_dict


class TestPaginationParams:
    """Test PaginationParams class."""

    def test_default_pagination(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        assert params.page == 1
        assert params.limit == 50
        assert params.offset == 0
        assert params.sort_by is None
        assert params.sort_order == "asc"

    def test_custom_pagination(self):
        """Test custom pagination parameters."""
        params = PaginationParams(page=2, limit=25, sort_by="name", sort_order="desc")
        assert params.page == 2
        assert params.limit == 25
        assert params.offset == 25
        assert params.sort_by == "name"
        assert params.sort_order == "desc"


class TestConstants:
    """Test constants."""

    def test_pagination_constants(self):
        """Test pagination-related constants."""
        assert DEFAULT_PAGE_SIZE == 50
        assert MAX_PAGE_SIZE == 100
        assert MAX_ITEMS_PER_PAGE == 100

    def test_timeout_constants(self):
        """Test timeout-related constants."""
        assert DEFAULT_TIMEOUT == 300  # 5 minutes
        assert MAX_TIMEOUT == 3600     # 1 hour

    def test_validation_constants(self):
        """Test validation-related constants."""
        assert MAX_NAME_LENGTH == 100
        assert MAX_DESCRIPTION_LENGTH == 1000
        assert MAX_TAGS_PER_ITEM == 10


class TestCompatibility:
    """Test backward compatibility and edge cases."""

    def test_enum_backward_compatibility(self):
        """Test that enum values haven't changed."""
        # This test ensures we don't accidentally change enum values
        # which would break existing serialized data
        assert AgentStatus.IDLE.value == "idle"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert ToolType.API.value == "api"

    def test_error_backward_compatibility(self):
        """Test that EngineError interface hasn't changed."""
        error = EngineError("test")
        # These methods/attributes should always exist
        assert hasattr(error, 'message')
        assert hasattr(error, 'error_code')
        assert hasattr(error, 'to_dict')
        assert hasattr(error, 'timestamp')
        assert hasattr(error, '__str__')

    def test_class_backward_compatibility(self):
        """Test that class interfaces haven't changed."""
        # PaginationParams
        params = PaginationParams()
        assert hasattr(params, 'page')
        assert hasattr(params, 'limit')
        assert hasattr(params, 'offset')

        # SearchFilters
        filters = SearchFilters()
        assert hasattr(filters, 'query')
        assert hasattr(filters, 'tags')

        # ExecutionContext
        context = ExecutionContext()
        assert hasattr(context, 'user_id')
        assert hasattr(context, 'get_duration')
        assert hasattr(context, 'to_dict')


class TestSearchFilters:
    """Test SearchFilters class."""

    def test_default_filters(self):
        """Test default search filters."""
        filters = SearchFilters()
        assert filters.query is None
        assert filters.tags == []
        assert filters.status is None
        assert filters.created_after is None
        assert filters.created_before is None
        assert filters.updated_after is None
        assert filters.updated_before is None

    def test_custom_filters(self):
        """Test custom search filters."""
        now = datetime.now(timezone.utc)
        filters = SearchFilters(
            query="test query",
            tags=["tag1", "tag2"],
            status="active",
            created_after=now,
            created_before=now,
            updated_after=now,
            updated_before=now
        )
        assert filters.query == "test query"
        assert filters.tags == ["tag1", "tag2"]
        assert filters.status == "active"
        assert filters.created_after == now
        assert filters.created_before == now
        assert filters.updated_after == now
        assert filters.updated_before == now


class TestExecutionContext:
    """Test ExecutionContext class."""

    def test_default_context(self):
        """Test default execution context."""
        context = ExecutionContext()
        assert context.user_id is None
        assert context.project_id is None
        assert context.session_id is None
        assert context.correlation_id is None
        assert context.metadata == {}
        assert isinstance(context.start_time, datetime)

    def test_custom_context(self):
        """Test custom execution context."""
        metadata = {"key": "value"}
        context = ExecutionContext(
            user_id="user123",
            project_id="project456",
            session_id="session789",
            correlation_id="corr123",
            metadata=metadata
        )
        assert context.user_id == "user123"
        assert context.project_id == "project456"
        assert context.session_id == "session789"
        assert context.correlation_id == "corr123"
        assert context.metadata == metadata

    def test_context_duration(self):
        """Test execution duration calculation."""
        context = ExecutionContext()
        duration = context.get_duration()
        assert duration >= 0
        assert isinstance(duration, float)

    def test_context_to_dict(self):
        """Test context serialization to dict."""
        context = ExecutionContext(
            user_id="user123",
            correlation_id="corr123",
            metadata={"test": "data"}
        )
        context_dict = context.to_dict()

        assert context_dict["user_id"] == "user123"
        assert context_dict["correlation_id"] == "corr123"
        assert context_dict["metadata"] == {"test": "data"}
        assert "start_time" in context_dict
        assert "duration" in context_dict
        assert context_dict["duration"] >= 0


class TestTypeAliases:
    """Test type aliases."""

    def test_type_aliases_are_strings(self):
        """Test that type aliases are string types."""
        # These should all be str type
        assert AgentId.__name__ == "str"
        assert TeamId.__name__ == "str"
        assert WorkflowId.__name__ == "str"
        assert ProtocolId.__name__ == "str"
        assert ToolId.__name__ == "str"
        assert BookId.__name__ == "str"
        assert ProjectId.__name__ == "str"
        assert UserId.__name__ == "str"