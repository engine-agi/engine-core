"""
from sqlalchemy import Column
from typing import Set, Tuple
from pydantic import BaseModel
from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from datetime import datetime
from pydantic import Field
from typing import Optional, List, Dict, Any

from datetime import datetime
from typing import Optional, List, Dict, Any
Book models for Engine Framework.

Books implement hierarchical memory system with:
- Books (top-level containers)
- Chapters (organizational units)
- Pages (content units)
- Semantic search capabilities
- Context tracking and retrieval

Based on Engine Framework data model specification.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field
from sqlalchemy import Column

    Column, String, Text, Boolean, Integer, Float,
    ForeignKey, Index, CheckConstraint
)
import re

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .agent import Agent
    from .team import Team


class BookStatus:
    """Book status values."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PRIVATE = "private"
    SHARED = "shared"


class Book(BaseModel, StringIdentifierMixin, ConfigurationMixin, ValidationMixin):
    """
    Book entity - hierarchical memory and knowledge base.

    Books provide structured memory storage for agents and teams,
    organizing information in a hierarchical format with chapters
    and pages. They support semantic search, context tracking,
    and collaborative knowledge management.

    Key features:
    - Hierarchical organization (book → chapters → pages)
    - Semantic search with embeddings
    - Version control and change tracking
    - Collaborative editing and sharing
    - Context-aware content retrieval
    """

    __tablename__ = "books"

    # Basic book information
    title = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Book title"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Book description and purpose"
    )

    # Book classification and organization
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Book category (e.g., 'project_memory', 'knowledge_base', 'documentation')"
    )

    tags = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Tags for book organization and discovery"
    )

    # Book status and access control
    status = Column(
        String(50),
        nullable=False,
        default=BookStatus.ACTIVE,
        index=True,
        comment="Book status and visibility"
    )

    # Semantic search configuration
    search_config = Column(
        JSONB,
        nullable=True,
        comment="Semantic search configuration and settings"
    )

    # Book metadata
    author = Column(
        String(255),
        nullable=True,
        comment="Book author or creator"
    )

    version = Column(
        String(50),
        nullable=False,
        default="1.0",
        comment="Book version for change management"
    )

    # Content statistics
    chapter_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of chapters in book"
    )

    page_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of pages in book"
    )

    # Access and usage tracking
    access_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times book has been accessed"
    )

    last_accessed_at = Column(
        String(50),
        nullable=True,
        comment="Last access timestamp"
    )

    # Collaborative features
    contributors = Column(
        ARRAY(String(255)),
        nullable=True,
        comment="List of contributors to the book"
    )

    # Book-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    book_metadata = Column(
        JSONB,
        nullable=True,
        comment="Book-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    # === RELATIONSHIPS ===

    # One-to-many relationship with chapters
    chapters = relationship("BookChapter", back_populates="book",
                            cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize book with validation."""
        # Set defaults
        if 'status' not in kwargs:
            kwargs['status'] = BookStatus.ACTIVE
        if 'version' not in kwargs:
            kwargs['version'] = '1.0'
        if 'chapter_count' not in kwargs:
            kwargs['chapter_count'] = 0
        if 'page_count' not in kwargs:
            kwargs['page_count'] = 0
        if 'access_count' not in kwargs:
            kwargs['access_count'] = 0

        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Book(id='{self.id}', title='{self.title}', chapters={self.chapter_count})>"

    # === VALIDATION METHODS ===

    @validates('id')
    def validate_id(self, key: str, value: str) -> str:
        """Validate book ID format."""
        if not value:
            raise ValueError("Book ID is required")

        # Must be alphanumeric with underscores/hyphens, 2-100 characters
        if not re.match(r'^[a-zA-Z0-9_-]{2,100}$', value):
            raise ValueError(
                "Book ID must be 2-100 characters, containing only "
                "letters, numbers, underscores, and hyphens"
            )

        return value.lower()

    @validates('title')
    def validate_title(self, key: str, value: str) -> str:
        """Validate book title."""
        if not value or not value.strip():
            raise ValueError("Book title is required")

        if len(value.strip()) > 255:
            raise ValueError("Book title cannot exceed 255 characters")

        return value.strip()

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate book status."""
        valid_statuses = [BookStatus.ACTIVE, BookStatus.ARCHIVED,
            BookStatus.PRIVATE, BookStatus.SHARED]

        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        return value

    # === CONTENT MANAGEMENT ===

    def add_chapter(self, chapter_id: str, title: str, description: Optional[str] = None) -> "BookChapter":
        """Add chapter to book."""
        chapter = BookChapter(
            id=chapter_id,
            book_id=self.id,
            title=title,
            description=description
        )
        # In real implementation, this would add to session
        # self.chapters.append(chapter)
        self.chapter_count += 1
        return chapter

    def remove_chapter(self, chapter_id: str) -> None:
        """Remove chapter from book."""
        # In real implementation, this would remove from session
        current_count = getattr(self, 'chapter_count', 0)
        setattr(self, 'chapter_count', max(0, current_count - 1))

    def get_chapter(self, chapter_id: str) -> Optional["BookChapter"]:
        """Get chapter by ID."""
        if self.chapters:
            for chapter in self.chapters:
                if chapter.id == chapter_id:
                    return chapter
        return None

    def has_chapter(self, chapter_id: str) -> bool:
        """Check if book has specific chapter."""
        return self.get_chapter(chapter_id) is not None

    # === SEARCH CONFIGURATION ===

    def enable_semantic_search(
        self,
        embedding_model: str = "text-embedding-3-small",
        similarity_threshold: float = 0.8
    ) -> None:
        """Enable semantic search for book."""
        self.search_config = {
            'enabled': True,
            'embedding_model': embedding_model,
            'similarity_threshold': similarity_threshold,
            'index_all_content': True,
            'enabled_at': datetime.utcnow().isoformat()
        }

    def disable_semantic_search(self) -> None:
        """Disable semantic search for book."""
        search_config_value = getattr(self, 'search_config', None)
        if search_config_value:
            search_config_value['enabled'] = False
            search_config_value['disabled_at'] = datetime.utcnow().isoformat()
            setattr(self, 'search_config', search_config_value)

    def is_semantic_search_enabled(self) -> bool:
        """Check if semantic search is enabled."""
        search_config_value = getattr(self, 'search_config', None)
        return search_config_value is not None and search_config_value.get('enabled', False)

    # === ACCESS TRACKING ===

    def record_access(self, accessor: Optional[str] = None) -> None:
        """Record book access."""
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow().isoformat()

        # Track access metadata
        if self.metadata is None:
            self.metadata = {}

        access_history = self.metadata.get('access_history', [])
        access_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'accessor': accessor
        })

        # Keep only last 100 access records
        if len(access_history) > 100:
            access_history = access_history[-100:]

        self.metadata['access_history'] = access_history

    # === COLLABORATIVE FEATURES ===

    def add_contributor(self, contributor: str) -> None:
        """Add contributor to book."""
        contributors_value = getattr(self, 'contributors', None)
        if contributors_value is None:
            setattr(self, 'contributors', [])

        contributors_list = getattr(self, 'contributors', [])
        if contributor not in contributors_list:
            contributors_list.append(contributor)
            setattr(self, 'contributors', contributors_list)

    def remove_contributor(self, contributor: str) -> None:
        """Remove contributor from book."""
        contributors_value = getattr(self, 'contributors', None)
        if contributors_value and contributor in contributors_value:
            contributors_value.remove(contributor)
            setattr(self, 'contributors', contributors_value)

    def has_contributor(self, contributor: str) -> bool:
        """Check if user is a contributor."""
        contributors_value = getattr(self, 'contributors', None)
        return contributors_value is not None and contributor in contributors_value

    # === BOOK SUMMARY ===

    def get_book_summary(self) -> Dict[str, Any]:
        """Get book summary information."""
        contributors_value = getattr(self, 'contributors', None)
        created_at_value = getattr(self, 'created_at', None)
        updated_at_value = getattr(self, 'updated_at', None)

        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'version': self.version,
            'chapter_count': getattr(self, 'chapter_count', 0),
            'page_count': getattr(self, 'page_count', 0),
            'access_count': getattr(self, 'access_count', 0),
            'has_semantic_search': self.is_semantic_search_enabled(),
            'contributor_count': len(contributors_value) if contributors_value else 0,
            'contributors': contributors_value,
            'tags': self.tags,
            'author': self.author,
            'last_accessed_at': self.last_accessed_at,
            'created_at': created_at_value.isoformat() if created_at_value else None,
            'updated_at': updated_at_value.isoformat() if updated_at_value else None
        }


