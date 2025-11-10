# Azure DevOps API Reference for Reminder Flows

## Base Configuration

### Connection Details
- **Organization**: `Realpage`
- **Project**: `Change_Management`
- **Base URL**: `https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis`
- **API Version**: `7.0`

### Authentication
- **Method**: Personal Access Token (PAT)
- **Header**: `Authorization: Basic {base64(:{PAT})}`
- **Scope Required**: `Work Items (Read)`

---

## Core Endpoints

### 1. WIQL Query (Work Item Query Language)

**Purpose**: Find work items matching specific criteria

**Endpoint**: `POST /_apis/wit/wiql?api-version=7.0`

**Request Body**:
```json
{
  "query": "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Approved'"
}
```

**Response**:
```json
{
  "queryType": "flat",
  "queryResultType": "workItem",
  "asOf": "2025-11-10T10:00:00Z",
  "workItems": [
    {
      "id": 887155,
      "url": "https://tfs.realpage.com/tfs/Realpage/_apis/wit/workItems/887155"
    }
  ]
}
```

**Rate Limit**: 60 requests/minute per PAT

**Power Automate Action**: "Send an HTTP request to Azure DevOps"
- **Organization Name**: `Realpage`
- **URI**: `Change_Management/_apis/wit/wiql?api-version=7.0`
- **Method**: POST
- **Body**: `{"query": "..."}`

---

### 2. Work Items Batch

**Purpose**: Fetch multiple work items with specific fields

**Endpoint**: `POST /_apis/wit/workitemsbatch?api-version=7.0`

**Request Body**:
```json
{
  "ids": [887155, 887185, 887198],
  "fields": [
    "System.Id",
    "System.Title",
    "System.State",
    "System.AssignedTo",
    "Microsoft.VSTS.Scheduling.StartDate",
    "Microsoft.VSTS.Scheduling.FinishDate"
  ]
}
```

**Response**:
```json
{
  "count": 3,
  "value": [
    {
      "id": 887155,
      "rev": 5,
      "fields": {
        "System.Id": 887155,
        "System.Title": "Deploy Application Update",
        "System.State": "Approved",
        "System.AssignedTo": {
          "displayName": "John Doe",
          "uniqueName": "john.doe@realpage.com",
          "id": "abc-123-def",
          "imageUrl": "https://..."
        },
        "Microsoft.VSTS.Scheduling.StartDate": "2025-11-10T15:30:00Z",
        "Microsoft.VSTS.Scheduling.FinishDate": "2025-11-10T17:00:00Z"
      },
      "url": "https://tfs.realpage.com/tfs/Realpage/_apis/wit/workItems/887155"
    }
  ]
}
```

**Limits**:
- Max IDs per request: 200
- Rate limit: 60 requests/minute per PAT

**Power Automate Action**: "Send an HTTP request to Azure DevOps"
- **URI**: `_apis/wit/workitemsbatch?api-version=7.0`
- **Method**: POST
- **Body**: `{"ids": [...], "fields": [...]}`

---

### 3. Get Single Work Item

**Purpose**: Fetch one work item with all or specific fields

**Endpoint**: `GET /_apis/wit/workitems/{id}?api-version=7.0&fields={fields}`

**Example**:
```
GET /_apis/wit/workitems/887155?api-version=7.0&fields=System.Title,System.State,System.AssignedTo
```

**Response**:
```json
{
  "id": 887155,
  "rev": 5,
  "fields": {
    "System.Title": "Deploy Application Update",
    "System.State": "Approved",
    "System.AssignedTo": {
      "displayName": "John Doe",
      "uniqueName": "john.doe@realpage.com"
    }
  },
  "url": "https://tfs.realpage.com/tfs/Realpage/_apis/wit/workItems/887155"
}
```

**Power Automate Action**: "Send an HTTP request to Azure DevOps"
- **URI**: `_apis/wit/workitems/@{variables('WorkItemId')}?api-version=7.0`
- **Method**: GET

---

### 4. List Available Fields

