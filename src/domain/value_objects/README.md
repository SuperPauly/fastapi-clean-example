# Domain Value Objects (`src/domain/value_objects/`)

Value Objects are **immutable** objects that represent concepts in your domain that are defined by their attributes rather than their identity. They are fundamental building blocks that help create a rich, expressive domain model while ensuring data integrity and consistency.

## 🎯 What are Value Objects?

Value Objects are objects that:
- Have **no identity** - they are defined entirely by their attributes
- Are **immutable** - cannot be changed after creation
- Are **replaceable** - create new instances instead of modifying existing ones
- Have **value equality** - two value objects are equal if all their attributes are equal
- **Encapsulate validation** - ensure they are always in a valid state

## 🏗️ Key Characteristics

### 1. **No Identity**
- No unique identifier (ID) needed
- Identity is determined by the combination of all attributes
- Two value objects with the same attributes are considered identical

### 2. **Immutability**
- Cannot be modified after creation
- All attributes are read-only
- Operations return new instances rather than modifying existing ones

### 3. **Self-Validation**
- Validate their own state during construction
- Ensure business rules are always enforced
- Fail fast with clear error messages

### 4. **Value Equality**
- Equality based on all attributes, not object reference
- Implement `__eq__` and `__hash__` methods appropriately
- Can be safely used in sets and as dictionary keys

## 📁 Common Value Objects

Based on the domain model, here are typical value objects:

### AuthorName
Represents an author's full name with validation rules.

### BookTitle  
Represents a book title with formatting and length constraints.

### Email
Represents an email address with format validation.

### ISBN
Represents an International Standard Book Number with validation.

### Money
Represents a monetary amount with currency.

### DateRange
Represents a period between two dates.

## 🔧 Implementation Examples

### AuthorName Value Object

```python
# src/domain/value_objects/author_name.py
from dataclasses import dataclass
from typing import Optional
import re

@dataclass(frozen=True)
class AuthorName:
    """
    Value object representing an author's name.
    
    Encapsulates validation rules for author names and provides
    various formatting options.
    """
    
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate name components after initialization."""
        self._validate_first_name()
        self._validate_last_name()
        self._validate_middle_name()
        self._validate_characters()
    
    @classmethod
    def from_full_name(cls, full_name: str) -> "AuthorName":
        """
        Create AuthorName from a full name string.
        
        Args:
            full_name: Full name as a single string
            
        Returns:
            AuthorName instance
            
        Raises:
            ValueError: If name format is invalid
            
        Examples:
            >>> AuthorName.from_full_name("John Doe")
            AuthorName(first_name='John', last_name='Doe')
            
            >>> AuthorName.from_full_name("John Michael Doe")
            AuthorName(first_name='John', middle_name='Michael', last_name='Doe')
        """
        if not full_name or not full_name.strip():
            raise ValueError("Full name cannot be empty")
        
        parts = [part.strip() for part in full_name.strip().split() if part.strip()]
        
        if len(parts) < 2:
            raise ValueError("Full name must contain at least first and last name")
        
        if len(parts) == 2:
            return cls(first_name=parts[0], last_name=parts[1])
        
        # Multiple middle names are joined together
        return cls(
            first_name=parts[0],
            middle_name=" ".join(parts[1:-1]),
            last_name=parts[-1]
        )
    
    @property
    def full_name(self) -> str:
        """
        Get the full name as a formatted string.
        
        Returns:
            Full name with proper spacing
        """
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """
        Get name in 'Last, First' format for display purposes.
        
        Returns:
            Name in 'Last, First Middle' format
        """
        if self.middle_name:
            return f"{self.last_name}, {self.first_name} {self.middle_name}"
        return f"{self.last_name}, {self.first_name}"
    
    @property
    def initials(self) -> str:
        """
        Get the initials of the name.
        
        Returns:
            Initials with periods (e.g., "J.M.D.")
        """
        initials = f"{self.first_name[0]}.{self.last_name[0]}."
        if self.middle_name:
            middle_initials = "".join([f"{name[0]}." for name in self.middle_name.split()])
            initials = f"{self.first_name[0]}.{middle_initials}{self.last_name[0]}."
        return initials
    
    @property
    def sort_key(self) -> str:
        """
        Get a key suitable for sorting names alphabetically.
        
        Returns:
            Sort key in 'Last, First, Middle' format
        """
        return self.display_name.lower()
    
    def with_middle_name(self, middle_name: str) -> "AuthorName":
        """
        Create a new AuthorName with a middle name added.
        
        Args:
            middle_name: Middle name to add
            
        Returns:
            New AuthorName instance with middle name
        """
        return AuthorName(
            first_name=self.first_name,
            last_name=self.last_name,
            middle_name=middle_name.strip()
        )
    
    def without_middle_name(self) -> "AuthorName":
        """
        Create a new AuthorName without the middle name.
        
        Returns:
            New AuthorName instance without middle name
        """
        return AuthorName(
            first_name=self.first_name,
            last_name=self.last_name
        )
    
    def _validate_first_name(self) -> None:
        """Validate first name constraints."""
        if not self.first_name or not self.first_name.strip():
            raise ValueError("First name cannot be empty")
        
        if len(self.first_name) > 50:
            raise ValueError("First name cannot exceed 50 characters")
        
        if len(self.first_name.strip()) < 2:
            raise ValueError("First name must be at least 2 characters long")
    
    def _validate_last_name(self) -> None:
        """Validate last name constraints."""
        if not self.last_name or not self.last_name.strip():
            raise ValueError("Last name cannot be empty")
        
        if len(self.last_name) > 50:
            raise ValueError("Last name cannot exceed 50 characters")
        
        if len(self.last_name.strip()) < 2:
            raise ValueError("Last name must be at least 2 characters long")
    
    def _validate_middle_name(self) -> None:
        """Validate middle name constraints."""
        if self.middle_name is not None:
            if len(self.middle_name) > 100:
                raise ValueError("Middle name cannot exceed 100 characters")
            
            if not self.middle_name.strip():
                raise ValueError("Middle name cannot be empty if provided")
    
    def _validate_characters(self) -> None:
        """Validate that names contain only allowed characters."""
        # Allow letters, spaces, hyphens, apostrophes, and periods
        name_pattern = re.compile(r"^[a-zA-Z\s\-'.]+$")
        
        if not name_pattern.match(self.first_name):
            raise ValueError("First name contains invalid characters")
        
        if not name_pattern.match(self.last_name):
            raise ValueError("Last name contains invalid characters")
        
        if self.middle_name and not name_pattern.match(self.middle_name):
            raise ValueError("Middle name contains invalid characters")
```

