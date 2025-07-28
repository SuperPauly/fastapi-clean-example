"""Task management API controller."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.application.services.notification_service import NotificationService
from src.infrastructure.dependencies import get_notification_service

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


# Request Models
class EmailRequest(BaseModel):
    """Request model for sending emails."""
    recipient: str = Field(..., description="Email recipient address")
    name: str = Field(..., description="Recipient's name")


class PasswordResetRequest(BaseModel):
    """Request model for password reset emails."""
    email: str = Field(..., description="User's email address")
    reset_token: str = Field(..., description="Password reset token")


class DataProcessingRequest(BaseModel):
    """Request model for data processing tasks."""
    data: Dict[str, Any] = Field(..., description="Data to be processed")
    delay_minutes: int = Field(default=5, ge=0, le=1440, description="Delay in minutes")


class ReportRequest(BaseModel):
    """Request model for report generation."""
    report_type: str = Field(..., description="Type of report (daily, weekly, monthly, yearly)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    delay_minutes: int = Field(default=0, ge=0, le=1440, description="Delay in minutes")


class BackupRequest(BaseModel):
    """Request model for database backup."""
    backup_type: str = Field(default="incremental", description="Backup type (full, incremental, differential)")
    scheduled_time: Optional[datetime] = Field(default=None, description="When to perform backup")


class NotificationBatchRequest(BaseModel):
    """Request model for batch notifications."""
    notifications: List[Dict[str, Any]] = Field(..., description="List of notifications to send")


class CleanupRequest(BaseModel):
    """Request model for cleanup tasks."""
    days_old: int = Field(default=7, ge=1, le=365, description="Days old threshold for cleanup")


class HealthCheckRequest(BaseModel):
    """Request model for health check scheduling."""
    interval_minutes: int = Field(default=60, ge=5, le=1440, description="Interval between checks")


# Response Models
class TaskResponse(BaseModel):
    """Response model for task operations."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Human-readable message")
    created_at: datetime = Field(default_factory=datetime.now, description="Task creation time")


class TaskStatusResponse(BaseModel):
    """Response model for task status queries."""
    task_id: str = Field(..., description="Task identifier")
    status: Optional[str] = Field(..., description="Current task status")
    checked_at: datetime = Field(default_factory=datetime.now, description="Status check time")


# Email Tasks
@router.post("/email/welcome", response_model=TaskResponse)
async def send_welcome_email(
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
            message=f"Welcome email queued for {request.recipient}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue welcome email: {str(e)}")


@router.post("/email/password-reset", response_model=TaskResponse)
async def send_password_reset_email(
    request: PasswordResetRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Send a password reset email asynchronously."""
    try:
        task_id = await service.send_password_reset_email(
            user_email=request.email,
            reset_token=request.reset_token
        )
        
        return TaskResponse(
            task_id=task_id,
            status="queued",
            message=f"Password reset email queued for {request.email}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue password reset email: {str(e)}")


# Data Processing Tasks
@router.post("/data/process", response_model=TaskResponse)
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
        
        delay_msg = f" in {request.delay_minutes} minutes" if request.delay_minutes > 0 else ""
        
        return TaskResponse(
            task_id=task_id,
            status="scheduled" if request.delay_minutes > 0 else "queued",
            message=f"Data processing scheduled{delay_msg}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule data processing: {str(e)}")


# Report Generation Tasks
@router.post("/reports/generate", response_model=TaskResponse)
async def generate_report(
    request: ReportRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Generate a report asynchronously."""
    try:
        # Validate report type
        valid_types = ["daily", "weekly", "monthly", "yearly"]
        if request.report_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}"
            )
        
        task_id = await service.generate_report(
            report_type=request.report_type,
            parameters=request.parameters,
            delay_minutes=request.delay_minutes
        )
        
        delay_msg = f" in {request.delay_minutes} minutes" if request.delay_minutes > 0 else ""
        
        return TaskResponse(
            task_id=task_id,
            status="scheduled" if request.delay_minutes > 0 else "queued",
            message=f"{request.report_type.title()} report generation scheduled{delay_msg}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule report generation: {str(e)}")


# Backup Tasks
@router.post("/backup/database", response_model=TaskResponse)
async def backup_database(
    request: BackupRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Schedule a database backup."""
    try:
        # Validate backup type
        valid_types = ["full", "incremental", "differential"]
        if request.backup_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid backup type. Must be one of: {', '.join(valid_types)}"
            )
        
        task_id = await service.schedule_database_backup(
            backup_type=request.backup_type,
            when=request.scheduled_time
        )
        
        time_msg = f" at {request.scheduled_time.isoformat()}" if request.scheduled_time else ""
        
        return TaskResponse(
            task_id=task_id,
            status="scheduled" if request.scheduled_time else "queued",
            message=f"{request.backup_type.title()} database backup scheduled{time_msg}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule database backup: {str(e)}")


# Notification Batch Tasks
@router.post("/notifications/batch", response_model=TaskResponse)
async def send_notification_batch(
    request: NotificationBatchRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Send a batch of notifications."""
    try:
        if not request.notifications:
            raise HTTPException(status_code=400, detail="Notification list cannot be empty")
        
        task_id = await service.send_notification_batch(
            notifications=request.notifications
        )
        
        return TaskResponse(
            task_id=task_id,
            status="queued",
            message=f"Batch of {len(request.notifications)} notifications queued for processing"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue notification batch: {str(e)}")


# Cleanup Tasks
@router.post("/cleanup/logs", response_model=TaskResponse)
async def schedule_log_cleanup(
    request: CleanupRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Schedule log cleanup task."""
    try:
        task_id = await service.schedule_daily_cleanup(
            days_old=request.days_old
        )
        
        return TaskResponse(
            task_id=task_id,
            status="scheduled",
            message=f"Log cleanup scheduled (files older than {request.days_old} days)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule log cleanup: {str(e)}")


# Health Check Tasks
@router.post("/health/schedule", response_model=TaskResponse)
async def schedule_health_check(
    request: HealthCheckRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Schedule periodic health checks."""
    try:
        task_id = await service.schedule_health_check(
            interval_minutes=request.interval_minutes
        )
        
        return TaskResponse(
            task_id=task_id,
            status="scheduled",
            message=f"Health check scheduled every {request.interval_minutes} minutes"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule health check: {str(e)}")


# Task Management
@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Get the status of a task."""
    try:
        status = await service.get_task_status(task_id)
        
        return TaskStatusResponse(
            task_id=task_id,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.delete("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """Cancel a scheduled task."""
    try:
        success = await service.cancel_task(task_id)
        
        if success:
            return {"message": f"Task {task_id} cancelled successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or cannot be cancelled")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


# Utility Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint for the task controller."""
    return {
        "status": "healthy",
        "service": "task-controller",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/info")
async def task_info():
    """Get information about available task types."""
    return {
        "available_tasks": {
            "email": {
                "welcome": "Send welcome emails to new users",
                "password_reset": "Send password reset emails"
            },
            "data": {
                "process": "Process data asynchronously with optional delay"
            },
            "reports": {
                "generate": "Generate reports (daily, weekly, monthly, yearly)"
            },
            "backup": {
                "database": "Perform database backups (full, incremental, differential)"
            },
            "notifications": {
                "batch": "Send batch notifications"
            },
            "cleanup": {
                "logs": "Clean up old log files"
            },
            "health": {
                "schedule": "Schedule periodic health checks"
            }
        },
        "task_statuses": [
            "queued",
            "scheduled", 
            "running",
            "completed",
            "failed",
            "cancelled"
        ]
    }