**Purpose**: Discover field reference names for your TFS instance

**Endpoint**: `GET /_apis/wit/fields?api-version=7.0`

**Response**:
```json
{
  "count": 150,
  "value": [
    {
      "name": "Title",
      "referenceName": "System.Title",
      "type": "string",
      "readOnly": false,
      "canSortBy": true,
      "isQueryable": true
    },
    {
      "name": "Proposed Start Date",
      "referenceName": "Microsoft.VSTS.Scheduling.StartDate",
      "type": "dateTime",
      "readOnly": false,
      "canSortBy": true,
      "isQueryable": true
    }
  ]
}
```

**Use Case**: Verify field names before using in WIQL or batch requests

---

## Field Reference Names

### Standard System Fields

| Display Name | Reference Name | Type | Description |
|--------------|----------------|------|-------------|
| ID | `System.Id` | Integer | Unique work item ID |
| Title | `System.Title` | String | Work item title |
| State | `System.State` | String | Current state |
| Assigned To | `System.AssignedTo` | Identity | Assigned user |
| Created By | `System.CreatedBy` | Identity | Creator |
| Created Date | `System.CreatedDate` | DateTime | Creation timestamp |
| Changed Date | `System.ChangedDate` | DateTime | Last modified |
| Work Item Type | `System.WorkItemType` | String | Type (e.g., "Normal Change Request") |

### Microsoft VSTS Fields

| Display Name | Reference Name | Type | Description |
|--------------|----------------|------|-------------|
| Start Date | `Microsoft.VSTS.Scheduling.StartDate` | DateTime | Proposed start |
| Finish Date | `Microsoft.VSTS.Scheduling.FinishDate` | DateTime | Proposed end |
| Activated Date | `Microsoft.VSTS.Common.ActivatedDate` | DateTime | Actual start |
| Closed Date | `Microsoft.VSTS.Common.ClosedDate` | DateTime | Actual end |
| State Change Date | `Microsoft.VSTS.Common.StateChangeDate` | DateTime | Last state change |

### Custom Fields (Verify in Your Instance)

Use the "List Available Fields" endpoint to discover custom fields in your TFS instance.

**Example custom fields** (may not exist):
- `Custom.ProposedStartDate`
- `Custom.ProposedEndDate`
- `Custom.PIRStatus`
- `Custom.MaintenanceWindow`

---

## WIQL Query Examples

### Filter by State and Date Range

```sql
SELECT [System.Id], [System.Title]
FROM WorkItems
WHERE [System.State] = 'Approved'
  AND [Microsoft.VSTS.Scheduling.StartDate] >= @Today
  AND [Microsoft.VSTS.Scheduling.StartDate] <= @Today + 0.02083
ORDER BY [Microsoft.VSTS.Scheduling.StartDate] ASC
```

### Multiple States

```sql
SELECT [System.Id]
FROM WorkItems
WHERE [System.State] IN ('Approved', 'In Progress')
  AND [System.WorkItemType] = 'Normal Change Request'
```

### Assigned to Specific User

```sql
SELECT [System.Id]
FROM WorkItems
WHERE [System.AssignedTo] = 'john.doe@realpage.com'
  AND [System.State] = 'In Progress'
```

### Date Comparisons

```sql
-- Items created in last 7 days
SELECT [System.Id]
FROM WorkItems
WHERE [System.CreatedDate] >= @Today - 7

-- Items with no end date
SELECT [System.Id]
FROM WorkItems
WHERE [Microsoft.VSTS.Scheduling.FinishDate] = ''

-- Items overdue
SELECT [System.Id]
FROM WorkItems
WHERE [Microsoft.VSTS.Scheduling.FinishDate] < @Today
  AND [System.State] <> 'Closed'
```

### Complex Conditions

