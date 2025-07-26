"""Create author use case."""

from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from src.application.ports.author_repository import AuthorRepositoryPort
from src.application.ports.logger import LoggerPort
from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName


class CreateAuthorRequest(BaseModel):
    """Request to create an author."""
    name: str = Field(..., min_length=1, max_length=100, description="Author's name")


class CreateAuthorResponse(BaseModel):
    """Response from creating an author."""
    author: Optional[Author] = Field(None, description="Created author entity")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Result message")
    
    model_config = {
        "arbitrary_types_allowed": True,  # Allow Author entity
    }


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
            # Validate input and create value object
            author_name = AuthorName(value=request.name)
            
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
            
        except ValidationError as e:
            error_msg = f"Invalid author data: {e}"
            self._logger.error(error_msg)
            return CreateAuthorResponse(
                author=None,
                success=False,
                message=error_msg
            )
        except ValueError as e:
            error_msg = f"Invalid author data: {str(e)}"
            self._logger.error(error_msg)
            return CreateAuthorResponse(
                author=None,
                success=False,
                message=error_msg
            )
        except Exception as e:
            error_msg = f"Failed to create author: {str(e)}"
            self._logger.error(error_msg)
            return CreateAuthorResponse(
                author=None,
                success=False,
                message=error_msg
            )

