"""
Protocol model for Engine Framework.

Protocols define command structures and semantic behavior patterns
for agents and teams. They specify:
- Available commands with parameters and semantic meaning
- Execution order and dependencies
- Validation rules and constraints
- Context-aware command selection

Based on Engine Framework data model specification.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, CheckConstraint, Column, ForeignKey, Index, Integer,
    String, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates

from .base import SQLAlchemyBaseModel
import re

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .agent import Agent
    from .team import Team


class Protocol(SQLAlchemyBaseModel):
    """
    Protocol entity - defines command structure and behavior patterns.

    Protocols provide structured command sets that define how agents
    and teams interact with their environment. They specify available
    commands, execution patterns, and semantic meanings to enable
    consistent and predictable behavior.

    Key features:
    - Semantic command definitions with parameters
    - Execution order and dependency management
    - Context-aware command selection
    - Validation rules for command usage
    - Integration with agent and team behavior
    """

    __tablename__ = "protocols"

    # Basic protocol information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable protocol name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Protocol purpose, usage patterns, and behavior"
    )

    # Protocol classification
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Protocol category (e.g., 'analysis', 'development', 'coordination')"
    )

    version = Column(
        String(50),
        nullable=False,
        default="1.0",
        comment="Protocol version for change management"
    )

    # Protocol status
    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        comment="Protocol status (active, deprecated, experimental)"
    )

    # Command structure
    commands = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="List of commands with parameters and semantic meanings"
    )

    # Validation and execution rules
    validation_rules = Column(
        JSONB,
        nullable=True,
        comment="Validation rules for command usage and execution"
    )

    execution_order = Column(
        JSONB,
        nullable=True,
        comment="Command execution order and dependency constraints"
    )

    # Context and conditions
    context_requirements = Column(
        JSONB,
        nullable=True,
        comment="Context requirements for protocol activation"
    )

    # Protocol metrics
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times protocol has been used"
    )

    # Semantic processing
    semantic_patterns = Column(
        JSONB,
        nullable=True,
        comment="Semantic patterns for command interpretation and matching"
    )

    # Protocol-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    protocol_metadata = Column(
        JSONB,
        nullable=True,
        comment="Protocol-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    def __init__(self, **kwargs):
        """Initialize protocol with validation."""
        # Set defaults
        if 'status' not in kwargs:
            kwargs['status'] = 'active'
        if 'version' not in kwargs:
            kwargs['version'] = '1.0'
        if 'commands' not in kwargs:
            kwargs['commands'] = []
        if 'usage_count' not in kwargs:
            kwargs['usage_count'] = 0

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        commands = getattr(self, 'commands') or []
        command_count = len(commands) if commands else 0
        return f"<Protocol(id='{self.id}', name='{self.name}', commands={command_count})>"

    # === VALIDATION METHODS ===

    @validates('id')
    def validate_id(self, key: str, value: str) -> str:
        """Validate protocol ID format."""
        if not value:
            raise ValueError("Protocol ID is required")

        # Must be alphanumeric with underscores, 2-100 characters
        if not re.match(r'^[a-zA-Z0-9_]{2,100}$', value):
            raise ValueError(
                "Protocol ID must be 2-100 characters, containing only "
                "letters, numbers, and underscores"
            )

        return value.lower()

    @validates('name')
    def validate_name(self, key: str, value: str) -> str:
        """Validate protocol name."""
        if not value or not value.strip():
            raise ValueError("Protocol name is required")

        if len(value.strip()) > 255:
            raise ValueError("Protocol name cannot exceed 255 characters")

        return value.strip()

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate protocol status."""
        valid_statuses = ['active', 'deprecated', 'experimental', 'archived']

        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        return value

    @validates('commands')
    def validate_commands(self, key: str, value: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate commands structure."""
        if not isinstance(value, list):
            raise ValueError("Commands must be a list")

        if len(value) == 0:
            raise ValueError("Protocol must have at least one command")

        # Validate each command structure
        for i, command in enumerate(value):
            if not isinstance(command, dict):
                raise ValueError(f"Command {i} must be a dictionary")

            # Required fields
            if 'name' not in command or not command['name']:
                raise ValueError(f"Command {i} must have a name")

            if 'description' not in command:
                raise ValueError(f"Command {i} must have a description")

            # Validate command name format
            if not re.match(r'^[a-zA-Z0-9_]{2,100}$', command['name']):
                raise ValueError(
                    f"Command {i} name must be 2-100 characters, "
                    "containing only letters, numbers, and underscores"
                )

            # Validate parameters if present
            if 'parameters' in command and command['parameters']:
                if not isinstance(command['parameters'], list):
                    raise ValueError(f"Command {i} parameters must be a list")

                for param in command['parameters']:
                    if not isinstance(param, str):
                        raise ValueError(f"Command {i} parameters must be strings")

            # Validate semantic meaning if present
            if 'semantic_meaning' in command and command['semantic_meaning']:
                if not isinstance(command['semantic_meaning'], str):
                    raise ValueError(f"Command {i} semantic_meaning must be a string")

        return value

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate protocol data before creating/updating."""
        validated = data.copy()

        # Required fields
        if 'id' not in validated or not validated['id']:
            raise ValueError("Protocol ID is required")

        if 'name' not in validated or not validated['name']:
            raise ValueError("Protocol name is required")

        if 'commands' not in validated or not validated['commands']:
            raise ValueError("Protocol commands are required")

        # Validate validation rules structure
        if 'validation_rules' in validated and validated['validation_rules']:
            if not isinstance(validated['validation_rules'], list):
                raise ValueError("Validation rules must be a list")

        # Validate execution order structure
        if 'execution_order' in validated and validated['execution_order']:
            if not isinstance(validated['execution_order'], dict):
                raise ValueError("Execution order must be a dictionary")

        return validated

    # === PROTOCOL COMMAND MANAGEMENT ===

    def add_command(
        self,
        name: str,
        description: str,
        parameters: Optional[List[str]] = None,
        semantic_meaning: Optional[str] = None,
        **kwargs
    ) -> None:
        """Add command to protocol."""
        commands = getattr(self, 'commands') or []
        if not commands:
            commands = []

        # Check for duplicate command names
        existing_names = [cmd['name'] for cmd in commands]
        if name in existing_names:
            raise ValueError(f"Command '{name}' already exists in protocol")

        command = {
            'name': name,
            'description': description,
            'parameters': parameters or [],
            'semantic_meaning': semantic_meaning,
            **kwargs
        }

        commands.append(command)
        setattr(self, 'commands', commands)

    def remove_command(self, name: str) -> None:
        """Remove command from protocol."""
        commands = getattr(self, 'commands') or []
        if commands:
            commands = [cmd for cmd in commands if cmd.get('name') != name]
            setattr(self, 'commands', commands)

    def get_command(self, name: str) -> Optional[Dict[str, Any]]:
        """Get command by name."""
        commands = getattr(self, 'commands') or []
        if commands:
            for command in commands:
                if command.get('name') == name:
                    return command
        return None

    def has_command(self, name: str) -> bool:
        """Check if protocol has specific command."""
        return self.get_command(name) is not None

    def find_commands_by_semantic_meaning(self, meaning: str) -> List[Dict[str, Any]]:
        """Find commands with specific semantic meaning."""
        commands = getattr(self, 'commands') or []
        if not commands:
            return []

        return [
            cmd for cmd in commands
            if cmd.get('semantic_meaning') == meaning
        ]

    # === VALIDATION RULE MANAGEMENT ===

    def add_validation_rule(self, rule: str) -> None:
        """Add validation rule to protocol."""
        validation_rules = getattr(self, 'validation_rules') or []
        if not validation_rules:
            validation_rules = []

        if rule not in validation_rules:
            validation_rules.append(rule)
            setattr(self, 'validation_rules', validation_rules)

    def remove_validation_rule(self, rule: str) -> None:
        """Remove validation rule from protocol."""
        validation_rules = getattr(self, 'validation_rules') or []
        if validation_rules and rule in validation_rules:
            validation_rules.remove(rule)
            setattr(self, 'validation_rules', validation_rules)

    def validate_command_usage(self, command_name: str, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate command usage against protocol rules."""
        errors = []

        # Check if command exists
        command = self.get_command(command_name)
        if not command:
            errors.append(f"Command '{command_name}' not found in protocol")
            return False, errors

        # Apply validation rules
        validation_rules = getattr(self, 'validation_rules') or []
        if validation_rules:
            for rule in validation_rules:
                # Simple rule evaluation (in real implementation, this would be more sophisticated)
                if rule == "analysis_required_before_implementation":
                    if command.get('semantic_meaning') == 'implementation':
                        if not context.get('analysis_completed'):
                            errors.append(
                                "Analysis must be completed before implementation")

                elif rule == "specification_must_be_complete":
                    if command.get('semantic_meaning') == 'validation':
                        if not context.get('specification_complete'):
                            errors.append(
                                "Specification must be complete before validation")

        return len(errors) == 0, errors

    # === EXECUTION ORDER MANAGEMENT ===

    def set_execution_order(self, order: Dict[str, Any]) -> None:
        """Set command execution order."""
        self.execution_order = order

    def get_next_commands(self, current_command: str, context: Dict[str, Any]) -> List[str]:
        """Get next commands in execution order."""
        execution_order = getattr(self, 'execution_order')
        if not execution_order:
            return []

        # Simple implementation - in real system this would be more sophisticated
        next_commands = execution_order.get(current_command, [])

        # Filter based on context if needed
        filtered_commands = []
        for cmd in next_commands:
            if isinstance(cmd, dict):
                # Conditional next command
                condition = cmd.get('condition')
                command_name = cmd.get('command')
                if self._evaluate_condition(condition, context):
                    filtered_commands.append(command_name)
            else:
                # Simple next command
                filtered_commands.append(cmd)

        return filtered_commands

    def _evaluate_condition(self, condition: Optional[str], context: Dict[str, Any]) -> bool:
        """Evaluate execution condition (simplified)."""
        if not condition:
            return True

        # Simple condition evaluation
        # In real implementation, this would use a proper expression evaluator
        if condition == "success":
            return context.get('success', False)
        elif condition == "analysis_complete":
            return context.get('analysis_complete', False)
        elif condition == "validation_passed":
            return context.get('validation_passed', False)

        return True

    # === SEMANTIC PROCESSING ===

    def add_semantic_pattern(self, pattern: str, meaning: str) -> None:
        """Add semantic pattern for command interpretation."""
        semantic_patterns = getattr(self, 'semantic_patterns') or {}
        if not semantic_patterns:
            semantic_patterns = {}

        semantic_patterns[pattern] = meaning
        setattr(self, 'semantic_patterns', semantic_patterns)

    def interpret_command(self, input_text: str) -> Optional[Dict[str, Any]]:
        """Interpret natural language input as protocol command."""
        semantic_patterns = getattr(self, 'semantic_patterns') or {}
        if not semantic_patterns:
            return None

        input_lower = input_text.lower()

        # Simple pattern matching (in real implementation, would use NLP)
        for pattern, meaning in semantic_patterns.items():
            if pattern.lower() in input_lower:
                # Find commands with this semantic meaning
                matching_commands = self.find_commands_by_semantic_meaning(meaning)
                if matching_commands:
                    return {
                        'command': matching_commands[0],
                        'semantic_meaning': meaning,
                        'confidence': 0.8,  # Simplified confidence score
                        'input_text': input_text
                    }

        return None

    # === PROTOCOL USAGE AND METRICS ===

    def increment_usage(self) -> None:
        """Increment protocol usage counter."""
        self.usage_count += 1

    def get_protocol_summary(self) -> Dict[str, Any]:
        """Get protocol summary information."""
        commands = getattr(self, 'commands') or []
        validation_rules = getattr(self, 'validation_rules') or []
        execution_order = getattr(self, 'execution_order')
        semantic_patterns = getattr(self, 'semantic_patterns')
        created_at = getattr(self, 'created_at')
        updated_at = getattr(self, 'updated_at')

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'version': self.version,
            'status': self.status,
            'command_count': len(commands) if commands else 0,
            'commands': [cmd.get('name') for cmd in (commands or [])],
            'validation_rule_count': len(validation_rules) if validation_rules else 0,
            'usage_count': self.usage_count,
            'has_execution_order': execution_order is not None,
            'has_semantic_patterns': semantic_patterns is not None,
            'created_at': created_at.isoformat() if created_at else None,
            'updated_at': updated_at.isoformat() if updated_at else None
        }

    @classmethod
    def create_analysis_first_protocol(cls) -> "Protocol":
        """Create the 'analysis_first' protocol from quickstart examples."""
        commands = [
            {
                'name': 'analyze_requirements',
                'description': 'Analyze project requirements and create technical specification',
                'parameters': ['requirements', 'tech_stack', 'constraints'],
                'semantic_meaning': 'deep_analysis'
            },
            {
                'name': 'validate_approach',
                'description': 'Validate technical approach and architecture decisions',
                'parameters': ['architecture', 'dependencies', 'risks'],
                'semantic_meaning': 'validation'
            },
            {
                'name': 'implement_solution',
                'description': 'Implement solution based on validated analysis',
                'parameters': ['specification', 'tests', 'code'],
                'semantic_meaning': 'implementation'
            }
        ]

        validation_rules = [
            'analysis_required_before_implementation',
            'specification_must_be_complete',
            'validation_required_for_architecture'
        ]

        execution_order = {
            'analyze_requirements': ['validate_approach'],
            'validate_approach': ['implement_solution'],
            'implement_solution': []
        }

        return cls(
            id='analysis_first',
            name='Analysis First Protocol',
            description='Requires thorough analysis before implementation',
            category='development',
            commands=commands,
            validation_rules=validation_rules,
            execution_order=execution_order
        )


# Database indexes for performance
Index('idx_protocol_category_status', Protocol.category, Protocol.status)
Index('idx_protocol_usage_count', Protocol.usage_count.desc())
Index('idx_protocol_version', Protocol.id, Protocol.version)

# Database constraints
CheckConstraint(
    Protocol.status.in_(['active', 'deprecated', 'experimental', 'archived']),
    name='ck_protocol_status_valid'
)

CheckConstraint(
    Protocol.usage_count >= 0,
    name='ck_protocol_usage_count_non_negative'
)
