"""Direct test script for the orchestrator agent using OpenAI API."""

import sys
import os
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


import asyncio
from openai import AsyncOpenAI
from src.utils.config import get_config
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
            limit = int(args.get("limit", 30))
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
        
        elif function_name == "get_cr_revision_history":
            cr_id = args.get("cr_id")
            if not cr_id.startswith("CR"):
                cr_id = f"CR{cr_id}"
            
            from_state = args.get("from_state")
            to_state = args.get("to_state")
            date = args.get("date")
            
            print(f"   Getting revision history for {cr_id}")
            if from_state or to_state:
                print(f"   Filtering: {from_state} -> {to_state}")
            if date:
                print(f"   Date filter: {date}")
            
            result = get_cr_revision_history(
                cr_id=cr_id,
                from_state=from_state,
                to_state=to_state,
                date=date
            )
            return result
        
        elif function_name == "query_crs_by_state_change":
            from_state = args.get("from_state")
            to_state = args.get("to_state")
            date = args.get("date")
            work_item_types = args.get("work_item_types")
            
            print(f"   Querying CRs that changed from '{from_state}' to '{to_state}'")
            if date:
                print(f"   Date: {date}")
            else:
                print(f"   Date: Today")
            
            result = query_crs_by_state_change(
                from_state=from_state,
                to_state=to_state,
                date=date,
                work_item_types=work_item_types
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


def setup_openai():
    """Configure OpenAI API with function calling."""
    config = get_config()
    
    if not config.OPENAI_API_KEY:
        print("\n❌ ERROR: OPENAI_API_KEY not set in .env file")
        print("\nTo get an API key:")
        print("  1. Go to: https://platform.openai.com/api-keys")
        print("  2. Create a new API key")
        print("  3. Add to .env: OPENAI_API_KEY=your_key_here")
        return None, None
    
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    model = config.OPENAI_MODEL
    
    # Define tools for function calling (OpenAI format)
    tools = [
        {
            "type": "function",
            "function": {
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
                            "description": "Max results (default 30)"
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
            }
        },
        {
            "type": "function",
            "function": {
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
        },
        {
            "type": "function",
            "function": {
                "name": "get_cr_revision_history",
                "description": "Get revision history for a Change Request, showing all state changes. Optionally filter by specific state transitions and dates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cr_id": {
                            "type": "string",
                            "description": "Work item ID (e.g., '2579597' or 'CR2579597')"
                        },
                        "from_state": {
                            "type": "string",
                            "description": "Optional: Filter for transitions FROM this state (e.g., 'Pending CAB')"
                        },
                        "to_state": {
                            "type": "string",
                            "description": "Optional: Filter for transitions TO this state (e.g., 'Approved')"
                        },
                        "date": {
                            "type": "string",
                            "description": "Optional: Filter for changes on this date (YYYY-MM-DD format)"
                        }
                    },
                    "required": ["cr_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_crs_by_state_change",
                "description": "Query Change Requests that transitioned from one state to another on a specific date. Use this to find CRs that changed from 'Pending CAB' to 'Approved' today, or any other state transition. IMPORTANT: If the user asks for 'today', leave the date parameter empty or null - do NOT calculate it yourself.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_state": {
                            "type": "string",
                            "description": "The state CRs transitioned FROM (e.g., 'Pending CAB', 'Draft', 'In Progress')"
                        },
                        "to_state": {
                            "type": "string",
                            "description": "The state CRs transitioned TO (e.g., 'Approved', 'Active', 'Closed')"
                        },
                        "date": {
                            "type": "string",
                            "description": "Optional: Filter for changes on this specific date in YYYY-MM-DD format (e.g., '2025-10-29'). Leave empty/null for today's date - the system will automatically use today's date if this is not provided."
                        },
                        "work_item_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional: Types to filter (Normal Change Request, Emergency Change Request, Standard Change Request)"
                        }
                    },
                    "required": ["from_state", "to_state"]
                }
            }
        }
    ]
    
    return client, model, tools


async def chat_loop(client, model_name, tools):
    """Interactive chat loop with the agent."""
    print("\n" + "=" * 70)
    print("🤖 CHANGE MANAGEMENT AI ASSISTANT")
    print("=" * 70)
    print("\nConnected to RealPage TFS Change Management")
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    # Initialize conversation history with current date context
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_date_readable = datetime.now().strftime("%B %d, %Y")
    
    messages = [
        {
            "role": "system",
            "content": f"""
You are a Change Management Assistant for RealPage TFS.

IMPORTANT: Today's date is {current_date_readable} ({current_date}).
When users ask for "today", use this date. When they ask for "yesterday", calculate it as one day before today.

Available Change Request Types: {', '.join(CHANGE_REQUEST_TYPES)}

Help users:
- Query change requests
- Get change details  
- Understand change management workflows

Be concise and helpful. Reference work item IDs when relevant.

CRITICAL: For date-related queries:
- If user asks for "today", leave the date parameter EMPTY (null/undefined) - the system will use today's date automatically
- If user asks for a specific date like "yesterday" or "October 28", calculate the exact date in YYYY-MM-DD format and provide it
- Never use dates from 2023 or other old years unless explicitly requested
"""
        }
    ]
    
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
            
            # Add user message to history
            messages.append({"role": "user", "content": user_input})
            
            # Send message to OpenAI
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Check if the model wants to call functions
            if response_message.tool_calls:
                # Add assistant's response to messages
                messages.append(response_message)
                
                # Execute all function calls
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"\n🔧 Executing: {function_name}({json.dumps(function_args, indent=2)})\n")
                    
                    # Call the actual TFS function
                    result = execute_function_call(function_name, function_args)
                    
                    # Add function result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(result)
                    })
                
                # Get final response from the model
                second_response = await client.chat.completions.create(
                    model=model_name,
                    messages=messages
                )
                
                final_message = second_response.choices[0].message
                messages.append(final_message)
                
                if final_message.content:
                    print(f"\nAgent: {final_message.content}\n")
            else:
                # No function calls, just return the response
                messages.append(response_message)
                if response_message.content:
                    print(f"\nAgent: {response_message.content}\n")
        
        except KeyboardInterrupt:
            print("\n\nAgent: Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            import traceback
            traceback.print_exc()


async def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("CHANGE MANAGEMENT AI ASSISTANT - DIRECT API")
    print("=" * 70)
    
    # Setup OpenAI
    result = setup_openai()
    if result is None or result[0] is None:
        return
    
    client, model_name, tools = result
    
    print(f"\n✓ OpenAI API configured (model: {model_name})")
    print("✓ Connected to RealPage TFS\n")
    
    try:
        await chat_loop(client, model_name, tools)
    finally:
        # Properly close the OpenAI client
        await client.close()


if __name__ == "__main__":
    # Run with proper cleanup on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())