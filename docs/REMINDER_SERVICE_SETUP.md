# CR Reminder Service Setup

## Overview

The reminder service automatically notifies CR creators **15 minutes before their scheduled start time**, prompting them to update the CR status (e.g., from "Approved" to "In Progress").

---

## Architecture

```
┌─────────────────────┐
│  Reminder Service   │  Runs every 5 minutes
│  (APScheduler)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Query Database    │  Find CRs starting in next 15 min
│  (SQL Server)       │  WHERE scheduled_start_date BETWEEN now AND now+15min
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Check if Already    │  Avoid duplicate reminders
│ Notified            │  (cr_notifications_sent table)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Send Notification  │  HTTP POST to Power Automate flow
│  (Power Automate)   │  Payload: user_email, cr_id, title, link
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Teams Personal DM  │  "Your CR starts in 15 min - update status"
│  (Flow bot)         │  Includes clickable link to CR
└─────────────────────┘
```

---

## Prerequisites

1. **Power Automate Per-User License** (~$15/month) assigned to the flow owner
2. **Power Automate Flow** configured to receive HTTP requests
3. **Database** with `change_requests` table populated (via `sync_azure_devops.py`)
4. **POWER_AUTOMATE_URL** configured in `.env`

---

## Power Automate Flow Setup

### 1. Create Flow

