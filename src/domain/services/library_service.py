"""Domain service for library operations."""

from typing import List
from uuid import UUID

from src.domain.entities.author import Author
from src.domain.entities.book import Book


class LibraryService:
    """Domain service for complex library operations."""
    
    @staticmethod
    def associate_author_with_book(author: Author, book: Book) -> None:
        """Associate an author with a book (bidirectional)."""
        author.add_book(book.id)
        book.add_author(author.id)
    
    @staticmethod
    def dissociate_author_from_book(author: Author, book: Book) -> None:
        """Dissociate an author from a book (bidirectional)."""
        author.remove_book(book.id)
        book.remove_author(author.id)
    
    @staticmethod
    def can_delete_author(author: Author) -> bool:
        """Check if an author can be safely deleted."""
        return not author.has_books()
    
    @staticmethod
    def can_delete_book(book: Book) -> bool:
        """Check if a book can be safely deleted."""
        # Books can always be deleted, but we might want to add business rules later
        return True
    
    @staticmethod
    def find_authors_without_books(authors: List[Author]) -> List[Author]:
        """Find authors who don't have any books."""
        return [author for author in authors if not author.has_books()]
    
    @staticmethod
    def find_books_without_authors(books: List[Book]) -> List[Book]:
        """Find books that don't have any authors."""
        return [book for book in books if not book.has_authors()]
    
    @staticmethod
    def get_shared_authors(book1: Book, book2: Book) -> List[UUID]:
        """Get authors that are shared between two books."""
        return list(set(book1.author_ids) & set(book2.author_ids))
    
    @staticmethod
    def get_shared_books(author1: Author, author2: Author) -> List[UUID]:
        """Get books that are shared between two authors."""
        return list(set(author1.book_ids) & set(author2.book_ids))

