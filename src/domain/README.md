# Domain Layer (`src/domain/`)

The **Domain Layer** is the heart of the hexagon architecture, containing the core business logic, entities, and rules that define what your application does. This layer is completely independent of any external concerns like databases, web frameworks, or user interfaces.

## 🎯 Purpose

The domain layer represents the **business model** of your application. It contains:
- **Business entities** with their properties and behaviors
- **Value objects** that represent concepts without identity
- **Domain services** that contain business logic not belonging to a single entity
- **Business rules and invariants** that must always be maintained

## 🏗️ Architecture Principles

### 1. **Pure Business Logic**
- No dependencies on external frameworks or libraries
- No knowledge of databases, web requests, or user interfaces
- Contains only the essential business concepts and rules

### 2. **Self-Contained**
- All business rules are enforced within this layer
- Entities validate their own state
- Domain services handle complex business operations

### 3. **Technology Agnostic**
- Can be used with any database, web framework, or UI
- Easy to test without external dependencies
- Portable across different technical implementations

## 📁 Directory Structure

```
domain/
├── entities/           # Business entities with identity
├── value_objects/      # Immutable objects without identity  
├── services/          # Domain services for complex business logic
└── README.md          # This file
```

## 📋 Components

### [`entities/`](./entities/) - Business Entities

Entities are objects with **identity** that persist over time. They contain:
- **Unique identifiers** (IDs)
- **Mutable state** that can change
- **Business methods** that operate on their data
- **Invariants** that must always be true

**Examples:**
- `Author` - A person who writes books
- `Book` - A published work with ISBN, title, etc.
- `User` - A system user with authentication details
- `Order` - A purchase transaction

### [`value_objects/`](./value_objects/) - Value Objects

Value objects are **immutable** objects defined by their attributes rather than identity:
- **No unique identifier** needed
- **Immutable** - cannot be changed after creation
- **Equality** based on all attributes
- **Replaceable** - create new instances instead of modifying

**Examples:**
- `AuthorName` - First and last name combination
- `BookTitle` - Title with validation rules
- `Email` - Email address with format validation
- `Money` - Amount and currency combination
- `DateRange` - Start and end date pair

### [`services/`](./services/) - Domain Services

Domain services contain business logic that:
- **Doesn't belong** to a single entity
- **Operates on multiple** entities or value objects
- **Implements complex** business rules
- **Coordinates** between different domain objects

**Examples:**
- `LibraryService` - Manages book lending rules
- `PricingService` - Calculates book prices with discounts
- `AuthorRankingService` - Ranks authors by popularity
- `InventoryService` - Manages stock levels and availability

## 🔧 Implementation Examples

### Entity Example: Author

```python
# src/domain/entities/author.py
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import date

from ..value_objects.author_name import AuthorName
from ..value_objects.email import Email

@dataclass
class Author:
    """Author entity representing a book author."""
    
    id: UUID
    name: AuthorName
    email: Optional[Email] = None
    bio: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    is_active: bool = True
    
    @classmethod
    def create(
        cls,
        name: AuthorName,
        email: Optional[Email] = None,
        bio: Optional[str] = None,
        birth_date: Optional[date] = None,
        nationality: Optional[str] = None
    ) -> "Author":
        """Create a new author with generated ID."""
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            bio=bio,
            birth_date=birth_date,
            nationality=nationality
        )
    
    def update_bio(self, bio: str) -> None:
        """Update author's biography."""
        if len(bio.strip()) < 10:
            raise ValueError("Bio must be at least 10 characters long")
        self.bio = bio.strip()
    
    def deactivate(self) -> None:
        """Deactivate the author."""
        self.is_active = False
    
    def get_age(self) -> Optional[int]:
        """Calculate author's age if birth date is known."""
        if not self.birth_date:
            return None
        
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
```

### Value Object Example: AuthorName

```python
# src/domain/value_objects/author_name.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class AuthorName:
    """Value object representing an author's name."""
    
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate name components."""
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name cannot be empty")
        
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name cannot be empty")
        
        if len(self.first_name) > 50:
            raise ValueError("First name cannot exceed 50 characters")
        
        if len(self.last_name) > 50:
            raise ValueError("Last name cannot exceed 50 characters")
    
    @property
    def full_name(self) -> str:
        """Get the full name as a string."""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get name in 'Last, First' format."""
        return f"{self.last_name}, {self.first_name}"
    
    @classmethod
    def from_full_name(cls, full_name: str) -> "AuthorName":
        """Create AuthorName from a full name string."""
        parts = full_name.strip().split()
        
        if len(parts) < 2:
            raise ValueError("Full name must contain at least first and last name")
        
        if len(parts) == 2:
            return cls(first_name=parts[0], last_name=parts[1])
        
        # Assume middle part is middle name, last part is last name
        return cls(
            first_name=parts[0],
            middle_name=" ".join(parts[1:-1]),
            last_name=parts[-1]
        )
```

