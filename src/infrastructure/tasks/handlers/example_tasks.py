"""Example task handlers for the task queue system."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import os
from pathlib import Path

from src.infrastructure.tasks.taskiq_adapter import broker
from src.infrastructure.dependencies import get_logger


@broker.task
async def send_email_task(recipient: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Send an email asynchronously.
    
    Args:
        recipient: Email recipient address
        subject: Email subject line
        body: Email body content
        
    Returns:
        Dict containing task result information
    """
    logger = await get_logger()
    
    try:
        # Simulate email sending delay
        await asyncio.sleep(2)
        
        # Log the email sending (in real implementation, use actual email service)
        await logger.info(f"Email sent to {recipient}: {subject}")
        
        # Simulate email service response
        result = {
            "status": "success",
            "recipient": recipient,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().timestamp()}"
        }
        
        return result
        
    except Exception as e:
        await logger.error(f"Failed to send email to {recipient}: {str(e)}")
        return {
            "status": "error",
            "recipient": recipient,
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }


@broker.task
async def process_data_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process data asynchronously.
    
    Args:
        data: Dictionary containing data to process
        
    Returns:
        Dict containing processed data and metadata
    """
    logger = await get_logger()
    
    try:
        # Simulate data processing time
        processing_time = data.get('processing_time', 5)
        await asyncio.sleep(processing_time)
        
        # Process the data (example transformation)
        processed_data = {
            "id": data.get("id", "unknown"),
            "original_data": data,
            "processed_at": datetime.now().isoformat(),
            "processing_duration": processing_time,
            "status": "completed",
            "transformations_applied": [
                "validation",
                "normalization", 
                "enrichment"
            ]
        }
        
        # Add some example processing logic
        if "items" in data:
            processed_data["item_count"] = len(data["items"])
            processed_data["total_value"] = sum(
                item.get("value", 0) for item in data["items"]
            )
        
        await logger.info(f"Data processed successfully: {data.get('id', 'unknown')}")
        
        return processed_data
        
    except Exception as e:
        await logger.error(f"Failed to process data: {str(e)}")
        raise


@broker.task
async def cleanup_old_logs_task(days_old: int = 7) -> Dict[str, Any]:
    """
    Clean up old log files.
    
    Args:
        days_old: Number of days old for files to be considered for cleanup
        
    Returns:
        Dict containing cleanup results
    """
    logger = await get_logger()
    
    try:
        # Simulate cleanup process
        await asyncio.sleep(3)
        
        logs_dir = Path("logs")
        cleaned_files = []
        total_size_cleaned = 0
        
        if logs_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            for log_file in logs_dir.glob("*.log*"):
                if log_file.is_file():
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        file_size = log_file.stat().st_size
                        # In real implementation, you would actually delete the file
                        # log_file.unlink()
                        
                        cleaned_files.append({
                            "filename": str(log_file),
                            "size": file_size,
                            "modified_date": file_mtime.isoformat()
                        })
                        total_size_cleaned += file_size
        
        result = {
            "status": "success",
            "cleaned_files_count": len(cleaned_files),
            "cleaned_files": cleaned_files,
            "total_size_cleaned": total_size_cleaned,
            "days_old_threshold": days_old,
            "cleaned_at": datetime.now().isoformat()
        }
        
        await logger.info(f"Log cleanup completed: {len(cleaned_files)} files cleaned")
        
        return result
        
    except Exception as e:
        await logger.error(f"Failed to cleanup logs: {str(e)}")
        raise


@broker.task
async def generate_report_task(report_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a report asynchronously.
    
    Args:
        report_type: Type of report to generate
        parameters: Report parameters and filters
        
    Returns:
        Dict containing report generation results
    """
    logger = await get_logger()
    
    try:
        # Simulate report generation time based on type
        generation_times = {
            "daily": 10,
            "weekly": 30,
            "monthly": 60,
            "yearly": 120
        }
        
        generation_time = generation_times.get(report_type, 15)
        await asyncio.sleep(generation_time)
        
        # Generate mock report data
        report_data = {
            "report_id": f"report_{datetime.now().timestamp()}",
            "type": report_type,
            "parameters": parameters,
            "generated_at": datetime.now().isoformat(),
            "generation_duration": generation_time,
            "status": "completed"
        }
        
        # Add mock data based on report type
        if report_type == "daily":
            report_data["data"] = {
                "total_users": 1250,
                "active_users": 890,
                "new_registrations": 45,
                "revenue": 12500.75
            }
        elif report_type == "weekly":
            report_data["data"] = {
                "total_users": 8750,
                "active_users": 6230,
                "new_registrations": 315,
                "revenue": 87503.25
            }
        
        # Save report to file (in real implementation)
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = reports_dir / report_filename
        
        # In real implementation, save the actual report
        # with open(report_path, 'w') as f:
        #     json.dump(report_data, f, indent=2)
        
        report_data["file_path"] = str(report_path)
        
        await logger.info(f"Report generated successfully: {report_type}")
        
        return report_data
        
    except Exception as e:
        await logger.error(f"Failed to generate report: {str(e)}")
        raise


