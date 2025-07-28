# Application Layer (`src/application/`)

The **Application Layer** orchestrates the execution of business use cases by coordinating domain objects and external services. It acts as the boundary between the domain logic and the outside world, defining what the application can do without specifying how it's implemented.

## 🎯 Purpose

The Application Layer:
- **Orchestrates use cases** - Coordinates domain objects to fulfill business scenarios
- **Defines application boundaries** - Specifies what the application can do
- **Manages transactions** - Ensures data consistency across operations
- **Handles application logic** - Logic specific to the application, not the domain
- **Provides ports (interfaces)** - Defines contracts for external dependencies

## 🏗️ Architecture Principles

### 1. **Orchestration, Not Business Logic**
- Coordinates domain objects but doesn't contain business rules
- Delegates business decisions to domain entities and services
- Focuses on the "how" of executing use cases

### 2. **Dependency Inversion**
- Depends on abstractions (ports) rather than concrete implementations
- Infrastructure adapters implement the ports defined here
- Enables testability and flexibility

### 3. **Transaction Management**
- Manages the scope of business transactions
- Ensures consistency across multiple domain operations
- Handles rollback scenarios and error recovery

### 4. **Application-Specific Logic**
- Contains logic that's specific to this application
- Different from domain logic (which is universal business rules)
- Examples: workflow orchestration, data transformation, validation

## 📁 Directory Structure

```
application/
├── use_cases/          # Application use cases (business scenarios)
├── services/          # Application services (orchestration logic)
├── ports/            # Interfaces for external dependencies
└── README.md         # This file
```

## 📋 Components

### [`use_cases/`](./use_cases/) - Use Cases

Use cases represent specific business scenarios or user stories. They:
- **Orchestrate domain objects** to fulfill business goals
- **Handle application workflow** and business process steps
- **Manage transactions** and ensure data consistency
- **Transform data** between external and domain representations

**Examples:**
- `CreateAuthorUseCase` - Register a new author in the system
- `PublishBookUseCase` - Publish a book with all required validations
- `ProcessOrderUseCase` - Handle a book purchase transaction
- `GenerateRoyaltyReportUseCase` - Create royalty reports for authors

### [`services/`](./services/) - Application Services

Application services provide higher-level operations that:
- **Combine multiple use cases** into complex workflows
- **Handle cross-cutting concerns** like logging, caching, notifications
- **Manage external integrations** through ports
- **Provide facades** for complex domain operations

**Examples:**
- `AuthorManagementService` - High-level author operations
- `BookCatalogService` - Book catalog management
- `OrderProcessingService` - Order workflow management
- `ReportingService` - Report generation and distribution

### [`ports/`](./ports/) - Ports (Interfaces)

Ports define contracts for external dependencies:
- **Repository interfaces** - Data persistence contracts
- **External service interfaces** - Third-party service contracts
- **Infrastructure interfaces** - System service contracts
- **Event interfaces** - Event publishing and handling contracts

**Examples:**
- `AuthorRepositoryPort` - Author data persistence interface
- `EmailServicePort` - Email sending interface
- `PaymentServicePort` - Payment processing interface
- `LoggerPort` - Logging interface

## 🔧 Implementation Examples

### Use Case Example: CreateAuthorUseCase

