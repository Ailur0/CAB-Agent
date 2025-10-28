### Building an Automated Change Management System with Google ADK and Python

This report provides a detailed, developer-centric guide to creating a sophisticated, automated change management system. The initial query was broad, asking how to achieve a goal using "ADK and coding." This document makes a sophisticated assumption that the goal is to build a real-world, complex system, such as one for automating IT change management. The solution leverages a code-first approach using Python, Google's Agent Development Kit (ADK) for backend orchestration, and a Microsoft Teams bot as the conversational front-end.

### 1. Foundational Code-Based Setup

A robust development environment is the cornerstone of this project. This section covers the setup for the Google ADK, Microsoft Teams bot development, and the cross-platform authentication required to connect these services securely.

#### **Google Agent Development Kit (ADK) Environment**

The ADK is an open-source, code-first Python toolkit for building and orchestrating sophisticated AI agents.

*   **Prerequisites**: You will need Python 3.9+ (3.10–3.12 recommended), a Google Account to get a Gemini API key, and familiarity with using a terminal and Python virtual environments.
*   **Installation**:
    1.  Create and activate a Python virtual environment to isolate project dependencies.
        ```bash
        # For macOS/Linux
        python3 -m venv .venv
        source .venv/bin/activate
        
        # For Windows
        python -m venv .venv
        .venv\Scripts\activate.bat
        ```
    2.  Install the ADK library using `pip`:
        ```bash
        pip install google-adk
        ```
*   **Configuration**:
    1.  Obtain a Gemini API key from Google AI Studio.
    2.  Store this key securely in a `.env` file in your project's root directory. The ADK automatically looks for the `GOOGLE_API_KEY` environment variable.
        ```
        GOOGLE_API_KEY="your_api_key_here"
        ```
*   **Local Testing**: The ADK provides several ways to test your agent locally before deployment:
    *   **Interactive Web UI**: Launch a web-based chat interface for visual testing with `adk web my_agent`.
    *   **API Server**: Expose your agent as an HTTP endpoint for integration testing with `adk api_server`.
    *   **Command-Line Interface (CLI)**: Interact with your agent directly from the terminal for quick tests using `adk run my_agent`.

#### **Microsoft Teams Bot Development Environment**

The front-end of our system will be a conversational bot in Microsoft Teams, built using Python.

*   **Prerequisites**: You need Python 3.7+, Visual Studio Code, a Microsoft 365 developer account, an Azure account for hosting, and a tunneling tool like ngrok for local testing.
*   **Recommended VS Code Extensions**:
    *   **Teams Toolkit**: Simplifies creating, debugging, and deploying Teams apps.
    *   **Python Extension**: Provides IntelliSense, linting, and debugging for Python.
    *   **Azure App Service Extension**: Helps with deploying your bot to Azure.
*   **Installation**:
    1.  Within an active virtual environment, install the necessary libraries:
        ```bash
        # Core library for building bots
        pip install botbuilder-core
        
        # Simplifies development of AI-powered bots for Teams
        pip install teams-ai
        
        # Web framework to handle HTTP requests (e.g., Flask or AIOHTTP)
        pip install flask aiohttp
        ```
*   **Bot Registration**: Your bot must be registered in Azure. Go to the Azure portal and create an "Azure Bot" resource. This process generates a Microsoft App ID and a client secret, which are essential for your bot's configuration.

#### **Cross-Platform Authentication**

Your application will need to securely authenticate with both Google Cloud and Microsoft Azure services.

*   **Authenticating with Google Cloud (Service Accounts)**:
    1.  **Creation**: In the Google Cloud Console, navigate to "IAM & Admin" > "Service Accounts" to create a new service account. Grant it the minimum necessary IAM roles (e.g., "Secret Manager Secret Accessor") following the principle of least privilege.
    2.  **Key Generation**: Create and download a JSON key file for the service account. **Treat this file like a password and never commit it to version control**.
    3.  **Usage in Python**: The recommended method is to set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your JSON key file. Google's client libraries will automatically use these credentials.
        ```python
        # No explicit credential handling is needed in the code
        from google.cloud import storage
        storage_client = storage.Client() 
        ```
    4.  **Security Best Practices**: For production, store keys in **Google Secret Manager** and have your application fetch them at runtime. When running on Google Cloud infrastructure (like Cloud Functions or Cloud Run), attach the service account directly to the resource and use Application Default Credentials (ADC) to avoid managing keys altogether.

