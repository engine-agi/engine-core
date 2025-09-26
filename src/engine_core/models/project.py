"""
Project model for Engine Framework.

A project is the top-level container for all Engine Framework entities.
It serves as the root for organizing agents, teams, workflows, protocols,
tools, and books within a cohesive development context.

Based on Engine Framework data model specification.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import ARRAY, JSON, Column, String, Text

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .agent import Agent
    from .book import Book
    from .protocol import Protocol
    from .team import Team
    from .tool import Tool
    from .workflow import Workflow


class Project(BaseModel):
    """
    Project entity - top-level container for Engine Framework entities.

    A project represents a cohesive development initiative that orchestrates
    multiple AI agents, teams, workflows, and tools to accomplish specific goals.

    Key characteristics:
    - String-based ID (user-friendly identifiers like "web_app_dev")
    - Central configuration hub for all related entities
    - Template support for rapid project setup
    - Rich metadata and requirements tracking
    - Hierarchical organization support
    """

    __tablename__ = "projects"

    # Basic project information
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable project name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Detailed project description and objectives"
    )

    # Project classification and context
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Project category (e.g., 'web_development', 'data_analysis', 'ai_research')"
    )

    complexity = Column(
        String(50),
        nullable=True,
        comment="Project complexity level ('beginner', 'intermediate', 'advanced', 'expert')"
    )

    priority = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Project priority level ('low', 'medium', 'high', 'critical')"
    )

    # Project requirements and specifications
    requirements = Column(
        JSON,
        nullable=True,
        comment="Project requirements, objectives, and success criteria"
    )

    tech_stack = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Technology stack used in the project"
    )

    # Project timeline and status
    status = Column(
        String(50),
        nullable=False,
        default="planning",
        index=True,
        comment="Current project status"
    )

    start_date = Column(
        String(50),
        nullable=True,
        comment="Project start date (flexible format)"
    )

    end_date = Column(
        String(50),
        nullable=True,
        comment="Project end date (flexible format)"
    )

    estimated_duration = Column(
        String(100),
        nullable=True,
        comment="Estimated project duration (e.g., '8 weeks', '3 months')"
    )

    # Template and initialization
    template = Column(
        String(100),
        nullable=True,
        comment="Template used to initialize the project"
    )

    template_version = Column(
        String(50),
        nullable=True,
        comment="Version of the template used"
    )

    # Project organization
    tags = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Tags for project organization and search"
    )

    owner = Column(
        String(255),
        nullable=True,
        comment="Project owner or responsible person"
    )

    # Relationships to other entities (defined as back references)
    # These will be populated by foreign keys in other models

    # Project-specific metadata (separate from base metadata to avoid conflicts)
    project_metadata = Column(
        JSON,
        nullable=True,
        comment="Project-specific metadata and tracking information"
    )

    # Override inherited metadata to avoid SQLAlchemy conflicts
    metadata = None

    def __init__(self, **kwargs):
        """Initialize project with validation."""
        # Set defaults
        if 'status' not in kwargs:
            kwargs['status'] = 'planning'
        if 'complexity' not in kwargs:
            kwargs['complexity'] = 'intermediate'
        if 'priority' not in kwargs:
            kwargs['priority'] = 'medium'

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Project(id='{self.id}', name='{self.name}', status='{self.status}')>"

    # def validate_id(self, key: str, value: str) -> str:
    #     """Validate project ID format."""
    #     if not value:
    #         raise ValueError("Project ID is required")

    #     # Must be alphanumeric with underscores/hyphens, 3-100 characters
    #     if not re.match(r'^[a-zA-Z0-9_-]{3,100}$', value):
    #         raise ValueError(
    #             "Project ID must be 3-100 characters, containing only "
    #             "letters, numbers, underscores, and hyphens"
    #         )

    #     return value.lower()  # Normalize to lowercase

    def validate_name(self, key: str, value: str) -> str:
        """Validate project name."""
        if not value or not value.strip():
            raise ValueError("Project name is required")

        if len(value.strip()) > 255:
            raise ValueError("Project name cannot exceed 255 characters")

        return value.strip()

    def validate_status(self, key: str, value: str) -> str:
        """Validate project status."""
        valid_statuses = [
            'planning', 'active', 'on_hold', 'completed',
            'cancelled', 'archived'
        ]

        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        return value

    def validate_complexity(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate project complexity level."""
        if value is None:
            return value

        valid_complexity = ['beginner', 'intermediate', 'advanced', 'expert']

        if value not in valid_complexity:
            raise ValueError(
                f"Complexity must be one of: {
                    ', '.join(valid_complexity)}")

        return value

    def validate_priority(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate project priority level."""
        if value is None:
            return value

        valid_priorities = ['low', 'medium', 'high', 'critical']

        if value not in valid_priorities:
            raise ValueError(f"Priority must be one of: {', '.join(valid_priorities)}")

        return value

    # @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate project data before creating/updating."""
        validated = data.copy()

        # Required fields
        if 'id' not in validated or not validated['id']:
            raise ValueError("Project ID is required")

        if 'name' not in validated or not validated['name']:
            raise ValueError("Project name is required")

        # Validate tech stack
        if 'tech_stack' in validated and validated['tech_stack']:
            if not isinstance(validated['tech_stack'], list):
                raise ValueError("Tech stack must be a list of strings")

            # Validate each tech stack item
            for tech in validated['tech_stack']:
                if not isinstance(tech, str) or not tech.strip():
                    raise ValueError("All tech stack items must be non-empty strings")

        # Validate requirements structure
        if 'requirements' in validated and validated['requirements']:
            if not isinstance(validated['requirements'], dict):
                raise ValueError("Requirements must be a dictionary")

        # Validate tags
        if 'tags' in validated and validated['tags']:
            if not isinstance(validated['tags'], list):
                raise ValueError("Tags must be a list of strings")

            for tag in validated['tags']:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError("All tags must be non-empty strings")

        return validated

    def validate_instance(self) -> List[str]:
        """Validate project instance and return list of errors."""
        errors = []

        # Validate required fields
        if not self.id:
            errors.append("Project ID is required")

        if not self.name:
            errors.append("Project name is required")

        # Validate tech stack consistency
        if self.tech_stack and self.requirements:
            req_tech = self.requirements.get('tech_stack', [])
            if req_tech and not all(tech in self.tech_stack for tech in req_tech):
                errors.append(
                    "Requirements tech stack must be subset of project tech stack")

        return errors

    # Utility methods for project management

    def add_requirement(self, key: str, value: Any) -> None:
        """Add or update a project requirement."""
        if self.requirements is None:
            self.requirements = {}
        self.requirements[key] = value

    def remove_requirement(self, key: str) -> None:
        """Remove a project requirement."""
        if self.requirements and key in self.requirements:
            del self.requirements[key]

    def get_requirement(self, key: str, default: Any = None) -> Any:
        """Get a specific requirement value."""
        if self.requirements:
            return self.requirements.get(key, default)
        return default

    def add_tech_stack_item(self, tech: str) -> None:
        """Add a technology to the tech stack."""
        if self.tech_stack is None:
            self.tech_stack = []

        tech = tech.strip().lower()
        if tech and tech not in self.tech_stack:
            self.tech_stack.append(tech)

    def remove_tech_stack_item(self, tech: str) -> None:
        """Remove a technology from the tech stack."""
        if self.tech_stack:
            tech = tech.strip().lower()
            if tech in self.tech_stack:
                self.tech_stack.remove(tech)

    def add_tag(self, tag: str) -> None:
        """Add a tag to the project."""
        if self.tags is None:
            self.tags = []

        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the project."""
        if self.tags:
            tag = tag.strip().lower()
            if tag in self.tags:
                self.tags.remove(tag)

    def update_status(self, new_status: str,
                      metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update project status with optional metadata."""
        self.status = new_status

        if metadata:
            if self.project_metadata is None:
                self.project_metadata = {}

            status_history = self.project_metadata.get('status_history', [])
            status_history.append({
                'from_status': getattr(self, '_sa_instance_state').committed_state.get('status'),
                'to_status': new_status,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata
            })

            self.project_metadata['status_history'] = status_history

    def get_summary(self) -> Dict[str, Any]:
        """Get project summary information."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'complexity': self.complexity,
            'priority': self.priority,
            'tech_stack_count': len(self.tech_stack) if self.tech_stack else 0,
            'requirements_count': len(self.requirements) if self.requirements else 0,
            'tags_count': len(self.tags) if self.tags else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    # @classmethod
    def create_from_template(
            cls,
            project_id: str,
            template_name: str,
            **overrides) -> "Project":
        """Create project from predefined template."""
        templates = {
            'web_development_basic': {
                'name': 'Basic Web Development Project',
                'category': 'web_development',
                'complexity': 'beginner',
                'tech_stack': [
                    'html',
                    'css',
                    'javascript'],
                'requirements': {
                    'features': [
                        'responsive_design',
                        'basic_functionality'],
                    'timeline': '4 weeks'}},
            'fullstack_advanced': {
                'name': 'Full-Stack Development Project',
                        'category': 'web_development',
                        'complexity': 'advanced',
                        'tech_stack': [
                            'python',
                            'fastapi',
                            'react',
                            'typescript',
                            'postgresql'],
                'requirements': {
                            'features': [
                                'authentication',
                                'api_design',
                                'database_integration'],
                            'timeline': '8-12 weeks',
                            'scalability': 'high'}},
            'ai_research': {
                'name': 'AI Research Project',
                'category': 'ai_research',
                'complexity': 'expert',
                'tech_stack': [
                    'python',
                    'pytorch',
                    'transformers',
                    'jupyter'],
                'requirements': {
                    'deliverables': [
                        'research_paper',
                        'model_implementation',
                        'evaluation_metrics'],
                    'timeline': '12-16 weeks'}}}

        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")

        template_data = templates[template_name].copy()
        template_data.update(overrides)
        template_data['id'] = project_id
        template_data['template'] = template_name
        template_data['template_version'] = '1.0'

        return cls(**template_data)


# Database indexes for performance
Index('idx_project_status_priority', Project.status, Project.priority)
Index('idx_project_category_complexity', Project.category, Project.complexity)
Index('idx_project_created_at', Project.created_at.desc())

# Database constraints
CheckConstraint(
    Project.status.in_(['planning', 'active', 'on_hold',
                       'completed', 'cancelled', 'archived']),
    name='ck_project_status_valid'
)

CheckConstraint(
    Project.complexity.in_(['beginner', 'intermediate', 'advanced', 'expert']),
    name='ck_project_complexity_valid'
)

CheckConstraint(
    Project.priority.in_(['low', 'medium', 'high', 'critical']),
    name='ck_project_priority_valid'
)
