"""Distributed task queue using Celery for scalable CR processing."""

import sys
import os
from typing import Dict, Any, List
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from celery import Celery, group
    from celery.schedules import crontab
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("WARNING: Celery not installed. Install with: pip install celery redis")

from src.utils import get_logger, Config

logger = get_logger(__name__)

# Initialize Celery app
# Redis is recommended as the broker for production
# For development, you can use: redis://localhost:6379/0
# For production, use a managed Redis service
celery_app = None

if CELERY_AVAILABLE:
    celery_app = Celery(
        'cab_agent',
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    )
    
    # Celery configuration
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minutes max per task
        worker_prefetch_multiplier=4,  # Prefetch 4 tasks per worker
        worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    )


# Task definitions
if CELERY_AVAILABLE:
    
    @celery_app.task(name='sync_single_cr', bind=True, max_retries=3)
    def sync_single_cr(self, cr_id: str) -> Dict[str, Any]:
        """
        Sync a single CR from Azure DevOps to database.
        
        Args:
            cr_id: The CR ID to sync
            
        Returns:
            Sync result
        """
        try:
            from src.tools import get_change_request
            from src.database import get_session, ChangeRequest, CRStateHistory
            from src.services.event_processor import process_cr_changes
            import asyncio
            
            logger.info(f"Syncing CR {cr_id}")
            
            # Fetch CR details
            cr_details = get_change_request(cr_id)
            
            if cr_details.get("status") != "success":
                return {"status": "error", "message": "Failed to fetch CR"}
            
            # Update database
            session = get_session()
            
            try:
                existing_cr = session.query(ChangeRequest).filter_by(cr_id=cr_id).first()
                
                # Extract created_by email
                created_by = cr_details.get("created_by")
                created_by_email = None
                if isinstance(created_by, dict):
                    created_by_email = created_by.get("uniqueName")
                    created_by = created_by.get("displayName")
                
                new_state = cr_details.get("state")
                new_assigned_to = cr_details.get("assigned_to")
                
                changes = []
                
                if existing_cr:
                    # Check for changes
                    if existing_cr.state != new_state:
                        changes.append({
                            "field": "state",
                            "old_value": existing_cr.state,
                            "new_value": new_state,
                        })
                    
                    if existing_cr.assigned_to != new_assigned_to:
                        changes.append({
                            "field": "assigned_to",
                            "old_value": existing_cr.assigned_to,
                            "new_value": new_assigned_to,
                        })
                    
                    if changes:
                        # Update CR
                        existing_cr.state = new_state
                        existing_cr.assigned_to = new_assigned_to
                        existing_cr.last_synced_at = datetime.utcnow()
                        existing_cr.updated_at = datetime.utcnow()
                        
                        # Log changes
                        for change in changes:
                            history = CRStateHistory(
                                cr_id=cr_id,
                                field_name=change["field"],
                                old_value=change["old_value"],
                                new_value=change["new_value"],
                                changed_at=datetime.utcnow(),
                            )
                            session.add(history)
                        
                        session.commit()
                        
                        # Process notifications
                        asyncio.run(process_cr_changes(cr_id, changes, cr_details))
                        
                        return {"status": "updated", "cr_id": cr_id, "changes": len(changes)}
                    else:
                        existing_cr.last_synced_at = datetime.utcnow()
                        session.commit()
                        return {"status": "no_changes", "cr_id": cr_id}
                else:
                    # New CR
                    new_cr = ChangeRequest(
                        cr_id=cr_id,
                        title=cr_details.get("title", "")[:500],
                        state=new_state,
                        created_by=created_by,
                        created_by_email=created_by_email,
                        assigned_to=new_assigned_to,
                        last_synced_at=datetime.utcnow(),
                    )
                    session.add(new_cr)
                    session.commit()
                    
                    return {"status": "new", "cr_id": cr_id}
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to sync CR {cr_id}", error=str(e))
            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
    
    
    @celery_app.task(name='sync_cr_batch')
    def sync_cr_batch(cr_ids: List[str]) -> Dict[str, Any]:
        """
        Sync a batch of CRs in parallel using Celery group.
        
        Args:
            cr_ids: List of CR IDs to sync
            
        Returns:
            Batch sync results
        """
        logger.info(f"Syncing batch of {len(cr_ids)} CRs")
        
        # Create a group of tasks
        job = group(sync_single_cr.s(cr_id) for cr_id in cr_ids)
        result = job.apply_async()
        
        # Wait for all tasks to complete
        results = result.get(timeout=300)  # 5 minute timeout
        
        # Aggregate results
        stats = {
            "total": len(cr_ids),
            "updated": sum(1 for r in results if r.get("status") == "updated"),
            "new": sum(1 for r in results if r.get("status") == "new"),
            "no_changes": sum(1 for r in results if r.get("status") == "no_changes"),
            "errors": sum(1 for r in results if r.get("status") == "error"),
        }
        
        logger.info("Batch sync complete", **stats)
        return stats
    
    
    @celery_app.task(name='process_notification')
    def process_notification(cr_id: str, notification_type: str, recipient: str, **kwargs) -> Dict[str, Any]:
        """
        Process a notification asynchronously.
        
        Args:
            cr_id: CR ID
            notification_type: Type of notification (approval, status_change, reminder, etc.)
            recipient: Recipient email
            **kwargs: Additional notification parameters
            
        Returns:
            Notification result
        """
        try:
            from src.tools import (
                notify_approval_request,
                notify_approval_status,
                notify_reminder,
            )
            
            logger.info(f"Processing {notification_type} notification for CR {cr_id}")
            
            if notification_type == "approval_request":
                result = notify_approval_request(
                    recipient,
                    cr_id,
                    kwargs.get("cr_title", ""),
                    kwargs.get("requester", ""),
                )
            elif notification_type == "approval_status":
                result = notify_approval_status(
                    recipient,
                    cr_id,
                    kwargs.get("status", ""),
                    kwargs.get("comments", ""),
                )
            elif notification_type == "reminder":
                result = notify_reminder(
                    recipient,
                    cr_id,
                    kwargs.get("message", ""),
                )
            else:
                return {"status": "error", "message": f"Unknown notification type: {notification_type}"}
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"Failed to process notification", error=str(e))
            return {"status": "error", "message": str(e)}
    
    
    # Periodic tasks
    @celery_app.on_after_configure.connect
    def setup_periodic_tasks(sender, **kwargs):
        """Setup periodic tasks for CR sync."""
        
        # Incremental sync every 5 minutes
        sender.add_periodic_task(
            300.0,  # 5 minutes
            incremental_sync_task.s(),
            name='incremental-sync-every-5-min'
        )
        
        # Full sync once a week (Sunday at 2 AM)
        sender.add_periodic_task(
            crontab(hour=2, minute=0, day_of_week=0),
            full_sync_task.s(),
            name='full-sync-weekly'
        )
    
    
    @celery_app.task(name='incremental_sync_task')
    def incremental_sync_task():
        """Incremental sync task - runs every 5 minutes."""
        from src.services.scalable_polling_service import scalable_polling_service
        import asyncio
        
        logger.info("Running incremental sync task")
        asyncio.run(scalable_polling_service.incremental_sync())
        return {"status": "completed"}
    
    
    @celery_app.task(name='full_sync_task')
    def full_sync_task():
        """Full sync task - runs weekly."""
        from src.services.scalable_polling_service import scalable_polling_service
        import asyncio
        
        logger.info("Running full sync task")
        asyncio.run(scalable_polling_service.full_sync())
        return {"status": "completed"}


