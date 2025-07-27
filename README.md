7# FastAPI Clean Architecture Template

A production-ready FastAPI template implementing **Hexagonal Architecture** (Ports and Adapters) with modern Python tooling and best practices.

## 🏗️ Architecture Overview

This template follows **Hexagonal Architecture** principles, ensuring clean separation of concerns and high testability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   FastAPI     │  │ PostgreSQL     │  │  Redis/Taskiq           │ │
│  │   Routes      │  │  Tortoise      │  │  Task Queue             │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Use Cases    │  │  Services      │  │      Ports             │ │
│  │               │  │                │  │   (Interfaces)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Entities     │  │    Value    b  │  │   Domain Services      │ │
│  │               │  │   Objects      │  │                        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis (for task queue)

### Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd fastapi-clean-example
```

2. **Install dependencies using Hatch:**
```bash
# Install Hatch if you haven't already
pip install hatch

# Create and activate development environment
hatch shell

# Or run commands directly
hatch run dev:python --version
```

3. **Configure environment:**
```bash
# Copy example settings
cp settings.toml.example settings.toml

# Update database and Redis settings in settings.toml
```

4. **Run the application:**
```bash
# Development mode
hatch run dev:uvicorn src.main:app --reload

# Production mode
hatch run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## 📁 Project Structure

```
src/
├── domain/                     # Domain Layer (Business Logic)
│   ├── entities/              # Business entities
│   ├── value_objects/         # Value objects
│   └── services/              # Domain services
├── application/               # Application Layer (Use Cases)
│   ├── use_cases/            # Application use cases
│   ├── services/             # Application services
│   └── ports/                # Interfaces/Ports
└── infrastructure/           # Infrastructure Layer (External Concerns)
    ├── web/                  # FastAPI routes and controllers
    ├── database/             # Database adapters
    ├── tasks/                # Task queue adapters
    ├── config/               # Configuration
    └── logging/              # Logging adapters
```

## 🎯 Hexagonal Architecture Principles

### 1. **Domain Layer** (Core Business Logic)
- Contains business entities, value objects, and domain services
- No dependencies on external frameworks
- Pure Python with business rules

### 2. **Application Layer** (Use Cases)
- Orchestrates domain objects to fulfill use cases
- Defines ports (interfaces) for external dependencies
- Contains application services and use cases

### 3. **Infrastructure Layer** (External Concerns)
- Implements adapters for ports defined in application layer
- Contains FastAPI routes, database repositories, task queues
- All external framework dependencies

## 📝 How to Add New Features

### Adding a New Entity

1. **Create Domain Entity:**
```python
# src/domain/entities/product.py
from uuid import UUID, uuid4
from typing import List
from pydantic import BaseModel, Field

from src.domain.value_objects.product_name import ProductName
from src.domain.value_objects.price import Price

class Product(BaseModel):
    """Product domain entity."""
    
    id: UUID = Field(default_factory=uuid4)
    name: ProductName = Field(...)
    price: Price = Field(...)
    category_ids: List[UUID] = Field(default_factory=list)
    
    model_config = {
        "frozen": False,
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
    }
```

2. **Create Value Objects:**
```python
# src/domain/value_objects/product_name.py
from pydantic import BaseModel, Field, validator

class ProductName(BaseModel):
    """Product name value object."""
    
    value: str = Field(..., min_length=1, max_length=100)
    
    @validator('value')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip().title()
    
    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }
```

3. **Create Repository Port:**
```python
# src/application/ports/product_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.product import Product

class ProductRepositoryPort(ABC):
    """Port for product repository operations."""
    
    @abstractmethod
    async def create(self, product: Product) -> Product:
        """Create a new product."""
        pass
    
    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Product]:
        """Get product by name."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Product]:
        """List all products."""
        pass
    
    @abstractmethod
    async def update(self, product: Product) -> Product:
        """Update existing product."""
        pass
    
    @abstractmethod
    async def delete(self, product_id: UUID) -> bool:
        """Delete product by ID."""
        pass
```

