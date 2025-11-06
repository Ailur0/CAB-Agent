"""Azure DevOps integration tools for change request management."""

import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils import azure_devops_auth, get_logger

logger = get_logger(__name__)

# RealPage TFS Work Item Types
CHANGE_REQUEST_TYPES = [
    "Normal Change Request",
    "Emergency Change Request",
    "Standard Change Request",
    "Informational Change Request",
    "Child Change Request",
]

ALL_CHANGE_TYPES = [
    "Change Implementer",
    "Child Change Request",
    "CMDB Request",
    "Continuous Delivery Deployment",
    "Continuous Delivery SRFC Authorization",
    "Emergency Change Request",
    "Informational Change Request",
    "Normal Change Request",
    "SRFC Authorization",
    "Standard Change Request",
]


def create_change_request(
    title: str,
    description: str,
    scheduled_time: str,
    duration_hours: int,
    requester_email: str,
) -> Dict[str, Any]:
    """
    Create a new Change Request work item in Azure DevOps.

    Args:
        title: Title of the change request.
        description: Detailed description of the change.
        scheduled_time: Scheduled time for the change (ISO format).
        duration_hours: Expected duration in hours.
        requester_email: Email of the person requesting the change.

    Returns:
        Dictionary containing the created CR details including CR ID.
    """
    logger.info(
        "Creating change request",
        title=title,
        scheduled_time=scheduled_time,
        duration_hours=duration_hours,
    )

    # Prepare work item fields
    work_item_data = [
        {"op": "add", "path": "/fields/System.Title", "value": title},
        {"op": "add", "path": "/fields/System.Description", "value": description},
        {
            "op": "add",
            "path": "/fields/Custom.ScheduledTime",
            "value": scheduled_time,
        },
        {
            "op": "add",
            "path": "/fields/Custom.DurationHours",
            "value": duration_hours,
        },
        {
            "op": "add",
            "path": "/fields/System.CreatedBy",
            "value": requester_email,
        },
        {"op": "add", "path": "/fields/System.State", "value": "Proposed"},
    ]

    try:
        # Call Azure DevOps API to create work item
        result = azure_devops_auth.call_api(
            endpoint="wit/workitems/$Change Request",
            method="POST",
            data=work_item_data,
        )

        cr_id = result.get("id")
        logger.info("Change request created successfully", cr_id=cr_id)

        return {
            "status": "success",
            "cr_id": f"CR{cr_id}",
            "title": title,
            "state": "Proposed",
            "url": result.get("_links", {}).get("html", {}).get("href"),
        }

    except Exception as e:
        logger.error("Failed to create change request", error=str(e))
        return {
            "status": "error",
            "message": f"Failed to create CR: {str(e)}",
        }


