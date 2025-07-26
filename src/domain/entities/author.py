"""Author domain entity."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4

from src.domain.value_objects.author_name import AuthorName


@dataclass
class Author:
    """Author domain entity representing a book author."""
    
    id: Optional[UUID]
    name: AuthorName
    book_ids: List[UUID]
    
    def __init__(self, name: AuthorName, id: Optional[UUID] = None, book_ids: Optional[List[UUID]] = None):
        """Initialize Author entity."""
        self.id = id or uuid4()
        self.name = name
        self.book_ids = book_ids or []
    
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

