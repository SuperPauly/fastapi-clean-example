# Domain Entities (`src/domain/entities/`)

Domain entities are the core business objects that have **identity** and **lifecycle** within your application. They represent the main concepts that your business revolves around and contain both data and behavior related to those concepts.

## 🎯 What are Domain Entities?

Entities are objects that:
- Have a **unique identity** that persists over time
- Can **change state** while maintaining their identity
- Contain **business logic** and **behavior**
- Enforce **business rules** and **invariants**
- Have a **lifecycle** (created, modified, archived, deleted)

## 🏗️ Key Characteristics

### 1. **Identity**
- Each entity has a unique identifier (usually UUID or ID)
- Identity remains constant throughout the entity's lifecycle
- Two entities are equal if they have the same identity

### 2. **Mutable State**
- Entities can change their attributes over time
- State changes must follow business rules
- All modifications should go through entity methods

### 3. **Business Behavior**
- Entities contain methods that implement business logic
- They validate their own state and enforce invariants
- They provide meaningful operations related to the business concept

### 4. **Encapsulation**
- Internal state is protected from invalid modifications
- Business rules are enforced within the entity
- External code interacts through well-defined methods

## 📁 Current Entities

Based on the project structure, here are the main entities:

### Author Entity
Represents a book author in the library system.

**Responsibilities:**
- Maintain author information (name, bio, contact details)
- Validate author data according to business rules
- Track author status (active/inactive)
- Calculate derived information (age, years active)

**Key Attributes:**
- `id`: Unique identifier
- `name`: Author's full name (value object)
- `email`: Contact email (value object)
- `bio`: Author biography
- `birth_date`: Date of birth
- `nationality`: Author's nationality
- `is_active`: Whether author is currently active

### Book Entity
Represents a published book in the library system.

**Responsibilities:**
- Maintain book information (title, ISBN, publication details)
- Validate book data and business rules
- Track inventory and availability
- Calculate pricing and discounts

**Key Attributes:**
- `id`: Unique identifier
- `title`: Book title (value object)
- `isbn`: International Standard Book Number
- `author_id`: Reference to author entity
- `publication_date`: When the book was published
- `page_count`: Number of pages
- `genre`: Book category/genre
- `price`: Book price (value object)
- `stock_quantity`: Available inventory

## 🔧 Implementation Examples

### Complete Author Entity