4. **Create Use Case:**
```python
# src/application/use_cases/create_product.py
from typing import Optional
from pydantic import BaseModel, Field, ValidationError

from src.application.ports.product_repository import ProductRepositoryPort
from src.application.ports.logger import LoggerPort
from src.domain.entities.product import Product
from src.domain.value_objects.product_name import ProductName
from src.domain.value_objects.price import Price

class CreateProductRequest(BaseModel):
    """Request to create a product."""
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)

class CreateProductResponse(BaseModel):
    """Response from creating a product."""
    product: Optional[Product] = Field(None)
    success: bool = Field(...)
    message: str = Field(...)
    
    model_config = {
        "arbitrary_types_allowed": True,
    }

class CreateProductUseCase:
    """Use case for creating a new product."""
    
    def __init__(
        self, 
        product_repository: ProductRepositoryPort,
        logger: LoggerPort
    ):
        self._product_repository = product_repository
        self._logger = logger
    
    async def execute(self, request: CreateProductRequest) -> CreateProductResponse:
        """Execute the create product use case."""
        try:
            # Create value objects
            product_name = ProductName(value=request.name)
            price = Price(value=request.price)
            
            # Check if product already exists
            existing_product = await self._product_repository.get_by_name(product_name.value)
            if existing_product:
                return CreateProductResponse(
                    product=existing_product,
                    success=False,
                    message=f"Product '{product_name.value}' already exists"
                )
            
            # Create new product
            product = Product(name=product_name, price=price)
            created_product = await self._product_repository.create(product)
            
            self._logger.info(f"Product created: {created_product.id}")
            
            return CreateProductResponse(
                product=created_product,
                success=True,
                message="Product created successfully"
            )
            
        except ValidationError as e:
            error_msg = f"Invalid product data: {e}"
            self._logger.error(error_msg)
            return CreateProductResponse(
                product=None,
                success=False,
                message=error_msg
            )
        except Exception as e:
            error_msg = f"Failed to create product: {str(e)}"
            self._logger.error(error_msg)
            return CreateProductResponse(
                product=None,
                success=False,
                message=error_msg
            )
```

### Adding FastAPI Routes (Following Hexagonal Principles)

1. **Create Route Controller:**
```python
# src/infrastructure/web/controllers/product_controller.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.application.use_cases.create_product import CreateProductUseCase, CreateProductRequest
from src.application.use_cases.get_product import GetProductUseCase
from src.application.use_cases.list_products import ListProductsUseCase
from src.infrastructure.dependencies import get_product_use_cases

router = APIRouter(prefix="/products", tags=["products"])

# Request/Response models for API
class CreateProductAPIRequest(BaseModel):
    """API request model for creating products."""
    name: str
    price: float

class ProductAPIResponse(BaseModel):
    """API response model for products."""
    id: str
    name: str
    price: float

@router.post("/", response_model=ProductAPIResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductAPIRequest,
    use_cases = Depends(get_product_use_cases)
) -> ProductAPIResponse:
    """Create a new product."""
    
    # Convert API request to use case request
    use_case_request = CreateProductRequest(
        name=request.name,
        price=request.price
    )
    
    # Execute use case
    response = await use_cases.create_product.execute(use_case_request)
    
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.message
        )
    
    # Convert domain entity to API response
    return ProductAPIResponse(
        id=str(response.product.id),
        name=response.product.name.value,
        price=response.product.price.value
    )

@router.get("/{product_id}", response_model=ProductAPIResponse)
async def get_product(
    product_id: UUID,
    use_cases = Depends(get_product_use_cases)
) -> ProductAPIResponse:
    """Get product by ID."""
    
    response = await use_cases.get_product.execute(product_id)
    
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.message
        )
    
    return ProductAPIResponse(
        id=str(response.product.id),
        name=response.product.name.value,
        price=response.product.price.value
    )

@router.get("/", response_model=List[ProductAPIResponse])
async def list_products(
    use_cases = Depends(get_product_use_cases)
) -> List[ProductAPIResponse]:
    """List all products."""
    
    response = await use_cases.list_products.execute()
    
    return [
        ProductAPIResponse(
            id=str(product.id),
            name=product.name.value,
            price=product.price.value
        )
        for product in response.products
    ]
```

