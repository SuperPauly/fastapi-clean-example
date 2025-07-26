# Development Guide: Hexagonal Architecture with FastAPI

This guide provides detailed instructions for developing with this FastAPI template while maintaining hexagonal architecture principles.

## 🏗️ Architecture Layers

### Domain Layer (Core Business Logic)
**Location**: `src/domain/`
**Purpose**: Contains pure business logic, entities, value objects, and domain services
**Dependencies**: None (pure Python)

```python
# Example: Domain Entity
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class Author(BaseModel):
    """Author domain entity - pure business logic."""
    
    id: UUID = Field(default_factory=uuid4)
    name: AuthorName = Field(...)
    book_ids: List[UUID] = Field(default_factory=list)
    
    def add_book(self, book_id: UUID) -> None:
        """Business rule: Add book to author."""
        if book_id not in self.book_ids:
            self.book_ids.append(book_id)
    
    def can_be_deleted(self) -> bool:
        """Business rule: Author can only be deleted if no books."""
        return len(self.book_ids) == 0
```

### Application Layer (Use Cases)
**Location**: `src/application/`
**Purpose**: Orchestrates domain objects, defines ports (interfaces)
**Dependencies**: Domain layer only

```python
# Example: Use Case
class CreateAuthorUseCase:
    """Use case for creating authors - orchestrates domain logic."""
    
    def __init__(
        self,
        author_repository: AuthorRepositoryPort,  # Port (interface)
        logger: LoggerPort,                       # Port (interface)
        task_queue: TaskQueuePort                 # Port (interface)
    ):
        self._author_repository = author_repository
        self._logger = logger
        self._task_queue = task_queue
    
    async def execute(self, request: CreateAuthorRequest) -> CreateAuthorResponse:
        """Execute the use case."""
        # 1. Create domain entity
        author = Author(name=AuthorName(value=request.name))
        
        # 2. Apply business rules
        if await self._author_repository.exists_by_name(author.name.value):
            return CreateAuthorResponse(success=False, message="Author exists")
        
        # 3. Persist using port
        created_author = await self._author_repository.create(author)
        
        # 4. Trigger side effects
        await self._task_queue.enqueue(
            send_author_created_notification,
            str(created_author.id),
            created_author.name.value
        )
        
        return CreateAuthorResponse(success=True, author=created_author)
```

### Infrastructure Layer (External Concerns)
**Location**: `src/infrastructure/`
**Purpose**: Implements adapters for ports, handles external frameworks
**Dependencies**: Application and Domain layers

```python
# Example: Repository Adapter
class AuthorRepository(AuthorRepositoryPort):
    """Concrete implementation of AuthorRepositoryPort."""
    
    async def create(self, author: Author) -> Author:
        """Implement the port using Tortoise ORM."""
        author_model = AuthorModel(
            id=author.id,
            name=author.name.value
        )
        await author_model.save()
        return author
```

## 🚀 Development Workflow

### 1. Adding a New Feature

#### Step 1: Define Domain Entities and Value Objects
```python
# src/domain/entities/product.py
class Product(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: ProductName = Field(...)
    price: Price = Field(...)
    category_id: Optional[UUID] = Field(None)
    
    def apply_discount(self, percentage: float) -> None:
        """Business rule: Apply discount to product."""
        if 0 < percentage <= 100:
            discount_amount = self.price.value * (percentage / 100)
            new_price = self.price.value - discount_amount
            self.price = Price(value=new_price)

# src/domain/value_objects/price.py
class Price(BaseModel):
    value: float = Field(..., gt=0)
    
    @validator('value')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return round(v, 2)
    
    model_config = {"frozen": True}
```

#### Step 2: Define Repository Port
```python
# src/application/ports/product_repository.py
class ProductRepositoryPort(ABC):
    @abstractmethod
    async def create(self, product: Product) -> Product:
        pass
    
    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        pass
    
    @abstractmethod
    async def list_by_category(self, category_id: UUID) -> List[Product]:
        pass
```

