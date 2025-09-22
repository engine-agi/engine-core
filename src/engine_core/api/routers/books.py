"""
Books API Router - Engine Framework Book Management.

This router provides comprehensive book management endpoints including CRUD operations,
hierarchical content management, and semantic search capabilities.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from datetime import datetime

from ..schemas.book_schemas import (
    BookCreateSchema,
    BookUpdateSchema,
    BookResponseSchema,
    BookListResponseSchema,
    ChapterCreateSchema,
    ChapterUpdateSchema,
    PageCreateSchema,
    PageUpdateSchema,
    SectionCreateSchema,
    SectionUpdateSchema,
    BookSearchResultSchema,
    ChapterSchema,
    PageSchema,
    SectionSchema
)
from ..schemas.base_schemas import BaseResponseSchema, ErrorResponseSchema
from ...core.book import BookBuilder, Book, SemanticSearchEngine

# Create router instance
router = APIRouter(
    prefix="/books",
    tags=["books"],
    responses={
        404: {"description": "Book, chapter, page, or section not found"},
        400: {"description": "Invalid request data"},
        500: {"description": "Internal server error"},
    }
)

# In-memory storage for demo purposes (would be replaced with proper persistence)
_books_storage: Dict[str, Book] = {}
_search_engines: Dict[str, SemanticSearchEngine] = {}


def get_book_or_404(book_id: str) -> Book:
    """Get book by ID or raise 404."""
    if book_id not in _books_storage:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return _books_storage[book_id]


def get_search_engine(book_id: str) -> SemanticSearchEngine:
    """Get or create search engine for book."""
    if book_id not in _search_engines:
        _search_engines[book_id] = SemanticSearchEngine(enable_embeddings=False)
    return _search_engines[book_id]


@router.post("/", response_model=BookResponseSchema)
async def create_book(book_data: BookCreateSchema = Body(...)):
    """Create a new book."""
    try:
        # Create book using BookBuilder
        book = (BookBuilder()
            .with_id(f"book_{len(_books_storage) + 1}")
            .with_title(book_data.title)
            .with_author(book_data.author)
            .with_description(book_data.description)
            .with_search_enabled(book_data.semantic_search_enabled)
            .build())

        # Store book
        _books_storage[book.book_id] = book

        # Initialize search engine if semantic search is enabled
        if book_data.semantic_search_enabled:
            _search_engines[book.book_id] = SemanticSearchEngine(enable_embeddings=False)

        return BookResponseSchema(
            id=book.book_id,
            title=book.title,
            author=book.author or "",
            description=book.description,
            language=book_data.language,
            version=book_data.version,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chapters_count=0,
            pages_count=0
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create book: {str(e)}")


@router.get("/", response_model=BookListResponseSchema)
async def list_books(
    skip: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of books to return")
):
    """List all books."""
    try:
        books = list(_books_storage.values())[skip:skip + limit]

        book_responses = []
        for book in books:
            book_responses.append(BookResponseSchema(
                id=book.book_id,
                title=book.title,
                author=book.author or "",
                description=book.description,
                language="en",  # Default
                version="1.0.0",  # Default
                active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                chapters_count=len(book.chapters),
                pages_count=sum(len(chapter.pages) for chapter in book.chapters)
            ))

        return BookListResponseSchema(
            success=True,
            message="Books retrieved successfully",
            timestamp=datetime.utcnow(),
            books=book_responses,
            pagination={
                "skip": skip,
                "limit": limit,
                "total": len(_books_storage)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list books: {str(e)}")


@router.get("/{book_id}", response_model=BookResponseSchema)
async def get_book(book_id: str = Path(..., description="Book ID")):
    """Get a specific book by ID."""
    try:
        book = get_book_or_404(book_id)

        return BookResponseSchema(
            id=book.book_id,
            title=book.title,
            author=book.author or "",
            description=book.description,
            language="en",
            version="1.0.0",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chapters_count=len(book.chapters),
            pages_count=sum(len(chapter.pages) for chapter in book.chapters)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get book: {str(e)}")


@router.put("/{book_id}", response_model=BookResponseSchema)
async def update_book(
    book_id: str = Path(..., description="Book ID"),
    book_data: BookUpdateSchema = Body(...)
):
    """Update a book."""
    try:
        book = get_book_or_404(book_id)

        # Update fields if provided
        if book_data.title is not None:
            book.title = book_data.title
        if book_data.author is not None:
            book.author = book_data.author
        if book_data.description is not None:
            book.description = book_data.description

        return BookResponseSchema(
            id=book.book_id,
            title=book.title,
            author=book.author or "",
            description=book.description,
            language="en",
            version="1.0.0",
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            chapters_count=len(book.chapters),
            pages_count=sum(len(chapter.pages) for chapter in book.chapters)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update book: {str(e)}")


@router.delete("/{book_id}", response_model=BaseResponseSchema)
async def delete_book(book_id: str = Path(..., description="Book ID")):
    """Delete a book."""
    try:
        book = get_book_or_404(book_id)

        # Remove from storage
        del _books_storage[book_id]
        if book_id in _search_engines:
            del _search_engines[book_id]

        return BaseResponseSchema(
            success=True,
            message=f"Book {book_id} deleted successfully",
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete book: {str(e)}")


@router.post("/{book_id}/chapters", response_model=ChapterSchema)
async def create_chapter(
    book_id: str = Path(..., description="Book ID"),
    chapter_data: ChapterCreateSchema = Body(...)
):
    """Create a new chapter in a book."""
    try:
        book = get_book_or_404(book_id)

        chapter = book.add_chapter(chapter_data.title, chapter_data.description)

        return ChapterSchema(
            chapter_id=chapter.chapter_id,
            title=chapter.title,
            description=chapter.description,
            order_index=chapter_data.order_index,
            word_count=0,  # Would be calculated
            estimated_read_time_minutes=0  # Would be calculated
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chapter: {str(e)}")


@router.post("/{book_id}/chapters/{chapter_id}/pages", response_model=PageSchema)
async def create_page(
    book_id: str = Path(..., description="Book ID"),
    chapter_id: str = Path(..., description="Chapter ID"),
    page_data: PageCreateSchema = Body(...)
):
    """Create a new page in a chapter."""
    try:
        book = get_book_or_404(book_id)
        chapter = book.get_chapter(chapter_id)

        if not chapter:
            raise HTTPException(status_code=404, detail=f"Chapter {chapter_id} not found")

        page = chapter.add_page(page_data.title, page_data.content)

        # Index for search if enabled
        if book.enable_search:
            search_engine = get_search_engine(book_id)
            search_engine.index_content(
                content_id=page.page_id,
                content_type="page",
                title=page.title,
                content=page.description,
                metadata=page.metadata
            )

        return PageSchema(
            page_id=page.page_id,
            chapter_id=chapter_id,
            title=page.title,
            content=page.description,
            order_index=page_data.order_index,
            word_count=len(page_data.content.split()),
            tags=page_data.tags,
            last_modified_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create page: {str(e)}")


@router.get("/{book_id}/search", response_model=List[BookSearchResultSchema])
async def search_book(
    book_id: str = Path(..., description="Book ID"),
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """Search content in a book."""
    try:
        book = get_book_or_404(book_id)

        if not book.enable_search:
            raise HTTPException(status_code=400, detail="Search not enabled for this book")

        search_engine = get_search_engine(book_id)

        # Perform search
        from ...core.book.book_builder import SearchQuery
        search_query = SearchQuery(query_text=query, semantic_search=False, max_results=limit)
        results = search_engine.search(search_query, book)

        # Convert to response schema
        response_results = []
        for result in results[:limit]:
            response_results.append(BookSearchResultSchema(
                content_id=result.content_id,
                title=result.title,
                content_snippet=result.content_snippet[:200] + "..." if len(result.content_snippet) > 200 else result.content_snippet,
                similarity_score=result.relevance_score,
                content_type=result.content_type,
                highlighted_content=result.content_snippet
            ))

        return response_results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/health")
async def books_health():
    """Health check endpoint for books service."""
    return {
        "service": "books",
        "status": "healthy",
        "books_count": len(_books_storage),
        "timestamp": datetime.utcnow().isoformat()
    }