### Email Value Object

```python
# src/domain/value_objects/email.py
from dataclasses import dataclass
import re
from typing import Optional

@dataclass(frozen=True)
class Email:
    """
    Value object representing an email address.
    
    Ensures email addresses are valid and provides utility methods
    for working with email addresses.
    """
    
    value: str
    
    def __post_init__(self):
        """Validate email format after initialization."""
        self._validate_format()
        self._validate_length()
        # Normalize the email address
        object.__setattr__(self, 'value', self.value.lower().strip())
    
    @classmethod
    def create(cls, email: str) -> "Email":
        """
        Create an Email instance with validation.
        
        Args:
            email: Email address string
            
        Returns:
            Email instance
            
        Raises:
            ValueError: If email format is invalid
        """
        return cls(value=email)
    
    @property
    def local_part(self) -> str:
        """
        Get the local part of the email (before @).
        
        Returns:
            Local part of the email address
        """
        return self.value.split('@')[0]
    
    @property
    def domain(self) -> str:
        """
        Get the domain part of the email (after @).
        
        Returns:
            Domain part of the email address
        """
        return self.value.split('@')[1]
    
    @property
    def is_business_email(self) -> bool:
        """
        Check if this appears to be a business email.
        
        Returns:
            True if likely a business email, False otherwise
        """
        personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'protonmail.com'
        }
        return self.domain.lower() not in personal_domains
    
    def mask_for_display(self) -> str:
        """
        Create a masked version for display purposes.
        
        Returns:
            Masked email address (e.g., "j***@example.com")
        """
        local = self.local_part
        if len(local) <= 2:
            masked_local = local[0] + '*'
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{self.domain}"
    
    def get_suggested_username(self) -> str:
        """
        Generate a suggested username from the email.
        
        Returns:
            Suggested username based on local part
        """
        # Remove common separators and numbers
        username = re.sub(r'[._\-+]', '', self.local_part)
        username = re.sub(r'\d+$', '', username)  # Remove trailing numbers
        return username.lower()
    
    def _validate_format(self) -> None:
        """Validate email format using regex."""
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        # RFC 5322 compliant email regex (simplified)
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        if not email_pattern.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
        
        # Additional checks
        if '..' in self.value:
            raise ValueError("Email cannot contain consecutive dots")
        
        if self.value.startswith('.') or self.value.endswith('.'):
            raise ValueError("Email cannot start or end with a dot")
    
    def _validate_length(self) -> None:
        """Validate email length constraints."""
        if len(self.value) > 254:  # RFC 5321 limit
            raise ValueError("Email address too long (max 254 characters)")
        
        local_part, domain_part = self.value.split('@')
        
        if len(local_part) > 64:  # RFC 5321 limit
            raise ValueError("Email local part too long (max 64 characters)")
        
        if len(domain_part) > 253:  # RFC 5321 limit
            raise ValueError("Email domain part too long (max 253 characters)")
```

