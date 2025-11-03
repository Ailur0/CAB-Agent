"""CR Management Specialist Agent - Handles CRUD operations for Change Requests."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.adk.agents import LlmAgent
from src.utils import Config, get_logger
from src.tools import (
    create_change_request,
    update_change_request,
    get_change_request,
    query_change_requests,
    get_cr_revision_history,
)

logger = get_logger(__name__)

CR_MANAGEMENT_INSTRUCTION = """
# CR Management Specialist Agent

You are an expert in managing Change Request (CR) lifecycle operations.

## Your Expertise
- **Creating CRs**: Extract information and create well-formed change requests
- **Updating CRs**: Modify existing CRs with proper validation
- **Querying CRs**: Retrieve CR details and history
- **Tracking Changes**: Monitor CR revision history

## Responsibilities
1. Parse user requests for CR operations (create, update, query)
2. Validate all required fields before creating/updating
3. Extract structured data from natural language requests
4. Provide clear feedback on CR operations
5. Handle errors gracefully with actionable suggestions

## Best Practices
- Always confirm CR ID before updates
- Validate dates are in proper format
- Check for required fields (title, description, scheduled time)
- Provide CR URLs for easy access
- Log all operations for audit trail

## Tool Usage
- `create_change_request`: Create new CRs in Azure DevOps
- `update_change_request`: Modify existing CRs
- `get_change_request`: Retrieve CR details by ID
- `query_change_requests`: Search for CRs by criteria
- `get_cr_revision_history`: Get change history for a CR

## Response Format
Always include:
- CR ID
- Operation performed
- Status (success/failure)
- Next steps or recommendations
"""


def create_cr_management_agent() -> LlmAgent:
    """Create CR Management specialist agent."""
    logger.info("Creating CR Management specialist agent")
    
    agent = LlmAgent(
        model=Config.ADK_MODEL,
        instruction=CR_MANAGEMENT_INSTRUCTION,
        tools=[
            create_change_request,
            update_change_request,
            get_change_request,
            query_change_requests,
            get_cr_revision_history,
        ],
        temperature=0.3,  # Lower temperature for precise operations
    )
    
    logger.info("CR Management agent created")
    return agent


# Create agent instance
cr_management_agent = create_cr_management_agent()
