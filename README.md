# FastAPI Clean Architecture Template

A production-ready FastAPI template implementing **Hexagonal Architecture** (Ports and Adapters) with modern Python tooling, comprehensive testing, and best practices for scalable web applications.

## 🎯 What is this Package For?

This template provides a **complete foundation** for building scalable, maintainable FastAPI applications using clean architecture principles. It's designed for:

- **Enterprise Applications**: Production-ready structure with proper separation of concerns
- **API Development**: RESTful APIs with automatic documentation and validation
- **Microservices**: Clean boundaries and dependency injection for service-oriented architecture
- **Learning**: Demonstrates hexagonal architecture, DDD, and modern Python practices
- **Rapid Prototyping**: Pre-configured tooling and patterns for quick development

## ✨ Features & Abilities

### 🏗️ **Architecture & Design**
- ✅ **Hexagonal Architecture** (Ports and Adapters pattern)
- ✅ **Domain-Driven Design** (DDD) principles
- ✅ **Dependency Injection** with proper inversion of control
- ✅ **Clean separation** of domain, application, and infrastructure layers
- ✅ **SOLID principles** implementation throughout

### 🚀 **Core Technologies**
- ✅ **FastAPI** - Modern, fast web framework with automatic API docs
- ✅ **TortoiseORM** - Async ORM for PostgreSQL database operations
- ✅ **Pydantic** - Data validation and serialization (not used as ORM)
- ✅ **PostgreSQL** - Robust relational database with async support
- ✅ **Redis** - Caching and task queue backend

### ⚡ **Performance & Scalability**
- ✅ **Async/Await** - Full asynchronous support throughout the stack
- ✅ **Task Queue** - Background job processing with Taskiq
- ✅ **Rate Limiting** - Built-in request rate limiting with PyrateLimiter
- ✅ **Connection Pooling** - Optimized database connections
- ✅ **Caching Strategies** - Redis-based caching implementation

### 🛠️ **Development Experience**
- ✅ **Hatch** - Modern Python project management (no Pipenv)
- ✅ **Ruff** - Lightning-fast linting and code formatting
- ✅ **MyPy** - Static type checking for better code quality
- ✅ **Pre-commit Hooks** - Automated code quality checks
- ✅ **Configuration Management** - Dynaconf for environment-specific settings

### 🧪 **Testing & Quality**
- ✅ **Comprehensive Test Suite** - Unit, integration, and E2E tests
- ✅ **GitHub Actions CI/CD** - Automated testing and deployment
- ✅ **Test Coverage** - Coverage reporting and enforcement
- ✅ **Docker Support** - Containerized testing environments
- ✅ **Factory Pattern** - Test data generation with Factory Boy

### 📚 **Documentation & Examples**
- ✅ **Interactive API Docs** - Automatic Swagger/OpenAPI documentation
- ✅ **Architecture Guides** - Detailed explanations of design decisions
- ✅ **Code Examples** - Real-world usage patterns and best practices
- ✅ **Configuration Wizard** - Interactive setup tool for new projects

## 🏗️ Architecture Overview

This template follows **Hexagonal Architecture** principles, ensuring clean separation of concerns and high testability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   FastAPI   │  │ PostgreSQL  │  │  Redis/Taskiq       │ │
│  │   Routes    │  │  Tortoise   │  │  Task Queue         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Use Cases  │  │  Services   │  │      Ports          │ │
│  │             │  │             │  │   (Interfaces)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Entities   │  │    Value    │  │   Domain Services   │ │
│  │             │  │   Objects   │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (for caching and task queue)
- Docker & Docker Compose (recommended for development)

### Installation

<details>
<summary><strong>📦 Step 1: Clone and Setup</strong></summary>

```bash
# Clone the repository
git clone <your-repo-url>
cd fastapi-clean-example

# Install Hatch if you haven't already
pip install hatch

# Create and activate development environment
hatch shell

# Or run commands directly
hatch run dev:python --version
```
</details>

<details>
<summary><strong>⚙️ Step 2: Configuration</strong></summary>

```bash
# Use the interactive configuration wizard
python manage_config.py

# Or manually copy and edit settings
cp settings.toml.example settings.toml

# Update database and Redis settings in settings.toml
[database]
url = "postgresql://user:password@localhost:5432/dbname"

[redis]
url = "redis://localhost:6379/0"

[rate_limiting]
enabled = true
default_rate = "100/minute"
```
</details>

