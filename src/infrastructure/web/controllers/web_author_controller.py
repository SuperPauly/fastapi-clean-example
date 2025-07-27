"""Web controller for author management using Jinja2 templates.

This controller demonstrates how to implement web interfaces while maintaining
hexagonal architecture principles. It acts as an adapter in the infrastructure
layer, converting web requests to use case calls and rendering responses.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.application.use_cases.create_author import CreateAuthorUseCase, CreateAuthorRequest
from src.application.use_cases.get_author import GetAuthorUseCase
from src.application.use_cases.list_authors import ListAuthorsUseCase
from src.infrastructure.dependencies import get_author_use_cases
from src.infrastructure.rate_limiting.decorators import rate_limit

# Initialize router and templates
router = APIRouter(prefix="/web/authors", tags=["web-authors"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
@rate_limit("50/minute")  # Allow 50 page views per minute per IP
async def authors_list_page(
    request: Request,
    use_cases = Depends(get_author_use_cases)
):
    """Display authors list page.
    
    This endpoint demonstrates:
    1. Web layer (Jinja2 template)
    2. Use case execution (ListAuthorsUseCase)
    3. Data transformation for presentation
    """
    
    # Execute use case to get authors
    response = await use_cases.list_authors.execute()
    
    # Transform domain entities for template
    authors_data = []
    total_books = 0
    
    for author in response.authors:
        book_count = len(author.book_ids)
        total_books += book_count
        
        authors_data.append({
            "id": str(author.id),
            "name": author.name.value,
            "book_count": book_count
        })
    
    return templates.TemplateResponse(
        "authors/list.html",
        {
            "request": request,
            "title": "Authors",
            "authors": authors_data,
            "total_books": total_books
        }
    )


@router.get("/create", response_class=HTMLResponse)
@rate_limit("20/minute")  # Allow 20 form views per minute per IP
async def create_author_page(request: Request):
    """Display create author form.
    
    This endpoint shows the separation between:
    - Infrastructure layer (web controller)
    - Presentation layer (Jinja2 template)
    """
    
    return templates.TemplateResponse(
        "authors/create.html",
        {
            "request": request,
            "title": "Create Author"
        }
    )


@router.post("/create", response_class=HTMLResponse)
@rate_limit("5/minute")  # Allow 5 form submissions per minute per IP
async def create_author_form(
    request: Request,
    name: str = Form(...),
    use_cases = Depends(get_author_use_cases)
):
    """Handle create author form submission.
    
    This endpoint demonstrates the hexagonal architecture flow:
    1. Web form input (Infrastructure)
    2. Use case request creation (Application)
    3. Domain validation and business logic (Domain)
    4. Repository persistence (Infrastructure)
    5. Response rendering (Infrastructure)
    """
    
    try:
        # Create use case request from form data
        use_case_request = CreateAuthorRequest(name=name.strip())
        
        # Execute use case
        response = await use_cases.create_author.execute(use_case_request)
        
        if response.success:
            # Redirect to authors list on success
            return RedirectResponse(
                url="/web/authors",
                status_code=303
            )
        else:
            # Show form with error message
            return templates.TemplateResponse(
                "authors/create.html",
                {
                    "request": request,
                    "title": "Create Author",
                    "error_message": response.message,
                    "form_data": {"name": name}
                }
            )
            
    except ValueError as e:
        # Handle validation errors
        return templates.TemplateResponse(
            "authors/create.html",
            {
                "request": request,
                "title": "Create Author",
                "error_message": f"Invalid input: {str(e)}",
                "form_data": {"name": name},
                "form_errors": {"name": str(e)}
            }
        )
    except Exception as e:
        # Handle unexpected errors
        return templates.TemplateResponse(
            "authors/create.html",
            {
                "request": request,
                "title": "Create Author",
                "error_message": "An unexpected error occurred. Please try again.",
                "form_data": {"name": name}
            }
        )


@router.get("/{author_id}", response_class=HTMLResponse)
async def author_detail_page(
    request: Request,
    author_id: UUID,
    use_cases = Depends(get_author_use_cases)
):
    """Display author detail page.
    
    This endpoint shows:
    1. URL parameter handling
    2. Use case execution with parameters
    3. Error handling for not found cases
    4. Data transformation for templates
    """
    
    try:
        # Execute use case to get author
        response = await use_cases.get_author.execute(author_id)
        
        if not response.success:
            raise HTTPException(status_code=404, detail=response.message)
        
        # Transform domain entity for template
        author_data = {
            "id": str(response.author.id),
            "name": response.author.name.value,
            "book_count": len(response.author.book_ids),
            "book_ids": [str(book_id) for book_id in response.author.book_ids]
        }
        
        return templates.TemplateResponse(
            "authors/detail.html",
            {
                "request": request,
                "title": f"Author: {response.author.name.value}",
                "author": author_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return templates.TemplateResponse(
            "authors/list.html",
            {
                "request": request,
                "title": "Authors",
                "error_message": f"Error loading author: {str(e)}",
                "authors": []
            }
        )


# Additional endpoints for completeness
@router.get("/{author_id}/edit", response_class=HTMLResponse)
async def edit_author_page(
    request: Request,
    author_id: UUID,
    use_cases = Depends(get_author_use_cases)
):
    """Display edit author form."""
    
    # Get author for editing
    response = await use_cases.get_author.execute(author_id)
    
    if not response.success:
        return RedirectResponse(url="/web/authors", status_code=303)
    
    author_data = {
        "id": str(response.author.id),
        "name": response.author.name.value
    }
    
    return templates.TemplateResponse(
        "authors/edit.html",
        {
            "request": request,
            "title": f"Edit Author: {response.author.name.value}",
            "author": author_data
        }
    )
