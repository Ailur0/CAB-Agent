"""Router Agent - Main orchestrator that delegates to specialized agents (Mixture of Experts)."""

import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from google.adk.agents import LlmAgent
from src.utils import Config, get_logger

logger = get_logger(__name__)

ROUTER_INSTRUCTION = """
# Router Agent - Mixture of Experts Orchestrator

You are the main orchestrator that intelligently routes requests to specialized expert agents.

## Available Expert Agents

### 1. CR Management Agent
**Expertise**: CRUD operations for Change Requests
**Use when**: User wants to create, update, query, or retrieve CR information
**Examples**: 
- "Create a CR for database migration"
- "Update CR12345 with new end time"
- "Show me details of CR12345"
- "Find all CRs created by john@example.com"

### 2. Validation Agent
**Expertise**: Compliance validation and conflict detection
**Use when**: Need to validate CR compliance or check for conflicts
**Examples**:
- "Validate CR12345 for compliance"
- "Check if there are conflicts for Friday 6pm maintenance"
- "Is the team available on Saturday morning?"
- "Find available time slots for next week"

### 3. Approval Agent
**Expertise**: Approval workflows and timeout management
**Use when**: Managing approvals, tracking approval status, or handling timeouts
**Examples**:
- "Send approval request for CR12345 to manager@example.com"
- "Check approval status for request APR-12345"
- "Record approval decision for CR12345"

### 4. PIR Agent
**Expertise**: Post-Implementation Review tracking
**Use when**: Managing PIR workflows after CR completion
**Examples**:
- "Initiate PIR for CR12345"
- "Check PIR status for CR12345"
- "Send PIR reminder"

### 5. Notification Agent
**Expertise**: Stakeholder communication and notifications
**Use when**: Sending notifications, reminders, or escalations
**Examples**:
- "Notify user@example.com about CR12345 approval"
- "Send reminder for pending CR"
- "Escalate CR12345 to management"

## Routing Strategy

1. **Analyze the user request** to understand intent
2. **Identify the primary task** (create, validate, approve, notify, etc.)
3. **Select the most appropriate expert agent**
4. **Delegate the task** with clear context
5. **Coordinate multiple agents** if task requires multiple specialties
6. **Synthesize responses** from multiple agents into coherent answer

## Multi-Agent Coordination

For complex requests requiring multiple agents:
1. Break down the request into subtasks
2. Route each subtask to appropriate expert
3. Execute in logical order (e.g., validate before create)
4. Combine results into unified response

## Examples of Routing

**Request**: "Create a CR for database migration on Friday at 6pm"
**Route to**: CR Management Agent → Validation Agent (check conflicts) → CR Management Agent (create)

**Request**: "Validate and send approval for CR12345"
**Route to**: Validation Agent → Approval Agent

**Request**: "What's the status of CR12345?"
**Route to**: CR Management Agent

## Your Response

After routing to expert agents:
1. Summarize what was done
2. Provide key results (CR ID, status, etc.)
3. Mention any issues or warnings
4. Suggest next steps if applicable
"""


def create_router_agent() -> LlmAgent:
    """
    Create the main router agent that delegates to specialized agents.
    
    This implements the Mixture of Experts pattern where the router
    intelligently selects which expert agent(s) to use based on the request.
    """
    logger.info("Creating Router agent (MoE orchestrator)")
    
    # Import specialized agents
    from src.agents.cr_management_agent import cr_management_agent
    from src.agents.validation_agent import validation_agent
    from src.agents.approval_agent import approval_agent
    from src.agents.pir_agent import pir_agent
    from src.agents.notification_agent import notification_agent
    
    # Create a tool that allows the router to delegate to expert agents
    def delegate_to_cr_management(task: str) -> Dict[str, Any]:
        """
        Delegate task to CR Management specialist agent.
        
        Args:
            task: The task description for the CR Management agent
            
        Returns:
            Result from the CR Management agent
        """
        logger.info("Delegating to CR Management agent", task=task)
        try:
            response = cr_management_agent.run(task)
            return {"status": "success", "response": response.text}
        except Exception as e:
            logger.error("CR Management agent error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def delegate_to_validation(task: str) -> Dict[str, Any]:
        """
        Delegate task to Validation specialist agent.
        
        Args:
            task: The task description for the Validation agent
            
        Returns:
            Result from the Validation agent
        """
        logger.info("Delegating to Validation agent", task=task)
        try:
            response = validation_agent.run(task)
            return {"status": "success", "response": response.text}
        except Exception as e:
            logger.error("Validation agent error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def delegate_to_approval(task: str) -> Dict[str, Any]:
        """
        Delegate task to Approval specialist agent.
        
        Args:
            task: The task description for the Approval agent
            
        Returns:
            Result from the Approval agent
        """
        logger.info("Delegating to Approval agent", task=task)
        try:
            response = approval_agent.run(task)
            return {"status": "success", "response": response.text}
        except Exception as e:
            logger.error("Approval agent error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def delegate_to_pir(task: str) -> Dict[str, Any]:
        """
        Delegate task to PIR specialist agent.
        
        Args:
            task: The task description for the PIR agent
            
        Returns:
            Result from the PIR agent
        """
        logger.info("Delegating to PIR agent", task=task)
        try:
            response = pir_agent.run(task)
            return {"status": "success", "response": response.text}
        except Exception as e:
            logger.error("PIR agent error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def delegate_to_notification(task: str) -> Dict[str, Any]:
        """
        Delegate task to Notification specialist agent.
        
        Args:
            task: The task description for the Notification agent
            
        Returns:
            Result from the Notification agent
        """
        logger.info("Delegating to Notification agent", task=task)
        try:
            response = notification_agent.run(task)
            return {"status": "success", "response": response.text}
        except Exception as e:
            logger.error("Notification agent error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    # Create router agent with delegation tools
    agent = LlmAgent(
        model=Config.ADK_MODEL,
        instruction=ROUTER_INSTRUCTION,
        tools=[
            delegate_to_cr_management,
            delegate_to_validation,
            delegate_to_approval,
            delegate_to_pir,
            delegate_to_notification,
        ],
        temperature=0.5,  # Moderate temperature for intelligent routing
    )
    
    logger.info("Router agent created successfully")
    return agent


# Create the router agent instance
router_agent = create_router_agent()


if __name__ == "__main__":
    print("\n🎯 Router Agent - Mixture of Experts")
    print("=" * 60)
    print("\nThis agent intelligently routes requests to specialized agents:")
    print("  • CR Management Agent - CRUD operations")
    print("  • Validation Agent - Compliance & conflict checking")
    print("  • Approval Agent - Approval workflows")
    print("  • PIR Agent - Post-Implementation Reviews")
    print("  • Notification Agent - Stakeholder communication")
    print("\nExample queries:")
    print('  - "Create a CR for database migration on Friday at 6pm"')
    print('  - "Validate CR12345 and check for conflicts"')
    print('  - "Send approval request for CR12345 to manager@example.com"')
    print()
