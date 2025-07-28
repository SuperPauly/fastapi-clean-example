# Domain Services (`src/domain/services/`)

Domain Services contain business logic that doesn't naturally belong to a single entity or value object. They represent operations, calculations, or business rules that involve multiple domain objects or require external knowledge that entities shouldn't have.

## 🎯 What are Domain Services?

Domain Services are **stateless** objects that:
- Contain **business logic** that spans multiple entities
- Implement **complex business rules** that don't fit in a single entity
- Coordinate **operations** between different domain objects
- Provide **calculations** based on business rules
- Remain **technology-agnostic** (no infrastructure dependencies)

## 🏗️ Key Characteristics

### 1. **Stateless**
- No instance variables or persistent state
- All data comes from method parameters
- Can be implemented as static methods or singleton instances

### 2. **Business-Focused**
- Express business concepts and operations
- Use domain language and terminology
- Implement business rules and policies

### 3. **Coordination**
- Orchestrate operations between multiple entities
- Handle complex business workflows
- Manage business invariants across entities

### 4. **Pure Domain Logic**
- No dependencies on infrastructure concerns
- No knowledge of databases, web frameworks, or external services
- Can be tested without mocks or external dependencies

## 🔧 When to Use Domain Services

Use Domain Services when:
- **Business logic spans multiple entities** - Operations involving several domain objects
- **Complex calculations** - Business rules requiring multiple inputs or complex algorithms
- **Business policies** - Rules that determine how the business operates
- **Domain concepts without natural entity home** - Operations that don't belong to any single entity
- **Avoiding entity bloat** - Keeping entities focused on their core responsibilities

## 📋 Implementation Examples

### LibraryService - Core Business Operations

