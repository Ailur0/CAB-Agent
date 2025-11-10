# WIQL Query Templates for Reminder Flows

## Overview

These WIQL (Work Item Query Language) queries filter Change Requests by state and date windows to identify CRs that need reminders.

## Flow A - Approved State Reminders

### Query 1: Pre-Start Reminders (20 minutes before)

```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] IN (
    'Normal Change Request',
    'Emergency Change Request',
    'Standard Change Request',
    'Informational Change Request',
    'Child Change Request'
)
AND [System.State] = 'Approved'
AND [Microsoft.VSTS.Scheduling.StartDate] >= @Today
AND [Microsoft.VSTS.Scheduling.StartDate] <= @Today + 0.02083
ORDER BY [Microsoft.VSTS.Scheduling.StartDate] ASC
```

**Notes**:
- `@Today + 0.02083` = 30 minutes from now (0.02083 days)
- Fetch window is 30 minutes to account for flow execution time
- Filter in Power Automate to send reminder at exactly -20 minutes

### Query 2: Start Time Follow-up (at Proposed Start Date)

```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] IN (
    'Normal Change Request',
    'Emergency Change Request',
    'Standard Change Request',
    'Informational Change Request',
    'Child Change Request'
)
AND [System.State] = 'Approved'
AND [Microsoft.VSTS.Scheduling.StartDate] >= @Today - 0.00347
AND [Microsoft.VSTS.Scheduling.StartDate] <= @Today + 0.00347
ORDER BY [Microsoft.VSTS.Scheduling.StartDate] ASC
```

**Notes**:
- `@Today ± 0.00347` = ±5 minutes window around current time
- Catches CRs whose start time has arrived but are still "Approved"

---

## Flow B - In Progress State Reminders

### Query 1: Pre-End Reminders (20 minutes before)

```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] IN (
    'Normal Change Request',
    'Emergency Change Request',
    'Standard Change Request',
    'Informational Change Request',
    'Child Change Request'
)
AND [System.State] = 'In Progress'
AND [Microsoft.VSTS.Scheduling.FinishDate] >= @Today
AND [Microsoft.VSTS.Scheduling.FinishDate] <= @Today + 0.02083
ORDER BY [Microsoft.VSTS.Scheduling.FinishDate] ASC
```

**Notes**:
- Similar to Flow A but filters on `FinishDate` and "In Progress" state
- 30-minute window for processing

### Query 2: End Time Check (at Proposed End Date)

```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] IN (
    'Normal Change Request',
    'Emergency Change Request',
    'Standard Change Request',
    'Informational Change Request',
    'Child Change Request'
)
AND [System.State] = 'In Progress'
AND [Microsoft.VSTS.Scheduling.FinishDate] >= @Today - 0.00347
AND [Microsoft.VSTS.Scheduling.FinishDate] <= @Today + 0.00347
ORDER BY [Microsoft.VSTS.Scheduling.FinishDate] ASC
```

**Notes**:
- ±5 minute window around current time
- Used to check if work is complete (Actual End Date filled, results entered)

---

## Flow C - Awaiting PIR State Reminders

### Query: All Awaiting PIR Items

```sql
SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
FROM WorkItems
WHERE [System.WorkItemType] IN (
    'Normal Change Request',
    'Emergency Change Request',
    'Standard Change Request',
    'Informational Change Request',
    'Child Change Request'
)
AND [System.State] = 'Awaiting PIR'
ORDER BY [System.CreatedDate] DESC
```

**Notes**:
- No date filter - all items in "Awaiting PIR" state
- Sort by creation date to prioritize older items
- Filter in Power Automate based on last reminder sent timestamp

---

## Using WIQL in Power Automate

### Method 1: Azure DevOps Connector (Premium)

**Action**: "Send a HTTP request to Azure DevOps"
- **URI**: `Change_Management/_apis/wit/wiql?api-version=7.0`
- **Method**: POST
- **Body**:
```json
{
  "query": "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Approved' AND [Microsoft.VSTS.Scheduling.StartDate] >= @Today AND [Microsoft.VSTS.Scheduling.StartDate] <= @Today + 0.02083"
}
```

### Method 2: HTTP Action with PAT

**Action**: HTTP
- **URI**: `https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis/wit/wiql?api-version=7.0`
- **Method**: POST
- **Headers**:
  - `Authorization`: `Basic {base64(:{PAT})}`
  - `Content-Type`: `application/json`
- **Body**: Same as above

---

## Fetching Full Work Item Details

After getting IDs from WIQL, fetch full details with `workitemsbatch`:

**Action**: "Send a HTTP request to Azure DevOps"
- **URI**: `_apis/wit/workitemsbatch?api-version=7.0`
- **Method**: POST
- **Body**:
```json
{
  "ids": [123456, 789012, 345678],
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

**Response parsing**:
```json
{
  "count": 3,
  "value": [
    {
      "id": 123456,
      "fields": {
        "System.Title": "Deploy to Production",
        "System.State": "Approved",
        "System.AssignedTo": {
          "displayName": "John Doe",
          "uniqueName": "john.doe@realpage.com"
        },
        "Microsoft.VSTS.Scheduling.StartDate": "2025-11-10T15:30:00Z"
      }
    }
  ]
}
```

---

## Date Arithmetic Reference

WIQL uses decimal days for date arithmetic:

| Time Period | Decimal Value |
|-------------|---------------|
| 5 minutes   | 0.00347       |
| 10 minutes  | 0.00694       |
| 15 minutes  | 0.01042       |
| 20 minutes  | 0.01389       |
| 30 minutes  | 0.02083       |
| 1 hour      | 0.04167       |
| 1 day       | 1.0           |

**Formula**: `minutes / 1440 = decimal days`

---

## Performance Tips

1. **Limit fields in SELECT**: Only request fields you need
2. **Use date windows**: Don't query all CRs - filter by date range
3. **Batch IDs**: Fetch up to 200 work items per `workitemsbatch` call
4. **Cache results**: Store in flow variable to avoid repeated API calls
5. **Index on dates**: Ensure TFS has indexes on date fields (usually default)

---

## Testing Queries

Test queries in Azure DevOps web UI:
1. Go to **Boards** → **Queries**
2. Create new query
3. Switch to **WIQL** editor
4. Paste query and run
5. Verify results match expected CRs

Or use REST API directly:
```bash
curl -X POST "https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis/wit/wiql?api-version=7.0" \
  -H "Authorization: Basic $(echo -n :YOUR_PAT | base64)" \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT [System.Id] FROM WorkItems WHERE [System.State] = '\''Approved'\''"}'
```
