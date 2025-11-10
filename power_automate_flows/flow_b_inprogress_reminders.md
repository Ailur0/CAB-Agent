# Flow B - In Progress State Reminders

## Overview

Handles reminders and escalations for Change Requests in "In Progress" state:
1. **Pre-end reminder**: 20 minutes before Proposed End Date
2. **Completion inquiry**: At Proposed End Date if results not filled
3. **Extension handling**: Monitor extended deadlines within maintenance window
4. **Escalation**: Alert manager/director if work incomplete after deadline

## Flow Configuration

### Basic Settings
- **Name**: `CR Reminders - In Progress State`
- **Trigger**: Recurrence
- **Frequency**: Every 10 minutes
- **Owner**: Service account with Power Automate per-user license
- **Run Mode**: Automated

### Connections Required
- Azure DevOps (TFS)
- SharePoint (for reminder tracking)
- Office 365 Outlook (for email)
- Azure AD (for manager hierarchy lookup)

---

## Flow Steps

### 1. Trigger: Recurrence
- **Interval**: 10
- **Frequency**: Minute
- **Time zone**: (UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi

---

### 2. Initialize Variables

#### Variable: CurrentTime
- **Name**: `CurrentTime`
- **Type**: String
- **Value**: `@{utcNow()}`

#### Variable: PreEndWindow
- **Name**: `PreEndWindow`
- **Type**: String
- **Value**: `@{addMinutes(utcNow(), 30)}`

#### Variable: MaintenanceWindowEnd
- **Name**: `MaintenanceWindowEnd`
- **Type**: String
- **Value**: Configure based on your maintenance window (e.g., `@{addHours(utcNow(), 4)}`)

---

### 3. Query Azure DevOps - Pre-End Candidates

**Action**: Send an HTTP request to Azure DevOps
- **Organization Name**: `Realpage`
- **URI**: `Change_Management/_apis/wit/wiql?api-version=7.0`
- **Method**: POST
- **Body**:
```json
{
  "query": "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] IN ('Normal Change Request', 'Emergency Change Request', 'Standard Change Request', 'Informational Change Request', 'Child Change Request') AND [System.State] = 'In Progress' AND [Microsoft.VSTS.Scheduling.FinishDate] >= @Today AND [Microsoft.VSTS.Scheduling.FinishDate] <= @Today + 0.02083 ORDER BY [Microsoft.VSTS.Scheduling.FinishDate] ASC"
}
```

**Parse JSON**:
- **Content**: `@{body('Send_an_HTTP_request_to_Azure_DevOps')}`
- **Schema**: (Same as Flow A)

---

### 4. Condition: Check if Results Found

**Condition**: `length(body('Parse_JSON')?['workItems']) is greater than 0`

#### If yes:

---

### 5. Extract Work Item IDs & Fetch Details

**Action**: Select
- **From**: `@{body('Parse_JSON')?['workItems']}`
- **Map**: `@{item()?['id']}`

**Action**: Send an HTTP request to Azure DevOps (Batch)
- **URI**: `_apis/wit/workitemsbatch?api-version=7.0`
- **Method**: POST
- **Body**:
```json
{
  "ids": @{body('Select')},
  "fields": [
    "System.Id",
    "System.Title",
    "System.State",
    "System.AssignedTo",
    "System.CreatedBy",
    "Microsoft.VSTS.Scheduling.StartDate",
    "Microsoft.VSTS.Scheduling.FinishDate",
    "Microsoft.VSTS.Common.ActivatedDate",
    "Microsoft.VSTS.Common.ClosedDate"
  ]
}
```

**Parse JSON**: (Batch response schema)

---

### 6. Apply to Each Work Item

**Action**: Apply to each
- **Select output**: `@{body('Parse_JSON_2')?['value']}`

---

### 7. Calculate Time Until End

**Action**: Compose
- **Name**: `MinutesUntilEnd`
- **Inputs**: 
```
@{div(sub(ticks(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.FinishDate']), ticks(utcNow())), 600000000)}
```

---

### 8. Branch: Pre-End Reminder vs. At-End Check

**Condition**: `@{outputs('MinutesUntilEnd')}`

#### Branch A: Pre-End Reminder (15-25 minutes before)

**Condition**: 
```
@{and(
  greater(outputs('MinutesUntilEnd'), 15),
  less(outputs('MinutesUntilEnd'), 25)
)}
```

##### If yes:

---

### 9. Check if Pre-End Reminder Already Sent

**Action**: Get items (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Filter Query**: 
```
WorkItemId eq @{items('Apply_to_each')?['id']} and ReminderType eq 'InProgress-PreEnd' and Status eq 'Sent'
```

**Condition**: `length(body('Get_items')?['value']) equals 0`

##### If not sent:

---

### 10. Send Pre-End Reminder Email

**Action**: Send an email (V2)
- **To**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
- **Subject**: `🔔 Reminder: CR@{items('Apply_to_each')?['id']} ends in 20 minutes`
- **Body**:
```html
<html>
<body style="font-family: Segoe UI, Arial, sans-serif;">
  <div style="background-color: #107C10; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
    <h2 style="margin: 0;">⏰ Change Request Ending Soon</h2>
  </div>
  
  <div style="padding: 20px; border: 1px solid #E1E1E1; border-top: none; border-radius: 0 0 5px 5px;">
    <p><strong>CR Number:</strong> CR@{items('Apply_to_each')?['id']}</p>
    <p><strong>Title:</strong> @{items('Apply_to_each')?['fields']?['System.Title']}</p>
    <p><strong>State:</strong> <span style="background-color: #D4EDDA; padding: 3px 8px; border-radius: 3px;">@{items('Apply_to_each')?['fields']?['System.State']}</span></p>
    <p><strong>Proposed End:</strong> @{formatDateTime(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.FinishDate'], 'dd MMM yyyy hh:mm tt')}</p>
    <p><strong>Assigned To:</strong> @{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}</p>
    
    <div style="background-color: #FFF4CE; padding: 15px; border-left: 4px solid #FFB900; margin: 20px 0;">
      <p style="margin: 0;"><strong>⚠️ Action Required:</strong></p>
      <p style="margin: 5px 0 0 0;">Your change request is scheduled to end in approximately <strong>20 minutes</strong>. Please prepare to complete and document your work.</p>
    </div>
    
    <h3 style="color: #107C10;">Before Completion:</h3>
    <ol>
      <li>Verify all changes have been implemented successfully</li>
      <li>Complete testing and validation</li>
      <li>Document results and any issues encountered</li>
      <li>Update the CR with completion details</li>
      <li>Transition to appropriate next state</li>
    </ol>
    
    <div style="background-color: #F3F2F1; padding: 15px; border-radius: 3px; margin: 20px 0;">
      <p style="margin: 0;"><strong>Need More Time?</strong></p>
      <p style="margin: 5px 0 0 0;">If you require an extension within the maintenance window, please update the CR with the new end time and reason.</p>
    </div>
    
    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      <p style="margin: 0;"><a href="https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/@{items('Apply_to_each')?['id']}" style="background-color: #107C10; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block;">View CR in Azure DevOps</a></p>
    </div>
    
    <p style="color: #666; font-size: 12px; margin-top: 20px;">This is an automated reminder from the CAB Agent system.</p>
  </div>
</body>
</html>
```

---

### 11. Log Pre-End Reminder

**Action**: Create item (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Fields**:
  - **WorkItemId**: `@{items('Apply_to_each')?['id']}`
  - **CRNumber**: `CR@{items('Apply_to_each')?['id']}`
  - **ReminderType**: `InProgress-PreEnd`
  - **State**: `In Progress`
  - **SentTimestamp**: `@{utcNow()}`
  - **RecipientEmail**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
  - **RecipientName**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}`
  - **ProposedEndDate**: `@{items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.FinishDate']}`
  - **Status**: `Sent`
  - **FlowRunId**: `@{workflow()?['run']?['name']}`

---

#### Branch B: At-End Inquiry (within 5 minutes of end time)

**Condition**: 
```
@{and(
  greater(outputs('MinutesUntilEnd'), -5),
  less(outputs('MinutesUntilEnd'), 5)
)}
```

##### If yes:

---

### 12. Check if Work is Complete

**Condition**: Check if results are filled
```
@{or(
  not(empty(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Common.ClosedDate'])),
  equals(items('Apply_to_each')?['fields']?['System.State'], 'Closed'),
  equals(items('Apply_to_each')?['fields']?['System.State'], 'Completed')
)}
```

##### If no (work incomplete):

---

### 13. Check if At-End Inquiry Already Sent

**Action**: Get items (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Filter Query**: 
```
WorkItemId eq @{items('Apply_to_each')?['id']} and ReminderType eq 'InProgress-AtEnd' and Status eq 'Sent'
```

**Condition**: `length(body('Get_items_2')?['value']) equals 0`

##### If not sent:

---

### 14. Send Completion Inquiry Email

**Action**: Send an email (V2)
- **To**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
- **Subject**: `⚠️ URGENT: CR@{items('Apply_to_each')?['id']} - Status Update Required`
- **Body**:
```html
<html>
<body style="font-family: Segoe UI, Arial, sans-serif;">
  <div style="background-color: #D13438; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
    <h2 style="margin: 0;">⚠️ Change Request Status Update Required</h2>
  </div>
  
  <div style="padding: 20px; border: 1px solid #E1E1E1; border-top: none; border-radius: 0 0 5px 5px;">
    <p><strong>CR Number:</strong> CR@{items('Apply_to_each')?['id']}</p>
    <p><strong>Title:</strong> @{items('Apply_to_each')?['fields']?['System.Title']}</p>
    <p><strong>Proposed End:</strong> @{formatDateTime(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.FinishDate'], 'dd MMM yyyy hh:mm tt')}</p>
    <p><strong>Current State:</strong> <span style="background-color: #D4EDDA; padding: 3px 8px; border-radius: 3px;">In Progress</span></p>
    
    <div style="background-color: #F8D7DA; padding: 15px; border-left: 4px solid #D13438; margin: 20px 0;">
      <p style="margin: 0;"><strong>🚨 IMMEDIATE ACTION REQUIRED</strong></p>
      <p style="margin: 5px 0 0 0;">The scheduled end time for this CR has arrived, but results have not been documented. Please respond immediately with a status update.</p>
    </div>
    
    <h3 style="color: #D13438;">Required Information:</h3>
    <ol>
      <li><strong>Current Status:</strong> Is the work complete?</li>
      <li><strong>Delay Reason:</strong> If incomplete, what is causing the delay?</li>
      <li><strong>Extension Needed:</strong> Do you need additional time?</li>
      <li><strong>New End Time:</strong> If extension needed, when will work be complete?</li>
      <li><strong>Risks/Issues:</strong> Any problems or concerns?</li>
    </ol>
    
    <div style="background-color: #FFF4CE; padding: 15px; border-radius: 3px; margin: 20px 0;">
      <p style="margin: 0;"><strong>📋 Next Steps:</strong></p>
      <ul style="margin: 5px 0 0 0;">
        <li>Reply to this email with status update</li>
        <li>Update the CR in Azure DevOps with results</li>
        <li>If extension needed, ensure it's within the maintenance window</li>
      </ul>
    </div>
    
    <div style="background-color: #F3F2F1; padding: 15px; border-radius: 3px; margin: 20px 0;">
      <p style="margin: 0; color: #A4262C;"><strong>⚠️ Important:</strong></p>
      <p style="margin: 5px 0 0 0;">If no response is received within 15 minutes, this issue will be escalated to your manager for immediate attention.</p>
    </div>
    
    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      <p style="margin: 0;">
        <a href="https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/@{items('Apply_to_each')?['id']}" style="background-color: #D13438; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block; margin-right: 10px;">View CR in Azure DevOps</a>
        <a href="mailto:cab@realpage.com?subject=CR@{items('Apply_to_each')?['id']} Status Update" style="background-color: #0078D4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block;">Reply with Status</a>
      </p>
    </div>
    
    <p style="color: #666; font-size: 12px; margin-top: 20px;">This is an automated inquiry from the CAB Agent system. Immediate response required.</p>
  </div>
</body>
</html>
```
- **Importance**: High

---

### 15. Log At-End Inquiry

**Action**: Create item (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Fields**:
  - **WorkItemId**: `@{items('Apply_to_each')?['id']}`
  - **CRNumber**: `CR@{items('Apply_to_each')?['id']}`
  - **ReminderType**: `InProgress-AtEnd`
  - **State**: `In Progress`
  - **SentTimestamp**: `@{utcNow()}`
  - **RecipientEmail**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
  - **RecipientName**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}`
  - **ProposedEndDate**: `@{items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.FinishDate']}`
  - **Status**: `Sent`
  - **Notes**: `Awaiting response - escalation scheduled if no update within 15 minutes`
  - **FlowRunId**: `@{workflow()?['run']?['name']}`

---

## Extension Handling Logic

### 16. Check for Extension Requests

**Action**: Get items (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Filter Query**: 
```
WorkItemId eq @{items('Apply_to_each')?['id']} and ReminderType eq 'InProgress-AtEnd' and ExtensionRequested eq true and Status eq 'Sent'
```

**Condition**: `length(body('Get_items_3')?['value']) is greater than 0`

##### If extension requested:

---

### 17. Validate Extension Within Maintenance Window

**Action**: Compose
- **Name**: `ExtendedEndDate`
- **Inputs**: `@{body('Get_items_3')?['value'][0]?['ExtendedEndDate']}`

**Condition**: Check if extended end is within maintenance window
```
@{less(ticks(outputs('ExtendedEndDate')), ticks(variables('MaintenanceWindowEnd')))}
```

##### If within window:

---

### 18. Monitor Extended Deadline

**Action**: Delay until (or schedule separate flow run)
- **Timestamp**: `@{outputs('ExtendedEndDate')}`

**After delay, check completion again** (repeat steps 12-15 with extended deadline)

---

##### If outside window or no extension:

---

## Escalation Logic

### 19. Check if Escalation Time Reached

**Action**: Get items (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Filter Query**: 
```
WorkItemId eq @{items('Apply_to_each')?['id']} and ReminderType eq 'InProgress-AtEnd' and Status eq 'Sent'
```

**Condition**: Check if 15+ minutes since inquiry
```
@{greater(
  div(sub(ticks(utcNow()), ticks(body('Get_items_4')?['value'][0]?['SentTimestamp'])), 600000000),
  15
)}
```

##### If yes (escalation needed):

---

### 20. Get Manager from Azure AD

**Action**: Get manager (V2) - Azure AD
- **User (UPN)**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`

**Parse JSON** (manager response):
- **Content**: `@{body('Get_manager_(V2)')}`
- **Schema**:
```json
{
  "type": "object",
  "properties": {
    "displayName": {"type": "string"},
    "mail": {"type": "string"},
    "userPrincipalName": {"type": "string"}
  }
}
```

---

### 21. Send Escalation Email to Manager

**Action**: Send an email (V2)
- **To**: `@{body('Parse_JSON_Manager')?['mail']}`
- **Cc**: `cab@realpage.com`
- **Subject**: `🚨 ESCALATION: CR@{items('Apply_to_each')?['id']} - Incomplete and Overdue`
- **Body**:
```html
<html>
<body style="font-family: Segoe UI, Arial, sans-serif;">
  <div style="background-color: #A4262C; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
    <h2 style="margin: 0;">🚨 ESCALATION: Change Request Overdue</h2>
  </div>
  
  <div style="padding: 20px; border: 1px solid #E1E1E1; border-top: none; border-radius: 0 0 5px 5px;">
    <p>Dear @{body('Parse_JSON_Manager')?['displayName']},</p>
    
    <p>This is an automated escalation regarding an overdue Change Request assigned to your team member.</p>
    
    <div style="background-color: #F8D7DA; padding: 15px; border-left: 4px solid #A4262C; margin: 20px 0;">
      <h3 style="margin: 0 0 10px 0; color: #A4262C;">Change Request Details</h3>
      <p style="margin: 5px 0;"><strong>CR Number:</strong> CR@{items('Apply_to_each')?['id']}</p>
      <p style="margin: 5px 0;"><strong>Title:</strong> @{items('Apply_to_each')?['fields']?['System.Title']}</p>
      <p style="margin: 5px 0;"><strong>Assigned To:</strong> @{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']} (@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']})</p>
      <p style="margin: 5px 0;"><strong>Proposed End:</strong> @{formatDateTime(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.FinishDate'], 'dd MMM yyyy hh:mm tt')}</p>
      <p style="margin: 5px 0;"><strong>Current State:</strong> In Progress (Incomplete)</p>
    </div>
    
    <h3 style="color: #A4262C;">Escalation Reason</h3>
    <p>The scheduled end time for this Change Request has passed, and:</p>
    <ul>
      <li>Results have not been documented in Azure DevOps</li>
      <li>No status update has been provided</li>
      <li>No response to completion inquiry sent 15+ minutes ago</li>
    </ul>
    
    <h3 style="color: #A4262C;">Required Actions</h3>
    <ol>
      <li>Contact @{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']} immediately to determine status</li>
      <li>Ensure CR is updated with current status and results</li>
      <li>If work is incomplete, determine:
        <ul>
          <li>Reason for delay</li>
          <li>Estimated completion time</li>
          <li>Any risks or issues</li>
        </ul>
      </li>
      <li>Update the CAB team on resolution</li>
    </ol>
    
    <div style="background-color: #FFF4CE; padding: 15px; border-radius: 3px; margin: 20px 0;">
      <p style="margin: 0;"><strong>⚠️ Impact:</strong></p>
      <p style="margin: 5px 0 0 0;">Overdue change requests may impact production systems and violate change management policies. Immediate attention is required.</p>
    </div>
    
    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      <p style="margin: 0;">
        <a href="https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/@{items('Apply_to_each')?['id']}" style="background-color: #A4262C; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block;">View CR in Azure DevOps</a>
      </p>
    </div>
    
    <p style="margin-top: 20px;">Please acknowledge receipt of this escalation and provide an update within 30 minutes.</p>
    
    <p>Thank you,<br>CAB Agent Automated System</p>
    
    <p style="color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      This is an automated escalation. For questions about the CAB process, contact the Change Management team at cab@realpage.com.
    </p>
  </div>
</body>
</html>
```
- **Importance**: High

---

### 22. Log Escalation

**Action**: Update item (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Id**: `@{body('Get_items_4')?['value'][0]?['ID']}`
- **Fields**:
  - **EscalationSent**: `true`
  - **EscalationRecipient**: `@{body('Parse_JSON_Manager')?['mail']}`
  - **Notes**: `Escalated to manager due to no response after 15 minutes`
  - **ModifiedDate**: `@{utcNow()}`

---

## Error Handling

Wrap all email/notification actions in **Scope** blocks with error handlers:

**Action**: Scope (for each major action group)

**Action**: Configure run after
- **Run after**: Scope has failed or timed out

**Action**: Create item (SharePoint) - Log failure
- Log error details to `CR_ReminderLog` with Status = `Failed`

---

## Testing

### Test Scenarios

1. **Pre-end reminder**: CR 20 min before end
2. **At-end inquiry**: CR at end time, incomplete
3. **Extension request**: User requests extension within window
4. **Extension monitoring**: Check completion at extended time
5. **Escalation**: No response 15 min after inquiry
6. **Manager lookup failure**: Invalid user or no manager
7. **Work completed**: CR closed before end time (skip reminders)

### Test Data

Create test CRs with:
- State: In Progress
- Proposed End Date: 25 minutes from now
- Leave results blank
- Assigned to test account with valid manager

---

## Monitoring

### Key Metrics
- Pre-end reminders sent
- At-end inquiries sent
- Extension requests received
- Escalations triggered
- Average time to completion after inquiry
- Manager response time

### Alerts
- Escalation rate > 5%
- Multiple escalations for same user
- Manager lookup failures
- Email delivery failures

---

## Maintenance

### Daily
- Review escalations
- Check extension requests
- Verify manager hierarchy accuracy

### Weekly
- Analyze completion patterns
- Review escalation effectiveness
- Update email templates if needed

### Monthly
- Audit extension approvals
- Review maintenance window boundaries
- Optimize timing thresholds
