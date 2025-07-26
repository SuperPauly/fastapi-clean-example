"""Tests for Taskiq integration."""

import pytest
from taskiq import InMemoryBroker

from src.infrastructure.tasks.taskiq_adapter import TaskiqTaskQueueAdapter
from src.infrastructure.tasks.handlers.notification_tasks import (
    send_author_created_notification,
    send_book_created_notification,
    cleanup_orphaned_records,
)


class TestTaskiqIntegration:
    """Test Taskiq task queue integration."""
    
    @pytest.fixture
    def taskiq_adapter(self, in_memory_broker: InMemoryBroker) -> TaskiqTaskQueueAdapter:
        """Create TaskiqTaskQueueAdapter with in-memory broker."""
        return TaskiqTaskQueueAdapter(broker_instance=in_memory_broker)
    
    @pytest.mark.asyncio
    async def test_enqueue_task(self, taskiq_adapter: TaskiqTaskQueueAdapter):
        """Test enqueueing a task."""
        # Define a simple test task
        async def test_task(message: str) -> str:
            return f"Processed: {message}"
        
        # Enqueue the task
        task_id = await taskiq_adapter.enqueue(test_task, "Hello World")
        
        # Verify task was enqueued
        assert task_id is not None
        assert isinstance(task_id, str)
    
    @pytest.mark.asyncio
    async def test_enqueue_notification_task(self, taskiq_adapter: TaskiqTaskQueueAdapter):
        """Test enqueueing a notification task."""
        # Enqueue author notification task
        task_id = await taskiq_adapter.enqueue(
            send_author_created_notification,
            "test-author-id",
            "Test Author"
        )
        
        # Verify task was enqueued
        assert task_id is not None
        assert isinstance(task_id, str)
    
    @pytest.mark.asyncio
    async def test_schedule_task(self, taskiq_adapter: TaskiqTaskQueueAdapter):
        """Test scheduling a task for future execution."""
        from datetime import datetime, timedelta
        
        # Schedule task for 1 minute from now
        future_time = datetime.now() + timedelta(minutes=1)
        
        async def scheduled_task(message: str) -> str:
            return f"Scheduled: {message}"
        
        # Schedule the task
        task_id = await taskiq_adapter.schedule(
            scheduled_task,
            future_time,
            "Future message"
        )
        
        # Verify task was scheduled
        assert task_id is not None
        assert isinstance(task_id, str)
    
    @pytest.mark.asyncio
    async def test_cancel_task_not_supported(self, taskiq_adapter: TaskiqTaskQueueAdapter):
        """Test that task cancellation returns False (not supported)."""
        result = await taskiq_adapter.cancel_task("test-task-id")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_task_status_no_backend(self, taskiq_adapter: TaskiqTaskQueueAdapter):
        """Test getting task status when no result backend is configured."""
        status = await taskiq_adapter.get_task_status("test-task-id")
        # Should return None when no result backend is available
        assert status is None


class TestNotificationTasks:
    """Test notification task handlers."""
    
    @pytest.mark.asyncio
    async def test_send_author_created_notification(self):
        """Test author created notification task."""
        # This test verifies the task can be called without errors
        # In a real scenario, you'd mock external services
        await send_author_created_notification("test-id", "Test Author")
    
    @pytest.mark.asyncio
    async def test_send_book_created_notification(self):
        """Test book created notification task."""
        # This test verifies the task can be called without errors
        # In a real scenario, you'd mock external services
        await send_book_created_notification("test-id", "Test Book")
    
    @pytest.mark.asyncio
    async def test_cleanup_orphaned_records(self):
        """Test cleanup orphaned records task."""
        # This test verifies the task can be called without errors
        # In a real scenario, you'd mock database operations
        await cleanup_orphaned_records()


@pytest.mark.integration
class TestTaskiqRealBroker:
    """Integration tests with real Taskiq broker (requires Redis)."""
    
    @pytest.mark.skip(reason="Requires Redis server running")
    @pytest.mark.asyncio
    async def test_real_broker_integration(self):
        """Test with real Redis broker (skipped by default)."""
        from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend
        
        # Create real broker (requires Redis)
        broker = ListQueueBroker(url="redis://localhost:6379/15")  # Use test DB
        result_backend = RedisAsyncResultBackend(redis_url="redis://localhost:6379/15")
        broker = broker.with_result_backend(result_backend)
        
        adapter = TaskiqTaskQueueAdapter(broker_instance=broker)
        
        # Test task
        async def test_task(message: str) -> str:
            return f"Real broker: {message}"
        
        # Enqueue task
        task_id = await adapter.enqueue(test_task, "Hello Redis!")
        
        assert task_id is not None
        assert isinstance(task_id, str)