1. Go to [Power Automate](https://make.powerautomate.com)
2. Create new **Instant cloud flow**
3. Name: `CAB Agent - CR Reminder`
4. Trigger: **When an HTTP request is received**

### 2. Configure HTTP Trigger

**Request Body JSON Schema:**

```json
{
  "type": "object",
  "properties": {
    "user_email": {
      "type": "string"
    },
    "cr_id": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "scheduled_start": {
      "type": "string"
    },
    "current_state": {
      "type": "string"
    },
    "cr_link": {
      "type": "string"
    },
    "notification_type": {
      "type": "string"
    }
  }
}
```

### 3. Add Teams Action

**Action:** `Post message in a chat or channel`

**Settings:**
- **Post as:** Flow bot
- **Post in:** Chat with Flow bot
- **Recipient:** `user_email` (from trigger)
- **Message:**

```
⏰ **CR Reminder - Starting Soon!**

Your change request is scheduled to start in **15 minutes**.

**CR ID:** [cr_id]  
**Title:** [title]  
**Scheduled Start:** [scheduled_start]  
**Current Status:** [current_state]

🔗 [Update CR Status]([cr_link])

Please ensure the CR status is updated to "In Progress" when you begin implementation.
```

### 4. Save and Copy URL

1. Save the flow
2. Copy the **HTTP POST URL** from the trigger
3. Add to `.env`:
   ```
   POWER_AUTOMATE_URL=https://prod-xx.westus.logic.azure.com:443/workflows/...
   ```

---

## Installation

### 1. Verify Database

Ensure CRs are synced with `scheduled_start_date` populated:

```bash
python sync_azure_devops.py --limit 100
```

Check in SSMS:
```sql
SELECT TOP 10 cr_id, title, scheduled_start_date, state, created_by_email
FROM change_requests
WHERE scheduled_start_date IS NOT NULL
ORDER BY scheduled_start_date DESC;
```

### 2. Configure Environment

Add to `.env`:

```env
# Power Automate Flow URL (required)
POWER_AUTOMATE_URL=https://prod-xx.westus.logic.azure.com:443/workflows/YOUR_FLOW_ID/...

# Database connection (already configured)
DATABASE_URL=mssql+pyodbc://...

# Azure DevOps (already configured)
AZURE_DEVOPS_SERVER_URL=https://tfs.realpage.com/tfs
AZURE_DEVOPS_COLLECTION=Realpage
AZURE_DEVOPS_PROJECT=Change_Management
AZURE_DEVOPS_PAT=your_pat_here
```

### 3. Test the Flow

```bash
python test_reminder.py
```

Expected output:
```
✅ Reminder sent successfully!
Check Teams for message from Flow bot.
```

### 4. Start the Service

```bash
python start_reminder_service.py
```

Output:
```
======================================================================
CAB AGENT - CR REMINDER SERVICE
======================================================================

🔔 Starting 15-minute reminder service...
   - Checks every 5 minutes for CRs starting soon
   - Sends Power Automate notification to CR creator
   - Includes link to update CR status

✅ Reminder service started successfully!

📋 Service details:
   - Check interval: 5 minutes
   - Reminder window: 15 minutes before start
   - Target states: Approved, Scheduled

💡 Press Ctrl+C to stop
```

---

## Service Behavior

### Reminder Logic

1. **Every 5 minutes**, the service queries the database:
   ```sql
   SELECT * FROM change_requests
   WHERE scheduled_start_date BETWEEN GETUTCDATE() AND DATEADD(MINUTE, 15, GETUTCDATE())
   AND state IN ('Approved', 'Scheduled')
   ```

2. **For each CR**, check if reminder already sent:
   ```sql
   SELECT * FROM cr_notifications_sent
   WHERE cr_id = 'CR123456'
   AND event_type = 'reminder_15min_before_start'
   AND recipient_email = 'creator@company.com'
   ```

3. **If not sent**, POST to Power Automate:
   ```json
   {
     "user_email": "creator@company.com",
     "cr_id": "CR2579597",
     "title": "Database Migration",
     "scheduled_start": "2025-11-10 14:30 UTC",
     "current_state": "Approved",
     "cr_link": "https://tfs.realpage.com/.../2579597",
     "notification_type": "reminder_15min"
   }
   ```

4. **Log notification** to prevent duplicates

### Deduplication

- Uses `cr_notifications_sent` table with unique constraint on `(cr_id, event_type, recipient_email)`
- Ensures each CR creator receives **exactly one** 15-minute reminder

### Error Handling

- Logs errors but continues processing other CRs
- Retries on next check cycle (5 minutes later)
- Monitors Power Automate response codes (expects 202 Accepted)

---

## Cost Model

### Licensing

| Component | License Required | Monthly Cost |
|-----------|-----------------|--------------|
| Flow Owner | Power Automate Per-User | ~$15 |
| Recipients | Microsoft 365 (any tier) | $0 (included) |

### Run Volume

**Assumptions:**
- 50 CRs per day with scheduled start times
- Each CR triggers 1 reminder
- Monthly runs = 50 × 30 = **1,500 runs/month**

**Per-User License Capacity:**
- Included runs: **40,000/month**
- Your usage: **1,500/month** (3.75% of capacity)
- Headroom: **38,500 runs** available for other flows

**Total Cost:** **$15/month** (one per-user license)

### Scaling

| Daily CRs | Monthly Runs | Cost |
|-----------|--------------|------|
| 50 | 1,500 | $15 (1 per-user) |
| 200 | 6,000 | $15 (1 per-user) |
| 1,000 | 30,000 | $15 (1 per-user) |
| 1,500 | 45,000 | $30 (2 per-user) or $150 (1 Process plan) |

---

## Monitoring

### Check Service Status

```bash
# View logs
tail -f logs/reminder_service.log

# Check database for recent notifications
SELECT TOP 20 cr_id, event_type, recipient_email, sent_at
FROM cr_notifications_sent
WHERE event_type = 'reminder_15min_before_start'
ORDER BY sent_at DESC;
```

### Power Automate Dashboard

1. Go to [Power Automate](https://make.powerautomate.com)
2. Select your flow
3. View **Run History**
4. Check for:
   - Success rate (should be ~100%)
   - Run count (should match database notifications)
   - Error details (if any failures)

### Capacity Monitoring

1. Admin Center → Power Platform → Capacity
2. Monitor **Flow runs** usage
3. Set alerts if approaching 40k/month threshold

---

## Troubleshooting

### No Reminders Sent

**Check 1:** Verify CRs have `scheduled_start_date` populated
```sql
SELECT COUNT(*) FROM change_requests WHERE scheduled_start_date IS NOT NULL;
```

**Check 2:** Verify `POWER_AUTOMATE_URL` is configured
```bash
grep POWER_AUTOMATE_URL .env
```

**Check 3:** Test flow manually
```bash
python test_reminder.py
```

**Check 4:** Check service logs
```bash
tail -f logs/reminder_service.log
```

### Duplicate Reminders

**Cause:** Database constraint not enforced

**Fix:** Recreate `cr_notifications_sent` table with unique constraint:
```sql
ALTER TABLE cr_notifications_sent
ADD CONSTRAINT UQ_Notification UNIQUE (cr_id, event_type, recipient_email);
```

### Flow Returns 400 Bad Request

**Cause:** JSON schema mismatch

**Fix:** Update flow schema to match payload in `reminder_service.py`:
- `user_email`
- `cr_id`
- `title`
- `scheduled_start`
- `current_state`
- `cr_link`
- `notification_type`

### Premium License Warning

**Cause:** Flow owner doesn't have Power Automate per-user license

**Fix:** Assign license in Microsoft 365 Admin Center:
1. Users → Active users
2. Select flow owner
3. Licenses and apps → Power Automate per user

---

## Production Deployment

### Run as Windows Service

**Option 1: NSSM (Non-Sucking Service Manager)**

```powershell
# Install NSSM
choco install nssm

# Create service
nssm install CABAgentReminder "C:\Python39\python.exe" "C:\CAB Agent\start_reminder_service.py"
nssm set CABAgentReminder AppDirectory "C:\CAB Agent"
nssm set CABAgentReminder DisplayName "CAB Agent Reminder Service"
nssm set CABAgentReminder Description "Sends 15-minute reminders for upcoming CRs"
nssm set CABAgentReminder Start SERVICE_AUTO_START

# Start service
nssm start CABAgentReminder
```

**Option 2: Task Scheduler**

1. Open Task Scheduler
2. Create Task:
   - Name: `CAB Agent Reminder Service`
   - Trigger: At system startup
   - Action: Start program
     - Program: `python.exe`
     - Arguments: `start_reminder_service.py`
     - Start in: `C:\CAB Agent`
   - Settings: Run whether user is logged on or not

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "start_reminder_service.py"]
```

```bash
docker build -t cab-agent-reminder .
docker run -d --name reminder --env-file .env cab-agent-reminder
```

---

## Summary

✅ **What you now have:**
- Automated 15-minute reminders for CR creators
- Personal Teams DMs via Power Automate
- Clickable links to update CR status
- Deduplication to prevent spam
- Cost-effective ($15/month for 1,500 notifications)

✅ **Next steps:**
1. Assign Power Automate per-user license to flow owner
2. Configure flow with HTTP trigger + Teams action
3. Add `POWER_AUTOMATE_URL` to `.env`
4. Test with `test_reminder.py`
5. Start service with `start_reminder_service.py`
6. Monitor run history in Power Automate dashboard

---

## References

- [Power Automate Licensing](https://powerautomate.microsoft.com/en-us/pricing/)
- [HTTP Request Trigger](https://learn.microsoft.com/en-us/power-automate/triggers-introduction#http-request-trigger)
- [Teams Connector](https://learn.microsoft.com/en-us/connectors/teams/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
