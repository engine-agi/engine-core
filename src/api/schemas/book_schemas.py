# Book Schemas for API
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import BookLanguage, ContentType, EmbeddingModel, SearchType

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


class BookSearchResultSchema(BaseModel):
    """Schema for book search result."""

    page_id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    content_snippet: str = Field(..., description="Content snippet")
    chapter_id: str = Field(..., description="Chapter ID")
    chapter_title: str = Field(..., description="Chapter title")
    similarity_score: float = Field(..., description="Similarity score")
    search_type: SearchType = Field(..., description="Search type")
    highlighted_content: str = Field(..., description="Highlighted content")


class BookEmbeddingSchema(BaseModel):
    """Schema for book embedding."""

    content_id: str = Field(..., description="Content ID")
    content_type: str = Field(..., description="Content type")
    embedding_vector: List[float] = Field(..., description="Embedding vector")
    embedding_model: EmbeddingModel = Field(..., description="Embedding model")
    dimension: int = Field(..., description="Vector dimension")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class BookCreateSchema(BaseModel):
    """Schema for creating a new book."""

    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    description: str = Field(..., description="Book description")
    language: BookLanguage = Field(..., description="Book language")
    version: str = Field(..., description="Book version")
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
    language: Optional[BookLanguage] = Field(default=None, description="Book language")
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
    language: BookLanguage = Field(..., description="Book language")
    version: str = Field(..., description="Book version")
    active: bool = Field(default=True, description="Book active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
