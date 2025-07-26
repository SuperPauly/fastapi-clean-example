"""Book domain entity."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4

from src.domain.value_objects.book_title import BookTitle


@dataclass
class Book:
    """Book domain entity representing a published book."""
    
    id: Optional[UUID]
    title: BookTitle
    author_ids: List[UUID]
    
    def __init__(self, title: BookTitle, id: Optional[UUID] = None, author_ids: Optional[List[UUID]] = None):
        """Initialize Book entity."""
        self.id = id or uuid4()
        self.title = title
        self.author_ids = author_ids or []
    
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

