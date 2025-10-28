# Implementation Plan

## Phase 1: ADK Backend Orchestration

**1. Orchestrator Agent Design**
- Create main OrchestratorAgent using LlmAgent or WorkflowAgent
- Design sub-agents: ValidateCrAgent, CheckCalendarAgent, ApprovalAgent
- Configure Gemini model (gemini-1.5-flash or pro)
- Test agent hierarchy with ADK CLI

**2. Agent Tools Development**
- Azure DevOps Tool: Create, update, query change requests
- Calendar Tool: Check Microsoft Graph calendar for conflicts
- Notification Tool: Trigger Teams bot proactive messages
- Validation Tool: Verify CR details and compliance

**3. Human-in-the-Loop Approval**
- Create approval request tool (sends to Teams, stores request ID)
- Implement LoopAgent with polling mechanism
- Add timeout logic and escalation path
- Test approval flow with both approval and timeout scenarios

## Phase 2: Proactive & Event-Driven Features

**4. Scheduled Reminders**
- Create Google Cloud Function for status reminders
- Query Azure DevOps for upcoming CRs
- Configure Google Cloud Scheduler with cron schedule

**5. Event-Driven PIR Workflows**
- Create Google Cloud Function for webhook handling
- Configure Azure DevOps Service Hook for CR closure events
- Implement payload parsing and PIR notification logic
- Set up API Gateway with API key authentication

## Phase 3: Security & Production

**6. Security Hardening**
- Migrate all secrets to Google Secret Manager and Azure Key Vault
- Implement managed identities for Azure resources
- Add payload validation, sanitization, and rate limiting
- Configure API Gateway and enable HTTPS for all endpoints

**7. Testing & Deployment**
- Write unit tests for tools and agents
- Integration tests for Teams bot workflows
- End-to-end test: CR creation → approval → notification → PIR
- Deploy bot to Azure App Service and Cloud Functions to Google Cloud
- Monitor logs and set up alerting

## Key Dependencies

**Required Accounts:**
- Google Cloud account (Gemini API key)
- Microsoft 365 developer account
- Azure subscription

**Critical Integrations:**
- Azure DevOps API
- Microsoft Graph API
- Google Cloud Scheduler
- Azure Bot Service