# Helper functions for task submission
def submit_cr_sync(cr_id: str) -> Any:
    """Submit a CR sync task to the queue."""
    if not CELERY_AVAILABLE or not celery_app:
        logger.warning("Celery not available, cannot submit task")
        return None
    
    return sync_single_cr.delay(cr_id)


def submit_batch_sync(cr_ids: List[str]) -> Any:
    """Submit a batch CR sync task to the queue."""
    if not CELERY_AVAILABLE or not celery_app:
        logger.warning("Celery not available, cannot submit task")
        return None
    
    return sync_cr_batch.delay(cr_ids)


def submit_notification(cr_id: str, notification_type: str, recipient: str, **kwargs) -> Any:
    """Submit a notification task to the queue."""
    if not CELERY_AVAILABLE or not celery_app:
        logger.warning("Celery not available, cannot submit task")
        return None
    
    return process_notification.delay(cr_id, notification_type, recipient, **kwargs)


if __name__ == "__main__":
    print("\n📋 Distributed Task Queue (Celery)")
    print("=" * 60)
    
    if not CELERY_AVAILABLE:
        print("\n❌ Celery is not installed!")
        print("\nTo install:")
        print("  pip install celery redis")
        print("\nTo start Redis (required):")
        print("  docker run -d -p 6379:6379 redis")
        print("\nOr use a managed Redis service (AWS ElastiCache, Azure Cache, etc.)")
    else:
        print("\n✓ Celery is available")
        print("\nTo start workers:")
        print("  celery -A src.services.task_queue worker --loglevel=info --concurrency=10")
        print("\nTo start beat scheduler (for periodic tasks):")
        print("  celery -A src.services.task_queue beat --loglevel=info")
        print("\nTo monitor tasks:")
        print("  celery -A src.services.task_queue flower")
        print("\nConfiguration:")
        print(f"  Broker: {os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')}")
        print(f"  Backend: {os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')}")
    
    print()
