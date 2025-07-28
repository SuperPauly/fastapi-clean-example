# Schemas Directory (`schemas/`)

The **Schemas Directory** contains data validation and serialization models that define the structure of data flowing between different layers of the application. In hexagon architecture, schemas act as **data contracts** that ensure type safety and validation across layer boundaries.

## 🎯 Purpose & Role in Hexagon Architecture

Schemas serve as **data transformation and validation layers** that:
- **Define API contracts** for request/response structures
- **Validate input data** before it reaches business logic
- **Transform data** between external and internal representations
- **Provide type safety** across application boundaries
- **Document data structures** for API consumers

```
External Data → Schema Validation → Internal Processing → Schema Serialization → Response
      ↓              ↓                      ↓                    ↓               ↑
   JSON/XML → Pydantic Models → Domain Objects → Response Models → JSON/XML
```

## 🏗️ Key Responsibilities

### 1. **Input Validation**
- Validate request data types and formats
- Enforce business constraints at the API boundary
- Provide clear error messages for invalid data

### 2. **Data Transformation**
- Convert between external and internal data formats
- Handle serialization and deserialization
- Map between different data representations

### 3. **API Documentation**
- Automatically generate API documentation
- Define clear contracts for API consumers
- Specify required and optional fields

## 📁 Schema Structure

```
schemas/
├── pydantic/               # Pydantic models for FastAPI
│   ├── author_schemas.py   # Author request/response models
│   ├── book_schemas.py     # Book request/response models
│   └── common_schemas.py   # Shared/common models
├── graphql/               # GraphQL schema definitions
│   ├── author_types.py    # Author GraphQL types
│   └── book_types.py      # Book GraphQL types
└── README.md              # This file
```

## 🔧 Implementation Examples

### Pydantic Schemas for REST API

```python
# schemas/pydantic/author_schemas.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class AuthorCreateRequest(BaseModel):
    """Schema for creating a new author."""
    
    first_name: str = Field(
        ..., 
        min_length=2, 
        max_length=50,
        description="Author's first name"
    )
    last_name: str = Field(
        ..., 
        min_length=2, 
        max_length=50,
        description="Author's last name"
    )
    middle_name: Optional[str] = Field(
        None, 
        max_length=50,
        description="Author's middle name (optional)"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Author's email address"
    )
    bio: Optional[str] = Field(
        None, 
        max_length=2000,
        description="Author's biography"
    )
    birth_date: Optional[date] = Field(
        None,
        description="Author's birth date"
    )
    nationality: Optional[str] = Field(
        None, 
        max_length=100,
        description="Author's nationality"
    )
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v and v > date.today():
            raise ValueError('Birth date cannot be in the future')
        if v and v.year < 1900:
            raise ValueError('Birth date cannot be before 1900')
        return v
    
    @validator('bio')
    def validate_bio(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('Bio must be at least 10 characters long')
        return v.strip() if v else None
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "middle_name": "Michael",
                "email": "john.doe@example.com",
                "bio": "John Doe is a renowned author of fantasy novels with over 20 years of experience.",
                "birth_date": "1980-05-15",
                "nationality": "American"
            }
        }

class AuthorUpdateRequest(BaseModel):
    """Schema for updating an existing author."""
    
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    bio: Optional[str] = Field(None, max_length=2000)
    birth_date: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    
    @validator('bio')
    def validate_bio(cls, v):
        if v is not None and len(v.strip()) < 10:
            raise ValueError('Bio must be at least 10 characters long')
        return v.strip() if v else None

class AuthorResponse(BaseModel):
    """Schema for author response data."""
    
    id: UUID
    name: str = Field(description="Author's full name")
    email: Optional[str] = Field(description="Author's email address")
    bio: Optional[str] = Field(description="Author's biography")
    nationality: Optional[str] = Field(description="Author's nationality")
    is_active: bool = Field(description="Whether the author is active")
    books_count: int = Field(description="Number of books by this author")
    total_sales: int = Field(description="Total sales across all books")
    created_at: datetime = Field(description="When the author was created")
    updated_at: datetime = Field(description="When the author was last updated")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Michael Doe",
                "email": "john.doe@example.com",
                "bio": "John Doe is a renowned author of fantasy novels.",
                "nationality": "American",
                "is_active": True,
                "books_count": 5,
                "total_sales": 15000,
                "created_at": "2023-01-15T10:30:00Z",
                "updated_at": "2023-06-20T14:45:00Z"
            }
        }

class AuthorListResponse(BaseModel):
    """Schema for paginated author list response."""
    
    authors: List[AuthorResponse]
    total_count: int = Field(description="Total number of authors")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    
    class Config:
        schema_extra = {
            "example": {
                "authors": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "is_active": True,
                        "books_count": 3,
                        "total_sales": 5000
                    }
                ],
                "total_count": 150,
                "page": 1,
                "page_size": 20,
                "total_pages": 8
            }
        }
```

### Book Schemas

