# Book Schemas for API
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# This module contains Pydantic schemas for book-related API operations


class ChapterSchema(BaseModel):
    """Schema for book chapter."""

    chapter_id: str = Field(..., description="Chapter ID")
    title: str = Field(..., description="Chapter title")
    description: str = Field(..., description="Chapter description")
    order_index: int = Field(..., description="Order index")
    word_count: int = Field(default=0, description="Word count")
    estimated_read_time_minutes: int = Field(
        default=0, description="Estimated read time"
    )


class PageSchema(BaseModel):
    """Schema for book page."""

    page_id: str = Field(..., description="Page ID")
    chapter_id: str = Field(..., description="Chapter ID")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content")
    order_index: int = Field(..., description="Order index")
    word_count: int = Field(default=0, description="Word count")
    tags: List[str] = Field(default_factory=list, description="Page tags")
    last_modified_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last modified timestamp"
    )


class SectionSchema(BaseModel):
    """Schema for content section."""

    section_id: str = Field(..., description="Section ID")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    content_type: ContentType = Field(..., description="Content type")
    order_index: int = Field(..., description="Order index")


class BookSearchResultSchema(BaseModel):
    """Schema for book search result."""

    content_id: str = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    content_snippet: str = Field(..., description="Content snippet")
    similarity_score: float = Field(..., description="Similarity score")
    content_type: str = Field(..., description="Content type")
    highlighted_content: str = Field(..., description="Highlighted content")


class BookCreateSchema(BaseModel):
    """Schema for creating a new book."""

    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    description: str = Field(..., description="Book description")
    language: str = Field(default="en", description="Book language")
    version: str = Field(default="1.0.0", description="Book version")
    tags: List[str] = Field(default_factory=list, description="Book tags")
    semantic_search_enabled: bool = Field(
        default=True, description="Semantic search enabled"
    )
    collaboration_enabled: bool = Field(
        default=True, description="Collaboration enabled"
    )
    access_control: List[str] = Field(
        default_factory=list, description="Access control"
    )


class BookUpdateSchema(BaseModel):
    """Schema for updating an existing book."""

    title: Optional[str] = Field(default=None, description="Book title")
    author: Optional[str] = Field(default=None, description="Book author")
    description: Optional[str] = Field(default=None, description="Book description")
    language: Optional[str] = Field(default=None, description="Book language")
    version: Optional[str] = Field(default=None, description="Book version")
    tags: Optional[List[str]] = Field(default=None, description="Book tags")
    semantic_search_enabled: Optional[bool] = Field(
        default=None, description="Semantic search enabled"
    )
    collaboration_enabled: Optional[bool] = Field(
        default=None, description="Collaboration enabled"
    )
    access_control: Optional[List[str]] = Field(
        default=None, description="Access control"
    )
    active: Optional[bool] = Field(default=None, description="Book active status")


class BookResponseSchema(BaseModel):
    """Schema for book response data."""

    id: str = Field(..., description="Book ID")
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    description: str = Field(..., description="Book description")
    language: str = Field(..., description="Book language")
    version: str = Field(..., description="Book version")
    active: bool = Field(default=True, description="Book active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    chapters_count: int = Field(default=0, description="Number of chapters")
    pages_count: int = Field(default=0, description="Number of pages")


class BookListResponseSchema(BaseResponseSchema):
    """Schema for book list response."""

    books: List[BookResponseSchema] = Field(..., description="List of books")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")


class ChapterCreateSchema(BaseModel):
    """Schema for creating a new chapter."""

    title: str = Field(..., description="Chapter title")
    description: str = Field(..., description="Chapter description")
    order_index: int = Field(default=0, description="Order index")


class ChapterUpdateSchema(BaseModel):
    """Schema for updating a chapter."""

    title: Optional[str] = Field(default=None, description="Chapter title")
    description: Optional[str] = Field(default=None, description="Chapter description")
    order_index: Optional[int] = Field(default=None, description="Order index")


class PageCreateSchema(BaseModel):
    """Schema for creating a new page."""

    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content")
    order_index: int = Field(default=0, description="Order index")
    tags: List[str] = Field(default_factory=list, description="Page tags")


class PageUpdateSchema(BaseModel):
    """Schema for updating a page."""

    title: Optional[str] = Field(default=None, description="Page title")
    content: Optional[str] = Field(default=None, description="Page content")
    order_index: Optional[int] = Field(default=None, description="Order index")
    tags: Optional[List[str]] = Field(default=None, description="Page tags")


class SectionCreateSchema(BaseModel):
    """Schema for creating a new section."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    content_type: ContentType = Field(
        default=ContentType.TEXT, description="Content type"
    )
    order_index: int = Field(default=0, description="Order index")


class SectionUpdateSchema(BaseModel):
    """Schema for updating a section."""

    title: Optional[str] = Field(default=None, description="Section title")
    content: Optional[str] = Field(default=None, description="Section content")
    content_type: Optional[ContentType] = Field(
        default=None, description="Content type"
    )
    order_index: Optional[int] = Field(default=None, description="Order index")
