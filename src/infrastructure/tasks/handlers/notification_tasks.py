"""Background task handlers for notifications."""

import asyncio
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from src.infrastructure.tasks.taskiq_adapter import broker
from src.infrastructure.logging.logger_adapter import LoguruLoggerAdapter

logger = LoguruLoggerAdapter()


class AuthorNotificationData(BaseModel):
    """Data model for author notification tasks."""
    id: str = Field(..., description="Author ID")
    name: str = Field(..., description="Author name")


class BookNotificationData(BaseModel):
    """Data model for book notification tasks."""
    id: str = Field(..., description="Book ID")
    title: str = Field(..., description="Book title")


@broker.task
async def send_author_created_notification(author_id: str, author_name: str) -> None:
    """Send notification when a new author is created."""
    logger.info(f"Sending author created notification for {author_name} (ID: {author_id})")
    
    # Here you would implement actual notification logic
    # For example: send email, push notification, webhook, etc.
    
    # Simulate some async work
    await asyncio.sleep(1)
    
    logger.info(f"Author created notification sent for {author_name}")


@broker.task
async def send_book_created_notification(book_id: str, book_title: str) -> None:
    """Send notification when a new book is created."""
    logger.info(f"Sending book created notification for {book_title} (ID: {book_id})")
    
    # Here you would implement actual notification logic
    # For example: send email, push notification, webhook, etc.
    
    # Simulate some async work
    await asyncio.sleep(1)
    
    logger.info(f"Book created notification sent for {book_title}")


@broker.task
async def cleanup_orphaned_records() -> None:
    """Periodic task to clean up orphaned records."""
    logger.info("Starting cleanup of orphaned records")
    
    # Here you would implement cleanup logic
    # For example: remove authors without books, books without authors, etc.
    
    # Simulate some async work
    await asyncio.sleep(2)
    
    logger.info("Cleanup of orphaned records completed")


# Note: Taskiq doesn't have built-in periodic tasks like Huey
# You would need to use an external scheduler like cron or implement custom scheduling
# For now, we'll provide a function that can be called to schedule the cleanup
async def schedule_daily_cleanup() -> str:
    """Schedule daily cleanup task."""
    # Schedule for next 2 AM
    tomorrow_2am = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
    if tomorrow_2am <= datetime.now():
        tomorrow_2am += timedelta(days=1)
    
    task_result = await cleanup_orphaned_records.kiq(eta=tomorrow_2am)
    return str(task_result.task_id)

