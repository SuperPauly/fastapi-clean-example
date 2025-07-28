# Services Directory (`services/`)

The **Services Directory** contains application-level services that orchestrate complex business workflows and coordinate between multiple use cases. These services provide higher-level operations and act as facades for complex domain operations in the hexagon architecture.

## 🎯 Purpose & Role in Hexagon Architecture

Services in this directory serve as **application orchestrators** that:
- **Coordinate multiple use cases** into complex workflows
- **Provide facade interfaces** for related operations
- **Handle cross-cutting concerns** like logging, caching, notifications
- **Manage external integrations** through defined ports
- **Simplify complex operations** for the presentation layer

```
Presentation Layer → Services → Use Cases → Domain Logic
       ↓              ↓          ↓           ↓
   Controllers → App Services → Business → Entities
```

## 🏗️ Key Responsibilities

### 1. **Workflow Orchestration**
- Combine multiple use cases into business workflows
- Handle complex multi-step operations
- Manage transaction boundaries across operations

### 2. **Cross-Cutting Concerns**
- Implement caching strategies
- Handle logging and monitoring
- Manage notifications and events

### 3. **External Integration**
- Coordinate with external services
- Handle data transformation between systems
- Manage API rate limiting and retries

## 📁 Service Structure

```
services/
├── author_service.py        # Author management operations
├── book_service.py          # Book catalog operations  
├── notification_service.py  # Email/SMS notifications
├── cache_service.py         # Caching operations
└── README.md               # This file
```

## 🔧 Implementation Examples

### Author Management Service

```python
# services/author_service.py
from typing import List, Optional, Dict
from uuid import UUID

from ..src.application.use_cases.create_author import CreateAuthorUseCase
from ..src.application.use_cases.update_author import UpdateAuthorUseCase
from ..src.application.ports.author_repository import AuthorRepositoryPort
from ..src.application.ports.logger import LoggerPort
from ..src.application.ports.cache import CachePort

class AuthorService:
    """
    High-level service for author management operations.
    
    Provides simplified interfaces for complex author-related
    workflows and handles cross-cutting concerns.
    """
    
    def __init__(
        self,
        create_author_use_case: CreateAuthorUseCase,
        update_author_use_case: UpdateAuthorUseCase,
        author_repository: AuthorRepositoryPort,
        logger: LoggerPort,
        cache: CachePort
    ):
        self._create_author_use_case = create_author_use_case
        self._update_author_use_case = update_author_use_case
        self._author_repository = author_repository
        self._logger = logger
        self._cache = cache
    
    async def register_author_with_onboarding(
        self,
        author_data: Dict,
        send_welcome_email: bool = True
    ) -> Dict:
        """
        Complete author registration with onboarding workflow.
        
        This method handles the full author registration process
        including creation, profile setup, and welcome communications.
        """
        await self._logger.info(f"Starting author registration for {author_data.get('email')}")
        
        try:
            # Step 1: Create the author
            result = await self._create_author_use_case.execute(author_data)
            
            if not result.success:
                return {"success": False, "message": result.message, "errors": result.errors}
            
            # Step 2: Send welcome email if requested
            if send_welcome_email and author_data.get('email'):
                await self._send_welcome_email(result.author_id, author_data['email'])
            
            # Step 3: Set up author profile defaults
            await self._setup_author_defaults(result.author_id)
            
            # Step 4: Cache author data for quick access
            author = await self._author_repository.find_by_id(result.author_id)
            await self._cache.set(f"author:{result.author_id}", author, ttl=3600)
            
            await self._logger.info(f"Author registration completed: {result.author_id}")
            
            return {
                "success": True,
                "author_id": result.author_id,
                "message": "Author registered successfully with onboarding completed"
            }
            
        except Exception as e:
            await self._logger.error(f"Author registration failed: {str(e)}")
            return {"success": False, "message": "Registration failed", "errors": [str(e)]}
    
    async def get_author_dashboard_data(self, author_id: UUID) -> Optional[Dict]:
        """Get comprehensive author dashboard information."""
        # Try cache first
        cache_key = f"author_dashboard:{author_id}"
        cached_data = await self._cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Fetch fresh data
        author = await self._author_repository.find_by_id(author_id)
        if not author:
            return None
        
        # Compile dashboard data
        dashboard_data = {
            "author_info": {
                "id": str(author.id),
                "name": author.name.full_name,
                "email": author.email.value if author.email else None,
                "is_active": author.is_active
            },
            "statistics": {
                "books_count": await self._author_repository.count_books_by_author(author_id),
                "total_sales": await self._author_repository.get_total_sales_by_author(author_id)
            }
        }
        
        # Cache for 30 minutes
        await self._cache.set(cache_key, dashboard_data, ttl=1800)
        
        return dashboard_data
    
    async def _send_welcome_email(self, author_id: UUID, email: str):
        """Send welcome email to new author."""
        # This would integrate with email service
        await self._logger.info(f"Sending welcome email to {email}")
    
    async def _setup_author_defaults(self, author_id: UUID):
        """Set up default author profile settings."""
        await self._logger.info(f"Setting up defaults for author {author_id}")
```