def update_change_request(
    cr_id: str, field_updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing Change Request in Azure DevOps.

    Args:
        cr_id: The Change Request ID (e.g., "CR12345").
        field_updates: Dictionary of fields to update (e.g., {"extension_time": "2 hours"}).

    Returns:
        Dictionary indicating the status of the update.
    """
    logger.info("Updating change request", cr_id=cr_id, updates=field_updates)

    # Extract numeric ID from CR ID
    work_item_id = cr_id.replace("CR", "")

    # Prepare update operations
    update_operations = []
    for field, value in field_updates.items():
        # Map friendly field names to Azure DevOps field paths
        field_mapping = {
            "extension_time": "/fields/Custom.ExtensionTime",
            "state": "/fields/System.State",
            "duration_hours": "/fields/Custom.DurationHours",
            "scheduled_time": "/fields/Custom.ScheduledTime",
            "comments": "/fields/System.History",
        }

        field_path = field_mapping.get(field, f"/fields/{field}")
        update_operations.append({"op": "add", "path": field_path, "value": value})

    try:
        result = azure_devops_auth.call_api(
            endpoint=f"wit/workitems/{work_item_id}",
            method="PATCH",
            data=update_operations,
        )

        logger.info("Change request updated successfully", cr_id=cr_id)

        return {
            "status": "success",
            "cr_id": cr_id,
            "updated_fields": list(field_updates.keys()),
        }

    except Exception as e:
        logger.error("Failed to update change request", cr_id=cr_id, error=str(e))
        return {
            "status": "error",
            "cr_id": cr_id,
            "message": f"Failed to update CR: {str(e)}",
        }


def get_change_request(cr_id: str) -> Dict[str, Any]:
    """
    Retrieve details of a Change Request from Azure DevOps.

    Args:
        cr_id: The Change Request ID (e.g., "CR12345").

    Returns:
        Dictionary containing CR details.
    """
    logger.info("Retrieving change request", cr_id=cr_id)

    work_item_id = cr_id.replace("CR", "")

    try:
        result = azure_devops_auth.call_api(
            endpoint=f"wit/workitems/{work_item_id}",
            method="GET",
        )

        fields = result.get("fields", {})

        # Get deployment details from custom fields
        deployment_details = {
            "is_automated_deployment": fields.get("Custom.IsthisanAzureDevOpsdeployment", fields.get("Custom.IsAutomatedDeployment", fields.get("Custom.AutomatedDeployment"))),
            "automation_technology": fields.get("Custom.AutomationTechnology"),
            "deployment_needs_deleted": fields.get("Custom.DeploymentNeedsDeleted", fields.get("Custom.NeedsDeleted")),
        }
        
        return {
            "status": "success",
            "cr_id": cr_id,
            "title": fields.get("System.Title"),
            "description": fields.get("System.Description"),
            "state": fields.get("System.State"),
            "scheduled_time": fields.get("Custom.ScheduledTime"),
            "duration_hours": fields.get("Custom.DurationHours"),
            "created_by": fields.get("System.CreatedBy"),
            "created_date": fields.get("System.CreatedDate"),
            "assigned_to": fields.get("System.AssignedTo", {}).get("displayName") if isinstance(fields.get("System.AssignedTo"), dict) else fields.get("System.AssignedTo"),
            "created_by_unique_name": fields.get("System.CreatedBy", {}).get("uniqueName") if isinstance(fields.get("System.CreatedBy"), dict) else None,
            "scheduled_start_date": fields.get("Custom.ScheduledStartDate", fields.get("Microsoft.VSTS.Scheduling.StartDate")),
            "scheduled_end_date": fields.get("Custom.ScheduledEndDate", fields.get("Microsoft.VSTS.Scheduling.FinishDate")),
            "approval_status": fields.get("Custom.ApprovalStatus", fields.get("Microsoft.VSTS.Common.ApprovalStatus")),
            "deployment_details": deployment_details,
        }

    except Exception as e:
        logger.error("Failed to retrieve change request", cr_id=cr_id, error=str(e))
        return {
            "status": "error",
            "cr_id": cr_id,
            "message": f"Failed to retrieve CR: {str(e)}",
        }


def query_change_requests(
    state: Optional[str] = None,
    assigned_to: Optional[str] = None,
    date_range: Optional[Dict[str, str]] = None,
    work_item_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Query Change Requests from Azure DevOps based on filters.

    Args:
        state: Filter by state (e.g., "Proposed", "Approved", "In Progress").
        assigned_to: Filter by assigned user email.
        date_range: Filter by date range with "start" and "end" keys.
        work_item_types: List of work item types to query. If None, queries all change-related types.

    Returns:
        List of Change Request dictionaries.
    """
    logger.info(
        "Querying change requests",
        state=state,
        assigned_to=assigned_to,
        date_range=date_range,
        work_item_types=work_item_types,
    )

    # Default change request types for RealPage TFS
    if work_item_types is None:
        work_item_types = [
            "Normal Change Request",
            "Emergency Change Request",
            "Standard Change Request",
            "Informational Change Request",
            "Child Change Request",
        ]

    # Build WIQL query
    query_parts = ["SELECT [System.Id], [System.Title], [System.State] FROM WorkItems"]
    
    # Build work item type filter
    if len(work_item_types) == 1:
        type_filter = f"[System.WorkItemType] = '{work_item_types[0]}'"
    else:
        type_conditions = [f"[System.WorkItemType] = '{wit}'" for wit in work_item_types]
        type_filter = "(" + " OR ".join(type_conditions) + ")"
    
    where_clauses = [type_filter]

    if state:
        where_clauses.append(f"[System.State] = '{state}'")

    if assigned_to:
        where_clauses.append(f"[System.AssignedTo] = '{assigned_to}'")

    if date_range:
        if "start" in date_range:
            where_clauses.append(
                f"[System.CreatedDate] >= '{date_range['start']}'"
            )
        if "end" in date_range:
            where_clauses.append(f"[System.CreatedDate] <= '{date_range['end']}'")

    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))

    wiql_query = " ".join(query_parts)

    try:
        result = azure_devops_auth.call_api(
            endpoint="wit/wiql",
            method="POST",
            data={"query": wiql_query},
        )

        work_items = result.get("workItems", [])
        logger.info("Query returned results", count=len(work_items))

        if not work_items:
            return []

        cr_list: List[Dict[str, Any]] = []
        # Reduce batch size to 50 for more reliable requests
        # Azure DevOps API supports up to 200, but smaller batches are more stable
        batch_size = 50

        for start in range(0, len(work_items), batch_size):
            batch = work_items[start:start + batch_size]
            
            # Validate and extract IDs
            batch_ids = []
            for item in batch:
                item_id = item.get("id")
                if item_id and isinstance(item_id, int):
                    batch_ids.append(item_id)
                else:
                    logger.warning("Invalid work item ID", item=item)
            
            if not batch_ids:
                logger.warning("No valid IDs in batch", batch_start=start)
                continue

            payload = {
                "ids": batch_ids,
                "fields": [
                    # Standard System fields (always available)
                    "System.Title",
                    "System.Description",
                    "System.State",
                    "System.WorkItemType",
                    "System.CreatedBy",
                    "System.AssignedTo",
                    "System.CreatedDate",
                    # Standard Microsoft VSTS fields (commonly available)
                    "Microsoft.VSTS.Scheduling.StartDate",
                    "Microsoft.VSTS.Scheduling.FinishDate",
                    "Microsoft.VSTS.Common.ClosedDate",
                    # Note: Custom fields removed as they don't exist in this TFS instance
                    # If you need custom fields, verify they exist first using the Fields API
                ],
            }

            try:
                logger.info(
                    "Fetching CR batch",
                    batch_start=start,
                    batch_size=len(batch_ids),
                    id_range=f"{batch_ids[0]}-{batch_ids[-1]}" if batch_ids else "empty",
                )
                
                batch_result = azure_devops_auth.call_api(
                    endpoint="wit/workitemsbatch",
                    method="POST",
                    data=payload,
                )
                
                logger.info(
                    "Successfully fetched CR batch",
                    batch_start=start,
                    results_count=len(batch_result.get("value", [])),
                )
            except Exception as batch_error:
                logger.error(
                    "Failed to fetch CR batch",
                    error=str(batch_error),
                    batch_start=start,
                    batch_size=len(batch_ids),
                    batch_ids=batch_ids[:5],  # Log first 5 IDs for debugging
                )
                # Continue processing other batches
                continue

            for work_item in batch_result.get("value", []):
                fields = work_item.get("fields", {})

                created_by = fields.get("System.CreatedBy")
                if isinstance(created_by, dict):
                    created_by_name = created_by.get("displayName")
                    created_by_email = created_by.get("uniqueName")
                else:
                    created_by_name = created_by
                    created_by_email = None

                assigned_to = fields.get("System.AssignedTo")
                if isinstance(assigned_to, dict):
                    assigned_to_name = assigned_to.get("displayName")
                else:
                    assigned_to_name = assigned_to

                cr_list.append(
                    {
                        "status": "success",
                        "cr_id": f"CR{work_item.get('id')}",
                        "title": fields.get("System.Title"),
                        "description": fields.get("System.Description"),
                        "state": fields.get("System.State"),
                        "work_item_type": fields.get("System.WorkItemType"),
                        "created_by": created_by_name,
                        "created_by_unique_name": created_by_email,
                        "scheduled_start_date": fields.get("Microsoft.VSTS.Scheduling.StartDate"),
                        "scheduled_end_date": fields.get("Microsoft.VSTS.Scheduling.FinishDate"),
                        "closed_date": fields.get("Microsoft.VSTS.Common.ClosedDate"),
                        "assigned_to": assigned_to_name,
                        "created_date": fields.get("System.CreatedDate"),
                    }
                )

        return cr_list

    except Exception as e:
        logger.error("Failed to query change requests", error=str(e))
        return []


