# Power Automate Reminder Flows - Azure DevOps Integration

This folder contains specifications, WIQL queries, and implementation guides for Power Automate flows that send reminders based on Change Request states in Azure DevOps.

## Overview

Three automated reminder flows pull data directly from Azure DevOps REST APIs:

1. **Flow A - Approved State Reminders**
   - Pre-start reminder (20 minutes before Proposed Start Date)
   - Follow-up reminder at Proposed Start Date if still in "Approved" state

2. **Flow B - In Progress State Reminders**
   - Pre-end reminder (20 minutes before Proposed End Date)
   - Inquiry and escalation logic for incomplete work
   - Extension request handling

3. **Flow C - Awaiting PIR State Reminders**
   - Periodic reminders to PIR assignee

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Power Automate Flows                      │
│  (Running under per-user premium license - $15/month)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Every 5-10 minutes
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Azure DevOps REST API (TFS)                     │
│  • WIQL queries (filter by state + date window)             │
│  • wit/workitemsbatch (fetch CR details)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Process results
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Reminder Logic                            │
│  • Check timing conditions                                   │
│  • Verify reminder not already sent                          │
│  • Send notifications (Email/Teams)                          │
│  • Log reminder events                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Reminder Tracking Store                         │
│  (SharePoint List / Dataverse / Azure Table)                │
│  Schema: WorkItemId, ReminderType, Timestamp, Status        │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Licensing
- **Power Automate per-user plan** (~$15 USD/month) for the service account that owns/runs the flows
- Includes all premium connectors (Azure DevOps, Azure AD)

### Permissions
- **Azure DevOps**: PAT with `Work Items (Read)` permission
- **Azure AD**: Permissions to read group members and user hierarchy (for escalations)
- **Email/Teams**: Appropriate mailbox or Teams app permissions

### Required Field Names
Verify these field reference names exist in your TFS instance:
- `Microsoft.VSTS.Scheduling.StartDate` (Proposed Start Date)
- `Microsoft.VSTS.Scheduling.FinishDate` (Proposed End Date)
- `Microsoft.VSTS.Common.ActivatedDate` (Actual Start Date)
- `Microsoft.VSTS.Common.ClosedDate` (Actual End Date)
- `System.State`
- `System.AssignedTo`

Check with: `GET https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis/wit/fields?api-version=7.0`

## Files in This Folder

- `README.md` - This file
- `flow_a_approved_reminders.md` - Detailed spec for Approved state flow
- `flow_b_inprogress_reminders.md` - Detailed spec for In Progress state flow
- `flow_c_awaiting_pir_reminders.md` - Detailed spec for Awaiting PIR state flow
- `wiql_queries.md` - WIQL query templates for each flow
- `reminder_tracking_schema.md` - Schema for tracking sent reminders
- `api_reference.md` - Azure DevOps API endpoints and examples
- `cost_estimate.md` - Cost model and usage projections

## Implementation Steps

1. **Set up reminder tracking store** (SharePoint list or Dataverse table)
2. **Create Azure DevOps connection** in Power Automate with PAT
3. **Create Azure AD connection** for group/hierarchy lookups
4. **Build Flow A** (Approved reminders) - start with this one
5. **Test Flow A** with a small set of test CRs
6. **Build Flow B** (In Progress reminders)
7. **Build Flow C** (Awaiting PIR reminders)
8. **Configure monitoring** (Application Insights or flow analytics)
9. **Deploy to production** with appropriate recurrence intervals

## Operational Considerations

### API Rate Limits
- Azure DevOps: 60 requests/minute per PAT
- Batch WIQL results (200 IDs per call)
- Stagger flow recurrence to avoid simultaneous API hits

### Error Handling
- Retry logic for 429 (rate limit) and 5xx errors
- Exponential backoff (1s, 2s, 4s)
- Alert on persistent failures

### Monitoring
- Track reminder success/failure rates
- Monitor API call volume
- Alert on escalations
- Audit log for compliance

## Cost Estimate Summary

Based on typical usage:
- **25,076 total CRs** in system
- **~500 active CRs** (Approved, In Progress, Awaiting PIR)
- **Flow runs every 10 minutes** = 144 runs/day per flow
- **3 flows** = 432 runs/day = ~13,000 runs/month

**Monthly cost**: $15 per-user license (includes unlimited runs with premium connectors)