class BookChapter(BaseModel, StringIdentifierMixin, ConfigurationMixin):
    """
    Book chapter - organizational unit within a book.

    Chapters group related pages and provide hierarchical organization.
    They can have their own metadata, ordering, and access controls.
    """

    __tablename__ = "book_chapters"

    # Chapter information
    title = Column(
        String(255),
        nullable=False,
        comment="Chapter title"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Chapter description and overview"
    )

    # Book association
    book_id = Column(
        String(255),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Book this chapter belongs to"
    )

    # Chapter ordering
    order_index = Column(
        Integer,
        nullable=True,
        comment="Chapter order within book"
    )

    # Content statistics
    page_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of pages in chapter"
    )

    # Chapter metadata
    tags = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Chapter-specific tags"
    )

    # Chapter-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    chapter_metadata = Column(
        JSONB,
        nullable=True,
        comment="Chapter-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    # === RELATIONSHIPS ===

    book = relationship("Book", back_populates="chapters")
    pages = relationship("BookPage", back_populates="chapter",
                         cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BookChapter(id='{self.id}', title='{self.title}', pages={self.page_count})>"

    # === PAGE MANAGEMENT ===

    def add_page(self, page_id: str, title: str, content: str) -> "BookPage":
        """Add page to chapter."""
        page = BookPage(
            id=page_id,
            chapter_id=self.id,
            book_id=self.book_id,
            title=title,
            content=content
        )
        # In real implementation, this would add to session
        # self.pages.append(page)
        self.page_count += 1
        return page

    def remove_page(self, page_id: str) -> None:
        """Remove page from chapter."""
        # In real implementation, this would remove from session
        current_count = getattr(self, 'page_count', 0)
        setattr(self, 'page_count', max(0, current_count - 1))

    def get_page(self, page_id: str) -> Optional["BookPage"]:
        """Get page by ID."""
        if self.pages:
            for page in self.pages:
                if page.id == page_id:
                    return page
        return None


class BookPage(BaseModel, StringIdentifierMixin, ConfigurationMixin):
    """
    Book page - content unit within a chapter.

    Pages contain the actual content and are the basic unit of information
    storage. They support rich content, versioning, and semantic indexing.
    """

    __tablename__ = "book_pages"

    # Page information
    title = Column(
        String(255),
        nullable=False,
        comment="Page title"
    )

    content = Column(
        Text,
        nullable=False,
        comment="Page content (markdown, text, or structured data)"
    )

    # Associations
    book_id = Column(
        String(255),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Book this page belongs to"
    )

    chapter_id = Column(
        String(255),
        ForeignKey("book_chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Chapter this page belongs to"
    )

    # Page ordering
    order_index = Column(
        Integer,
        nullable=True,
        comment="Page order within chapter"
    )

    # Content metadata
    content_type = Column(
        String(50),
        nullable=False,
        default="markdown",
        comment="Content type (markdown, text, json, html)"
    )

    word_count = Column(
        Integer,
        nullable=True,
        comment="Approximate word count"
    )

    # Semantic search support
    embedding = Column(
        ARRAY(Float),
        nullable=True,
        comment="Content embedding vector for semantic search"
    )

    embedding_model = Column(
        String(100),
        nullable=True,
        comment="Model used to generate embedding"
    )

    # Page versioning
    version = Column(
        String(50),
        nullable=False,
        default="1.0",
        comment="Page version"
    )

    # Access tracking
    access_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times page has been accessed"
    )

    # Page tags
    tags = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Page-specific tags"
    )

    # Page-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    page_metadata = Column(
        JSONB,
        nullable=True,
        comment="Page-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None

    # === RELATIONSHIPS ===

    book = relationship("Book")
    chapter = relationship("BookChapter", back_populates="pages")

    def __repr__(self) -> str:
        return f"<BookPage(id='{self.id}', title='{self.title}', chapter='{self.chapter_id}')>"

    # === VALIDATION ===

    @validates('content_type')
    def validate_content_type(self, key: str, value: str) -> str:
        """Validate content type."""
        valid_types = ['markdown', 'text', 'json', 'html', 'yaml']

        if value not in valid_types:
            raise ValueError(f"Content type must be one of: {', '.join(valid_types)}")

        return value

    # === CONTENT MANAGEMENT ===

    def update_content(self, new_content: str, version_increment: bool = True) -> None:
        """Update page content with optional version increment."""
        self.content = new_content

        # Update word count (simplified)
        self.word_count = len(new_content.split()) if new_content else 0

        # Increment version if requested
        if version_increment:
            try:
                major, minor = map(int, self.version.split('.'))
                self.version = f"{major}.{minor + 1}"
            except ValueError:
                self.version = "1.1"  # Default increment

    def record_access(self) -> None:
        """Record page access."""
        self.access_count += 1

    def generate_embedding(self, embedding_model: str = "text-embedding-3-small") -> None:
        """Generate embedding for semantic search (placeholder)."""
        # In real implementation, this would call an embedding API
        # For now, just store the model name
        self.embedding_model = embedding_model
        # Placeholder embedding (in real implementation, would be actual vector)
        self.embedding = [0.0] * 1536  # Typical embedding dimension

    def calculate_similarity(self, query_embedding: List[float]) -> float:
        """Calculate similarity with query embedding."""
        embedding_value = getattr(self, 'embedding', None)
        if not embedding_value or not query_embedding:
            return 0.0

        # Simplified cosine similarity calculation
        # In real implementation, would use proper vector operations
        return 0.8  # Placeholder similarity score


