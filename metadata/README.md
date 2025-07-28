# Metadata Directory (`metadata/`)

The **Metadata Directory** contains configuration and metadata files that define application behavior, API documentation, and system information. These files provide essential configuration data that supports the application's operation without containing business logic.

## 🎯 Purpose & Role in Hexagon Architecture

Metadata serves as **configuration and documentation support** that:
- **Defines API metadata** for documentation generation
- **Stores application configuration** templates and examples
- **Provides system information** for monitoring and debugging
- **Contains reference data** that doesn't change frequently
- **Supports development tools** with configuration files

## 🏗️ Key Responsibilities

### 1. **API Documentation**
- OpenAPI/Swagger specifications
- API version information and changelog
- Endpoint descriptions and examples

### 2. **Application Configuration**
- Environment-specific settings
- Feature flags and toggles
- System constants and enumerations

### 3. **Reference Data**
- Static lookup tables
- Country codes, currencies, time zones
- System-wide constants and mappings

## 📁 Metadata Structure

```
metadata/
├── api_info.py            # API metadata and information
├── constants.py           # Application constants
├── enums.py              # System enumerations
└── README.md             # This file
```

## 🔧 Implementation Examples

### API Information and Metadata

```python
# metadata/api_info.py
from typing import Dict, List, Any

# API Version and Basic Information
API_VERSION = "1.0.0"
API_TITLE = "FastAPI Clean Architecture Template"
API_DESCRIPTION = """
A comprehensive FastAPI application template following Clean Architecture principles.

This API provides endpoints for managing authors and books in a library system,
demonstrating hexagon architecture with proper separation of concerns.

## Features

- **Author Management**: Create, read, update, and delete authors
- **Book Catalog**: Manage book inventory and metadata
- **Search & Filtering**: Advanced search capabilities
- **Pagination**: Efficient data pagination
- **Validation**: Comprehensive input validation
- **Documentation**: Auto-generated API documentation

## Architecture

This application follows the Hexagon Architecture (Ports and Adapters) pattern:

- **Domain Layer**: Core business logic and entities
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: Database, external services, and adapters
- **Presentation Layer**: REST API, GraphQL, CLI interfaces

## Authentication

Currently, this API does not require authentication. In production environments,
you should implement proper authentication and authorization mechanisms.
"""

# Contact Information
CONTACT_INFO = {
    "name": "API Support Team",
    "url": "https://github.com/SuperPauly/fastapi-clean-example",
    "email": "support@example.com"
}

# License Information
LICENSE_INFO = {
    "name": "MIT License",
    "url": "https://opensource.org/licenses/MIT"
}

# Tags for API Organization
API_TAGS = [
    {
        "name": "authors",
        "description": "Operations related to author management",
        "externalDocs": {
            "description": "Author Management Guide",
            "url": "https://docs.example.com/authors"
        }
    },
    {
        "name": "books",
        "description": "Operations related to book catalog management",
        "externalDocs": {
            "description": "Book Catalog Guide", 
            "url": "https://docs.example.com/books"
        }
    },
    {
        "name": "health",
        "description": "System health and monitoring endpoints"
    }
]

# Server Information for Different Environments
SERVERS = [
    {
        "url": "http://localhost:8000",
        "description": "Development server"
    },
    {
        "url": "https://staging-api.example.com",
        "description": "Staging server"
    },
    {
        "url": "https://api.example.com",
        "description": "Production server"
    }
]

# OpenAPI Extensions
OPENAPI_EXTENSIONS = {
    "x-logo": {
        "url": "https://example.com/logo.png",
        "altText": "FastAPI Clean Architecture Logo"
    },
    "x-api-id": "fastapi-clean-architecture-template",
    "x-audience": "developers"
}

def get_api_metadata() -> Dict[str, Any]:
    """
    Get complete API metadata for FastAPI application.
    
    Returns:
        Dictionary containing all API metadata
    """
    return {
        "title": API_TITLE,
        "description": API_DESCRIPTION,
        "version": API_VERSION,
        "contact": CONTACT_INFO,
        "license": LICENSE_INFO,
        "tags": API_TAGS,
        "servers": SERVERS,
        **OPENAPI_EXTENSIONS
    }
```

### Application Constants

