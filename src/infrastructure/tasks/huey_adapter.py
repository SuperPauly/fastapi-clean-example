"""Huey task queue adapter."""

from datetime import datetime
from typing import Any, Callable, Optional
from huey import RedisHuey

from src.application.ports.task_queue import TaskQueuePort
from src.infrastructure.config.settings import redis_config


# Initialize Huey instance
huey = RedisHuey(
    name="fastapi-clean-tasks",
    url=redis_config.url,
    immediate=False,
)


class HueyTaskQueueAdapter(TaskQueuePort):
    """Huey implementation of the task queue port."""
    
    def __init__(self, huey_instance=None):
        """Initialize the task queue adapter."""
        self._huey = huey_instance or huey
    
    async def enqueue(
        self, 
        task_func: Callable[..., Any], 
        *args: Any, 
        **kwargs: Any
    ) -> str:
        """Enqueue a task for immediate execution."""
        # Wrap the function with Huey decorator if not already wrapped
        if not hasattr(task_func, 'task_class'):
            task_func = self._huey.task()(task_func)
        
        # Enqueue the task
        result = task_func(*args, **kwargs)
        return str(result.id) if hasattr(result, 'id') else str(result)
    
    async def schedule(
        self, 
        task_func: Callable[..., Any], 
        when: datetime,
        *args: Any, 
        **kwargs: Any
    ) -> str:
        """Schedule a task for future execution."""
        # Wrap the function with Huey decorator if not already wrapped
        if not hasattr(task_func, 'task_class'):
            task_func = self._huey.task()(task_func)
        
        # Schedule the task
        result = task_func.schedule(args=args, kwargs=kwargs, eta=when)
        return str(result.id) if hasattr(result, 'id') else str(result)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        try:
            # Huey doesn't provide direct task cancellation by ID
            # This would require custom implementation or task tracking
            return False
        except Exception:
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        try:
            # Huey doesn't provide direct task status by ID
            # This would require custom implementation or task tracking
            return None
        except Exception:
            return None

