"""Pydantic schemas for Author API."""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AuthorCreateRequest(BaseModel):
    """Request schema for creating an author."""
    name: str = Field(..., min_length=1, max_length=100, description="Author name")


class AuthorUpdateRequest(BaseModel):
    """Request schema for updating an author."""
    name: str = Field(..., min_length=1, max_length=100, description="Author name")


class AuthorResponse(BaseModel):
    """Response schema for author data."""
    id: UUID = Field(..., description="Author ID")
    name: str = Field(..., description="Author name")
    book_ids: List[UUID] = Field(default_factory=list, description="List of book IDs")
    
    class Config:
        from_attributes = True


class AuthorListResponse(BaseModel):
    """Response schema for author list."""
    authors: List[AuthorResponse] = Field(..., description="List of authors")
    total_count: int = Field(..., description="Total number of authors")


class AuthorListRequest(BaseModel):
    """Request schema for listing authors."""
    name_filter: Optional[str] = Field(None, description="Filter by author name")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")