### Notification Service

```python
# services/notification_service.py
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

from ..src.application.ports.email_service import EmailServicePort
from ..src.application.ports.sms_service import SMSServicePort
from ..src.application.ports.logger import LoggerPort

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

@dataclass
class NotificationRequest:
    recipient: str
    message: str
    subject: Optional[str] = None
    notification_type: NotificationType = NotificationType.EMAIL
    template: Optional[str] = None
    template_data: Optional[Dict] = None

class NotificationService:
    """
    Service for handling various types of notifications.
    
    Provides a unified interface for sending emails, SMS,
    and other notifications with template support.
    """
    
    def __init__(
        self,
        email_service: EmailServicePort,
        sms_service: SMSServicePort,
        logger: LoggerPort
    ):
        self._email_service = email_service
        self._sms_service = sms_service
        self._logger = logger
    
    async def send_notification(self, request: NotificationRequest) -> bool:
        """Send a notification using the appropriate service."""
        try:
            if request.notification_type == NotificationType.EMAIL:
                return await self._send_email(request)
            elif request.notification_type == NotificationType.SMS:
                return await self._send_sms(request)
            else:
                await self._logger.warning(f"Unsupported notification type: {request.notification_type}")
                return False
                
        except Exception as e:
            await self._logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    async def send_bulk_notifications(self, requests: List[NotificationRequest]) -> Dict:
        """Send multiple notifications and return results."""
        results = {"successful": 0, "failed": 0, "errors": []}
        
        for request in requests:
            success = await self.send_notification(request)
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"Failed to send to {request.recipient}")
        
        return results
    
    async def _send_email(self, request: NotificationRequest) -> bool:
        """Send email notification."""
        if request.template:
            return await self._email_service.send_template_email(
                to=request.recipient,
                template=request.template,
                data=request.template_data or {}
            )
        else:
            return await self._email_service.send_email(
                to=request.recipient,
                subject=request.subject or "Notification",
                body=request.message
            )
    
    async def _send_sms(self, request: NotificationRequest) -> bool:
        """Send SMS notification."""
        return await self._sms_service.send_sms(
            to=request.recipient,
            message=request.message
        )
```

### Cache Service

