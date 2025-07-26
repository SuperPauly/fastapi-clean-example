"""Task queue port (interface)."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from datetime import datetime


class TaskQueuePort(ABC):
    """Port (interface) for task queue operations."""
    
    @abstractmethod
    async def enqueue(
        self, 
        task_func: Callable[..., Any], 
        *args: Any, 
        **kwargs: Any
    ) -> str:
        """Enqueue a task for immediate execution."""
        pass
    
    @abstractmethod
    async def schedule(
        self, 
        task_func: Callable[..., Any], 
        when: datetime,
        *args: Any, 
        **kwargs: Any
    ) -> str:
        """Schedule a task for future execution."""
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        pass

