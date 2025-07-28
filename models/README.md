# Models Directory (`models/`)

The **Models Directory** contains database model definitions that represent the structure of data as it's stored in the database. In hexagon architecture, models are part of the **infrastructure layer** and serve as the persistence representation of domain entities.

## 🎯 Purpose & Role in Hexagon Architecture

Database models serve as **persistence adapters** that:
- **Define database table structures** and relationships
- **Map domain entities** to database representations
- **Handle database-specific concerns** (indexes, constraints, migrations)
- **Provide ORM functionality** for data persistence
- **Abstract database implementation details** from domain logic

```
Domain Entity ←→ Repository ←→ Database Model ←→ Database
      ↓              ↓            ↓            ↓
   Author.py → AuthorRepository → AuthorModel → PostgreSQL
```

## 🏗️ Key Responsibilities

### 1. **Database Schema Definition**
- Define table structures, columns, and data types
- Specify relationships between tables
- Set up indexes and constraints for performance

### 2. **ORM Integration**
- Provide SQLAlchemy/Tortoise ORM model definitions
- Handle database sessions and connections
- Support query optimization and lazy loading

### 3. **Data Mapping**
- Map between domain entities and database records
- Handle data type conversions and serialization
- Manage database-specific field requirements

## 📁 Model Structure

```
models/
├── author_model.py         # Author database model
├── book_model.py          # Book database model
├── base_model.py          # Base model with common fields
└── README.md              # This file
```

## 🔧 Implementation Examples

### Base Model with Common Fields

```python
# models/base_model.py
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    """
    Base model with common fields for all database tables.
    
    Provides standard fields that most entities need:
    - id: Primary key
    - created_at: Creation timestamp
    - updated_at: Last update timestamp
    - is_active: Soft delete flag
    """
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the record"
    )
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when the record was created"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when the record was last updated"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Flag indicating if the record is active (soft delete)"
    )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
```

### Author Model

```python
# models/author_model.py
from sqlalchemy import Column, String, Text, Date, Index
from sqlalchemy.orm import relationship
from .base_model import BaseModel

class AuthorModel(BaseModel):
    """
    Database model for Author entity.
    
    Maps the Author domain entity to database table structure
    with appropriate constraints, indexes, and relationships.
    """
    
    __tablename__ = "authors"
    
    # Name fields
    first_name = Column(
        String(50),
        nullable=False,
        doc="Author's first name"
    )
    
    last_name = Column(
        String(50),
        nullable=False,
        doc="Author's last name"
    )
    
    middle_name = Column(
        String(50),
        nullable=True,
        doc="Author's middle name (optional)"
    )
    
    # Contact information
    email = Column(
        String(254),  # RFC 5321 email length limit
        nullable=True,
        unique=True,
        index=True,
        doc="Author's email address (unique)"
    )
    
    # Profile information
    bio = Column(
        Text,
        nullable=True,
        doc="Author's biography"
    )
    
    birth_date = Column(
        Date,
        nullable=True,
        doc="Author's birth date"
    )
    
    nationality = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Author's nationality"
    )
    
    # Relationships
    books = relationship(
        "BookModel",
        back_populates="author",
        lazy="select",
        doc="Books written by this author"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_author_name', 'last_name', 'first_name'),
        Index('idx_author_nationality_active', 'nationality', 'is_active'),
        Index('idx_author_email_active', 'email', 'is_active'),
    )
    
    def __repr__(self):
        return f"<AuthorModel(id={self.id}, name='{self.first_name} {self.last_name}')>"
```

### Book Model

```python
# models/book_model.py
from sqlalchemy import Column, String, Text, Date, Integer, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base_model import BaseModel

class BookModel(BaseModel):
    """
    Database model for Book entity.
    
    Represents books in the database with full metadata,
    pricing information, and inventory tracking.
    """
    
    __tablename__ = "books"
    
    # Basic book information
    title = Column(
        String(200),
        nullable=False,
        index=True,
        doc="Book title"
    )
    
    isbn = Column(
        String(17),  # Format: 978-XXXXXXXXX
        nullable=False,
        unique=True,
        index=True,
        doc="International Standard Book Number (unique)"
    )
    
    # Author relationship
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("authors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="ID of the book's author"
    )
    
    # Publication details
    publication_date = Column(
        Date,
        nullable=True,
        index=True,
        doc="Date when the book was published"
    )
    
    page_count = Column(
        Integer,
        nullable=True,
        doc="Number of pages in the book"
    )
    
    genre = Column(
        String(50),
        nullable=True,
        index=True,
        doc="Book genre/category"
    )
    
    description = Column(
        Text,
        nullable=True,
        doc="Book description/summary"
    )
    
    # Pricing information
    price_amount = Column(
        Numeric(10, 2),  # Up to 99,999,999.99
        nullable=False,
        default=0.00,
        doc="Book price amount"
    )
    
    price_currency = Column(
        String(3),  # ISO 4217 currency codes
        nullable=False,
        default="USD",
        doc="Price currency (ISO 4217 code)"
    )
    
    # Inventory tracking
    stock_quantity = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Current stock quantity"
    )
    
    sales_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of books sold"
    )
    
    # Relationships
    author = relationship(
        "AuthorModel",
        back_populates="books",
        lazy="select",
        doc="Author who wrote this book"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_book_title', 'title'),
        Index('idx_book_author_active', 'author_id', 'is_active'),
        Index('idx_book_genre_active', 'genre', 'is_active'),
        Index('idx_book_publication_date', 'publication_date'),
        Index('idx_book_stock_active', 'stock_quantity', 'is_active'),
        Index('idx_book_price_range', 'price_amount', 'price_currency'),
    )
    
    def __repr__(self):
        return f"<BookModel(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"
```

