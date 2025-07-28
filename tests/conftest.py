"""Test configuration and fixtures."""

import asyncio
import os
from pathlib import Path
import tempfile
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

# Import TUI-related ports if they exist
try:
    from src.application.ports.logger_configuration import LoggerConfigurationPort, LoggerApplicationPort
except ImportError:
    # Fallback for when TUI components aren't available
    LoggerConfigurationPort = None
    LoggerApplicationPort = None


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


# TUI Testing Configuration
@pytest.fixture(autouse=True)
def setup_tui_test_environment():
    """Set up environment variables for TUI testing."""
    # Disable terminal features that might interfere with testing
    original_env = {}
    tui_env_vars = {
        "TERM": "dumb",
        "NO_COLOR": "1", 
        "TEXTUAL_HEADLESS": "1"
    }
    
    # Store original values and set new ones
    for key, value in tui_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment variables
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def tui_test_timeout():
    """Provide timeout settings for TUI tests."""
    return 10.0  # 10 seconds timeout for TUI operations


# TUI-specific fixtures (only if TUI components are available)
if LoggerConfigurationPort is not None:
    @pytest.fixture
    def mock_logger_config_port():
        """Create a mock logger configuration port."""
        mock = Mock(spec=LoggerConfigurationPort)
        mock.load_configuration = AsyncMock(return_value=None)
        mock.save_configuration = AsyncMock(return_value=True)
        mock.delete_configuration = AsyncMock(return_value=True)
        mock.list_configurations = AsyncMock(return_value=[])
        mock.get_configuration_summary = AsyncMock(return_value=None)
        mock.validate_configuration = AsyncMock(return_value=[])
        mock.export_configuration = AsyncMock(return_value=None)
        mock.import_configuration = AsyncMock(return_value=None)
        return mock


if LoggerApplicationPort is not None:
    @pytest.fixture
    def mock_logger_application_port():
        """Create a mock logger application port."""
        mock = Mock(spec=LoggerApplicationPort)
        mock.apply_configuration = AsyncMock(return_value=True)
        mock.test_configuration = AsyncMock(return_value={"success": True, "output": []})
        mock.get_current_configuration = AsyncMock(return_value=None)
        mock.reset_logger = AsyncMock(return_value=True)
        mock.preview_log_output = AsyncMock(return_value=[])
        return mock


@pytest.fixture
def sample_config_data():
    """Provide sample configuration data for testing."""
    return {
        "name": "test_config",
        "description": "Test configuration",
        "enabled": True,
        "global_level": {"value": "DEBUG"},
        "handlers": [
            {
                "id": "test-handler",
                "name": "console",
                "enabled": True,
                "handler_type": "console",
                "sink": "sys.stdout",
                "level": {"value": "INFO"},
                "format_config": {
                    "preset": "simple",
                    "custom_format": None,
                    "colorize": True,
                    "serialize": False,
                    "backtrace": True,
                    "diagnose": True
                },
                "rotation": {
                    "rotation_type": "none",
                    "size_limit": None,
                    "size_unit": "MB",
                    "time_interval": None,
                    "time_unit": "day",
                    "rotation_time": None,
                    "retention_count": None,
                    "retention_time": None,
                    "compression": None
                },
                "enqueue": False,
                "catch": True,
                "encoding": "utf-8",
                "mode": "a",
                "buffering": 1,
                "filter_expression": None
            }
        ],
        "activation": [],
        "patcher": None,
        "extra": {}
    }


# Pytest configuration for TUI tests
def pytest_configure(config):
    """Configure pytest for TUI testing."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "tui: mark test as a TUI test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "test_loguru_tui" in item.nodeid or "test_dynaconf_tui" in item.nodeid:
            item.add_marker(pytest.mark.tui)
        
        if "/integration/" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        if "/e2e/" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        
        if "/performance/" in item.nodeid:
            item.add_marker(pytest.mark.slow)