```python
# src/domain/services/library_service.py
from typing import List, Optional, Dict, Set
from datetime import date, timedelta
from decimal import Decimal

from ..entities.author import Author
from ..entities.book import Book
from ..value_objects.money import Money
from ..value_objects.isbn import ISBN

class LibraryService:
    """
    Domain service for core library business operations.
    
    Handles business logic that involves multiple entities or
    complex business rules that don't belong to a single entity.
    """
    
    @staticmethod
    def calculate_author_royalty(
        author: Author,
        books: List[Book],
        sales_data: Dict[str, int],
        royalty_rates: Optional[Dict[str, Decimal]] = None
    ) -> Money:
        """
        Calculate total royalty payments for an author.
        
        Business Rules:
        - Standard royalty rate is 10%
        - Bestsellers (>1000 sales) get 15%
        - Premium authors get custom rates
        - Only active books count toward royalties
        
        Args:
            author: The author to calculate royalties for
            books: List of books by the author
            sales_data: Dictionary mapping book ID to sales count
            royalty_rates: Optional custom royalty rates by author ID
            
        Returns:
            Total royalty amount in USD
        """
        if not author.is_active:
            return Money.zero("USD")
        
        total_royalty = Money.zero("USD")
        author_books = [book for book in books if book.author_id == author.id]
        
        # Get custom royalty rate for this author
        base_rate = Decimal("0.10")  # 10% default
        if royalty_rates and str(author.id) in royalty_rates:
            base_rate = royalty_rates[str(author.id)]
        
        for book in author_books:
            if not book.is_active:
                continue
                
            book_sales = sales_data.get(str(book.id), 0)
            if book_sales == 0:
                continue
            
            # Determine royalty rate based on sales performance
            royalty_rate = base_rate
            if book_sales > 1000:  # Bestseller bonus
                royalty_rate = min(royalty_rate + Decimal("0.05"), Decimal("0.20"))
            
            # Calculate royalty for this book
            book_revenue = book.price.multiply(book_sales)
            book_royalty = book_revenue.multiply(royalty_rate)
            
            total_royalty = total_royalty.add(book_royalty)
        
        return total_royalty
    
    @staticmethod
    def can_author_publish_book(
        author: Author,
        existing_books: List[Book],
        proposed_publication_date: Optional[date] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if an author can publish a new book based on business rules.
        
        Business Rules:
        - Author must be active
        - Authors can only publish 2 books per calendar year
        - Must wait at least 6 months between publications
        - Cannot have more than 5 unpublished books in pipeline
        
        Args:
            author: The author wanting to publish
            existing_books: All existing books by the author
            proposed_publication_date: When the book would be published
            
        Returns:
            Tuple of (can_publish, reason_if_not)
        """
        if not author.is_active:
            return False, "Author is not active"
        
        pub_date = proposed_publication_date or date.today()
        current_year = pub_date.year
        
        # Check yearly limit
        books_this_year = [
            book for book in existing_books
            if (book.author_id == author.id and
                book.publication_date and
                book.publication_date.year == current_year)
        ]
        
        if len(books_this_year) >= 2:
            return False, f"Author has already published {len(books_this_year)} books in {current_year}"
        
        # Check minimum time between publications
        recent_books = [
            book for book in existing_books
            if (book.author_id == author.id and
                book.publication_date and
                book.publication_date >= pub_date - timedelta(days=180))
        ]
        
        if recent_books:
            last_pub_date = max(book.publication_date for book in recent_books)
            days_since = (pub_date - last_pub_date).days
            if days_since < 180:
                return False, f"Must wait {180 - days_since} more days since last publication"
        
        # Check pipeline limit (books without publication date)
        unpublished_books = [
            book for book in existing_books
            if book.author_id == author.id and book.publication_date is None
        ]
        
        if len(unpublished_books) >= 5:
            return False, "Author has too many unpublished books in pipeline"
        
        return True, None
    
    @staticmethod
    def suggest_book_price(
        book: Book,
        market_data: Dict[str, any],
        competitor_prices: List[Money]
    ) -> Money:
        """
        Suggest optimal pricing for a book based on market analysis.
        
        Business Rules:
        - Base price starts at $15.00
        - Adjust for page count (longer books cost more)
        - Adjust for genre popularity
        - Consider competitor pricing
        - Apply author reputation multiplier
        
        Args:
            book: The book to price
            market_data: Market analysis data
            competitor_prices: Prices of similar books
            
        Returns:
            Suggested price in USD
        """
        base_price = Decimal("15.00")
        
        # Page count adjustment
        if book.page_count:
            if book.page_count > 500:
                base_price *= Decimal("1.5")  # Long books
            elif book.page_count > 300:
                base_price *= Decimal("1.2")  # Medium books
            elif book.page_count < 200:
                base_price *= Decimal("0.8")  # Short books
        
        # Genre popularity adjustment
        genre_multipliers = market_data.get("genre_multipliers", {})
        if book.genre and book.genre in genre_multipliers:
            base_price *= Decimal(str(genre_multipliers[book.genre]))
        
        # Author reputation adjustment
        author_reputation = market_data.get("author_reputation", {}).get(
            str(book.author_id), "new"
        )
        reputation_multipliers = {
            "bestselling": Decimal("1.5"),
            "established": Decimal("1.2"),
            "emerging": Decimal("1.0"),
            "new": Decimal("0.9")
        }
        base_price *= reputation_multipliers.get(author_reputation, Decimal("1.0"))
        
        # Competitor pricing consideration
        if competitor_prices:
            avg_competitor_price = sum(
                price.amount for price in competitor_prices
            ) / len(competitor_prices)
            
            # Don't price more than 20% above average competitor price
            max_price = avg_competitor_price * Decimal("1.2")
            if base_price > max_price:
                base_price = max_price
            
            # Don't price less than 80% of average (maintain quality perception)
            min_price = avg_competitor_price * Decimal("0.8")
            if base_price < min_price:
                base_price = min_price
        
        return Money.create(base_price, "USD")
    
    @staticmethod
    def validate_isbn_uniqueness(
        isbn: ISBN,
        existing_books: List[Book],
        exclude_book_id: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that an ISBN is unique across all books.
        
        Business Rule: Each ISBN must be globally unique
        
        Args:
            isbn: ISBN to validate
            existing_books: All existing books in the system
            exclude_book_id: Book ID to exclude from check (for updates)
            
        Returns:
            Tuple of (is_unique, conflicting_book_title_if_not)
        """
        for book in existing_books:
            if exclude_book_id and str(book.id) == exclude_book_id:
                continue
                
            if book.isbn == isbn:
                return False, book.title.value
        
        return True, None
    
    @staticmethod
    def calculate_inventory_reorder_point(
        book: Book,
        sales_history: List[int],
        lead_time_days: int = 14
    ) -> int:
        """
        Calculate when to reorder book inventory.
        
        Business Rules:
        - Maintain enough stock for lead time + safety buffer
        - Safety buffer is 50% of average daily sales
        - Minimum reorder point is 5 books
        
        Args:
            book: Book to calculate reorder point for
            sales_history: Daily sales for the last 30 days
            lead_time_days: Days to receive new inventory
            
        Returns:
            Reorder point quantity
        """
        if not sales_history:
            return 5  # Minimum reorder point
        
        # Calculate average daily sales
        avg_daily_sales = sum(sales_history) / len(sales_history)
        
        # Calculate lead time demand
        lead_time_demand = avg_daily_sales * lead_time_days
        
        # Add safety stock (50% of average daily sales * lead time)
        safety_stock = (avg_daily_sales * lead_time_days) * Decimal("0.5")
        
        reorder_point = int(lead_time_demand + safety_stock)
        
        # Ensure minimum reorder point
        return max(reorder_point, 5)
    
    @staticmethod
    def determine_book_categories(
        book: Book,
        sales_data: Dict[str, int],
        all_books: List[Book]
    ) -> Set[str]:
        """
        Categorize books based on performance and characteristics.
        
        Categories:
        - "bestseller": Top 10% of sales
        - "new_release": Published within last 6 months
        - "backlist": Older books still selling
        - "slow_moving": Low sales velocity
        - "out_of_print": No longer available
        
        Args:
            book: Book to categorize
            sales_data: Sales data for all books
            all_books: All books for comparison
            
        Returns:
            Set of category strings
        """
        categories = set()
        book_sales = sales_data.get(str(book.id), 0)
        
        # Bestseller category (top 10% of sales)
        all_sales = [sales_data.get(str(b.id), 0) for b in all_books]
        all_sales.sort(reverse=True)
        if all_sales:
            top_10_percent_threshold = all_sales[len(all_sales) // 10]
            if book_sales >= top_10_percent_threshold:
                categories.add("bestseller")
        
        # New release category
        if book.publication_date:
            days_since_publication = (date.today() - book.publication_date).days
            if days_since_publication <= 180:  # 6 months
                categories.add("new_release")
            elif days_since_publication > 365 and book_sales > 0:
                categories.add("backlist")
        
        # Slow moving category
        if book_sales < 10 and book.publication_date:
            days_since_publication = (date.today() - book.publication_date).days
            if days_since_publication > 90:  # 3 months with low sales
                categories.add("slow_moving")
        
        # Out of print category
        if not book.is_active or book.stock_quantity == 0:
            categories.add("out_of_print")
        
        return categories
```

