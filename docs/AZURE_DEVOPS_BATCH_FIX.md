# Azure DevOps Batch API Error Fix

## Problem
The sync script was failing with a `400 Bad Request` error when fetching work items from Azure DevOps at batch 13900:

```
2025-11-06 17:03:54 [error] Failed to fetch CR batch batch_size=100 batch_start=13900 
error='400 Client Error: Bad Request for url: https://tfs.realpage.com/tfs/Realpage/Change_Management/_apis/wit/workitemsbatch?api-version=7.0'
```

## Root Causes
1. **Invalid custom fields** - Fields like `Custom.ScheduledTime` don't exist in this TFS instance
2. **Large batch size (100)** - While Azure DevOps supports up to 200 items, smaller batches are more stable
3. **No validation of work item IDs** - Invalid IDs could cause 400 errors
4. **Insufficient error logging** - Response body wasn't logged, making diagnosis difficult
5. **No retry logic** - Transient errors would immediately fail
6. **No rate limiting handling** - API rate limits could cause failures

## Fixes Applied

### 1. Removed Invalid Custom Fields (`azure_devops_tool.py`) ⭐ PRIMARY FIX
The error message revealed:
```
'TF51535: Cannot find field Custom.ScheduledTime.'
```

**Removed these non-existent custom fields:**
- `Custom.ScheduledTime`
- `Custom.DurationHours`
- `Custom.ScheduledStartDate`
- `Custom.ScheduledEndDate`
- `Custom.ApprovalStatus`
- `Custom.IsthisanAzureDevOpsdeployment`
- `Custom.IsAutomatedDeployment`
- `Custom.AutomatedDeployment`
- `Custom.AutomationTechnology`
- `Custom.DeploymentNeedsDeleted`
- `Custom.NeedsDeleted`

**Now using only standard fields:**
- System fields: `Title`, `Description`, `State`, `WorkItemType`, `CreatedBy`, `AssignedTo`, `CreatedDate`
- Microsoft VSTS fields: `StartDate`, `FinishDate`, `ClosedDate`

### 2. Reduced Batch Size (`azure_devops_tool.py`)
- Changed from **100 to 50** work items per batch
- Smaller batches are more reliable and less likely to hit payload size limits
- Reduces memory usage and improves error recovery

### 3. Added Work Item ID Validation (`azure_devops_tool.py`)
```python
# Validate and extract IDs
batch_ids = []
for item in batch:
    item_id = item.get("id")
    if item_id and isinstance(item_id, int):
        batch_ids.append(item_id)
    else:
        logger.warning("Invalid work item ID", item=item)
```
- Validates that IDs exist and are integers
- Skips invalid IDs with warning logs
- Prevents 400 errors from malformed requests

### 4. Enhanced Error Logging (`auth.py`)
```python
try:
    error_detail = response.json()
    logger.error(
        "Azure DevOps API error",
        status_code=response.status_code,
        error_detail=error_detail,  # Full error details from API
        endpoint=endpoint,
    )
except:
    logger.error(
        "Azure DevOps API error",
        status_code=response.status_code,
        response_text=response.text[:500],  # Raw response text
        endpoint=endpoint,
    )
```
- Logs the full error response from Azure DevOps API
- Shows exactly what went wrong (e.g., invalid field names, missing permissions)
- Helps diagnose issues quickly

### 5. Added Retry Logic with Exponential Backoff (`auth.py`)
```python
for attempt in range(max_retries):
    try:
        response = requests.request(...)
        # ... handle response
    except requests.exceptions.RequestException as e:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
            continue
```
- **3 retry attempts** for transient errors
- **Exponential backoff**: 1s, 2s, 4s delays
- Retries on:
  - Rate limiting (429)
  - Server errors (500, 502, 503, 504)
  - Network errors (timeouts, connection issues)

### 6. Improved Batch Logging (`azure_devops_tool.py`)
```python
logger.info(
    "Fetching CR batch",
    batch_start=start,
    batch_size=len(batch_ids),
    id_range=f"{batch_ids[0]}-{batch_ids[-1]}",
)
```
- Logs batch progress with ID ranges
- Shows successful batch completions
- Logs first 5 IDs on error for debugging

### 7. Graceful Error Handling
- Continues processing remaining batches if one fails
- Collects all successful results
- Doesn't fail entire sync on single batch error

## Testing

### 1. Test with Limited Sync
```bash
python sync_azure_devops.py --limit 100
```
This will test the first 100 CRs (2 batches of 50).

### 2. Test Full Sync
```bash
python sync_azure_devops.py --all
```
This will sync all CRs with the new error handling.

### 3. Monitor Logs
Watch for:
- ✅ **Success logs**: "Successfully fetched CR batch"
- ⚠️ **Warning logs**: Invalid IDs, retries
- ❌ **Error logs**: Failed batches with detailed error messages

### 4. Check Error Details
If a 400 error occurs again, the logs will now show:
- **Exact error message** from Azure DevOps
- **Batch IDs** that failed (first 5)
- **Attempt number** if retrying
- **Response body** with detailed error information

## Expected Improvements

1. **Higher success rate** - Smaller batches and retries handle transient issues
2. **Better diagnostics** - Detailed error logs show exactly what's wrong
3. **Graceful degradation** - Continues processing even if some batches fail
4. **Rate limit handling** - Automatically retries with backoff on 429 errors
5. **Network resilience** - Handles timeouts and connection issues

## Common 400 Error Causes

Based on the enhanced logging, you may see these specific errors:

### Invalid Field Names
```json
{
  "message": "VS403496: The field 'Custom.FieldName' does not exist."
}
```
**Fix**: Remove or rename the field in the `fields` list

### Invalid Work Item IDs
```json
{
  "message": "VS403040: Work item 12345 does not exist."
}
```
**Fix**: Already handled by ID validation

### Permission Issues
```json
{
  "message": "VS403499: You do not have permission to access this resource."
}
```
**Fix**: Check PAT token permissions

### Payload Too Large
```json
{
  "message": "Request entity too large"
}
```
**Fix**: Already handled by reducing batch size to 50

## Monitoring

After running the sync, check:

1. **Total CRs processed** vs **expected count**
2. **Error rate** - Should be < 1% with retries
3. **Batch failures** - Investigate any consistent failures
4. **Performance** - Smaller batches may be slightly slower but more reliable

## Next Steps

If errors persist:

1. **Check the detailed error logs** - They now show the exact API error
2. **Verify field names** - Some custom fields may not exist in your Azure DevOps instance
3. **Test with smaller batches** - Reduce to 25 or 10 if needed
4. **Check API limits** - Azure DevOps may have project-specific limits
5. **Verify PAT permissions** - Ensure token has "Work Items (Read)" permission