<details>
<summary><strong>🚀 Step 3: Run the Application</strong></summary>

```bash
# Development mode with hot reload
hatch run dev:uvicorn src.main:app --reload

# Production mode
hatch run uvicorn src.main:app --host 0.0.0.0 --port 8000

# Run with task queue worker
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker

# Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Admin: http://localhost:8000/admin
```
</details>

## 📁 Project Structure

<details>
<summary><strong>🏗️ View Complete Project Structure</strong></summary>

```
src/
├── domain/                     # Domain Layer (Business Logic)
│   ├── entities/              # Business entities
│   │   ├── author.py         # Author domain entity
│   │   └── book.py           # Book domain entity
│   ├── value_objects/         # Value objects
│   │   ├── author_name.py    # Author name value object
│   │   └── book_title.py     # Book title value object
│   └── services/              # Domain services
│       └── library_service.py # Domain business logic
├── application/               # Application Layer (Use Cases)
│   ├── use_cases/            # Application use cases
│   │   ├── create_author.py  # Create author use case
│   │   ├── create_book.py    # Create book use case
│   │   ├── get_author.py     # Get author use case
│   │   └── list_authors.py   # List authors use case
│   ├── services/             # Application services
│   │   └── author_service.py # Author application service
│   └── ports/                # Interfaces/Ports
│       ├── author_repository.py # Author repository interface
│       ├── book_repository.py   # Book repository interface
│       ├── logger.py           # Logger interface
│       ├── task_queue.py       # Task queue interface
│       └── rate_limiter.py     # Rate limiter interface
├── infrastructure/           # Infrastructure Layer (External Concerns)
│   ├── web/                  # FastAPI routes and controllers
│   │   ├── controllers/      # Web controllers
│   │   └── middleware/       # Custom middleware
│   ├── database/             # Database adapters
│   │   ├── models/          # Tortoise ORM models
│   │   ├── repositories/    # Repository implementations
│   │   └── connection.py    # Database connection
│   ├── tasks/                # Task queue adapters
│   │   ├── handlers/        # Task handlers
│   │   └── taskiq_adapter.py # Taskiq implementation
│   ├── rate_limiting/        # Rate limiting implementation
│   │   └── pyrate_adapter.py # PyrateLimiter adapter
│   ├── config/               # Configuration
│   │   └── settings.py      # Settings management
│   └── logging/              # Logging adapters
│       ├── logger_adapter.py # Logger implementation
│       └── setup.py         # Logging setup
└── presentation/             # Presentation Layer
    ├── api/                  # API schemas
    │   └── schemas/         # Pydantic schemas
    └── graphql/             # GraphQL schemas (optional)
```
</details>

## 🎯 Hexagonal Architecture Principles

<details>
<summary><strong>🏛️ Understanding the Architecture Layers</strong></summary>

### 1. **Domain Layer** (Core Business Logic)
- Contains business entities, value objects, and domain services
- No dependencies on external frameworks
- Pure Python with business rules
- Example: `Author`, `Book` entities with business validation

### 2. **Application Layer** (Use Cases)
- Orchestrates domain objects to fulfill use cases
- Defines ports (interfaces) for external dependencies
- Contains application services and use cases
- Example: `CreateAuthorUseCase`, `AuthorService`

### 3. **Infrastructure Layer** (External Concerns)
- Implements adapters for ports defined in application layer
- Contains FastAPI routes, database repositories, task queues
- All external framework dependencies
- Example: `AuthorRepositoryImpl`, `TaskiqAdapter`

### 4. **Presentation Layer** (API Contracts)
- Defines API schemas and contracts
- Pydantic models for request/response validation
- GraphQL schemas (if using GraphQL)
- Example: `AuthorCreateSchema`, `AuthorResponseSchema`
</details>

## 📝 How to Add New Features

<details>
<summary><strong>🆕 Adding a New Entity (Complete Example)</strong></summary>

### 1. Create Domain Entity

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

### 2. Create Value Objects

```python
# src/domain/value_objects/product_name.py
from pydantic import BaseModel, Field, field_validator

class ProductName(BaseModel):
    """Product name value object."""
    
    value: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('value')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip().title()
```

### 3. Create Repository Port

```python
# src/application/ports/product_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.product import Product

class ProductRepository(ABC):
    """Product repository interface."""
    
    @abstractmethod
    async def create(self, product: Product) -> Product:
        """Create a new product."""
        pass
    
    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Product]:
        """List all products."""
        pass
```