```python
# src/application/use_cases/create_author.py
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..ports.author_repository import AuthorRepositoryPort
from ..ports.logger import LoggerPort
from ..ports.event_publisher import EventPublisherPort
from ...domain.entities.author import Author
from ...domain.value_objects.author_name import AuthorName
from ...domain.value_objects.email import Email

@dataclass
class CreateAuthorCommand:
    """Command object for creating an author."""
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    birth_date: Optional[str] = None  # ISO format date string
    nationality: Optional[str] = None

@dataclass
class CreateAuthorResult:
    """Result object for author creation."""
    author_id: UUID
    success: bool
    message: str
    errors: Optional[list] = None

class CreateAuthorUseCase:
    """
    Use case for creating a new author.
    
    This use case orchestrates the creation of an author entity,
    validates business rules, persists the data, and publishes
    relevant events.
    """
    
    def __init__(
        self,
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort,
        event_publisher: EventPublisherPort
    ):
        self._author_repository = author_repository
        self._logger = logger
        self._event_publisher = event_publisher
    
    async def execute(self, command: CreateAuthorCommand) -> CreateAuthorResult:
        """
        Execute the create author use case.
        
        Args:
            command: Command containing author creation data
            
        Returns:
            Result indicating success or failure with details
        """
        try:
            await self._logger.info(
                f"Creating author: {command.first_name} {command.last_name}"
            )
            
            # 1. Validate and create value objects
            author_name = self._create_author_name(command)
            email = self._create_email(command.email) if command.email else None
            birth_date = self._parse_birth_date(command.birth_date)
            
            # 2. Check business rules
            validation_result = await self._validate_author_creation(email)
            if not validation_result.is_valid:
                return CreateAuthorResult(
                    author_id=None,
                    success=False,
                    message="Validation failed",
                    errors=validation_result.errors
                )
            
            # 3. Create domain entity
            author = Author.create(
                name=author_name,
                email=email,
                bio=command.bio,
                birth_date=birth_date,
                nationality=command.nationality
            )
            
            # 4. Persist the author
            saved_author = await self._author_repository.save(author)
            
            # 5. Publish domain event
            await self._event_publisher.publish_author_created(saved_author)
            
            await self._logger.info(
                f"Successfully created author with ID: {saved_author.id}"
            )
            
            return CreateAuthorResult(
                author_id=saved_author.id,
                success=True,
                message="Author created successfully"
            )
            
        except ValueError as e:
            await self._logger.error(f"Validation error creating author: {str(e)}")
            return CreateAuthorResult(
                author_id=None,
                success=False,
                message="Invalid data provided",
                errors=[str(e)]
            )
        
        except Exception as e:
            await self._logger.error(f"Unexpected error creating author: {str(e)}")
            return CreateAuthorResult(
                author_id=None,
                success=False,
                message="An unexpected error occurred",
                errors=[str(e)]
            )
    
    def _create_author_name(self, command: CreateAuthorCommand) -> AuthorName:
        """Create AuthorName value object from command."""
        return AuthorName(
            first_name=command.first_name,
            last_name=command.last_name,
            middle_name=command.middle_name
        )
    
    def _create_email(self, email_str: str) -> Email:
        """Create Email value object from string."""
        return Email.create(email_str)
    
    def _parse_birth_date(self, date_str: Optional[str]):
        """Parse birth date from ISO string."""
        if not date_str:
            return None
        
        from datetime import datetime
        try:
            return datetime.fromisoformat(date_str).date()
        except ValueError:
            raise ValueError(f"Invalid birth date format: {date_str}")
    
    async def _validate_author_creation(self, email: Optional[Email]):
        """Validate business rules for author creation."""
        errors = []
        
        # Check if email is already in use
        if email:
            existing_author = await self._author_repository.find_by_email(email)
            if existing_author:
                errors.append(f"Email {email.value} is already in use")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

@dataclass
class ValidationResult:
    """Result of validation operations."""
    is_valid: bool
    errors: list
```

### Application Service Example: AuthorManagementService

