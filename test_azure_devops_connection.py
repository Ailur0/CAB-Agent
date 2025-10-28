"""Quick test script to verify Azure DevOps configuration."""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.tools.azure_devops_tool import (
    create_change_request,
    get_change_request,
    query_change_requests,
    validate_change_request,
    update_change_request,
)
from src.utils.config import get_config
from src.utils.auth import get_azure_devops_auth
from collections import defaultdict
from datetime import datetime, timedelta


def test_connection():
    """Test basic Azure DevOps connection."""
    print("=" * 60)
    print("Azure DevOps / TFS Connection Test")
    print("=" * 60)
    
    # Check configuration
    config = get_config()
    
    # Determine if using TFS or Azure DevOps Cloud
    if config.AZURE_DEVOPS_SERVER_URL:
        print(f"\n✓ Server Type: TFS/Azure DevOps Server")
        print(f"✓ Server URL: {config.AZURE_DEVOPS_SERVER_URL}")
        print(f"✓ Collection: {config.AZURE_DEVOPS_COLLECTION}")
        print(f"✓ Project: {config.AZURE_DEVOPS_PROJECT}")
        print(f"✓ Base URL: {config.get_devops_base_url()}")
    else:
        print(f"\n✓ Server Type: Azure DevOps Cloud")
        print(f"✓ Organization: {config.AZURE_DEVOPS_ORG}")
        print(f"✓ Project: {config.AZURE_DEVOPS_PROJECT}")
    
    print(f"✓ PAT configured: {'Yes' if config.AZURE_DEVOPS_PAT else 'No'}")
    
    if not config.AZURE_DEVOPS_PAT:
        print("\n❌ ERROR: Azure DevOps PAT not configured in .env")
        return False
    
    return True


def test_query_change_requests():
    """Test querying existing change requests."""
    print("\n" + "=" * 60)
    print("Testing: Query Change Requests")
    print("=" * 60)
    
    try:
        # Query all change requests
        results = query_change_requests()
        
        if results:
            print(f"\n✓ Found {len(results)} change request(s)")
            for cr in results[:3]:  # Show first 3
                print(f"\n  CR ID: {cr.get('cr_id')}")
                print(f"  Title: {cr.get('title')}")
                print(f"  State: {cr.get('state')}")
        else:
            print("\n✓ Query successful (no change requests found)")
            print("  This is normal if you haven't created any CRs yet")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_create_change_request():
    """Test creating a new change request."""
    print("\n" + "=" * 60)
    print("Testing: Create Change Request")
    print("=" * 60)
    
    # Let user choose work item type
    print("\nAvailable Change Request Types:")
    print("  1. Normal Change Request (default)")
    print("  2. Emergency Change Request")
    print("  3. Standard Change Request")
    print("  4. Informational Change Request")
    print("  5. Child Change Request")
    
    type_choice = input("\nSelect type (1-5, default: 1): ").strip()
    type_map = {
        "1": "Normal Change Request",
        "2": "Emergency Change Request",
        "3": "Standard Change Request",
        "4": "Informational Change Request",
        "5": "Child Change Request",
    }
    work_item_type = type_map.get(type_choice, "Normal Change Request")
    
    # Prepare test data
    scheduled_time = (datetime.now() + timedelta(days=7)).isoformat() + "Z"
    
    try:
        result = create_change_request(
            title=f"[TEST] Sample {work_item_type}",
            description="This is a test change request created to verify Azure DevOps integration.",
            scheduled_time=scheduled_time,
            duration_hours=2,
            requester_email="test@example.com",
            work_item_type=work_item_type,
        )
        
        if result.get("status") == "success":
            cr_id = result.get("cr_id")
            print(f"\n✓ Change Request created successfully!")
            print(f"  CR ID: {cr_id}")
            print(f"  Title: {result.get('title')}")
            print(f"  State: {result.get('state')}")
            print(f"  URL: {result.get('url')}")
            return cr_id
        else:
            print(f"\n❌ Failed to create CR: {result.get('message')}")
            return None
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return None


