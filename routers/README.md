# Routers Directory (`routers/`)

The **Routers Directory** contains FastAPI route definitions that handle HTTP requests and responses. In hexagon architecture, routers are part of the **presentation layer** - they serve as **adapters** that translate HTTP requests into application use cases and convert results back to HTTP responses.

## 🎯 Purpose & Role in Hexagon Architecture

Routers act as **HTTP adapters** that:
- **Handle HTTP requests** and route them to appropriate handlers
- **Validate request data** using Pydantic models
- **Call application use cases** to execute business logic
- **Transform responses** into appropriate HTTP formats
- **Manage HTTP-specific concerns** (status codes, headers, etc.)

```
HTTP Request → Router → Use Case → Domain Logic → Response
     ↓           ↓         ↓           ↓           ↑
   FastAPI → Validation → App Layer → Business → JSON
```

## 🏗️ Key Responsibilities

### 1. **Request Routing**
- Define URL patterns and HTTP methods
- Route requests to appropriate handler functions
- Handle path parameters and query strings

### 2. **Input Validation**
- Validate request bodies using Pydantic schemas
- Handle query parameters and path validation
- Provide clear error messages for invalid input

### 3. **Use Case Orchestration**
- Call appropriate application use cases
- Handle dependency injection for services
- Manage request/response lifecycle

### 4. **Response Formatting**
- Convert domain objects to API responses
- Set appropriate HTTP status codes
- Handle error responses and exceptions

## 📁 Router Structure

```
routers/
├── v1/                      # API version 1 routes
│   ├── authors.py          # Author-related endpoints
│   ├── books.py            # Book-related endpoints
│   └── __init__.py
├── health.py               # Health check endpoints
├── __init__.py
└── README.md               # This file
```

## 🔧 Implementation Examples

### Author Router with Full CRUD Operations