### Money Value Object

```python
# src/domain/value_objects/money.py
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

@dataclass(frozen=True)
class Money:
    """
    Value object representing a monetary amount with currency.
    
    Handles currency operations, formatting, and validation while
    ensuring precision with decimal arithmetic.
    """
    
    amount: Decimal
    currency: str
    
    def __post_init__(self):
        """Validate money constraints after initialization."""
        self._validate_amount()
        self._validate_currency()
        # Ensure amount has proper decimal precision
        object.__setattr__(
            self, 
            'amount', 
            self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )
    
    @classmethod
    def create(cls, amount: Union[str, int, float, Decimal], currency: str) -> "Money":
        """
        Create Money instance with type conversion.
        
        Args:
            amount: Monetary amount (will be converted to Decimal)
            currency: Currency code (e.g., 'USD', 'EUR')
            
        Returns:
            Money instance
        """
        if isinstance(amount, (int, float)):
            decimal_amount = Decimal(str(amount))
        elif isinstance(amount, str):
            decimal_amount = Decimal(amount)
        else:
            decimal_amount = amount
        
        return cls(amount=decimal_amount, currency=currency.upper())
    
    @classmethod
    def zero(cls, currency: str) -> "Money":
        """
        Create a zero amount in the specified currency.
        
        Args:
            currency: Currency code
            
        Returns:
            Money instance with zero amount
        """
        return cls(amount=Decimal('0.00'), currency=currency.upper())
    
    def add(self, other: "Money") -> "Money":
        """
        Add two money amounts.
        
        Args:
            other: Money to add
            
        Returns:
            New Money instance with sum
            
        Raises:
            ValueError: If currencies don't match
        """
        self._ensure_same_currency(other)
        return Money(
            amount=self.amount + other.amount,
            currency=self.currency
        )
    
    def subtract(self, other: "Money") -> "Money":
        """
        Subtract money amount.
        
        Args:
            other: Money to subtract
            
        Returns:
            New Money instance with difference
            
        Raises:
            ValueError: If currencies don't match
        """
        self._ensure_same_currency(other)
        return Money(
            amount=self.amount - other.amount,
            currency=self.currency
        )
    
    def multiply(self, factor: Union[int, float, Decimal]) -> "Money":
        """
        Multiply money by a factor.
        
        Args:
            factor: Multiplication factor
            
        Returns:
            New Money instance with product
        """
        if isinstance(factor, (int, float)):
            factor = Decimal(str(factor))
        
        return Money(
            amount=self.amount * factor,
            currency=self.currency
        )
    
    def divide(self, divisor: Union[int, float, Decimal]) -> "Money":
        """
        Divide money by a divisor.
        
        Args:
            divisor: Division factor
            
        Returns:
            New Money instance with quotient
            
        Raises:
            ValueError: If divisor is zero
        """
        if isinstance(divisor, (int, float)):
            divisor = Decimal(str(divisor))
        
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        
        return Money(
            amount=self.amount / divisor,
            currency=self.currency
        )
    
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0
    
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < 0
    
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0
    
    def abs(self) -> "Money":
        """Get absolute value."""
        return Money(amount=abs(self.amount), currency=self.currency)
    
    def format(self, locale: str = "en_US") -> str:
        """
        Format money for display.
        
        Args:
            locale: Locale for formatting
            
        Returns:
            Formatted money string
        """
        # Simple formatting - in real implementation, use locale-specific formatting
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥'
        }
        
        symbol = currency_symbols.get(self.currency, self.currency)
        
        if self.currency == 'JPY':
            # Japanese Yen doesn't use decimal places
            return f"{symbol}{int(self.amount):,}"
        
        return f"{symbol}{self.amount:,.2f}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'amount': str(self.amount),
            'currency': self.currency
        }
    
    def _validate_amount(self) -> None:
        """Validate amount constraints."""
        if not isinstance(self.amount, Decimal):
            raise ValueError("Amount must be a Decimal")
    
    def _validate_currency(self) -> None:
        """Validate currency code."""
        if not self.currency:
            raise ValueError("Currency cannot be empty")
        
        if not isinstance(self.currency, str):
            raise ValueError("Currency must be a string")
        
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code")
        
        if not self.currency.isalpha():
            raise ValueError("Currency must contain only letters")
    
    def _ensure_same_currency(self, other: "Money") -> None:
        """Ensure two money objects have the same currency."""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} and {other.currency}"
            )
    
    def __str__(self) -> str:
        """String representation."""
        return self.format()
    
    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        self._ensure_same_currency(other)
        return self.amount < other.amount
    
    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        self._ensure_same_currency(other)
        return self.amount <= other.amount
    
    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        self._ensure_same_currency(other)
        return self.amount > other.amount
    
    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        self._ensure_same_currency(other)
        return self.amount >= other.amount
```

