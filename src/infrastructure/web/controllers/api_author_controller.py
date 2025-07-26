"""API controller for author management.

This controller demonstrates how to implement REST API endpoints while maintaining
hexagonal architecture principles. It acts as an adapter in the infrastructure
layer, converting HTTP requests to use case calls and formatting responses.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.use_cases.create_author import CreateAuthorUseCase, CreateAuthorRequest
from src.application.use_cases.get_author import GetAuthorUseCase
from src.application.use_cases.list_authors import ListAuthorsUseCase
from src.application.use_cases.update_author import UpdateAuthorUseCase, UpdateAuthorRequest
from src.application.use_cases.delete_author import DeleteAuthorUseCase
from src.infrastructure.dependencies import get_author_use_cases

# Initialize router
router = APIRouter(prefix="/api/v1/authors", tags=["authors"])


# API Request/Response Models (Infrastructure Layer)
class CreateAuthorAPIRequest(BaseModel):
    """API request model for creating authors.
    
    This model is part of the infrastructure layer and handles
    API-specific concerns like validation and serialization.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Author's name")


class UpdateAuthorAPIRequest(BaseModel):
    """API request model for updating authors."""
    name: str = Field(..., min_length=1, max_length=100, description="Author's updated name")


class AuthorAPIResponse(BaseModel):
    """API response model for authors.
    
    This model transforms domain entities into API-friendly format,
    maintaining separation between domain and infrastructure concerns.
    """
    id: str = Field(..., description="Author's unique identifier")
    name: str = Field(..., description="Author's name")
    book_count: int = Field(..., description="Number of books by this author")
    book_ids: List[str] = Field(default_factory=list, description="List of book IDs")


class AuthorListAPIResponse(BaseModel):
    """API response model for author lists."""
    authors: List[AuthorAPIResponse] = Field(..., description="List of authors")
    total: int = Field(..., description="Total number of authors")


class APIErrorResponse(BaseModel):
    """Standard API error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


# API Endpoints
@router.post(
    "/",
    response_model=AuthorAPIResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": APIErrorResponse, "description": "Invalid input"},
        409: {"model": APIErrorResponse, "description": "Author already exists"}
    }
)
async def create_author(
    request: CreateAuthorAPIRequest,
    use_cases = Depends(get_author_use_cases)
) -> AuthorAPIResponse:
    """Create a new author.
    
    This endpoint demonstrates the hexagonal architecture flow:
    1. API request validation (Infrastructure)
    2. Use case request creation (Application)
    3. Domain validation and business logic (Domain)
    4. Repository persistence (Infrastructure)
    5. Response transformation (Infrastructure)
    
    Args:
        request: Author creation request
        use_cases: Injected use cases
        
    Returns:
        Created author data
        
    Raises:
        HTTPException: If validation fails or author already exists
    """
    
    # Convert API request to use case request
    use_case_request = CreateAuthorRequest(name=request.name)
    
    # Execute use case
    response = await use_cases.create_author.execute(use_case_request)
    
    if not response.success:
        # Determine appropriate HTTP status code
        if "already exists" in response.message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=response.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
    
    # Transform domain entity to API response
    return AuthorAPIResponse(
        id=str(response.author.id),
        name=response.author.name.value,
        book_count=len(response.author.book_ids),
        book_ids=[str(book_id) for book_id in response.author.book_ids]
    )


@router.get(
    "/",
    response_model=AuthorListAPIResponse,
    responses={
        500: {"model": APIErrorResponse, "description": "Internal server error"}
    }
)
async def list_authors(
    use_cases = Depends(get_author_use_cases)
) -> AuthorListAPIResponse:
    """List all authors.
    
    This endpoint shows:
    1. Simple use case execution
    2. Domain entity transformation
    3. Structured API response
    
    Args:
        use_cases: Injected use cases
        
    Returns:
        List of all authors
    """
    
    # Execute use case
    response = await use_cases.list_authors.execute()
    
    # Transform domain entities to API responses
    authors_data = [
        AuthorAPIResponse(
            id=str(author.id),
            name=author.name.value,
            book_count=len(author.book_ids),
            book_ids=[str(book_id) for book_id in author.book_ids]
        )
        for author in response.authors
    ]
    
    return AuthorListAPIResponse(
        authors=authors_data,
        total=len(authors_data)
    )


@router.get(
    "/{author_id}",
    response_model=AuthorAPIResponse,
    responses={
        404: {"model": APIErrorResponse, "description": "Author not found"},
        400: {"model": APIErrorResponse, "description": "Invalid author ID"}
    }
)
async def get_author(
    author_id: UUID,
    use_cases = Depends(get_author_use_cases)
) -> AuthorAPIResponse:
    """Get author by ID.
    
    This endpoint demonstrates:
    1. URL parameter validation
    2. Use case execution with parameters
    3. Error handling for not found cases
    4. Domain to API transformation
    
    Args:
        author_id: Author's unique identifier
        use_cases: Injected use cases
        
    Returns:
        Author data
        
    Raises:
        HTTPException: If author not found or invalid ID
    """
    
    # Execute use case
    response = await use_cases.get_author.execute(author_id)
    
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    
    # Transform domain entity to API response
    return AuthorAPIResponse(
        id=str(response.author.id),
        name=response.author.name.value,
        book_count=len(response.author.book_ids),
        book_ids=[str(book_id) for book_id in response.author.book_ids]
    )


@router.put(
    "/{author_id}",
    response_model=AuthorAPIResponse,
    responses={
        404: {"model": APIErrorResponse, "description": "Author not found"},
        400: {"model": APIErrorResponse, "description": "Invalid input"}
    }
)
async def update_author(
    author_id: UUID,
    request: UpdateAuthorAPIRequest,
    use_cases = Depends(get_author_use_cases)
) -> AuthorAPIResponse:
    """Update author by ID.
    
    This endpoint shows:
    1. Combined path and body parameters
    2. Use case request creation
    3. Domain validation
    4. Response transformation
    
    Args:
        author_id: Author's unique identifier
        request: Author update request
        use_cases: Injected use cases
        
    Returns:
        Updated author data
        
    Raises:
        HTTPException: If author not found or validation fails
    """
    
    # Convert API request to use case request
    use_case_request = UpdateAuthorRequest(
        author_id=author_id,
        name=request.name
    )
    
    # Execute use case
    response = await use_cases.update_author.execute(use_case_request)
    
    if not response.success:
        if "not found" in response.message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
    
    # Transform domain entity to API response
    return AuthorAPIResponse(
        id=str(response.author.id),
        name=response.author.name.value,
        book_count=len(response.author.book_ids),
        book_ids=[str(book_id) for book_id in response.author.book_ids]
    )


@router.delete(
    "/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": APIErrorResponse, "description": "Author not found"},
        409: {"model": APIErrorResponse, "description": "Author has associated books"}
    }
)
async def delete_author(
    author_id: UUID,
    use_cases = Depends(get_author_use_cases)
):
    """Delete author by ID.
    
    This endpoint demonstrates:
    1. DELETE operation handling
    2. Business rule validation (can't delete author with books)
    3. Appropriate HTTP status codes
    4. No content response
    
    Args:
        author_id: Author's unique identifier
        use_cases: Injected use cases
        
    Raises:
        HTTPException: If author not found or has associated books
    """
    
    # Execute use case
    response = await use_cases.delete_author.execute(author_id)
    
    if not response.success:
        if "not found" in response.message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response.message
            )
        elif "books" in response.message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=response.message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.message
            )
    
    # Return 204 No Content (no response body needed)

