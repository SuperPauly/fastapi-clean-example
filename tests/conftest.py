"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from taskiq import InMemoryBroker

from src.application.ports.author_repository import AuthorRepositoryPort
from src.application.ports.book_repository import BookRepositoryPort
from src.application.ports.logger import LoggerPort
from src.application.ports.task_queue import TaskQueuePort
from src.domain.entities.author import Author
from src.domain.entities.book import Book
from src.domain.value_objects.author_name import AuthorName
from src.domain.value_objects.book_title import BookTitle


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_logger() -> LoggerPort:
    """Mock logger for testing."""
    logger = Mock(spec=LoggerPort)
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_author_repository() -> AuthorRepositoryPort:
    """Mock author repository for testing."""
    repository = AsyncMock(spec=AuthorRepositoryPort)
    return repository


@pytest.fixture
def mock_book_repository() -> BookRepositoryPort:
    """Mock book repository for testing."""
    repository = AsyncMock(spec=BookRepositoryPort)
    return repository


@pytest.fixture
def mock_task_queue() -> TaskQueuePort:
    """Mock task queue for testing."""
    task_queue = AsyncMock(spec=TaskQueuePort)
    task_queue.enqueue.return_value = "test-task-id"
    task_queue.schedule.return_value = "test-scheduled-task-id"
    return task_queue


@pytest.fixture
def in_memory_broker() -> InMemoryBroker:
    """In-memory Taskiq broker for testing."""
    return InMemoryBroker()


@pytest.fixture
def sample_author() -> Author:
    """Sample author for testing."""
    return Author(name=AuthorName(value="Test Author"))


@pytest.fixture
def sample_book(sample_author: Author) -> Book:
    """Sample book for testing."""
    return Book(
        title=BookTitle(value="Test Book"),
        author_ids=[sample_author.id]
    )


@pytest.fixture
def sample_author_name() -> AuthorName:
    """Sample author name for testing."""
    return AuthorName(value="Test Author")


@pytest.fixture
def sample_book_title() -> BookTitle:
    """Sample book title for testing."""
    return BookTitle(value="Test Book")


# Async fixtures for database testing
@pytest.fixture
async def async_mock_author_repository() -> AsyncGenerator[AuthorRepositoryPort, None]:
    """Async mock author repository for testing."""
    repository = AsyncMock(spec=AuthorRepositoryPort)
    yield repository


@pytest.fixture
async def async_mock_book_repository() -> AsyncGenerator[BookRepositoryPort, None]:
    """Async mock book repository for testing."""
    repository = AsyncMock(spec=BookRepositoryPort)
    yield repository


# Test data factories
class AuthorFactory:
    """Factory for creating test authors."""
    
    @staticmethod
    def create(name: str = "Test Author") -> Author:
        """Create a test author."""
        return Author(name=AuthorName(value=name))
    
    @staticmethod
    def create_multiple(count: int, name_prefix: str = "Author") -> list[Author]:
        """Create multiple test authors."""
        return [
            AuthorFactory.create(f"{name_prefix} {i}")
            for i in range(1, count + 1)
        ]


class BookFactory:
    """Factory for creating test books."""
    
    @staticmethod
    def create(title: str = "Test Book", author_ids: list = None) -> Book:
        """Create a test book."""
        if author_ids is None:
            author_ids = []
        return Book(
            title=BookTitle(value=title),
            author_ids=author_ids
        )
    
    @staticmethod
    def create_multiple(count: int, title_prefix: str = "Book") -> list[Book]:
        """Create multiple test books."""
        return [
            BookFactory.create(f"{title_prefix} {i}")
            for i in range(1, count + 1)
        ]


@pytest.fixture
def author_factory() -> AuthorFactory:
    """Author factory fixture."""
    return AuthorFactory


@pytest.fixture
def book_factory() -> BookFactory:
    """Book factory fixture."""
    return BookFactory

