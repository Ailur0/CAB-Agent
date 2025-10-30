"""Background polling service to sync Azure DevOps CRs to database."""

import sys
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_session, ChangeRequest, CRStateHistory
from src.tools import query_change_requests, get_change_request
from src.utils import get_logger
from src.services.event_processor import process_cr_changes

logger = get_logger(__name__)


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return date_str
    except:
        return None


async def sync_crs():
    """Sync CRs from Azure DevOps to database and detect changes."""
    logger.info("Starting CR sync")
    
    session = get_session()
    
    try:
        # Query all CRs from Azure DevOps
        crs = query_change_requests()
        
        if not crs:
            logger.warning("No CRs found in Azure DevOps")
            return
        
        logger.info(f"Found {len(crs)} CRs to sync")
        
        synced_count = 0
        updated_count = 0
        new_count = 0
        
        for cr in crs:
            cr_id = cr.get("cr_id")
            
            try:
                # Get full CR details
                cr_details = get_change_request(cr_id)
                
                if cr_details.get("status") != "success":
                    continue
                
                # Get existing CR from database
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
                        logger.info(f"CR {cr_id} changed", changes=changes)
                        
                        # Update CR
                        existing_cr.state = new_state
                        existing_cr.assigned_to = new_assigned_to
                        existing_cr.approval_status = cr_details.get("approval_status")
                        existing_cr.scheduled_start_date = parse_date(cr_details.get("scheduled_start_date"))
                        existing_cr.scheduled_end_date = parse_date(cr_details.get("scheduled_end_date"))
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
                        
                        # Process notifications
                        await process_cr_changes(cr_id, changes, cr_details)
                        
                        updated_count += 1
                    
                    existing_cr.last_synced_at = datetime.utcnow()
                    
                else:
                    # New CR - insert
                    new_cr = ChangeRequest(
                        cr_id=cr_id,
                        title=cr_details.get("title", "")[:500],
                        description=cr_details.get("description", ""),
                        state=new_state,
                        work_item_type=cr.get("work_item_type", "Normal Change Request"),
                        created_by=created_by,
                        created_by_email=created_by_email,
                        assigned_to=new_assigned_to,
                        scheduled_start_date=parse_date(cr_details.get("scheduled_start_date")),
                        scheduled_end_date=parse_date(cr_details.get("scheduled_end_date")),
                        approval_status=cr_details.get("approval_status"),
                        created_at=parse_date(cr_details.get("created_date")),
                        last_synced_at=datetime.utcnow(),
                    )
                    session.add(new_cr)
                    new_count += 1
                    logger.info(f"New CR {cr_id} added to database")
                
                session.commit()
                synced_count += 1
                
            except Exception as e:
                logger.error(f"Failed to sync CR {cr_id}", error=str(e))
                session.rollback()
        
        logger.info(
            "Sync complete",
            synced=synced_count,
            new=new_count,
            updated=updated_count,
        )
        
    except Exception as e:
        logger.error("Sync failed", error=str(e))
    finally:
        session.close()


def start_polling_service(interval_minutes=5):
    """
    Start background polling service.
    
    Args:
        interval_minutes: Polling interval in minutes (default: 5)
    """
    logger.info(f"Starting polling service (interval: {interval_minutes} minutes)")
    
    scheduler = AsyncIOScheduler()
    
    # Add sync job
    scheduler.add_job(
        sync_crs,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="sync_azure_devops",
        name="Sync Azure DevOps CRs",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Polling service started")
    
    return scheduler