```python
# src/domain/entities/author.py
from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import date, datetime

from ..value_objects.author_name import AuthorName
from ..value_objects.email import Email

@dataclass
class Author:
    """
    Author entity representing a book author.
    
    An author is a person who writes books and has a persistent identity
    in the system. Authors can be active or inactive, and they maintain
    biographical information and contact details.
    """
    
    # Identity
    id: UUID = field(default_factory=uuid4)
    
    # Core attributes
    name: AuthorName = field()
    email: Optional[Email] = None
    bio: Optional[str] = None
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    
    # Status and metadata
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate entity state after initialization."""
        self._validate_bio()
        self._validate_birth_date()
    
    @classmethod
    def create(
        cls,
        name: AuthorName,
        email: Optional[Email] = None,
        bio: Optional[str] = None,
        birth_date: Optional[date] = None,
        nationality: Optional[str] = None
    ) -> "Author":
        """
        Create a new author with business rule validation.
        
        Args:
            name: Author's full name
            email: Optional contact email
            bio: Optional biography
            birth_date: Optional date of birth
            nationality: Optional nationality
            
        Returns:
            New Author instance
            
        Raises:
            ValueError: If business rules are violated
        """
        author = cls(
            name=name,
            email=email,
            bio=bio,
            birth_date=birth_date,
            nationality=nationality
        )
        
        # Additional business rule: Authors must be at least 16 years old
        if birth_date and author.get_age() < 16:
            raise ValueError("Authors must be at least 16 years old")
        
        return author
    
    def update_bio(self, bio: str) -> None:
        """
        Update the author's biography.
        
        Args:
            bio: New biography text
            
        Raises:
            ValueError: If bio doesn't meet requirements
        """
        if not bio or len(bio.strip()) < 10:
            raise ValueError("Bio must be at least 10 characters long")
        
        if len(bio) > 2000:
            raise ValueError("Bio cannot exceed 2000 characters")
        
        self.bio = bio.strip()
        self.updated_at = datetime.now()
    
    def update_email(self, email: Email) -> None:
        """Update the author's email address."""
        self.email = email
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """
        Deactivate the author.
        
        Deactivated authors cannot publish new books but existing
        books remain available.
        """
        self.is_active = False
        self.updated_at = datetime.now()
    
    def reactivate(self) -> None:
        """Reactivate a previously deactivated author."""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def get_age(self) -> Optional[int]:
        """
        Calculate the author's current age.
        
        Returns:
            Age in years, or None if birth date is unknown
        """
        if not self.birth_date:
            return None
        
        today = date.today()
        age = today.year - self.birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        
        return age
    
    def get_years_active(self) -> int:
        """
        Calculate how many years the author has been in the system.
        
        Returns:
            Number of years since creation
        """
        years = datetime.now().year - self.created_at.year
        return max(0, years)
    
    def can_publish_book(self) -> bool:
        """
        Check if the author can publish a new book.
        
        Returns:
            True if author can publish, False otherwise
        """
        return self.is_active
    
    def _validate_bio(self) -> None:
        """Validate biography constraints."""
        if self.bio is not None:
            if len(self.bio) > 2000:
                raise ValueError("Bio cannot exceed 2000 characters")
    
    def _validate_birth_date(self) -> None:
        """Validate birth date constraints."""
        if self.birth_date:
            if self.birth_date > date.today():
                raise ValueError("Birth date cannot be in the future")
            
            if self.birth_date.year < 1900:
                raise ValueError("Birth date cannot be before 1900")
    
    def __eq__(self, other) -> bool:
        """Two authors are equal if they have the same ID."""
        if not isinstance(other, Author):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dictionaries."""
        return hash(self.id)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        status = "Active" if self.is_active else "Inactive"
        return f"Author({self.name.full_name}, {status})"
```

### Complete Book Entity