*   **Authenticating with Microsoft Graph API (MSAL)**:
    1.  **App Registration**: In the Microsoft Entra ID portal, create a new "App registration". Note the **Application (client) ID** and **Directory (tenant) ID**.
    2.  **Client Secret**: Under "Certificates & secrets," create a new client secret and copy its value immediately, as it will not be fully visible again.
    3.  **API Permissions**: Grant your application the necessary Microsoft Graph permissions. There are two types:
        *   **Delegated Permissions**: The app acts on behalf of a signed-in user.
        *   **Application Permissions**: The app runs in the background without a user. These often require admin consent. For this system's backend, you will use Application permissions.
    4.  **Usage in Python (Application Permissions)**: Use the Microsoft Authentication Library (`msal`) for Python to acquire a token using the client credentials flow. The scope for this flow is always `https://graph.microsoft.com/.default`.
        ```python
        import msal
        import requests

        # --- Configuration (Store these securely in a secret manager) ---
        CLIENT_ID = "YOUR_APPLICATION_CLIENT_ID"
        CLIENT_SECRET = "YOUR_CLIENT_SECRET_VALUE"
        TENANT_ID = "YOUR_DIRECTORY_TENANT_ID"
        AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
        SCOPES = ["https://graph.microsoft.com/.default"]

        app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            authority=AUTHORITY,
            client_credential=CLIENT_SECRET
        )

        result = app.acquire_token_for_client(scopes=SCOPES)

        if "access_token" in result:
            headers = {'Authorization': 'Bearer ' + result['access_token']}
            response = requests.get("https://graph.microsoft.com/v1.0/users", headers=headers)
            print(response.json())
        else:
            print(f"Error acquiring token: {result.get('error_description')}")
        ```

### 2. Developing the Teams Bot Front-End in Python

The Teams bot serves as the user interface for initiating requests and receiving notifications.

#### **Bot Application Logic and Web Server**

The core of the bot is built around the `TeamsActivityHandler`, which processes incoming events from Teams. This logic is hosted on a web server that listens for requests from the Bot Framework service.

*   **Web Server**: AIOHTTP is recommended due to its asynchronous nature, which aligns well with the Bot Framework SDK. Flask is also a viable, beginner-friendly option.
*   **Core Logic (`bot.py`)**: Create a class that inherits from `TeamsActivityHandler`. The `TurnContext` object, passed to each handler, provides all information about the incoming activity and is used to send replies.
    *   Override `on_message_activity` to handle user messages.
    *   Override `on_members_added_activity` to greet new users.
    *   Override Teams-specific methods like `on_teams_team_renamed_activity` to react to channel events.
    ```python
    from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
    from botbuilder.schema import ChannelAccount

    class MyTeamsBot(ActivityHandler):
        async def on_message_activity(self, turn_context: TurnContext):
            # Logic to parse command and trigger ADK agent
            await turn_context.send_activity(MessageFactory.text(f"Processing your request for: '{turn_context.activity.text}'"))

        async def on_members_added_activity(self, members_added: [ChannelAccount], turn_context: TurnContext):
            for member in members_added:
                if member.id != turn_context.activity.recipient.id:
                    await turn_context.send_activity(MessageFactory.text(f"Welcome, {member.name}!"))
    ```
*   **Server Setup (`app.py` with AIOHTTP)**: The server code initializes the `BotFrameworkAdapter` with your App ID and secret, creates an endpoint (e.g., `/api/messages`), and processes incoming activities by calling the adapter's `process_activity` method.

#### **Command Parsing and State Management**

To understand user requests and manage multi-step conversations, the bot needs NLU and state management capabilities.

*   **Intent and Entity Extraction**: Use Azure's **Conversational Language Understanding (CLU)** to parse user messages. For a message like "extend CR12345 by 2 hours," you would train a CLU model to extract the `extend_request` intent and entities like `change_request_id` ("CR12345") and `duration` ("2 hours"). You can create a custom Python recognizer to call the CLU API endpoint from your bot.
*   **Conversation State**: The Bot Framework SDK provides `ConversationState` to store information related to the current conversation (like the status of a request) and `UserState` for user-specific data. For production, use a persistent storage layer like Azure Blob Storage or Cosmos DB to ensure state is not lost if the bot restarts. Use state property accessors to read and write to your state objects.
*   **Multi-Turn Dialogs**: Use a `WaterfallDialog` within a `ComponentDialog` to guide the user through a sequence of steps, such as confirming details for a request. This dialog structure works with `ConversationState` to track progress across multiple turns.