2. **Create Dependency Injection:**
```python
# src/infrastructure/dependencies.py
from functools import lru_cache
from typing import NamedTuple

from src.application.use_cases.create_product import CreateProductUseCase
from src.application.use_cases.get_product import GetProductUseCase
from src.application.use_cases.list_products import ListProductsUseCase
from src.infrastructure.database.repositories.product_repository import ProductRepository
from src.infrastructure.logging.logger_adapter import LoguruLoggerAdapter

class ProductUseCases(NamedTuple):
    """Container for product use cases."""
    create_product: CreateProductUseCase
    get_product: GetProductUseCase
    list_products: ListProductsUseCase

@lru_cache()
def get_product_use_cases() -> ProductUseCases:
    """Get product use cases with dependencies."""
    
    # Infrastructure adapters
    product_repository = ProductRepository()
    logger = LoguruLoggerAdapter()
    
    # Use cases
    return ProductUseCases(
        create_product=CreateProductUseCase(product_repository, logger),
        get_product=GetProductUseCase(product_repository, logger),
        list_products=ListProductsUseCase(product_repository, logger)
    )
```

3. **Register Routes:**
```python
# src/infrastructure/web/api.py
from fastapi import APIRouter

from src.infrastructure.web.controllers.product_controller import router as product_router
from src.infrastructure.web.controllers.author_controller import router as author_router

api_router = APIRouter(prefix="/api/v1")

# Register all route controllers
api_router.include_router(product_router)
api_router.include_router(author_router)
```

### Adding Jinja2 Templates (Web Interface)

1. **Create Template Controller:**
```python
# src/infrastructure/web/controllers/web_controller.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.application.use_cases.create_product import CreateProductUseCase, CreateProductRequest
from src.application.use_cases.list_products import ListProductsUseCase
from src.infrastructure.dependencies import get_product_use_cases

router = APIRouter(prefix="/web", tags=["web"])
templates = Jinja2Templates(directory="templates")

@router.get("/products", response_class=HTMLResponse)
async def products_page(
    request: Request,
    use_cases = Depends(get_product_use_cases)
):
    """Display products page."""
    
    # Get products using use case
    response = await use_cases.list_products.execute()
    
    return templates.TemplateResponse(
        "products/list.html",
        {
            "request": request,
            "products": [
                {
                    "id": str(product.id),
                    "name": product.name.value,
                    "price": product.price.value
                }
                for product in response.products
            ],
            "title": "Products"
        }
    )

@router.get("/products/create", response_class=HTMLResponse)
async def create_product_page(request: Request):
    """Display create product form."""
    
    return templates.TemplateResponse(
        "products/create.html",
        {
            "request": request,
            "title": "Create Product"
        }
    )

@router.post("/products/create", response_class=HTMLResponse)
async def create_product_form(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    use_cases = Depends(get_product_use_cases)
):
    """Handle create product form submission."""
    
    # Create use case request
    use_case_request = CreateProductRequest(name=name, price=price)
    
    # Execute use case
    response = await use_cases.create_product.execute(use_case_request)
    
    if response.success:
        # Redirect to products list on success
        return templates.TemplateResponse(
            "products/create.html",
            {
                "request": request,
                "title": "Create Product",
                "success_message": response.message
            }
        )
    else:
        # Show form with error
        return templates.TemplateResponse(
            "products/create.html",
            {
                "request": request,
                "title": "Create Product",
                "error_message": response.message,
                "form_data": {"name": name, "price": price}
            }
        )
```

2. **Create Jinja2 Templates:**

