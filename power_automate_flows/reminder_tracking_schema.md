# Reminder Tracking Schema

## Purpose

Track which reminders have been sent to prevent duplicate notifications and maintain audit trail.

## Storage Options

### Option 1: SharePoint List (Recommended for simplicity)
- Easy to set up in Power Automate
- Built-in versioning and permissions
- Can be viewed/edited by admins
- No additional licensing required

### Option 2: Dataverse Table
- Better performance for high volume
- Advanced querying capabilities
- Requires Dataverse license/capacity
- Better integration with Power Platform

### Option 3: Azure Table Storage
- Lowest cost for high volume
- Requires Azure subscription
- More complex setup
- Best for enterprise scale

## Schema

### Table: `ReminderLog`

| Column Name | Type | Required | Description | Example |
|-------------|------|----------|-------------|---------|
| `Id` | Auto-increment | Yes | Unique identifier | 1234 |
| `WorkItemId` | Number | Yes | Azure DevOps CR ID | 887155 |
| `CRNumber` | Text | Yes | Formatted CR number | CR887155 |
| `ReminderType` | Choice | Yes | Type of reminder sent | "Approved-PreStart" |
| `State` | Text | Yes | CR state at time of reminder | "Approved" |
| `SentTimestamp` | DateTime | Yes | When reminder was sent | 2025-11-10T10:10:00Z |
| `RecipientEmail` | Text | Yes | Who received the reminder | john.doe@realpage.com |
| `RecipientName` | Text | No | Display name | John Doe |
| `ProposedStartDate` | DateTime | No | Scheduled start | 2025-11-10T10:30:00Z |
| `ProposedEndDate` | DateTime | No | Scheduled end | 2025-11-10T12:00:00Z |
| `Status` | Choice | Yes | Reminder status | "Sent", "Failed", "Pending" |
| `ErrorMessage` | Text (multi) | No | Error details if failed | "Rate limit exceeded" |
| `ExtensionRequested` | Boolean | No | Extension flag | false |
| `ExtendedEndDate` | DateTime | No | New end date if extended | 2025-11-10T13:00:00Z |
| `EscalationSent` | Boolean | No | Escalation flag | false |
| `EscalationRecipient` | Text | No | Manager/director email | jane.manager@realpage.com |
| `Notes` | Text (multi) | No | Additional context | "User on vacation" |
| `FlowRunId` | Text | No | Power Automate run ID | 08585329112602834816... |
| `CreatedBy` | Person | Yes | Service account | service@realpage.com |
| `ModifiedDate` | DateTime | Yes | Last update | 2025-11-10T10:15:00Z |

### ReminderType Values

| Value | Description | Flow |
|-------|-------------|------|
| `Approved-PreStart` | 20 min before start | Flow A |
| `Approved-AtStart` | At start time follow-up | Flow A |
| `InProgress-PreEnd` | 20 min before end | Flow B |
| `InProgress-AtEnd` | At end time inquiry | Flow B |
| `InProgress-Extension` | Extension reminder | Flow B |
| `InProgress-Escalation` | Manager escalation | Flow B |
| `AwaitingPIR-Reminder` | PIR completion reminder | Flow C |

### Status Values

| Value | Description |
|-------|-------------|
| `Sent` | Successfully delivered |
| `Failed` | Delivery failed |
| `Pending` | Queued but not sent |
| `Acknowledged` | Recipient confirmed |

---

## SharePoint List Setup

### Create List

1. Go to SharePoint site
2. Click **New** → **List**
3. Name: `CR_ReminderLog`
4. Description: "Tracks reminders sent for Change Requests"

### Add Columns

