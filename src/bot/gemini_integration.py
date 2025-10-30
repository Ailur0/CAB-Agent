"""OpenAI integration for Teams bot."""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from openai import AsyncOpenAI
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.tools import (
    create_change_request,
    query_change_requests,
    get_change_request,
    update_change_request,
    check_calendar_conflicts,
    get_cr_revision_history,
    query_crs_by_state_change,
    CHANGE_REQUEST_TYPES,
)

logger = get_logger(__name__)


class OpenAIAgent:
    """OpenAI agent for processing change management requests."""
    
    def __init__(self):
        """Initialize the OpenAI agent."""
        config = get_config()
        
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.ADK_MODEL
        self.temperature = config.ADK_TEMPERATURE
        
        # Define tools for function calling (OpenAI format)
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_change_requests",
                    "description": "Query change requests from RealPage TFS. Use when user asks for CRs or work items.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "description": "Filter by state: Active, Approved, Assigned, Awaiting PIR, Cancelled, Draft, In Progress, Pending Approvals, Pending CAB, Pending Closure, Rejected, Validate, Closed"
                            },
                            "work_item_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types: Normal Change Request, Emergency Change Request, Standard Change Request"
                            },
                            "assigned_to": {
                                "type": "string",
                                "description": "Filter by assignee email or name (e.g., 'john.doe@realpage.com' or 'John Doe')"
                            },
                            "days_back": {
                                "type": "integer",
                                "description": "Filter by days back from today"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results (default 5)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_change_request",
                    "description": "Get details of a specific change request by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cr_id": {
                                "type": "string",
                                "description": "Work item ID (e.g., '2579597' or 'CR2579597')"
                            }
                        },
                        "required": ["cr_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_change_request",
                    "description": "Update a change request's fields",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cr_id": {"type": "string", "description": "Work item ID"},
                            "updates": {"type": "object", "description": "Fields to update"}
                        },
                        "required": ["cr_id", "updates"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_change_request",
                    "description": "Create a new change request in TFS",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "change_type": {"type": "string"},
                            "scheduled_start_date": {"type": "string"},
                            "scheduled_end_date": {"type": "string"},
                            "assigned_to": {"type": "string"}
                        },
                        "required": ["title", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_cr_revision_history",
                    "description": "Get revision history for a Change Request, showing all state changes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cr_id": {"type": "string", "description": "Work item ID"},
                            "from_state": {"type": "string", "description": "Optional: Filter FROM this state"},
                            "to_state": {"type": "string", "description": "Optional: Filter TO this state"},
                            "date": {"type": "string", "description": "Optional: Filter by date (YYYY-MM-DD)"}
                        },
                        "required": ["cr_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_crs_by_state_change",
                    "description": "Query CRs that transitioned from one state to another on a specific date. If user asks for 'today', leave date empty/null.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_state": {"type": "string", "description": "State CRs transitioned FROM"},
                            "to_state": {"type": "string", "description": "State CRs transitioned TO"},
                            "date": {"type": "string", "description": "Optional: Specific date (YYYY-MM-DD). Leave empty for today."},
                            "work_item_types": {"type": "array", "items": {"type": "string"}, "description": "Optional: CR types"}
                        },
                        "required": ["from_state", "to_state"]
                    }
                }
            }
        ]
        
        self.conversations = {}  # Store conversation history by user_id
        
        logger.info("OpenAIAgent initialized")
    
    def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a TFS function call."""
        try:
            logger.info(f"Executing: {function_name}", args=args)
            
            if function_name == "query_change_requests":
                state = args.get("state")
                work_item_types = args.get("work_item_types")
                limit = int(args.get("limit", 5))
                days_back = args.get("days_back")
                assigned_to = args.get("assigned_to")
                
                date_range = None
                if days_back:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=int(days_back))
                    date_range = {
                        "start": start_date.strftime("%Y-%m-%d"),
                        "end": end_date.strftime("%Y-%m-%d")
                    }
                
                results = query_change_requests(
                    state=state,
                    work_item_types=work_item_types,
                    assigned_to=assigned_to,
                    date_range=date_range
                )
                
                results = results[:limit]
                
                formatted_results = []
                for cr in results:
                    formatted_results.append({
                        "cr_id": cr.get("cr_id", "N/A"),
                        "title": cr.get("title", "N/A"),
                        "state": cr.get("state", "N/A"),
                        "created_by": cr.get("created_by", "N/A"),
                        "assigned_to": cr.get("assigned_to", "N/A"),
                        "scheduled_start": cr.get("scheduled_start_date", "N/A"),
                        "description": cr.get("description", "N/A")[:150] if cr.get("description") else "N/A",
                    })
                
                return {"status": "success", "count": len(formatted_results), "results": formatted_results}
            
            elif function_name == "get_change_request":
                cr_id = args.get("cr_id")
                if not cr_id.startswith("CR"):
                    cr_id = f"CR{cr_id}"
                return get_change_request(cr_id)
            
            elif function_name == "update_change_request":
                cr_id = args.get("cr_id")
                if not cr_id.startswith("CR"):
                    cr_id = f"CR{cr_id}"
                updates = args.get("updates", {})
                return update_change_request(cr_id, updates)
            
            elif function_name == "create_change_request":
                return create_change_request(
                    title=args.get("title"),
                    description=args.get("description"),
                    change_type=args.get("change_type", "Normal Change Request"),
                    scheduled_start_date=args.get("scheduled_start_date"),
                    scheduled_end_date=args.get("scheduled_end_date"),
                    assigned_to=args.get("assigned_to")
                )
            
            elif function_name == "get_cr_revision_history":
                cr_id = args.get("cr_id")
                if not cr_id.startswith("CR"):
                    cr_id = f"CR{cr_id}"
                return get_cr_revision_history(
                    cr_id=cr_id,
                    from_state=args.get("from_state"),
                    to_state=args.get("to_state"),
                    date=args.get("date")
                )
            
            elif function_name == "query_crs_by_state_change":
                return query_crs_by_state_change(
                    from_state=args.get("from_state"),
                    to_state=args.get("to_state"),
                    date=args.get("date"),
                    work_item_types=args.get("work_item_types")
                )
            
            else:
                return {"status": "error", "message": f"Unknown function: {function_name}"}
        
        except Exception as e:
            logger.error(f"Function error: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    async def process_message(self, user_id: str, message: str, user_name: str = None) -> str:
        """
        Process a user message and return AI response.
        
        Args:
            user_id: Unique identifier for the user
            message: User's message text
            user_name: Optional user display name
        
        Returns:
            AI response text
        """
        try:
            # Get or create conversation history
            if user_id not in self.conversations:
                from datetime import datetime
                current_date = datetime.now().strftime("%Y-%m-%d")
                current_date_readable = datetime.now().strftime("%B %d, %Y")
                
                system_message = {
                    "role": "system",
                    "content": f"""