### 4. Implement Repository Adapter

```python
# src/infrastructure/database/repositories/product_repository_impl.py
from typing import List, Optional
from uuid import UUID

from src.application.ports.product_repository import ProductRepository
from src.domain.entities.product import Product
from src.infrastructure.database.models.product_model import ProductModel

class ProductRepositoryImpl(ProductRepository):
    """Product repository implementation using Tortoise ORM."""
    
    async def create(self, product: Product) -> Product:
        """Create a new product."""
        product_model = ProductModel(
            id=product.id,
            name=product.name.value,
            price=float(product.price.value),
        )
        await product_model.save()
        return product
    
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        try:
            product_model = await ProductModel.get(id=product_id)
            return Product(
                id=product_model.id,
                name=ProductName(value=product_model.name),
                price=Price(value=product_model.price),
            )
        except DoesNotExist:
            return None
```
</details>

<details>
<summary><strong>⚡ Adding Rate Limiting to Routes</strong></summary>

### API Route Rate Limiting

```python
# src/infrastructure/web/controllers/api_product_controller.py
from fastapi import APIRouter, Depends, HTTPException
from src.infrastructure.rate_limiting.decorators import rate_limit

router = APIRouter(prefix="/api/v1/products", tags=["products"])

@router.post("/", response_model=ProductResponse)
@rate_limit("10/minute")  # 10 requests per minute
async def create_product(
    product_data: ProductCreateRequest,
    product_service: ProductService = Depends(get_product_service)
):
    """Create a new product with rate limiting."""
    try:
        product = await product_service.create_product(product_data)
        return ProductResponse.from_domain(product)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}")
@rate_limit("100/minute")  # 100 requests per minute for read operations
async def get_product(
    product_id: UUID,
    product_service: ProductService = Depends(get_product_service)
):
    """Get product by ID with rate limiting."""
    product = await product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.from_domain(product)
```

### Template Route Rate Limiting

```python
# src/infrastructure/web/controllers/web_product_controller.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from src.infrastructure.rate_limiting.decorators import rate_limit

router = APIRouter(prefix="/products", tags=["web"])
templates = Jinja2Templates(directory="templates")

@router.get("/")
@rate_limit("50/minute")  # 50 page views per minute
async def list_products(
    request: Request,
    product_service: ProductService = Depends(get_product_service)
):
    """List products page with rate limiting."""
    products = await product_service.list_products()
    return templates.TemplateResponse(
        "products/list.html",
        {"request": request, "products": products}
    )

@router.get("/create")
@rate_limit("20/minute")  # 20 form views per minute
async def create_product_form(request: Request):
    """Create product form with rate limiting."""
    return templates.TemplateResponse(
        "products/create.html",
        {"request": request}
    )
```

### Custom Rate Limiting Strategies

```python
# Different rate limiting strategies
@rate_limit("100/minute")           # Per IP address
@rate_limit("1000/hour")           # Per hour limit
@rate_limit("10/minute", per="user") # Per authenticated user
@rate_limit("5/minute", per="endpoint") # Per specific endpoint
```
</details>

## 🧪 Testing

This project includes comprehensive testing infrastructure with unit, integration, end-to-end, performance, and accessibility tests.

<details>
<summary><strong>🔬 Running Tests</strong></summary>

### Prerequisites
```bash
# Install development dependencies
pip install -e ".[dev]"

# Or using Hatch
hatch shell dev
```

### Basic Test Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run with verbose output
pytest -v

# Run specific test files
pytest tests/unit/presentation/test_loguru_tui.py
pytest tests/integration/test_tui_workflows.py
```

### Test Categories
```bash
# Run unit tests only
pytest tests/unit/

# Run TUI-specific tests
pytest -m tui

# Run integration tests
pytest tests/integration/ -v

# Run end-to-end tests
pytest tests/e2e/ -v --timeout=120

# Run performance tests (slow)
pytest tests/performance/ -v --timeout=180

# Run accessibility tests
pytest tests/accessibility/ -v

# Skip slow tests
pytest -m "not slow"
```

### Using Hatch (Recommended)
```bash
# Run all tests with Hatch
hatch run dev:pytest

# Run with coverage
hatch run dev:pytest --cov=src --cov-report=html