```python
# src/domain/entities/book.py
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from datetime import date, datetime
from decimal import Decimal

from ..value_objects.book_title import BookTitle
from ..value_objects.isbn import ISBN
from ..value_objects.money import Money

@dataclass
class Book:
    """
    Book entity representing a published book.
    
    A book is a published work with a unique identity (ISBN) that can be
    sold, inventoried, and associated with an author.
    """
    
    # Identity
    id: UUID = field(default_factory=uuid4)
    
    # Core attributes
    title: BookTitle = field()
    isbn: ISBN = field()
    author_id: UUID = field()
    
    # Publication details
    publication_date: Optional[date] = None
    page_count: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    
    # Commercial attributes
    price: Money = field(default_factory=lambda: Money(Decimal("0.00"), "USD"))
    stock_quantity: int = 0
    
    # Status and metadata
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate entity state after initialization."""
        self._validate_page_count()
        self._validate_stock_quantity()
        self._validate_publication_date()
    
    @classmethod
    def create(
        cls,
        title: BookTitle,
        isbn: ISBN,
        author_id: UUID,
        price: Money,
        publication_date: Optional[date] = None,
        page_count: Optional[int] = None,
        genre: Optional[str] = None,
        description: Optional[str] = None,
        initial_stock: int = 0
    ) -> "Book":
        """
        Create a new book with business rule validation.
        
        Args:
            title: Book title
            isbn: International Standard Book Number
            author_id: ID of the book's author
            price: Book price
            publication_date: When the book was published
            page_count: Number of pages
            genre: Book genre/category
            description: Book description
            initial_stock: Initial stock quantity
            
        Returns:
            New Book instance
            
        Raises:
            ValueError: If business rules are violated
        """
        return cls(
            title=title,
            isbn=isbn,
            author_id=author_id,
            price=price,
            publication_date=publication_date,
            page_count=page_count,
            genre=genre,
            description=description,
            stock_quantity=initial_stock
        )
    
    def update_price(self, new_price: Money) -> None:
        """
        Update the book's price.
        
        Args:
            new_price: New price for the book
            
        Raises:
            ValueError: If price is negative
        """
        if new_price.amount < 0:
            raise ValueError("Price cannot be negative")
        
        self.price = new_price
        self.updated_at = datetime.now()
    
    def add_stock(self, quantity: int) -> None:
        """
        Add stock to inventory.
        
        Args:
            quantity: Number of books to add
            
        Raises:
            ValueError: If quantity is negative
        """
        if quantity < 0:
            raise ValueError("Cannot add negative stock")
        
        self.stock_quantity += quantity
        self.updated_at = datetime.now()
    
    def remove_stock(self, quantity: int) -> None:
        """
        Remove stock from inventory.
        
        Args:
            quantity: Number of books to remove
            
        Raises:
            ValueError: If trying to remove more stock than available
        """
        if quantity < 0:
            raise ValueError("Cannot remove negative stock")
        
        if quantity > self.stock_quantity:
            raise ValueError(
                f"Cannot remove {quantity} books. Only {self.stock_quantity} in stock"
            )
        
        self.stock_quantity -= quantity
        self.updated_at = datetime.now()
    
    def is_available(self) -> bool:
        """
        Check if the book is available for purchase.
        
        Returns:
            True if book is active and in stock
        """
        return self.is_active and self.stock_quantity > 0
    
    def is_out_of_stock(self) -> bool:
        """
        Check if the book is out of stock.
        
        Returns:
            True if stock quantity is zero
        """
        return self.stock_quantity == 0
    
    def get_availability_status(self) -> str:
        """
        Get human-readable availability status.
        
        Returns:
            Status string
        """
        if not self.is_active:
            return "Discontinued"
        elif self.stock_quantity == 0:
            return "Out of Stock"
        elif self.stock_quantity < 5:
            return "Low Stock"
        else:
            return "In Stock"
    
    def apply_discount(self, discount_percentage: Decimal) -> Money:
        """
        Calculate discounted price.
        
        Args:
            discount_percentage: Discount as percentage (0-100)
            
        Returns:
            Discounted price
            
        Raises:
            ValueError: If discount is invalid
        """
        if discount_percentage < 0 or discount_percentage > 100:
            raise ValueError("Discount must be between 0 and 100 percent")
        
        discount_multiplier = (100 - discount_percentage) / 100
        discounted_amount = self.price.amount * discount_multiplier
        
        return Money(discounted_amount, self.price.currency)
    
    def deactivate(self) -> None:
        """Deactivate the book (discontinue)."""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def reactivate(self) -> None:
        """Reactivate a previously deactivated book."""
        self.is_active = True
        self.updated_at = datetime.now()
    
    def _validate_page_count(self) -> None:
        """Validate page count constraints."""
        if self.page_count is not None and self.page_count <= 0:
            raise ValueError("Page count must be positive")
    
    def _validate_stock_quantity(self) -> None:
        """Validate stock quantity constraints."""
        if self.stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative")
    
    def _validate_publication_date(self) -> None:
        """Validate publication date constraints."""
        if self.publication_date and self.publication_date > date.today():
            raise ValueError("Publication date cannot be in the future")
    
    def __eq__(self, other) -> bool:
        """Two books are equal if they have the same ID."""
        if not isinstance(other, Book):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dictionaries."""
        return hash(self.id)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"Book({self.title.value}, ISBN: {self.isbn.value})"
```

## 🧪 Testing Entities

