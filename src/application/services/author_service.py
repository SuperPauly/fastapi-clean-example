"""Application service for author operations."""

from typing import List, Optional
from uuid import UUID

from src.application.ports.author_repository import AuthorRepositoryPort
from src.application.ports.logger import LoggerPort
from src.application.ports.task_queue import TaskQueuePort
from src.application.use_cases.create_author import CreateAuthorUseCase, CreateAuthorRequest
from src.application.use_cases.get_author import GetAuthorUseCase, GetAuthorRequest
from src.application.use_cases.list_authors import ListAuthorsUseCase, ListAuthorsRequest
from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName


class AuthorApplicationService:
    """Application service coordinating author operations."""
    
    def __init__(
        self,
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort,
        task_queue: TaskQueuePort
    ):
        self._author_repository = author_repository
        self._logger = logger
        self._task_queue = task_queue
        
        # Initialize use cases
        self._create_author_use_case = CreateAuthorUseCase(author_repository, logger)
        self._get_author_use_case = GetAuthorUseCase(author_repository, logger)
        self._list_authors_use_case = ListAuthorsUseCase(author_repository, logger)
    
    async def create_author(self, name: str) -> Author:
        """Create a new author."""
        request = CreateAuthorRequest(name=name)
        response = await self._create_author_use_case.execute(request)
        
        if not response.success:
            raise ValueError(response.message)
        
        # Enqueue notification task
        try:
            from src.infrastructure.tasks.handlers.notification_tasks import send_author_created_notification
            await self._task_queue.enqueue(
                send_author_created_notification,
                str(response.author.id),
                response.author.name.value
            )
        except Exception as e:
            self._logger.warning(f"Failed to enqueue notification task: {e}")
        
        return response.author
    
    async def get_author(self, author_id: UUID) -> Optional[Author]:
        """Get author by ID."""
        request = GetAuthorRequest(author_id=author_id)
        response = await self._get_author_use_case.execute(request)
        
        if not response.success:
            self._logger.info(response.message)
            return None
        
        return response.author
    
    async def list_authors(
        self,
        name_filter: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Author]:
        """List authors with optional filtering."""
        request = ListAuthorsRequest(
            name_filter=name_filter,
            limit=limit,
            offset=offset
        )
        response = await self._list_authors_use_case.execute(request)
        
        if not response.success:
            self._logger.error(response.message)
            return []
        
        return response.authors
    
    async def update_author(self, author_id: UUID, name: str) -> Author:
        """Update an existing author."""
        author = await self._author_repository.get_by_id(author_id)
        if not author:
            raise ValueError(f"Author with ID {author_id} not found")
        
        # Update author name
        new_name = AuthorName(name)
        author.update_name(new_name)
        
        updated_author = await self._author_repository.update(author)
        self._logger.info(f"Author updated: {updated_author.id}")
        
        return updated_author
    
    async def delete_author(self, author_id: UUID) -> None:
        """Delete an author."""
        author = await self._author_repository.get_by_id(author_id)
        if not author:
            raise ValueError(f"Author with ID {author_id} not found")
        
        # Check if author has books
        if author.has_books():
            raise ValueError("Cannot delete author with associated books")
        
        await self._author_repository.delete(author_id)
        self._logger.info(f"Author deleted: {author_id}")