### Domain Service Example: LibraryService

```python
# src/domain/services/library_service.py
from typing import List, Optional
from datetime import date, timedelta

from ..entities.author import Author
from ..entities.book import Book
from ..value_objects.money import Money

class LibraryService:
    """Domain service for library business operations."""
    
    @staticmethod
    def calculate_author_royalty(
        author: Author, 
        books: List[Book], 
        sales_data: dict
    ) -> Money:
        """Calculate total royalty for an author based on book sales."""
        total_royalty = Money(0, "USD")
        
        for book in books:
            if book.author_id != author.id:
                continue
                
            book_sales = sales_data.get(str(book.id), 0)
            royalty_rate = 0.10  # 10% royalty rate
            
            if book_sales > 1000:
                royalty_rate = 0.15  # Higher rate for bestsellers
            
            book_royalty = Money(
                book.price.amount * book_sales * royalty_rate,
                book.price.currency
            )
            total_royalty = total_royalty.add(book_royalty)
        
        return total_royalty
    
    @staticmethod
    def can_author_publish_book(author: Author, existing_books: List[Book]) -> bool:
        """Check if author can publish a new book based on business rules."""
        if not author.is_active:
            return False
        
        # Authors can only publish 2 books per year
        current_year = date.today().year
        books_this_year = [
            book for book in existing_books 
            if (book.author_id == author.id and 
                book.publication_date and 
                book.publication_date.year == current_year)
        ]
        
        return len(books_this_year) < 2
    
    @staticmethod
    def suggest_book_price(book: Book, market_data: dict) -> Money:
        """Suggest optimal price for a book based on market data."""
        base_price = 15.00  # Base price in USD
        
        # Adjust based on page count
        if book.page_count > 500:
            base_price *= 1.5
        elif book.page_count < 200:
            base_price *= 0.8
        
        # Adjust based on genre popularity
        genre_multiplier = market_data.get("genre_multipliers", {}).get(
            book.genre, 1.0
        )
        base_price *= genre_multiplier
        
        return Money(base_price, "USD")
```

## 🧪 Testing Domain Layer

Domain layer testing is straightforward since there are no external dependencies:

```python
# tests/unit/domain/entities/test_author.py
import pytest
from datetime import date
from uuid import UUID

from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName
from src.domain.value_objects.email import Email

class TestAuthor:
    def test_create_author_with_valid_data(self):
        # Arrange
        name = AuthorName("John", "Doe")
        email = Email("john.doe@example.com")
        
        # Act
        author = Author.create(name=name, email=email)
        
        # Assert
        assert isinstance(author.id, UUID)
        assert author.name == name
        assert author.email == email
        assert author.is_active is True
    
    def test_update_bio_with_valid_bio(self):
        # Arrange
        author = Author.create(name=AuthorName("Jane", "Smith"))
        bio = "Jane Smith is a renowned author of fantasy novels."
        
        # Act
        author.update_bio(bio)
        
        # Assert
        assert author.bio == bio
    
    def test_update_bio_with_short_bio_raises_error(self):
        # Arrange
        author = Author.create(name=AuthorName("Jane", "Smith"))
        
        # Act & Assert
        with pytest.raises(ValueError, match="Bio must be at least 10 characters"):
            author.update_bio("Too short")
    
    def test_get_age_with_birth_date(self):
        # Arrange
        birth_date = date(1980, 5, 15)
        author = Author.create(
            name=AuthorName("John", "Doe"),
            birth_date=birth_date
        )
        
        # Act
        age = author.get_age()
        
        # Assert
        expected_age = date.today().year - 1980
        assert age in [expected_age - 1, expected_age]  # Account for birthday
```

## ✅ Best Practices

### Do's
- Keep entities focused on their core responsibilities
- Validate business rules within entities and value objects
- Use value objects for concepts without identity
- Make value objects immutable
- Put complex business logic in domain services
- Write comprehensive unit tests

### Don'ts
- Don't add infrastructure dependencies (databases, HTTP, etc.)
- Don't put presentation logic in domain objects
- Don't make entities anemic (without behavior)
- Don't bypass business rules for "convenience"
- Don't create circular dependencies between domain objects

## 🔄 Integration with Other Layers

The domain layer is used by:
- **Application Layer**: Use cases orchestrate domain objects
- **Infrastructure Layer**: Repositories persist domain entities
- **Presentation Layer**: Controllers convert between domain objects and DTOs

The domain layer should never directly depend on other layers.

## 📚 Additional Resources

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Implementing Domain-Driven Design by Vaughn Vernon](https://vaughnvernon.co/?page_id=168)
- [Value Objects Explained](https://martinfowler.com/bliki/ValueObject.html)