#### **Proactive Messaging**

To send notifications like approval status or escalations, the bot must be able to send proactive messages.

1.  **Capture Conversation Reference**: During any user interaction, capture the `conversation_reference` from the `TurnContext`. This reference acts as the "return address" for the user or channel.
    ```python
    from botbuilder.core import TurnContext
    conversation_reference = TurnContext.get_conversation_reference(turn_context.activity)
    ```
2.  **Securely Store the Reference**: Store the captured `conversation_reference` in a persistent database like Azure Blob Storage or Cosmos DB, keyed by a unique identifier like the user ID or request ID. Avoid hardcoding connection strings by using a service like Azure Key Vault, which your bot can access via a managed identity.
3.  **Trigger and Send**: Create a dedicated API endpoint on your bot (e.g., `/api/notify`) that can be called by your backend system. When this endpoint is triggered, retrieve the appropriate `conversation_reference` from storage and use the adapter's `continue_conversation` method to send the message.
4.  **Handle Stale References**: Conversation references can become stale. Implement a cleanup mechanism, such as using the Time To Live (TTL) feature in Cosmos DB, to remove old references and avoid errors.

### 3. Backend Orchestration with Google's ADK

The ADK is used to build the backend agent that orchestrates the entire change management workflow.

#### **Orchestrator Agent Design**

A primary "Orchestrator Agent" manages the end-to-end process by delegating tasks to specialized sub-agents.

*   **Architecture**: The orchestrator receives a request and routes it to the correct sub-agent (e.g., a `ValidateCrAgent`, `CheckCalendarAgent`). This modular, hierarchical design makes the system easier to debug, maintain, and scale.
*   **Agent Types**:
    *   `LlmAgent`: Uses a large language model to dynamically decide which tool or sub-agent to use based on natural language instructions.
    *   `WorkflowAgent`: Orchestrates sub-agents in a deterministic sequence (e.g., `SequentialAgent` or `ParallelAgent`), which is more reliable for predictable processes.
*   **Instructions**: The `instruction` parameter is critical for guiding the agent's behavior. Your instructions should be specific, clear, use markdown for readability, and explain the agent's role and how it should use its tools.

#### **Defining Agent Tools**

Each step of the workflow (e.g., updating a CR in Azure DevOps) is implemented as a "Tool" that the agent can use.

*   **Implementation**: A tool is a standard Python function. The ADK automatically inspects the function's signature and docstring to understand its purpose and arguments. No special decorators are needed.
*   **Key Elements**:
    1.  **Type Hints**: Use Python type hints for all function parameters. This tells the LLM what kind of data to provide for each argument.
    2.  **Docstring**: Write a clear, descriptive docstring explaining the function's purpose and its parameters. This is the primary information the LLM uses to decide when to call the tool.
    3.  **Integration**: Simply pass the function object into the `tools` list when creating your `LlmAgent`.

    ```python
    from google.adk.agents import LlmAgent

    def update_cr_in_devops(cr_id: str, new_extension_time: str) -> dict:
        """
        Updates the extension time for a given Change Request (CR) in Azure DevOps.

        Args:
            cr_id (str): The ID of the Change Request to update.
            new_extension_time (str): The new time to set for the extension.

        Returns:
            dict: A dictionary indicating the status of the update.
        """
        # ... logic to call Azure DevOps API ...
        print(f"--> Tool: Updating {cr_id} with new time {new_extension_time}")
        return {"status": "success", "cr_id": cr_id}

    # Provide the function as a tool to the agent
    orchestrator_agent = LlmAgent(
        model='gemini-1.5-flash',
        instruction="You are an agent that manages change requests. Use your tools to perform actions.",
        tools=[update_cr_in_devops]
    )
    ```

#### **Implementing Human-in-the-Loop with a Timeout**

For handling approvals, the agent can implement a human-in-the-loop (HITL) pattern with a timeout for escalation.

