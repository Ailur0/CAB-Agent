# Comprehensive CR Reminder Flows

## Overview

The CAB Agent implements three automated reminder workflows that track CRs through their lifecycle and send timely notifications via Power Automate to ensure proper status management and completion.

---

## Flow 1: Approved State Reminders

### Purpose
Ensure CRs transition from "Approved" to "In Progress" at the scheduled start time.

### Timing & Logic

#### Part 1: 20 Minutes Before Start
- **Trigger:** CR in "Approved" state with `scheduled_start_date` in next 20 minutes
- **Recipient:** CR creator (`created_by_email`)
- **Message:** "Your CR is starting in 20 minutes. Please transition to 'In Progress' when you begin."
- **Event Type:** `approved_20min_before_start`

#### Part 2: At Scheduled Start Time
- **Trigger:** CR still in "Approved" state at or past `scheduled_start_date`
- **Recipient:** CR creator
- **Message:** "Your CR scheduled start time has arrived. Please update status to 'In Progress' immediately."
- **Event Type:** `approved_at_start_not_in_progress`
- **Window:** Checks CRs with start time between now and 5 minutes ago

### Implementation

```python
# Query CRs starting in next 20 minutes
approved_crs = session.query(ChangeRequest).filter(
    ChangeRequest.scheduled_start_date.isnot(None),
    ChangeRequest.scheduled_start_date >= now,
    ChangeRequest.scheduled_start_date <= now + timedelta(minutes=20),
    ChangeRequest.state == "Approved"
).all()

# Query CRs at start time still Approved
overdue_crs = session.query(ChangeRequest).filter(
    ChangeRequest.scheduled_start_date.isnot(None),
    ChangeRequest.scheduled_start_date <= now,
    ChangeRequest.scheduled_start_date >= now - timedelta(minutes=5),
    ChangeRequest.state == "Approved"
).all()
```

---

## Flow 2: In Progress State Reminders

### Purpose
Ensure CRs in progress complete on time, fill results, and request extensions if needed.

### Timing & Logic

#### Part 1: 20 Minutes Before End
- **Trigger:** CR in "In Progress" state with `scheduled_end_date` in next 20 minutes
- **Recipient:** CR creator
- **Message:** "Your CR is ending in 20 minutes. Please fill in results and update status."
- **Event Type:** `in_progress_20min_before_end`

#### Part 2: At Scheduled End Time
- **Trigger:** CR still in "In Progress" state at or past `scheduled_end_date`
- **Recipient:** CR creator
- **Message:** "Your CR scheduled end time has passed. Please provide completion status and results. Do you need an extension?"
- **Event Type:** `in_progress_at_end_no_results`
- **Requires Response:** Yes (user should reply with status/extension request)
- **Window:** Checks CRs with end time between now and 5 minutes ago

### Follow-up Actions (Manual Process)

When a CR remains "In Progress" past end time:

1. **User responds with extension request:**
   - If extension falls within Maintenance Window → Approve and wait
   - Send reminder again at new extended end time
   
2. **No response or extension denied:**
   - Escalate to manager/director per reporting hierarchy
   - Log escalation in system

### Implementation

```python
# Query CRs ending in next 20 minutes
in_progress_crs = session.query(ChangeRequest).filter(
    ChangeRequest.scheduled_end_date.isnot(None),
    ChangeRequest.scheduled_end_date >= now,
    ChangeRequest.scheduled_end_date <= now + timedelta(minutes=20),
    ChangeRequest.state == "In Progress"
).all()

# Query CRs past end time still In Progress
overdue_crs = session.query(ChangeRequest).filter(
    ChangeRequest.scheduled_end_date.isnot(None),
    ChangeRequest.scheduled_end_date <= now,
    ChangeRequest.scheduled_end_date >= now - timedelta(minutes=5),
    ChangeRequest.state == "In Progress"
).all()
```

---

## Flow 3: Awaiting PIR State Reminders

### Purpose
Ensure Post-Implementation Reviews (PIRs) are completed promptly.

### Timing & Logic

- **Trigger:** CR in "Awaiting PIR" state
- **Recipient:** Assigned user (`assigned_to`) or CR creator if not assigned
- **Message:** "Formal reminder: Please complete and submit the Post-Implementation Review (PIR) for this CR."
- **Event Type:** `awaiting_pir_reminder_YYYYMMDD` (daily unique)
- **Frequency:** Once per day (hourly checks, daily notification)
- **No ETA:** PIR has no specific deadline, but daily reminders ensure completion

### Implementation

```python
# Query all CRs in Awaiting PIR state
awaiting_pir_crs = session.query(ChangeRequest).filter(
    ChangeRequest.state == "Awaiting PIR"
).all()

# Send daily reminder (event_type includes date to prevent duplicates)
event_type = f"awaiting_pir_reminder_{datetime.utcnow().strftime('%Y%m%d')}"
```