# Run specific test categories
hatch run dev:pytest -m tui                    # TUI tests
hatch run dev:pytest -m integration           # Integration tests
hatch run dev:pytest -m e2e                   # End-to-end tests
hatch run dev:pytest -m slow                  # Performance tests
hatch run dev:pytest -m "not slow"            # Skip slow tests

# Run tests with timeout
hatch run dev:pytest --timeout=60
```

### Docker Testing
```bash
# Run tests in Docker environment
docker-compose -f docker-compose.test.yml up --build

# Run specific test suites in Docker
docker-compose -f docker-compose.test.yml run --rm app pytest tests/unit/
docker-compose -f docker-compose.test.yml run --rm app pytest -m tui
```

### Test Environment Setup
```bash
# Set environment variables for testing
export ENVIRONMENT=testing
export DATABASE_URL=postgresql://test_user:test_password@localhost:5432/test_db
export REDIS_URL=redis://localhost:6379/1
export TERM=dumb
export NO_COLOR=1
export TEXTUAL_HEADLESS=1

# Start test services
docker-compose up postgres redis -d
```
</details>

<details>
<summary><strong>📊 Test Coverage & Reports</strong></summary>

### Coverage Commands
```bash
# Generate coverage report
hatch run dev:pytest --cov=src --cov-report=html --cov-report=xml

# View HTML coverage report
open htmlcov/index.html

# Generate coverage badge
hatch run dev:coverage-badge -o coverage.svg

# Check coverage requirements
hatch run dev:pytest --cov=src --cov-fail-under=80
```

### Test Structure & Coverage Goals
```
tests/
├── unit/presentation/           # TUI component unit tests (95%+ coverage)
├── integration/                 # Cross-layer workflow tests (90%+ coverage)
├── e2e/                        # Complete user scenario tests (85%+ coverage)
├── performance/                # Scalability & efficiency tests (100% coverage)
├── accessibility/              # Keyboard & screen reader tests (100% coverage)
├── fixtures/                   # Test data & mock repositories
└── utils/                      # Testing utilities & helpers
```

### Coverage Requirements
- **Overall Project**: 80% minimum coverage enforced in CI/CD
- **Domain Layer**: 95%+ coverage (business logic)
- **Application Layer**: 90%+ coverage (use cases)
- **Infrastructure Layer**: 85%+ coverage (adapters)
- **TUI Components**: 95%+ coverage (presentation layer)

### Test Reports
```bash
# Generate multiple report formats
pytest --cov=src \
       --cov-report=html \
       --cov-report=xml \
       --cov-report=term \
       --cov-report=json

# JUnit XML for CI/CD
pytest --junitxml=test-results.xml

# Performance benchmarks
pytest tests/performance/ --benchmark-json=benchmark.json
```
</details>

<details>
<summary><strong>🎯 Test Categories Explained</strong></summary>

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Focus**: Domain entities, value objects, use cases, TUI components
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Mocked external dependencies

### Integration Tests (`tests/integration/`)
- **Purpose**: Test interactions between layers
- **Focus**: Repository implementations, service integrations, cross-layer workflows
- **Speed**: Medium (1-10 seconds per test)
- **Dependencies**: Real database and Redis connections

### End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete user workflows
- **Focus**: Full application scenarios, API endpoints, TUI workflows
- **Speed**: Slow (10-60 seconds per test)
- **Dependencies**: Full application stack

### Performance Tests (`tests/performance/`)
- **Purpose**: Test scalability and efficiency
- **Focus**: Response times, memory usage, concurrent operations
- **Speed**: Very slow (30-180 seconds per test)
- **Dependencies**: Load testing scenarios

### Accessibility Tests (`tests/accessibility/`)
- **Purpose**: Test inclusive design compliance
- **Focus**: Keyboard navigation, screen readers, responsive design
- **Speed**: Fast (< 5 seconds per test)
- **Dependencies**: TUI accessibility features

### TUI Tests (Marker: `@pytest.mark.tui`)
- **Purpose**: Test Text User Interface components
- **Focus**: Loguru TUI, Dynaconf TUI, navigation, forms
- **Speed**: Medium (2-10 seconds per test)
- **Dependencies**: Headless terminal environment
</details>

<details>
<summary><strong>🐛 Debugging Tests</strong></summary>

### Debug Commands
```bash
# Run tests with debugging
pytest --pdb                    # Drop into debugger on failure
pytest -s                      # Show print statements
pytest --tb=long               # Detailed traceback
pytest --lf                    # Run last failed tests only
pytest --ff                    # Run failed tests first

