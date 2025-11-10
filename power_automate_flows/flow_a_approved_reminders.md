# Flow A - Approved State Reminders

## Overview

Sends reminders for Change Requests in "Approved" state:
1. **Pre-start reminder**: 20 minutes before Proposed Start Date
2. **Follow-up reminder**: At Proposed Start Date if still in "Approved" state

## Flow Configuration

### Basic Settings
- **Name**: `CR Reminders - Approved State`
- **Trigger**: Recurrence
- **Frequency**: Every 10 minutes
- **Owner**: Service account with Power Automate per-user license
- **Run Mode**: Automated

### Connections Required
- Azure DevOps (TFS)
- SharePoint (for reminder tracking)
- Office 365 Outlook (for email) or Teams (for chat messages)
- Azure AD (optional, for group notifications)

---

## Flow Steps

### 1. Trigger: Recurrence
- **Interval**: 10
- **Frequency**: Minute
- **Time zone**: (UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi
- **Start time**: (Leave default or set to business hours start)

---

### 2. Initialize Variables

#### Variable: CurrentTime
- **Name**: `CurrentTime`
- **Type**: String
- **Value**: `@{utcNow()}`

#### Variable: PreStartWindow
- **Name**: `PreStartWindow`
- **Type**: String
- **Value**: `@{addMinutes(utcNow(), 30)}`
- **Purpose**: 30-minute window for WIQL query

#### Variable: AtStartWindow
- **Name**: `AtStartWindow`
- **Type**: String
- **Value**: `@{addMinutes(utcNow(), 5)}`
- **Purpose**: 5-minute window for follow-up check

---

### 3. Query Azure DevOps - Pre-Start Candidates

**Action**: Send an HTTP request to Azure DevOps
- **Organization Name**: `Realpage`
- **URI**: `Change_Management/_apis/wit/wiql?api-version=7.0`
- **Method**: POST
- **Body**:
```json
{
  "query": "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] IN ('Normal Change Request', 'Emergency Change Request', 'Standard Change Request', 'Informational Change Request', 'Child Change Request') AND [System.State] = 'Approved' AND [Microsoft.VSTS.Scheduling.StartDate] >= @Today AND [Microsoft.VSTS.Scheduling.StartDate] <= @Today + 0.02083 ORDER BY [Microsoft.VSTS.Scheduling.StartDate] ASC"
}
```

**Parse JSON** (output of HTTP request):
- **Content**: `@{body('Send_an_HTTP_request_to_Azure_DevOps')}`
- **Schema**:
```json
{
  "type": "object",
  "properties": {
    "queryType": {"type": "string"},
    "queryResultType": {"type": "string"},
    "asOf": {"type": "string"},
    "workItems": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "url": {"type": "string"}
        }
      }
    }
  }
}
```

---

### 4. Condition: Check if Results Found

**Condition**: `length(body('Parse_JSON')?['workItems']) is greater than 0`

#### If yes (results found):

---

### 5. Extract Work Item IDs

**Action**: Select
- **From**: `@{body('Parse_JSON')?['workItems']}`
- **Map**: `@{item()?['id']}`
- **Output**: Array of IDs

---

### 6. Fetch Full Work Item Details

**Action**: Send an HTTP request to Azure DevOps
- **Organization Name**: `Realpage`
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
    "Microsoft.VSTS.Scheduling.FinishDate"
  ]
}
```

**Parse JSON** (batch response):
- **Content**: `@{body('Send_an_HTTP_request_to_Azure_DevOps_2')}`
- **Schema**:
```json
{
  "type": "object",
  "properties": {
    "count": {"type": "integer"},
    "value": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "integer"},
          "fields": {
            "type": "object",
            "properties": {
              "System.Id": {"type": "integer"},
              "System.Title": {"type": "string"},
              "System.State": {"type": "string"},
              "System.AssignedTo": {
                "type": "object",
                "properties": {
                  "displayName": {"type": "string"},
                  "uniqueName": {"type": "string"}
                }
              },
              "Microsoft.VSTS.Scheduling.StartDate": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

---

### 7. Apply to Each Work Item

**Action**: Apply to each
- **Select output from previous steps**: `@{body('Parse_JSON_2')?['value']}`

#### Inside the loop:

---

### 8. Calculate Time Until Start

**Action**: Compose
- **Name**: `MinutesUntilStart`
- **Inputs**: 
```
@{div(sub(ticks(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.StartDate']), ticks(utcNow())), 600000000)}
```
**Note**: This calculates minutes between now and start date

---

### 9. Condition: Check Reminder Timing

**Condition**: 
```
@{and(
  greater(outputs('MinutesUntilStart'), 15),
  less(outputs('MinutesUntilStart'), 25)
)}
```
**Logic**: Between 15-25 minutes before start (allows for 10-minute flow interval)

#### If yes (in reminder window):

---

### 10. Check if Reminder Already Sent

**Action**: Get items (SharePoint)
- **Site Address**: Your SharePoint site URL
- **List Name**: `CR_ReminderLog`
- **Filter Query**: 
```
WorkItemId eq @{items('Apply_to_each')?['id']} and ReminderType eq 'Approved-PreStart' and Status eq 'Sent'
```
- **Top Count**: 1

---

### 11. Condition: Reminder Not Sent Before

**Condition**: `length(body('Get_items')?['value']) equals 0`

#### If yes (not sent before):

---

### 12. Send Pre-Start Reminder Email

**Action**: Send an email (V2) - Office 365 Outlook
- **To**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
- **Subject**: `🔔 Reminder: CR@{items('Apply_to_each')?['id']} starts in 20 minutes`
- **Body**:
```html
<html>
<body style="font-family: Segoe UI, Arial, sans-serif;">
  <div style="background-color: #0078D4; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
    <h2 style="margin: 0;">⏰ Change Request Starting Soon</h2>
  </div>
  
  <div style="padding: 20px; border: 1px solid #E1E1E1; border-top: none; border-radius: 0 0 5px 5px;">
    <p><strong>CR Number:</strong> CR@{items('Apply_to_each')?['id']}</p>
    <p><strong>Title:</strong> @{items('Apply_to_each')?['fields']?['System.Title']}</p>
    <p><strong>State:</strong> <span style="background-color: #FFF4CE; padding: 3px 8px; border-radius: 3px;">@{items('Apply_to_each')?['fields']?['System.State']}</span></p>
    <p><strong>Proposed Start:</strong> @{formatDateTime(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.StartDate'], 'dd MMM yyyy hh:mm tt')}</p>
    <p><strong>Assigned To:</strong> @{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}</p>
    
    <div style="background-color: #FFF4CE; padding: 15px; border-left: 4px solid #FFB900; margin: 20px 0;">
      <p style="margin: 0;"><strong>⚠️ Action Required:</strong></p>
      <p style="margin: 5px 0 0 0;">Your change request is scheduled to start in approximately <strong>20 minutes</strong>. Please ensure you are ready to begin implementation.</p>
    </div>
    
    <h3 style="color: #0078D4;">Next Steps:</h3>
    <ol>
      <li>Review the change implementation plan</li>
      <li>Ensure all prerequisites are met</li>
      <li>Update the CR state to "In Progress" when you begin</li>
      <li>Document any issues or deviations</li>
    </ol>
    
    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      <p style="margin: 0;"><a href="https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/@{items('Apply_to_each')?['id']}" style="background-color: #0078D4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block;">View CR in Azure DevOps</a></p>
    </div>
    
    <p style="color: #666; font-size: 12px; margin-top: 20px;">This is an automated reminder from the CAB Agent system. If you have questions, contact the Change Management team.</p>
  </div>
</body>
</html>
```
- **Importance**: High

**Optional**: Send Teams message instead/additionally
**Action**: Post message in a chat or channel (Teams)
- **Recipient**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
- **Message**:
```
🔔 **Change Request Starting Soon**

**CR Number:** CR@{items('Apply_to_each')?['id']}
**Title:** @{items('Apply_to_each')?['fields']?['System.Title']}
**Proposed Start:** @{formatDateTime(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.StartDate'], 'dd MMM yyyy hh:mm tt')}

⚠️ Your CR starts in **20 minutes**. Please be ready to begin implementation.

[View in Azure DevOps](https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/@{items('Apply_to_each')?['id']})
```

---

### 13. Log Reminder Sent

**Action**: Create item (SharePoint)
- **Site Address**: Your SharePoint site URL
- **List Name**: `CR_ReminderLog`
- **Fields**:
  - **WorkItemId**: `@{items('Apply_to_each')?['id']}`
  - **CRNumber**: `CR@{items('Apply_to_each')?['id']}`
  - **ReminderType**: `Approved-PreStart`
  - **State**: `@{items('Apply_to_each')?['fields']?['System.State']}`
  - **SentTimestamp**: `@{utcNow()}`
  - **RecipientEmail**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
  - **RecipientName**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}`
  - **ProposedStartDate**: `@{items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.StartDate']}`
  - **Status**: `Sent`
  - **FlowRunId**: `@{workflow()?['run']?['name']}`

---

### 14. Error Handling (Scope)

Wrap steps 12-13 in a **Scope** action, then add:

**Action**: Configure run after (on Scope)
- **Run after**: has failed or has timed out

**Action**: Create item (SharePoint) - Log failure
- **Site Address**: Your SharePoint site URL
- **List Name**: `CR_ReminderLog`
- **Fields**:
  - **WorkItemId**: `@{items('Apply_to_each')?['id']}`
  - **CRNumber**: `CR@{items('Apply_to_each')?['id']}`
  - **ReminderType**: `Approved-PreStart`
  - **State**: `@{items('Apply_to_each')?['fields']?['System.State']}`
  - **SentTimestamp**: `@{utcNow()}`
  - **RecipientEmail**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
  - **Status**: `Failed`
  - **ErrorMessage**: `@{body('Send_an_email_(V2)')?['error']?['message']}`
  - **FlowRunId**: `@{workflow()?['run']?['name']}`

---

## Follow-Up Reminder Logic

Add a **parallel branch** to the main flow (after step 6) to handle follow-up reminders:

### 15. Filter for At-Start Window

**Action**: Filter array
- **From**: `@{body('Parse_JSON_2')?['value']}`
- **Condition**: 
```
@{and(
  equals(item()?['fields']?['System.State'], 'Approved'),
  less(abs(sub(ticks(item()?['fields']?['Microsoft.VSTS.Scheduling.StartDate']), ticks(utcNow()))), 3000000000)
)}
```
**Logic**: State still "Approved" AND within 5 minutes of start time

### 16. Apply to Each (Follow-up)

Loop through filtered items and repeat steps 10-14, but:
- Change **ReminderType** to `Approved-AtStart`
- Change email subject to: `⚠️ URGENT: CR@{items('Apply_to_each')?['id']} should have started`
- Update email body to emphasize urgency and request immediate action

---

## Testing

### Test Scenarios

1. **Happy path**: CR in Approved state, 20 minutes before start
   - Expected: Email sent, logged in SharePoint
   
2. **Already sent**: Same CR, reminder already in log
   - Expected: Skip sending, no duplicate
   
3. **State changed**: CR moved to "In Progress" before reminder
   - Expected: No reminder (filtered out by WIQL)
   
4. **Email failure**: Invalid recipient email
   - Expected: Logged as Failed with error message
   
5. **Follow-up**: CR still Approved at start time
   - Expected: Second reminder sent

### Test Data

Create test CRs with:
- State: Approved
- Proposed Start Date: 25 minutes from now
- Assigned To: Your test account

Run flow manually and verify:
- WIQL returns the test CR
- Email received
- SharePoint log entry created
- No duplicates on subsequent runs

---

## Monitoring

### Key Metrics
- Reminders sent per day
- Failed deliveries
- Average time between reminder and state change
- CRs requiring follow-up (still Approved at start time)

### Alerts
- Email failures > 5% of attempts
- Follow-up reminders > 10% of pre-start reminders
- Flow run failures

### Optimization
- Adjust recurrence interval based on volume (5-15 minutes)
- Tune time windows if too many/few reminders
- Consider batching notifications for same assignee

---

## Maintenance

### Weekly
- Review failed reminders
- Check for orphaned log entries
- Verify connection health

### Monthly
- Archive old log entries (>90 days)
- Review and optimize WIQL queries
- Update email templates if needed

### Quarterly
- Review metrics and adjust thresholds
- Update documentation
- Test disaster recovery (recreate flow from scratch)