```python
# metadata/constants.py
from typing import Dict, List

# Database Configuration
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds

# Validation Constants
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 50
MAX_BIO_LENGTH = 2000
MAX_DESCRIPTION_LENGTH = 1000
MIN_BIO_LENGTH = 10

# Business Rules
MAX_BOOKS_PER_AUTHOR_PER_YEAR = 2
MIN_DAYS_BETWEEN_PUBLICATIONS = 180
MAX_UNPUBLISHED_BOOKS_PER_AUTHOR = 5
MIN_AUTHOR_AGE = 16

# Currency and Pricing
DEFAULT_CURRENCY = "USD"
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
MAX_BOOK_PRICE = 999.99
MIN_BOOK_PRICE = 0.01

# File and Upload Limits
MAX_FILE_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".doc", ".docx", ".txt"]

# Email Configuration
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
MAX_EMAIL_LENGTH = 254  # RFC 5321 limit

# ISBN Configuration
ISBN_REGEX = r'^978-\d{10}$'
ISBN_LENGTH = 14  # Including hyphens

# System Limits
MAX_SEARCH_RESULTS = 1000
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRY_ATTEMPTS = 3

# Cache Keys
CACHE_KEY_PATTERNS = {
    "author": "author:{author_id}",
    "author_books": "author_books:{author_id}",
    "book": "book:{book_id}",
    "book_by_isbn": "book_isbn:{isbn}",
    "author_dashboard": "author_dashboard:{author_id}",
    "search_results": "search:{query_hash}"
}

# HTTP Status Messages
STATUS_MESSAGES = {
    "AUTHOR_CREATED": "Author created successfully",
    "AUTHOR_UPDATED": "Author updated successfully", 
    "AUTHOR_DELETED": "Author deactivated successfully",
    "AUTHOR_NOT_FOUND": "Author not found",
    "BOOK_CREATED": "Book created successfully",
    "BOOK_UPDATED": "Book updated successfully",
    "BOOK_NOT_FOUND": "Book not found",
    "VALIDATION_ERROR": "Validation failed",
    "DUPLICATE_EMAIL": "Email address already in use",
    "DUPLICATE_ISBN": "ISBN already exists"
}

# Feature Flags (for development/testing)
FEATURE_FLAGS = {
    "ENABLE_AUTHOR_REGISTRATION": True,
    "ENABLE_BOOK_CREATION": True,
    "ENABLE_BULK_OPERATIONS": True,
    "ENABLE_ADVANCED_SEARCH": True,
    "ENABLE_CACHING": True,
    "ENABLE_RATE_LIMITING": True,
    "ENABLE_METRICS": True
}

# Logging Configuration
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### System Enumerations

```python
# metadata/enums.py
from enum import Enum, IntEnum
from typing import List

class BookGenre(str, Enum):
    """Enumeration of supported book genres."""
    
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    SCIENCE_FICTION = "science_fiction"
    FANTASY = "fantasy"
    THRILLER = "thriller"
    HORROR = "horror"
    BIOGRAPHY = "biography"
    HISTORY = "history"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    SELF_HELP = "self_help"
    CHILDREN = "children"
    YOUNG_ADULT = "young_adult"
    POETRY = "poetry"
    DRAMA = "drama"
    ACADEMIC = "academic"
    REFERENCE = "reference"
    
    @classmethod
    def get_all_genres(cls) -> List[str]:
        """Get list of all available genres."""
        return [genre.value for genre in cls]
    
    @classmethod
    def get_fiction_genres(cls) -> List[str]:
        """Get list of fiction genres."""
        fiction_genres = [
            cls.FICTION, cls.MYSTERY, cls.ROMANCE, cls.SCIENCE_FICTION,
            cls.FANTASY, cls.THRILLER, cls.HORROR
        ]
        return [genre.value for genre in fiction_genres]