def test_get_change_request(cr_id):
    """Test retrieving a change request."""
    print("\n" + "=" * 60)
    print("Testing: Get Change Request")
    print("=" * 60)
    
    try:
        result = get_change_request(cr_id)
        
        if result.get("status") == "success":
            print(f"\n✓ Retrieved CR successfully!")
            print(f"  CR ID: {result.get('cr_id')}")
            print(f"  Title: {result.get('title')}")
            print(f"  State: {result.get('state')}")
            print(f"  Scheduled: {result.get('scheduled_time')}")
            print(f"  Duration: {result.get('duration_hours')} hours")
            return True
        else:
            print(f"\n❌ Failed to retrieve CR: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_validate_change_request(cr_id):
    """Test validating a change request."""
    print("\n" + "=" * 60)
    print("Testing: Validate Change Request")
    print("=" * 60)
    
    try:
        result = validate_change_request(cr_id)
        
        if result.get("status") == "success":
            is_valid = result.get("valid")
            issues = result.get("issues", [])
            
            if is_valid:
                print(f"\n✓ CR is valid!")
            else:
                print(f"\n⚠ CR has validation issues:")
                for issue in issues:
                    print(f"  - {issue}")
            
            return True
        else:
            print(f"\n❌ Validation failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_update_change_request(cr_id):
    """Test updating a change request."""
    print("\n" + "=" * 60)
    print("Testing: Update Change Request")
    print("=" * 60)
    
    try:
        result = update_change_request(
            cr_id=cr_id,
            field_updates={
                "comments": "Updated via test script",
                "state": "Proposed"
            }
        )
        
        if result.get("status") == "success":
            print(f"\n✓ CR updated successfully!")
            print(f"  Updated fields: {', '.join(result.get('updated_fields', []))}")
            return True
        else:
            print(f"\n❌ Failed to update CR: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def query_all_work_items_by_state(days_back=30, limit=100):
    """Query all work items and group them by state."""
    print("\n" + "=" * 70)
    print("QUERYING ALL WORK ITEMS - GROUPED BY STATE")
    print("=" * 70)
    
    auth = get_azure_devops_auth()
    config = get_config()
    
    print(f"\nProject: {config.AZURE_DEVOPS_PROJECT}")
    print(f"Looking back: {days_back} days")
    print(f"Limit: {limit if limit else 'No limit'}")
    print("-" * 70)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Build WIQL query for all work items
    wiql_query = f"""
    SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType],
           [System.AssignedTo], [System.ChangedDate]
    FROM WorkItems
    WHERE [System.TeamProject] = '{config.AZURE_DEVOPS_PROJECT}'
    AND [System.ChangedDate] >= '{start_date.strftime('%Y-%m-%d')}'
    ORDER BY [System.ChangedDate] DESC
    """
    
    try:
        # Execute WIQL query
        result = auth.call_api(
            endpoint="wit/wiql",
            method="POST",
            data={"query": wiql_query},
        )
        
        work_items = result.get("workItems", [])
        total_count = len(work_items)
        
        print(f"\n✓ Found {total_count} work items")
        
        if limit and len(work_items) > limit:
            work_items = work_items[:limit]
            print(f"  (Showing first {limit} items)")
        
        # Fetch details for each work item
        detailed_items = []
        print("\nFetching details...")
        
        for i, item in enumerate(work_items, 1):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(work_items)}")
            
            try:
                work_item_id = item["id"]
                details = auth.call_api(
                    endpoint=f"wit/workitems/{work_item_id}",
                    method="GET",
                )
                
                fields = details.get("fields", {})
                assigned_to = fields.get("System.AssignedTo", {})
                
                detailed_items.append({
                    "id": work_item_id,
                    "title": fields.get("System.Title", "N/A"),
                    "state": fields.get("System.State", "Unknown"),
                    "type": fields.get("System.WorkItemType", "Unknown"),
                    "assigned_to": assigned_to.get("displayName", "Unassigned") if isinstance(assigned_to, dict) else "Unassigned",
                    "unique_name": assigned_to.get("uniqueName", "N/A") if isinstance(assigned_to, dict) else "N/A",
                    "changed_date": fields.get("System.ChangedDate", "N/A"),
                    "url": details.get("_links", {}).get("html", {}).get("href", "N/A"),
                })
            except Exception as e:
                print(f"  ⚠ Skipped item {item['id']}: {str(e)[:50]}")
        
        print(f"\n✓ Retrieved {len(detailed_items)} work items\n")
        
        # Group by state
        grouped = defaultdict(list)
        for item in detailed_items:
            state = item.get("state", "Unknown")
            grouped[state].append(item)
        
        # Print summary by type
        print("\n" + "=" * 70)
        print("SUMMARY BY WORK ITEM TYPE")
        print("=" * 70)
        
        type_counts = defaultdict(int)
        for item in detailed_items:
            type_counts[item['type']] += 1
        
        for item_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {item_type}: {count}")
        
        # Print detailed results grouped by state
        print("\n" + "=" * 70)
        print("WORK ITEMS GROUPED BY STATE")
        print("=" * 70)
        
        sorted_states = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
        
        for state, items in sorted_states:
            print(f"\n{'='*70}")
            print(f"STATE: {state} ({len(items)} items)")
            print("=" * 70)
            
            for item in items:
                print(f"\n  [{item['id']}] {item['type']}")
                print(f"  Title: {item['title'][:70]}{'...' if len(item['title']) > 70 else ''}")
                print(f"  Assigned: {item['assigned_to']} ({item['unique_name']})")
                print(f"  Changed: {item['changed_date'][:10] if item['changed_date'] != 'N/A' else 'N/A'}")
                print(f"  URL: {item['url']}")
        
        # Summary
        print("\n" + "=" * 70)
        print("STATE SUMMARY")
        print("=" * 70)
        for state, items in sorted_states:
            print(f"  {state}: {len(items)} items")
        
        return detailed_items
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def test_get_existing_work_item(work_item_id: str):
    """Test retrieving an existing work item by ID."""
    print("\n" + "=" * 60)
    print(f"Testing: Get Work Item {work_item_id}")
    print("=" * 60)
    
    try:
        # Format as CR ID
        cr_id = f"CR{work_item_id}"
        result = get_change_request(cr_id)
        
        if result.get("status") == "success":
            print(f"\n✓ Successfully retrieved work item!")
            print(f"\n  ID: {result.get('cr_id')}")
            print(f"  Title: {result.get('title')}")
            print(f"  State: {result.get('state')}")
            print(f"  Description: {result.get('description', 'N/A')[:100]}..." if result.get('description') else "  Description: N/A")
            print(f"  Created By: {result.get('created_by')}")
            print(f"  Created Date: {result.get('created_date')}")
            
            if result.get('scheduled_time'):
                print(f"  Scheduled Time: {result.get('scheduled_time')}")
            if result.get('duration_hours'):
                print(f"  Duration: {result.get('duration_hours')} hours")
            
            return True
        else:
            print(f"\n⚠ Could not retrieve work item: {result.get('message')}")
            print("  Note: This might be because the work item type or custom fields don't match.")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n🚀 Starting Azure DevOps Integration Tests\n")
    
    # Test 1: Connection
    if not test_connection():
        print("\n❌ Connection test failed. Please check your .env configuration.")
        return
    
    # Test 2: Query existing CRs
    test_query_change_requests()
    
    # Test 2.5: Query ALL work items grouped by state
    print("\n" + "=" * 60)
    response = input("\nDo you want to query ALL work items grouped by state? (y/n): ")
    if response.lower() == 'y':
        days_input = input("  How many days back? (default: 30): ").strip()
        days_back = int(days_input) if days_input else 30
        
        limit_input = input("  Max items to retrieve? (default: 100, 0 for all): ").strip()
        limit = int(limit_input) if limit_input else 100
        limit = None if limit == 0 else limit
        
        query_all_work_items_by_state(days_back=days_back, limit=limit)
    
    # Test 2.6: Try to retrieve a specific work item if provided
    print("\n" + "=" * 60)
    response = input("\nDo you want to test retrieving a specific work item? (y/n): ")
    if response.lower() == 'y':
        work_item_id = input("Enter the work item ID (e.g., 2579597): ").strip()
        if work_item_id:
            test_get_existing_work_item(work_item_id)
    
    # Test 3: Create a new CR
    print("\n" + "=" * 60)
    response = input("\nDo you want to create a test Change Request? (y/n): ")
    if response.lower() == 'y':
        cr_id = test_create_change_request()
        
        if cr_id:
            # Test 4: Get the CR
            test_get_change_request(cr_id)
            
            # Test 5: Validate the CR
            test_validate_change_request(cr_id)
            
            # Test 6: Update the CR
            test_update_change_request(cr_id)
    
    print("\n" + "=" * 60)
    print("✅ Testing Complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. View your change requests in Azure DevOps")
    print("  2. Test the Teams bot integration")
    print("  3. Run the ADK agents with: adk web src/agents/orchestrator_agent.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