def validate_change_request(cr_id: str) -> Dict[str, Any]:
    """
    Validate a Change Request for compliance and completeness.

    Args:
        cr_id: The Change Request ID to validate.

    Returns:
        Dictionary with validation results and any issues found.
    """
    logger.info("Validating change request", cr_id=cr_id)

    cr_details = get_change_request(cr_id)

    if cr_details.get("status") != "success":
        return {
            "status": "error",
            "cr_id": cr_id,
            "valid": False,
            "message": "CR not found",
        }

    issues = []

    # Check required fields
    if not cr_details.get("title"):
        issues.append("Missing title")

    if not cr_details.get("description"):
        issues.append("Missing description")

    if not cr_details.get("scheduled_time"):
        issues.append("Missing scheduled time")

    if not cr_details.get("duration_hours"):
        issues.append("Missing duration")

    # Check scheduled time is in the future
    if cr_details.get("scheduled_time"):
        try:
            scheduled = datetime.fromisoformat(
                cr_details["scheduled_time"].replace("Z", "+00:00")
            )
            if scheduled < datetime.now(scheduled.tzinfo):
                issues.append("Scheduled time is in the past")
        except Exception:
            issues.append("Invalid scheduled time format")

    is_valid = len(issues) == 0

    logger.info(
        "Validation complete",
        cr_id=cr_id,
        valid=is_valid,
        issues_count=len(issues),
    )

    return {
        "status": "success",
        "cr_id": cr_id,
        "valid": is_valid,
        "issues": issues,
    }


