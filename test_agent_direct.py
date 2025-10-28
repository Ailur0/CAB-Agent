"""Direct test script for the orchestrator agent using Gemini API."""

import sys
import os
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import google.generativeai as genai
from src.utils.config import get_config
from src.tools import (
    create_change_request,
    query_change_requests,
    get_change_request,
    update_change_request,
    check_calendar_conflicts,
    CHANGE_REQUEST_TYPES,
)


def execute_function_call(function_name, args):
    """Execute a TFS function call."""
    try:
        if function_name == "query_change_requests":
            # Extract parameters
            state = args.get("state")
            work_item_types = args.get("work_item_types")
            # Convert protobuf RepeatedComposite to list if needed
            if work_item_types and not isinstance(work_item_types, list):
                work_item_types = list(work_item_types)
            limit = int(args.get("limit", 2))
            days_back = args.get("days_back")
            assigned_to = args.get("assigned_to")
            
            # Calculate date range if days_back is provided
            date_range = None
            if days_back:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=int(days_back))
                date_range = {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                }
            
            print(f"   Querying TFS: state={state}, types={work_item_types}, assigned_to={assigned_to}, days_back={days_back}, limit={limit}")
            
            # Query TFS (note: query_change_requests has internal limit of 10)
            results = query_change_requests(
                state=state,
                work_item_types=work_item_types,
                assigned_to=assigned_to,
                date_range=date_range
            )
            
            if not results:
                return {
                    "status": "success",
                    "count": 0,
                    "message": "No change requests found matching the criteria.",
                    "results": []
                }
            
            # Limit results to what user requested
            results = results[:limit]
            
            # Format results for AI
            formatted_results = []
            for cr in results:
                formatted_results.append({
                    "cr_id": cr.get("cr_id", "N/A"),
                    "title": cr.get("title", "N/A"),
                    "state": cr.get("state", "N/A"),
                    "created_date": cr.get("created_date", "N/A"),
                    "created_by": cr.get("created_by", "N/A"),
                    "created_by_email": cr.get("created_by_unique_name", "N/A"),
                    "assigned_to": cr.get("assigned_to", "N/A"),
                    "scheduled_start": cr.get("scheduled_start_date", "N/A"),
                    "scheduled_end": cr.get("scheduled_end_date", "N/A"),
                    "approval_status": cr.get("approval_status", "N/A"),
                    "description": cr.get("description", "N/A")[:200] if cr.get("description") else "N/A",
                })
            
            return {
                "status": "success",
                "count": len(formatted_results),
                "results": formatted_results
            }
        
        elif function_name == "get_change_request":
            cr_id = args.get("cr_id")
            if not cr_id.startswith("CR"):
                cr_id = f"CR{cr_id}"
            
            print(f"   Fetching details for {cr_id}")
            result = get_change_request(cr_id)
            return result
        
        elif function_name == "update_change_request":
            cr_id = args.get("cr_id")
            if not cr_id.startswith("CR"):
                cr_id = f"CR{cr_id}"
            
            updates = args.get("updates", {})
            print(f"   Updating {cr_id} with: {updates}")
            
            result = update_change_request(cr_id, updates)
            return result
        
        elif function_name == "create_change_request":
            print(f"   Creating new change request...")
            
            result = create_change_request(
                title=args.get("title"),
                description=args.get("description"),
                change_type=args.get("change_type", "Normal Change Request"),
                scheduled_start_date=args.get("scheduled_start_date"),
                scheduled_end_date=args.get("scheduled_end_date"),
                assigned_to=args.get("assigned_to")
            )
            return result
        
        elif function_name == "check_calendar_conflicts":
            start_date = args.get("start_date")
            end_date = args.get("end_date")
            
            print(f"   Checking calendar conflicts: {start_date} to {end_date}")
            
            result = check_calendar_conflicts(
                start_date=start_date,
                end_date=end_date
            )
            return result
        
        else:
            return {"status": "error", "message": f"Unknown function: {function_name}"}
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"   ERROR: {str(e)}")
        print(error_details)
        return {"status": "error", "message": str(e), "details": error_details}