### Tortoise ORM Alternative (if using Tortoise instead of SQLAlchemy)

```python
# models/tortoise_author_model.py
from tortoise.models import Model
from tortoise import fields
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .book_model import BookModel

class AuthorModel(Model):
    """
    Tortoise ORM model for Author entity.
    
    Alternative implementation using Tortoise ORM
    for async database operations.
    """
    
    id = fields.UUIDField(pk=True)
    
    # Name fields
    first_name = fields.CharField(max_length=50, description="Author's first name")
    last_name = fields.CharField(max_length=50, description="Author's last name")
    middle_name = fields.CharField(max_length=50, null=True, description="Author's middle name")
    
    # Contact information
    email = fields.CharField(max_length=254, unique=True, null=True, description="Author's email")
    
    # Profile information
    bio = fields.TextField(null=True, description="Author's biography")
    birth_date = fields.DateField(null=True, description="Author's birth date")
    nationality = fields.CharField(max_length=100, null=True, description="Author's nationality")
    
    # Status and timestamps
    is_active = fields.BooleanField(default=True, description="Active status")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    # Relationships
    books: fields.ReverseRelation["BookModel"]
    
    class Meta:
        table = "authors"
        indexes = [
            ("last_name", "first_name"),
            ("nationality", "is_active"),
            ("email", "is_active"),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
```

## 🧪 Testing Models

```python
# tests/unit/models/test_author_model.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from models.base_model import Base
from models.author_model import AuthorModel

class TestAuthorModel:
    @pytest.fixture
    def db_session(self):
        """Create in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_create_author_model(self, db_session):
        """Test creating an author model."""
        author = AuthorModel(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            bio="A great author",
            nationality="American"
        )
        
        db_session.add(author)
        db_session.commit()
        
        assert author.id is not None
        assert author.first_name == "John"
        assert author.last_name == "Doe"
        assert author.is_active is True
        assert author.created_at is not None
    
    def test_author_model_unique_email_constraint(self, db_session):
        """Test that email uniqueness is enforced."""
        author1 = AuthorModel(
            first_name="John",
            last_name="Doe",
            email="same@example.com"
        )
        
        author2 = AuthorModel(
            first_name="Jane",
            last_name="Smith",
            email="same@example.com"
        )
        
        db_session.add(author1)
        db_session.commit()
        
        db_session.add(author2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
```

## ✅ Best Practices

### Model Design
- **Use descriptive table and column names** that match domain concepts
- **Add appropriate indexes** for common query patterns
- **Set up proper constraints** (unique, foreign key, check constraints)
- **Include documentation** in column definitions
- **Use appropriate data types** for each field

### Relationships
- **Define relationships clearly** with proper back references
- **Use appropriate lazy loading** strategies
- **Set up cascade options** for related data
- **Consider performance implications** of relationship loading

### Database Optimization
- **Create indexes** for frequently queried columns
- **Use composite indexes** for multi-column queries
- **Consider partitioning** for large tables
- **Monitor query performance** and optimize as needed

## ❌ Common Pitfalls

- **Exposing models directly** to other layers - use repositories instead
- **Missing indexes** on frequently queried columns
- **Inappropriate data types** for business requirements
- **Not handling database migrations** properly
- **Tight coupling** between models and business logic

## 🔄 Integration Points

Models integrate with:
- **Repository Layer** - Used by repositories for data persistence
- **Infrastructure Layer** - Part of database infrastructure
- **Migration System** - Define database schema changes
- **ORM Framework** - Provide database abstraction

The models directory is crucial for data persistence, providing the database representation of your domain entities while keeping database concerns separate from business logic.

