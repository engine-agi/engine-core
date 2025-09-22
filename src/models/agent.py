"""
Agent model for Engine Framework.

An agent is an AI-powered entity with 11 configurable modules that can
perform tasks, execute workflows, and collaborate within teams.

The 11 agent modules provide comprehensive customization:
1. id (required) - Unique identifier
2. model (required) - AI model to use
3. name (optional) - Human-readable name
4. speciality (optional) - Domain expertise
5. persona (optional) - Personality and behavior
6. stack (required) - Technology capabilities
7. tools (optional) - External tool integrations
8. protocol (optional) - Command protocol
9. workflow (optional) - Personal workflow
10. book (optional) - Memory/knowledge base
11. config (optional) - Advanced configuration

Based on Engine Framework data model specification.
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from sqlalchemy import (
    Column, String, Text, Boolean, Float, Integer, 
    ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship, validates, backref
from datetime import datetime
import re
import json

from .base import BaseModel, StringIdentifierMixin, ConfigurationMixin, ValidationMixin, TimestampMixin

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .project import Project
    from .team import Team
    from .workflow import Workflow
    from .protocol import Protocol
    from .tool import Tool
    from .book import Book


class Agent(BaseModel, StringIdentifierMixin, ConfigurationMixin, ValidationMixin, TimestampMixin):
    """
    Agent entity - AI-powered entity with 11 configurable modules.
    
    Agents are the fundamental execution units in the Engine Framework.
    Each agent represents an AI model configured with specific capabilities,
    personality, tools, and behaviors to perform specialized tasks.
    
    The 11-module architecture provides maximum flexibility while maintaining
    simplicity - only 3 fields are required (id, model, stack), with 8 optional
    modules for progressive complexity.
    """
    
    __tablename__ = "agents"

    # === REQUIRED MODULES (3) ===
    
    # Module 1: id (inherited from StringIdentifierMixin)
    # Already defined in parent class
    
    # Module 2: model (REQUIRED)
    model = Column(
        String(100),
        nullable=False,
        index=True,
        comment="AI model identifier (e.g., 'claude-3.5-sonnet', 'gpt-4', 'llama-2-70b')"
    )
    
    # Module 3: stack (REQUIRED) 
    stack = Column(
        ARRAY(String(100)),
        nullable=False,
        comment="Technology stack capabilities (programming languages, frameworks, tools)"
    )

    # === OPTIONAL MODULES (8) ===
    
    # Module 4: name (optional)
    name = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Human-readable agent name"
    )
    
    # Module 5: speciality (optional)
    speciality = Column(
        Text,
        nullable=True,
        comment="Domain expertise and specialized capabilities"
    )
    
    # Module 6: persona (optional)
    persona = Column(
        Text,
        nullable=True,
        comment="Personality traits, communication style, and behavioral characteristics"
    )
    
    # Module 7: tools (optional) - References to Tool entities
    tools = Column(
        ARRAY(String(255)),
        nullable=True,
        comment="List of tool IDs this agent can use"
    )
    
    # Module 8: protocol (optional) - Reference to Protocol entity
    protocol_id = Column(
        String(255),
        ForeignKey("protocols.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Protocol ID defining agent's command structure and behavior"
    )
    
    # Module 9: workflow (optional) - Reference to Workflow entity  
    workflow_id = Column(
        String(255),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Personal workflow ID for individual task execution"
    )
    
    # Module 10: book (optional) - Reference to Book entity
    book_id = Column(
        String(255),
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Memory/knowledge base ID for context and learning"
    )
    
    # Module 11: config (optional) - Inherited from ConfigurationMixin
    # Advanced configuration already provided by parent class
    
    # === RELATIONSHIPS ===
    
    # Back-reference to project (set by project foreign key in junction table)
    project_id = Column(
        String(255),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Project this agent belongs to"
    )
    
    # Relationships
    protocol = relationship("Protocol", back_populates="agents")
    workflow = relationship("Workflow", back_populates="agents") 
    book = relationship("Book", back_populates="agents")
    project = relationship("Project", back_populates="agents")
    
    # === AGENT STATE AND EXECUTION ===
    
    status = Column(
        String(50),
        nullable=False,
        default="idle",
        index=True,
        comment="Current agent status"
    )
    
    # Execution metrics
    total_executions = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of executions performed"
    )
    
    successful_executions = Column(
        Integer,
        default=0,
        nullable=False, 
        comment="Number of successful executions"
    )
    
    average_execution_time = Column(
        Float,
        nullable=True,
        comment="Average execution time in seconds"
    )
    
    # Current execution context
    current_task = Column(
        String(255),
        nullable=True,
        comment="Currently executing task or workflow"
    )
    
    # Agent performance and learning
    performance_score = Column(
        Float,
        nullable=True,
        comment="Agent performance score (0.0 to 1.0)"
    )
    
    learning_data = Column(
        JSONB,
        nullable=True,
        comment="Learning history and adaptation data"
    )

    # Agent-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    agent_metadata = Column(
        JSONB,
        nullable=True,
        comment="Agent-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    def __init__(self, **kwargs):
        """Initialize agent with validation."""
        # Set defaults
        if 'status' not in kwargs:
            kwargs['status'] = 'idle'
        if 'total_executions' not in kwargs:
            kwargs['total_executions'] = 0
        if 'successful_executions' not in kwargs:
            kwargs['successful_executions'] = 0
            
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Agent(id='{self.id}', name='{self.name}', model='{self.model}')>"

    # === VALIDATION METHODS ===

    @validates('id')
    def validate_id(self, key: str, value: str) -> str:
        """Validate agent ID format."""
        if not value:
            raise ValueError("Agent ID is required")
        
        # Must be alphanumeric with underscores, 2-100 characters
        if not re.match(r'^[a-zA-Z0-9_]{2,100}$', value):
            raise ValueError(
                "Agent ID must be 2-100 characters, containing only "
                "letters, numbers, and underscores"
            )
        
        return value.lower()  # Normalize to lowercase

    @validates('model')
    def validate_model(self, key: str, value: str) -> str:
        """Validate AI model identifier."""
        if not value or not value.strip():
            raise ValueError("AI model is required")
        
        # List of supported models (can be extended)
        supported_models = [
            'claude-3.5-sonnet', 'claude-3-haiku', 'claude-3-opus',
            'gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo',
            'llama-2-70b', 'llama-2-13b', 'llama-2-7b',
            'mistral-7b', 'mixtral-8x7b',
            'gemini-pro', 'gemini-1.5-pro',
            'palm-2', 'palm-2-chat'
        ]
        
        value = value.strip().lower()
        if value not in supported_models:
            raise ValueError(f"Model '{value}' not supported. Supported models: {', '.join(supported_models)}")
        
        return value

    @validates('stack')
    def validate_stack(self, key: str, value: List[str]) -> List[str]:
        """Validate technology stack."""
        if not value or not isinstance(value, list):
            raise ValueError("Technology stack is required and must be a list")
        
        if len(value) == 0:
            raise ValueError("At least one technology must be specified in stack")
        
        # Validate each stack item
        valid_stack_items = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("All stack items must be non-empty strings")
            
            item = item.strip().lower()
            if item not in valid_stack_items:
                valid_stack_items.append(item)
        
        if len(valid_stack_items) > 20:
            raise ValueError("Maximum 20 technologies allowed in stack")
        
        return valid_stack_items

    @validates('name')
    def validate_name(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate agent name."""
        if value is not None:
            value = value.strip()
            if len(value) > 255:
                raise ValueError("Agent name cannot exceed 255 characters")
            return value if value else None
        return value

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate agent status."""
        valid_statuses = ['idle', 'active', 'busy', 'error', 'offline', 'maintenance']
        
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return value

    @validates('performance_score')
    def validate_performance_score(self, key: str, value: Optional[float]) -> Optional[float]:
        """Validate performance score."""
        if value is not None:
            if not 0.0 <= value <= 1.0:
                raise ValueError("Performance score must be between 0.0 and 1.0")
        return value

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent data before creating/updating."""
        validated = data.copy()
        
        # Required fields validation
        required_fields = ['id', 'model', 'stack']
        for field in required_fields:
            if field not in validated or not validated[field]:
                raise ValueError(f"Agent {field} is required")
        
        # Validate tools references
        if 'tools' in validated and validated['tools']:
            if not isinstance(validated['tools'], list):
                raise ValueError("Tools must be a list of tool IDs")
            
            for tool_id in validated['tools']:
                if not isinstance(tool_id, str) or not tool_id.strip():
                    raise ValueError("All tool IDs must be non-empty strings")
        
        # Validate configuration
        if 'config' in validated and validated['config']:
            if not isinstance(validated['config'], dict):
                raise ValueError("Config must be a dictionary")
            
            # Validate specific config fields
            config = validated['config']
            
            if 'temperature' in config:
                temp = config['temperature']
                if not isinstance(temp, (int, float)) or not 0.0 <= temp <= 2.0:
                    raise ValueError("Temperature must be a number between 0.0 and 2.0")
            
            if 'max_tokens' in config:
                tokens = config['max_tokens']
                if not isinstance(tokens, int) or not 1 <= tokens <= 100000:
                    raise ValueError("Max tokens must be an integer between 1 and 100,000")
        
        return validated

    def validate_instance(self) -> List[str]:
        """Validate agent instance and return list of errors."""
        errors = []
        
        # Validate required fields
        if not getattr(self, 'id', None):
            errors.append("Agent ID is required")
        
        if not getattr(self, 'model', None):
            errors.append("AI model is required")
        
        stack = getattr(self, 'stack', None)
        if not stack or len(stack) == 0:
            errors.append("Technology stack is required")
        
        # Validate consistency
        successful_executions = getattr(self, 'successful_executions', 0)
        total_executions = getattr(self, 'total_executions', 0)
        if successful_executions > total_executions:
            errors.append("Successful executions cannot exceed total executions")
        
        # Validate references exist (would need database queries in real implementation)
        # For now, just validate they are properly formatted
        
        return errors

    # === UTILITY METHODS ===

    def has_capability(self, technology: str) -> bool:
        """Check if agent has specific technology capability."""
        stack = getattr(self, 'stack', None)
        if not stack:
            return False
        
        tech_lower = technology.lower()
        return tech_lower in [item.lower() for item in stack]

    def add_capability(self, technology: str) -> None:
        """Add technology capability to agent stack."""
        stack = getattr(self, 'stack', None)
        if not stack:
            self.stack = []
            stack = []
        
        tech_lower = technology.lower()
        if not self.has_capability(tech_lower):
            stack.append(tech_lower)
            self.stack = stack

    def remove_capability(self, technology: str) -> None:
        """Remove technology capability from agent stack."""
        stack = getattr(self, 'stack', None)
        if stack:
            tech_lower = technology.lower()
            self.stack = [item for item in stack if item.lower() != tech_lower]

    def add_tool(self, tool_id: str) -> None:
        """Add tool reference to agent."""
        tools = getattr(self, 'tools', None)
        if not tools:
            self.tools = []
            tools = []
        
        if tool_id not in tools:
            tools.append(tool_id)
            self.tools = tools

    def remove_tool(self, tool_id: str) -> None:
        """Remove tool reference from agent."""
        tools = getattr(self, 'tools', None)
        if tools and tool_id in tools:
            tools.remove(tool_id)
            self.tools = tools

    def update_execution_stats(
        self, 
        execution_time: float, 
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update agent execution statistics."""
        # Get current values using getattr
        total_executions = getattr(self, 'total_executions', 0) + 1
        successful_executions = getattr(self, 'successful_executions', 0)
        
        if success:
            successful_executions += 1
        
        # Update instance attributes
        self.total_executions = total_executions
        self.successful_executions = successful_executions
        
        # Update average execution time
        current_avg = getattr(self, 'average_execution_time', None)
        if current_avg is None:
            self.average_execution_time = execution_time
        else:
            # Running average calculation
            total_time = current_avg * (total_executions - 1) + execution_time
            self.average_execution_time = total_time / total_executions
        
        # Update performance score based on success rate
        self.performance_score = successful_executions / total_executions
        
        # Store learning data
        if metadata:
            learning_data = getattr(self, 'learning_data', None)
            if learning_data is None:
                learning_data = {'executions': []}
            
            executions = learning_data['executions']
            executions.append({
                'timestamp': datetime.utcnow().isoformat(),
                'execution_time': execution_time,
                'success': success,
                'metadata': metadata
            })
            
            # Keep only last 100 execution records
            if len(executions) > 100:
                executions = executions[-100:]
            
            learning_data['executions'] = executions
            self.learning_data = learning_data

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get summary of agent capabilities."""
        stack = getattr(self, 'stack', None) or []
        tools = getattr(self, 'tools', None) or []
        total_executions = getattr(self, 'total_executions', 0)
        successful_executions = getattr(self, 'successful_executions', 0)
        
        return {
            'id': getattr(self, 'id', None),
            'name': getattr(self, 'name', None),
            'model': getattr(self, 'model', None),
            'speciality': getattr(self, 'speciality', None),
            'technology_count': len(stack),
            'technologies': stack,
            'tools_count': len(tools),
            'has_protocol': getattr(self, 'protocol_id', None) is not None,
            'has_workflow': getattr(self, 'workflow_id', None) is not None,
            'has_memory': getattr(self, 'book_id', None) is not None,
            'status': getattr(self, 'status', None),
            'performance_score': getattr(self, 'performance_score', None),
            'success_rate': (successful_executions / total_executions 
                           if total_executions > 0 else None),
            'total_executions': total_executions
        }

    def reset_stats(self) -> None:
        """Reset agent execution statistics."""
        self.total_executions = 0
        self.successful_executions = 0
        self.average_execution_time = None
        self.performance_score = None
        self.learning_data = None

    @classmethod
    def create_minimal(cls, agent_id: str, model: str, stack: List[str]) -> "Agent":
        """Create agent with minimal required configuration (3 modules)."""
        return cls(
            id=agent_id,
            model=model,
            stack=stack
        )

    @classmethod
    def create_complete(
        cls,
        agent_id: str,
        model: str,
        stack: List[str],
        name: Optional[str] = None,
        speciality: Optional[str] = None,
        persona: Optional[str] = None,
        tools: Optional[List[str]] = None,
        protocol_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        book_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> "Agent":
        """Create agent with all 11 modules configured."""
        return cls(
            id=agent_id,
            model=model,
            stack=stack,
            name=name,
            speciality=speciality,
            persona=persona,
            tools=tools,
            protocol_id=protocol_id,
            workflow_id=workflow_id,
            book_id=book_id,
            config=config
        )


# Database indexes for performance
Index('idx_agent_model_status', Agent.model, Agent.status)
Index('idx_agent_project_status', Agent.project_id, Agent.status)
# Note: Performance and execution indexes removed due to type conflicts

# Database constraints
CheckConstraint(
    Agent.status.in_(['idle', 'active', 'busy', 'error', 'offline', 'maintenance']),
    name='ck_agent_status_valid'
)

# Note: Execution and performance constraints removed due to type conflicts