#### Step 3: Create Use Cases
```python
# src/application/use_cases/create_product.py
class CreateProductUseCase:
    def __init__(
        self,
        product_repository: ProductRepositoryPort,
        logger: LoggerPort
    ):
        self._product_repository = product_repository
        self._logger = logger
    
    async def execute(self, request: CreateProductRequest) -> CreateProductResponse:
        # Validate business rules
        product = Product(
            name=ProductName(value=request.name),
            price=Price(value=request.price)
        )
        
        # Check business constraints
        existing = await self._product_repository.get_by_name(product.name.value)
        if existing:
            return CreateProductResponse(
                success=False,
                message="Product already exists"
            )
        
        # Persist
        created_product = await self._product_repository.create(product)
        
        self._logger.info(f"Product created: {created_product.id}")
        
        return CreateProductResponse(
            success=True,
            product=created_product
        )
```

#### Step 4: Implement Repository Adapter
```python
# src/infrastructure/database/repositories/product_repository.py
class ProductRepository(ProductRepositoryPort):
    async def create(self, product: Product) -> Product:
        product_model = ProductModel(
            id=product.id,
            name=product.name.value,
            price=product.price.value,
            category_id=product.category_id
        )
        await product_model.save()
        return product
    
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        try:
            model = await ProductModel.get(id=product_id)
            return Product(
                id=model.id,
                name=ProductName(value=model.name),
                price=Price(value=model.price),
                category_id=model.category_id
            )
        except DoesNotExist:
            return None
```

#### Step 5: Create API Controller
```python
# src/infrastructure/web/controllers/api_product_controller.py
@router.post("/", response_model=ProductAPIResponse)
async def create_product(
    request: CreateProductAPIRequest,
    use_cases = Depends(get_product_use_cases)
) -> ProductAPIResponse:
    # Convert API request to use case request
    use_case_request = CreateProductRequest(
        name=request.name,
        price=request.price
    )
    
    # Execute use case
    response = await use_cases.create_product.execute(use_case_request)
    
    if not response.success:
        raise HTTPException(status_code=400, detail=response.message)
    
    # Convert domain entity to API response
    return ProductAPIResponse(
        id=str(response.product.id),
        name=response.product.name.value,
        price=response.product.price.value
    )
```

#### Step 6: Create Web Controller (Optional)
```python
# src/infrastructure/web/controllers/web_product_controller.py
@router.post("/create")
async def create_product_form(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    use_cases = Depends(get_product_use_cases)
):
    use_case_request = CreateProductRequest(name=name, price=price)
    response = await use_cases.create_product.execute(use_case_request)
    
    if response.success:
        return RedirectResponse(url="/web/products", status_code=303)
    else:
        return templates.TemplateResponse(
            "products/create.html",
            {
                "request": request,
                "error_message": response.message,
                "form_data": {"name": name, "price": price}
            }
        )
```

#### Step 7: Update Dependencies
```python
# src/infrastructure/dependencies.py
@lru_cache()
def get_product_use_cases() -> ProductUseCases:
    product_repository = ProductRepository()
    logger = LoguruLoggerAdapter()
    
    return ProductUseCases(
        create_product=CreateProductUseCase(product_repository, logger),
        get_product=GetProductUseCase(product_repository, logger),
        list_products=ListProductsUseCase(product_repository, logger)
    )
```

### 2. Testing Strategy

#### Unit Tests (Domain Layer)
```python
# tests/domain/test_product.py
def test_product_apply_discount():
    """Test domain business logic."""
    product = Product(
        name=ProductName(value="Test Product"),
        price=Price(value=100.0)
    )
    
    product.apply_discount(10.0)
    
    assert product.price.value == 90.0

def test_price_validation():
    """Test value object validation."""
    with pytest.raises(ValueError):
        Price(value=-10.0)
```

#### Integration Tests (Use Cases)
```python
# tests/application/test_create_product_use_case.py
@pytest.mark.asyncio
async def test_create_product_success(mock_product_repository, mock_logger):
    """Test use case with mocked dependencies."""
    mock_product_repository.get_by_name.return_value = None
    mock_product_repository.create.return_value = Product(
        name=ProductName(value="Test Product"),
        price=Price(value=99.99)
    )
    
    use_case = CreateProductUseCase(mock_product_repository, mock_logger)
    request = CreateProductRequest(name="Test Product", price=99.99)
    
    response = await use_case.execute(request)
    
    assert response.success is True
    assert response.product.name.value == "Test Product"
    mock_product_repository.create.assert_called_once()
```

