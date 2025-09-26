"""
from pathlib import Path
from typing import Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime

from typing import Optional, List, Dict, Any

from datetime import datetime
from typing import Optional, List, Dict, Any
Book System Core - Hierarchical Memory Management Architecture.

The Book System provides a comprehensive hierarchical memory framework for the
Engine Framework, enabling agents, teams, and workflows to store, organize,
and retrieve information using a chapter-page structure with semantic search
and intelligent content management.

Key Features:
- BookBuilder for declarative memory structure creation
- Hierarchical organization (Book → Chapter → Page → Section)
- Semantic search with vector embeddings
- Content versioning and history tracking
- Cross-references and linking between pages
- Content summarization and indexing
- Access control and permissions
- Multi-format content support (text, code, images, etc.)
- Real-time collaborative editing
- Content lifecycle management

Architecture:
- Abstract BookInterface for consistency
- Hierarchical content models (Book, Chapter, Page, Section)
- SemanticSearchEngine for intelligent retrieval
- ContentManager for format handling
- VersionManager for change tracking
- IndexManager for fast lookups
- PermissionManager for access control

Dependencies:
- Vector embeddings for semantic search
- Content processing pipelines
- Version control systems
- Full-text search engines
- Permission frameworks
"""
import asyncio
import hashlib
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content that can be stored."""

    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    IMAGE = "image"
    DOCUMENT = "document"
    LINK = "link"
    REFERENCE = "reference"


class AccessLevel(Enum):
    """Access levels for content."""

    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


class ContentStatus(Enum):
    """Content lifecycle status."""

    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    DELETED = "deleted"


class SearchScope(Enum):
    """Scope for search operations."""

    BOOK = "book"
    CHAPTER = "chapter"
    PAGE = "page"
    SECTION = "section"
    GLOBAL = "global"


@dataclass
class ContentMetadata:
    """Metadata for content items."""

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1
    content_type: ContentType = ContentType.TEXT
    content_size: int = 0
    checksum: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    language: str = "en"
    encoding: str = "utf-8"
    status: ContentStatus = ContentStatus.DRAFT
    access_level: AccessLevel = AccessLevel.INTERNAL
    expiry_date: Optional[datetime] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentReference:
    """Reference to other content items."""

    target_type: str  # "book", "chapter", "page", "section"
    target_id: str
    reference_type: str  # "link", "embed", "citation", "dependency"
    anchor: Optional[str] = None  # Specific location within target
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """Search query configuration."""

    query_text: str
    content_types: List[ContentType] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    date_range: Optional[Tuple[datetime, datetime]] = None
    access_levels: List[AccessLevel] = field(default_factory=list)
    scope: SearchScope = SearchScope.GLOBAL
    scope_id: Optional[str] = None
    include_archived: bool = False
    max_results: int = 50
    semantic_search: bool = True
    fuzzy_matching: bool = False
    highlight_results: bool = True


@dataclass
class SearchResult:
    """Search result item."""

    content_id: str
    content_type: str  # "book", "chapter", "page", "section"
    title: str
    content_snippet: str
    relevance_score: float
    highlights: List[str] = field(default_factory=list)
    path: List[str] = field(default_factory=list)  # Hierarchical path
    metadata: Optional[ContentMetadata] = None
    references: List[ContentReference] = field(default_factory=list)


class ContentSection:
    """A section within a page with specific content."""

    def __init__(
        self,
        section_id: str,
        title: str,
        content: str = "",
        content_type: ContentType = ContentType.TEXT,
        parent_page_id: Optional[str] = None,
        order: int = 0,
    ):
        """Initialize content section."""
        self.section_id = section_id
        self.title = title
        self.content = content
        self.content_type = content_type
        self.parent_page_id = parent_page_id
        self.order = order
        self.metadata = ContentMetadata(content_type=content_type)
        self.references: List[ContentReference] = []
        self.subsections: List["ContentSection"] = []

        # Update content size and checksum
        self._update_content_metrics()

    def update_content(self, content: str, updated_by: Optional[str] = None) -> None:
        """Update section content."""
        self.content = content
        self.metadata.updated_at = datetime.utcnow()
        self.metadata.updated_by = updated_by
        self.metadata.version += 1
        self._update_content_metrics()

    def add_reference(self, reference: ContentReference) -> None:
        """Add content reference."""
        self.references.append(reference)

    def add_subsection(self, subsection: "ContentSection") -> None:
        """Add subsection."""
        subsection.parent_page_id = self.section_id
        subsection.order = len(self.subsections)
        self.subsections.append(subsection)

    def get_full_content(self, include_subsections: bool = True) -> str:
        """Get full content including subsections."""
        content_parts = [self.content]

        if include_subsections:
            for subsection in sorted(self.subsections, key=lambda s: s.order):
                content_parts.append(f"\n\n## {subsection.title}\n")
                content_parts.append(subsection.get_full_content(True))

        return "".join(content_parts)

    def search_content(self, query: str, case_sensitive: bool = False) -> List[int]:
        """Search for text within content and return positions."""
        content = self.content if case_sensitive else self.content.lower()
        search_query = query if case_sensitive else query.lower()

        positions = []
        start = 0
        while True:
            pos = content.find(search_query, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        return positions

    def _update_content_metrics(self) -> None:
        """Update content size and checksum."""
        content_bytes = self.content.encode("utf-8")
        self.metadata.content_size = len(content_bytes)
        self.metadata.checksum = hashlib.md5(content_bytes).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary."""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
            "content_type": self.content_type.value,
            "parent_page_id": self.parent_page_id,
            "order": self.order,
            "metadata": {
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "created_by": self.metadata.created_by,
                "updated_by": self.metadata.updated_by,
                "version": self.metadata.version,
                "content_size": self.metadata.content_size,
                "checksum": self.metadata.checksum,
                "tags": self.metadata.tags,
                "categories": self.metadata.categories,
                "status": self.metadata.status.value,
                "access_level": self.metadata.access_level.value,
            },
            "references": [
                {
                    "target_type": ref.target_type,
                    "target_id": ref.target_id,
                    "reference_type": ref.reference_type,
                    "anchor": ref.anchor,
                    "label": ref.label,
                }
                for ref in self.references
            ],
            "subsections": [sub.to_dict() for sub in self.subsections],
        }


