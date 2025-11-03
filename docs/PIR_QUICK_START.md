# PIR Follow-ups - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Update Configuration

Add these lines to your `.env` file:

```bash
# PIR Configuration
PIR_REMINDER_HOURS=24
PIR_ESCALATION_HOURS=48
CHANGE_MANAGER_EMAIL=your.manager@example.com
```

### Step 2: Initialize Database

Run the database setup to create the PIR tracking table:

```bash
python setup_database.py
```

This creates the `pir_tracking` table in your SQL Server database.

### Step 3: Test the PIR Agent

Run the test suite to verify everything works:

```bash
python tests/test_pir_agent.py
```

Expected output:
```
✅ Database initialized
✅ Test PIR data created successfully!
✅ PIR reminders processed
✅ PIR escalations processed
✅ PIR analytics generated
```

### Step 4: Enable Automatic PIR Tracking

The PIR workflow is automatically triggered when a CR moves to "Awaiting PIR" state. Ensure your polling service is running:

```bash
# In one terminal, start the polling service
python src/services/polling_service.py
```

### Step 5: Schedule PIR Reminders

Set up the PIR scheduler to run every hour:

**Windows (PowerShell as Administrator):**
```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\Users\banish\CAB Agent\src\functions\pir_scheduler\main.py" -WorkingDirectory "C:\Users\banish\CAB Agent"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
Register-ScheduledTask -TaskName "PIR Scheduler" -Action $action -Trigger $trigger -Description "Check PIR reminders and escalations"
```

**Or run manually for testing:**
```bash
python src/functions/pir_scheduler/main.py
```

## 📊 How It Works

### Automatic Workflow

1. **CR moves to "Awaiting PIR"** → System detects via polling service
2. **PIR tracking initiated** → Reviewers notified immediately
3. **After 24 hours** → Reminder sent to reviewers
4. **After 48 hours** → Escalated to Change Manager
5. **PIR completed** → Requester notified, CR closed

### Manual Operations

**Check pending PIRs:**
```python
from src.agents.pir_agent import get_pending_pirs
result = get_pending_pirs()
print(f"Pending PIRs: {result['count']}")
```

**Complete a PIR manually:**
```python
from src.agents.pir_agent import complete_pir
complete_pir("CR12345", "reviewer@example.com", "All tests passed")
```

**View analytics:**
```python
from src.agents.pir_agent import get_pir_analytics
analytics = get_pir_analytics(days=30)
print(f"Completion rate: {analytics['completion_rate']}%")
```

## ✅ Validation Checklist

Verify your implementation meets all requirements:

- [x] **Automated PIR Notification System**
  - [x] Reviewers identified automatically
  - [x] Immediate notification sent when PIR needed
  - [x] CR details and instructions included

- [x] **PIR Tracking and Reminders**
  - [x] 24-hour reminder sent automatically
  - [x] Tracks reminder status to avoid duplicates
  - [x] Includes urgency indicators

- [x] **PIR Escalation Workflow**
  - [x] 48-hour escalation to Change Manager
  - [x] Status changes to "escalated"
  - [x] Complete audit trail maintained

- [x] **PIR Completion Workflow**
  - [x] Records completion timestamp
  - [x] Updates CR to "Closed"
  - [x] Notifies requester
  - [x] Stores PIR comments

- [x] **PIR Analytics**
  - [x] Completion rate tracking
  - [x] Average completion time
  - [x] SLA compliance metrics
  - [x] Pending vs. escalated counts

## 🎯 Expected Outcomes

Based on Problem 5 validation criteria:

| Metric | Target | Implementation |
|--------|--------|----------------|
| Automated notifications | 100% | ✅ All reviewers notified |
| PIR completion time reduction | 60% | ✅ Automated reminders |
| Manual follow-ups | Zero | ✅ Fully automated |
| Visibility | Complete | ✅ Real-time tracking + analytics |

## 🔧 Common Commands

```bash
# Check pending PIRs
python -c "from src.agents.pir_agent import get_pending_pirs; print(get_pending_pirs())"

# Run reminder check manually
python -c "from src.agents.pir_agent import check_pir_reminders; print(check_pir_reminders())"

# Run escalation check manually
python -c "from src.agents.pir_agent import check_pir_escalations; print(check_pir_escalations())"

# Get 30-day analytics
python -c "from src.agents.pir_agent import get_pir_analytics; print(get_pir_analytics(30))"
```

## 📝 Next Steps

1. **Monitor**: Watch the first few PIRs to ensure notifications are sent
2. **Adjust**: Tune `PIR_REMINDER_HOURS` and `PIR_ESCALATION_HOURS` as needed
3. **Analyze**: Review analytics weekly to identify bottlenecks
4. **Optimize**: Use metrics to improve PIR completion rates

## 🆘 Troubleshooting

**PIRs not being tracked?**
- Verify polling service is running
- Check CR state is exactly "Awaiting PIR"
- Review event processor logs

**Reminders not sending?**
- Ensure PIR scheduler is running
- Check `PIR_REMINDER_HOURS` configuration
- Verify Teams webhook URL is valid

**Need help?**
- Check logs in `logs/` directory
- Review `docs/PIR_IMPLEMENTATION.md` for detailed documentation
- Run test suite to validate setup

## 🎉 Success!

Your PIR follow-ups are now fully automated. The system will:
- ✅ Notify reviewers immediately
- ✅ Send reminders after 24 hours
- ✅ Escalate after 48 hours
- ✅ Track all metrics
- ✅ Provide complete visibility

No more manual follow-ups needed!
