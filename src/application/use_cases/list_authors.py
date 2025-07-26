"""List authors use case."""

from dataclasses import dataclass
from typing import List, Optional

from src.application.ports.author_repository import AuthorRepositoryPort
from src.application.ports.logger import LoggerPort
from src.domain.entities.author import Author


@dataclass
class ListAuthorsRequest:
    """Request to list authors."""
    name_filter: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass
class ListAuthorsResponse:
    """Response from listing authors."""
    authors: List[Author]
    success: bool
    message: str
    total_count: int


class ListAuthorsUseCase:
    """Use case for listing authors with optional filtering."""
    
    def __init__(
        self, 
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort
    ):
        self._author_repository = author_repository
        self._logger = logger
    
    async def execute(self, request: ListAuthorsRequest) -> ListAuthorsResponse:
        """Execute the list authors use case."""
        try:
            authors = await self._author_repository.list(
                name_filter=request.name_filter,
                limit=request.limit,
                offset=request.offset
            )
            
            self._logger.debug(f"Retrieved {len(authors)} authors")
            
            return ListAuthorsResponse(
                authors=authors,
                success=True,
                message=f"Retrieved {len(authors)} authors",
                total_count=len(authors)
            )
            
        except Exception as e:
            self._logger.error(f"Failed to list authors: {str(e)}")
            return ListAuthorsResponse(
                authors=[],
                success=False,
                message=f"Failed to list authors: {str(e)}",
                total_count=0
            )

