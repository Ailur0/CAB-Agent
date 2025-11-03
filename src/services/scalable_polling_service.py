"""Scalable polling service with batch processing and worker pools for handling 90,000+ CRs."""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_session, ChangeRequest, CRStateHistory
from src.tools import query_change_requests, get_change_request
from src.utils import get_logger, Config
from src.services.event_processor import process_cr_changes

logger = get_logger(__name__)

# Configuration for scalability
BATCH_SIZE = 100  # Process 100 CRs at a time
MAX_WORKERS = 10  # Number of parallel workers
INCREMENTAL_SYNC_HOURS = 24  # Only sync CRs updated in last 24 hours for incremental sync
FULL_SYNC_INTERVAL_HOURS = 168  # Full sync once a week (168 hours)


class ScalablePollingService:
    """
    Scalable polling service that can handle 90,000+ CRs efficiently.
    
    Features:
    - Batch processing to avoid memory overload
    - Worker pool for parallel processing
    - Incremental sync (only changed CRs) vs full sync
    - Rate limiting to avoid API throttling
    - Health monitoring and metrics
    """
    
    def __init__(
        self,
        batch_size: int = BATCH_SIZE,
        max_workers: int = MAX_WORKERS,
        incremental_sync_hours: int = INCREMENTAL_SYNC_HOURS,
    ):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.incremental_sync_hours = incremental_sync_hours
        self.scheduler = None
        self.last_full_sync = None
        self.metrics = {
            "total_synced": 0,
            "total_updated": 0,
            "total_new": 0,
            "total_errors": 0,
            "last_sync_duration": 0,
            "last_sync_time": None,
        }
    
    def parse_date(self, date_str):
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date_str
        except:
            return None
    
    async def sync_cr_batch(self, cr_ids: List[str]) -> Dict[str, int]:
        """
        Sync a batch of CRs in parallel using worker pool.
        
        Args:
            cr_ids: List of CR IDs to sync
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {"synced": 0, "updated": 0, "new": 0, "errors": 0}
        
        # Use ThreadPoolExecutor for parallel API calls
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all CR fetch tasks
            future_to_cr = {
                executor.submit(get_change_request, cr_id): cr_id 
                for cr_id in cr_ids
            }
            
            # Process results as they complete
            for future in as_completed(future_to_cr):
                cr_id = future_to_cr[future]
                
                try:
                    cr_details = future.result()
                    
                    if cr_details.get("status") != "success":
                        stats["errors"] += 1
                        continue
                    
                    # Update database
                    await self._update_cr_in_db(cr_id, cr_details, stats)
                    stats["synced"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync CR {cr_id}", error=str(e))
                    stats["errors"] += 1
        
        return stats
    
    async def _update_cr_in_db(self, cr_id: str, cr_details: Dict[str, Any], stats: Dict[str, int]):
        """Update CR in database and detect changes."""
        session = get_session()
        
        try:
            existing_cr = session.query(ChangeRequest).filter_by(cr_id=cr_id).first()
            
            # Extract created_by email
            created_by = cr_details.get("created_by")
            created_by_email = None
            if isinstance(created_by, dict):
                created_by_email = created_by.get("uniqueName")
                created_by = created_by.get("displayName")
            elif cr_details.get("created_by_unique_name"):
                created_by_email = cr_details.get("created_by_unique_name")
            
            new_state = cr_details.get("state")
            new_assigned_to = cr_details.get("assigned_to")
            
            if existing_cr:
                # Check for changes
                changes = []
                
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
                    existing_cr.approval_status = cr_details.get("approval_status")
                    existing_cr.scheduled_start_date = self.parse_date(cr_details.get("scheduled_start_date"))
                    existing_cr.scheduled_end_date = self.parse_date(cr_details.get("scheduled_end_date"))
                    existing_cr.last_synced_at = datetime.utcnow()
                    existing_cr.updated_at = datetime.utcnow()
                    
                    # Log changes to history
                    for change in changes:
                        history = CRStateHistory(
                            cr_id=cr_id,
                            field_name=change["field"],
                            old_value=change["old_value"],
                            new_value=change["new_value"],
                            changed_at=datetime.utcnow(),
                        )
                        session.add(history)
                    
                    # Process notifications asynchronously
                    await process_cr_changes(cr_id, changes, cr_details)
                    
                    stats["updated"] += 1
                
                existing_cr.last_synced_at = datetime.utcnow()
            else:
                # New CR - insert
                new_cr = ChangeRequest(
                    cr_id=cr_id,
                    title=cr_details.get("title", "")[:500],
                    description=cr_details.get("description", ""),
                    state=new_state,
                    work_item_type=cr_details.get("work_item_type", "Normal Change Request"),
                    created_by=created_by,
                    created_by_email=created_by_email,
                    assigned_to=new_assigned_to,
                    scheduled_start_date=self.parse_date(cr_details.get("scheduled_start_date")),
                    scheduled_end_date=self.parse_date(cr_details.get("scheduled_end_date")),
                    approval_status=cr_details.get("approval_status"),
                    created_at=self.parse_date(cr_details.get("created_date")),
                    last_synced_at=datetime.utcnow(),
                )
                session.add(new_cr)
                stats["new"] += 1
            
            session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update CR {cr_id} in database", error=str(e))
            session.rollback()
            raise
        finally:
            session.close()
    
    async def incremental_sync(self):
        """
        Incremental sync - only sync CRs updated in the last N hours.
        This is much faster for regular polling.
        """
        logger.info("Starting incremental CR sync")
        start_time = datetime.utcnow()
        
        try:
            # Query only recently updated CRs from Azure DevOps
            # This requires a custom query with date filter
            cutoff_date = datetime.utcnow() - timedelta(hours=self.incremental_sync_hours)
            
            # Get CRs from database that need refresh
            session = get_session()
            stale_crs = (
                session.query(ChangeRequest)
                .filter(ChangeRequest.last_synced_at < cutoff_date)
                .limit(1000)  # Limit to prevent overload
                .all()
            )
            session.close()
            
            cr_ids = [cr.cr_id for cr in stale_crs]
            
            if not cr_ids:
                logger.info("No stale CRs to sync")
                return
            
            logger.info(f"Incremental sync: {len(cr_ids)} CRs to refresh")
            
            # Process in batches
            total_stats = {"synced": 0, "updated": 0, "new": 0, "errors": 0}
            
            for i in range(0, len(cr_ids), self.batch_size):
                batch = cr_ids[i:i + self.batch_size]
                logger.info(f"Processing batch {i // self.batch_size + 1} ({len(batch)} CRs)")
                
                batch_stats = await self.sync_cr_batch(batch)
                
                # Aggregate stats
                for key in total_stats:
                    total_stats[key] += batch_stats[key]
                
                # Small delay to avoid API rate limiting
                await asyncio.sleep(1)
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(total_stats, duration)
            
            logger.info(
                "Incremental sync complete",
                duration=f"{duration:.2f}s",
                **total_stats
            )
            
        except Exception as e:
            logger.error("Incremental sync failed", error=str(e))
            self.metrics["total_errors"] += 1
    
    async def full_sync(self):
        """
        Full sync - sync all CRs from Azure DevOps.
        This is slower but ensures complete data consistency.
        Run this less frequently (e.g., once a week).
        """
        logger.info("Starting FULL CR sync (all 90,000+ CRs)")
        start_time = datetime.utcnow()
        
        try:
            # Query all CRs from Azure DevOps
            crs = query_change_requests()
            
            if not crs:
                logger.warning("No CRs found in Azure DevOps")
                return
            
            logger.info(f"Full sync: {len(crs)} CRs found")
            
            # Extract CR IDs
            cr_ids = [cr.get("cr_id") for cr in crs if cr.get("cr_id")]
            
            # Process in batches
            total_stats = {"synced": 0, "updated": 0, "new": 0, "errors": 0}
            
            for i in range(0, len(cr_ids), self.batch_size):
                batch = cr_ids[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(cr_ids) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} CRs)")
                
                batch_stats = await self.sync_cr_batch(batch)
                
                # Aggregate stats
                for key in total_stats:
                    total_stats[key] += batch_stats[key]
                
                # Progress update every 10 batches
                if batch_num % 10 == 0:
                    logger.info(
                        f"Progress: {batch_num}/{total_batches} batches",
                        synced=total_stats["synced"],
                        updated=total_stats["updated"],
                    )
                
                # Small delay to avoid API rate limiting
                await asyncio.sleep(1)
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(total_stats, duration)
            self.last_full_sync = datetime.utcnow()
            
            logger.info(
                "Full sync complete",
                duration=f"{duration:.2f}s",
                **total_stats
            )
            
        except Exception as e:
            logger.error("Full sync failed", error=str(e))
            self.metrics["total_errors"] += 1
    
    def _update_metrics(self, stats: Dict[str, int], duration: float):
        """Update service metrics."""
        self.metrics["total_synced"] += stats["synced"]
        self.metrics["total_updated"] += stats["updated"]
        self.metrics["total_new"] += stats["new"]
        self.metrics["total_errors"] += stats["errors"]
        self.metrics["last_sync_duration"] = duration
        self.metrics["last_sync_time"] = datetime.utcnow().isoformat()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current service metrics."""
        return {
            **self.metrics,
            "last_full_sync": self.last_full_sync.isoformat() if self.last_full_sync else None,
            "batch_size": self.batch_size,
            "max_workers": self.max_workers,
        }
    
    def start(
        self,
        incremental_interval_minutes: int = 5,
        full_sync_interval_hours: int = FULL_SYNC_INTERVAL_HOURS,
    ):
        """
        Start the scalable polling service.
        
        Args:
            incremental_interval_minutes: How often to run incremental sync (default: 5 min)
            full_sync_interval_hours: How often to run full sync (default: 168 hours = 1 week)
        """
        logger.info(
            "Starting scalable polling service",
            incremental_interval=f"{incremental_interval_minutes} min",
            full_sync_interval=f"{full_sync_interval_hours} hours",
            batch_size=self.batch_size,
            max_workers=self.max_workers,
        )
        
        self.scheduler = AsyncIOScheduler()
        
        # Add incremental sync job (frequent)
        self.scheduler.add_job(
            self.incremental_sync,
            trigger=IntervalTrigger(minutes=incremental_interval_minutes),
            id="incremental_sync",
            name="Incremental CR Sync",
            replace_existing=True,
        )
        
        # Add full sync job (infrequent)
        self.scheduler.add_job(
            self.full_sync,
            trigger=IntervalTrigger(hours=full_sync_interval_hours),
            id="full_sync",
            name="Full CR Sync",
            replace_existing=True,
        )
        
        # Run initial full sync
        self.scheduler.add_job(
            self.full_sync,
            id="initial_full_sync",
            name="Initial Full Sync",
        )
        
        self.scheduler.start()
        logger.info("Scalable polling service started")
        
        return self.scheduler
    
    def stop(self):
        """Stop the polling service."""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scalable polling service stopped")


# Create service instance
scalable_polling_service = ScalablePollingService()


if __name__ == "__main__":
    print("\n⚡ Scalable Polling Service")
    print("=" * 60)
    print("\nOptimized for handling 90,000+ CRs:")
    print(f"  • Batch size: {BATCH_SIZE} CRs per batch")
    print(f"  • Worker pool: {MAX_WORKERS} parallel workers")
    print(f"  • Incremental sync: Every 5 minutes (last {INCREMENTAL_SYNC_HOURS}h)")
    print(f"  • Full sync: Every {FULL_SYNC_INTERVAL_HOURS} hours (1 week)")
    print("\nFeatures:")
    print("  ✓ Batch processing to avoid memory overload")
    print("  ✓ Parallel worker pool for faster processing")
    print("  ✓ Incremental sync for efficiency")
    print("  ✓ Rate limiting to avoid API throttling")
    print("  ✓ Health monitoring and metrics")
    print()