@broker.task
async def backup_database_task(backup_type: str = "incremental") -> Dict[str, Any]:
    """
    Perform database backup asynchronously.
    
    Args:
        backup_type: Type of backup (full, incremental, differential)
        
    Returns:
        Dict containing backup results
    """
    logger = await get_logger()
    
    try:
        # Simulate backup time based on type
        backup_times = {
            "incremental": 30,
            "differential": 60,
            "full": 180
        }
        
        backup_time = backup_times.get(backup_type, 60)
        await asyncio.sleep(backup_time)
        
        # Generate backup metadata
        backup_data = {
            "backup_id": f"backup_{datetime.now().timestamp()}",
            "type": backup_type,
            "started_at": (datetime.now() - timedelta(seconds=backup_time)).isoformat(),
            "completed_at": datetime.now().isoformat(),
            "duration": backup_time,
            "status": "completed"
        }
        
        # Add mock backup statistics
        if backup_type == "full":
            backup_data.update({
                "tables_backed_up": 25,
                "records_backed_up": 150000,
                "backup_size_mb": 2500,
                "compression_ratio": 0.65
            })
        elif backup_type == "incremental":
            backup_data.update({
                "tables_backed_up": 8,
                "records_backed_up": 5000,
                "backup_size_mb": 150,
                "compression_ratio": 0.70
            })
        
        # Simulate backup file creation
        backups_dir = Path("backups")
        backups_dir.mkdir(exist_ok=True)
        
        backup_filename = f"{backup_type}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql.gz"
        backup_path = backups_dir / backup_filename
        
        backup_data["file_path"] = str(backup_path)
        backup_data["file_name"] = backup_filename
        
        await logger.info(f"Database backup completed: {backup_type}")
        
        return backup_data
        
    except Exception as e:
        await logger.error(f"Failed to backup database: {str(e)}")
        raise


@broker.task
async def send_notification_batch_task(notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send a batch of notifications asynchronously.
    
    Args:
        notifications: List of notification dictionaries
        
    Returns:
        Dict containing batch processing results
    """
    logger = await get_logger()
    
    try:
        successful_notifications = []
        failed_notifications = []
        
        for notification in notifications:
            try:
                # Simulate notification sending
                await asyncio.sleep(0.5)  # Small delay per notification
                
                notification_result = {
                    "id": notification.get("id"),
                    "recipient": notification.get("recipient"),
                    "type": notification.get("type", "email"),
                    "sent_at": datetime.now().isoformat(),
                    "status": "sent"
                }
                
                successful_notifications.append(notification_result)
                
            except Exception as e:
                failed_notification = {
                    "id": notification.get("id"),
                    "recipient": notification.get("recipient"),
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                }
                failed_notifications.append(failed_notification)
        
        result = {
            "batch_id": f"batch_{datetime.now().timestamp()}",
            "total_notifications": len(notifications),
            "successful_count": len(successful_notifications),
            "failed_count": len(failed_notifications),
            "successful_notifications": successful_notifications,
            "failed_notifications": failed_notifications,
            "processed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        await logger.info(
            f"Notification batch processed: {len(successful_notifications)} sent, "
            f"{len(failed_notifications)} failed"
        )
        
        return result
        
    except Exception as e:
        await logger.error(f"Failed to process notification batch: {str(e)}")
        raise


@broker.task
async def health_check_task() -> Dict[str, Any]:
    """
    Perform system health check asynchronously.
    
    Returns:
        Dict containing health check results
    """
    logger = await get_logger()
    
    try:
        # Simulate health checks
        await asyncio.sleep(5)
        
        # Mock health check results
        health_data = {
            "check_id": f"health_{datetime.now().timestamp()}",
            "checked_at": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {
                "database": {
                    "status": "healthy",
                    "response_time_ms": 45,
                    "connection_pool": "80% utilized"
                },
                "redis": {
                    "status": "healthy", 
                    "response_time_ms": 12,
                    "memory_usage": "65% utilized"
                },
                "disk_space": {
                    "status": "healthy",
                    "usage_percentage": 72,
                    "available_gb": 150
                },
                "memory": {
                    "status": "healthy",
                    "usage_percentage": 68,
                    "available_gb": 8
                }
            }
        }
        
        await logger.info("System health check completed successfully")
        
        return health_data
        
    except Exception as e:
        await logger.error(f"Health check failed: {str(e)}")
        raise

