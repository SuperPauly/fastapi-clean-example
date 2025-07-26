"""Create book use case."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from src.application.ports.author_repository import AuthorRepositoryPort
from src.application.ports.book_repository import BookRepositoryPort
from src.application.ports.logger import LoggerPort
from src.domain.entities.book import Book
from src.domain.services.library_service import LibraryService
from src.domain.value_objects.book_title import BookTitle


@dataclass
class CreateBookRequest:
    """Request to create a book."""
    title: str
    author_ids: List[UUID]


@dataclass
class CreateBookResponse:
    """Response from creating a book."""
    book: Optional[Book]
    success: bool
    message: str


class CreateBookUseCase:
    """Use case for creating a new book."""
    
    def __init__(
        self, 
        book_repository: BookRepositoryPort,
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort
    ):
        self._book_repository = book_repository
        self._author_repository = author_repository
        self._logger = logger
    
    async def execute(self, request: CreateBookRequest) -> CreateBookResponse:
        """Execute the create book use case."""
        try:
            # Validate input
            book_title = BookTitle(request.title)
            
            # Check if book already exists
            existing_book = await self._book_repository.get_by_title(book_title.value)
            if existing_book:
                self._logger.warning(f"Book already exists: {book_title.value}")
                return CreateBookResponse(
                    book=existing_book,
                    success=False,
                    message=f"Book with title '{book_title.value}' already exists"
                )
            
            # Validate that all authors exist
            for author_id in request.author_ids:
                if not await self._author_repository.exists(author_id):
                    self._logger.warning(f"Author not found: {author_id}")
                    return CreateBookResponse(
                        book=None,
                        success=False,
                        message=f"Author with ID {author_id} not found"
                    )
            
            # Create new book
            book = Book(title=book_title, author_ids=request.author_ids.copy())
            created_book = await self._book_repository.create(book)
            
            # Update authors to include this book
            for author_id in request.author_ids:
                author = await self._author_repository.get_by_id(author_id)
                if author:
                    LibraryService.associate_author_with_book(author, created_book)
                    await self._author_repository.update(author)
            
            self._logger.info(f"Book created successfully: {created_book.id}")
            
            return CreateBookResponse(
                book=created_book,
                success=True,
                message="Book created successfully"
            )
            
        except ValueError as e:
            self._logger.error(f"Invalid book data: {str(e)}")
            return CreateBookResponse(
                book=None,
                success=False,
                message=f"Invalid book data: {str(e)}"
            )
        except Exception as e:
            self._logger.error(f"Failed to create book: {str(e)}")
            return CreateBookResponse(
                book=None,
                success=False,
                message=f"Failed to create book: {str(e)}"
            )