def setup_gemini():
    """Configure Gemini API with function calling."""
    config = get_config()
    
    if not config.GOOGLE_API_KEY:
        print("\n❌ ERROR: GOOGLE_API_KEY not set in .env file")
        print("\nTo get an API key:")
        print("  1. Go to: https://makersuite.google.com/app/apikey")
        print("  2. Create a new API key")
        print("  3. Add to .env: GOOGLE_API_KEY=your_key_here")
        return None
    
    genai.configure(api_key=config.GOOGLE_API_KEY)
    
    # Define tools for function calling
    tools = [
        {
            "function_declarations": [
                {
                    "name": "query_change_requests",
                    "description": "Query change requests from RealPage TFS. Use this when user asks for change requests, CRs, or work items. Supports filtering by date range.",
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
                                "description": "Filter by number of days back from today (e.g., 2 for past 2 days, 7 for past week)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results (default 2)"
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
                    "description": "Update a change request's fields (state, assigned_to, dates, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cr_id": {
                                "type": "string",
                                "description": "Work item ID to update"
                            },
                            "updates": {
                                "type": "object",
                                "description": "Fields to update (e.g., {\"state\": \"In Progress\", \"assigned_to\": \"user@email.com\"})"
                            }
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
                            "title": {
                                "type": "string",
                                "description": "Title of the change request"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the change"
                            },
                            "change_type": {
                                "type": "string",
                                "description": "Type: Normal Change Request, Emergency Change Request, or Standard Change Request"
                            },
                            "scheduled_start_date": {
                                "type": "string",
                                "description": "Start date in ISO format (YYYY-MM-DDTHH:MM:SSZ)"
                            },
                            "scheduled_end_date": {
                                "type": "string",
                                "description": "End date in ISO format (YYYY-MM-DDTHH:MM:SSZ)"
                            },
                            "assigned_to": {
                                "type": "string",
                                "description": "Email of person to assign to"
                            }
                        },
                        "required": ["title", "description"]
                    }
                },
                {
                    "name": "check_calendar_conflicts",
                    "description": "Check for calendar conflicts in a given date range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date in ISO format (YYYY-MM-DDTHH:MM:SSZ)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in ISO format (YYYY-MM-DDTHH:MM:SSZ)"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                }
            ]
        }
    ]
    
    return genai.GenerativeModel('gemini-2.0-flash-exp', tools=tools)


def chat_loop(model):
    """Interactive chat loop with the agent."""
    print("\n" + "=" * 70)
    print("🤖 CHANGE MANAGEMENT AI ASSISTANT")
    print("=" * 70)
    print("\nConnected to RealPage TFS Change Management")
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    # Initialize chat
    chat = model.start_chat(history=[])
    
    system_prompt = f"""
You are a Change Management Assistant for RealPage TFS.

Available Change Request Types: {', '.join(CHANGE_REQUEST_TYPES)}

Help users:
- Query change requests
- Get change details  
- Understand change management workflows

Be concise and helpful. Reference work item IDs when relevant.
"""
    
    chat.send_message(system_prompt)
    
    print("Agent: Hello! I'm your Change Management Assistant.")
    print("       Ask me about change requests or TFS workflows.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nAgent: Goodbye!\n")
                break
            
            # Send message to agent
            response = chat.send_message(user_input)
            
            # Check if agent wants to call functions
            function_calls = []
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
            
            # Execute all function calls and collect responses
            if function_calls:
                function_responses = []
                
                for function_call in function_calls:
                    function_name = function_call.name
                    function_args = dict(function_call.args)
                    
                    # Convert protobuf types to native Python types for JSON serialization
                    serializable_args = {}
                    for key, value in function_args.items():
                        if hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
                            serializable_args[key] = list(value)
                        else:
                            serializable_args[key] = value
                    
                    print(f"\n🔧 Executing: {function_name}({json.dumps(serializable_args, indent=2)})\n")
                    
                    # Call the actual TFS function
                    result = execute_function_call(function_name, function_args)
                    
                    # Add to responses
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": result}
                            )
                        )
                    )
                
                # Send all results back to agent at once
                response = chat.send_message(
                    genai.protos.Content(parts=function_responses)
                )
            
            # Print agent's response
            if response.text:
                print(f"\nAgent: {response.text}\n")
        
        except KeyboardInterrupt:
            print("\n\nAgent: Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("CHANGE MANAGEMENT AI ASSISTANT - DIRECT API")
    print("=" * 70)
    
    # Setup Gemini
    model = setup_gemini()
    if not model:
        return
    
    print("\n✓ Gemini API configured")
    print("✓ Connected to RealPage TFS\n")
    
    chat_loop(model)


if __name__ == "__main__":
    main()