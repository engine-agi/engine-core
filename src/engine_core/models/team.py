"""
Team model for Engine Framework.

A team coordinates multiple agents to work together on complex tasks.
Teams provide orchestration, coordination strategies, and hierarchical
organization for collaborative AI agent work.

Team coordination strategies:
- Hierarchical: Leader-based with clear chain of command
- Collaborative: Equal participation with consensus decisions
- Parallel: Independent work with synchronized results

Based on Engine Framework data model specification.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean, CheckConstraint, Column, ForeignKey, Index, Integer,
    String, Table, Text, MetaData
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates

from .base import SQLAlchemyBaseModel, metadata
import re

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .agent import Agent
    from .book import Book
    from .project import Project
    from .protocol import Protocol
    from .workflow import Workflow

# Many-to-many association table for team-agent relationships
team_agents = Table(
    'team_agents',
    metadata,
    Column('team_id', String(255), ForeignKey(
        'teams.id', ondelete='CASCADE'), primary_key=True),
    Column('agent_id', String(255), ForeignKey(
        'agents.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(100), nullable=True, comment='Agent role within the team'),
    Column('joined_at', String(50), nullable=True,
           comment='When agent joined the team'),
    Column('is_active', Boolean, default=True,
           comment='Whether agent is active in team')
)


class Team(SQLAlchemyBaseModel):
    """
    Team entity - coordinates multiple agents for collaborative work.

    Teams provide structured coordination between multiple AI agents,
    enabling complex multi-step workflows that require specialized
    expertise and collaborative decision-making.

    Key features:
    - Multiple coordination strategies (hierarchical, collaborative, parallel)
    - Flexible member management with roles
    - Team-level protocols and workflows
    - Shared memory/knowledge base
    - Execution monitoring and coordination
    """

    __tablename__ = "teams"

    # Basic team information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable team name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Team purpose, objectives, and working methods"
    )

    # Team coordination strategy
    coordination = Column(
        String(50),
        nullable=False,
        default="collaborative",
        index=True,
        comment="Team coordination strategy"
    )

    # Team hierarchy and leadership (for hierarchical coordination)
    hierarchy = Column(
        JSONB,
        nullable=True,
        comment="Team hierarchy structure with leaders and reporting relationships"
    )

    # Project association
    project_id = Column(
        String(255),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Project this team belongs to"
    )

    # Team-level protocol (overrides individual agent protocols)
    protocol_id = Column(
        String(255),
        ForeignKey("protocols.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Team protocol that overrides individual agent protocols"
    )

    # Team-level workflow
    workflow_id = Column(
        String(255),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Team workflow for coordinated execution"
    )

    # Shared team memory
    book_id = Column(
        String(255),
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Shared team memory/knowledge base"
    )

    # Team status and execution
    status = Column(
        String(50),
        nullable=False,
        default="idle",
        index=True,
        comment="Current team status"
    )

    # Team execution metrics
    total_executions = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of team executions"
    )

    successful_executions = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of successful team executions"
    )

    current_workflow = Column(
        String(255),
        nullable=True,
        comment="Currently executing workflow or task"
    )

    # Team coordination settings
    coordination_config = Column(
        JSONB,
        nullable=True,
        comment="Coordination-specific configuration and rules"
    )

    # Communication and decision-making
    communication_style = Column(
        String(50),
        nullable=True,
        comment="Team communication style (formal, casual, structured)"
    )

    decision_making = Column(
        String(50),
        nullable=True,
        comment="Decision making process (consensus, majority, leader, hybrid)"
    )

    # Team-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    team_metadata = Column(
        JSONB,
        nullable=True,
        comment="Team-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    # === RELATIONSHIPS ===

    # Many-to-many relationship with agents
    agents = relationship(
        "Agent",
        secondary=team_agents,
        back_populates="teams",
        lazy='select'
    )

    # Foreign key relationships
    project = relationship("Project", back_populates="teams")
    protocol = relationship("Protocol", back_populates="teams")
    workflow = relationship("Workflow", back_populates="teams")
    book = relationship("Book", back_populates="teams")

    def __init__(self, **kwargs):
        """Initialize team with validation."""
        # Set defaults
        if 'coordination' not in kwargs:
            kwargs['coordination'] = 'collaborative'
        if 'status' not in kwargs:
            kwargs['status'] = 'idle'
        if 'total_executions' not in kwargs:
            kwargs['total_executions'] = 0
        if 'successful_executions' not in kwargs:
            kwargs['successful_executions'] = 0
        if 'communication_style' not in kwargs:
            kwargs['communication_style'] = 'structured'
        if 'decision_making' not in kwargs:
            kwargs['decision_making'] = 'consensus'

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Team(id='{self.id}', name='{self.name}', coordination='{self.coordination}')>"

    # === VALIDATION METHODS ===

    @validates('id')
    def validate_id(self, key: str, value: str) -> str:
        """Validate team ID format."""
        if not value:
            raise ValueError("Team ID is required")

        # Must be alphanumeric with underscores/hyphens, 2-100 characters
        if not re.match(r'^[a-zA-Z0-9_-]{2,100}$', value):
            raise ValueError(
                "Team ID must be 2-100 characters, containing only "
                "letters, numbers, underscores, and hyphens"
            )

        return value.lower()  # Normalize to lowercase

    @validates('name')
    def validate_name(self, key: str, value: str) -> str:
        """Validate team name."""
        if not value or not value.strip():
            raise ValueError("Team name is required")

        if len(value.strip()) > 255:
            raise ValueError("Team name cannot exceed 255 characters")

        return value.strip()

    @validates('coordination')
    def validate_coordination(self, key: str, value: str) -> str:
        """Validate coordination strategy."""
        valid_strategies = ['hierarchical', 'collaborative', 'parallel']

        if value not in valid_strategies:
            raise ValueError(
                f"Coordination must be one of: {', '.join(valid_strategies)}")

        return value

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate team status."""
        valid_statuses = ['idle', 'active', 'busy',
            'coordinating', 'error', 'disbanded']

        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        return value

    @validates('communication_style')
    def validate_communication_style(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate communication style."""
        if value is None:
            return value

        valid_styles = ['formal', 'casual', 'structured', 'adaptive']

        if value not in valid_styles:
            raise ValueError(
                f"Communication style must be one of: {', '.join(valid_styles)}")

        return value

    @validates('decision_making')
    def validate_decision_making(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate decision making process."""
        if value is None:
            return value

        valid_processes = ['consensus', 'majority', 'leader', 'hybrid', 'weighted']

        if value not in valid_processes:
            raise ValueError(
                f"Decision making must be one of: {', '.join(valid_processes)}")

        return value

    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate team data before creating/updating."""
        validated = data.copy()

        # Required fields
        if 'id' not in validated or not validated['id']:
            raise ValueError("Team ID is required")

        if 'name' not in validated or not validated['name']:
            raise ValueError("Team name is required")

        # Validate hierarchy structure for hierarchical teams
        if validated.get('coordination') == 'hierarchical':
            hierarchy = validated.get('hierarchy', {})

            if not hierarchy.get('leader'):
                raise ValueError(
                    "Hierarchical teams must have a leader specified in hierarchy")

        # Validate coordination config
        if 'coordination_config' in validated and validated['coordination_config']:
            if not isinstance(validated['coordination_config'], dict):
                raise ValueError("Coordination config must be a dictionary")

        return validated

    def validate_instance(self) -> List[str]:
        """Validate team instance and return list of errors."""
        errors = []

        # Validate required fields
        if not getattr(self, 'id', None):
            errors.append("Team ID is required")

        if not getattr(self, 'name', None):
            errors.append("Team name is required")

        # Validate coordination-specific requirements
        coordination = getattr(self, 'coordination', None)
        hierarchy = getattr(self, 'hierarchy', None)
        if coordination == 'hierarchical':
            if not hierarchy or not hierarchy.get('leader'):
                errors.append("Hierarchical teams must have a leader defined")

        # Validate execution statistics
        successful_executions = getattr(self, 'successful_executions', 0)
        total_executions = getattr(self, 'total_executions', 0)
        if successful_executions > total_executions:
            errors.append("Successful executions cannot exceed total executions")

        return errors

    # === TEAM MANAGEMENT METHODS ===

    def add_agent(self, agent_id: str, role: Optional[str] = None) -> None:
        """Add agent to team with optional role."""
        # This would be implemented with database session in real usage
        # For now, just validate the data
        if not agent_id:
            raise ValueError("Agent ID is required")

        # Add role to hierarchy if hierarchical coordination
        coordination = getattr(self, 'coordination', None)
        hierarchy = getattr(self, 'hierarchy', None) or {}

        if coordination == 'hierarchical' and role:
            if not hierarchy:
                hierarchy = {}
                self.hierarchy = hierarchy

            members = hierarchy.get('members', [])
            if agent_id not in members:
                members.append(agent_id)
                hierarchy['members'] = members
                self.hierarchy = hierarchy

            # Set role in hierarchy
            roles = hierarchy.get('roles', {})
            roles[agent_id] = role
            hierarchy['roles'] = roles
            self.hierarchy = hierarchy

    def remove_agent(self, agent_id: str) -> None:
        """Remove agent from team."""
        # Remove from hierarchy if exists
        hierarchy = getattr(self, 'hierarchy', None)
        if hierarchy:
            members = hierarchy.get('members', [])
            if agent_id in members:
                members.remove(agent_id)
                hierarchy['members'] = members
                self.hierarchy = hierarchy

            # Remove role
            roles = hierarchy.get('roles', {})
            if agent_id in roles:
                del roles[agent_id]
                hierarchy['roles'] = roles
                self.hierarchy = hierarchy

    def set_leader(self, agent_id: str) -> None:
        """Set team leader (for hierarchical coordination)."""
        coordination = getattr(self, 'coordination', None)
        if coordination != 'hierarchical':
            raise ValueError("Leaders can only be set for hierarchical coordination")

        hierarchy = getattr(self, 'hierarchy', None)
        if not hierarchy:
            hierarchy = {}
            self.hierarchy = hierarchy

        hierarchy['leader'] = agent_id
        self.hierarchy = hierarchy

        # Ensure leader is in members
        members = hierarchy.get('members', [])
        if agent_id not in members:
            members.append(agent_id)
            hierarchy['members'] = members
            self.hierarchy = hierarchy

    def get_leader(self) -> Optional[str]:
        """Get team leader ID."""
        hierarchy = getattr(self, 'hierarchy', None)
        if hierarchy:
            return hierarchy.get('leader')
        return None

    def get_agent_role(self, agent_id: str) -> Optional[str]:
        """Get agent's role in the team."""
        hierarchy = getattr(self, 'hierarchy', None)
        if hierarchy:
            roles = hierarchy.get('roles', {})
            return roles.get(agent_id)
        return None

    def update_coordination_config(self, key: str, value: Any) -> None:
        """Update coordination-specific configuration."""
        coordination_config = getattr(self, 'coordination_config', None)
        if coordination_config is None:
            coordination_config = {}
            self.coordination_config = coordination_config

        coordination_config[key] = value
        self.coordination_config = coordination_config

    def get_coordination_config(self, key: str, default: Any = None) -> Any:
        """Get coordination configuration value."""
        coordination_config = getattr(self, 'coordination_config', None)
        if coordination_config:
            return coordination_config.get(key, default)
        return default

    # === EXECUTION AND MONITORING ===

    def update_execution_stats(self, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update team execution statistics."""
        self.total_executions += 1

        if success:
            self.successful_executions += 1

        # Update last execution timestamp
        self.last_executed_at = datetime.utcnow()

        # Store execution metadata
        if metadata:
            if self.metadata is None:
                self.metadata = {}

            execution_history = self.metadata.get('execution_history', [])
            execution_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'success': success,
                'metadata': metadata
            })

            # Keep only last 50 execution records
            if len(execution_history) > 50:
                execution_history = execution_history[-50:]

            self.metadata['execution_history'] = execution_history

    def get_success_rate(self) -> Optional[float]:
        """Get team success rate."""
        total_executions = getattr(self, 'total_executions', 0)
        if total_executions > 0:
            successful_executions = getattr(self, 'successful_executions', 0)
            return successful_executions / total_executions
        return None

    def get_team_summary(self) -> Dict[str, Any]:
        """Get team summary information."""
        agents = getattr(self, 'agents', None) or []
        created_at = getattr(self, 'created_at', None)
        updated_at = getattr(self, 'updated_at', None)

        return {
            'id': getattr(self, 'id', None),
            'name': getattr(self, 'name', None),
            'description': getattr(self, 'description', None),
            'coordination': getattr(self, 'coordination', None),
            'status': getattr(self, 'status', None),
            'agent_count': len(agents),
            'leader': self.get_leader(),
            'has_protocol': getattr(self, 'protocol_id', None) is not None,
            'has_workflow': getattr(self, 'workflow_id', None) is not None,
            'has_shared_memory': getattr(self, 'book_id', None) is not None,
            'success_rate': self.get_success_rate(),
            'total_executions': getattr(self, 'total_executions', 0),
            'communication_style': getattr(self, 'communication_style', None),
            'decision_making': getattr(self, 'decision_making', None),
            'created_at': created_at.isoformat() if created_at else None,
            'updated_at': updated_at.isoformat() if updated_at else None
        }

    # === COORDINATION STRATEGY IMPLEMENTATIONS ===

    def get_coordination_strategy(self) -> Dict[str, Any]:
        """Get coordination strategy details."""
        coordination = getattr(self, 'coordination', None)
        base_strategy = {
            'type': coordination,
            'communication_style': getattr(self, 'communication_style', None),
            'decision_making': getattr(self, 'decision_making', None)
        }

        if coordination == 'hierarchical':
            base_strategy['leader'] = self.get_leader()
            base_strategy['hierarchy'] = getattr(self, 'hierarchy', None)
            base_strategy['escalation_rules'] = self.get_coordination_config(
                'escalation_rules', [])
            base_strategy['approval_required'] = self.get_coordination_config(
                'approval_required', True)
        elif coordination == 'collaborative':
            base_strategy['consensus_threshold'] = self.get_coordination_config(
                'consensus_threshold', 0.7)
            base_strategy['discussion_rounds'] = self.get_coordination_config(
                'discussion_rounds', 3)
            base_strategy['conflict_resolution'] = self.get_coordination_config(
                'conflict_resolution', 'vote')
        elif coordination == 'parallel':
            base_strategy['synchronization_points'] = self.get_coordination_config(
                'synchronization_points', [])
            base_strategy['result_aggregation'] = self.get_coordination_config(
                'result_aggregation', 'merge')
            base_strategy['failure_handling'] = self.get_coordination_config(
                'failure_handling', 'continue')

        return base_strategy

    @classmethod
    def create_hierarchical_team(
        cls,
        team_id: str,
        name: str,
        leader_id: str,
        members: List[str],
        **kwargs
    ) -> "Team":
        """Create hierarchical team with leader and members."""
        hierarchy = {
            'leader': leader_id,
            'members': members,
            'roles': {leader_id: 'leader'},
            'decision_flow': 'leader_approval_required',
            'escalation_rules': ['complex_decisions_to_leader', 'conflicts_to_leader']
        }

        # Set member roles if provided
        for i, member_id in enumerate(members):
            if member_id != leader_id:
                hierarchy['roles'][member_id] = f'member_{i+1}'

        return cls(
            id=team_id,
            name=name,
            coordination='hierarchical',
            hierarchy=hierarchy,
            decision_making='leader',
            **kwargs
        )

    @classmethod
    def create_collaborative_team(
        cls,
        team_id: str,
        name: str,
        members: List[str],
        **kwargs
    ) -> "Team":
        """Create collaborative team with equal participation."""
        coordination_config = {
            'consensus_threshold': 0.7,
            'discussion_rounds': 3,
            'conflict_resolution': 'vote',
            'equal_participation': True
        }

        return cls(
            id=team_id,
            name=name,
            coordination='collaborative',
            coordination_config=coordination_config,
            decision_making='consensus',
            **kwargs
        )

    @classmethod
    def create_parallel_team(
        cls,
        team_id: str,
        name: str,
        members: List[str],
        **kwargs
    ) -> "Team":
        """Create parallel team for independent work."""
        coordination_config = {
            'synchronization_points': ['start', 'end'],
            'result_aggregation': 'merge',
            'failure_handling': 'continue',
            'independent_execution': True
        }

        return cls(
            id=team_id,
            name=name,
            coordination='parallel',
            coordination_config=coordination_config,
            decision_making='independent',
            **kwargs
        )


# Database indexes for performance
Index('idx_team_coordination_status', Team.coordination, Team.status)
Index('idx_team_project_status', Team.project_id, Team.status)
Index('idx_team_executions', Team.total_executions.desc())

# Database constraints
CheckConstraint(
    Team.coordination.in_(['hierarchical', 'collaborative', 'parallel']),
    name='ck_team_coordination_valid'
)

CheckConstraint(
    Team.status.in_(['idle', 'active', 'busy', 'coordinating', 'error', 'disbanded']),
    name='ck_team_status_valid'
)

CheckConstraint(
    Team.successful_executions <= Team.total_executions,
    name='ck_team_executions_consistent'
)
