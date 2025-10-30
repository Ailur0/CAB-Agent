"""Initial sync script to populate database with existing CRs from Azure DevOps."""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

from src.database import get_session, ChangeRequest
from src.tools import query_change_requests, get_change_request
from src.utils import get_logger

logger = get_logger(__name__)


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        # Handle ISO format with Z
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return date_str
    except:
        return None


def sync_all_crs(limit=None):
    """
    Fetch all CRs from Azure DevOps and populate database.
    
    Args:
        limit: Maximum number of CRs to sync (None for all)
    """
    print("\n" + "=" * 70)
    print("CAB AGENT - INITIAL DATABASE SYNC")
    print("=" * 70)
    
    print("\n📥 Fetching CRs from Azure DevOps...")
    
    session = get_session()
    
    try:
        # Query all CRs (no filters)
        crs = query_change_requests()
        
        if not crs:
            print("⚠️  No CRs found in Azure DevOps")
            return
        
        total = len(crs)
        print(f"✅ Found {total} CRs")
        
        if limit:
            crs = crs[:limit]
            print(f"   Limiting to first {limit} CRs")
        
        print(f"\n💾 Syncing {len(crs)} CRs to database...")
        
        synced = 0
        skipped = 0
        errors = 0
        
        for i, cr in enumerate(crs, 1):
            cr_id = cr.get("cr_id")
            
            try:
                # Check if CR already exists
                existing = session.query(ChangeRequest).filter_by(cr_id=cr_id).first()
                
                if existing:
                    print(f"   [{i}/{len(crs)}] {cr_id} - Already exists, skipping")
                    skipped += 1
                    continue
                
                # Get full CR details
                cr_details = get_change_request(cr_id)
                
                if cr_details.get("status") != "success":
                    print(f"   [{i}/{len(crs)}] {cr_id} - Failed to fetch details")
                    errors += 1
                    continue
                
                # Extract created_by email
                created_by = cr_details.get("created_by")
                created_by_email = None
                if isinstance(created_by, dict):
                    created_by_email = created_by.get("uniqueName")
                    created_by = created_by.get("displayName")
                elif cr_details.get("created_by_unique_name"):
                    created_by_email = cr_details.get("created_by_unique_name")
                
                # Create CR record
                cr_record = ChangeRequest(
                    cr_id=cr_id,
                    title=cr_details.get("title", "")[:500],  # Truncate to fit column
                    description=cr_details.get("description", ""),
                    state=cr_details.get("state"),
                    work_item_type=cr.get("work_item_type", "Normal Change Request"),
                    created_by=created_by,
                    created_by_email=created_by_email,
                    assigned_to=cr_details.get("assigned_to"),
                    scheduled_start_date=parse_date(cr_details.get("scheduled_start_date")),
                    scheduled_end_date=parse_date(cr_details.get("scheduled_end_date")),
                    approval_status=cr_details.get("approval_status"),
                    created_at=parse_date(cr_details.get("created_date")),
                    last_synced_at=datetime.utcnow(),
                )
                
                session.add(cr_record)
                session.commit()
                
                print(f"   [{i}/{len(crs)}] {cr_id} - ✅ Synced ({cr_record.state})")
                synced += 1
                
            except Exception as e:
                print(f"   [{i}/{len(crs)}] {cr_id} - ❌ Error: {str(e)}")
                errors += 1
                session.rollback()
        
        print("\n" + "=" * 70)
        print("SYNC COMPLETE")
        print("=" * 70)
        print(f"✅ Synced:  {synced}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"❌ Errors:  {errors}")
        print(f"📊 Total:   {synced + skipped + errors}")
        
        print("\n💡 View synced data in SSMS:")
        print("   SELECT TOP 10 cr_id, title, state FROM change_requests;")
        
    except Exception as e:
        logger.error("Sync failed", error=str(e))
        print(f"\n❌ Sync failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync CRs from Azure DevOps to database")
    parser.add_argument("--limit", type=int, help="Limit number of CRs to sync")
    parser.add_argument("--all", action="store_true", help="Sync all CRs (no limit)")
    
    args = parser.parse_args()
    
    if args.all:
        sync_all_crs()
    else:
        limit = args.limit or 100  # Default to 100 if not specified
        sync_all_crs(limit=limit)
