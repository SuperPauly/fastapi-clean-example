# Redis Setup and Task Queue Configuration

This guide explains how to set up Redis and configure the task queue system for the FastAPI Clean Architecture Template.

## 📋 Prerequisites

- Redis server installed and running
- Python environment with project dependencies installed

## 🚀 Redis Installation

### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install Redis
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify installation
redis-cli ping
# Should return: PONG
```

### macOS (using Homebrew)
```bash
# Install Redis
brew install redis

# Start Redis service
brew services start redis

# Verify installation
redis-cli ping
# Should return: PONG
```

### Windows (using WSL or Docker)
```bash
# Using Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Verify installation
docker exec redis redis-cli ping
# Should return: PONG
```

### Docker Compose (Recommended for Development)
```bash
# Start Redis with the project
docker-compose up redis -d

# Verify installation
docker-compose exec redis redis-cli ping
# Should return: PONG
```

## ⚙️ Redis Configuration

### Basic Configuration (`redis.conf`)
```conf
# Network
bind 127.0.0.1
port 6379

# General
daemonize yes
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log

# Persistence
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir /var/lib/redis

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Security (uncomment and set password)
# requirepass your_secure_password
```

### Production Configuration
```conf
# Additional production settings
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Append only file
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128
```

## 🔧 Project Configuration

### Environment Variables
```bash
# .env file
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_secure_password  # if authentication is enabled
TASKIQ_BROKER_URL=redis://localhost:6379/0
TASKIQ_RESULT_BACKEND_URL=redis://localhost:6379/1
```

### Settings Configuration (`settings.toml`)
```toml
[redis]
url = "redis://localhost:6379/0"
password = ""  # Set if authentication is enabled
max_connections = 20
retry_on_timeout = true
socket_timeout = 5
socket_connect_timeout = 5

[taskiq]
broker_url = "redis://localhost:6379/0"
result_backend_url = "redis://localhost:6379/1"
max_retries = 3
retry_delay = 60
task_timeout = 300
```

## 🎯 Task Queue Setup

### 1. Basic Task Definition

```python
# src/infrastructure/tasks/handlers/example_tasks.py
from taskiq import TaskiqScheduler
from datetime import datetime, timedelta
import asyncio

from src.infrastructure.tasks.taskiq_adapter import broker
from src.application.ports.logger import LoggerPort
from src.infrastructure.dependencies import get_logger

# Define a simple task
@broker.task
async def send_email_task(recipient: str, subject: str, body: str) -> dict:
    """Send an email asynchronously."""
    logger = get_logger()
    
    try:
        # Simulate email sending
        await asyncio.sleep(2)  # Simulate network delay
        
        await logger.info(f"Email sent to {recipient}: {subject}")
        
        return {
            "status": "success",
            "recipient": recipient,
            "subject": subject,
            "sent_at": datetime.now().isoformat()
        }
    except Exception as e:
        await logger.error(f"Failed to send email to {recipient}: {str(e)}")
        return {
            "status": "error",
            "recipient": recipient,
            "error": str(e)
        }