**Base Template:**
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}FastAPI Clean Architecture{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">FastAPI Clean Architecture</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/web/products">Products</a>
                <a class="nav-link" href="/web/authors">Authors</a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% if success_message %}
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            {{ success_message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endif %}

        {% if error_message %}
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            {{ error_message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endif %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

**Products List Template:**
```html
<!-- templates/products/list.html -->
{% extends "base.html" %}

{% block title %}{{ title }} - FastAPI Clean Architecture{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1>{{ title }}</h1>
    <a href="/web/products/create" class="btn btn-primary">Create Product</a>
</div>

<div class="row">
    {% for product in products %}
    <div class="col-md-4 mb-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">{{ product.name }}</h5>
                <p class="card-text">
                    <strong>Price:</strong> ${{ "%.2f"|format(product.price) }}
                </p>
                <p class="card-text">
                    <small class="text-muted">ID: {{ product.id }}</small>
                </p>
            </div>
        </div>
    </div>
    {% else %}
    <div class="col-12">
        <div class="alert alert-info">
            No products found. <a href="/web/products/create">Create one now</a>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

**Create Product Template:**
```html
<!-- templates/products/create.html -->
{% extends "base.html" %}

{% block title %}{{ title }} - FastAPI Clean Architecture{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <h1>{{ title }}</h1>
        
        <form method="post" action="/web/products/create">
            <div class="mb-3">
                <label for="name" class="form-label">Product Name</label>
                <input 
                    type="text" 
                    class="form-control" 
                    id="name" 
                    name="name" 
                    value="{{ form_data.name if form_data else '' }}"
                    required
                >
            </div>
            
            <div class="mb-3">
                <label for="price" class="form-label">Price</label>
                <input 
                    type="number" 
                    step="0.01" 
                    min="0.01"
                    class="form-control" 
                    id="price" 
                    name="price" 
                    value="{{ form_data.price if form_data else '' }}"
                    required
                >
            </div>
            
            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">Create Product</button>
                <a href="/web/products" class="btn btn-secondary">Cancel</a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```

3. **Configure Templates in Main App:**
```python
# src/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.infrastructure.web.api import api_router
from src.infrastructure.web.controllers.web_controller import router as web_router

app = FastAPI(title="FastAPI Clean Architecture")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(api_router)

# Include web routes
app.include_router(web_router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FastAPI Clean Architecture Template"}
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
hatch run test:pytest

# Run with coverage
hatch run test:pytest --cov=src --cov-report=html

# Run specific test file
hatch run test:pytest tests/test_use_cases.py

# Run with verbose output
hatch run test:pytest -v
```

### Writing Tests Following Hexagonal Principles

```python
# tests/test_create_product_use_case.py
import pytest
from unittest.mock import AsyncMock

from src.application.use_cases.create_product import CreateProductUseCase, CreateProductRequest
from src.domain.entities.product import Product
from src.domain.value_objects.product_name import ProductName
from src.domain.value_objects.price import Price

@pytest.mark.asyncio
async def test_create_product_success(mock_product_repository, mock_logger):
    """Test successful product creation."""
    
    # Arrange
    mock_product_repository.get_by_name.return_value = None
    mock_product_repository.create.return_value = Product(
        name=ProductName(value="Test Product"),
        price=Price(value=99.99)
    )
    
    use_case = CreateProductUseCase(mock_product_repository, mock_logger)
    request = CreateProductRequest(name="Test Product", price=99.99)
    
    # Act
    response = await use_case.execute(request)
    
    # Assert
    assert response.success is True
    assert response.product is not None
    assert response.product.name.value == "Test Product"
    assert response.product.price.value == 99.99
    mock_product_repository.create.assert_called_once()
    mock_logger.info.assert_called()

@pytest.mark.asyncio
async def test_create_product_already_exists(mock_product_repository, mock_logger):
    """Test product creation when product already exists."""
    
    # Arrange
    existing_product = Product(
        name=ProductName(value="Existing Product"),
        price=Price(value=50.00)
    )
    mock_product_repository.get_by_name.return_value = existing_product
    
    use_case = CreateProductUseCase(mock_product_repository, mock_logger)
    request = CreateProductRequest(name="Existing Product", price=99.99)
    
    # Act
    response = await use_case.execute(request)
    
    # Assert
    assert response.success is False
    assert "already exists" in response.message
    mock_product_repository.create.assert_not_called()
```

## 🔧 Development Tools

### Code Quality
```bash
# Format code with Ruff
hatch run dev:ruff format .

# Lint code with Ruff
hatch run dev:ruff check .

# Type check with MyPy
hatch run dev:mypy src/

# Run pre-commit hooks
hatch run dev:pre-commit run --all-files
```

### Task Queue
```bash
# Start Taskiq worker
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker

# Monitor tasks
hatch run taskiq monitor src.infrastructure.tasks.taskiq_adapter:broker
```

## 📚 Key Benefits of This Architecture

1. **🔄 Testability**: Easy to mock dependencies and test business logic in isolation
2. **🔧 Maintainability**: Clear separation of concerns makes code easier to understand and modify
3. **🚀 Scalability**: Can easily swap implementations without affecting business logic
4. **🛡️ Flexibility**: Framework-agnostic domain layer protects against technology changes
5. **📈 Extensibility**: Easy to add new features following established patterns

## 🤝 Contributing

1. Follow the hexagonal architecture principles
2. Write tests for all new features
3. Use Pydantic for data validation
4. Keep domain logic pure (no external dependencies)
5. Use dependency injection for all external services

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

