"""
Book Service Layer - Memory Management and Content Organization.

The Book Service provides comprehensive business logic for hierarchical memory 
management, content organization, search operations, and knowledge management
within the Engine Framework ecosystem.

Key Features:
- Complete book lifecycle management (create, read, update, delete)
- Hierarchical content organization (books, chapters, pages, sections)
- Advanced semantic search with indexing
- Content versioning and history tracking
- Access control and permission management
- Content analytics and metrics
- Cross-reference management
- Template-based content creation
- Bulk operations and migrations
- Real-time collaboration features

Architecture:
- Service layer with business logic separation
- Repository pattern for data persistence
- Search engine integration for semantic queries
- Version control for content changes
- Permission system for access control
- Analytics engine for usage tracking
- Template system for rapid content creation
- Integration with Agent/Team/Workflow services

Dependencies:
- BookBuilder from core.book.book_builder
- Database repositories for persistence
- Search engines for content indexing
- Authentication services for permissions
- Event system for real-time updates
"""

from typing import Dict, Any, List, Optional, Set, Tuple, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
import json
import logging
from pathlib import Path

# Import core book components
from ..core.book.book_builder import (
    Book, BookChapter, BookPage, ContentSection,
    BookBuilder, SearchQuery, SearchResult, ContentMetadata,
    ContentType, AccessLevel, ContentStatus, SearchScope,
    ContentReference, SemanticSearchEngine
)

logger = logging.getLogger(__name__)


