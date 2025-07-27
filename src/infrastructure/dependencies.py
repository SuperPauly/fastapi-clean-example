"""Dependency injection configuration for FastAPI.

This module demonstrates how to implement dependency injection while maintaining
hexagonal architecture principles. It acts as the composition root, wiring together
all the dependencies and ensuring proper separation of concerns.
"""

from functools import lru_cache
from typing import NamedTuple

# Application layer imports
from src.application.use_cases.create_author import CreateAuthorUseCase
from src.application.use_cases.get_author import GetAuthorUseCase
from src.application.use_cases.list_authors import ListAuthorsUseCase
from src.application.use_cases.create_book import CreateBookUseCase

# Infrastructure layer imports
from src.infrastructure.database.repositories.author_repository import AuthorRepository
from src.infrastructure.database.repositories.book_repository import BookRepository
from src.infrastructure.logging.logger_adapter import LoguruLoggerAdapter
from src.infrastructure.tasks.taskiq_adapter import TaskiqTaskQueueAdapter
from src.infrastructure.rate_limiting.pyrate_adapter import PyrateLimiterAdapter

# Logger configuration imports
from src.infrastructure.config.logger_config_adapter import DynaconfLoggerConfigAdapter
from src.infrastructure.logging.loguru_config_adapter import LoguruConfigAdapter
from src.application.ports.logger_configuration import LoggerConfigurationPort, LoggerApplicationPort


class AuthorUseCases(NamedTuple):
    """Container for author-related use cases.
    
    This container groups related use cases together, making dependency
    injection cleaner and more organized. It follows the principle of
    keeping related functionality together while maintaining loose coupling.
    """
    create_author: CreateAuthorUseCase
    get_author: GetAuthorUseCase
    list_authors: ListAuthorsUseCase


class BookUseCases(NamedTuple):
    """Container for book-related use cases."""
    create_book: CreateBookUseCase


@lru_cache()
def get_author_repository() -> AuthorRepository:
    """Get author repository instance.
    
    This function demonstrates the adapter pattern - we return a concrete
    implementation that satisfies the AuthorRepositoryPort interface.
    The @lru_cache decorator ensures we use a singleton pattern.
    
    Returns:
        AuthorRepository: Concrete implementation of AuthorRepositoryPort
    """
    return AuthorRepository()


@lru_cache()
def get_book_repository() -> BookRepository:
    """Get book repository instance.
    
    Returns:
        BookRepository: Concrete implementation of BookRepositoryPort
    """
    return BookRepository()


@lru_cache()
def get_logger() -> LoguruLoggerAdapter:
    """Get logger instance.
    
    This function demonstrates how to inject logging adapters while
    keeping the application layer independent of specific logging frameworks.
    
    Returns:
        LoguruLoggerAdapter: Concrete implementation of LoggerPort
    """
    return LoguruLoggerAdapter()


@lru_cache()
def get_task_queue() -> TaskiqTaskQueueAdapter:
    """Get task queue instance.
    
    This function shows how to inject task queue adapters, allowing
    the application layer to remain independent of specific task queue
    implementations (Taskiq, Celery, etc.).
    
    Returns:
        TaskiqTaskQueueAdapter: Concrete implementation of TaskQueuePort
    """
    return TaskiqTaskQueueAdapter()


@lru_cache()
def get_rate_limiter() -> PyrateLimiterAdapter:
    """Get rate limiter instance.
    
    This function demonstrates how to inject rate limiting adapters while
    keeping the application layer independent of specific rate limiting
    implementations (PyrateLimiter, Redis-based, etc.).
    
    Returns:
        PyrateLimiterAdapter: Concrete implementation of RateLimiter port
    """
    # TODO: Get Redis URL from configuration
    return PyrateLimiterAdapter()


