"""Author repository port (interface)."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.author import Author


class AuthorRepositoryPort(ABC):
    """Port (interface) for author repository operations."""
    
    @abstractmethod
    async def create(self, author: Author) -> Author:
        """Create a new author."""
        pass
    
    @abstractmethod
    async def get_by_id(self, author_id: UUID) -> Optional[Author]:
        """Get author by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Author]:
        """Get author by name."""
        pass
    
    @abstractmethod
    async def list(
        self, 
        name_filter: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Author]:
        """List authors with optional filtering and pagination."""
        pass
    
    @abstractmethod
    async def update(self, author: Author) -> Author:
        """Update an existing author."""
        pass
    
    @abstractmethod
    async def delete(self, author_id: UUID) -> None:
        """Delete an author."""
        pass
    
    @abstractmethod
    async def exists(self, author_id: UUID) -> bool:
        """Check if author exists."""
        pass