### PricingService - Specialized Business Logic

```python
# src/domain/services/pricing_service.py
from typing import List, Dict, Optional
from datetime import date, timedelta
from decimal import Decimal

from ..entities.book import Book
from ..value_objects.money import Money

class PricingService:
    """
    Domain service for pricing strategies and discount calculations.
    
    Handles complex pricing logic that involves multiple business rules
    and market considerations.
    """
    
    @staticmethod
    def calculate_bulk_discount(
        books: List[Book],
        quantities: List[int],
        customer_tier: str = "standard"
    ) -> tuple[Money, Money, Decimal]:
        """
        Calculate bulk purchase discounts.
        
        Business Rules:
        - 5-9 books: 5% discount
        - 10-24 books: 10% discount  
        - 25+ books: 15% discount
        - Premium customers get additional 5%
        - Educational customers get additional 10%
        
        Args:
            books: List of books being purchased
            quantities: Quantity for each book
            customer_tier: Customer tier (standard, premium, educational)
            
        Returns:
            Tuple of (original_total, discounted_total, discount_percentage)
        """
        if len(books) != len(quantities):
            raise ValueError("Books and quantities lists must have same length")
        
        # Calculate original total
        original_total = Money.zero("USD")
        for book, qty in zip(books, quantities):
            book_total = book.price.multiply(qty)
            original_total = original_total.add(book_total)
        
        # Calculate total quantity
        total_quantity = sum(quantities)
        
        # Determine base discount rate
        if total_quantity >= 25:
            base_discount = Decimal("0.15")  # 15%
        elif total_quantity >= 10:
            base_discount = Decimal("0.10")  # 10%
        elif total_quantity >= 5:
            base_discount = Decimal("0.05")   # 5%
        else:
            base_discount = Decimal("0.00")   # No discount
        
        # Apply customer tier bonus
        tier_bonuses = {
            "educational": Decimal("0.10"),  # Additional 10%
            "premium": Decimal("0.05"),      # Additional 5%
            "standard": Decimal("0.00")      # No bonus
        }
        
        tier_bonus = tier_bonuses.get(customer_tier, Decimal("0.00"))
        total_discount = min(base_discount + tier_bonus, Decimal("0.25"))  # Max 25%
        
        # Calculate discounted total
        discount_amount = original_total.multiply(total_discount)
        discounted_total = original_total.subtract(discount_amount)
        
        return original_total, discounted_total, total_discount
    
    @staticmethod
    def calculate_seasonal_pricing(
        book: Book,
        target_date: date,
        sales_history: Dict[str, List[int]]
    ) -> Money:
        """
        Adjust pricing based on seasonal demand patterns.
        
        Business Rules:
        - Academic books: Higher prices during semester starts
        - Holiday books: Higher prices in November-December
        - Summer reading: Lower prices in June-August
        - Back-to-school: Higher prices in August-September
        
        Args:
            book: Book to price
            target_date: Date for pricing
            sales_history: Historical sales data by month
            
        Returns:
            Seasonally adjusted price
        """
        base_price = book.price
        month = target_date.month
        
        # Determine seasonal multiplier based on genre and month
        seasonal_multipliers = {
            "academic": {
                1: Decimal("1.2"),   # Spring semester
                8: Decimal("1.3"),   # Fall semester
                9: Decimal("1.2"),   # Fall semester
            },
            "children": {
                11: Decimal("1.2"),  # Holiday season
                12: Decimal("1.3"),  # Holiday season
                6: Decimal("0.9"),   # Summer break
                7: Decimal("0.9"),   # Summer break
            },
            "fiction": {
                6: Decimal("1.1"),   # Summer reading
                7: Decimal("1.1"),   # Summer reading
                12: Decimal("1.1"),  # Holiday gifts
            }
        }
        
        genre_key = book.genre.lower() if book.genre else "fiction"
        multiplier = seasonal_multipliers.get(genre_key, {}).get(
            month, Decimal("1.0")
        )
        
        # Consider historical demand
        if sales_history and str(book.id) in sales_history:
            book_history = sales_history[str(book.id)]
            if len(book_history) >= 12:  # Full year of data
                current_month_sales = book_history[month - 1]
                avg_monthly_sales = sum(book_history) / 12
                
                if avg_monthly_sales > 0:
                    demand_ratio = current_month_sales / avg_monthly_sales
                    # Adjust multiplier based on historical demand
                    if demand_ratio > 1.5:
                        multiplier *= Decimal("1.1")
                    elif demand_ratio < 0.5:
                        multiplier *= Decimal("0.9")
        
        return base_price.multiply(multiplier)
    
    @staticmethod
    def calculate_dynamic_pricing(
        book: Book,
        current_stock: int,
        recent_sales_velocity: int,
        competitor_prices: List[Money],
        target_margin: Decimal = Decimal("0.40")
    ) -> Money:
        """
        Calculate dynamic pricing based on supply, demand, and competition.
        
        Business Rules:
        - Low stock + high demand = higher prices
        - High stock + low demand = lower prices
        - Stay competitive with market prices
        - Maintain minimum target margin
        
        Args:
            book: Book to price
            current_stock: Current inventory level
            recent_sales_velocity: Sales in last 7 days
            competitor_prices: List of competitor prices
            target_margin: Minimum profit margin to maintain
            
        Returns:
            Dynamically calculated price
        """
        base_price = book.price
        
        # Calculate supply/demand ratio
        if current_stock == 0:
            supply_demand_multiplier = Decimal("1.3")  # High demand, no supply
        elif current_stock < 10 and recent_sales_velocity > 5:
            supply_demand_multiplier = Decimal("1.2")  # Low stock, high demand
        elif current_stock > 50 and recent_sales_velocity < 2:
            supply_demand_multiplier = Decimal("0.8")  # High stock, low demand
        else:
            supply_demand_multiplier = Decimal("1.0")  # Balanced
        
        # Consider competitor pricing
        if competitor_prices:
            avg_competitor_price = sum(
                price.amount for price in competitor_prices
            ) / len(competitor_prices)
            
            competitor_adjusted_price = Money.create(avg_competitor_price, "USD")
            
            # Don't price more than 15% above average competitor
            max_competitive_price = competitor_adjusted_price.multiply(Decimal("1.15"))
            
            # Don't price less than 85% of average (quality perception)
            min_competitive_price = competitor_adjusted_price.multiply(Decimal("0.85"))
            
            # Apply supply/demand adjustment within competitive range
            target_price = base_price.multiply(supply_demand_multiplier)
            
            if target_price.amount > max_competitive_price.amount:
                target_price = max_competitive_price
            elif target_price.amount < min_competitive_price.amount:
                target_price = min_competitive_price
        else:
            target_price = base_price.multiply(supply_demand_multiplier)
        
        # Ensure minimum margin is maintained
        # Assuming cost is 60% of base price for margin calculation
        estimated_cost = base_price.multiply(Decimal("0.60"))
        minimum_price = estimated_cost.divide(Decimal("1.0") - target_margin)
        
        if target_price.amount < minimum_price.amount:
            target_price = minimum_price
        
        return target_price
```