# Database indexes for performance
Index('idx_book_category_status', Book.category, Book.status)
Index('idx_book_access_count', Book.access_count)

Index('idx_chapter_book_order', BookChapter.book_id, BookChapter.order_index)
Index('idx_chapter_page_count', BookChapter.page_count)

Index('idx_page_book_chapter', BookPage.book_id, BookPage.chapter_id)
Index('idx_page_content_type', BookPage.content_type)
Index('idx_page_access_count', BookPage.access_count)
Index('idx_page_word_count', BookPage.word_count)

# Database constraints
CheckConstraint(
    Book.status.in_([BookStatus.ACTIVE, BookStatus.ARCHIVED,
                    BookStatus.PRIVATE, BookStatus.SHARED]),
    name='ck_book_status_valid'
)

CheckConstraint(
    Book.chapter_count >= 0,
    name='ck_book_chapter_count_non_negative'
)

CheckConstraint(
    Book.page_count >= 0,
    name='ck_book_page_count_non_negative'
)

CheckConstraint(
    Book.access_count >= 0,
    name='ck_book_access_count_non_negative'
)

CheckConstraint(
    BookChapter.page_count >= 0,
    name='ck_chapter_page_count_non_negative'
)

CheckConstraint(
    BookPage.content_type.in_(['markdown', 'text', 'json', 'html', 'yaml']),
    name='ck_page_content_type_valid'
)

CheckConstraint(
    BookPage.access_count >= 0,
    name='ck_page_access_count_non_negative'
)