@lru_cache()
def get_author_use_cases() -> AuthorUseCases:
    """Get author use cases with all dependencies injected.
    
    This function demonstrates the composition root pattern - it's responsible
    for wiring together all the dependencies needed by the use cases. This
    keeps the dependency injection logic centralized and makes testing easier.
    
    The hexagonal architecture flow:
    1. Infrastructure adapters are created (repositories, logger, task queue)
    2. Use cases are instantiated with their required ports
    3. The container is returned for use by controllers
    
    Returns:
        AuthorUseCases: Container with all author-related use cases
    """
    
    # Get infrastructure adapters (implementations of ports)
    author_repository = get_author_repository()
    logger = get_logger()
    task_queue = get_task_queue()
    
    # Create use cases with injected dependencies
    return AuthorUseCases(
        create_author=CreateAuthorUseCase(
            author_repository=author_repository,
            logger=logger,
            task_queue=task_queue
        ),
        get_author=GetAuthorUseCase(
            author_repository=author_repository,
            logger=logger
        ),
        list_authors=ListAuthorsUseCase(
            author_repository=author_repository,
            logger=logger
        )
    )


@lru_cache()
def get_book_use_cases() -> BookUseCases:
    """Get book use cases with all dependencies injected.
    
    This function shows how to handle use cases that depend on multiple
    repositories, demonstrating the flexibility of the hexagonal architecture.
    
    Returns:
        BookUseCases: Container with all book-related use cases
    """
    
    # Get infrastructure adapters
    book_repository = get_book_repository()
    author_repository = get_author_repository()
    logger = get_logger()
    task_queue = get_task_queue()
    
    # Create use cases with injected dependencies
    return BookUseCases(
        create_book=CreateBookUseCase(
            book_repository=book_repository,
            author_repository=author_repository,
            logger=logger,
            task_queue=task_queue
        )
    )


# Alternative dependency injection patterns for advanced use cases

class DependencyContainer:
    """Alternative dependency container using class-based approach.
    
    This class demonstrates an alternative to the function-based approach
    above. It can be useful for more complex dependency graphs or when
    you need more control over the lifecycle of dependencies.
    """
    
    def __init__(self):
        """Initialize the dependency container."""
        self._author_repository = None
        self._book_repository = None
        self._logger = None
        self._task_queue = None
    
    @property
    def author_repository(self) -> AuthorRepository:
        """Get or create author repository."""
        if self._author_repository is None:
            self._author_repository = AuthorRepository()
        return self._author_repository
    
    @property
    def book_repository(self) -> BookRepository:
        """Get or create book repository."""
        if self._book_repository is None:
            self._book_repository = BookRepository()
        return self._book_repository
    
    @property
    def logger(self) -> LoguruLoggerAdapter:
        """Get or create logger."""
        if self._logger is None:
            self._logger = LoguruLoggerAdapter()
        return self._logger
    
    @property
    def task_queue(self) -> TaskiqTaskQueueAdapter:
        """Get or create task queue."""
        if self._task_queue is None:
            self._task_queue = TaskiqTaskQueueAdapter()
        return self._task_queue
    
    def get_create_author_use_case(self) -> CreateAuthorUseCase:
        """Get create author use case with dependencies."""
        return CreateAuthorUseCase(
            author_repository=self.author_repository,
            logger=self.logger,
            task_queue=self.task_queue
        )


# Global container instance (optional pattern)
_container = DependencyContainer()


def get_dependency_container() -> DependencyContainer:
    """Get the global dependency container.
    
    This function provides access to the global container, which can be
    useful for scenarios where you need more control over dependency
    lifecycle or want to implement custom scoping.
    
    Returns:
        DependencyContainer: The global dependency container
    """
    return _container


# Logger configuration dependencies

@lru_cache()
def get_logger_config_port() -> LoggerConfigurationPort:
    """Get logger configuration port instance.
    
    This function provides the configuration persistence adapter for
    the Loguru configuration tool, using Dynaconf for storage.
    
    Returns:
        LoggerConfigurationPort: Configuration persistence adapter
    """
    return DynaconfLoggerConfigAdapter()


@lru_cache()
def get_logger_application_port() -> LoggerApplicationPort:
    """Get logger application port instance.
    
    This function provides the Loguru integration adapter for
    applying configurations to the actual logger.
    
    Returns:
        LoggerApplicationPort: Loguru integration adapter
    """
    return LoguruConfigAdapter()


async def get_logger_config_dependencies() -> tuple[LoggerConfigurationPort, LoggerApplicationPort]:
    """Get logger configuration dependencies.
    
    This function provides both ports needed for the logger configuration
    tool, following the hexagonal architecture pattern.
    
    Returns:
        tuple: (config_port, logger_port) for dependency injection
    """
    config_port = get_logger_config_port()
    logger_port = get_logger_application_port()
    
    return config_port, logger_port