---

## Power Automate Flow Configuration

### Updated JSON Schema

The Power Automate HTTP trigger must accept this schema:

```json
{
  "type": "object",
  "properties": {
    "user_email": {
      "type": "string",
      "description": "Recipient email address"
    },
    "cr_id": {
      "type": "string",
      "description": "Change Request ID (e.g., CR2579597)"
    },
    "title": {
      "type": "string",
      "description": "CR title"
    },
    "current_state": {
      "type": "string",
      "description": "Current CR state"
    },
    "cr_link": {
      "type": "string",
      "description": "URL to CR in Azure DevOps"
    },
    "notification_type": {
      "type": "string",
      "description": "Type of notification for routing logic"
    },
    "message": {
      "type": "string",
      "description": "Custom message text"
    },
    "scheduled_time": {
      "type": "string",
      "description": "Scheduled start/end time (optional)"
    },
    "requires_response": {
      "type": "boolean",
      "description": "Whether user response is needed"
    }
  }
}
```

### Flow Logic (Condition-Based Routing)

```
HTTP Trigger
    ↓
Condition: notification_type
    ↓
├─ approved_20min_before_start
│     → Post: "⏰ Starting in 20 min - transition to In Progress"
│
├─ approved_at_start_not_in_progress
│     → Post: "🚨 Start time reached - update status NOW"
│
├─ in_progress_20min_before_end
│     → Post: "⏰ Ending in 20 min - fill results"
│
├─ in_progress_at_end_no_results
│     → Post: "🚨 End time passed - provide status or request extension"
│     → Include Adaptive Card with buttons: [Completed] [Need Extension]
│
└─ awaiting_pir_reminder
      → Post: "📋 Please complete PIR for this CR"
```

### Sample Teams Message Template

```markdown
{notification_icon} **CR Reminder**

**CR ID:** {cr_id}  
**Title:** {title}  
**Current State:** {current_state}  
{if scheduled_time}**Scheduled:** {scheduled_time}{endif}

{message}

🔗 [Update CR Status]({cr_link})

{if requires_response}
Please reply with:
- ✅ Completed
- ⏰ Need extension (specify duration)
- ❌ Issue encountered (explain)
{endif}
```

---

## Deduplication Strategy

### Event Type Naming

Each notification has a unique `event_type` stored in `cr_notifications_sent`:

| Flow | Event Type | Uniqueness |
|------|-----------|------------|
| Approved - 20min before | `approved_20min_before_start` | Per CR |
| Approved - at start | `approved_at_start_not_in_progress` | Per CR |
| In Progress - 20min before | `in_progress_20min_before_end` | Per CR |
| In Progress - at end | `in_progress_at_end_no_results` | Per CR |
| Awaiting PIR | `awaiting_pir_reminder_YYYYMMDD` | Per CR per day |

### Database Constraint

```sql
ALTER TABLE cr_notifications_sent
ADD CONSTRAINT UQ_Notification 
UNIQUE (cr_id, event_type, recipient_email);
```

This ensures:
- Each CR gets exactly one 20-min reminder
- Each CR gets exactly one at-start/at-end reminder
- PIR reminders sent once per day

---

## Service Configuration

### Scheduler Jobs

```python
# Flow 1 & 2: Check every 5 minutes
scheduler.add_job(
    check_approved_state_reminders,
    trigger=IntervalTrigger(minutes=5),
    id="check_approved_reminders"
)

scheduler.add_job(
    check_in_progress_reminders,
    trigger=IntervalTrigger(minutes=5),
    id="check_in_progress_reminders"
)

# Flow 3: Check every hour (daily notification)
scheduler.add_job(
    check_awaiting_pir_reminders,
    trigger=IntervalTrigger(hours=1),
    id="check_awaiting_pir_reminders"
)
```

### Environment Variables

```env
# Required
POWER_AUTOMATE_URL=https://prod-xx.westus.logic.azure.com:443/workflows/...
DATABASE_URL=mssql+pyodbc://...
AZURE_DEVOPS_SERVER_URL=https://tfs.realpage.com/tfs
AZURE_DEVOPS_COLLECTION=Realpage
AZURE_DEVOPS_PROJECT=Change_Management
```

---

## Cost Model

### Notification Volume Estimate

**Assumptions:**
- 50 CRs per day with scheduled times
- Each CR triggers up to 4 notifications (2 for Approved, 2 for In Progress)
- 10 CRs per day in Awaiting PIR

**Monthly Runs:**
- Approved reminders: 50 × 2 × 30 = **3,000 runs**
- In Progress reminders: 50 × 2 × 30 = **3,000 runs**
- Awaiting PIR reminders: 10 × 30 = **300 runs**
- **Total: 6,300 runs/month**