#### API Tests (Infrastructure Layer)
```python
# tests/infrastructure/test_api_product_controller.py
@pytest.mark.asyncio
async def test_create_product_api(client, mock_use_cases):
    """Test API endpoint."""
    response = client.post(
        "/api/v1/products/",
        json={"name": "Test Product", "price": 99.99}
    )
    
    assert response.status_code == 201
    assert response.json()["name"] == "Test Product"
```

## 🎯 Best Practices

### 1. Dependency Direction
```
Infrastructure → Application → Domain
```
- Domain layer has no dependencies
- Application layer depends only on Domain
- Infrastructure layer depends on Application and Domain

### 2. Error Handling
```python
# Domain layer: Use exceptions for business rule violations
class InsufficientStockError(Exception):
    """Raised when trying to sell more items than available."""
    pass

# Application layer: Convert to response objects
class SellProductResponse(BaseModel):
    success: bool
    message: str
    product: Optional[Product] = None

# Infrastructure layer: Convert to HTTP responses
if not response.success:
    if "insufficient stock" in response.message.lower():
        raise HTTPException(status_code=409, detail=response.message)
    else:
        raise HTTPException(status_code=400, detail=response.message)
```

### 3. Data Transformation
```python
# Always transform data at layer boundaries
def domain_to_api(product: Product) -> ProductAPIResponse:
    """Transform domain entity to API response."""
    return ProductAPIResponse(
        id=str(product.id),
        name=product.name.value,
        price=product.price.value
    )

def api_to_domain_request(api_request: CreateProductAPIRequest) -> CreateProductRequest:
    """Transform API request to use case request."""
    return CreateProductRequest(
        name=api_request.name,
        price=api_request.price
    )
```

### 4. Configuration Management
```python
# Use Dynaconf for environment-specific configuration
from src.infrastructure.config.settings import settings

class ProductRepository(ProductRepositoryPort):
    def __init__(self):
        self.db_url = settings.DATABASE.URL
        self.cache_ttl = settings.CACHE.TTL
```

### 5. Logging
```python
# Use structured logging with context
class CreateProductUseCase:
    async def execute(self, request: CreateProductRequest) -> CreateProductResponse:
        self._logger.info(
            "Creating product",
            extra={
                "product_name": request.name,
                "price": request.price,
                "use_case": "CreateProduct"
            }
        )
```

## 🔧 Development Commands

### Environment Management
```bash
# Activate development environment
hatch shell

# Install new dependency
hatch add fastapi-users[sqlalchemy]

# Add development dependency
hatch add --dev pytest-mock

# Update dependencies
hatch dep update
```

### Code Quality
```bash
# Format code
hatch run dev:ruff format .

# Lint code
hatch run dev:ruff check . --fix

# Type checking
hatch run dev:mypy src/

# Run all quality checks
hatch run dev:pre-commit run --all-files
```

### Testing
```bash
# Run all tests
hatch run test:pytest

# Run with coverage
hatch run test:pytest --cov=src --cov-report=html

# Run specific test category
hatch run test:pytest -m "unit"
hatch run test:pytest -m "integration"

# Run tests with verbose output
hatch run test:pytest -v -s
```

### Database Management
```bash
# Generate migration
hatch run aerich init-db

# Apply migrations
hatch run aerich upgrade

# Create new migration
hatch run aerich migrate --name "add_product_table"
```

### Task Queue
```bash
# Start worker
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker

# Monitor tasks
hatch run taskiq monitor src.infrastructure.tasks.taskiq_adapter:broker

# Schedule task
hatch run python -c "
from src.infrastructure.tasks.handlers.notification_tasks import cleanup_orphaned_records
import asyncio
asyncio.run(cleanup_orphaned_records.kiq())
"
```

## 📚 Additional Resources

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Hatch Documentation](https://hatch.pypa.io/)