```python
# services/cache_service.py
from typing import Any, Optional, Dict, List
from datetime import timedelta
import json
import hashlib

from ..src.application.ports.cache import CachePort
from ..src.application.ports.logger import LoggerPort

class CacheService:
    """
    Service for managing application-level caching strategies.
    
    Provides high-level caching operations with automatic
    serialization, key management, and cache invalidation.
    """
    
    def __init__(self, cache: CachePort, logger: LoggerPort):
        self._cache = cache
        self._logger = logger
        self._key_prefix = "app:"
    
    async def get_or_set(
        self,
        key: str,
        factory_func,
        ttl: int = 3600,
        **factory_kwargs
    ) -> Any:
        """
        Get value from cache or set it using factory function.
        
        Args:
            key: Cache key
            factory_func: Function to generate value if not cached
            ttl: Time to live in seconds
            **factory_kwargs: Arguments for factory function
        """
        full_key = self._build_key(key)
        
        # Try to get from cache
        cached_value = await self._cache.get(full_key)
        if cached_value is not None:
            await self._logger.debug(f"Cache hit for key: {key}")
            return cached_value
        
        # Generate new value
        await self._logger.debug(f"Cache miss for key: {key}, generating new value")
        new_value = await factory_func(**factory_kwargs)
        
        # Store in cache
        await self._cache.set(full_key, new_value, ttl=ttl)
        
        return new_value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        full_pattern = self._build_key(pattern)
        count = await self._cache.delete_pattern(full_pattern)
        await self._logger.info(f"Invalidated {count} cache keys matching pattern: {pattern}")
        return count
    
    async def warm_cache(self, cache_definitions: List[Dict]) -> Dict:
        """Warm cache with predefined data."""
        results = {"successful": 0, "failed": 0}
        
        for definition in cache_definitions:
            try:
                key = definition["key"]
                value = definition["value"]
                ttl = definition.get("ttl", 3600)
                
                await self._cache.set(self._build_key(key), value, ttl=ttl)
                results["successful"] += 1
                
            except Exception as e:
                await self._logger.error(f"Failed to warm cache for {definition}: {str(e)}")
                results["failed"] += 1
        
        return results
    
    def _build_key(self, key: str) -> str:
        """Build full cache key with prefix."""
        return f"{self._key_prefix}{key}"
```

## 🧪 Testing Services

```python
# tests/unit/services/test_author_service.py
import pytest
from unittest.mock import AsyncMock, Mock

from services.author_service import AuthorService

class TestAuthorService:
    @pytest.fixture
    def mock_dependencies(self):
        return {
            "create_author_use_case": AsyncMock(),
            "update_author_use_case": AsyncMock(),
            "author_repository": AsyncMock(),
            "logger": AsyncMock(),
            "cache": AsyncMock()
        }
    
    @pytest.fixture
    def service(self, mock_dependencies):
        return AuthorService(**mock_dependencies)
    
    @pytest.mark.asyncio
    async def test_register_author_with_onboarding_success(self, service, mock_dependencies):
        """Test successful author registration with onboarding."""
        # Arrange
        author_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        }
        
        mock_result = Mock()
        mock_result.success = True
        mock_result.author_id = "123e4567-e89b-12d3-a456-426614174000"
        
        mock_dependencies["create_author_use_case"].execute.return_value = mock_result
        
        # Act
        result = await service.register_author_with_onboarding(author_data)
        
        # Assert
        assert result["success"] is True
        assert result["author_id"] == mock_result.author_id
        mock_dependencies["create_author_use_case"].execute.assert_called_once()
```

## ✅ Best Practices

### Service Design
- **Keep services focused** on specific business areas
- **Use dependency injection** for all external dependencies
- **Handle errors gracefully** with proper logging
- **Implement caching strategies** for performance
- **Provide clear interfaces** for complex operations

### Cross-Cutting Concerns
- **Centralize logging** and monitoring logic
- **Implement consistent error handling** across services
- **Use caching strategically** for expensive operations
- **Handle external service failures** with retries and fallbacks

## ❌ Common Pitfalls

- **Making services too large** - Keep them focused and cohesive
- **Putting domain logic in services** - Delegate to domain layer
- **Not handling failures** - Always consider error scenarios
- **Tight coupling** - Use dependency injection and interfaces

## 🔄 Integration Points

Services integrate with:
- **Application Layer** - Use application use cases and ports
- **Presentation Layer** - Provide simplified interfaces for controllers
- **Infrastructure Layer** - Access external services through ports
- **Domain Layer** - Coordinate domain operations without containing business logic

The services directory provides essential orchestration capabilities that make complex business workflows manageable and maintainable in your hexagon architecture.