### Licensing

| Component | License | Monthly Cost |
|-----------|---------|--------------|
| Flow Owner | Power Automate Per-User | $15 |
| Recipients | Microsoft 365 (any tier) | $0 (included) |

**Capacity:**
- Per-user license: 40,000 runs/month included
- Usage: 6,300 runs (15.75% of capacity)
- Headroom: 33,700 runs available

**Total Cost:** **$15/month** (one per-user license)

---

## Testing

### Test Individual Flows

```bash
# Create test CRs in database with specific states and times

# Test Approved flow (20min before start)
python -c "
from datetime import datetime, timedelta
from src.database import get_session, ChangeRequest
session = get_session()
cr = ChangeRequest(
    cr_id='CRTEST001',
    title='Test Approved Reminder',
    state='Approved',
    created_by_email='your.email@company.com',
    scheduled_start_date=datetime.utcnow() + timedelta(minutes=15)
)
session.add(cr)
session.commit()
print('Test CR created')
"

# Wait for reminder service to pick it up (within 5 minutes)
# Check Teams for notification
```

### Test Power Automate Integration

```bash
python test_reminder.py
```

### Monitor Notifications

```sql
-- View recent notifications
SELECT TOP 20 
    cr_id, 
    event_type, 
    recipient_email, 
    sent_at
FROM cr_notifications_sent
ORDER BY sent_at DESC;

-- Count by type
SELECT 
    event_type, 
    COUNT(*) as count
FROM cr_notifications_sent
WHERE sent_at >= DATEADD(day, -7, GETUTCDATE())
GROUP BY event_type;
```

---

## Troubleshooting

### No Reminders Sent

**Check 1:** Verify CRs have correct states and times
```sql
SELECT cr_id, state, scheduled_start_date, scheduled_end_date, created_by_email
FROM change_requests
WHERE state IN ('Approved', 'In Progress', 'Awaiting PIR')
AND (scheduled_start_date IS NOT NULL OR scheduled_end_date IS NOT NULL OR state = 'Awaiting PIR');
```

**Check 2:** Verify service is running
```bash
# Check process
ps aux | grep start_reminder_service

# Check logs
tail -f logs/reminder_service.log
```

**Check 3:** Test Power Automate URL
```bash
curl -X POST $POWER_AUTOMATE_URL \
  -H "Content-Type: application/json" \
  -d '{"user_email":"test@company.com","cr_id":"CRTEST","title":"Test","notification_type":"test","current_state":"Test","cr_link":"https://test.com","message":"Test message"}'
```

### Duplicate Notifications

**Cause:** Database constraint not enforced or service running multiple instances

**Fix 1:** Ensure unique constraint exists
```sql
SELECT * FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE TABLE_NAME = 'cr_notifications_sent' AND CONSTRAINT_TYPE = 'UNIQUE';
```

**Fix 2:** Check for multiple service instances
```bash
ps aux | grep start_reminder_service | wc -l
# Should return 1 (plus grep itself)
```

### Flow Returns 400 Bad Request

**Cause:** JSON schema mismatch

**Fix:** Update Power Automate flow schema to match payload structure above

---

## Production Deployment

### Windows Service (Recommended)

```powershell
# Install NSSM
choco install nssm

# Create service
nssm install CABAgentReminders "C:\Python39\python.exe" "C:\CAB Agent\start_reminder_service.py"
nssm set CABAgentReminders AppDirectory "C:\CAB Agent"
nssm set CABAgentReminders DisplayName "CAB Agent Comprehensive Reminders"
nssm set CABAgentReminders Description "Multi-state CR reminder workflows"
nssm set CABAgentReminders Start SERVICE_AUTO_START

# Start service
nssm start CABAgentReminders
```

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
docker build -t cab-agent-reminders .
docker run -d --name reminders --env-file .env cab-agent-reminders
```

---

## Summary

✅ **What's Implemented:**
- Flow 1: Approved state reminders (20min before + at start)
- Flow 2: In Progress state reminders (20min before end + at end)
- Flow 3: Awaiting PIR daily reminders
- Deduplication via database tracking
- Power Automate integration with custom messages
- Cost-effective ($15/month for 6,300 notifications)

✅ **Next Steps:**
1. Update Power Automate flow with new JSON schema
2. Add condition-based routing for notification types
3. Test each flow with sample CRs
4. Deploy service as Windows Service or Docker container
5. Monitor run history and notification logs

---

## References

- [Power Automate Licensing](https://powerautomate.microsoft.com/en-us/pricing/)
- [Adaptive Cards for Teams](https://adaptivecards.io/designer/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
