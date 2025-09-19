"""
Agent Configuration Models - Pydantic schemas for Engine Framework agents.

This module defines the data models for agent configuration with all 11 modules:
- Required: id, model, stack (minimal configuration)
- Optional: name, speciality, persona, tools, protocol_id, workflow_id, book_id

Based on Engine Framework Agent architecture supporting:
- Progressive configuration (minimal → complete)
- Validation and type safety with Pydantic
- Integration with other pillars (protocols, workflows, tools, books)
- Builder pattern compatibility
"""

from typing import Dict, Any, List, Optional, Union, Set
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime


class AgentStatus(str, Enum):
    """Agent execution status enumeration."""
    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    ERROR = "error"
    DISABLED = "disabled"


class AgentModel(str, Enum):
    """Supported AI models enumeration."""
    CLAUDE_3_5_SONNET = "claude-3.5-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    LOCAL_LLAMA = "local-llama"
    LOCAL_MISTRAL = "local-mistral"


class AgentConfig(BaseModel):
    """
    Complete agent configuration with all 11 modules.

    Supports progressive configuration:
    - Minimal: id, model, stack (3 required fields)
    - Complete: All 11 modules with full customization
    """

    # Required fields (minimal configuration)
    id: str = Field(..., description="Unique agent identifier", min_length=1, max_length=100)
    model: AgentModel = Field(..., description="AI model for agent execution")
    stack: List[str] = Field(..., description="Technology stack (programming languages, frameworks)")

    # Optional fields (progressive configuration)
    name: Optional[str] = Field(None, description="Human-readable agent name", max_length=200)
    speciality: Optional[str] = Field(None, description="Agent's domain expertise", max_length=500)
    persona: Optional[str] = Field(None, description="Behavioral characteristics and personality", max_length=1000)
    tools: Optional[List[str]] = Field(None, description="Tool IDs available to the agent")
    protocol_id: Optional[str] = Field(None, description="Associated protocol identifier")
    workflow_id: Optional[str] = Field(None, description="Associated workflow identifier")
    book_id: Optional[str] = Field(None, description="Associated memory book identifier")

    # Metadata (auto-generated)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: AgentStatus = Field(default=AgentStatus.IDLE)
    project_id: Optional[str] = Field(None, description="Parent project identifier")
    version: str = Field(default="1.0.0", description="Configuration version")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict(exclude_unset=True, exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create configuration from dictionary."""
        return cls(**data)

    def is_minimal(self) -> bool:
        """Check if configuration is minimal (only required fields)."""
        optional_fields = ['name', 'speciality', 'persona', 'tools', 'protocol_id', 'workflow_id', 'book_id']
        return all(getattr(self, field) is None for field in optional_fields)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging/debugging."""
        return {
            'id': self.id,
            'model': self.model,
            'stack': self.stack,
            'name': self.name,
            'speciality': self.speciality,
            'has_tools': bool(self.tools),
            'has_protocol': bool(self.protocol_id),
            'has_workflow': bool(self.workflow_id),
            'has_book': bool(self.book_id),
            'status': self.status,
            'is_minimal': self.is_minimal()
        }
class AgentExecutionConfig(BaseModel):
    """
    Configuration for agent execution context.

    Defines execution parameters, timeouts, and resource limits.
    """

    max_execution_time: int = Field(default=300, description="Maximum execution time in seconds", ge=1, le=3600)
    max_memory_mb: int = Field(default=512, description="Maximum memory usage in MB", ge=64, le=4096)
    max_concurrent_tasks: int = Field(default=5, description="Maximum concurrent tasks", ge=1, le=20)
    retry_attempts: int = Field(default=3, description="Number of retry attempts on failure", ge=0, le=10)
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds", ge=0.1, le=60.0)

    enable_logging: bool = Field(default=True, description="Enable execution logging")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentValidationResult(BaseModel):
    """
    Result of agent configuration validation.

    Used by builders and services to report validation status.
    """

    is_valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Validation warning messages")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")

    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add validation warning."""
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """Add improvement suggestion."""
        self.suggestions.append(message)

    def has_issues(self) -> bool:
        """Check if there are any errors or warnings."""
        return bool(self.errors or self.warnings)


class AgentTemplate(BaseModel):
    """
    Template for agent configuration.

    Used for creating agents from predefined templates.
    """

    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Template category (e.g., 'development', 'analysis')")

    base_config: AgentConfig = Field(..., description="Base agent configuration")
    required_customizations: List[str] = Field(default_factory=list, description="Fields that must be customized")

    tags: List[str] = Field(default_factory=list, description="Template tags for search")
    version: str = Field(default="1.0.0", description="Template version")

    def is_compatible(self, customizations: Dict[str, Any]) -> bool:
        """Check if customizations are compatible with template."""
        return all(field in customizations for field in self.required_customizations)

    def apply_customizations(self, customizations: Dict[str, Any]) -> AgentConfig:
        """Apply customizations to base configuration."""
        config_dict = self.base_config.dict()
        config_dict.update(customizations)
        return AgentConfig(**config_dict)
