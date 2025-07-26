"""Tortoise ORM implementation of Author repository."""

from typing import List, Optional
from uuid import UUID

from src.application.ports.author_repository import AuthorRepositoryPort
from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName
from src.infrastructure.database.models.author_model import AuthorModel


class TortoiseAuthorRepository(AuthorRepositoryPort):
    """Tortoise ORM implementation of the author repository port."""
    
    async def create(self, author: Author) -> Author:
        """Create a new author."""
        author_model = AuthorModel(
            id=author.id,
            name=author.name.value
        )
        await author_model.save()
        
        # Convert back to domain entity
        return self._to_domain_entity(author_model)
    
    async def get_by_id(self, author_id: UUID) -> Optional[Author]:
        """Get author by ID."""
        try:
            author_model = await AuthorModel.get(id=author_id).prefetch_related("books")
            return self._to_domain_entity(author_model)
        except Exception:
            return None
    
    async def get_by_name(self, name: str) -> Optional[Author]:
        """Get author by name."""
        try:
            author_model = await AuthorModel.get(name=name).prefetch_related("books")
            return self._to_domain_entity(author_model)
        except Exception:
            return None
    
    async def list(
        self, 
        name_filter: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Author]:
        """List authors with optional filtering and pagination."""
        query = AuthorModel.all().prefetch_related("books")
        
        if name_filter:
            query = query.filter(name__icontains=name_filter)
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        author_models = await query
        return [self._to_domain_entity(model) for model in author_models]
    
    async def update(self, author: Author) -> Author:
        """Update an existing author."""
        author_model = await AuthorModel.get(id=author.id)
        author_model.name = author.name.value
        await author_model.save()
        
        return self._to_domain_entity(author_model)
    
    async def delete(self, author_id: UUID) -> None:
        """Delete an author."""
        author_model = await AuthorModel.get(id=author_id)
        await author_model.delete()
    
    async def exists(self, author_id: UUID) -> bool:
        """Check if author exists."""
        return await AuthorModel.exists(id=author_id)
    
    def _to_domain_entity(self, author_model: AuthorModel) -> Author:
        """Convert Tortoise model to domain entity."""
        book_ids = []
        if hasattr(author_model, 'books') and author_model.books:
            book_ids = [book.id for book in author_model.books]
        
        return Author(
            id=author_model.id,
            name=AuthorName(author_model.name),
            book_ids=book_ids
        )

