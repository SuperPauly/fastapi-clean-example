"""Taskiq task queue adapter."""

from datetime import datetime
from typing import Any, Callable, Optional

from taskiq import TaskiqScheduler
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker

from src.application.ports.task_queue import TaskQueuePort
from src.infrastructure.config.settings import taskiq_config


# Initialize Taskiq broker and result backend
broker = ListQueueBroker(url=taskiq_config.broker_url)
result_backend = RedisAsyncResultBackend(redis_url=taskiq_config.result_backend_url)
broker = broker.with_result_backend(result_backend)

# Initialize scheduler for scheduled tasks
scheduler = TaskiqScheduler(broker=broker, sources=[])


class TaskiqTaskQueueAdapter(TaskQueuePort):
    """Taskiq implementation of the task queue port."""
    
    def __init__(self, broker_instance=None):
        """Initialize the task queue adapter."""
        self._broker = broker_instance or broker
    
    async def enqueue(
        self, 
        task_func: Callable[..., Any], 
        *args: Any, 
        **kwargs: Any
    ) -> str:
        """Enqueue a task for immediate execution."""
        # Create a task from the function if not already a task
        if not hasattr(task_func, 'kicker'):
            task_func = self._broker.task(task_func)
        
        # Kick the task (enqueue it)
        task_result = await task_func.kiq(*args, **kwargs)
        return str(task_result.task_id)
    
    async def schedule(
        self, 
        task_func: Callable[..., Any], 
        when: datetime,
        *args: Any, 
        **kwargs: Any
    ) -> str:
        """Schedule a task for future execution."""
        # Create a task from the function if not already a task
        if not hasattr(task_func, 'kicker'):
            task_func = self._broker.task(task_func)
        
        # Schedule the task using eta (estimated time of arrival)
        task_result = await task_func.kiq(*args, eta=when, **kwargs)
        return str(task_result.task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        try:
            # Taskiq doesn't provide direct task cancellation by ID in the basic setup
            # This would require custom implementation with result backend
            # For now, return False to indicate cancellation is not supported
            return False
        except Exception:
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        try:
            if self._broker.result_backend:
                result = await self._broker.result_backend.get_result(task_id)
                if result:
                    return "completed" if result.is_finished else "pending"
            return None
        except Exception:
            return None
