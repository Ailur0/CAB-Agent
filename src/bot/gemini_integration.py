"""Gemini AI integration for Teams bot."""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import google.generativeai as genai
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.tools import (
    create_change_request,
    query_change_requests,
    get_change_request,
    update_change_request,
    check_calendar_conflicts,
    CHANGE_REQUEST_TYPES,
)

logger = get_logger(__name__)


class GeminiAgent:
    """Gemini AI agent for processing change management requests."""
    
    def __init__(self):
        """Initialize the Gemini agent."""
        config = get_config()
        
        if not config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        genai.configure(api_key=config.GOOGLE_API_KEY)
        
        # Define tools for function calling
        tools = [
            {
                "function_declarations": [
                    {
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
                    },
                    {
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
                    },
                    {
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
                    },
                    {
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
                ]
            }
        ]
        
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp', tools=tools)
        self.conversations = {}  # Store conversation history by user_id
        
        logger.info("GeminiAgent initialized")
    
    def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a TFS function call."""
        try:
            logger.info(f"Executing: {function_name}", args=args)
            
            if function_name == "query_change_requests":
                state = args.get("state")
                work_item_types = args.get("work_item_types")
                # Convert protobuf RepeatedComposite to list if needed
                if work_item_types and not isinstance(work_item_types, list):
                    work_item_types = list(work_item_types)
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
                chat = self.model.start_chat(history=[])
                
                system_prompt = f"""
You are a Change Management Assistant for RealPage TFS in Microsoft Teams.

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
"""
                chat.send_message(system_prompt)
                self.conversations[user_id] = chat
            else:
                chat = self.conversations[user_id]
            
            logger.info(f"Processing message for {user_id}: {message}")
            
            # Send user message
            response = chat.send_message(message)
            
            # Check for function calls
            function_calls = []
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
            
            # Execute all function calls
            if function_calls:
                function_responses = []
                
                for function_call in function_calls:
                    function_name = function_call.name
                    function_args = dict(function_call.args)
                    
                    result = self._execute_function(function_name, function_args)
                    
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": result}
                            )
                        )
                    )
                
                # Send function results back
                response = chat.send_message(
                    genai.protos.Content(parts=function_responses)
                )
            
            return response.text if response.text else "✅ Request processed."
        
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


def get_gemini_agent() -> GeminiAgent:
    """Get or create the global Gemini agent instance."""
    global _agent
    if _agent is None:
        _agent = GeminiAgent()
    return _agent
