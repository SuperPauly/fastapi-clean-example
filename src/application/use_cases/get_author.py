"""Get author use case."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.ports.author_repository import AuthorRepositoryPort
from src.application.ports.logger import LoggerPort
from src.domain.entities.author import Author


@dataclass
class GetAuthorRequest:
    """Request to get an author."""
    author_id: UUID


@dataclass
class GetAuthorResponse:
    """Response from getting an author."""
    author: Optional[Author]
    success: bool
    message: str


class GetAuthorUseCase:
    """Use case for getting an author by ID."""
    
    def __init__(
        self, 
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort
    ):
        self._author_repository = author_repository
        self._logger = logger
    
    async def execute(self, request: GetAuthorRequest) -> GetAuthorResponse:
        """Execute the get author use case."""
        try:
            author = await self._author_repository.get_by_id(request.author_id)
            
            if not author:
                self._logger.info(f"Author not found: {request.author_id}")
                return GetAuthorResponse(
                    author=None,
                    success=False,
                    message=f"Author with ID {request.author_id} not found"
                )
            
            self._logger.debug(f"Author retrieved: {author.id}")
            
            return GetAuthorResponse(
                author=author,
                success=True,
                message="Author retrieved successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to get author: {str(e)}")
            return GetAuthorResponse(
                author=None,
                success=False,
                message=f"Failed to get author: {str(e)}"
            )