```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE (
    [System.WorkItemType] = 'Normal Change Request'
    OR [System.WorkItemType] = 'Emergency Change Request'
  )
  AND [System.State] = 'Approved'
  AND [Microsoft.VSTS.Scheduling.StartDate] >= @Today
  AND [Microsoft.VSTS.Scheduling.StartDate] <= @Today + 0.02083
ORDER BY [Microsoft.VSTS.Scheduling.StartDate] ASC
```

---

## Power Automate Integration

### Parse WIQL Response

**Schema for Parse JSON**:
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

**Extract IDs**:
```
Select action:
  From: @{body('Parse_JSON')?['workItems']}
  Map: @{item()?['id']}
```

### Parse Batch Response

**Schema for Parse JSON**:
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
          "rev": {"type": "integer"},
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
                  "uniqueName": {"type": "string"},
                  "id": {"type": "string"}
                }
              },
              "Microsoft.VSTS.Scheduling.StartDate": {"type": "string"},
              "Microsoft.VSTS.Scheduling.FinishDate": {"type": "string"}
            }
          },
          "url": {"type": "string"}
        }
      }
    }
  }
}
```

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Cause | Solution |
|------|---------|-------|----------|
| 200 | OK | Success | Continue processing |
| 400 | Bad Request | Invalid WIQL or field name | Check query syntax and field names |
| 401 | Unauthorized | Invalid or expired PAT | Refresh PAT, check permissions |
| 403 | Forbidden | Insufficient permissions | Grant "Work Items (Read)" scope |
| 404 | Not Found | Invalid work item ID | Validate ID exists |
| 429 | Too Many Requests | Rate limit exceeded | Implement retry with backoff |
| 500 | Internal Server Error | TFS server error | Retry after delay |
| 503 | Service Unavailable | TFS maintenance | Retry after delay |

### Retry Logic in Power Automate

**Configure Retry Policy**:
1. Click "..." on HTTP action
2. Select "Settings"
3. Configure:
   - **Retry Policy**: Exponential Interval
   - **Count**: 3
   - **Interval**: PT10S (10 seconds)
   - **Minimum Interval**: PT5S
   - **Maximum Interval**: PT1H

**Manual Retry with Condition**:
```
Scope: Try API Call
  HTTP: Call Azure DevOps
  
Configure run after (on Scope):
  Run after: has failed or has timed out
  
Condition: Check if retryable error
  @{or(
    equals(outputs('HTTP')?['statusCode'], 429),
    equals(outputs('HTTP')?['statusCode'], 500),
    equals(outputs('HTTP')?['statusCode'], 503)
  )}
  
If yes:
  Delay: 10 seconds
  HTTP: Retry call
```

---

## Performance Optimization

### Batch Requests Efficiently

**Bad** (multiple single requests):
```
For each ID in [1, 2, 3, 4, 5]:
  GET /wit/workitems/{ID}
```
**Result**: 5 API calls, 5x slower

**Good** (single batch request):
```
POST /wit/workitemsbatch
Body: {"ids": [1, 2, 3, 4, 5]}
```
**Result**: 1 API call, 5x faster

### Limit Fields in Requests

**Bad** (fetch all fields):
```json
{
  "ids": [1, 2, 3]
}
```
**Result**: Large response, slower parsing

**Good** (fetch only needed fields):
```json
{
  "ids": [1, 2, 3],
  "fields": [
    "System.Title",
    "System.State",
    "System.AssignedTo"
  ]
}
```
**Result**: Smaller response, faster parsing

### Use Date Windows in WIQL

**Bad** (query all items):
```sql
SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Approved'
```
**Result**: Returns 1000s of items

**Good** (filter by date):
```sql
SELECT [System.Id] FROM WorkItems 
WHERE [System.State] = 'Approved'
  AND [Microsoft.VSTS.Scheduling.StartDate] >= @Today
  AND [Microsoft.VSTS.Scheduling.StartDate] <= @Today + 0.02083
```
**Result**: Returns only relevant items (10-20)

---

## Rate Limiting

### Limits
- **60 requests per minute** per PAT
- **Resets**: Every 60 seconds
- **Applies to**: All API calls using same PAT

### Monitoring Usage

**Track in Power Automate**:
```
Initialize variable: APICallCount = 0