class BookPage:
    """A page within a chapter containing sections and content."""

    def __init__(
        self,
        page_id: str,
        title: str,
        chapter_id: str,
        order: int = 0,
        description: str = "",
    ):
        """Initialize book page."""
        self.page_id = page_id
        self.title = title
        self.chapter_id = chapter_id
        self.order = order
        self.description = description
        self.metadata = ContentMetadata()
        self.sections: List[ContentSection] = []
        self.references: List[ContentReference] = []
        self.tags: Set[str] = set()
        self.categories: Set[str] = set()

    def add_section(
        self,
        title: str,
        content: str = "",
        content_type: ContentType = ContentType.TEXT,
        section_id: Optional[str] = None,
    ) -> ContentSection:
        """Add a new section to the page."""
        if section_id is None:
            section_id = f"{self.page_id}_section_{len(self.sections) + 1}"

        section = ContentSection(
            section_id=section_id,
            title=title,
            content=content,
            content_type=content_type,
            parent_page_id=self.page_id,
            order=len(self.sections),
        )

        self.sections.append(section)
        self._update_page_metadata()
        return section

    def get_section(self, section_id: str) -> Optional[ContentSection]:
        """Get section by ID."""
        return next((s for s in self.sections if s.section_id == section_id), None)

    def update_section(
        self, section_id: str, content: str, updated_by: Optional[str] = None
    ) -> bool:
        """Update section content."""
        section = self.get_section(section_id)
        if section:
            section.update_content(content, updated_by)
            self._update_page_metadata()
            return True
        return False

    def remove_section(self, section_id: str) -> bool:
        """Remove section from page."""
        section = self.get_section(section_id)
        if section:
            self.sections.remove(section)
            # Reorder remaining sections
            for i, s in enumerate(self.sections):
                s.order = i
            self._update_page_metadata()
            return True
        return False

    def reorder_sections(self, section_order: List[str]) -> bool:
        """Reorder sections based on ID list."""
        try:
            section_dict = {s.section_id: s for s in self.sections}
            reordered_sections = []

            for i, section_id in enumerate(section_order):
                if section_id in section_dict:
                    section = section_dict[section_id]
                    section.order = i
                    reordered_sections.append(section)

            self.sections = reordered_sections
            self._update_page_metadata()
            return True

        except Exception as e:
            logger.error(f"Failed to reorder sections: {str(e)}")
            return False

    def add_reference(self, reference: ContentReference) -> None:
        """Add content reference."""
        self.references.append(reference)

    def add_tag(self, tag: str) -> None:
        """Add tag to page."""
        self.tags.add(tag)
        self.metadata.tags = list(self.tags)

    def add_category(self, category: str) -> None:
        """Add category to page."""
        self.categories.add(category)
        self.metadata.categories = list(self.categories)

    def get_full_content(self, include_metadata: bool = False) -> str:
        """Get full page content including all sections."""
        content_parts = []

        if include_metadata:
            content_parts.append(f"# {self.title}\n")
            if self.description:
                content_parts.append(f"{self.description}\n\n")

        for section in sorted(self.sections, key=lambda s: s.order):
            if section.title:
                content_parts.append(f"## {section.title}\n")
            content_parts.append(section.get_full_content(True))
            content_parts.append("\n\n")

        return "".join(content_parts)

    def search_content(
        self, query: str, case_sensitive: bool = False
    ) -> List[SearchResult]:
        """Search within page content."""
        results = []

        # Search in title and description
        title_content = self.title if case_sensitive else self.title.lower()
        desc_content = self.description if case_sensitive else self.description.lower()
        search_query = query if case_sensitive else query.lower()

        title_score = 0
        if search_query in title_content:
            title_score = 0.9
        if search_query in desc_content:
            title_score = max(title_score, 0.7)

        if title_score > 0:
            results.append(
                SearchResult(
                    content_id=self.page_id,
                    content_type="page",
                    title=self.title,
                    content_snippet=self.description[:200] + "..."
                    if len(self.description) > 200
                    else self.description,
                    relevance_score=title_score,
                    highlights=[self.title] if search_query in title_content else [],
                    path=[self.chapter_id, self.page_id],
                    metadata=self.metadata,
                )
            )

        # Search in sections
        for section in self.sections:
            positions = section.search_content(query, case_sensitive)
            if positions:
                # Create snippet around first match
                snippet_start = max(0, positions[0] - 100)
                snippet_end = min(len(section.content), positions[0] + 100)
                snippet = section.content[snippet_start:snippet_end]

                results.append(
                    SearchResult(
                        content_id=section.section_id,
                        content_type="section",
                        title=section.title,
                        content_snippet=snippet,
                        relevance_score=0.8,
                        highlights=[query],
                        path=[self.chapter_id, self.page_id, section.section_id],
                        metadata=section.metadata,
                    )
                )

        return results

    def get_word_count(self) -> int:
        """Get total word count for page."""
        full_content = self.get_full_content(False)
        return len(full_content.split())

    def get_character_count(self) -> int:
        """Get total character count for page."""
        full_content = self.get_full_content(False)
        return len(full_content)

    def _update_page_metadata(self) -> None:
        """Update page metadata based on content."""
        self.metadata.updated_at = datetime.utcnow()
        self.metadata.version += 1

        # Update content size
        full_content = self.get_full_content(False)
        content_bytes = full_content.encode("utf-8")
        self.metadata.content_size = len(content_bytes)
        self.metadata.checksum = hashlib.md5(content_bytes).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert page to dictionary."""
        return {
            "page_id": self.page_id,
            "title": self.title,
            "chapter_id": self.chapter_id,
            "order": self.order,
            "description": self.description,
            "metadata": {
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "created_by": self.metadata.created_by,
                "updated_by": self.metadata.updated_by,
                "version": self.metadata.version,
                "content_size": self.metadata.content_size,
                "checksum": self.metadata.checksum,
                "tags": list(self.tags),
                "categories": list(self.categories),
                "status": self.metadata.status.value,
                "access_level": self.metadata.access_level.value,
            },
            "references": [
                {
                    "target_type": ref.target_type,
                    "target_id": ref.target_id,
                    "reference_type": ref.reference_type,
                    "anchor": ref.anchor,
                    "label": ref.label,
                }
                for ref in self.references
            ],
            "sections": [section.to_dict() for section in self.sections],
        }


class BookChapter:
    """A chapter within a book containing organized pages."""

    def __init__(
        self,
        chapter_id: str,
        title: str,
        book_id: str,
        order: int = 0,
        description: str = "",
    ):
        """Initialize book chapter."""
        self.chapter_id = chapter_id
        self.title = title
        self.book_id = book_id
        self.order = order
        self.description = description
        self.metadata = ContentMetadata()
        self.pages: List[BookPage] = []
        self.references: List[ContentReference] = []
        self.tags: Set[str] = set()
        self.categories: Set[str] = set()

    def add_page(
        self, title: str, description: str = "", page_id: Optional[str] = None
    ) -> BookPage:
        """Add a new page to the chapter."""
        if page_id is None:
            page_id = f"{self.chapter_id}_page_{len(self.pages) + 1}"

        page = BookPage(
            page_id=page_id,
            title=title,
            chapter_id=self.chapter_id,
            order=len(self.pages),
            description=description,
        )

        self.pages.append(page)
        self._update_chapter_metadata()
        return page

    def get_page(self, page_id: str) -> Optional[BookPage]:
        """Get page by ID."""
        return next((p for p in self.pages if p.page_id == page_id), None)

    def remove_page(self, page_id: str) -> bool:
        """Remove page from chapter."""
        page = self.get_page(page_id)
        if page:
            self.pages.remove(page)
            # Reorder remaining pages
            for i, p in enumerate(self.pages):
                p.order = i
            self._update_chapter_metadata()
            return True
        return False

    def reorder_pages(self, page_order: List[str]) -> bool:
        """Reorder pages based on ID list."""
        try:
            page_dict = {p.page_id: p for p in self.pages}
            reordered_pages = []

            for i, page_id in enumerate(page_order):
                if page_id in page_dict:
                    page = page_dict[page_id]
                    page.order = i
                    reordered_pages.append(page)

            self.pages = reordered_pages
            self._update_chapter_metadata()
            return True

        except Exception as e:
            logger.error(f"Failed to reorder pages: {str(e)}")
            return False

    def search_content(
        self, query: str, case_sensitive: bool = False
    ) -> List[SearchResult]:
        """Search within chapter content."""
        results = []

        # Search in chapter title and description
        title_content = self.title if case_sensitive else self.title.lower()
        desc_content = self.description if case_sensitive else self.description.lower()
        search_query = query if case_sensitive else query.lower()

        chapter_score = 0
        if search_query in title_content:
            chapter_score = 0.9
        if search_query in desc_content:
            chapter_score = max(chapter_score, 0.7)

        if chapter_score > 0:
            results.append(
                SearchResult(
                    content_id=self.chapter_id,
                    content_type="chapter",
                    title=self.title,
                    content_snippet=self.description[:200] + "..."
                    if len(self.description) > 200
                    else self.description,
                    relevance_score=chapter_score,
                    highlights=[self.title] if search_query in title_content else [],
                    path=[self.book_id, self.chapter_id],
                    metadata=self.metadata,
                )
            )

        # Search in all pages
        for page in self.pages:
            page_results = page.search_content(query, case_sensitive)
            results.extend(page_results)

        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def get_page_count(self) -> int:
        """Get total number of pages in chapter."""
        return len(self.pages)

    def get_word_count(self) -> int:
        """Get total word count for chapter."""
        total_words = 0
        for page in self.pages:
            total_words += page.get_word_count()
        return total_words

    def get_character_count(self) -> int:
        """Get total character count for chapter."""
        total_chars = 0
        for page in self.pages:
            total_chars += page.get_character_count()
        return total_chars

    def add_reference(self, reference: ContentReference) -> None:
        """Add content reference."""
        self.references.append(reference)

    def add_tag(self, tag: str) -> None:
        """Add tag to chapter."""
        self.tags.add(tag)
        self.metadata.tags = list(self.tags)

    def add_category(self, category: str) -> None:
        """Add category to chapter."""
        self.categories.add(category)
        self.metadata.categories = list(self.categories)

    def _update_chapter_metadata(self) -> None:
        """Update chapter metadata based on content."""
        self.metadata.updated_at = datetime.utcnow()
        self.metadata.version += 1

        # Aggregate content size from pages
        total_size = 0
        for page in self.pages:
            total_size += page.metadata.content_size
        self.metadata.content_size = total_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert chapter to dictionary."""
        return {
            "chapter_id": self.chapter_id,
            "title": self.title,
            "book_id": self.book_id,
            "order": self.order,
            "description": self.description,
            "metadata": {
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "created_by": self.metadata.created_by,
                "updated_by": self.metadata.updated_by,
                "version": self.metadata.version,
                "content_size": self.metadata.content_size,
                "checksum": self.metadata.checksum,
                "tags": list(self.tags),
                "categories": list(self.categories),
                "status": self.metadata.status.value,
                "access_level": self.metadata.access_level.value,
            },
            "references": [
                {
                    "target_type": ref.target_type,
                    "target_id": ref.target_id,
                    "reference_type": ref.reference_type,
                    "anchor": ref.anchor,
                    "label": ref.label,
                }
                for ref in self.references
            ],
            "pages": [page.to_dict() for page in self.pages],
            "statistics": {
                "page_count": self.get_page_count(),
                "word_count": self.get_word_count(),
                "character_count": self.get_character_count(),
            },
        }