*   **Pattern**: The agent sends an approval request, waits for a response, and triggers a different action if no response is received within a set time.
*   **Implementation**:
    1.  **Send Request**: A custom tool sends the approval request to an external system (e.g., a message to a manager in Teams) and stores a request ID and timestamp in the agent's session state.
    2.  **Wait and Poll**: A `LoopAgent` is used to repeatedly call another tool that checks the status of the approval request in the external system.
    3.  **Timeout Logic**: Inside the loop, the agent checks if the current time has exceeded the stored timestamp by the timeout duration.
    4.  **Exit Loop**: If a response is received ('approved'/'rejected') or a timeout occurs, the agent yields an event with `actions=EventActions(escalate=True)`. This terminates the `LoopAgent`.
    5.  **Handle Outcome**: After the loop terminates, the next agent in the sequence can check the final status and proceed with the approved action or the escalation path.
*   **Simplified Approvals**: For simple cases where the user interacting with the agent provides the approval, you can use the `require_confirmation` parameter on a `FunctionTool`. This pauses the tool and waits for user confirmation before proceeding, though it lacks an automatic timeout.

### 4. Proactive Reminder and PIR Workflows

The system can be extended with proactive capabilities using scheduled and event-driven serverless functions.

#### **Scheduled Status Reminders**

A Google Cloud Function can be scheduled to run periodically to send reminders about upcoming changes.

*   **Trigger**: Use **Google Cloud Scheduler** to create a job that runs on a defined cron schedule (e.g., daily).
*   **Target**: Configure the scheduler job to trigger a **Google Cloud Function** via an HTTP request or a Pub/Sub message. Secure the HTTP trigger by requiring authentication and configuring the scheduler to use an OIDC service account with the "Cloud Functions Invoker" role.
*   **Function Logic**: The Python function will contain the logic to query Azure DevOps for relevant CRs and use the Microsoft Graph API to send proactive reminders to the correct users in Teams. Credentials for these services should be managed securely using Google Secret Manager.

#### **Event-Driven PIR Follow-ups**

An Azure DevOps webhook can trigger a Cloud Function in response to specific events, such as a change request being closed.

*   **Webhook Configuration**: In Azure DevOps Project Settings, create a **Service Hook** (webhook). Configure it to trigger on a specific event (e.g., "Work item updated") and to send a POST request to your Google Cloud Function's trigger URL.
*   **Function Logic**: The Cloud Function will receive the event payload from Azure DevOps in the request body. It can then parse this payload to execute logic for Post-Implementation Review (PIR) notifications, reminders, or escalations.
*   **Security Best Practices**:
    *   **Use HTTPS**: Always use the function's HTTPS URL to encrypt data in transit.
    *   **Authentication**:
        *   **Shared Secret**: Pass a shared secret in an HTTP header from Azure DevOps and verify it within your Cloud Function code. Store this secret securely using **Google Secret Manager**.
        *   **API Gateway (Most Secure)**: Place **Google Cloud API Gateway** in front of your function. The gateway can require an API key for access, offloading authentication from your function and keeping the function itself from being publicly accessible.
    *   **Payload Validation**: Always validate the structure and content of the incoming JSON payload to ensure it is well-formed and not malicious.
    *   **Idempotency**: Design your function so that receiving the same webhook multiple times does not cause duplicate actions or errors.

***

### Executive Summary

This report outlines a powerful, code-first methodology for building an automated change management system using Python. The architecture combines a **Microsoft Teams bot** for user interaction, a backend built with **Google's Agent Development Kit (ADK)** for intelligent workflow orchestration, and serverless **Google Cloud Functions** for handling scheduled and event-driven tasks.

Key components of this solution include:
*   **Conversational Front-End**: A Python-based bot in Microsoft Teams that uses the Bot Framework SDK to parse user commands, manage conversation state, and deliver proactive notifications.
*   **Intelligent Backend**: A multi-agent system built with the Google ADK, where a primary orchestrator agent delegates tasks like validating change requests, checking calendars, and seeking human approval to specialized sub-agents.
*   **Event-Driven Workflows**: Google Cloud Functions triggered by Cloud Scheduler and Azure DevOps webhooks to automate proactive reminders and post-implementation review processes.
*   **Secure Integration**: A strong emphasis on security, using Google Secret Manager and Azure Key Vault for credential storage, service accounts and managed identities for controlled access, and best practices for authenticating with both Google Cloud and Microsoft Azure services.