```python
# tests/unit/domain/entities/test_author.py
import pytest
from datetime import date, datetime
from uuid import UUID

from src.domain.entities.author import Author
from src.domain.value_objects.author_name import AuthorName
from src.domain.value_objects.email import Email

class TestAuthor:
    def test_create_author_generates_unique_id(self):
        """Test that each author gets a unique ID."""
        name = AuthorName("John", "Doe")
        
        author1 = Author.create(name=name)
        author2 = Author.create(name=name)
        
        assert isinstance(author1.id, UUID)
        assert isinstance(author2.id, UUID)
        assert author1.id != author2.id
    
    def test_create_author_with_young_age_raises_error(self):
        """Test that authors under 16 cannot be created."""
        name = AuthorName("Young", "Author")
        birth_date = date.today().replace(year=date.today().year - 15)
        
        with pytest.raises(ValueError, match="Authors must be at least 16 years old"):
            Author.create(name=name, birth_date=birth_date)
    
    def test_update_bio_with_valid_bio(self):
        """Test updating bio with valid content."""
        author = Author.create(name=AuthorName("Jane", "Smith"))
        bio = "Jane Smith is a renowned author of fantasy novels with over 20 years of experience."
        
        author.update_bio(bio)
        
        assert author.bio == bio
        assert author.updated_at > author.created_at
    
    def test_update_bio_with_short_bio_raises_error(self):
        """Test that short bios are rejected."""
        author = Author.create(name=AuthorName("Jane", "Smith"))
        
        with pytest.raises(ValueError, match="Bio must be at least 10 characters long"):
            author.update_bio("Too short")
    
    def test_deactivate_author(self):
        """Test author deactivation."""
        author = Author.create(name=AuthorName("John", "Doe"))
        
        assert author.is_active is True
        assert author.can_publish_book() is True
        
        author.deactivate()
        
        assert author.is_active is False
        assert author.can_publish_book() is False
    
    def test_get_age_calculation(self):
        """Test age calculation."""
        birth_date = date(1980, 6, 15)
        author = Author.create(
            name=AuthorName("John", "Doe"),
            birth_date=birth_date
        )
        
        age = author.get_age()
        expected_age = date.today().year - 1980
        
        # Age should be within 1 year of expected (accounting for birthday)
        assert age in [expected_age - 1, expected_age]
    
    def test_author_equality_based_on_id(self):
        """Test that authors are equal based on ID."""
        name = AuthorName("John", "Doe")
        author1 = Author.create(name=name)
        author2 = Author.create(name=name)
        
        # Different authors with same name are not equal
        assert author1 != author2
        
        # Same author instance is equal to itself
        assert author1 == author1
```

## ✅ Best Practices

### Entity Design
- **Single Responsibility**: Each entity should represent one business concept
- **Rich Behavior**: Include business methods, not just data containers
- **Invariant Protection**: Validate business rules within the entity
- **Immutable Identity**: ID should never change once set
- **Meaningful Names**: Use domain language for methods and properties

### Business Rules
- **Encapsulation**: Keep business rules inside the entity
- **Validation**: Validate state in constructors and setters
- **Consistency**: Ensure entity is always in a valid state
- **Domain Language**: Use terms from the business domain

### Implementation
- **Value Objects**: Use value objects for complex attributes
- **Factory Methods**: Provide clear creation methods
- **Defensive Programming**: Validate inputs and state
- **Immutable When Possible**: Prefer immutable attributes where appropriate

## ❌ Common Pitfalls

- **Anemic Entities**: Entities with only getters/setters and no behavior
- **God Entities**: Entities that know too much or do too much
- **Infrastructure Leakage**: Adding database or web framework dependencies
- **Weak Invariants**: Not enforcing business rules consistently
- **Identity Confusion**: Changing entity identity or using wrong equality logic

## 🔄 Integration Points

Entities interact with other layers through:
- **Application Layer**: Use cases orchestrate entity operations
- **Infrastructure Layer**: Repositories persist and retrieve entities
- **Domain Services**: Complex operations involving multiple entities

Remember: Entities should never directly depend on other layers!