For each API call:
  Increment variable: APICallCount
  
At end of flow:
  Log: "API calls this run: @{variables('APICallCount')}"
```

### Staying Under Limits

**Strategy 1: Stagger Flows**
- Flow A runs at :00, :10, :20, :30, :40, :50
- Flow B runs at :05, :15, :25, :35, :45, :55
- Flow C runs at :00 (every 4 hours)

**Strategy 2: Batch Aggressively**
- Fetch up to 200 IDs per batch call
- Minimize separate API calls

**Strategy 3: Cache Results**
- Store batch results in flow variable
- Reuse for multiple operations
- Don't re-fetch same data

---

## Testing & Debugging

### Test API Calls with cURL

```bash
# WIQL Query
curl -X POST "https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis/wit/wiql?api-version=7.0" \
  -H "Authorization: Basic $(echo -n :YOUR_PAT | base64)" \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT [System.Id] FROM WorkItems WHERE [System.State] = '\''Approved'\''"}'

# Batch Request
curl -X POST "https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis/wit/workitemsbatch?api-version=7.0" \
  -H "Authorization: Basic $(echo -n :YOUR_PAT | base64)" \
  -H "Content-Type: application/json" \
  -d '{"ids":[887155,887185],"fields":["System.Title","System.State"]}'

# Single Work Item
curl "https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis/wit/workitems/887155?api-version=7.0" \
  -H "Authorization: Basic $(echo -n :YOUR_PAT | base64)"
```

### Test in Power Automate

1. Create test flow with manual trigger
2. Add HTTP action with API call
3. Run manually
4. Check run history for:
   - Request body
   - Response body
   - Status code
   - Duration
5. Use "Peek code" to see exact HTTP request

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Field not found | 400 error: "Cannot find field X" | Verify field exists with `/fields` endpoint |
| Invalid WIQL | 400 error: "Invalid query" | Test query in Azure DevOps web UI first |
| Rate limited | 429 error | Add retry logic, reduce call frequency |
| Timeout | 504 error | Reduce batch size, add timeout handling |
| Empty results | 200 but no items | Check WIQL date filters, verify test data |

---

## Security Best Practices

### PAT Management
- ✅ Use dedicated service account
- ✅ Minimum required scope (Work Items Read)
- ✅ Set expiration (90 days max)
- ✅ Store in Azure Key Vault or secure connection
- ✅ Rotate regularly
- ❌ Never hardcode in flow
- ❌ Never commit to source control
- ❌ Never share across environments

### Connection Security
- ✅ Use Azure DevOps connector (handles auth)
- ✅ Limit connection access to flow owners
- ✅ Audit connection usage
- ✅ Revoke unused connections
- ❌ Don't use personal PATs for production
- ❌ Don't share connection credentials

### Data Protection
- ✅ Log only necessary data
- ✅ Mask sensitive fields in logs
- ✅ Encrypt data at rest (SharePoint)
- ✅ Use HTTPS for all API calls
- ❌ Don't log full work item details
- ❌ Don't store PATs in SharePoint

---

## Additional Resources

### Official Documentation
- [Azure DevOps REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/)
- [Work Items API](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/)
- [WIQL Syntax](https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
- [Power Automate Azure DevOps Connector](https://learn.microsoft.com/en-us/connectors/visualstudioteamservices/)

### Tools
- [Azure DevOps REST API Explorer](https://learn.microsoft.com/en-us/rest/api/azure/devops/)
- [Postman Collection](https://www.postman.com/azure-devops)
- [Power Automate Flow Checker](https://flow.microsoft.com/en-us/blog/introducing-the-flow-checker/)

### Support
- Azure DevOps API Issues: [Developer Community](https://developercommunity.visualstudio.com/)
- Power Automate Issues: [Power Automate Community](https://powerusers.microsoft.com/t5/Power-Automate-Community/ct-p/MPACommunity)
- Internal: Contact CAB Agent development team
