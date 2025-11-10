# Flow C - Awaiting PIR State Reminders

## Overview

Sends periodic reminders to complete Post-Implementation Review (PIR) for Change Requests in "Awaiting PIR" state.

**Key Characteristics:**
- No time-based deadline (no ETA)
- Periodic reminders until PIR completed
- Formal tone emphasizing compliance requirement
- Escalation after multiple missed reminders

## Flow Configuration

### Basic Settings
- **Name**: `CR Reminders - Awaiting PIR State`
- **Trigger**: Recurrence
- **Frequency**: Every 4 hours (or daily, based on policy)
- **Owner**: Service account with Power Automate per-user license
- **Run Mode**: Automated

### Connections Required
- Azure DevOps (TFS)
- SharePoint (for reminder tracking)
- Office 365 Outlook (for email)
- Azure AD (optional, for escalation)

---

## Flow Steps

### 1. Trigger: Recurrence
- **Interval**: 4 (or 24 for daily)
- **Frequency**: Hour (or Day)
- **Time zone**: (UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi
- **At these hours**: 8, 12, 16, 20 (for 4-hour interval)
- **At these minutes**: 0

**Note**: Adjust frequency based on PIR completion SLA and volume

---

### 2. Initialize Variables

#### Variable: CurrentTime
- **Name**: `CurrentTime`
- **Type**: String
- **Value**: `@{utcNow()}`

#### Variable: ReminderThreshold
- **Name**: `ReminderThreshold`
- **Type**: Integer
- **Value**: `4`
- **Purpose**: Hours since last reminder before sending new one

#### Variable: EscalationThreshold
- **Name**: `EscalationThreshold`
- **Type**: Integer
- **Value**: `3`
- **Purpose**: Number of reminders before escalation

---

### 3. Query Azure DevOps - All Awaiting PIR Items

**Action**: Send an HTTP request to Azure DevOps
- **Organization Name**: `Realpage`
- **URI**: `Change_Management/_apis/wit/wiql?api-version=7.0`
- **Method**: POST
- **Body**:
```json
{
  "query": "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.CreatedDate], [Microsoft.VSTS.Common.ClosedDate] FROM WorkItems WHERE [System.WorkItemType] IN ('Normal Change Request', 'Emergency Change Request', 'Standard Change Request', 'Informational Change Request', 'Child Change Request') AND [System.State] = 'Awaiting PIR' ORDER BY [System.CreatedDate] ASC"
}
```

**Parse JSON**:
- **Content**: `@{body('Send_an_HTTP_request_to_Azure_DevOps')}`
- **Schema**: (Standard WIQL response)

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
    "System.CreatedDate",
    "Microsoft.VSTS.Common.ClosedDate",
    "Microsoft.VSTS.Scheduling.FinishDate"
  ]
}
```

**Parse JSON**: (Batch response)

---

### 6. Apply to Each Work Item

**Action**: Apply to each
- **Select output**: `@{body('Parse_JSON_2')?['value']}`

---

### 7. Get Previous Reminders for This CR

**Action**: Get items (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Filter Query**: 
```
WorkItemId eq @{items('Apply_to_each')?['id']} and ReminderType eq 'AwaitingPIR-Reminder' and Status eq 'Sent'
```
- **Order By**: SentTimestamp descending
- **Top Count**: 10

---

### 8. Calculate Reminder Count

**Action**: Compose
- **Name**: `ReminderCount`
- **Inputs**: `@{length(body('Get_items')?['value'])}`

---

### 9. Check Last Reminder Time

**Condition**: Should send reminder?

**If reminder count = 0** (never sent):
- Send reminder

**If reminder count > 0**:
- **Action**: Compose
  - **Name**: `HoursSinceLastReminder`
  - **Inputs**: 
  ```
  @{div(sub(ticks(utcNow()), ticks(body('Get_items')?['value'][0]?['SentTimestamp'])), 36000000000)}
  ```

- **Condition**: `@{greater(outputs('HoursSinceLastReminder'), variables('ReminderThreshold'))}`

#### If yes (time to send reminder):

---

### 10. Determine if Escalation Needed

**Condition**: `@{greaterOrEquals(outputs('ReminderCount'), variables('EscalationThreshold'))}`

#### Branch A: Standard Reminder (< 3 reminders)

---

### 11. Send PIR Reminder Email

**Action**: Send an email (V2)
- **To**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
- **Subject**: `📋 Reminder: PIR Required for CR@{items('Apply_to_each')?['id']}`
- **Body**:
```html
<html>
<body style="font-family: Segoe UI, Arial, sans-serif;">
  <div style="background-color: #0078D4; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
    <h2 style="margin: 0;">📋 Post-Implementation Review Required</h2>
  </div>
  
  <div style="padding: 20px; border: 1px solid #E1E1E1; border-top: none; border-radius: 0 0 5px 5px;">
    <p>Hello @{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']},</p>
    
    <p>This is a reminder that a Post-Implementation Review (PIR) is required for the following Change Request:</p>
    
    <div style="background-color: #F3F2F1; padding: 15px; border-radius: 3px; margin: 20px 0;">
      <p style="margin: 5px 0;"><strong>CR Number:</strong> CR@{items('Apply_to_each')?['id']}</p>
      <p style="margin: 5px 0;"><strong>Title:</strong> @{items('Apply_to_each')?['fields']?['System.Title']}</p>
      <p style="margin: 5px 0;"><strong>Completed:</strong> @{formatDateTime(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Common.ClosedDate'], 'dd MMM yyyy hh:mm tt')}</p>
      <p style="margin: 5px 0;"><strong>Current State:</strong> <span style="background-color: #FFF4CE; padding: 3px 8px; border-radius: 3px;">Awaiting PIR</span></p>
      <p style="margin: 5px 0;"><strong>Days Since Completion:</strong> @{div(sub(ticks(utcNow()), ticks(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Common.ClosedDate'])), 864000000000)}</p>
    </div>
    
    <h3 style="color: #0078D4;">What is a PIR?</h3>
    <p>A Post-Implementation Review documents the outcomes of the change and captures lessons learned. It is a required step in the change management process.</p>
    
    <h3 style="color: #0078D4;">Required Information:</h3>
    <ol>
      <li><strong>Success Criteria:</strong> Were the change objectives met?</li>
      <li><strong>Issues Encountered:</strong> Any problems during implementation?</li>
      <li><strong>Lessons Learned:</strong> What went well? What could be improved?</li>
      <li><strong>Follow-up Actions:</strong> Any additional work required?</li>
      <li><strong>Documentation:</strong> Are all changes properly documented?</li>
    </ol>
    
    <div style="background-color: #E1F5FE; padding: 15px; border-left: 4px solid #0078D4; margin: 20px 0;">
      <p style="margin: 0;"><strong>📝 How to Complete:</strong></p>
      <ol style="margin: 5px 0 0 0;">
        <li>Open the CR in Azure DevOps</li>
        <li>Fill in the PIR fields/comments</li>
        <li>Attach any relevant documentation</li>
        <li>Update the state to "Closed" or "Completed"</li>
      </ol>
    </div>
    
    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      <p style="margin: 0;">
        <a href="https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/@{items('Apply_to_each')?['id']}" style="background-color: #0078D4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block;">Complete PIR in Azure DevOps</a>
      </p>
    </div>
    
    <p style="margin-top: 20px;">Thank you for your cooperation in maintaining our change management standards.</p>
    
    <p>Best regards,<br>Change Advisory Board</p>
    
    <p style="color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      This is reminder #@{add(outputs('ReminderCount'), 1)} for this CR. Reminders are sent every @{variables('ReminderThreshold')} hours until the PIR is completed.
    </p>
  </div>
</body>
</html>
```

---

### 12. Log PIR Reminder

**Action**: Create item (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Fields**:
  - **WorkItemId**: `@{items('Apply_to_each')?['id']}`
  - **CRNumber**: `CR@{items('Apply_to_each')?['id']}`
  - **ReminderType**: `AwaitingPIR-Reminder`
  - **State**: `Awaiting PIR`
  - **SentTimestamp**: `@{utcNow()}`
  - **RecipientEmail**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
  - **RecipientName**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}`
  - **Status**: `Sent`
  - **Notes**: `Reminder #@{add(outputs('ReminderCount'), 1)}`
  - **FlowRunId**: `@{workflow()?['run']?['name']}`

---

#### Branch B: Escalation (≥ 3 reminders)

---

### 13. Get Manager from Azure AD

**Action**: Get manager (V2) - Azure AD
- **User (UPN)**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`

**Parse JSON** (manager response)

---

### 14. Send Escalation Email

**Action**: Send an email (V2)
- **To**: `@{body('Parse_JSON_Manager')?['mail']}`
- **Cc**: `cab@realpage.com`, `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
- **Subject**: `⚠️ ESCALATION: PIR Overdue for CR@{items('Apply_to_each')?['id']}`
- **Body**:
```html
<html>
<body style="font-family: Segoe UI, Arial, sans-serif;">
  <div style="background-color: #D13438; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
    <h2 style="margin: 0;">⚠️ ESCALATION: Overdue Post-Implementation Review</h2>
  </div>
  
  <div style="padding: 20px; border: 1px solid #E1E1E1; border-top: none; border-radius: 0 0 5px 5px;">
    <p>Dear @{body('Parse_JSON_Manager')?['displayName']},</p>
    
    <p>This is an escalation regarding an overdue Post-Implementation Review (PIR) for a Change Request assigned to your team member.</p>
    
    <div style="background-color: #F8D7DA; padding: 15px; border-left: 4px solid #D13438; margin: 20px 0;">
      <h3 style="margin: 0 0 10px 0; color: #D13438;">Change Request Details</h3>
      <p style="margin: 5px 0;"><strong>CR Number:</strong> CR@{items('Apply_to_each')?['id']}</p>
      <p style="margin: 5px 0;"><strong>Title:</strong> @{items('Apply_to_each')?['fields']?['System.Title']}</p>
      <p style="margin: 5px 0;"><strong>Assigned To:</strong> @{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}</p>
      <p style="margin: 5px 0;"><strong>Completed:</strong> @{formatDateTime(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Common.ClosedDate'], 'dd MMM yyyy')}</p>
      <p style="margin: 5px 0;"><strong>Days Overdue:</strong> @{div(sub(ticks(utcNow()), ticks(items('Apply_to_each')?['fields']?['Microsoft.VSTS.Common.ClosedDate'])), 864000000000)}</p>
      <p style="margin: 5px 0;"><strong>Reminders Sent:</strong> @{outputs('ReminderCount')}</p>
    </div>
    
    <h3 style="color: #D13438;">Escalation Reason</h3>
    <p>Despite @{outputs('ReminderCount')} previous reminders, the required Post-Implementation Review has not been completed. This is a mandatory step in our change management process and is required for compliance and continuous improvement.</p>
    
    <h3 style="color: #D13438;">Required Actions</h3>
    <ol>
      <li>Contact @{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']} to ensure PIR completion</li>
      <li>Review the change outcomes and document lessons learned</li>
      <li>Complete the PIR in Azure DevOps within 48 hours</li>
      <li>Notify the CAB team once completed</li>
    </ol>
    
    <div style="background-color: #FFF4CE; padding: 15px; border-radius: 3px; margin: 20px 0;">
      <p style="margin: 0;"><strong>⚠️ Impact of Non-Compliance:</strong></p>
      <ul style="margin: 5px 0 0 0;">
        <li>Incomplete change management records</li>
        <li>Lost opportunities for process improvement</li>
        <li>Potential audit findings</li>
        <li>Delayed closure of change tickets</li>
      </ul>
    </div>
    
    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      <p style="margin: 0;">
        <a href="https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/@{items('Apply_to_each')?['id']}" style="background-color: #D13438; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block;">View CR in Azure DevOps</a>
      </p>
    </div>
    
    <p style="margin-top: 20px;">Please acknowledge receipt of this escalation and provide an update on PIR completion status.</p>
    
    <p>Thank you for your immediate attention to this matter.</p>
    
    <p>Regards,<br>Change Advisory Board</p>
    
    <p style="color: #666; font-size: 12px; margin-top: 20px; padding-top: 20px; border-top: 1px solid #E1E1E1;">
      This is an automated escalation after @{outputs('ReminderCount')} unacknowledged reminders. For questions, contact cab@realpage.com.
    </p>
  </div>
</body>
</html>
```
- **Importance**: High

---

### 15. Log Escalation

**Action**: Create item (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Fields**:
  - **WorkItemId**: `@{items('Apply_to_each')?['id']}`
  - **CRNumber**: `CR@{items('Apply_to_each')?['id']}`
  - **ReminderType**: `AwaitingPIR-Reminder`
  - **State**: `Awaiting PIR`
  - **SentTimestamp**: `@{utcNow()}`
  - **RecipientEmail**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
  - **RecipientName**: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}`
  - **Status**: `Sent`
  - **EscalationSent**: `true`
  - **EscalationRecipient**: `@{body('Parse_JSON_Manager')?['mail']}`
  - **Notes**: `Escalated to manager after @{outputs('ReminderCount')} reminders`
  - **FlowRunId**: `@{workflow()?['run']?['name']}`

---

## Error Handling

**Action**: Scope (wrap email actions)

**Action**: Configure run after (on Scope failure)

**Action**: Create item (SharePoint) - Log failure
- Log error with Status = `Failed`

---

## Additional Features

### 16. Optional: Send Summary to CAB Team

Add a parallel branch that runs once per day:

**Action**: Get items (SharePoint)
- **List Name**: `CR_ReminderLog`
- **Filter Query**: 
```
ReminderType eq 'AwaitingPIR-Reminder' and SentTimestamp ge '@{formatDateTime(addDays(utcNow(), -1), 'yyyy-MM-dd')}T00:00:00Z'
```

**Action**: Create HTML table
- **From**: `@{body('Get_items')?['value']}`
- **Columns**: CRNumber, RecipientName, SentTimestamp, Notes

**Action**: Send an email (V2)
- **To**: `cab@realpage.com`
- **Subject**: `Daily PIR Reminder Summary - @{formatDateTime(utcNow(), 'dd MMM yyyy')}`
- **Body**: Include HTML table and summary stats

---

## Testing

### Test Scenarios

1. **First reminder**: CR just entered "Awaiting PIR"
2. **Subsequent reminder**: CR with 1-2 previous reminders
3. **Escalation**: CR with 3+ reminders
4. **Manager lookup failure**: User with no manager
5. **Already completed**: CR moved to "Closed" (should skip)
6. **Timing**: Verify reminders respect threshold hours

### Test Data

Create test CRs with:
- State: Awaiting PIR
- Closed Date: 5-10 days ago
- Assigned to test account with valid manager

---

## Monitoring

### Key Metrics
- Total CRs in "Awaiting PIR" state
- Average time to PIR completion
- Reminder count distribution
- Escalation rate
- PIR completion rate after escalation

### Alerts
- CRs in "Awaiting PIR" > 30 days
- Escalation rate > 20%
- Manager lookup failures
- Email delivery failures

### Reports

**Weekly PIR Status Report**:
- CRs awaiting PIR by age
- Top 10 oldest PIRs
- Completion trend
- Escalation summary

---

## Optimization

### Frequency Tuning

Adjust recurrence based on:
- **High volume** (>50 CRs): Every 4 hours
- **Medium volume** (10-50 CRs): Every 8 hours or twice daily
- **Low volume** (<10 CRs): Once daily

### Reminder Threshold

Adjust hours between reminders:
- **Urgent PIRs**: 4 hours
- **Standard PIRs**: 24 hours
- **Low priority**: 48 hours

### Escalation Threshold

Adjust reminder count before escalation:
- **Strict policy**: 2 reminders
- **Standard policy**: 3 reminders
- **Lenient policy**: 5 reminders

---

## Maintenance

### Weekly
- Review PIR completion rates
- Check escalation effectiveness
- Verify manager hierarchy accuracy

### Monthly
- Analyze PIR completion time trends
- Review and update email templates
- Optimize reminder frequency

### Quarterly
- Audit PIR quality
- Update PIR requirements/fields
- Review escalation policy effectiveness