class Book:
    """A complete book containing organized chapters and pages."""

    def __init__(
        self,
        book_id: str,
        title: str,
        description: str = "",
        author: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """Initialize book."""
        self.book_id = book_id
        self.title = title
        self.description = description
        self.author = author
        self.project_id = project_id
        self.metadata = ContentMetadata()
        self.chapters: List[BookChapter] = []
        self.references: List[ContentReference] = []
        self.tags: Set[str] = set()
        self.categories: Set[str] = set()

        # Book-level settings
        self.is_public = False
        self.allow_comments = False
        self.enable_versioning = True
        self.enable_search = True
        self.search_index_enabled = False

    def add_chapter(
        self, title: str, description: str = "", chapter_id: Optional[str] = None
    ) -> BookChapter:
        """Add a new chapter to the book."""
        if chapter_id is None:
            chapter_id = f"{self.book_id}_chapter_{len(self.chapters) + 1}"

        chapter = BookChapter(
            chapter_id=chapter_id,
            title=title,
            book_id=self.book_id,
            order=len(self.chapters),
            description=description,
        )

        self.chapters.append(chapter)
        self._update_book_metadata()
        return chapter

    def get_chapter(self, chapter_id: str) -> Optional[BookChapter]:
        """Get chapter by ID."""
        return next((c for c in self.chapters if c.chapter_id == chapter_id), None)

    def remove_chapter(self, chapter_id: str) -> bool:
        """Remove chapter from book."""
        chapter = self.get_chapter(chapter_id)
        if chapter:
            self.chapters.remove(chapter)
            # Reorder remaining chapters
            for i, c in enumerate(self.chapters):
                c.order = i
            self._update_book_metadata()
            return True
        return False

    def reorder_chapters(self, chapter_order: List[str]) -> bool:
        """Reorder chapters based on ID list."""
        try:
            chapter_dict = {c.chapter_id: c for c in self.chapters}
            reordered_chapters = []

            for i, chapter_id in enumerate(chapter_order):
                if chapter_id in chapter_dict:
                    chapter = chapter_dict[chapter_id]
                    chapter.order = i
                    reordered_chapters.append(chapter)

            self.chapters = reordered_chapters
            self._update_book_metadata()
            return True

        except Exception as e:
            logger.error(f"Failed to reorder chapters: {str(e)}")
            return False

    def get_page(self, page_id: str) -> Optional[BookPage]:
        """Get page by ID from any chapter."""
        for chapter in self.chapters:
            page = chapter.get_page(page_id)
            if page:
                return page
        return None

    def get_section(self, section_id: str) -> Optional[ContentSection]:
        """Get section by ID from any page."""
        for chapter in self.chapters:
            for page in chapter.pages:
                section = page.get_section(section_id)
                if section:
                    return section
        return None

    def search_content(self, query: SearchQuery) -> List[SearchResult]:
        """Search within book content."""
        results = []

        # Search in book title and description if scope allows
        if query.scope in [SearchScope.BOOK, SearchScope.GLOBAL]:
            title_content = self.title.lower()
            desc_content = self.description.lower()
            search_query = query.query_text.lower()

            book_score = 0
            if search_query in title_content:
                book_score = 0.9
            if search_query in desc_content:
                book_score = max(book_score, 0.7)

            if book_score > 0:
                results.append(
                    SearchResult(
                        content_id=self.book_id,
                        content_type="book",
                        title=self.title,
                        content_snippet=self.description[:200] + "..."
                        if len(self.description) > 200
                        else self.description,
                        relevance_score=book_score,
                        highlights=[self.title]
                        if search_query in title_content
                        else [],
                        path=[self.book_id],
                        metadata=self.metadata,
                    )
                )

        # Search in chapters and pages
        for chapter in self.chapters:
            if (
                query.scope == SearchScope.CHAPTER
                and query.scope_id != chapter.chapter_id
            ):
                continue

            chapter_results = chapter.search_content(query.query_text, False)

            # Filter by scope
            if query.scope == SearchScope.PAGE:
                chapter_results = [
                    r for r in chapter_results if query.scope_id in r.path
                ]
            elif query.scope == SearchScope.SECTION:
                chapter_results = [
                    r for r in chapter_results if r.content_id == query.scope_id
                ]

            results.extend(chapter_results)

        # Apply additional filters
        results = self._filter_search_results(results, query)

        # Sort by relevance and limit results
        results = sorted(results, key=lambda r: r.relevance_score, reverse=True)
        return results[: query.max_results]

    def _filter_search_results(
        self, results: List[SearchResult], query: SearchQuery
    ) -> List[SearchResult]:
        """Apply filters to search results."""
        filtered_results = results

        # Filter by content types
        if query.content_types:
            content_type_values = [ct.value for ct in query.content_types]
            filtered_results = [
                r
                for r in filtered_results
                if r.metadata and r.metadata.content_type.value in content_type_values
            ]

        # Filter by tags
        if query.tags:
            filtered_results = [
                r
                for r in filtered_results
                if r.metadata and any(tag in r.metadata.tags for tag in query.tags)
            ]

        # Filter by categories
        if query.categories:
            filtered_results = [
                r
                for r in filtered_results
                if r.metadata
                and any(cat in r.metadata.categories for cat in query.categories)
            ]

        # Filter by date range
        if query.date_range:
            start_date, end_date = query.date_range
            filtered_results = [
                r
                for r in filtered_results
                if r.metadata and start_date <= r.metadata.created_at <= end_date
            ]

        # Filter by access levels
        if query.access_levels:
            access_values = [al.value for al in query.access_levels]
            filtered_results = [
                r
                for r in filtered_results
                if r.metadata and r.metadata.access_level.value in access_values
            ]

        return filtered_results

    def get_table_of_contents(self, max_depth: int = 3) -> Dict[str, Any]:
        """Generate table of contents."""
        toc = {"book_id": self.book_id, "title": self.title, "chapters": []}

        for chapter in sorted(self.chapters, key=lambda c: c.order):
            chapter_entry = {
                "chapter_id": chapter.chapter_id,
                "title": chapter.title,
                "order": chapter.order,
                "pages": [],
            }

            if max_depth > 1:
                for page in sorted(chapter.pages, key=lambda p: p.order):
                    page_entry = {
                        "page_id": page.page_id,
                        "title": page.title,
                        "order": page.order,
                        "sections": [],
                    }

                    if max_depth > 2:
                        for section in sorted(page.sections, key=lambda s: s.order):
                            section_entry = {
                                "section_id": section.section_id,
                                "title": section.title,
                                "order": section.order,
                            }
                            page_entry["sections"].append(section_entry)

                    chapter_entry["pages"].append(page_entry)

            toc["chapters"].append(chapter_entry)

        return toc

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive book statistics."""
        total_pages = sum(len(chapter.pages) for chapter in self.chapters)
        total_sections = sum(
            len(page.sections) for chapter in self.chapters for page in chapter.pages
        )
        total_words = sum(chapter.get_word_count() for chapter in self.chapters)
        total_characters = sum(
            chapter.get_character_count() for chapter in self.chapters
        )

        return {
            "chapter_count": len(self.chapters),
            "page_count": total_pages,
            "section_count": total_sections,
            "word_count": total_words,
            "character_count": total_characters,
            "content_size": self.metadata.content_size,
            "last_updated": self.metadata.updated_at.isoformat(),
            "version": self.metadata.version,
            "tags": list(self.tags),
            "categories": list(self.categories),
        }

    def add_reference(self, reference: ContentReference) -> None:
        """Add content reference."""
        self.references.append(reference)

    def add_tag(self, tag: str) -> None:
        """Add tag to book."""
        self.tags.add(tag)
        self.metadata.tags = list(self.tags)

    def add_category(self, category: str) -> None:
        """Add category to book."""
        self.categories.add(category)
        self.metadata.categories = list(self.categories)

    def _update_book_metadata(self) -> None:
        """Update book metadata based on content."""
        self.metadata.updated_at = datetime.utcnow()
        self.metadata.version += 1

        # Aggregate content size from chapters
        total_size = 0
        for chapter in self.chapters:
            total_size += chapter.metadata.content_size
        self.metadata.content_size = total_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert book to dictionary."""
        return {
            "book_id": self.book_id,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "project_id": self.project_id,
            "metadata": {
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "created_by": self.metadata.created_by,
                "updated_by": self.metadata.updated_by,
                "version": self.metadata.version,
                "content_size": self.metadata.content_size,
                "checksum": self.metadata.checksum,
                "tags": list(self.tags),
                "categories": list(self.categories),
                "status": self.metadata.status.value,
                "access_level": self.metadata.access_level.value,
            },
            "settings": {
                "is_public": self.is_public,
                "allow_comments": self.allow_comments,
                "enable_versioning": self.enable_versioning,
                "enable_search": self.enable_search,
                "search_index_enabled": self.search_index_enabled,
            },
            "references": [
                {
                    "target_type": ref.target_type,
                    "target_id": ref.target_id,
                    "reference_type": ref.reference_type,
                    "anchor": ref.anchor,
                    "label": ref.label,
                }
                for ref in self.references
            ],
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "statistics": self.get_statistics(),
            "table_of_contents": self.get_table_of_contents(),
        }


class BookBuilder:
    """Builder for creating books with a fluent interface."""

    def __init__(self):
        """Initialize book builder."""
        self.reset()

    def reset(self):
        """Reset builder to initial state."""
        self._book_id = None
        self._title = None
        self._description = ""
        self._author = None
        self._project_id = None
        self._is_public = False
        self._allow_comments = False
        self._enable_versioning = True
        self._enable_search = True
        self._tags = set()
        self._categories = set()
        self._access_level = AccessLevel.INTERNAL
        self._content_status = ContentStatus.DRAFT
        return self

    def with_id(self, book_id: str):
        """Set book ID."""
        self._book_id = book_id
        return self

    def with_title(self, title: str):
        """Set book title."""
        self._title = title
        return self

    def with_description(self, description: str):
        """Set book description."""
        self._description = description
        return self

    def with_author(self, author: str):
        """Set book author."""
        self._author = author
        return self

    def with_project(self, project_id: str):
        """Set project ID."""
        self._project_id = project_id
        return self

    def with_public_access(self, is_public: bool = True):
        """Set public access."""
        self._is_public = is_public
        return self

    def with_comments_enabled(self, allow_comments: bool = True):
        """Enable comments."""
        self._allow_comments = allow_comments
        return self

    def with_versioning(self, enable_versioning: bool = True):
        """Enable versioning."""
        self._enable_versioning = enable_versioning
        return self

    def with_search_enabled(self, enable_search: bool = True):
        """Enable search."""
        self._enable_search = enable_search
        return self

    def with_access_level(self, access_level: AccessLevel):
        """Set access level."""
        self._access_level = access_level
        return self

    def with_status(self, status: ContentStatus):
        """Set content status."""
        self._content_status = status
        return self

    def add_tag(self, tag: str):
        """Add tag."""
        self._tags.add(tag)
        return self

    def add_tags(self, tags: List[str]):
        """Add multiple tags."""
        self._tags.update(tags)
        return self

    def add_category(self, category: str):
        """Add category."""
        self._categories.add(category)
        return self

    def add_categories(self, categories: List[str]):
        """Add multiple categories."""
        self._categories.update(categories)
        return self

    def build(self) -> Book:
        """Build the book."""
        if not self._book_id:
            raise ValueError("Book ID is required")
        if not self._title:
            raise ValueError("Book title is required")

        # Create book
        book = Book(
            book_id=self._book_id,
            title=self._title,
            description=self._description,
            author=self._author,
            project_id=self._project_id,
        )

        # Set configuration
        book.is_public = self._is_public
        book.allow_comments = self._allow_comments
        book.enable_versioning = self._enable_versioning
        book.enable_search = self._enable_search

        # Set metadata
        book.metadata.access_level = self._access_level
        book.metadata.status = self._content_status
        book.metadata.tags = list(self._tags)
        book.metadata.categories = list(self._categories)
        book.tags = self._tags.copy()
        book.categories = self._categories.copy()

        # Reset for next build
        self.reset()

        return book


# === SEMANTIC SEARCH ENGINE ===


class SemanticSearchEngine:
    """Semantic search engine for book content."""

    def __init__(self, enable_embeddings: bool = False):
        """Initialize semantic search engine."""
        self.enable_embeddings = enable_embeddings
        self.content_index: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: Dict[str, Set[str]] = {}

        # Mock embedding function (in production, use actual embeddings)
        self._embeddings_cache: Dict[str, List[float]] = {}

    def index_content(
        self,
        content_id: str,
        content_type: str,
        title: str,
        content: str,
        metadata: ContentMetadata,
    ) -> None:
        """Index content for search."""

        # Store content in index
        self.content_index[content_id] = {
            "content_type": content_type,
            "title": title,
            "content": content,
            "metadata": metadata,
            "indexed_at": datetime.utcnow(),
        }

        # Build inverted index for full-text search
        words = self._extract_words(title + " " + content)
        for word in words:
            if word not in self.inverted_index:
                self.inverted_index[word] = set()
            self.inverted_index[word].add(content_id)

        # Generate embeddings if enabled
        if self.enable_embeddings:
            combined_text = f"{title} {content}"
            self._embeddings_cache[content_id] = self._generate_embedding(combined_text)

    def search(self, query: SearchQuery, book: Book) -> List[SearchResult]:
        """Perform semantic search."""

        if query.semantic_search and self.enable_embeddings:
            return self._semantic_search(query, book)
        else:
            return self._keyword_search(query, book)

    def _keyword_search(self, query: SearchQuery, book: Book) -> List[SearchResult]:
        """Perform keyword-based search."""
        query_words = self._extract_words(query.query_text)
        matching_content_ids = set()

        # Find content IDs that contain query words
        for word in query_words:
            if word in self.inverted_index:
                if not matching_content_ids:
                    matching_content_ids = self.inverted_index[word].copy()
                else:
                    matching_content_ids &= self.inverted_index[word]

        # Score and create search results
        results = []
        for content_id in matching_content_ids:
            if content_id in self.content_index:
                index_entry = self.content_index[content_id]

                # Calculate relevance score
                score = self._calculate_relevance_score(
                    query.query_text, index_entry["title"], index_entry["content"]
                )

                # Create search result
                snippet = self._create_snippet(index_entry["content"], query.query_text)
                highlights = self._extract_highlights(
                    index_entry["title"] + " " + index_entry["content"],
                    query.query_text,
                )

                result = SearchResult(
                    content_id=content_id,
                    content_type=index_entry["content_type"],
                    title=index_entry["title"],
                    content_snippet=snippet,
                    relevance_score=score,
                    highlights=highlights,
                    metadata=index_entry["metadata"],
                )

                results.append(result)

        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    def _semantic_search(self, query: SearchQuery, book: Book) -> List[SearchResult]:
        """Perform semantic search using embeddings."""
        # Generate query embedding
        query_embedding = self._generate_embedding(query.query_text)

        # Calculate similarity with all indexed content
        similarities = []
        for content_id, content_embedding in self._embeddings_cache.items():
            similarity = self._cosine_similarity(query_embedding, content_embedding)
            similarities.append((content_id, similarity))

        # Sort by similarity and create results
        results = []
        for content_id, similarity in sorted(
            similarities, key=lambda x: x[1], reverse=True
        ):
            if content_id in self.content_index and similarity > 0.1:  # Threshold
                index_entry = self.content_index[content_id]

                snippet = self._create_snippet(index_entry["content"], query.query_text)

                result = SearchResult(
                    content_id=content_id,
                    content_type=index_entry["content_type"],
                    title=index_entry["title"],
                    content_snippet=snippet,
                    relevance_score=similarity,
                    metadata=index_entry["metadata"],
                )

                results.append(result)

        return results

    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text."""
        # Simple word extraction (in production, use proper tokenization)
        words = re.findall(r"\b\w+\b", text.lower())
        return [word for word in words if len(word) > 2]  # Filter short words

    def _calculate_relevance_score(self, query: str, title: str, content: str) -> float:
        """Calculate relevance score for keyword search."""
        query_words = set(self._extract_words(query))
        title_words = set(self._extract_words(title))
        content_words = set(self._extract_words(content))

        # Title match gets higher weight
        title_matches = len(query_words & title_words)
        content_matches = len(query_words & content_words)

        title_score = (title_matches / len(query_words)) * 0.7 if query_words else 0
        content_score = (content_matches / len(query_words)) * 0.3 if query_words else 0

        return title_score + content_score

    def _create_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """Create content snippet around query match."""
        query_lower = query.lower()
        content_lower = content.lower()

        match_pos = content_lower.find(query_lower)
        if match_pos == -1:
            return (
                content[:max_length] + "..." if len(content) > max_length else content
            )

        start = max(0, match_pos - max_length // 2)
        end = min(len(content), match_pos + max_length // 2)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _extract_highlights(self, text: str, query: str) -> List[str]:
        """Extract highlighted terms from text."""
        query_words = self._extract_words(query)
        highlights = []

        for word in query_words:
            # Find actual word matches in text (case-insensitive)
            pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
            matches = pattern.findall(text)
            highlights.extend(matches)

        return list(set(highlights))  # Remove duplicates

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding vector."""
        # Mock implementation - in production, use actual embedding model
        import hashlib

        hash_obj = hashlib.md5(text.encode())
        hash_hex = hash_obj.hexdigest()

        # Convert hash to float vector
        embedding = []
        for i in range(0, len(hash_hex), 2):
            val = int(hash_hex[i : i + 2], 16) / 255.0
            embedding.append(val)

        # Normalize vector
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# === EXAMPLE USAGE ===


async def example_book_usage():
    """Example usage of the Book system."""

    # Create a book using the builder
    book = (
        BookBuilder()
        .with_id("technical_guide")
        .with_title("Engine Framework Technical Guide")
        .with_description("Comprehensive guide for the Engine Framework")
        .with_author("Development Team")
        .with_project("engine_framework")
        .add_tags(["technical", "guide", "framework"])
        .add_categories(["documentation", "development"])
        .with_public_access(True)
        .with_search_enabled(True)
        .build()
    )

    # Add chapters
    intro_chapter = book.add_chapter("Introduction", "Overview of the Engine Framework")

    architecture_chapter = book.add_chapter(
        "Architecture", "System architecture and design patterns"
    )

    # Add pages to chapters
    overview_page = intro_chapter.add_page(
        "Framework Overview", "High-level overview of framework capabilities"
    )

    getting_started_page = intro_chapter.add_page(
        "Getting Started", "Quick start guide for new users"
    )

    # Add sections to pages
    overview_page.add_section(
        "What is Engine Framework",
        "The Engine Framework is a comprehensive AI agent orchestration system...",
        ContentType.MARKDOWN,
    )

    overview_page.add_section(
        "Key Features",
        "- Agent Management\n- Team Coordination\n- Workflow Orchestration\n- Tool Integration",
        ContentType.MARKDOWN,
    )

    getting_started_page.add_section(
        "Installation", "pip install engine-agi", ContentType.CODE
    )

    # Add content to architecture chapter
    core_page = architecture_chapter.add_page(
        "Core Components", "Overview of the six core pillars"
    )

    core_page.add_section(
        "Agent System",
        "The Agent System provides AI agent creation and management capabilities...",
        ContentType.TEXT,
    )

    # Search content
    search_query = SearchQuery(
        query_text="agent management", max_results=10, semantic_search=False
    )

    results = book.search_content(search_query)
    print(f"Found {len(results)} search results")

    for result in results:
        print(f"- {result.title} (Score: {result.relevance_score:.2f})")
        print(f"  Path: {' → '.join(result.path)}")
        print(f"  Snippet: {result.content_snippet[:100]}...")
        print()

    # Get statistics
    stats = book.get_statistics()
    print(f"Book Statistics:")
    print(f"- Chapters: {stats['chapter_count']}")
    print(f"- Pages: {stats['page_count']}")
    print(f"- Sections: {stats['section_count']}")
    print(f"- Words: {stats['word_count']}")
    print(f"- Characters: {stats['character_count']}")

    # Get table of contents
    toc = book.get_table_of_contents()
    print(f"\nTable of Contents:")
    print(json.dumps(toc, indent=2))

    # Convert to dictionary for serialization
    book_dict = book.to_dict()
    print(
        f"\nBook serialized to dictionary with {len(json.dumps(book_dict))} characters"
    )


if __name__ == "__main__":
    # Run example
    import asyncio

    asyncio.run(example_book_usage())
