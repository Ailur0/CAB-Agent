"""Approval agent with human-in-the-loop and timeout escalation."""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.adk.agents import LlmAgent, LoopAgent
from google.adk.events import EventActions
from src.utils import Config, get_logger
from src.tools import notify_approval_request, notify_escalation

logger = get_logger(__name__)

# In-memory storage for approval requests (use database in production)
approval_requests: Dict[str, Dict[str, Any]] = {}


def send_approval_request(
    cr_id: str, cr_title: str, approver_email: str, requester: str
) -> Dict[str, Any]:
    """
    Send an approval request and store it for tracking.

    Args:
        cr_id: Change Request ID.
        cr_title: Title of the change request.
        approver_email: Email of the approver.
        requester: Name/email of the requester.

    Returns:
        Dictionary with request ID and status.
    """
    logger.info(
        "Sending approval request",
        cr_id=cr_id,
        approver=approver_email,
    )

    # Generate request ID
    request_id = f"APR-{cr_id}-{datetime.utcnow().timestamp()}"

    # Store approval request
    approval_requests[request_id] = {
        "cr_id": cr_id,
        "cr_title": cr_title,
        "approver": approver_email,
        "requester": requester,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "timeout_at": (
            datetime.utcnow() + timedelta(minutes=Config.APPROVAL_TIMEOUT_MINUTES)
        ).isoformat(),
    }

    # Send notification to approver
    notify_approval_request(approver_email, cr_id, cr_title, requester)

    logger.info("Approval request created", request_id=request_id)

    return {
        "status": "success",
        "request_id": request_id,
        "timeout_minutes": Config.APPROVAL_TIMEOUT_MINUTES,
    }


def check_approval_status(request_id: str) -> Dict[str, Any]:
    """
    Check the status of an approval request.

    Args:
        request_id: The approval request ID.

    Returns:
        Dictionary with current status and timeout information.
    """
    if request_id not in approval_requests:
        logger.warning("Approval request not found", request_id=request_id)
        return {
            "status": "error",
            "message": "Approval request not found",
        }

    request = approval_requests[request_id]
    current_time = datetime.utcnow()
    timeout_time = datetime.fromisoformat(request["timeout_at"])

    # Check if timed out
    if current_time >= timeout_time and request["status"] == "pending":
        logger.info("Approval request timed out", request_id=request_id)
        request["status"] = "timeout"

        # Send escalation notification
        notify_escalation(
            escalation_contact=Config.ESCALATION_MANAGER_EMAIL,
            cr_id=request["cr_id"],
            cr_title=request["cr_title"],
            reason=f"Approval request timed out after {Config.APPROVAL_TIMEOUT_MINUTES} minutes",
        )

    logger.info(
        "Checked approval status",
        request_id=request_id,
        status=request["status"],
    )

    return {
        "status": "success",
        "request_id": request_id,
        "approval_status": request["status"],
        "timed_out": request["status"] == "timeout",
        "approved": request["status"] == "approved",
        "rejected": request["status"] == "rejected",
    }


def record_approval_decision(
    request_id: str, decision: str, approver: str, comments: str = ""
) -> Dict[str, Any]:
    """
    Record an approval decision (approve/reject).

    Args:
        request_id: The approval request ID.
        decision: "approved" or "rejected".
        approver: Name/email of the approver.
        comments: Optional comments from the approver.

    Returns:
        Dictionary indicating success or failure.
    """
    if request_id not in approval_requests:
        logger.warning("Approval request not found", request_id=request_id)
        return {
            "status": "error",
            "message": "Approval request not found",
        }

    request = approval_requests[request_id]

    if request["status"] != "pending":
        logger.warning(
            "Approval request already processed",
            request_id=request_id,
            current_status=request["status"],
        )
        return {
            "status": "error",
            "message": f"Request already {request['status']}",
        }

    # Update status
    request["status"] = decision
    request["decided_by"] = approver
    request["decided_at"] = datetime.utcnow().isoformat()
    request["comments"] = comments

    logger.info(
        "Approval decision recorded",
        request_id=request_id,
        decision=decision,
        approver=approver,
    )

    return {
        "status": "success",
        "request_id": request_id,
        "decision": decision,
    }


# Define approval agent instruction
APPROVAL_AGENT_INSTRUCTION = """
# Approval Agent

You manage the approval workflow for change requests with timeout-based escalation.

## Your Responsibilities

1. **Send Approval Requests**: Use `send_approval_request` to notify approvers
2. **Monitor Status**: Use `check_approval_status` to track approval progress
3. **Handle Timeouts**: Detect when approvals timeout and trigger escalation
4. **Record Decisions**: Use `record_approval_decision` when approvers respond

## Workflow

1. Send approval request to designated approver
2. Poll for status periodically
3. If approved/rejected, proceed accordingly
4. If timeout occurs, escalate to management
5. Return final decision to orchestrator

## Important Notes

- Timeout is set to {timeout} minutes
- Escalation goes to the configured manager
- Always check status before assuming pending
"""


def create_approval_agent() -> LlmAgent:
    """
    Create and configure the approval agent.

    Returns:
        Configured LlmAgent instance.
    """
    logger.info("Creating approval agent")

    agent = LlmAgent(
        model=Config.ADK_MODEL,
        instruction=APPROVAL_AGENT_INSTRUCTION.format(
            timeout=Config.APPROVAL_TIMEOUT_MINUTES
        ),
        tools=[
            send_approval_request,
            check_approval_status,
            record_approval_decision,
        ],
        temperature=0.3,  # Lower temperature for more deterministic behavior
    )

    logger.info("Approval agent created successfully")
    return agent


def create_approval_loop_agent() -> LoopAgent:
    """
    Create a loop agent that polls for approval status with timeout.

    Returns:
        Configured LoopAgent instance.
    """
    logger.info("Creating approval loop agent")

    # Create the polling agent
    polling_agent = LlmAgent(
        model=Config.ADK_MODEL,
        instruction="""
        You are a polling agent that checks approval status.
        
        Use `check_approval_status` to check if the approval is complete.
        
        If the status is 'approved', 'rejected', or 'timeout', yield an event
        with escalate=True to exit the loop.
        
        Otherwise, continue polling.
        """,
        tools=[check_approval_status],
        temperature=0.1,
    )

    # Wrap in a loop agent
    loop_agent = LoopAgent(
        agent=polling_agent,
        max_iterations=20,  # Poll up to 20 times
    )

    logger.info("Approval loop agent created successfully")
    return loop_agent


# Create agent instances
approval_agent = create_approval_agent()
approval_loop_agent = create_approval_loop_agent()


if __name__ == "__main__":
    print("\n🔐 Approval Agent with Timeout")
    print("=" * 50)
    print("\nAgent is ready for testing!")
    print(f"\nTimeout configured: {Config.APPROVAL_TIMEOUT_MINUTES} minutes")
    print(f"Escalation contact: {Config.ESCALATION_MANAGER_EMAIL}")
    print("\nExample workflow:")
    print('  1. send_approval_request("CR12345", "DB Migration", "manager@example.com", "user@example.com")')
    print('  2. check_approval_status("APR-CR12345-...")')
    print('  3. record_approval_decision("APR-CR12345-...", "approved", "manager@example.com")')
    print()