# Debug specific test
pytest tests/unit/presentation/test_loguru_tui.py::TestLoguruConfigApp::test_load_configuration_success -v -s

# Debug TUI tests
pytest -m tui -v -s --tb=short --timeout=30
```

### Common Issues
1. **TUI Tests Hanging**: Use `--timeout=30` parameter
2. **Database Connection Issues**: Ensure PostgreSQL is running
3. **Redis Connection Issues**: Ensure Redis is running
4. **Import Errors**: Check PYTHONPATH and virtual environment
5. **Permission Errors**: Check file permissions in logs/ and configs/ directories

### Test Data Management
```bash
# Reset test database
docker-compose exec postgres psql -U test_user -d test_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Clear Redis test data
docker-compose exec redis redis-cli -n 1 FLUSHDB

# Clean test artifacts
rm -rf htmlcov/ .coverage test-results.xml .pytest_cache/
```
</details>

## 🛠️ Development Tools

<details>
<summary><strong>🔧 Code Quality Tools</strong></summary>

```bash
# Format code
hatch run dev:format

# Lint code
hatch run dev:lint

# Type checking
hatch run dev:typing

# Security scan
hatch run dev:security

# Run all quality checks
hatch run dev:all
```
</details>

<details>
<summary><strong>📝 Pre-commit Hooks</strong></summary>

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```
</details>

## 🚀 Deployment

<details>
<summary><strong>🐳 Docker Deployment</strong></summary>

```bash
# Build production image
docker build -t fastapi-clean-app .

# Run with docker-compose
docker-compose up -d

# Environment-specific deployment
docker-compose -f docker-compose.prod.yml up -d
```
</details>

<details>
<summary><strong>☁️ Cloud Deployment</strong></summary>

The template includes configurations for:
- **AWS ECS/Fargate** - Container orchestration
- **Google Cloud Run** - Serverless containers
- **Azure Container Instances** - Managed containers
- **Kubernetes** - Full orchestration platform
</details>

## 📚 Additional Resources

<details>
<summary><strong>📖 Learning Resources</strong></summary>

- [Hexagonal Architecture Guide](./docs/hexagonal-architecture.md)
- [Domain-Driven Design Patterns](./docs/ddd-patterns.md)
- [Testing Strategies](./docs/testing-guide.md)
- [Configuration Management](./CONFIG_TOOL_README.md)
- [Development Guide](./DEVELOPMENT_GUIDE.md)
</details>

<details>
<summary><strong>🤝 Contributing</strong></summary>

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.
</details>

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework
- **Tortoise ORM** - Async ORM inspired by Django ORM
- **Pydantic** - Data validation using Python type hints
- **Hatch** - Modern Python project management
- **Clean Architecture** - Robert C. Martin's architectural principles

---

**Built with ❤️ using Hexagonal Architecture principles**

## 🔧 Redis Setup & Task Queue

This project uses Redis for caching and as a message broker for the task queue system. For detailed setup instructions, see [docs/redis-setup.md](docs/redis-setup.md).

<details>
<summary><strong>🚀 Quick Redis Setup</strong></summary>

### Using Docker (Recommended)
```bash
# Start Redis with Docker Compose
docker-compose up redis -d

# Verify Redis is running
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Manual Installation

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### macOS
```bash
brew install redis
brew services start redis
```

#### Windows (WSL)
```bash
# Install Redis in WSL
sudo apt update && sudo apt install redis-server
redis-server --daemonize yes
```

### Configuration
```bash
# Copy example settings
cp settings.toml.example settings.toml

# Update Redis settings in settings.toml
[redis]
url = "redis://localhost:6379/0"
password = ""
max_connections = 20

[taskiq]
broker_url = "redis://localhost:6379/0"
result_backend_url = "redis://localhost:6379/1"
```

### Starting Task Workers
```bash
# Start task workers
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker

# With multiple workers
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker --workers 4

# Using Docker
docker-compose up taskiq-worker -d
```

### Testing Task Queue
```bash
# Test task queue functionality
curl -X POST "http://localhost:8000/api/v1/tasks/email/welcome" \
     -H "Content-Type: application/json" \
     -d '{"recipient": "test@example.com", "name": "Test User"}'

# Check task status
curl "http://localhost:8000/api/v1/tasks/status/{task_id}"
```
</details>