@broker.task
async def process_data_task(data: dict) -> dict:
    """Process data asynchronously."""
    logger = get_logger()
    
    try:
        # Simulate data processing
        await asyncio.sleep(5)  # Simulate processing time
        
        processed_data = {
            "original": data,
            "processed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        await logger.info(f"Data processed successfully: {data.get('id', 'unknown')}")
        
        return processed_data
    except Exception as e:
        await logger.error(f"Failed to process data: {str(e)}")
        raise

@broker.task
async def cleanup_old_logs_task() -> dict:
    """Clean up old log files."""
    logger = get_logger()
    
    try:
        # Simulate cleanup process
        await asyncio.sleep(3)
        
        await logger.info("Log cleanup completed")
        
        return {
            "status": "success",
            "cleaned_files": 15,
            "cleaned_at": datetime.now().isoformat()
        }
    except Exception as e:
        await logger.error(f"Failed to cleanup logs: {str(e)}")
        raise
```

### 2. Using Tasks in Your Application

```python
# src/application/services/notification_service.py
from typing import Optional
from datetime import datetime, timedelta

from src.application.ports.task_queue import TaskQueuePort
from src.infrastructure.tasks.handlers.example_tasks import (
    send_email_task, 
    process_data_task,
    cleanup_old_logs_task
)

class NotificationService:
    """Service for handling notifications and background tasks."""
    
    def __init__(self, task_queue: TaskQueuePort):
        self.task_queue = task_queue
    
    async def send_welcome_email(self, user_email: str, user_name: str) -> str:
        """Send a welcome email to a new user."""
        subject = f"Welcome to our platform, {user_name}!"
        body = f"""
        Hello {user_name},
        
        Welcome to our platform! We're excited to have you on board.
        
        Best regards,
        The Team
        """
        
        # Enqueue the email task
        task_id = await self.task_queue.enqueue(
            send_email_task,
            recipient=user_email,
            subject=subject,
            body=body
        )
        
        return task_id
    
    async def schedule_data_processing(self, data: dict, delay_minutes: int = 5) -> str:
        """Schedule data processing for later execution."""
        when = datetime.now() + timedelta(minutes=delay_minutes)
        
        task_id = await self.task_queue.schedule(
            process_data_task,
            when=when,
            data=data
        )
        
        return task_id
    
    async def schedule_daily_cleanup(self) -> str:
        """Schedule daily log cleanup."""
        # Schedule for next day at 2 AM
        tomorrow = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
        tomorrow += timedelta(days=1)
        
        task_id = await self.task_queue.schedule(
            cleanup_old_logs_task,
            when=tomorrow
        )
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        return await self.task_queue.get_task_status(task_id)
```

### 3. FastAPI Integration

```python
# src/infrastructure/web/controllers/task_controller.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from src.application.services.notification_service import NotificationService
from src.infrastructure.dependencies import get_notification_service

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

class EmailRequest(BaseModel):
    recipient: str
    name: str

class DataProcessingRequest(BaseModel):
    data: Dict[str, Any]
    delay_minutes: int = 5

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

@router.post("/send-email", response_model=TaskResponse)
async def send_email(
    request: EmailRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Send a welcome email asynchronously."""
    try:
        task_id = await service.send_welcome_email(
            user_email=request.recipient,
            user_name=request.name
        )
        
        return TaskResponse(
            task_id=task_id,
            status="queued",
            message="Email task has been queued for processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-data", response_model=TaskResponse)
async def process_data(
    request: DataProcessingRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Schedule data processing task."""
    try:
        task_id = await service.schedule_data_processing(
            data=request.data,
            delay_minutes=request.delay_minutes
        )
        
        return TaskResponse(
            task_id=task_id,
            status="scheduled",
            message=f"Data processing scheduled for {request.delay_minutes} minutes from now"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Get the status of a task."""
    try:
        status = await service.get_task_status(task_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"task_id": task_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule-cleanup", response_model=TaskResponse)
async def schedule_cleanup(
    service: NotificationService = Depends(get_notification_service)
):
    """Schedule daily cleanup task."""
    try:
        task_id = await service.schedule_daily_cleanup()
        
        return TaskResponse(
            task_id=task_id,
            status="scheduled",
            message="Daily cleanup has been scheduled"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 🏃‍♂️ Running the Task Queue

### 1. Start Redis Server
```bash
# Using system service
sudo systemctl start redis-server

# Using Docker
docker-compose up redis -d

# Verify Redis is running
redis-cli ping
```

### 2. Start the Task Worker
```bash
# Using Hatch (recommended)
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker

# With multiple workers
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker --workers 4

# With specific concurrency
hatch run taskiq worker src.infrastructure.tasks.taskiq_adapter:broker --max-async-tasks 10
```

### 3. Start the FastAPI Application
```bash
# Development mode
hatch run dev:uvicorn src.main:app --reload

# Production mode
hatch run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Using Docker Compose (All Services)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f taskiq-worker

# Scale workers
docker-compose up -d --scale taskiq-worker=4
```

## 📊 Monitoring and Management

### Redis CLI Commands
```bash
# Connect to Redis
redis-cli

# Monitor real-time commands
redis-cli monitor

# Get Redis info
redis-cli info

# List all keys
redis-cli keys "*"

# Get queue length
redis-cli llen taskiq:default

# Flush all data (be careful!)
redis-cli flushall
```

### Task Queue Monitoring
```python
# src/infrastructure/tasks/monitoring.py
import asyncio
from typing import Dict, List
from redis import Redis

class TaskQueueMonitor:
    """Monitor task queue statistics."""
    
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        return {
            "pending_tasks": self.redis.llen("taskiq:default"),
            "failed_tasks": self.redis.llen("taskiq:failed"),
            "completed_tasks": self.redis.get("taskiq:completed") or 0,
            "active_workers": len(self.redis.smembers("taskiq:workers"))
        }
    
    def get_failed_tasks(self) -> List[str]:
        """Get list of failed tasks."""
        return [
            task.decode() for task in 
            self.redis.lrange("taskiq:failed", 0, -1)
        ]
    
    def clear_failed_tasks(self) -> int:
        """Clear failed tasks queue."""
        return self.redis.delete("taskiq:failed")
```

## 🔧 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # Check Redis logs
   sudo tail -f /var/log/redis/redis-server.log
   ```

2. **Tasks Not Processing**
   ```bash
   # Check worker logs
   docker-compose logs taskiq-worker
   
   # Check queue length
   redis-cli llen taskiq:default
   ```

3. **Memory Issues**
   ```bash
   # Check Redis memory usage
   redis-cli info memory
   
   # Set memory limit
   redis-cli config set maxmemory 256mb
   ```

### Performance Tuning

1. **Redis Configuration**
   - Increase `maxmemory` for larger queues
   - Use `appendonly yes` for persistence
   - Tune `tcp-keepalive` for connection stability

2. **Worker Configuration**
   - Increase worker count for CPU-bound tasks
   - Increase `max-async-tasks` for I/O-bound tasks
   - Use task priorities for important tasks

3. **Connection Pooling**
   - Configure Redis connection pool size
   - Use connection timeouts
   - Implement retry logic

## 📚 Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [Taskiq Documentation](https://taskiq-python.github.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Redis Best Practices](https://redis.io/docs/manual/config/)

## 🤝 Contributing

When adding new tasks:

1. Define tasks in `src/infrastructure/tasks/handlers/`
2. Add service methods in `src/application/services/`
3. Create API endpoints in `src/infrastructure/web/controllers/`
4. Add tests in `tests/integration/tasks/`
5. Update documentation