```python
# src/application/services/author_service.py
from typing import List, Optional
from uuid import UUID

from ..use_cases.create_author import CreateAuthorUseCase, CreateAuthorCommand
from ..use_cases.update_author import UpdateAuthorUseCase, UpdateAuthorCommand
from ..use_cases.deactivate_author import DeactivateAuthorUseCase
from ..ports.author_repository import AuthorRepositoryPort
from ..ports.logger import LoggerPort
from ...domain.entities.author import Author
from ...domain.value_objects.email import Email

class AuthorManagementService:
    """
    Application service for managing authors.
    
    Provides high-level operations for author management by
    coordinating multiple use cases and handling complex workflows.
    """
    
    def __init__(
        self,
        create_author_use_case: CreateAuthorUseCase,
        update_author_use_case: UpdateAuthorUseCase,
        deactivate_author_use_case: DeactivateAuthorUseCase,
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort
    ):
        self._create_author_use_case = create_author_use_case
        self._update_author_use_case = update_author_use_case
        self._deactivate_author_use_case = deactivate_author_use_case
        self._author_repository = author_repository
        self._logger = logger
    
    async def register_new_author(
        self,
        first_name: str,
        last_name: str,
        email: str,
        **kwargs
    ) -> dict:
        """
        Register a new author with full onboarding workflow.
        
        This method handles the complete author registration process
        including validation, creation, and initial setup.
        
        Args:
            first_name: Author's first name
            last_name: Author's last name
            email: Author's email address
            **kwargs: Additional author information
            
        Returns:
            Dictionary with registration result and author details
        """
        await self._logger.info(f"Starting author registration for {email}")
        
        # Create the author
        command = CreateAuthorCommand(
            first_name=first_name,
            last_name=last_name,
            email=email,
            **kwargs
        )
        
        result = await self._create_author_use_case.execute(command)
        
        if result.success:
            # Perform additional onboarding steps
            await self._send_welcome_email(result.author_id)
            await self._setup_author_profile(result.author_id)
            
            await self._logger.info(
                f"Author registration completed for ID: {result.author_id}"
            )
        
        return {
            "success": result.success,
            "author_id": result.author_id,
            "message": result.message,
            "errors": result.errors
        }
    
    async def get_author_profile(self, author_id: UUID) -> Optional[dict]:
        """
        Get complete author profile information.
        
        Args:
            author_id: ID of the author
            
        Returns:
            Author profile dictionary or None if not found
        """
        author = await self._author_repository.find_by_id(author_id)
        if not author:
            return None
        
        # Get additional profile information
        books_count = await self._author_repository.count_books_by_author(author_id)
        total_sales = await self._author_repository.get_total_sales_by_author(author_id)
        
        return {
            "id": str(author.id),
            "name": author.name.full_name,
            "email": author.email.value if author.email else None,
            "bio": author.bio,
            "nationality": author.nationality,
            "is_active": author.is_active,
            "books_count": books_count,
            "total_sales": total_sales,
            "created_at": author.created_at.isoformat(),
            "updated_at": author.updated_at.isoformat()
        }
    
    async def search_authors(
        self,
        query: str,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        Search for authors with filtering and pagination.
        
        Args:
            query: Search query string
            filters: Optional filters (nationality, active status, etc.)
            page: Page number (1-based)
            page_size: Number of results per page
            
        Returns:
            Dictionary with search results and pagination info
        """
        await self._logger.debug(f"Searching authors with query: {query}")
        
        # Use repository to perform search
        search_result = await self._author_repository.search(
            query=query,
            filters=filters or {},
            offset=(page - 1) * page_size,
            limit=page_size
        )
        
        # Transform domain objects to DTOs
        authors_data = [
            {
                "id": str(author.id),
                "name": author.name.full_name,
                "email": author.email.value if author.email else None,
                "nationality": author.nationality,
                "is_active": author.is_active
            }
            for author in search_result.authors
        ]
        
        return {
            "authors": authors_data,
            "total_count": search_result.total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (search_result.total_count + page_size - 1) // page_size
        }
    
    async def bulk_update_authors(
        self,
        author_updates: List[dict]
    ) -> dict:
        """
        Update multiple authors in a single operation.
        
        Args:
            author_updates: List of author update dictionaries
            
        Returns:
            Dictionary with bulk update results
        """
        await self._logger.info(f"Starting bulk update for {len(author_updates)} authors")
        
        successful_updates = []
        failed_updates = []
        
        for update_data in author_updates:
            try:
                author_id = UUID(update_data["id"])
                command = UpdateAuthorCommand(
                    author_id=author_id,
                    **{k: v for k, v in update_data.items() if k != "id"}
                )
                
                result = await self._update_author_use_case.execute(command)
                
                if result.success:
                    successful_updates.append(author_id)
                else:
                    failed_updates.append({
                        "author_id": author_id,
                        "errors": result.errors
                    })
                    
            except Exception as e:
                failed_updates.append({
                    "author_id": update_data.get("id"),
                    "errors": [str(e)]
                })
        
        await self._logger.info(
            f"Bulk update completed: {len(successful_updates)} successful, "
            f"{len(failed_updates)} failed"
        )
        
        return {
            "successful_count": len(successful_updates),
            "failed_count": len(failed_updates),
            "successful_updates": successful_updates,
            "failed_updates": failed_updates
        }
    
    async def _send_welcome_email(self, author_id: UUID) -> None:
        """Send welcome email to new author."""
        # This would use an email service port
        await self._logger.info(f"Sending welcome email to author {author_id}")
    
    async def _setup_author_profile(self, author_id: UUID) -> None:
        """Set up initial author profile."""
        # This would perform initial profile setup
        await self._logger.info(f"Setting up profile for author {author_id}")
```

### Port Example: AuthorRepositoryPort

```python
# src/application/ports/author_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ...domain.entities.author import Author
from ...domain.value_objects.email import Email

class AuthorRepositoryPort(ABC):
    """
    Port (interface) for author data persistence.
    
    Defines the contract that infrastructure adapters must implement
    to provide author data persistence capabilities.
    """
    
    @abstractmethod
    async def save(self, author: Author) -> Author:
        """
        Save an author entity.
        
        Args:
            author: Author entity to save
            
        Returns:
            Saved author entity with updated metadata
            
        Raises:
            RepositoryError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, author_id: UUID) -> Optional[Author]:
        """
        Find an author by their ID.
        
        Args:
            author_id: Unique identifier of the author
            
        Returns:
            Author entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[Author]:
        """
        Find an author by their email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Author entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_all(
        self,
        offset: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Author]:
        """
        Find all authors with pagination.
        
        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive authors
            
        Returns:
            List of author entities
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        filters: dict,
        offset: int = 0,
        limit: int = 100
    ) -> "AuthorSearchResult":
        """
        Search for authors with filters.
        
        Args:
            query: Search query string
            filters: Dictionary of filters to apply
            offset: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Search result with authors and total count
        """
        pass
    
    @abstractmethod
    async def count_books_by_author(self, author_id: UUID) -> int:
        """
        Count the number of books by an author.
        
        Args:
            author_id: ID of the author
            
        Returns:
            Number of books by the author
        """
        pass
    
    @abstractmethod
    async def get_total_sales_by_author(self, author_id: UUID) -> int:
        """
        Get total sales for all books by an author.
        
        Args:
            author_id: ID of the author
            
        Returns:
            Total sales count
        """
        pass
    
    @abstractmethod
    async def delete(self, author_id: UUID) -> bool:
        """
        Delete an author by ID.
        
        Args:
            author_id: ID of the author to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryError: If delete operation fails
        """
        pass

class AuthorSearchResult:
    """Result object for author search operations."""
    
    def __init__(self, authors: List[Author], total_count: int):
        self.authors = authors
        self.total_count = total_count
```

