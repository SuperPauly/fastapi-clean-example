"""Create author use case."""

from dataclasses import dataclass
from typing import Optional

from src.application.ports.author_repository import AuthorRepositoryPort
from src.application.ports.logger import LoggerPort
from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName


@dataclass
class CreateAuthorRequest:
    """Request to create an author."""
    name: str


@dataclass
class CreateAuthorResponse:
    """Response from creating an author."""
    author: Author
    success: bool
    message: str


class CreateAuthorUseCase:
    """Use case for creating a new author."""
    
    def __init__(
        self, 
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort
    ):
        self._author_repository = author_repository
        self._logger = logger
    
    async def execute(self, request: CreateAuthorRequest) -> CreateAuthorResponse:
        """Execute the create author use case."""
        try:
            # Validate input
            author_name = AuthorName(request.name)
            
            # Check if author already exists
            existing_author = await self._author_repository.get_by_name(author_name.value)
            if existing_author:
                self._logger.warning(f"Author already exists: {author_name.value}")
                return CreateAuthorResponse(
                    author=existing_author,
                    success=False,
                    message=f"Author with name '{author_name.value}' already exists"
                )
            
            # Create new author
            author = Author(name=author_name)
            created_author = await self._author_repository.create(author)
            
            self._logger.info(f"Author created successfully: {created_author.id}")
            
            return CreateAuthorResponse(
                author=created_author,
                success=True,
                message="Author created successfully"
            )
            
        except ValueError as e:
            self._logger.error(f"Invalid author data: {str(e)}")
            return CreateAuthorResponse(
                author=None,
                success=False,
                message=f"Invalid author data: {str(e)}"
            )
        except Exception as e:
            self._logger.error(f"Failed to create author: {str(e)}")
            return CreateAuthorResponse(
                author=None,
                success=False,
                message=f"Failed to create author: {str(e)}"
            )

