"""Book repository port (interface)."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.book import Book


class BookRepositoryPort(ABC):
    """Port (interface) for book repository operations."""
    
    @abstractmethod
    async def create(self, book: Book) -> Book:
        """Create a new book."""
        pass
    
    @abstractmethod
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Get book by ID."""
        pass
    
    @abstractmethod
    async def get_by_title(self, title: str) -> Optional[Book]:
        """Get book by title."""
        pass
    
    @abstractmethod
    async def list(
        self, 
        title_filter: Optional[str] = None,
        author_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Book]:
        """List books with optional filtering and pagination."""
        pass
    
    @abstractmethod
    async def update(self, book: Book) -> Book:
        """Update an existing book."""
        pass
    
    @abstractmethod
    async def delete(self, book_id: UUID) -> None:
        """Delete a book."""
        pass
    
    @abstractmethod
    async def exists(self, book_id: UUID) -> bool:
        """Check if book exists."""
        pass