def get_cr_revision_history(
    cr_id: str,
    from_state: Optional[str] = None,
    to_state: Optional[str] = None,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get revision history for a Change Request, optionally filtered by state transitions.
    
    Args:
        cr_id: The Change Request ID (e.g., "CR12345" or "12345")
        from_state: Filter for transitions FROM this state (e.g., "Pending CAB")
        to_state: Filter for transitions TO this state (e.g., "Approved")
        date: Filter for changes on this date (YYYY-MM-DD format)
    
    Returns:
        Dictionary containing revision history and state transitions
    """
    logger.info(
        "Getting CR revision history",
        cr_id=cr_id,
        from_state=from_state,
        to_state=to_state,
        date=date
    )
    
    work_item_id = cr_id.replace("CR", "")
    
    try:
        # Get all revisions for the work item
        result = azure_devops_auth.call_api(
            endpoint=f"wit/workitems/{work_item_id}/revisions",
            method="GET"
        )
        
        revisions = result.get("value", [])
        
        # Track state changes
        state_changes = []
        previous_state = None
        
        for revision in revisions:
            fields = revision.get("fields", {})
            current_state = fields.get("System.State")
            changed_date = fields.get("System.ChangedDate", "")
            changed_by = fields.get("System.ChangedBy", {})
            
            # Parse date for filtering
            revision_date = None
            if changed_date:
                try:
                    from datetime import datetime
                    revision_date = datetime.fromisoformat(changed_date.replace("Z", "+00:00")).date()
                except:
                    pass
            
            # Check if state changed
            if previous_state and current_state != previous_state:
                change_info = {
                    "revision": revision.get("rev"),
                    "from_state": previous_state,
                    "to_state": current_state,
                    "changed_date": changed_date,
                    "changed_date_only": str(revision_date) if revision_date else None,
                    "changed_by": changed_by.get("displayName") if isinstance(changed_by, dict) else str(changed_by),
                    "changed_by_email": changed_by.get("uniqueName") if isinstance(changed_by, dict) else None,
                }
                
                # Apply filters
                include = True
                
                if from_state and previous_state != from_state:
                    include = False
                
                if to_state and current_state != to_state:
                    include = False
                
                if date and revision_date:
                    from datetime import datetime
                    filter_date = datetime.strptime(date, "%Y-%m-%d").date()
                    if revision_date != filter_date:
                        include = False
                
                if include:
                    state_changes.append(change_info)
            
            previous_state = current_state
        
        logger.info(
            "Retrieved CR revision history",
            cr_id=cr_id,
            total_revisions=len(revisions),
            state_changes=len(state_changes)
        )
        
        return {
            "status": "success",
            "cr_id": cr_id,
            "total_revisions": len(revisions),
            "state_changes": state_changes,
            "current_state": previous_state
        }
    
    except Exception as e:
        logger.error(f"Error getting CR revision history: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "cr_id": cr_id,
            "message": str(e)
        }


def query_crs_by_state_change(
    from_state: str,
    to_state: str,
    date: Optional[str] = None,
    work_item_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Query Change Requests that transitioned from one state to another.
    
    Args:
        from_state: The state CRs transitioned FROM (e.g., "Pending CAB")
        to_state: The state CRs transitioned TO (e.g., "Approved")
        date: Filter for changes on this date (YYYY-MM-DD format). Defaults to today.
        work_item_types: List of work item types to query
    
    Returns:
        Dictionary containing CRs that match the state transition criteria
    """
    from datetime import datetime, timedelta
    
    # Default to today if no date provided
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
        logger.info("No date provided, using today's date", date=date)
    else:
        logger.info("Using provided date", date=date)
    
    logger.info(
        "Querying CRs by state change",
        from_state=from_state,
        to_state=to_state,
        date=date
    )
    
    try:
        # First, query all CRs in the target state
        # We'll check their history to see if they transitioned on the specified date
        crs_in_target_state = query_change_requests(
            state=to_state,
            work_item_types=work_item_types
        )
        
        matching_crs = []
        
        for cr in crs_in_target_state:
            cr_id = cr.get("cr_id")  # Fixed: use "cr_id" instead of "id"
            
            if not cr_id:
                logger.warning("CR missing cr_id field", cr=cr)
                continue
            
            # Get revision history for this CR
            history = get_cr_revision_history(
                cr_id=cr_id,  # Already a string like "CR12345"
                from_state=from_state,
                to_state=to_state,
                date=date
            )
            
            # If there are matching state changes, include this CR
            if history.get("status") == "success" and history.get("state_changes"):
                cr["state_transition"] = history["state_changes"][0]  # Most recent matching transition
                matching_crs.append(cr)
        
        logger.info(
            "Found CRs with state change",
            count=len(matching_crs),
            from_state=from_state,
            to_state=to_state,
            date=date
        )
        
        return {
            "status": "success",
            "count": len(matching_crs),
            "from_state": from_state,
            "to_state": to_state,
            "date": date,
            "change_requests": matching_crs
        }
    
    except Exception as e:
        logger.error(f"Error querying CRs by state change: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