## 🧪 Testing Application Layer

```python
# tests/unit/application/use_cases/test_create_author.py
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from src.application.use_cases.create_author import (
    CreateAuthorUseCase, 
    CreateAuthorCommand,
    CreateAuthorResult
)
from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName
from src.domain.value_objects.email import Email

class TestCreateAuthorUseCase:
    @pytest.fixture
    def mock_author_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_logger(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_event_publisher(self):
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_author_repository, mock_logger, mock_event_publisher):
        return CreateAuthorUseCase(
            author_repository=mock_author_repository,
            logger=mock_logger,
            event_publisher=mock_event_publisher
        )
    
    @pytest.mark.asyncio
    async def test_execute_with_valid_command_succeeds(
        self, 
        use_case, 
        mock_author_repository,
        mock_event_publisher
    ):
        """Test successful author creation."""
        # Arrange
        command = CreateAuthorCommand(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        
        # Mock repository responses
        mock_author_repository.find_by_email.return_value = None
        mock_author_repository.save.return_value = Author.create(
            name=AuthorName("John", "Doe"),
            email=Email.create("john.doe@example.com")
        )
        
        # Act
        result = await use_case.execute(command)
        
        # Assert
        assert result.success is True
        assert result.author_id is not None
        assert "successfully" in result.message.lower()
        
        # Verify repository was called
        mock_author_repository.save.assert_called_once()
        mock_event_publisher.publish_author_created.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_with_duplicate_email_fails(
        self,
        use_case,
        mock_author_repository
    ):
        """Test author creation fails with duplicate email."""
        # Arrange
        command = CreateAuthorCommand(
            first_name="John",
            last_name="Doe",
            email="existing@example.com"
        )
        
        # Mock existing author with same email
        existing_author = Author.create(
            name=AuthorName("Jane", "Smith"),
            email=Email.create("existing@example.com")
        )
        mock_author_repository.find_by_email.return_value = existing_author
        
        # Act
        result = await use_case.execute(command)
        
        # Assert
        assert result.success is False
        assert result.author_id is None
        assert "already in use" in str(result.errors)
        
        # Verify save was not called
        mock_author_repository.save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_with_invalid_email_fails(self, use_case):
        """Test author creation fails with invalid email."""
        # Arrange
        command = CreateAuthorCommand(
            first_name="John",
            last_name="Doe",
            email="invalid-email"
        )
        
        # Act
        result = await use_case.execute(command)
        
        # Assert
        assert result.success is False
        assert result.author_id is None
        assert "Invalid data provided" in result.message
```

## ✅ Best Practices

### Use Case Design
- **Single responsibility** - Each use case should handle one business scenario
- **Command/Query separation** - Separate commands (write) from queries (read)
- **Input validation** - Validate all inputs before processing
- **Error handling** - Provide meaningful error messages and recovery options
- **Transaction boundaries** - Define clear transaction scopes

### Service Design
- **Facade pattern** - Provide simplified interfaces for complex operations
- **Composition** - Combine use cases rather than duplicating logic
- **Stateless** - Keep services stateless for better scalability
- **Dependency injection** - Use constructor injection for dependencies

### Port Design
- **Interface segregation** - Keep interfaces focused and minimal
- **Stable abstractions** - Don't change interfaces frequently
- **Domain-focused** - Express operations in domain terms
- **Async by default** - Use async methods for I/O operations

## ❌ Common Pitfalls

- **Business logic in application layer** - Keep business rules in domain layer
- **Tight coupling** - Avoid depending on concrete implementations
- **God services** - Services that do too many unrelated things
- **Leaky abstractions** - Ports that expose infrastructure details
- **Missing error handling** - Not handling all possible error scenarios

## 🔄 Integration Points

The Application Layer:
- **Uses Domain Layer** - Orchestrates domain entities and services
- **Defines Ports** - For infrastructure layer to implement
- **Serves Presentation Layer** - Provides use cases for controllers/handlers
- **Manages Transactions** - Coordinates with infrastructure for data consistency

This layer is the heart of the hexagon architecture, defining what your application does while remaining independent of how it's implemented.