You are a Change Management Assistant for RealPage TFS in Microsoft Teams.

IMPORTANT: Today's date is {current_date_readable} ({current_date}).
When users ask for "today", use this date. When they ask for "yesterday", calculate it as one day before today.

Available Change Request Types: {', '.join(CHANGE_REQUEST_TYPES)}

Help users:
- Query change requests
- Get change details
- Create new change requests
- Update existing change requests
- Understand change management workflows

Be concise, friendly, and helpful. Use emojis when appropriate for Teams.
Reference work item IDs when relevant.
{f'Current user: {user_name}' if user_name else ''}

CRITICAL: For date-related queries:
- If user asks for "today", leave the date parameter EMPTY (null/undefined) - the system will use today's date automatically
- If user asks for a specific date like "yesterday" or "October 28", calculate the exact date in YYYY-MM-DD format and provide it
- Never use dates from 2023 or other old years unless explicitly requested
"""
                }
                self.conversations[user_id] = [system_message]
            
            # Add user message to conversation history
            self.conversations[user_id].append({
                "role": "user",
                "content": message
            })
            
            logger.info(f"Processing message for {user_id}: {message}")
            
            # Call OpenAI API with function calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.conversations[user_id],
                tools=self.tools,
                tool_choice="auto",
                temperature=self.temperature
            )
            
            response_message = response.choices[0].message
            
            # Check if the model wants to call functions
            if response_message.tool_calls:
                # Add assistant's response to conversation
                self.conversations[user_id].append(response_message)
                
                # Execute all function calls
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Calling function: {function_name}", args=function_args)
                    
                    # Execute the function
                    function_result = self._execute_function(function_name, function_args)
                    
                    # Add function result to conversation
                    self.conversations[user_id].append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_result)
                    })
                
                # Get final response from the model
                second_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversations[user_id],
                    temperature=self.temperature
                )
                
                final_message = second_response.choices[0].message
                self.conversations[user_id].append(final_message)
                
                return final_message.content if final_message.content else "✅ Request processed."
            else:
                # No function calls, just return the response
                self.conversations[user_id].append(response_message)
                return response_message.content if response_message.content else "✅ Request processed."
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return f"❌ Sorry, I encountered an error: {str(e)}"
    
    def clear_conversation(self, user_id: str):
        """Clear conversation history for a user."""
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Cleared conversation for {user_id}")


# Global instance
_agent = None


def get_openai_agent() -> OpenAIAgent:
    """Get or create the global OpenAI agent instance."""
    global _agent
    if _agent is None:
        _agent = OpenAIAgent()
    return _agent


# Backward compatibility alias
get_gemini_agent = get_openai_agent
GeminiAgent = OpenAIAgent