class AuthorStatus(str, Enum):
    """Enumeration of author status values."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    
    @classmethod
    def get_active_statuses(cls) -> List[str]:
        """Get statuses considered as active."""
        return [cls.ACTIVE.value, cls.PENDING.value]

class BookStatus(str, Enum):
    """Enumeration of book availability status."""
    
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    PRE_ORDER = "pre_order"
    
    @classmethod
    def get_available_statuses(cls) -> List[str]:
        """Get statuses where book can be ordered."""
        return [cls.IN_STOCK.value, cls.LOW_STOCK.value, cls.PRE_ORDER.value]

class SortOrder(str, Enum):
    """Enumeration for sort order directions."""
    
    ASC = "asc"
    DESC = "desc"
    ASCENDING = "ascending"
    DESCENDING = "descending"
    
    @classmethod
    def normalize(cls, value: str) -> str:
        """Normalize sort order value."""
        value = value.lower()
        if value in [cls.ASC.value, cls.ASCENDING.value]:
            return cls.ASC.value
        elif value in [cls.DESC.value, cls.DESCENDING.value]:
            return cls.DESC.value
        else:
            return cls.ASC.value  # Default

class Priority(IntEnum):
    """Enumeration for priority levels."""
    
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    @classmethod
    def get_description(cls, priority: int) -> str:
        """Get human-readable description for priority level."""
        descriptions = {
            cls.LOW: "Low Priority",
            cls.MEDIUM: "Medium Priority", 
            cls.HIGH: "High Priority",
            cls.CRITICAL: "Critical Priority"
        }
        return descriptions.get(priority, "Unknown Priority")

class Currency(str, Enum):
    """Enumeration of supported currencies."""
    
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    JPY = "JPY"  # Japanese Yen
    
    @classmethod
    def get_symbol(cls, currency: str) -> str:
        """Get currency symbol for display."""
        symbols = {
            cls.USD: "$",
            cls.EUR: "€",
            cls.GBP: "£",
            cls.CAD: "C$",
            cls.AUD: "A$",
            cls.JPY: "¥"
        }
        return symbols.get(currency, currency)

class NotificationType(str, Enum):
    """Enumeration of notification types."""
    
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    
    @classmethod
    def get_delivery_methods(cls) -> List[str]:
        """Get all available delivery methods."""
        return [method.value for method in cls]

class LogLevel(str, Enum):
    """Enumeration of logging levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def get_numeric_level(cls, level: str) -> int:
        """Get numeric value for log level."""
        levels = {
            cls.DEBUG: 10,
            cls.INFO: 20,
            cls.WARNING: 30,
            cls.ERROR: 40,
            cls.CRITICAL: 50
        }
        return levels.get(level.upper(), 20)  # Default to INFO
```

## 🧪 Testing Metadata

```python
# tests/unit/metadata/test_constants.py
import pytest
from metadata.constants import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SUPPORTED_CURRENCIES,
    CACHE_KEY_PATTERNS
)
from metadata.enums import BookGenre, Currency

class TestConstants:
    def test_pagination_constants(self):
        """Test pagination constants are reasonable."""
        assert DEFAULT_PAGE_SIZE > 0
        assert MAX_PAGE_SIZE > DEFAULT_PAGE_SIZE
        assert MAX_PAGE_SIZE <= 1000  # Reasonable upper limit
    
    def test_supported_currencies_match_enum(self):
        """Test that supported currencies match Currency enum."""
        enum_currencies = [currency.value for currency in Currency]
        assert set(SUPPORTED_CURRENCIES) == set(enum_currencies)
    
    def test_cache_key_patterns_format(self):
        """Test that cache key patterns are properly formatted."""
        for key, pattern in CACHE_KEY_PATTERNS.items():
            assert isinstance(pattern, str)
            assert ":" in pattern  # Should have namespace separator

class TestEnums:
    def test_book_genre_completeness(self):
        """Test that book genres cover major categories."""
        genres = BookGenre.get_all_genres()
        
        # Should have major genres
        assert "fiction" in genres
        assert "non_fiction" in genres
        assert "science_fiction" in genres
        assert "children" in genres
    
    def test_currency_symbols(self):
        """Test currency symbol mapping."""
        assert Currency.get_symbol("USD") == "$"
        assert Currency.get_symbol("EUR") == "€"
        assert Currency.get_symbol("UNKNOWN") == "UNKNOWN"  # Fallback
```

## ✅ Best Practices

### Organization
- **Group related constants** in logical sections
- **Use descriptive names** that clearly indicate purpose
- **Provide documentation** for complex constants
- **Keep values consistent** across the application

### Maintenance
- **Version your metadata** when making breaking changes
- **Use enums for fixed sets** of values
- **Centralize configuration** to avoid duplication
- **Review regularly** to remove unused constants

## ❌ Common Pitfalls

- **Hardcoding values** throughout the application instead of using constants
- **Not updating metadata** when business rules change
- **Inconsistent naming** conventions for constants
- **Missing documentation** for complex configurations

## 🔄 Integration Points

Metadata integrates with:
- **Application Layer** - Provides business rule constants
- **Presentation Layer** - Supplies API documentation and validation rules
- **Infrastructure Layer** - Offers configuration values and limits
- **Testing** - Provides test data and validation constants

The metadata directory is essential for maintaining consistent configuration and documentation across your hexagon architecture application.

