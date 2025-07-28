"""Notification service for handling background tasks and notifications."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from src.application.ports.task_queue import TaskQueuePort
from src.application.ports.logger import LoggerPort


class NotificationService:
    """Service for handling notifications and background tasks."""
    
    def __init__(self, task_queue: TaskQueuePort, logger: LoggerPort):
        """
        Initialize the notification service.
        
        Args:
            task_queue: Task queue port for background processing
            logger: Logger port for logging operations
        """
        self.task_queue = task_queue
        self.logger = logger
    
    async def send_welcome_email(self, user_email: str, user_name: str) -> str:
        """
        Send a welcome email to a new user.
        
        Args:
            user_email: User's email address
            user_name: User's display name
            
        Returns:
            Task ID for tracking the email sending task
        """
        from src.infrastructure.tasks.handlers.example_tasks import send_email_task
        
        subject = f"Welcome to our platform, {user_name}!"
        body = f"""
        Hello {user_name},
        
        Welcome to our platform! We're excited to have you on board.
        
        Here are some things you can do to get started:
        - Complete your profile
        - Explore our features
        - Join our community
        
        If you have any questions, don't hesitate to reach out to our support team.
        
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
        
        await self.logger.info(f"Welcome email queued for {user_email} with task ID: {task_id}")
        
        return task_id
    
    async def send_password_reset_email(self, user_email: str, reset_token: str) -> str:
        """
        Send a password reset email.
        
        Args:
            user_email: User's email address
            reset_token: Password reset token
            
        Returns:
            Task ID for tracking the email sending task
        """
        from src.infrastructure.tasks.handlers.example_tasks import send_email_task
        
        subject = "Password Reset Request"
        body = f"""
        Hello,
        
        You have requested to reset your password. Please click the link below to reset your password:
        
        https://yourapp.com/reset-password?token={reset_token}
        
        This link will expire in 24 hours.
        
        If you did not request this password reset, please ignore this email.
        
        Best regards,
        The Team
        """
        
        task_id = await self.task_queue.enqueue(
            send_email_task,
            recipient=user_email,
            subject=subject,
            body=body
        )
        
        await self.logger.info(f"Password reset email queued for {user_email} with task ID: {task_id}")
        
        return task_id
    
    async def schedule_data_processing(self, data: Dict[str, Any], delay_minutes: int = 5) -> str:
        """
        Schedule data processing for later execution.
        
        Args:
            data: Data to be processed
            delay_minutes: Delay in minutes before processing
            
        Returns:
            Task ID for tracking the processing task
        """
        from src.infrastructure.tasks.handlers.example_tasks import process_data_task
        
        when = datetime.now() + timedelta(minutes=delay_minutes)
        
        task_id = await self.task_queue.schedule(
            process_data_task,
            when=when,
            data=data
        )
        
        await self.logger.info(
            f"Data processing scheduled for {when.isoformat()} with task ID: {task_id}"
        )
        
        return task_id
    
    async def schedule_daily_cleanup(self, days_old: int = 7) -> str:
        """
        Schedule daily log cleanup.
        
        Args:
            days_old: Number of days old for files to be considered for cleanup
            
        Returns:
            Task ID for tracking the cleanup task
        """
        from src.infrastructure.tasks.handlers.example_tasks import cleanup_old_logs_task
        
        # Schedule for next day at 2 AM
        tomorrow = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
        tomorrow += timedelta(days=1)
        
        task_id = await self.task_queue.schedule(
            cleanup_old_logs_task,
            when=tomorrow,
            days_old=days_old
        )
        
        await self.logger.info(
            f"Daily cleanup scheduled for {tomorrow.isoformat()} with task ID: {task_id}"
        )
        
        return task_id
    
    async def generate_report(self, report_type: str, parameters: Dict[str, Any], delay_minutes: int = 0) -> str:
        """
        Generate a report asynchronously.
        
        Args:
            report_type: Type of report to generate (daily, weekly, monthly, yearly)
            parameters: Report parameters and filters
            delay_minutes: Delay in minutes before generating the report
            
        Returns:
            Task ID for tracking the report generation task
        """
        from src.infrastructure.tasks.handlers.example_tasks import generate_report_task
        
        if delay_minutes > 0:
            when = datetime.now() + timedelta(minutes=delay_minutes)
            task_id = await self.task_queue.schedule(
                generate_report_task,
                when=when,
                report_type=report_type,
                parameters=parameters
            )
        else:
            task_id = await self.task_queue.enqueue(
                generate_report_task,
                report_type=report_type,
                parameters=parameters
            )
        
        await self.logger.info(
            f"Report generation ({report_type}) queued with task ID: {task_id}"
        )
        
        return task_id
    
    async def schedule_database_backup(self, backup_type: str = "incremental", when: Optional[datetime] = None) -> str:
        """
        Schedule a database backup.
        
        Args:
            backup_type: Type of backup (full, incremental, differential)
            when: When to perform the backup (defaults to immediate)
            
        Returns:
            Task ID for tracking the backup task
        """
        from src.infrastructure.tasks.handlers.example_tasks import backup_database_task
        
        if when:
            task_id = await self.task_queue.schedule(
                backup_database_task,
                when=when,
                backup_type=backup_type
            )
        else:
            task_id = await self.task_queue.enqueue(
                backup_database_task,
                backup_type=backup_type
            )
        
        await self.logger.info(
            f"Database backup ({backup_type}) scheduled with task ID: {task_id}"
        )
        
        return task_id
    
    async def send_notification_batch(self, notifications: List[Dict[str, Any]]) -> str:
        """
        Send a batch of notifications.
        
        Args:
            notifications: List of notification dictionaries
            
        Returns:
            Task ID for tracking the batch processing task
        """
        from src.infrastructure.tasks.handlers.example_tasks import send_notification_batch_task
        
        task_id = await self.task_queue.enqueue(
            send_notification_batch_task,
            notifications=notifications
        )
        
        await self.logger.info(
            f"Notification batch ({len(notifications)} notifications) queued with task ID: {task_id}"
        )
        
        return task_id
    
    async def schedule_health_check(self, interval_minutes: int = 60) -> str:
        """
        Schedule periodic health checks.
        
        Args:
            interval_minutes: Interval between health checks in minutes
            
        Returns:
            Task ID for tracking the health check task
        """
        from src.infrastructure.tasks.handlers.example_tasks import health_check_task
        
        when = datetime.now() + timedelta(minutes=interval_minutes)
        
        task_id = await self.task_queue.schedule(
            health_check_task,
            when=when
        )
        
        await self.logger.info(
            f"Health check scheduled for {when.isoformat()} with task ID: {task_id}"
        )
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            Task status or None if task not found
        """
        status = await self.task_queue.get_task_status(task_id)
        
        if status:
            await self.logger.debug(f"Task {task_id} status: {status}")
        else:
            await self.logger.warning(f"Task {task_id} not found")
        
        return status
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled, False otherwise
        """
        success = await self.task_queue.cancel_task(task_id)
        
        if success:
            await self.logger.info(f"Task {task_id} cancelled successfully")
        else:
            await self.logger.warning(f"Failed to cancel task {task_id}")
        
        return success

