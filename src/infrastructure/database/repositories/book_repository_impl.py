"""Tortoise ORM implementation of Book repository."""

from typing import List, Optional
from uuid import UUID

from src.application.ports.book_repository import BookRepositoryPort
from src.domain.entities.book import Book
from src.domain.value_objects.book_title import BookTitle
from src.infrastructure.database.models.book_model import BookModel


class TortoiseBookRepository(BookRepositoryPort):
    """Tortoise ORM implementation of the book repository port."""
    
    async def create(self, book: Book) -> Book:
        """Create a new book."""
        book_model = BookModel(
            id=book.id,
            title=book.title.value
        )
        await book_model.save()
        
        # Convert back to domain entity
        return self._to_domain_entity(book_model)
    
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Get book by ID."""
        try:
            book_model = await BookModel.get(id=book_id).prefetch_related("authors")
            return self._to_domain_entity(book_model)
        except Exception:
            return None
    
    async def get_by_title(self, title: str) -> Optional[Book]:
        """Get book by title."""
        try:
            book_model = await BookModel.get(title=title).prefetch_related("authors")
            return self._to_domain_entity(book_model)
        except Exception:
            return None
    
    async def list(
        self, 
        title_filter: Optional[str] = None,
        author_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Book]:
        """List books with optional filtering and pagination."""
        query = BookModel.all().prefetch_related("authors")
        
        if title_filter:
            query = query.filter(title__icontains=title_filter)
        
        if author_id:
            query = query.filter(authors__id=author_id)
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        book_models = await query
        return [self._to_domain_entity(model) for model in book_models]
    
    async def update(self, book: Book) -> Book:
        """Update an existing book."""
        book_model = await BookModel.get(id=book.id)
        book_model.title = book.title.value
        await book_model.save()
        
        return self._to_domain_entity(book_model)
    
    async def delete(self, book_id: UUID) -> None:
        """Delete a book."""
        book_model = await BookModel.get(id=book_id)
        await book_model.delete()
    
    async def exists(self, book_id: UUID) -> bool:
        """Check if book exists."""
        return await BookModel.exists(id=book_id)
    
    def _to_domain_entity(self, book_model: BookModel) -> Book:
        """Convert Tortoise model to domain entity."""
        author_ids = []
        if hasattr(book_model, 'authors') and book_model.authors:
            author_ids = [author.id for author in book_model.authors]
        
        return Book(
            id=book_model.id,
            title=BookTitle(book_model.title),
            author_ids=author_ids
        )