## 🧪 Testing Domain Services

```python
# tests/unit/domain/services/test_library_service.py
import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from src.domain.services.library_service import LibraryService
from src.domain.entities.author import Author
from src.domain.entities.book import Book
from src.domain.value_objects.author_name import AuthorName
from src.domain.value_objects.book_title import BookTitle
from src.domain.value_objects.isbn import ISBN
from src.domain.value_objects.money import Money

class TestLibraryService:
    def test_calculate_author_royalty_with_no_sales(self):
        """Test royalty calculation with no sales."""
        author = Author.create(name=AuthorName("John", "Doe"))
        books = [
            Book.create(
                title=BookTitle("Test Book"),
                isbn=ISBN("978-0123456789"),
                author_id=author.id,
                price=Money.create(20, "USD")
            )
        ]
        sales_data = {}
        
        royalty = LibraryService.calculate_author_royalty(
            author, books, sales_data
        )
        
        assert royalty.amount == Decimal("0.00")
        assert royalty.currency == "USD"
    
    def test_calculate_author_royalty_with_standard_sales(self):
        """Test royalty calculation with standard sales."""
        author = Author.create(name=AuthorName("John", "Doe"))
        book = Book.create(
            title=BookTitle("Test Book"),
            isbn=ISBN("978-0123456789"),
            author_id=author.id,
            price=Money.create(20, "USD")
        )
        books = [book]
        sales_data = {str(book.id): 100}  # 100 sales
        
        royalty = LibraryService.calculate_author_royalty(
            author, books, sales_data
        )
        
        # 100 sales * $20 * 10% = $200
        assert royalty.amount == Decimal("200.00")
    
    def test_calculate_author_royalty_with_bestseller_bonus(self):
        """Test royalty calculation with bestseller bonus."""
        author = Author.create(name=AuthorName("John", "Doe"))
        book = Book.create(
            title=BookTitle("Bestseller"),
            isbn=ISBN("978-0123456789"),
            author_id=author.id,
            price=Money.create(25, "USD")
        )
        books = [book]
        sales_data = {str(book.id): 1500}  # Bestseller level
        
        royalty = LibraryService.calculate_author_royalty(
            author, books, sales_data
        )
        
        # 1500 sales * $25 * 15% (bestseller rate) = $5625
        assert royalty.amount == Decimal("5625.00")
    
    def test_can_author_publish_book_inactive_author(self):
        """Test that inactive authors cannot publish."""
        author = Author.create(name=AuthorName("John", "Doe"))
        author.deactivate()
        
        can_publish, reason = LibraryService.can_author_publish_book(
            author, []
        )
        
        assert can_publish is False
        assert "not active" in reason
    
    def test_can_author_publish_book_yearly_limit_exceeded(self):
        """Test yearly publication limit."""
        author = Author.create(name=AuthorName("John", "Doe"))
        
        # Create 2 books already published this year
        current_year = date.today().year
        existing_books = [
            Book.create(
                title=BookTitle(f"Book {i}"),
                isbn=ISBN(f"978-012345678{i}"),
                author_id=author.id,
                price=Money.create(20, "USD"),
                publication_date=date(current_year, i + 1, 1)
            )
            for i in range(2)
        ]
        
        can_publish, reason = LibraryService.can_author_publish_book(
            author, existing_books
        )
        
        assert can_publish is False
        assert "already published 2 books" in reason
    
    def test_can_author_publish_book_minimum_time_not_met(self):
        """Test minimum time between publications."""
        author = Author.create(name=AuthorName("John", "Doe"))
        
        # Book published 90 days ago (less than 180 day minimum)
        recent_book = Book.create(
            title=BookTitle("Recent Book"),
            isbn=ISBN("978-0123456789"),
            author_id=author.id,
            price=Money.create(20, "USD"),
            publication_date=date.today() - timedelta(days=90)
        )
        
        can_publish, reason = LibraryService.can_author_publish_book(
            author, [recent_book]
        )
        
        assert can_publish is False
        assert "Must wait" in reason
        assert "more days" in reason
    
    def test_suggest_book_price_with_page_count_adjustment(self):
        """Test price suggestion with page count adjustment."""
        book = Book.create(
            title=BookTitle("Long Book"),
            isbn=ISBN("978-0123456789"),
            author_id=uuid4(),
            price=Money.create(15, "USD"),
            page_count=600  # Long book
        )
        
        suggested_price = LibraryService.suggest_book_price(
            book, {}, []
        )
        
        # Base $15 * 1.5 for long book = $22.50
        assert suggested_price.amount == Decimal("22.50")
    
    def test_validate_isbn_uniqueness_with_conflict(self):
        """Test ISBN uniqueness validation with conflict."""
        isbn = ISBN("978-0123456789")
        existing_book = Book.create(
            title=BookTitle("Existing Book"),
            isbn=isbn,
            author_id=uuid4(),
            price=Money.create(20, "USD")
        )
        
        is_unique, conflicting_title = LibraryService.validate_isbn_uniqueness(
            isbn, [existing_book]
        )
        
        assert is_unique is False
        assert conflicting_title == "Existing Book"
    
    def test_validate_isbn_uniqueness_no_conflict(self):
        """Test ISBN uniqueness validation without conflict."""
        isbn = ISBN("978-0123456789")
        different_isbn = ISBN("978-9876543210")
        existing_book = Book.create(
            title=BookTitle("Existing Book"),
            isbn=different_isbn,
            author_id=uuid4(),
            price=Money.create(20, "USD")
        )
        
        is_unique, conflicting_title = LibraryService.validate_isbn_uniqueness(
            isbn, [existing_book]
        )
        
        assert is_unique is True
        assert conflicting_title is None
```