```python
# routers/v1/authors.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID

from ...src.application.use_cases.create_author import CreateAuthorUseCase, CreateAuthorCommand
from ...src.application.use_cases.update_author import UpdateAuthorUseCase, UpdateAuthorCommand
from ...src.application.services.author_service import AuthorManagementService
from ...schemas.pydantic.author_schemas import (
    AuthorCreateRequest,
    AuthorUpdateRequest, 
    AuthorResponse,
    AuthorListResponse
)
from ...infrastructure.dependencies import (
    get_create_author_use_case,
    get_update_author_use_case,
    get_author_management_service
)

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])

@router.post(
    "/",
    response_model=AuthorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new author",
    description="Create a new author with the provided information"
)
async def create_author(
    request: AuthorCreateRequest,
    use_case: CreateAuthorUseCase = Depends(get_create_author_use_case)
) -> AuthorResponse:
    """
    Create a new author.
    
    - **first_name**: Author's first name (required)
    - **last_name**: Author's last name (required)  
    - **email**: Author's email address (optional)
    - **bio**: Author's biography (optional)
    - **birth_date**: Author's birth date in ISO format (optional)
    - **nationality**: Author's nationality (optional)
    """
    # Convert request to command
    command = CreateAuthorCommand(
        first_name=request.first_name,
        last_name=request.last_name,
        middle_name=request.middle_name,
        email=request.email,
        bio=request.bio,
        birth_date=request.birth_date.isoformat() if request.birth_date else None,
        nationality=request.nationality
    )
    
    # Execute use case
    result = await use_case.execute(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": result.message,
                "errors": result.errors
            }
        )
    
    # Get created author for response
    service: AuthorManagementService = Depends(get_author_management_service)
    author_data = await service.get_author_profile(result.author_id)
    
    return AuthorResponse(**author_data)

@router.get(
    "/",
    response_model=AuthorListResponse,
    summary="List authors",
    description="Get a paginated list of authors with optional filtering"
)
async def list_authors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    nationality: Optional[str] = Query(None, description="Filter by nationality"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and bio"),
    service: AuthorManagementService = Depends(get_author_management_service)
) -> AuthorListResponse:
    """
    Get a list of authors with pagination and filtering.
    
    Query parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Number of items per page (default: 20, max: 100)
    - **nationality**: Filter by author nationality
    - **is_active**: Filter by active status (true/false)
    - **search**: Search in author name and biography
    """
    # Build filters
    filters = {}
    if nationality:
        filters["nationality"] = nationality
    if is_active is not None:
        filters["is_active"] = is_active
    
    # Execute search
    result = await service.search_authors(
        query=search or "",
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    return AuthorListResponse(
        authors=[AuthorResponse(**author) for author in result["authors"]],
        total_count=result["total_count"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"]
    )

@router.get(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Get author by ID",
    description="Retrieve a specific author by their unique identifier"
)
async def get_author(
    author_id: UUID,
    service: AuthorManagementService = Depends(get_author_management_service)
) -> AuthorResponse:
    """Get a specific author by ID."""
    author_data = await service.get_author_profile(author_id)
    
    if not author_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with ID {author_id} not found"
        )
    
    return AuthorResponse(**author_data)

@router.put(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Update author",
    description="Update an existing author's information"
)
async def update_author(
    author_id: UUID,
    request: AuthorUpdateRequest,
    use_case: UpdateAuthorUseCase = Depends(get_update_author_use_case),
    service: AuthorManagementService = Depends(get_author_management_service)
) -> AuthorResponse:
    """Update an existing author."""
    # Convert request to command
    command = UpdateAuthorCommand(
        author_id=author_id,
        **request.dict(exclude_unset=True)
    )
    
    # Execute use case
    result = await use_case.execute(command)
    
    if not result.success:
        if "not found" in result.message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": result.message,
                    "errors": result.errors
                }
            )
    
    # Get updated author for response
    author_data = await service.get_author_profile(author_id)
    return AuthorResponse(**author_data)

@router.delete(
    "/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete author",
    description="Deactivate an author (soft delete)"
)
async def delete_author(
    author_id: UUID,
    use_case: DeactivateAuthorUseCase = Depends(get_deactivate_author_use_case)
):
    """Deactivate an author (soft delete)."""
    result = await use_case.execute(author_id)
    
    if not result.success:
        if "not found" in result.message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )

@router.post(
    "/bulk",
    response_model=dict,
    summary="Bulk update authors",
    description="Update multiple authors in a single request"
)
async def bulk_update_authors(
    updates: List[AuthorUpdateRequest],
    service: AuthorManagementService = Depends(get_author_management_service)
) -> dict:
    """Update multiple authors in bulk."""
    # Convert requests to update data
    update_data = [
        {"id": str(update.id), **update.dict(exclude={"id"}, exclude_unset=True)}
        for update in updates
    ]
    
    result = await service.bulk_update_authors(update_data)
    
    return {
        "message": f"Bulk update completed: {result['successful_count']} successful, {result['failed_count']} failed",
        "successful_count": result["successful_count"],
        "failed_count": result["failed_count"],
        "failed_updates": result["failed_updates"]
    }
```

### Book Router with Advanced Features

```python
# routers/v1/books.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from ...src.application.use_cases.create_book import CreateBookUseCase, CreateBookCommand
from ...src.application.services.book_catalog_service import BookCatalogService
from ...schemas.pydantic.book_schemas import (
    BookCreateRequest,
    BookResponse,
    BookListResponse,
    BookSearchFilters
)
from ...infrastructure.dependencies import (
    get_create_book_use_case,
    get_book_catalog_service
)

router = APIRouter(prefix="/api/v1/books", tags=["books"])

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    request: BookCreateRequest,
    use_case: CreateBookUseCase = Depends(get_create_book_use_case)
) -> BookResponse:
    """Create a new book."""
    command = CreateBookCommand(
        title=request.title,
        isbn=request.isbn,
        author_id=request.author_id,
        price_amount=request.price,
        price_currency=request.currency or "USD",
        publication_date=request.publication_date.isoformat() if request.publication_date else None,
        page_count=request.page_count,
        genre=request.genre,
        description=request.description,
        initial_stock=request.initial_stock or 0
    )
    
    result = await use_case.execute(command)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": result.message, "errors": result.errors}
        )
    
    # Return created book data
    service: BookCatalogService = Depends(get_book_catalog_service)
    book_data = await service.get_book_details(result.book_id)
    
    return BookResponse(**book_data)

@router.get("/", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    genre: Optional[str] = Query(None),
    author_id: Optional[UUID] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    in_stock_only: bool = Query(False),
    search: Optional[str] = Query(None),
    service: BookCatalogService = Depends(get_book_catalog_service)
) -> BookListResponse:
    """List books with filtering and pagination."""
    filters = BookSearchFilters(
        genre=genre,
        author_id=author_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only
    )
    
    result = await service.search_books(
        query=search or "",
        filters=filters.dict(exclude_none=True),
        page=page,
        page_size=page_size
    )
    
    return BookListResponse(**result)

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    service: BookCatalogService = Depends(get_book_catalog_service)
) -> BookResponse:
    """Get a specific book by ID."""
    book_data = await service.get_book_details(book_id)
    
    if not book_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    return BookResponse(**book_data)

@router.get("/isbn/{isbn}", response_model=BookResponse)
async def get_book_by_isbn(
    isbn: str,
    service: BookCatalogService = Depends(get_book_catalog_service)
) -> BookResponse:
    """Get a book by its ISBN."""
    book_data = await service.find_book_by_isbn(isbn)
    
    if not book_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ISBN {isbn} not found"
        )
    
    return BookResponse(**book_data)

@router.patch("/{book_id}/stock")
async def update_book_stock(
    book_id: UUID,
    new_quantity: int = Query(..., ge=0),
    service: BookCatalogService = Depends(get_book_catalog_service)
):
    """Update book stock quantity."""
    success = await service.update_stock(book_id, new_quantity)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    return {"message": f"Stock updated to {new_quantity}"}
```