## 🧪 Testing Value Objects

```python
# tests/unit/domain/value_objects/test_author_name.py
import pytest
from src.domain.value_objects.author_name import AuthorName

class TestAuthorName:
    def test_create_simple_name(self):
        """Test creating a simple first/last name."""
        name = AuthorName("John", "Doe")
        
        assert name.first_name == "John"
        assert name.last_name == "Doe"
        assert name.middle_name is None
        assert name.full_name == "John Doe"
        assert name.display_name == "Doe, John"
    
    def test_create_name_with_middle_name(self):
        """Test creating a name with middle name."""
        name = AuthorName("John", "Doe", "Michael")
        
        assert name.middle_name == "Michael"
        assert name.full_name == "John Michael Doe"
        assert name.display_name == "Doe, John Michael"
    
    def test_from_full_name_simple(self):
        """Test creating from full name string."""
        name = AuthorName.from_full_name("John Doe")
        
        assert name.first_name == "John"
        assert name.last_name == "Doe"
        assert name.middle_name is None
    
    def test_from_full_name_with_middle(self):
        """Test creating from full name with middle name."""
        name = AuthorName.from_full_name("John Michael Doe")
        
        assert name.first_name == "John"
        assert name.middle_name == "Michael"
        assert name.last_name == "Doe"
    
    def test_empty_first_name_raises_error(self):
        """Test that empty first name raises error."""
        with pytest.raises(ValueError, match="First name cannot be empty"):
            AuthorName("", "Doe")
    
    def test_empty_last_name_raises_error(self):
        """Test that empty last name raises error."""
        with pytest.raises(ValueError, match="Last name cannot be empty"):
            AuthorName("John", "")
    
    def test_invalid_characters_raise_error(self):
        """Test that invalid characters raise error."""
        with pytest.raises(ValueError, match="First name contains invalid characters"):
            AuthorName("John123", "Doe")
    
    def test_initials_property(self):
        """Test initials generation."""
        name = AuthorName("John", "Doe")
        assert name.initials == "J.D."
        
        name_with_middle = AuthorName("John", "Doe", "Michael")
        assert name_with_middle.initials == "J.M.D."
    
    def test_value_equality(self):
        """Test that names with same values are equal."""
        name1 = AuthorName("John", "Doe")
        name2 = AuthorName("John", "Doe")
        name3 = AuthorName("Jane", "Doe")
        
        assert name1 == name2
        assert name1 != name3
        assert hash(name1) == hash(name2)
    
    def test_immutability(self):
        """Test that AuthorName is immutable."""
        name = AuthorName("John", "Doe")
        
        # This should raise an error since the object is frozen
        with pytest.raises(AttributeError):
            name.first_name = "Jane"
```

## ✅ Best Practices

### Design Principles
- **Make them immutable** - Use `@dataclass(frozen=True)` or similar
- **Validate in constructor** - Fail fast with clear error messages
- **Use meaningful names** - Names should reflect domain concepts
- **Keep them simple** - Focus on a single concept or closely related attributes
- **Provide utility methods** - Add methods that make sense for the concept

### Implementation Guidelines
- **Use appropriate types** - Decimal for money, datetime for dates, etc.
- **Implement equality** - Based on all attributes, not object identity
- **Provide factory methods** - For common creation patterns
- **Add formatting methods** - For display and serialization
- **Document business rules** - Explain validation logic in docstrings

### Testing Strategy
- **Test validation** - Ensure invalid values are rejected
- **Test equality** - Verify value-based equality works correctly
- **Test immutability** - Confirm objects cannot be modified
- **Test edge cases** - Boundary conditions and special values
- **Test utility methods** - All formatting and calculation methods

## ❌ Common Pitfalls

- **Mutable value objects** - Breaks the fundamental principle
- **Identity-based equality** - Should be value-based, not reference-based
- **Weak validation** - Not enforcing business rules consistently
- **Too complex** - Value objects should be simple and focused
- **Missing edge cases** - Not handling null, empty, or boundary values

## 🔄 Integration with Entities

Value objects are used within entities to:
- **Represent complex attributes** - Like names, addresses, money amounts
- **Enforce validation** - Business rules are enforced at the value object level
- **Provide rich behavior** - Methods for formatting, calculation, comparison
- **Ensure consistency** - Same validation rules applied everywhere

Example entity using value objects:
```python
@dataclass
class Author:
    id: UUID
    name: AuthorName  # Value object
    email: Email      # Value object
    # ... other attributes
```

This ensures that wherever an `AuthorName` or `Email` is used, it's always valid and provides consistent behavior.

