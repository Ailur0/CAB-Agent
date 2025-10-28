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

        # Fetch details for each work item
        cr_list = []
        for item in work_items[:10]:  # Limit to 10 for performance
            cr_details = get_change_request(f"CR{item['id']}")
            if cr_details.get("status") == "success":
                cr_list.append(cr_details)

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
