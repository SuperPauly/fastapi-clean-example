"""Book domain entity."""

from typing import List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from src.domain.value_objects.book_title import BookTitle


class Book(BaseModel):
    """Book domain entity representing a published book."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the book")
    title: BookTitle = Field(..., description="Book's title")
    author_ids: List[UUID] = Field(default_factory=list, description="List of author IDs associated with this book")
    
    model_config = {
        "frozen": False,  # Allow mutations for business operations
        "validate_assignment": True,  # Validate on assignment
        "arbitrary_types_allowed": True,  # Allow BookTitle value object
    }
    
    def __init__(self, title: BookTitle, id: Optional[UUID] = None, author_ids: Optional[List[UUID]] = None, **data):
        """Initialize Book entity."""
        super().__init__(
            id=id or uuid4(),
            title=title,
            author_ids=author_ids or [],
            **data
        )
    
    @field_validator('author_ids')
    @classmethod
    def remove_duplicate_author_ids(cls, v: List[UUID]) -> List[UUID]:
        """Remove duplicate author IDs while preserving order."""
        if not v:
            return []
        seen: Set[UUID] = set()
        return [author_id for author_id in v if not (author_id in seen or seen.add(author_id))]
    
    def add_author(self, author_id: UUID) -> None:
        """Add an author to this book."""
        if author_id not in self.author_ids:
            self.author_ids.append(author_id)
    
    def remove_author(self, author_id: UUID) -> None:
        """Remove an author from this book."""
        if author_id in self.author_ids:
            self.author_ids.remove(author_id)
    
    def has_authors(self) -> bool:
        """Check if book has any authors."""
        return len(self.author_ids) > 0
    
    def update_title(self, new_title: BookTitle) -> None:
        """Update book's title."""
        self.title = new_title
    
    def __eq__(self, other) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Book):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

