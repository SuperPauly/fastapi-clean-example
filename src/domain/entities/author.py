"""Author domain entity."""

from typing import List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from src.domain.value_objects.author_name import AuthorName


class Author(BaseModel):
    """Author domain entity representing a book author."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the author")
    name: AuthorName = Field(..., description="Author's name")
    book_ids: List[UUID] = Field(default_factory=list, description="List of book IDs associated with this author")
    
    model_config = {
        "frozen": False,  # Allow mutations for business operations
        "validate_assignment": True,  # Validate on assignment
        "arbitrary_types_allowed": True,  # Allow AuthorName value object
    }
    
    def __init__(self, name: AuthorName, id: Optional[UUID] = None, book_ids: Optional[List[UUID]] = None, **data):
        """Initialize Author entity."""
        super().__init__(
            id=id or uuid4(),
            name=name,
            book_ids=book_ids or [],
            **data
        )
    
    @field_validator('book_ids')
    @classmethod
    def remove_duplicate_book_ids(cls, v: List[UUID]) -> List[UUID]:
        """Remove duplicate book IDs while preserving order."""
        if not v:
            return []
        seen: Set[UUID] = set()
        return [book_id for book_id in v if not (book_id in seen or seen.add(book_id))]
    
    def add_book(self, book_id: UUID) -> None:
        """Add a book to this author."""
        if book_id not in self.book_ids:
            self.book_ids.append(book_id)
    
    def remove_book(self, book_id: UUID) -> None:
        """Remove a book from this author."""
        if book_id in self.book_ids:
            self.book_ids.remove(book_id)
    
    def has_books(self) -> bool:
        """Check if author has any books."""
        return len(self.book_ids) > 0
    
    def update_name(self, new_name: AuthorName) -> None:
        """Update author's name."""
        self.name = new_name
    
    def __eq__(self, other) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Author):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

