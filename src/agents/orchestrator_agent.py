"""Main orchestrator agent for change management workflows."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.adk.agents import LlmAgent
from src.utils import Config, get_logger
from src.tools import (
    create_change_request,
    update_change_request,
    get_change_request,
    validate_change_request,
    check_calendar_conflicts,
    notify_approval_request,
    notify_approval_status,
)

logger = get_logger(__name__)

# Define the orchestrator agent instruction
ORCHESTRATOR_INSTRUCTION = """
# Change Management Orchestrator Agent

You are an intelligent orchestrator for IT change management workflows. Your role is to:

## Primary Responsibilities
1. **Process user requests** for creating, updating, or querying change requests
2. **Validate** change requests for compliance and completeness
3. **Check for conflicts** with calendars and other scheduled changes
4. **Coordinate approvals** by routing requests to appropriate approvers
5. **Provide status updates** and notifications to stakeholders

## Workflow Guidelines

### Creating Change Requests
- Extract key information: title, description, scheduled time, duration
- Validate all required fields are present
- Check for calendar conflicts with the scheduled time
- Create the CR in Azure DevOps
- Return the CR ID and confirmation to the user

### Extending Change Requests
- Retrieve the existing CR details
- Validate the extension request
- Check for conflicts with the new extended time
- Update the CR with the extension
- Notify relevant stakeholders

### Approval Workflows
- Send approval requests to designated approvers
- Track approval status
- Handle timeouts by escalating to management
- Notify requesters of approval decisions

### Status Queries
- Retrieve CR details from Azure DevOps
- Format and present information clearly
- Provide actionable next steps

## Tool Usage
- Use `create_change_request` to create new CRs
- Use `update_change_request` to modify existing CRs
- Use `get_change_request` to retrieve CR details
- Use `validate_change_request` to check CR compliance
- Use `check_calendar_conflicts` to verify scheduling
- Use `notify_approval_request` to request approvals
- Use `notify_approval_status` to send approval outcomes

## Communication Style
- Be clear, concise, and professional
- Provide specific CR IDs and timestamps
- Highlight any issues or conflicts found
- Suggest alternatives when problems are detected

## Error Handling
- If a tool fails, explain the issue clearly
- Suggest corrective actions
- Escalate critical failures appropriately
"""


def create_orchestrator_agent() -> LlmAgent:
    """
    Create and configure the main orchestrator agent.

    Returns:
        Configured LlmAgent instance.
    """
    logger.info("Creating orchestrator agent", model=Config.ADK_MODEL)

    agent = LlmAgent(
        model=Config.ADK_MODEL,
        instruction=ORCHESTRATOR_INSTRUCTION,
        tools=[
            create_change_request,
            update_change_request,
            get_change_request,
            validate_change_request,
            check_calendar_conflicts,
            notify_approval_request,
            notify_approval_status,
        ],
        temperature=Config.ADK_TEMPERATURE,
    )

    logger.info("Orchestrator agent created successfully")
    return agent


# Create the agent instance
orchestrator_agent = create_orchestrator_agent()


if __name__ == "__main__":
    # Test the agent with a sample query
    print("\n🤖 Change Management Orchestrator Agent")
    print("=" * 50)
    print("\nAgent is ready for testing!")
    print("\nTo test the agent, run:")
    print("  adk web src/agents/orchestrator_agent.py")
    print("\nOr use the CLI:")
    print("  adk run src/agents/orchestrator_agent.py")
    print("\nExample queries:")
    print('  - "Create a CR for database migration on Friday at 6pm"')
    print('  - "Extend CR12345 by 2 hours"')
    print('  - "What is the status of CR12345?"')
    print()
