# Repositories Directory (`repositories/`)

The **Repositories Directory** contains data access implementations that handle persistence and retrieval of domain entities. In hexagon architecture, repositories are **infrastructure adapters** that implement the repository ports defined in the application layer, providing concrete data persistence mechanisms.

## 🎯 Purpose & Role in Hexagon Architecture

Repositories serve as the **data access layer** that:
- **Implement repository ports** defined in the application layer
- **Translate between domain entities and data models** 
- **Handle database operations** (CRUD, queries, transactions)
- **Provide data persistence abstraction** for the domain layer
- **Manage data mapping and transformation**

```
┌─────────────────────────────────────────┐
│           PRESENTATION LAYER            │
│  ┌─────────────────────────────────┐   │
│  │        INFRASTRUCTURE LAYER     │   │
│  │  ┌─────────────────────────┐   │   │
│  │  │    APPLICATION LAYER    │   │   │
│  │  │  ┌─────────────────┐   │   │   │
│  │  │  │  DOMAIN LAYER   │   │   │   │
│  │  │  └─────────────────┘   │   │   │
│  │  └─────────────────────────┘   │   │
│  │         ↑                       │   │
│  │    REPOSITORIES ←──────────────┐│   │
│  │    (Data Access)               ││   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 🏗️ Key Responsibilities

### 1. **Port Implementation**
- Implement repository interfaces from `src/application/ports/`
- Provide concrete data persistence mechanisms
- Handle database-specific operations and optimizations

### 2. **Entity-Model Translation**
- Convert domain entities to database models
- Transform database records back to domain entities
- Handle complex object mapping and relationships

### 3. **Query Management**
- Implement complex database queries
- Handle filtering, sorting, and pagination
- Optimize database performance and indexing

### 4. **Transaction Coordination**
- Manage database transactions and consistency
- Handle rollback scenarios and error recovery
- Coordinate with application layer transaction boundaries

## 📁 Repository Structure

```
repositories/
├── author_repository.py      # Author data persistence
├── book_repository.py        # Book data persistence  
├── base_repository.py        # Common repository functionality
├── exceptions.py             # Repository-specific exceptions
└── README.md                 # This file
```

## 🔧 Implementation Examples

### Base Repository Pattern

```python
# repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

T = TypeVar('T')
M = TypeVar('M')