```python
# schemas/pydantic/book_schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal

class BookCreateRequest(BaseModel):
    """Schema for creating a new book."""
    
    title: str = Field(..., min_length=1, max_length=200)
    isbn: str = Field(..., regex=r'^978-\d{10}$')
    author_id: UUID = Field(..., description="ID of the book's author")
    price: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", regex=r'^[A-Z]{3}$')
    publication_date: Optional[date] = None
    page_count: Optional[int] = Field(None, gt=0)
    genre: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    initial_stock: Optional[int] = Field(default=0, ge=0)
    
    @validator('publication_date')
    def validate_publication_date(cls, v):
        if v and v > date.today():
            raise ValueError('Publication date cannot be in the future')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "The Great Adventure",
                "isbn": "978-0123456789",
                "author_id": "123e4567-e89b-12d3-a456-426614174000",
                "price": 24.99,
                "currency": "USD",
                "publication_date": "2023-06-15",
                "page_count": 350,
                "genre": "Fantasy",
                "description": "An epic fantasy adventure...",
                "initial_stock": 100
            }
        }

class BookResponse(BaseModel):
    """Schema for book response data."""
    
    id: UUID
    title: str
    isbn: str
    author_id: UUID
    author_name: str = Field(description="Author's full name")
    price: Decimal
    currency: str
    publication_date: Optional[date]
    page_count: Optional[int]
    genre: Optional[str]
    description: Optional[str]
    stock_quantity: int
    is_active: bool
    availability_status: str = Field(description="Human-readable availability status")
    created_at: datetime
    updated_at: datetime

class BookSearchFilters(BaseModel):
    """Schema for book search filters."""
    
    genre: Optional[str] = None
    author_id: Optional[UUID] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    in_stock_only: bool = False
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v

class BookListResponse(BaseModel):
    """Schema for paginated book list response."""
    
    books: List[BookResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
```

### Common/Shared Schemas

```python
# schemas/pydantic/common_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

class ErrorDetail(BaseModel):
    """Schema for error details."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(description="Error message")
    code: Optional[str] = Field(None, description="Error code")

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    message: str = Field(description="Main error message")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Validation failed",
                "errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_EMAIL"
                    }
                ],
                "timestamp": "2023-06-20T14:45:00Z"
            }
        }

class SuccessResponse(BaseModel):
    """Schema for success responses."""
    
    message: str = Field(description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

class SortOrder(str, Enum):
    """Enumeration for sort orders."""
    ASC = "asc"
    DESC = "desc"

class SortParams(BaseModel):
    """Schema for sorting parameters."""
    
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")
```

### GraphQL Schema Example

```python
# schemas/graphql/author_types.py
import strawberry
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

@strawberry.type
class Author:
    """GraphQL type for Author."""
    
    id: UUID
    name: str
    email: Optional[str]
    bio: Optional[str]
    nationality: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

@strawberry.input
class AuthorInput:
    """GraphQL input type for creating/updating authors."""
    
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: Optional[str] = None

@strawberry.type
class AuthorConnection:
    """GraphQL connection type for paginated author results."""
    
    authors: List[Author]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
```

## 🧪 Testing Schemas

```python
# tests/unit/schemas/test_author_schemas.py
import pytest
from datetime import date
from pydantic import ValidationError

from schemas.pydantic.author_schemas import AuthorCreateRequest, AuthorUpdateRequest

class TestAuthorSchemas:
    def test_author_create_request_valid_data(self):
        """Test AuthorCreateRequest with valid data."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "bio": "A great author with many years of experience."
        }
        
        schema = AuthorCreateRequest(**data)
        
        assert schema.first_name == "John"
        assert schema.last_name == "Doe"
        assert schema.email == "john@example.com"
    
    def test_author_create_request_invalid_email(self):
        """Test AuthorCreateRequest with invalid email."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AuthorCreateRequest(**data)
        
        assert "email" in str(exc_info.value)
    
    def test_author_create_request_short_bio(self):
        """Test AuthorCreateRequest with bio too short."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "bio": "Short"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AuthorCreateRequest(**data)
        
        assert "at least 10 characters" in str(exc_info.value)
    
    def test_author_create_request_future_birth_date(self):
        """Test AuthorCreateRequest with future birth date."""
        from datetime import date, timedelta
        
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": date.today() + timedelta(days=1)
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AuthorCreateRequest(**data)
        
        assert "future" in str(exc_info.value)
```

## ✅ Best Practices

### Schema Design
- **Use descriptive field names** that match domain language
- **Provide clear validation messages** for better user experience
- **Include examples** in schema configuration for documentation
- **Use appropriate data types** (EmailStr, UUID, etc.)
- **Implement custom validators** for business rules

### Validation Strategy
- **Validate at the boundary** - catch errors early
- **Provide specific error messages** for each validation rule
- **Use field constraints** (min_length, max_length, regex)
- **Implement cross-field validation** when needed

### Documentation
- **Add field descriptions** for API documentation
- **Provide schema examples** for better understanding
- **Document validation rules** clearly
- **Keep schemas up to date** with business requirements

## ❌ Common Pitfalls

- **Over-validating** - Don't duplicate domain validation in schemas
- **Under-validating** - Always validate external input
- **Inconsistent naming** - Use consistent field names across schemas
- **Missing examples** - Always provide schema examples
- **Tight coupling** - Don't expose internal domain structure directly

## 🔄 Integration Points

Schemas integrate with:
- **Presentation Layer** - Used in routers for request/response validation
- **Application Layer** - Transform between external and internal data
- **Infrastructure Layer** - Serialize/deserialize data for external services
- **Documentation** - Automatically generate API documentation

The schemas directory is essential for maintaining data integrity and providing clear contracts between your application and external consumers.

