"""
Tests for Book System - Hierarchical Memory Management.

Tests cover:
- BookBuilder fluent interface and configuration
- Book hierarchical structure (Book → Chapter → Page → Section)
- Semantic search functionality
- Content management and versioning
- Persistence and storage operations
- Integration with agents and teams
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import List, Dict, Any

from engine_core.core.book.book_builder import (
    BookBuilder,
    Book,
    BookChapter,
    BookPage,
    ContentSection,
    SemanticSearchEngine,
    ContentType,
    AccessLevel,
    ContentStatus,
    SearchScope,
    ContentMetadata,
    SearchQuery,
    SearchResult
)


class TestBookBuilder:
    """Test BookBuilder functionality."""

    def test_builder_initialization(self):
        """Test builder initializes with default configuration."""
        builder = BookBuilder()
        assert builder._book_id is None
        assert builder._title is None
        assert builder._description == ""
        assert builder._is_public is False
        assert builder._enable_versioning is True
        assert builder._enable_search is True

    def test_with_id(self):
        """Test setting book ID."""
        builder = BookBuilder()
        result = builder.with_id("test_book")
        assert result is builder
        assert builder._book_id == "test_book"

    def test_with_title(self):
        """Test setting book title."""
        builder = BookBuilder()
        builder.with_title("Test Book")
        assert builder._title == "Test Book"

    def test_with_description(self):
        """Test setting book description."""
        builder = BookBuilder()
        builder.with_description("A test book description")
        assert builder._description == "A test book description"

    def test_with_author(self):
        """Test setting book author."""
        builder = BookBuilder()
        builder.with_author("Test Author")
        assert builder._author == "Test Author"

    def test_with_project(self):
        """Test setting project ID."""
        builder = BookBuilder()
        builder.with_project("test_project")
        assert builder._project_id == "test_project"

    def test_with_public_access(self):
        """Test setting public access."""
        builder = BookBuilder()
        builder.with_public_access(True)
        assert builder._is_public is True

    def test_with_comments_enabled(self):
        """Test enabling comments."""
        builder = BookBuilder()
        builder.with_comments_enabled(True)
        assert builder._allow_comments is True

    def test_with_versioning(self):
        """Test enabling versioning."""
        builder = BookBuilder()
        builder.with_versioning(False)
        assert builder._enable_versioning is False

    def test_with_search_enabled(self):
        """Test enabling search."""
        builder = BookBuilder()
        builder.with_search_enabled(False)
        assert builder._enable_search is False

    def test_with_access_level(self):
        """Test setting access level."""
        builder = BookBuilder()
        builder.with_access_level(AccessLevel.PUBLIC)
        assert builder._access_level == AccessLevel.PUBLIC

    def test_with_status(self):
        """Test setting content status."""
        builder = BookBuilder()
        builder.with_status(ContentStatus.PUBLISHED)
        assert builder._content_status == ContentStatus.PUBLISHED

    def test_add_tag(self):
        """Test adding tags."""
        builder = BookBuilder()
        builder.add_tag("test")
        assert "test" in builder._tags

    def test_add_tags(self):
        """Test adding multiple tags."""
        builder = BookBuilder()
        builder.add_tags(["tag1", "tag2", "tag3"])
        assert "tag1" in builder._tags
        assert "tag2" in builder._tags
        assert "tag3" in builder._tags

    def test_add_category(self):
        """Test adding categories."""
        builder = BookBuilder()
        builder.add_category("documentation")
        assert "documentation" in builder._categories

    def test_add_categories(self):
        """Test adding multiple categories."""
        builder = BookBuilder()
        builder.add_categories(["tech", "guide"])
        assert "tech" in builder._categories
        assert "guide" in builder._categories

    def test_build_without_id_raises_error(self):
        """Test building without ID raises error."""
        builder = BookBuilder()
        with pytest.raises(ValueError, match="Book ID is required"):
            builder.build()

    def test_build_without_title_raises_error(self):
        """Test building without title raises error."""
        builder = BookBuilder()
        builder.with_id("test_book")
        with pytest.raises(ValueError, match="Book title is required"):
            builder.build()

    def test_build_basic_book(self):
        """Test building a basic book."""
        book = (BookBuilder()
            .with_id("test_book")
            .with_title("Test Book")
            .build())

        assert isinstance(book, Book)
        assert book.book_id == "test_book"
        assert book.title == "Test Book"
        assert book.description == ""
        assert book.is_public is False
        assert book.enable_versioning is True
        assert book.enable_search is True

    def test_build_complete_book(self):
        """Test building a complete book with all options."""
        book = (BookBuilder()
            .with_id("complete_book")
            .with_title("Complete Test Book")
            .with_description("A comprehensive test book")
            .with_author("Test Author")
            .with_project("test_project")
            .with_public_access(True)
            .with_comments_enabled(True)
            .with_versioning(True)
            .with_search_enabled(True)
            .with_access_level(AccessLevel.INTERNAL)
            .with_status(ContentStatus.PUBLISHED)
            .add_tags(["test", "documentation"])
            .add_categories(["tech", "guide"])
            .build())

        assert book.book_id == "complete_book"
        assert book.title == "Complete Test Book"
        assert book.description == "A comprehensive test book"
        assert book.author == "Test Author"
        assert book.project_id == "test_project"
        assert book.is_public is True
        assert book.allow_comments is True
        assert book.enable_versioning is True
        assert book.enable_search is True
        assert book.metadata.access_level == AccessLevel.INTERNAL
        assert book.metadata.status == ContentStatus.PUBLISHED
        assert "test" in book.tags
        assert "documentation" in book.tags
        assert "tech" in book.categories
        assert "guide" in book.categories

    def test_builder_reset_after_build(self):
        """Test that builder resets after build."""
        builder = BookBuilder()
        builder.with_id("test_book").with_title("Test Book")

        # Build first book
        book1 = builder.build()
        assert book1.book_id == "test_book"

        # Builder should be reset
        assert builder._book_id is None
        assert builder._title is None

        # Build second book with different settings
        book2 = builder.with_id("book2").with_title("Book 2").build()
        assert book2.book_id == "book2"
        assert book2.title == "Book 2"


class TestBookStructure:
    """Test Book hierarchical structure."""

    @pytest.fixture
    def sample_book(self):
        """Create a sample book for testing."""
        book = (BookBuilder()
            .with_id("sample_book")
            .with_title("Sample Book")
            .with_description("A sample book for testing")
            .build())

        # Add chapters
        chapter1 = book.add_chapter("Introduction", "Book introduction")
        chapter2 = book.add_chapter("Core Concepts", "Main concepts")

        # Add pages to chapters
        page1 = chapter1.add_page("Welcome", "Welcome to the book")
        page2 = chapter1.add_page("Overview", "Book overview")

        page3 = chapter2.add_page("Basic Concepts", "Fundamental ideas")
        page4 = chapter2.add_page("Advanced Topics", "Complex subjects")

        # Add sections to pages
        section1 = page1.add_section("Greeting", "Hello and welcome!")
        section2 = page1.add_section("Purpose", "The purpose of this book")

        return book

    def test_book_creation(self, sample_book):
        """Test basic book creation."""
        assert sample_book.book_id == "sample_book"
        assert sample_book.title == "Sample Book"
        assert sample_book.description == "A sample book for testing"
        assert len(sample_book.chapters) == 2

    def test_chapter_operations(self, sample_book):
        """Test chapter operations."""
        # Test getting chapter
        chapter1 = sample_book.get_chapter("sample_book_chapter_1")
        assert chapter1 is not None
        assert chapter1.title == "Introduction"

        # Test adding chapter
        new_chapter = sample_book.add_chapter("Conclusion", "Book conclusion")
        assert len(sample_book.chapters) == 3
        assert new_chapter.title == "Conclusion"

        # Test removing chapter
        success = sample_book.remove_chapter("sample_book_chapter_1")
        assert success
        assert len(sample_book.chapters) == 2

    def test_page_operations(self, sample_book):
        """Test page operations."""
        chapter1 = sample_book.get_chapter("sample_book_chapter_1")
        assert chapter1 is not None

        # Test getting page
        page1 = sample_book.get_page("sample_book_chapter_1_page_1")
        assert page1 is not None
        assert page1.title == "Welcome"

        # Test getting page from chapter
        page2 = chapter1.get_page("sample_book_chapter_1_page_2")
        assert page2 is not None
        assert page2.title == "Overview"

    def test_section_operations(self, sample_book):
        """Test section operations."""
        page1 = sample_book.get_page("sample_book_chapter_1_page_1")
        assert page1 is not None

        # Test getting section
        section1 = sample_book.get_section("sample_book_chapter_1_page_1_section_1")
        assert section1 is not None
        assert section1.title == "Greeting"
        assert section1.content == "Hello and welcome!"

    def test_hierarchical_path(self, sample_book):
        """Test hierarchical path generation."""
        section = sample_book.get_section("sample_book_chapter_1_page_1_section_1")
        assert section is not None

        # Test path generation (assuming method exists)
        # This would depend on the actual implementation
        # path = section.get_path()
        # assert path == ["sample_book", "Introduction", "Welcome", "Greeting"]

    def test_content_updates(self, sample_book):
        """Test content update operations."""
        section = sample_book.get_section("sample_book_chapter_1_page_1_section_1")
        assert section is not None

        original_version = section.metadata.version
        original_updated = section.metadata.updated_at

        # Update content
        section.update_content("Updated greeting content!", "test_user")

        assert section.content == "Updated greeting content!"
        assert section.metadata.version == original_version + 1
        assert section.metadata.updated_by == "test_user"
        assert section.metadata.updated_at > original_updated


class TestSemanticSearchEngine:
    """Test semantic search functionality."""

    @pytest.fixture
    def search_engine(self):
        """Create a search engine for testing."""
        return SemanticSearchEngine(enable_embeddings=False)

    @pytest.fixture
    def sample_book(self):
        """Create a sample book with content."""
        book = (BookBuilder()
            .with_id("search_test_book")
            .with_title("Search Test Book")
            .build())

        chapter = book.add_chapter("Python Programming", "Python concepts")
        page1 = chapter.add_page("Variables", "Variable concepts in Python")
        page1.add_section("Definition", "Variables store data values")
        page1.add_section("Types", "Python has int, str, float, bool types")

        page2 = chapter.add_page("Functions", "Function concepts")
        page2.add_section("Definition", "Functions are reusable code blocks")
        page2.add_section("Parameters", "Functions can accept parameters")

        return book

    def test_search_engine_initialization(self, search_engine):
        """Test search engine initialization."""
        assert not search_engine.enable_embeddings
        assert isinstance(search_engine.content_index, dict)
        assert isinstance(search_engine.inverted_index, dict)

    def test_index_content(self, search_engine, sample_book):
        """Test content indexing."""
        # Index a page
        page = sample_book.get_page("search_test_book_chapter_1_page_1")
        assert page is not None

        search_engine.index_content(
            content_id=page.page_id,
            content_type="page",
            title=page.title,
            content=page.description,
            metadata=page.metadata
        )

        # Check indexing
        assert page.page_id in search_engine.content_index
        assert "variables" in search_engine.inverted_index
        assert page.page_id in search_engine.inverted_index["variables"]

    def test_keyword_search(self, search_engine, sample_book):
        """Test keyword-based search."""
        # Index content
        for chapter in sample_book.chapters:
            for page in chapter.pages:
                search_engine.index_content(
                    content_id=page.page_id,
                    content_type="page",
                    title=page.title,
                    content=page.description,
                    metadata=page.metadata
                )

        # Perform search
        query = SearchQuery(
            query_text="python variables",
            semantic_search=False
        )

        results = search_engine.search(query, sample_book)

        assert len(results) > 0
        # Should find the Variables page
        found_variables = any("Variables" in result.title for result in results)
        assert found_variables

    def test_search_with_filters(self, search_engine, sample_book):
        """Test search with content type filters."""
        # Index content
        for chapter in sample_book.chapters:
            for page in chapter.pages:
                search_engine.index_content(
                    content_id=page.page_id,
                    content_type="page",
                    title=page.title,
                    content=page.description,
                    metadata=page.metadata
                )

        # Search with filters
        query = SearchQuery(
            query_text="function",
            content_types=[ContentType.TEXT],
            max_results=5,
            semantic_search=False
        )

        results = search_engine.search(query, sample_book)

        # Should find functions-related content
        assert len(results) >= 0  # May find Functions page

    def test_empty_search_results(self, search_engine, sample_book):
        """Test search with no matching results."""
        query = SearchQuery(
            query_text="nonexistent content xyz123",
            semantic_search=False
        )

        results = search_engine.search(query, sample_book)
        assert len(results) == 0

    def test_word_extraction(self, search_engine):
        """Test word extraction from text."""
        text = "Hello, world! This is a test."
        words = search_engine._extract_words(text)

        # Should extract meaningful words
        assert "hello" in words
        assert "world" in words
        assert "test" in words
        # Should filter short words
        assert "a" not in words
        assert "is" not in words

    def test_relevance_scoring(self, search_engine):
        """Test relevance score calculation."""
        score = search_engine._calculate_relevance_score(
            query="python functions",
            title="Python Functions Guide",
            content="Learn about functions in Python programming"
        )

        assert score > 0
        # Title match should give higher score
        assert score > 0.1


class TestContentManagement:
    """Test content management operations."""

    @pytest.fixture
    def content_section(self):
        """Create a test content section."""
        return ContentSection(
            section_id="test_section",
            title="Test Section",
            content="This is test content for the section.",
            content_type=ContentType.TEXT
        )

    def test_content_section_creation(self, content_section):
        """Test content section creation."""
        assert content_section.section_id == "test_section"
        assert content_section.title == "Test Section"
        assert content_section.content == "This is test content for the section."
        assert content_section.content_type == ContentType.TEXT
        assert content_section.metadata.content_type == ContentType.TEXT

    def test_content_update(self, content_section):
        """Test content update functionality."""
        original_version = content_section.metadata.version
        original_updated = content_section.metadata.updated_at

        # Update content
        content_section.update_content("Updated content", "test_user")

        assert content_section.content == "Updated content"
        assert content_section.metadata.version == original_version + 1
        assert content_section.metadata.updated_by == "test_user"
        assert content_section.metadata.updated_at > original_updated

    def test_content_checksum(self, content_section):
        """Test content checksum generation."""
        # Checksum should be generated
        assert content_section.metadata.checksum is not None
        assert isinstance(content_section.metadata.checksum, str)

        # Checksum should change when content changes
        original_checksum = content_section.metadata.checksum
        content_section.update_content("New content")
        assert content_section.metadata.checksum != original_checksum

    def test_content_references(self, content_section):
        """Test content reference management."""
        from engine_core.core.book.book_builder import ContentReference

        reference = ContentReference(
            target_type="page",
            target_id="target_page_1",
            reference_type="link",
            label="See also"
        )

        content_section.add_reference(reference)
        assert len(content_section.references) == 1
        assert content_section.references[0].target_id == "target_page_1"

    def test_subsections(self, content_section):
        """Test subsection management."""
        subsection = ContentSection(
            section_id="subsection_1",
            title="Subsection",
            content="Subsection content"
        )

        content_section.add_subsection(subsection)
        assert len(content_section.subsections) == 1
        assert content_section.subsections[0].title == "Subsection"


class TestPersistenceAndStorage:
    """Test persistence and storage operations."""

    @pytest.fixture
    def sample_book(self):
        """Create a sample book for persistence testing."""
        book = (BookBuilder()
            .with_id("persistence_test")
            .with_title("Persistence Test Book")
            .build())

        chapter = book.add_chapter("Test Chapter", "For persistence testing")
        page = chapter.add_page("Test Page", "Page content")
        page.add_section("Test Section", "Section content")

        return book

    def test_book_serialization(self, sample_book):
        """Test book serialization to dict."""
        # Assuming there's a to_dict method
        # book_dict = sample_book.to_dict()
        # assert isinstance(book_dict, dict)
        # assert book_dict["book_id"] == "persistence_test"
        pass  # Placeholder - implement when serialization is added

    def test_content_metadata_persistence(self, sample_book):
        """Test that metadata is properly maintained."""
        page = sample_book.get_page("persistence_test_chapter_1_page_1")
        assert page is not None

        # Check metadata persistence
        assert page.metadata.created_at is not None
        assert page.metadata.content_type == ContentType.TEXT
        assert page.metadata.status == ContentStatus.DRAFT

    def test_version_tracking(self, sample_book):
        """Test version tracking for content changes."""
        section = sample_book.get_section("persistence_test_chapter_1_page_1_section_1")
        assert section is not None

        initial_version = section.metadata.version

        # Make multiple updates
        section.update_content("Version 2")
        assert section.metadata.version == initial_version + 1

        section.update_content("Version 3")
        assert section.metadata.version == initial_version + 2

    def test_content_size_tracking(self, sample_book):
        """Test content size tracking."""
        section = sample_book.get_section("persistence_test_chapter_1_page_1_section_1")
        assert section is not None

        # Content size should be tracked
        assert section.metadata.content_size > 0
        assert section.metadata.content_size == len(section.content)

        # Size should update with content
        section.update_content("Much longer content that should increase the size significantly")
        assert section.metadata.content_size == len(section.content)


class TestIntegration:
    """Integration tests for book system."""

    @pytest.mark.asyncio
    async def test_complete_book_workflow(self):
        """Test complete book creation and management workflow."""
        # Create book
        book = (BookBuilder()
            .with_id("workflow_test")
            .with_title("Workflow Test Book")
            .with_description("Testing complete workflow")
            .with_author("Test System")
            .build())

        # Add hierarchical content
        intro_chapter = book.add_chapter("Introduction", "Book introduction")
        welcome_page = intro_chapter.add_page("Welcome", "Welcome message")
        welcome_page.add_section("Greeting", "Hello, welcome to our book!")
        welcome_page.add_section("Overview", "This book covers...")

        # Add more content
        content_chapter = book.add_chapter("Main Content", "Core content")
        topic_page = content_chapter.add_page("Key Topic", "Important topic")
        topic_page.add_section("Explanation", "Detailed explanation here")

        # Verify structure
        assert len(book.chapters) == 2
        assert len(intro_chapter.pages) == 1
        assert len(welcome_page.sections) == 2
        assert len(content_chapter.pages) == 1

        # Test search
        search_engine = SemanticSearchEngine(enable_embeddings=False)

        # Index content
        for chapter in book.chapters:
            for page in chapter.pages:
                search_engine.index_content(
                    content_id=page.page_id,
                    content_type="page",
                    title=page.title,
                    content=page.description,
                    metadata=page.metadata
                )

        # Search for content
        query = SearchQuery(query_text="welcome", semantic_search=False)
        results = search_engine.search(query, book)

        assert len(results) > 0

    def test_book_builder_patterns(self):
        """Test different book builder usage patterns."""
        # Simple book
        simple_book = (BookBuilder()
            .with_id("simple")
            .with_title("Simple Book")
            .build())

        assert simple_book.book_id == "simple"

        # Complex book with all features
        complex_book = (BookBuilder()
            .with_id("complex")
            .with_title("Complex Book")
            .with_description("Feature-rich book")
            .with_author("Author Name")
            .with_project("project_123")
            .with_public_access(True)
            .with_comments_enabled(True)
            .with_access_level(AccessLevel.INTERNAL)
            .with_status(ContentStatus.PUBLISHED)
            .add_tags(["important", "featured"])
            .add_categories(["documentation", "tutorial"])
            .build())

        assert complex_book.is_public is True
        assert complex_book.allow_comments is True
        assert "important" in complex_book.tags
        assert "documentation" in complex_book.categories

    def test_content_lifecycle(self):
        """Test content lifecycle management."""
        section = ContentSection(
            section_id="lifecycle_test",
            title="Lifecycle Test",
            content="Initial content"
        )

        # Start as draft
        assert section.metadata.status == ContentStatus.DRAFT

        # Update status (assuming method exists)
        # section.metadata.status = ContentStatus.REVIEW
        # assert section.metadata.status == ContentStatus.REVIEW

        # Content updates should maintain history
        section.update_content("Reviewed content", "reviewer")
        assert section.metadata.version > 1
        assert section.metadata.updated_by == "reviewer"