```powershell
# PowerShell script to create columns (run in SharePoint Online Management Shell)

Connect-PnPOnline -Url "https://yourorg.sharepoint.com/sites/CABAgent"

# Number columns
Add-PnPField -List "CR_ReminderLog" -DisplayName "WorkItemId" -InternalName "WorkItemId" -Type Number -Required

# Text columns
Add-PnPField -List "CR_ReminderLog" -DisplayName "CRNumber" -InternalName "CRNumber" -Type Text -Required
Add-PnPField -List "CR_ReminderLog" -DisplayName "State" -InternalName "State" -Type Text -Required
Add-PnPField -List "CR_ReminderLog" -DisplayName "RecipientEmail" -InternalName "RecipientEmail" -Type Text -Required
Add-PnPField -List "CR_ReminderLog" -DisplayName "RecipientName" -InternalName "RecipientName" -Type Text
Add-PnPField -List "CR_ReminderLog" -DisplayName "EscalationRecipient" -InternalName "EscalationRecipient" -Type Text
Add-PnPField -List "CR_ReminderLog" -DisplayName "FlowRunId" -InternalName "FlowRunId" -Type Text

# DateTime columns
Add-PnPField -List "CR_ReminderLog" -DisplayName "SentTimestamp" -InternalName "SentTimestamp" -Type DateTime -Required
Add-PnPField -List "CR_ReminderLog" -DisplayName "ProposedStartDate" -InternalName "ProposedStartDate" -Type DateTime
Add-PnPField -List "CR_ReminderLog" -DisplayName "ProposedEndDate" -InternalName "ProposedEndDate" -Type DateTime
Add-PnPField -List "CR_ReminderLog" -DisplayName "ExtendedEndDate" -InternalName "ExtendedEndDate" -Type DateTime

# Choice columns
Add-PnPField -List "CR_ReminderLog" -DisplayName "ReminderType" -InternalName "ReminderType" -Type Choice -Choices @("Approved-PreStart","Approved-AtStart","InProgress-PreEnd","InProgress-AtEnd","InProgress-Extension","InProgress-Escalation","AwaitingPIR-Reminder") -Required
Add-PnPField -List "CR_ReminderLog" -DisplayName "Status" -InternalName "Status" -Type Choice -Choices @("Sent","Failed","Pending","Acknowledged") -Required

# Boolean columns
Add-PnPField -List "CR_ReminderLog" -DisplayName "ExtensionRequested" -InternalName "ExtensionRequested" -Type Boolean
Add-PnPField -List "CR_ReminderLog" -DisplayName "EscalationSent" -InternalName "EscalationSent" -Type Boolean

# Multi-line text columns
Add-PnPField -List "CR_ReminderLog" -DisplayName "ErrorMessage" -InternalName "ErrorMessage" -Type Note
Add-PnPField -List "CR_ReminderLog" -DisplayName "Notes" -InternalName "Notes" -Type Note
```

### Set Permissions

- **Service account**: Full control
- **CAB team**: Edit
- **Managers**: Read
- **General users**: No access

---

## Power Automate Usage

### Check if Reminder Already Sent

**Action**: Get items (SharePoint)
- **Site Address**: Your SharePoint site
- **List Name**: CR_ReminderLog
- **Filter Query**: 
  ```
  WorkItemId eq 887155 and ReminderType eq 'Approved-PreStart' and Status eq 'Sent'
  ```
- **Top Count**: 1

**Condition**: 
```
length(outputs('Get_items')?['body/value']) is equal to 0
```
If true → Send reminder (not sent before)
If false → Skip (already sent)

### Log Reminder Sent

**Action**: Create item (SharePoint)
- **Site Address**: Your SharePoint site
- **List Name**: CR_ReminderLog
- **Fields**:
  - WorkItemId: `@{items('Apply_to_each')?['id']}`
  - CRNumber: `CR@{items('Apply_to_each')?['id']}`
  - ReminderType: `Approved-PreStart`
  - State: `@{items('Apply_to_each')?['fields']?['System.State']}`
  - SentTimestamp: `@{utcNow()}`
  - RecipientEmail: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['uniqueName']}`
  - RecipientName: `@{items('Apply_to_each')?['fields']?['System.AssignedTo']?['displayName']}`
  - ProposedStartDate: `@{items('Apply_to_each')?['fields']?['Microsoft.VSTS.Scheduling.StartDate']}`
  - Status: `Sent`
  - FlowRunId: `@{workflow()?['run']?['name']}`

### Update Reminder Status

**Action**: Update item (SharePoint)
- **Site Address**: Your SharePoint site
- **List Name**: CR_ReminderLog
- **Id**: `@{outputs('Get_items')?['body/value'][0]?['ID']}`
- **Fields**:
  - Status: `Failed`
  - ErrorMessage: `@{outputs('Send_email')?['error']?['message']}`
  - ModifiedDate: `@{utcNow()}`

---

## Queries for Reporting

### Reminders Sent Today

```
SentTimestamp ge '@{formatDateTime(utcNow(), 'yyyy-MM-dd')}T00:00:00Z'
```

### Failed Reminders

```
Status eq 'Failed'
```

### Escalations This Week

```
ReminderType eq 'InProgress-Escalation' and SentTimestamp ge '@{addDays(utcNow(), -7)}'
```

### Reminders for Specific CR

```
WorkItemId eq 887155
```

### Pending Extensions

```
ExtensionRequested eq true and Status eq 'Sent'
```

---

## Data Retention

- **Keep**: 90 days for active tracking
- **Archive**: Move to separate list/table after 90 days
- **Delete**: After 1 year (or per compliance requirements)

Set up Power Automate scheduled flow to archive old records monthly.

---

## Monitoring & Alerts

### Daily Summary Flow

Create a scheduled flow that runs daily at 8 AM:
1. Get all reminders sent yesterday
2. Count by type and status
3. Email summary to CAB team

### Alert on Failures

Create an automated flow triggered on item creation:
1. Trigger: When item created in CR_ReminderLog
2. Condition: Status = 'Failed'
3. Send alert email to support team

### Escalation Dashboard

Create Power BI report connected to SharePoint list:
- Escalations by week
- Top CRs requiring escalation
- Average time to completion after escalation