class BookOperation(Enum):
    """Types of operations performed on books."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEARCH = "search"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    COLLABORATE = "collaborate"


class CollaborationMode(Enum):
    """Collaboration modes for books."""
    READ_ONLY = "read_only"
    COMMENT_ONLY = "comment_only"
    EDIT_SECTIONS = "edit_sections"
    EDIT_PAGES = "edit_pages"
    EDIT_CHAPTERS = "edit_chapters"
    FULL_EDIT = "full_edit"
    ADMIN = "admin"


@dataclass
class BookTemplate:
    """Template for creating books."""
    template_id: str
    name: str
    description: str
    category: str
    structure: Dict[str, Any]  # Chapter/page structure
    default_content: Dict[str, str]  # Default content for sections
    metadata_template: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BookMetrics:
    """Analytics metrics for books."""
    book_id: str
    view_count: int = 0
    search_count: int = 0
    edit_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collaboration_sessions: int = 0
    unique_visitors: Set[str] = field(default_factory=set)
    popular_pages: List[Tuple[str, int]] = field(default_factory=list)  # (page_id, views)
    search_terms: Dict[str, int] = field(default_factory=dict)  # term -> count
    last_accessed: Optional[datetime] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class CollaborationSession:
    """Active collaboration session."""
    session_id: str
    book_id: str
    participants: List[str]
    mode: CollaborationMode
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    active_pages: Dict[str, str] = field(default_factory=dict)  # page_id -> user_id
    pending_changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ContentVersion:
    """Version information for content."""
    version_id: str
    content_id: str
    content_type: str  # "book", "chapter", "page", "section"
    version_number: int
    content_snapshot: Dict[str, Any]
    changes: List[str]
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    commit_message: Optional[str] = None


@dataclass
class BookExportOptions:
    """Options for exporting books."""
    format: str  # "json", "markdown", "html", "pdf", "docx"
    include_metadata: bool = True
    include_comments: bool = False
    include_version_history: bool = False
    max_depth: int = -1  # -1 for all levels
    selected_chapters: List[str] = field(default_factory=list)
    custom_styling: Dict[str, Any] = field(default_factory=dict)


class MockBookRepository:
    """Mock repository for book persistence."""
    
    def __init__(self):
        """Initialize mock repository."""
        self.books: Dict[str, Book] = {}
        self.templates: Dict[str, BookTemplate] = {}
        self.metrics: Dict[str, BookMetrics] = {}
        self.versions: Dict[str, List[ContentVersion]] = {}
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}
        
        # Initialize with default templates
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default book templates."""
        
        # Technical Documentation Template
        tech_doc_template = BookTemplate(
            template_id="technical_documentation",
            name="Technical Documentation",
            description="Template for technical documentation and guides",
            category="documentation",
            structure={
                "chapters": [
                    {
                        "title": "Introduction",
                        "description": "Project overview and getting started",
                        "pages": [
                            {"title": "Overview", "sections": ["What is this?", "Key Features", "Requirements"]},
                            {"title": "Quick Start", "sections": ["Installation", "Basic Usage", "Examples"]}
                        ]
                    },
                    {
                        "title": "Architecture", 
                        "description": "System architecture and design",
                        "pages": [
                            {"title": "System Design", "sections": ["Overview", "Components", "Data Flow"]},
                            {"title": "API Reference", "sections": ["Endpoints", "Authentication", "Examples"]}
                        ]
                    },
                    {
                        "title": "Developer Guide",
                        "description": "Development guidelines and best practices",
                        "pages": [
                            {"title": "Development Setup", "sections": ["Environment", "Dependencies", "Configuration"]},
                            {"title": "Contributing", "sections": ["Guidelines", "Pull Requests", "Testing"]}
                        ]
                    }
                ]
            },
            default_content={
                "What is this?": "Brief description of the project and its purpose.",
                "Key Features": "- Feature 1\n- Feature 2\n- Feature 3",
                "Requirements": "System requirements and prerequisites.",
                "Installation": "Step-by-step installation instructions.",
                "Basic Usage": "Basic usage examples and common patterns."
            },
            metadata_template={
                "tags": ["documentation", "technical", "guide"],
                "categories": ["development"],
                "access_level": "internal",
                "status": "draft"
            },
            is_public=True
        )
        
        # Project Knowledge Base Template
        knowledge_base_template = BookTemplate(
            template_id="knowledge_base",
            name="Knowledge Base",
            description="Template for project knowledge bases and wikis",
            category="knowledge",
            structure={
                "chapters": [
                    {
                        "title": "Getting Started",
                        "description": "Essential information for new team members",
                        "pages": [
                            {"title": "Team Overview", "sections": ["Mission", "Team Structure", "Contacts"]},
                            {"title": "Onboarding", "sections": ["First Day", "Tools Setup", "Resources"]}
                        ]
                    },
                    {
                        "title": "Processes",
                        "description": "Standard operating procedures and workflows",
                        "pages": [
                            {"title": "Development Process", "sections": ["Workflow", "Code Review", "Deployment"]},
                            {"title": "Communication", "sections": ["Meetings", "Channels", "Reporting"]}
                        ]
                    },
                    {
                        "title": "Resources",
                        "description": "Useful resources and references",
                        "pages": [
                            {"title": "Tools and Systems", "sections": ["Development Tools", "Infrastructure", "Access"]},
                            {"title": "External Resources", "sections": ["Documentation", "Learning", "Support"]}
                        ]
                    }
                ]
            },
            default_content={
                "Mission": "Our team mission and objectives.",
                "Team Structure": "Team roles and responsibilities.",
                "Workflow": "Standard development workflow and procedures.",
                "Code Review": "Code review guidelines and best practices.",
                "Development Tools": "List of tools and how to access them."
            },
            metadata_template={
                "tags": ["knowledge", "team", "processes"],
                "categories": ["internal"],
                "access_level": "internal",
                "status": "published"
            },
            is_public=False
        )
        
        # Research Notes Template
        research_template = BookTemplate(
            template_id="research_notes",
            name="Research Notes",
            description="Template for research documentation and analysis",
            category="research",
            structure={
                "chapters": [
                    {
                        "title": "Research Overview",
                        "description": "High-level research goals and methodology",
                        "pages": [
                            {"title": "Objectives", "sections": ["Goals", "Hypothesis", "Success Metrics"]},
                            {"title": "Methodology", "sections": ["Approach", "Tools", "Timeline"]}
                        ]
                    },
                    {
                        "title": "Findings",
                        "description": "Research results and observations",
                        "pages": [
                            {"title": "Data Collection", "sections": ["Sources", "Methods", "Quality"]},
                            {"title": "Analysis", "sections": ["Results", "Insights", "Patterns"]}
                        ]
                    },
                    {
                        "title": "Conclusions",
                        "description": "Summary and recommendations",
                        "pages": [
                            {"title": "Summary", "sections": ["Key Findings", "Implications", "Limitations"]},
                            {"title": "Next Steps", "sections": ["Recommendations", "Future Research", "Action Items"]}
                        ]
                    }
                ]
            },
            default_content={
                "Goals": "Primary research objectives and questions.",
                "Hypothesis": "Initial hypothesis and assumptions.",
                "Approach": "Research methodology and approach.",
                "Results": "Key findings and results from the research.",
                "Key Findings": "Summary of the most important discoveries."
            },
            metadata_template={
                "tags": ["research", "analysis", "findings"],
                "categories": ["research"],
                "access_level": "restricted",
                "status": "draft"
            },
            is_public=False
        )
        
        # Store templates
        self.templates[tech_doc_template.template_id] = tech_doc_template
        self.templates[knowledge_base_template.template_id] = knowledge_base_template
        self.templates[research_template.template_id] = research_template
    
    async def save_book(self, book: Book) -> bool:
        """Save book to repository."""
        try:
            self.books[book.book_id] = book
            
            # Initialize metrics if not exists
            if book.book_id not in self.metrics:
                self.metrics[book.book_id] = BookMetrics(book_id=book.book_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save book {book.book_id}: {str(e)}")
            return False
    
    async def get_book(self, book_id: str) -> Optional[Book]:
        """Get book by ID."""
        return self.books.get(book_id)
    
    async def delete_book(self, book_id: str) -> bool:
        """Delete book from repository."""
        try:
            if book_id in self.books:
                del self.books[book_id]
                if book_id in self.metrics:
                    del self.metrics[book_id]
                if book_id in self.versions:
                    del self.versions[book_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete book {book_id}: {str(e)}")
            return False
    
    async def list_books(
        self, 
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        tags: List[str] = None,
        limit: int = 50
    ) -> List[Book]:
        """List books with optional filters."""
        books = list(self.books.values())
        
        # Apply filters
        if user_id:
            books = [b for b in books if b.author == user_id]
        
        if project_id:
            books = [b for b in books if b.project_id == project_id]
        
        if tags:
            books = [b for b in books if any(tag in b.tags for tag in tags)]
        
        # Sort by updated date and limit
        books = sorted(books, key=lambda b: b.metadata.updated_at, reverse=True)
        return books[:limit]
    
    async def save_template(self, template: BookTemplate) -> bool:
        """Save book template."""
        try:
            self.templates[template.template_id] = template
            return True
        except Exception as e:
            logger.error(f"Failed to save template {template.template_id}: {str(e)}")
            return False
    
    async def get_template(self, template_id: str) -> Optional[BookTemplate]:
        """Get book template by ID."""
        return self.templates.get(template_id)
    
    async def list_templates(self, category: Optional[str] = None) -> List[BookTemplate]:
        """List book templates."""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return sorted(templates, key=lambda t: t.name)
    
    async def save_metrics(self, metrics: BookMetrics) -> bool:
        """Save book metrics."""
        try:
            self.metrics[metrics.book_id] = metrics
            return True
        except Exception as e:
            logger.error(f"Failed to save metrics for {metrics.book_id}: {str(e)}")
            return False
    
    async def get_metrics(self, book_id: str) -> Optional[BookMetrics]:
        """Get book metrics."""
        return self.metrics.get(book_id)
    
    async def save_version(self, version: ContentVersion) -> bool:
        """Save content version."""
        try:
            if version.content_id not in self.versions:
                self.versions[version.content_id] = []
            
            self.versions[version.content_id].append(version)
            return True
        except Exception as e:
            logger.error(f"Failed to save version for {version.content_id}: {str(e)}")
            return False
    
    async def get_versions(self, content_id: str) -> List[ContentVersion]:
        """Get content versions."""
        return self.versions.get(content_id, [])


class BookService:
    """Service for book management and operations."""
    
    def __init__(self, repository: MockBookRepository = None):
        """Initialize book service."""
        self.repository = repository or MockBookRepository()
        self.search_engine = SemanticSearchEngine(enable_embeddings=True)
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}
        
        # Performance metrics
        self.operation_counts = {op.value: 0 for op in BookOperation}
        self.response_times: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
    
    # === BOOK LIFECYCLE MANAGEMENT ===
    
    async def create_book(
        self,
        book_id: str,
        title: str,
        description: str = "",
        author: Optional[str] = None,
        project_id: Optional[str] = None,
        template_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Book]:
        """Create a new book."""
        start_time = datetime.utcnow()
        
        try:
            # Check if book already exists
            existing_book = await self.repository.get_book(book_id)
            if existing_book:
                raise ValueError(f"Book with ID {book_id} already exists")
            
            # Create book from template or scratch
            if template_id:
                book = await self._create_book_from_template(
                    book_id, title, description, author, project_id, template_id, **kwargs
                )
            else:
                # Create book using builder
                builder = BookBuilder()\
                    .with_id(book_id)\
                    .with_title(title)\
                    .with_description(description)
                
                if author:
                    builder = builder.with_author(author)
                if project_id:
                    builder = builder.with_project(project_id)
                
                # Apply additional options
                for key, value in kwargs.items():
                    if hasattr(builder, f'with_{key}'):
                        builder = getattr(builder, f'with_{key}')(value)
                
                book = builder.build()
            
            # Save to repository
            success = await self.repository.save_book(book)
            if not success:
                raise RuntimeError("Failed to save book to repository")
            
            # Index content for search
            await self._index_book_content(book)
            
            # Update metrics
            await self._record_operation(BookOperation.CREATE, book_id, start_time)
            
            logger.info(f"Created book: {book_id}")
            return book
            
        except Exception as e:
            logger.error(f"Failed to create book {book_id}: {str(e)}")
            await self._record_error("create_book", str(e))
            return None
    
    async def _create_book_from_template(
        self,
        book_id: str,
        title: str,
        description: str,
        author: Optional[str],
        project_id: Optional[str],
        template_id: str,
        **kwargs
    ) -> Book:
        """Create book from template."""
        template = await self.repository.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Create base book
        builder = BookBuilder()\
            .with_id(book_id)\
            .with_title(title)\
            .with_description(description or template.description)
        
        if author:
            builder = builder.with_author(author)
        if project_id:
            builder = builder.with_project(project_id)
        
        # Apply template metadata
        if template.metadata_template:
            meta = template.metadata_template
            if 'tags' in meta:
                builder = builder.add_tags(meta['tags'])
            if 'categories' in meta:
                builder = builder.add_categories(meta['categories'])
            if 'access_level' in meta:
                builder = builder.with_access_level(AccessLevel(meta['access_level']))
            if 'status' in meta:
                builder = builder.with_status(ContentStatus(meta['status']))
        
        book = builder.build()
        
        # Create chapters and pages from template structure
        if 'chapters' in template.structure:
            for chapter_data in template.structure['chapters']:
                chapter = book.add_chapter(
                    chapter_data['title'],
                    chapter_data.get('description', '')
                )
                
                # Add pages
                if 'pages' in chapter_data:
                    for page_data in chapter_data['pages']:
                        page = chapter.add_page(
                            page_data['title'],
                            page_data.get('description', '')
                        )
                        
                        # Add sections with default content
                        if 'sections' in page_data:
                            for section_title in page_data['sections']:
                                default_content = template.default_content.get(section_title, "")
                                page.add_section(section_title, default_content)
        
        return book
    
    async def get_book(self, book_id: str, user_id: Optional[str] = None) -> Optional[Book]:
        """Get book by ID."""
        start_time = datetime.utcnow()
        
        try:
            book = await self.repository.get_book(book_id)
            
            if book:
                # Update view metrics
                await self._update_view_metrics(book_id, user_id)
                
                # Record access
                await self._record_operation(BookOperation.READ, book_id, start_time)
                
                logger.debug(f"Retrieved book: {book_id}")
            
            return book
            
        except Exception as e:
            logger.error(f"Failed to get book {book_id}: {str(e)}")
            await self._record_error("get_book", str(e))
            return None
    
    async def update_book(
        self,
        book_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """Update book properties."""
        start_time = datetime.utcnow()
        
        try:
            book = await self.repository.get_book(book_id)
            if not book:
                raise ValueError(f"Book {book_id} not found")
            
            # Create version snapshot before update
            if book.enable_versioning:
                await self._create_version_snapshot(book, user_id, "Book update")
            
            # Apply updates
            updated = False
            
            if 'title' in updates:
                book.title = updates['title']
                updated = True
            
            if 'description' in updates:
                book.description = updates['description']
                updated = True
            
            if 'tags' in updates:
                book.tags = set(updates['tags'])
                book.metadata.tags = list(book.tags)
                updated = True
            
            if 'categories' in updates:
                book.categories = set(updates['categories'])
                book.metadata.categories = list(book.categories)
                updated = True
            
            if 'is_public' in updates:
                book.is_public = updates['is_public']
                updated = True
            
            if 'allow_comments' in updates:
                book.allow_comments = updates['allow_comments']
                updated = True
            
            if updated:
                book.metadata.updated_at = datetime.utcnow()
                book.metadata.updated_by = user_id
                book.metadata.version += 1
                
                # Save changes
                success = await self.repository.save_book(book)
                if success:
                    # Re-index content
                    await self._index_book_content(book)
                    
                    # Update metrics
                    await self._record_operation(BookOperation.UPDATE, book_id, start_time)
                    
                    logger.info(f"Updated book: {book_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update book {book_id}: {str(e)}")
            await self._record_error("update_book", str(e))
            return False
    
    async def delete_book(self, book_id: str, user_id: Optional[str] = None) -> bool:
        """Delete book."""
        start_time = datetime.utcnow()
        
        try:
            book = await self.repository.get_book(book_id)
            if not book:
                return False
            
            # Create final version snapshot
            if book.enable_versioning:
                await self._create_version_snapshot(book, user_id, "Book deleted")
            
            # Delete from repository
            success = await self.repository.delete_book(book_id)
            
            if success:
                # Clean up collaboration sessions
                sessions_to_remove = [
                    sid for sid, session in self.collaboration_sessions.items()
                    if session.book_id == book_id
                ]
                for session_id in sessions_to_remove:
                    del self.collaboration_sessions[session_id]
                
                # Update metrics
                await self._record_operation(BookOperation.DELETE, book_id, start_time)
                
                logger.info(f"Deleted book: {book_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete book {book_id}: {str(e)}")
            await self._record_error("delete_book", str(e))
            return False
    
    async def list_books(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        tags: List[str] = None,
        categories: List[str] = None,
        access_level: Optional[AccessLevel] = None,
        status: Optional[ContentStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Book]:
        """List books with filters."""
        try:
            books = await self.repository.list_books(user_id, project_id, tags, limit + offset)
            
            # Apply additional filters
            if categories:
                books = [b for b in books if any(cat in b.categories for cat in categories)]
            
            if access_level:
                books = [b for b in books if b.metadata.access_level == access_level]
            
            if status:
                books = [b for b in books if b.metadata.status == status]
            
            # Apply pagination
            return books[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list books: {str(e)}")
            await self._record_error("list_books", str(e))
            return []
    
    # === CONTENT MANAGEMENT ===
    
    async def add_chapter(
        self,
        book_id: str,
        title: str,
        description: str = "",
        position: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Add chapter to book."""
        try:
            book = await self.repository.get_book(book_id)
            if not book:
                raise ValueError(f"Book {book_id} not found")
            
            # Create version snapshot
            if book.enable_versioning:
                await self._create_version_snapshot(book, user_id, f"Added chapter: {title}")
            
            chapter = book.add_chapter(title, description)
            
            # Reorder if position specified
            if position is not None and position < len(book.chapters) - 1:
                chapter_ids = [c.chapter_id for c in book.chapters]
                chapter_ids.remove(chapter.chapter_id)
                chapter_ids.insert(position, chapter.chapter_id)
                book.reorder_chapters(chapter_ids)
            
            # Save changes
            success = await self.repository.save_book(book)
            if success:
                await self._index_book_content(book)
                logger.info(f"Added chapter {chapter.chapter_id} to book {book_id}")
                return chapter.chapter_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to add chapter to book {book_id}: {str(e)}")
            return None
    
    async def add_page(
        self,
        book_id: str,
        chapter_id: str,
        title: str,
        description: str = "",
        position: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Add page to chapter."""
        try:
            book = await self.repository.get_book(book_id)
            if not book:
                raise ValueError(f"Book {book_id} not found")
            
            chapter = book.get_chapter(chapter_id)
            if not chapter:
                raise ValueError(f"Chapter {chapter_id} not found")
            
            # Create version snapshot
            if book.enable_versioning:
                await self._create_version_snapshot(book, user_id, f"Added page: {title}")
            
            page = chapter.add_page(title, description)
            
            # Reorder if position specified
            if position is not None and position < len(chapter.pages) - 1:
                page_ids = [p.page_id for p in chapter.pages]
                page_ids.remove(page.page_id)
                page_ids.insert(position, page.page_id)
                chapter.reorder_pages(page_ids)
            
            # Save changes
            success = await self.repository.save_book(book)
            if success:
                await self._index_book_content(book)
                logger.info(f"Added page {page.page_id} to chapter {chapter_id}")
                return page.page_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to add page to chapter {chapter_id}: {str(e)}")
            return None
    
    async def add_section(
        self,
        book_id: str,
        page_id: str,
        title: str,
        content: str = "",
        content_type: ContentType = ContentType.TEXT,
        position: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """Add section to page."""
        try:
            book = await self.repository.get_book(book_id)
            if not book:
                raise ValueError(f"Book {book_id} not found")
            
            page = book.get_page(page_id)
            if not page:
                raise ValueError(f"Page {page_id} not found")
            
            # Create version snapshot
            if book.enable_versioning:
                await self._create_version_snapshot(book, user_id, f"Added section: {title}")
            
            section = page.add_section(title, content, content_type)
            section.metadata.created_by = user_id
            section.metadata.updated_by = user_id
            
            # Reorder if position specified
            if position is not None and position < len(page.sections) - 1:
                section_ids = [s.section_id for s in page.sections]
                section_ids.remove(section.section_id)
                section_ids.insert(position, section.section_id)
                page.reorder_sections(section_ids)
            
            # Save changes
            success = await self.repository.save_book(book)
            if success:
                await self._index_book_content(book)
                logger.info(f"Added section {section.section_id} to page {page_id}")
                return section.section_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to add section to page {page_id}: {str(e)}")
            return None
    
    async def update_content(
        self,
        book_id: str,
        content_id: str,
        content_type: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """Update content (chapter, page, or section)."""
        try:
            book = await self.repository.get_book(book_id)
            if not book:
                raise ValueError(f"Book {book_id} not found")
            
            # Create version snapshot
            if book.enable_versioning:
                await self._create_version_snapshot(
                    book, user_id, 
                    f"Updated {content_type}: {content_id}"
                )
            
            updated = False
            
            if content_type == "chapter":
                chapter = book.get_chapter(content_id)
                if chapter:
                    if 'title' in updates:
                        chapter.title = updates['title']
                        updated = True
                    if 'description' in updates:
                        chapter.description = updates['description']
                        updated = True
            
            elif content_type == "page":
                page = book.get_page(content_id)
                if page:
                    if 'title' in updates:
                        page.title = updates['title']
                        updated = True
                    if 'description' in updates:
                        page.description = updates['description']
                        updated = True
            
            elif content_type == "section":
                section = book.get_section(content_id)
                if section:
                    if 'title' in updates:
                        section.title = updates['title']
                        updated = True
                    if 'content' in updates:
                        section.update_content(updates['content'], user_id)
                        updated = True
            
            if updated:
                # Save changes
                success = await self.repository.save_book(book)
                if success:
                    await self._index_book_content(book)
                    logger.info(f"Updated {content_type} {content_id} in book {book_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update {content_type} {content_id}: {str(e)}")
            return False
    
    # === SEARCH OPERATIONS ===
    
    async def search_books(self, query: SearchQuery) -> List[SearchResult]:
        """Search across all books."""
        start_time = datetime.utcnow()
        
        try:
            all_results = []
            
            if query.scope == SearchScope.GLOBAL:
                # Search across all books
                books = await self.repository.list_books(limit=1000)  # Large limit for search
                
                for book in books:
                    book_results = await self._search_book_content(book, query)
                    all_results.extend(book_results)
            
            else:
                # Search specific book
                if query.scope_id:
                    book = await self.repository.get_book(query.scope_id)
                    if book:
                        all_results = await self._search_book_content(book, query)
            
            # Sort results by relevance
            all_results = sorted(all_results, key=lambda r: r.relevance_score, reverse=True)
            
            # Update search metrics
            await self._update_search_metrics(query.query_text, len(all_results))
            await self._record_operation(BookOperation.SEARCH, query.scope_id or "global", start_time)
            
            return all_results[:query.max_results]
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            await self._record_error("search_books", str(e))
            return []
    
    async def _search_book_content(self, book: Book, query: SearchQuery) -> List[SearchResult]:
        """Search within a specific book."""
        # Use the book's built-in search
        results = book.search_content(query)
        
        # Enhance results with additional information
        for result in results:
            result.path = [book.book_id] + result.path[1:]  # Ensure book ID is in path
        
        return results
    
    # === TEMPLATE MANAGEMENT ===
    
    async def create_template(
        self,
        template_id: str,
        name: str,
        description: str,
        category: str,
        structure: Dict[str, Any],
        default_content: Dict[str, str] = None,
        metadata_template: Dict[str, Any] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """Create book template."""
        try:
            template = BookTemplate(
                template_id=template_id,
                name=name,
                description=description,
                category=category,
                structure=structure,
                default_content=default_content or {},
                metadata_template=metadata_template or {},
                created_by=user_id
            )
            
            success = await self.repository.save_template(template)
            if success:
                logger.info(f"Created template: {template_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create template {template_id}: {str(e)}")
            return False
    
    async def get_template(self, template_id: str) -> Optional[BookTemplate]:
        """Get book template."""
        try:
            return await self.repository.get_template(template_id)
        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {str(e)}")
            return None
    
    async def list_templates(self, category: Optional[str] = None) -> List[BookTemplate]:
        """List book templates."""
        try:
            return await self.repository.list_templates(category)
        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            return []
    
    # === ANALYTICS AND METRICS ===
    
    async def get_book_metrics(self, book_id: str) -> Optional[BookMetrics]:
        """Get book analytics metrics."""
        try:
            return await self.repository.get_metrics(book_id)
        except Exception as e:
            logger.error(f"Failed to get metrics for book {book_id}: {str(e)}")
            return None
    
    async def get_popular_books(self, limit: int = 10) -> List[Tuple[str, BookMetrics]]:
        """Get most popular books by view count."""
        try:
            books = await self.repository.list_books(limit=1000)
            book_metrics = []
            
            for book in books:
                metrics = await self.repository.get_metrics(book.book_id)
                if metrics:
                    book_metrics.append((book.book_id, metrics))
            
            # Sort by view count
            book_metrics.sort(key=lambda x: x[1].view_count, reverse=True)
            return book_metrics[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get popular books: {str(e)}")
            return []
    
    async def get_service_statistics(self) -> Dict[str, Any]:
        """Get service performance statistics."""
        total_books = len(self.repository.books)
        total_templates = len(self.repository.templates)
        total_operations = sum(self.operation_counts.values())
        
        avg_response_times = {}
        for operation, times in self.response_times.items():
            if times:
                avg_response_times[operation] = sum(times) / len(times)
        
        return {
            'total_books': total_books,
            'total_templates': total_templates,
            'total_operations': total_operations,
            'operation_counts': self.operation_counts.copy(),
            'average_response_times': avg_response_times,
            'error_counts': self.error_counts.copy(),
            'active_collaboration_sessions': len(self.collaboration_sessions)
        }
    
    # === VERSION MANAGEMENT ===
    
    async def get_content_versions(self, content_id: str) -> List[ContentVersion]:
        """Get version history for content."""
        try:
            return await self.repository.get_versions(content_id)
        except Exception as e:
            logger.error(f"Failed to get versions for {content_id}: {str(e)}")
            return []
    
    async def revert_to_version(
        self,
        book_id: str,
        content_id: str,
        version_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Revert content to specific version."""
        try:
            # Get version data
            versions = await self.repository.get_versions(content_id)
            target_version = next((v for v in versions if v.version_id == version_id), None)
            
            if not target_version:
                raise ValueError(f"Version {version_id} not found")
            
            # Apply version snapshot (implementation would depend on content type)
            # This is a simplified example
            updates = target_version.content_snapshot
            content_type = target_version.content_type
            
            success = await self.update_content(book_id, content_id, content_type, updates, user_id)
            if success:
                logger.info(f"Reverted {content_id} to version {version_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to revert {content_id} to version {version_id}: {str(e)}")
            return False
    
    # === EXPORT/IMPORT OPERATIONS ===
    
    async def export_book(
        self,
        book_id: str,
        options: BookExportOptions
    ) -> Optional[Dict[str, Any]]:
        """Export book in specified format."""
        start_time = datetime.utcnow()
        
        try:
            book = await self.repository.get_book(book_id)
            if not book:
                raise ValueError(f"Book {book_id} not found")
            
            # Export based on format
            if options.format == "json":
                exported_data = book.to_dict()
                
                # Apply export options
                if not options.include_metadata:
                    exported_data.pop('metadata', None)
                
                if options.selected_chapters:
                    filtered_chapters = [
                        c for c in exported_data['chapters']
                        if c['chapter_id'] in options.selected_chapters
                    ]
                    exported_data['chapters'] = filtered_chapters
                
                await self._record_operation(BookOperation.EXPORT, book_id, start_time)
                logger.info(f"Exported book {book_id} as {options.format}")
                return exported_data
            
            elif options.format == "markdown":
                # Convert to markdown format
                markdown_content = self._convert_to_markdown(book, options)
                exported_data = {
                    'format': 'markdown',
                    'content': markdown_content,
                    'metadata': book.metadata.__dict__ if options.include_metadata else None
                }
                
                await self._record_operation(BookOperation.EXPORT, book_id, start_time)
                return exported_data
            
            else:
                raise ValueError(f"Unsupported export format: {options.format}")
                
        except Exception as e:
            logger.error(f"Failed to export book {book_id}: {str(e)}")
            await self._record_error("export_book", str(e))
            return None
    
    def _convert_to_markdown(self, book: Book, options: BookExportOptions) -> str:
        """Convert book to markdown format."""
        markdown_parts = []
        
        # Title and description
        markdown_parts.append(f"# {book.title}\n")
        if book.description:
            markdown_parts.append(f"{book.description}\n\n")
        
        # Table of contents
        if options.include_metadata:
            toc = book.get_table_of_contents()
            markdown_parts.append("## Table of Contents\n\n")
            for chapter in toc['chapters']:
                markdown_parts.append(f"- [{chapter['title']}](#{chapter['title'].lower().replace(' ', '-')})\n")
                for page in chapter['pages']:
                    markdown_parts.append(f"  - [{page['title']}](#{page['title'].lower().replace(' ', '-')})\n")
            markdown_parts.append("\n")
        
        # Chapters
        for chapter in book.chapters:
            if options.selected_chapters and chapter.chapter_id not in options.selected_chapters:
                continue
                
            markdown_parts.append(f"## {chapter.title}\n\n")
            if chapter.description:
                markdown_parts.append(f"{chapter.description}\n\n")
            
            # Pages
            for page in chapter.pages:
                markdown_parts.append(f"### {page.title}\n\n")
                if page.description:
                    markdown_parts.append(f"{page.description}\n\n")
                
                # Sections
                for section in page.sections:
                    markdown_parts.append(f"#### {section.title}\n\n")
                    markdown_parts.append(f"{section.content}\n\n")
        
        return "".join(markdown_parts)
    
    # === HELPER METHODS ===
    
    async def _index_book_content(self, book: Book) -> None:
        """Index book content for search."""
        try:
            # Index book
            self.search_engine.index_content(
                book.book_id, "book", book.title, 
                book.description, book.metadata
            )
            
            # Index chapters
            for chapter in book.chapters:
                self.search_engine.index_content(
                    chapter.chapter_id, "chapter", chapter.title,
                    chapter.description, chapter.metadata
                )
                
                # Index pages
                for page in chapter.pages:
                    full_content = page.get_full_content(False)
                    self.search_engine.index_content(
                        page.page_id, "page", page.title,
                        full_content, page.metadata
                    )
                    
                    # Index sections
                    for section in page.sections:
                        self.search_engine.index_content(
                            section.section_id, "section", section.title,
                            section.content, section.metadata
                        )
        
        except Exception as e:
            logger.error(f"Failed to index book {book.book_id}: {str(e)}")
    
    async def _create_version_snapshot(
        self,
        book: Book,
        user_id: Optional[str],
        commit_message: str
    ) -> None:
        """Create version snapshot of book."""
        try:
            version = ContentVersion(
                version_id=str(uuid.uuid4()),
                content_id=book.book_id,
                content_type="book",
                version_number=book.metadata.version,
                content_snapshot=book.to_dict(),
                changes=[commit_message],
                created_by=user_id or "system",
                commit_message=commit_message
            )
            
            await self.repository.save_version(version)
            
        except Exception as e:
            logger.error(f"Failed to create version snapshot for {book.book_id}: {str(e)}")
    
    async def _update_view_metrics(self, book_id: str, user_id: Optional[str]) -> None:
        """Update book view metrics."""
        try:
            metrics = await self.repository.get_metrics(book_id)
            if metrics:
                metrics.view_count += 1
                metrics.last_accessed = datetime.utcnow()
                
                if user_id:
                    metrics.unique_visitors.add(user_id)
                
                await self.repository.save_metrics(metrics)
                
        except Exception as e:
            logger.error(f"Failed to update view metrics for {book_id}: {str(e)}")
    
    async def _update_search_metrics(self, query_text: str, result_count: int) -> None:
        """Update search metrics."""
        try:
            # Track search terms across all books
            # In a real implementation, this would be more sophisticated
            pass
            
        except Exception as e:
            logger.error(f"Failed to update search metrics: {str(e)}")
    
    async def _record_operation(self, operation: BookOperation, resource_id: str, start_time: datetime) -> None:
        """Record operation metrics."""
        try:
            self.operation_counts[operation.value] += 1
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            if operation.value not in self.response_times:
                self.response_times[operation.value] = []
            self.response_times[operation.value].append(response_time)
            
            # Keep only recent response times (last 100)
            if len(self.response_times[operation.value]) > 100:
                self.response_times[operation.value] = self.response_times[operation.value][-100:]
                
        except Exception as e:
            logger.error(f"Failed to record operation metrics: {str(e)}")
    
    async def _record_error(self, operation: str, error: str) -> None:
        """Record error metrics."""
        try:
            if operation not in self.error_counts:
                self.error_counts[operation] = 0
            self.error_counts[operation] += 1
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {str(e)}")


# === EXAMPLE USAGE ===

async def example_book_service_usage():
    """Example usage of the Book Service."""
    
    # Initialize service
    service = BookService()
    
    # Create book from template
    book = await service.create_book(
        book_id="project_docs",
        title="Project Documentation",
        description="Complete project documentation and guides",
        author="development_team",
        project_id="main_project",
        template_id="technical_documentation",
        tags=["documentation", "project", "guide"],
        is_public=True
    )
    
    print(f"Created book: {book.book_id if book else 'Failed'}")
    
    if book:
        # Add custom content
        chapter_id = await service.add_chapter(
            book.book_id,
            "Custom Architecture",
            "Detailed architecture documentation",
            user_id="dev_user"
        )
        
        if chapter_id:
            page_id = await service.add_page(
                book.book_id,
                chapter_id,
                "System Components",
                "Overview of system components",
                user_id="dev_user"
            )
            
            if page_id:
                section_id = await service.add_section(
                    book.book_id,
                    page_id,
                    "Agent System",
                    "The Agent System provides comprehensive AI agent management...",
                    ContentType.MARKDOWN,
                    user_id="dev_user"
                )
                
                print(f"Added section: {section_id}")
        
        # Search content
        search_query = SearchQuery(
            query_text="agent system",
            max_results=5,
            semantic_search=True
        )
        
        results = await service.search_books(search_query)
        print(f"\nFound {len(results)} search results:")
        
        for result in results:
            print(f"- {result.title} (Score: {result.relevance_score:.2f})")
            print(f"  Type: {result.content_type}")
            print(f"  Path: {' → '.join(result.path)}")
            print(f"  Snippet: {result.content_snippet[:100]}...")
            print()
        
        # Get book metrics
        metrics = await service.get_book_metrics(book.book_id)
        if metrics:
            print(f"Book Metrics:")
            print(f"- Views: {metrics.view_count}")
            print(f"- Searches: {metrics.search_count}")
            print(f"- Edits: {metrics.edit_count}")
            print(f"- Unique visitors: {len(metrics.unique_visitors)}")
        
        # Export book
        export_options = BookExportOptions(
            format="markdown",
            include_metadata=True,
            max_depth=3
        )
        
        exported_data = await service.export_book(book.book_id, export_options)
        if exported_data:
            print(f"\nExported book as {export_options.format}")
            print(f"Content length: {len(exported_data['content'])} characters")
        
        # Get service statistics
        stats = await service.get_service_statistics()
        print(f"\nService Statistics:")
        print(f"- Total books: {stats['total_books']}")
        print(f"- Total templates: {stats['total_templates']}")
        print(f"- Total operations: {stats['total_operations']}")
        print(f"- Operation counts: {stats['operation_counts']}")


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_book_service_usage())