## ✅ Best Practices

### Design Principles
- **Keep them stateless** - No instance variables or mutable state
- **Focus on business logic** - Express domain concepts and rules
- **Use domain language** - Method names should reflect business operations
- **Single responsibility** - Each service should have a focused purpose
- **Avoid infrastructure dependencies** - Keep them pure domain logic

### Implementation Guidelines
- **Static methods preferred** - Unless you need dependency injection
- **Clear method signatures** - Make inputs and outputs explicit
- **Comprehensive validation** - Validate all inputs and business rules
- **Return meaningful results** - Include success/failure indicators and reasons
- **Document business rules** - Explain the "why" behind the logic

### Testing Strategy
- **Pure unit tests** - No mocks needed since services are stateless
- **Test business rules** - Verify all business logic paths
- **Test edge cases** - Boundary conditions and error scenarios
- **Test combinations** - Multiple business rules interacting
- **Use domain examples** - Test with realistic business scenarios

## ❌ Common Pitfalls

- **Anemic services** - Services that just orchestrate without business logic
- **Infrastructure leakage** - Adding database or web framework dependencies
- **God services** - Services that do too many unrelated things
- **Stateful services** - Adding instance variables or mutable state
- **Bypassing entities** - Manipulating entity data directly instead of through entity methods

## 🔄 Integration with Other Layers

Domain Services are used by:
- **Application Layer** - Use cases call domain services for complex operations
- **Other Domain Services** - Services can collaborate with each other
- **Domain Entities** - Entities can use services for operations they can't handle alone

Domain Services should never:
- **Call infrastructure directly** - Use ports/interfaces instead
- **Know about presentation concerns** - No knowledge of HTTP, UI, etc.
- **Manage transactions** - That's an infrastructure concern
- **Handle persistence** - Use repositories through application layer

## 📚 Additional Resources

- [Domain Services in Domain-Driven Design](https://martinfowler.com/bliki/EvansClassification.html)
- [When to Create a Domain Service](https://enterprisecraftsmanship.com/posts/domain-services-vs-application-services/)
- [Domain Services vs Application Services](https://stackoverflow.com/questions/2268699/domain-driven-design-domain-service-application-service)