### Health Check Router (Simple Example)

```python
# routers/health.py
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

from ..infrastructure.dependencies import get_database_health, get_redis_health

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "FastAPI Clean Architecture Template"
    }

@router.get("/detailed")
async def detailed_health_check(
    db_health: Dict = Depends(get_database_health),
    redis_health: Dict = Depends(get_redis_health)
) -> Dict[str, Any]:
    """Detailed health check with dependency status."""
    overall_status = "healthy"
    
    if db_health["status"] != "healthy" or redis_health["status"] != "healthy":
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "database": db_health,
            "redis": redis_health
        }
    }
```

## 🧪 Testing Routers

```python
# tests/integration/routers/test_authors.py
import pytest
from httpx import AsyncClient
from fastapi import status

class TestAuthorRoutes:
    @pytest.mark.asyncio
    async def test_create_author_success(self, client: AsyncClient):
        """Test successful author creation."""
        author_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "bio": "A talented writer with years of experience."
        }
        
        response = await client.post("/api/v1/authors/", json=author_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@example.com"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_author_invalid_email(self, client: AsyncClient):
        """Test author creation with invalid email."""
        author_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email"
        }
        
        response = await client.post("/api/v1/authors/", json=author_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()["detail"]["errors"][0].lower()
    
    @pytest.mark.asyncio
    async def test_list_authors_with_pagination(self, client: AsyncClient):
        """Test author listing with pagination."""
        response = await client.get("/api/v1/authors/?page=1&page_size=10")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "authors" in data
        assert "total_count" in data
        assert "page" in data
        assert data["page"] == 1
```

## ✅ Best Practices

### Router Organization
- **Group related endpoints** in the same router file
- **Use consistent URL patterns** and naming conventions
- **Version your APIs** using prefixes like `/api/v1/`
- **Apply appropriate HTTP methods** (GET, POST, PUT, DELETE, PATCH)

### Request/Response Handling
- **Use Pydantic models** for request/response validation
- **Provide clear error messages** with appropriate HTTP status codes
- **Handle exceptions gracefully** with proper error responses
- **Document endpoints** with clear summaries and descriptions

### Dependency Management
- **Use FastAPI's dependency injection** for services and use cases
- **Keep routers thin** - delegate business logic to application layer
- **Handle authentication/authorization** through dependencies
- **Validate permissions** before executing operations

## ❌ Common Pitfalls

- **Putting business logic in routers** - Keep them focused on HTTP concerns
- **Not validating input properly** - Always use Pydantic models
- **Inconsistent error handling** - Standardize error response formats
- **Missing documentation** - Always document your endpoints
- **Not handling edge cases** - Consider all possible error scenarios

## 🔄 Integration Points

Routers integrate with:
- **Application Layer** - Call use cases and services
- **Schemas Directory** - Use Pydantic models for validation
- **Infrastructure Layer** - Access dependencies and services
- **Presentation Layer** - Part of the HTTP API interface

The routers directory is essential for exposing your application's functionality through HTTP APIs, providing a clean interface between web requests and your business logic.