class BaseRepository(Generic[T, M], ABC):
    """
    Base repository providing common CRUD operations.
    
    Generic base class that handles standard database operations
    while allowing specific repositories to customize behavior.
    """
    
    def __init__(self, session: AsyncSession, model_class: type[M]):
        self._session = session
        self._model_class = model_class
    
    async def save(self, entity: T) -> T:
        """
        Save an entity to the database.
        
        Args:
            entity: Domain entity to save
            
        Returns:
            Saved entity with updated metadata
        """
        try:
            # Convert entity to database model
            model = self._entity_to_model(entity)
            
            # Add to session and flush to get ID
            self._session.add(model)
            await self._session.flush()
            
            # Convert back to entity
            return self._model_to_entity(model)
            
        except Exception as e:
            await self._session.rollback()
            raise RepositoryError(f"Failed to save entity: {str(e)}")
    
    async def find_by_id(self, entity_id: UUID) -> Optional[T]:
        """Find entity by ID."""
        try:
            stmt = select(self._model_class).where(
                self._model_class.id == entity_id
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            return self._model_to_entity(model) if model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to find entity by ID: {str(e)}")
    
    async def find_all(
        self, 
        offset: int = 0, 
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[T]:
        """Find all entities with pagination and filtering."""
        try:
            stmt = select(self._model_class)
            
            # Apply filters if provided
            if filters:
                stmt = self._apply_filters(stmt, filters)
            
            # Apply pagination
            stmt = stmt.offset(offset).limit(limit)
            
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to find entities: {str(e)}")
    
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID."""
        try:
            stmt = delete(self._model_class).where(
                self._model_class.id == entity_id
            )
            result = await self._session.execute(stmt)
            return result.rowcount > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to delete entity: {str(e)}")
    
    @abstractmethod
    def _entity_to_model(self, entity: T) -> M:
        """Convert domain entity to database model."""
        pass
    
    @abstractmethod
    def _model_to_entity(self, model: M) -> T:
        """Convert database model to domain entity."""
        pass
    
    def _apply_filters(self, stmt, filters: dict):
        """Apply filters to query statement."""
        # Override in specific repositories for custom filtering
        return stmt

class RepositoryError(Exception):
    """Exception raised by repository operations."""
    pass
```

### Author Repository Implementation

```python
# repositories/author_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository, RepositoryError
from ..models.author_model import AuthorModel
from ..models.book_model import BookModel
from ...src.application.ports.author_repository import AuthorRepositoryPort, AuthorSearchResult
from ...src.domain.entities.author import Author
from ...src.domain.value_objects.author_name import AuthorName
from ...src.domain.value_objects.email import Email

class AuthorRepository(BaseRepository[Author, AuthorModel], AuthorRepositoryPort):
    """
    Author repository implementation using SQLAlchemy.
    
    Provides concrete implementation of author data persistence
    with optimized queries and proper entity-model mapping.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, AuthorModel)
    
    async def find_by_email(self, email: Email) -> Optional[Author]:
        """
        Find author by email address.
        
        Args:
            email: Email value object to search for
            
        Returns:
            Author entity if found, None otherwise
        """
        try:
            stmt = select(AuthorModel).where(
                AuthorModel.email == email.value
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            return self._model_to_entity(model) if model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to find author by email: {str(e)}")
    
    async def search(
        self,
        query: str,
        filters: dict,
        offset: int = 0,
        limit: int = 100
    ) -> AuthorSearchResult:
        """
        Search authors with full-text search and filters.
        
        Args:
            query: Search query string
            filters: Dictionary of filters (nationality, active status, etc.)
            offset: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Search result with authors and total count
        """
        try:
            # Build base query
            stmt = select(AuthorModel)
            count_stmt = select(func.count(AuthorModel.id))
            
            # Apply text search
            if query.strip():
                search_filter = or_(
                    AuthorModel.first_name.ilike(f"%{query}%"),
                    AuthorModel.last_name.ilike(f"%{query}%"),
                    AuthorModel.bio.ilike(f"%{query}%")
                )
                stmt = stmt.where(search_filter)
                count_stmt = count_stmt.where(search_filter)
            
            # Apply filters
            filter_conditions = []
            
            if filters.get('nationality'):
                filter_conditions.append(
                    AuthorModel.nationality == filters['nationality']
                )
            
            if filters.get('is_active') is not None:
                filter_conditions.append(
                    AuthorModel.is_active == filters['is_active']
                )
            
            if filters.get('min_age'):
                # Calculate birth date for minimum age
                from datetime import date, timedelta
                max_birth_date = date.today() - timedelta(days=filters['min_age'] * 365)
                filter_conditions.append(
                    AuthorModel.birth_date <= max_birth_date
                )
            
            if filter_conditions:
                combined_filter = and_(*filter_conditions)
                stmt = stmt.where(combined_filter)
                count_stmt = count_stmt.where(combined_filter)
            
            # Apply ordering and pagination
            stmt = stmt.order_by(
                AuthorModel.last_name, 
                AuthorModel.first_name
            ).offset(offset).limit(limit)
            
            # Execute queries
            result = await self._session.execute(stmt)
            count_result = await self._session.execute(count_stmt)
            
            models = result.scalars().all()
            total_count = count_result.scalar()
            
            # Convert to domain entities
            authors = [self._model_to_entity(model) for model in models]
            
            return AuthorSearchResult(authors=authors, total_count=total_count)
            
        except Exception as e:
            raise RepositoryError(f"Failed to search authors: {str(e)}")
    
    async def count_books_by_author(self, author_id: UUID) -> int:
        """Count books by author."""
        try:
            stmt = select(func.count(BookModel.id)).where(
                BookModel.author_id == author_id
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to count books: {str(e)}")
    
    async def get_total_sales_by_author(self, author_id: UUID) -> int:
        """Get total sales for all books by author."""
        try:
            # This would join with sales/order tables in a real implementation
            stmt = select(func.coalesce(func.sum(BookModel.sales_count), 0)).where(
                BookModel.author_id == author_id
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to get total sales: {str(e)}")
    
    async def find_authors_with_books(
        self, 
        offset: int = 0, 
        limit: int = 100
    ) -> List[Author]:
        """Find authors with their books eagerly loaded."""
        try:
            stmt = select(AuthorModel).options(
                selectinload(AuthorModel.books)
            ).offset(offset).limit(limit)
            
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to find authors with books: {str(e)}")
    
    def _entity_to_model(self, entity: Author) -> AuthorModel:
        """Convert Author entity to AuthorModel."""
        return AuthorModel(
            id=entity.id,
            first_name=entity.name.first_name,
            last_name=entity.name.last_name,
            middle_name=entity.name.middle_name,
            email=entity.email.value if entity.email else None,
            bio=entity.bio,
            birth_date=entity.birth_date,
            nationality=entity.nationality,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def _model_to_entity(self, model: AuthorModel) -> Author:
        """Convert AuthorModel to Author entity."""
        # Reconstruct value objects
        author_name = AuthorName(
            first_name=model.first_name,
            last_name=model.last_name,
            middle_name=model.middle_name
        )
        
        email = Email.create(model.email) if model.email else None
        
        # Create entity with all attributes
        return Author(
            id=model.id,
            name=author_name,
            email=email,
            bio=model.bio,
            birth_date=model.birth_date,
            nationality=model.nationality,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _apply_filters(self, stmt, filters: dict):
        """Apply custom filters for author queries."""
        conditions = []
        
        if 'is_active' in filters:
            conditions.append(AuthorModel.is_active == filters['is_active'])
        
        if 'nationality' in filters:
            conditions.append(AuthorModel.nationality == filters['nationality'])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        return stmt
```

### Book Repository Implementation

```python
# repositories/book_repository.py
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository, RepositoryError
from ..models.book_model import BookModel
from ..models.author_model import AuthorModel
from ...src.application.ports.book_repository import BookRepositoryPort
from ...src.domain.entities.book import Book
from ...src.domain.value_objects.book_title import BookTitle
from ...src.domain.value_objects.isbn import ISBN
from ...src.domain.value_objects.money import Money

class BookRepository(BaseRepository[Book, BookModel], BookRepositoryPort):
    """
    Book repository implementation with advanced querying capabilities.
    
    Handles book persistence with optimized queries for common operations
    like finding by ISBN, genre filtering, and inventory management.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, BookModel)
    
    async def find_by_isbn(self, isbn: ISBN) -> Optional[Book]:
        """Find book by ISBN."""
        try:
            stmt = select(BookModel).where(BookModel.isbn == isbn.value)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            return self._model_to_entity(model) if model else None
            
        except Exception as e:
            raise RepositoryError(f"Failed to find book by ISBN: {str(e)}")
    
    async def find_by_author(
        self, 
        author_id: UUID, 
        include_inactive: bool = False
    ) -> List[Book]:
        """Find all books by a specific author."""
        try:
            stmt = select(BookModel).where(BookModel.author_id == author_id)
            
            if not include_inactive:
                stmt = stmt.where(BookModel.is_active == True)
            
            stmt = stmt.order_by(desc(BookModel.publication_date))
            
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to find books by author: {str(e)}")
    
    async def find_by_genre(
        self, 
        genre: str, 
        offset: int = 0, 
        limit: int = 100
    ) -> List[Book]:
        """Find books by genre with pagination."""
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.genre.ilike(f"%{genre}%"),
                    BookModel.is_active == True
                )
            ).order_by(desc(BookModel.created_at)).offset(offset).limit(limit)
            
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to find books by genre: {str(e)}")
    
    async def find_low_stock_books(self, threshold: int = 10) -> List[Book]:
        """Find books with stock below threshold."""
        try:
            stmt = select(BookModel).where(
                and_(
                    BookModel.stock_quantity <= threshold,
                    BookModel.stock_quantity > 0,
                    BookModel.is_active == True
                )
            ).order_by(BookModel.stock_quantity)
            
            result = await self._session.execute(stmt)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            raise RepositoryError(f"Failed to find low stock books: {str(e)}")
    
    async def update_stock(self, book_id: UUID, new_quantity: int) -> bool:
        """Update book stock quantity."""
        try:
            stmt = select(BookModel).where(BookModel.id == book_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            model.stock_quantity = new_quantity
            await self._session.flush()
            
            return True
            
        except Exception as e:
            raise RepositoryError(f"Failed to update stock: {str(e)}")
    
    def _entity_to_model(self, entity: Book) -> BookModel:
        """Convert Book entity to BookModel."""
        return BookModel(
            id=entity.id,
            title=entity.title.value,
            isbn=entity.isbn.value,
            author_id=entity.author_id,
            publication_date=entity.publication_date,
            page_count=entity.page_count,
            genre=entity.genre,
            description=entity.description,
            price_amount=entity.price.amount,
            price_currency=entity.price.currency,
            stock_quantity=entity.stock_quantity,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def _model_to_entity(self, model: BookModel) -> Book:
        """Convert BookModel to Book entity."""
        # Reconstruct value objects
        title = BookTitle(model.title)
        isbn = ISBN(model.isbn)
        price = Money.create(model.price_amount, model.price_currency)
        
        return Book(
            id=model.id,
            title=title,
            isbn=isbn,
            author_id=model.author_id,
            publication_date=model.publication_date,
            page_count=model.page_count,
            genre=model.genre,
            description=model.description,
            price=price,
            stock_quantity=model.stock_quantity,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
```

## 🧪 Testing Repositories

```python
# tests/integration/repositories/test_author_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.author_repository import AuthorRepository
from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName
from src.domain.value_objects.email import Email

class TestAuthorRepository:
    @pytest.fixture
    async def repository(self, db_session: AsyncSession):
        return AuthorRepository(db_session)
    
    @pytest.mark.asyncio
    async def test_save_and_find_author(self, repository):
        """Test saving and retrieving an author."""
        # Arrange
        author = Author.create(
            name=AuthorName("John", "Doe"),
            email=Email.create("john.doe@example.com")
        )
        
        # Act
        saved_author = await repository.save(author)
        found_author = await repository.find_by_id(saved_author.id)
        
        # Assert
        assert found_author is not None
        assert found_author.name.full_name == "John Doe"
        assert found_author.email.value == "john.doe@example.com"
    
    @pytest.mark.asyncio
    async def test_find_by_email(self, repository):
        """Test finding author by email."""
        # Arrange
        email = Email.create("unique@example.com")
        author = Author.create(
            name=AuthorName("Jane", "Smith"),
            email=email
        )
        await repository.save(author)
        
        # Act
        found_author = await repository.find_by_email(email)
        
        # Assert
        assert found_author is not None
        assert found_author.email == email
    
    @pytest.mark.asyncio
    async def test_search_authors(self, repository):
        """Test author search functionality."""
        # Arrange - create test authors
        authors = [
            Author.create(name=AuthorName("John", "Doe"), nationality="USA"),
            Author.create(name=AuthorName("Jane", "Smith"), nationality="UK"),
            Author.create(name=AuthorName("Bob", "Johnson"), nationality="USA")
        ]
        
        for author in authors:
            await repository.save(author)
        
        # Act
        result = await repository.search(
            query="John",
            filters={"nationality": "USA"},
            offset=0,
            limit=10
        )
        
        # Assert
        assert len(result.authors) == 1
        assert result.authors[0].name.first_name == "John"
        assert result.total_count == 1
```

## ✅ Best Practices

### Repository Design
- **Implement repository ports** from application layer
- **Use generic base classes** to reduce code duplication
- **Handle entity-model mapping** consistently
- **Provide optimized queries** for common operations
- **Manage database transactions** properly

### Error Handling
- **Wrap database exceptions** in repository-specific exceptions
- **Provide meaningful error messages** for debugging
- **Handle connection failures** gracefully
- **Log database operations** for monitoring

### Performance Optimization
- **Use eager loading** for related entities when needed
- **Implement proper indexing** strategies
- **Cache frequently accessed data** when appropriate
- **Optimize query patterns** for common use cases

## ❌ Common Pitfalls

- **Leaking database models** to application/domain layers
- **Not handling database exceptions** properly
- **Creating N+1 query problems** with lazy loading
- **Mixing business logic** with data access logic
- **Not using transactions** for multi-step operations

## 🔄 Integration Points

Repositories integrate with:
- **Application Layer** - Implement repository ports
- **Infrastructure Layer** - Use database connections and ORM
- **Domain Layer** - Work with domain entities and value objects
- **Models Directory** - Use database models for persistence

The repositories directory is crucial for data persistence in hexagon architecture, providing the concrete implementations that allow your domain logic to persist and retrieve data without being coupled to specific database technologies.

