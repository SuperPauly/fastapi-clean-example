"""Pydantic schemas for Book API."""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class BookCreateRequest(BaseModel):
    """Request schema for creating a book."""
    title: str = Field(..., min_length=1, max_length=200, description="Book title")
    author_ids: List[UUID] = Field(..., min_items=1, description="List of author IDs")


class BookUpdateRequest(BaseModel):
    """Request schema for updating a book."""
    title: str = Field(..., min_length=1, max_length=200, description="Book title")
    author_ids: List[UUID] = Field(..., min_items=1, description="List of author IDs")


class BookResponse(BaseModel):
    """Response schema for book data."""
    id: UUID = Field(..., description="Book ID")
    title: str = Field(..., description="Book title")
    author_ids: List[UUID] = Field(default_factory=list, description="List of author IDs")
    
    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    """Response schema for book list."""
    books: List[BookResponse] = Field(..., description="List of books")
    total_count: int = Field(..., description="Total number of books")


class BookListRequest(BaseModel):
    """Request schema for listing books."""
    title_filter: Optional[str] = Field(None, description="Filter by book title")
    author_id: Optional[UUID] = Field(None, description="Filter by author ID")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")

