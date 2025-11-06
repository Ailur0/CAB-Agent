# CAB Agent Notification System - Summary

## What's Implemented

### ✅ Dual Notification System (No Azure Bot Service)

1. **Teams Channel Notifications** (Webhook)
   - Broadcasts to entire channel
   - Includes clickable "View CR" button
   - Free, instant setup

2. **Personal DM Notifications** (Power Automate)
   - Direct messages to CR creators
   - Includes clickable CR link
   - Free with Office 365

---

## CR Link Format

All notifications include a link to view the CR in Azure DevOps/TFS:

```
https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/{work_item_id}
```

Example: `https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597`

---

## Files Modified

### Configuration
- ✅ `src/utils/config.py`
  - Added `POWER_AUTOMATE_URL` config
  - Added `get_work_item_url()` method to generate CR links

### Notification Logic
- ✅ `src/services/event_processor.py`
  - Updated `send_teams_webhook_notification()` to include CR link button
  - Added `send_power_automate_notification()` for personal DMs
  - Both notifications sent simultaneously when CR state changes

### Environment Template
- ✅ `.env.template`
  - Added `POWER_AUTOMATE_URL` configuration option

### Test Scripts
- ✅ `test_power_automate.py`
  - Test personal notifications with CR links

### Documentation
- ✅ `docs/POWER_AUTOMATE_SETUP.md`
  - Complete setup guide for Power Automate flow
  - Includes JSON schema, message templates, troubleshooting

- ✅ `docs/NON_AZURE_IMPLEMENTATION.md`
  - Comprehensive guide for all non-Azure options

---

## How It Works

### 1. CR State Changes
```
User updates CR in Azure DevOps
    ↓
Polling service detects change (every 5 min)
    ↓
Event processor checks rules
    ↓
Notifications triggered
```

### 2. Dual Notifications Sent
```
Event Processor
    ├─→ Teams Webhook
    │   └─→ Channel notification with "View CR" button
    │
    └─→ Power Automate
        └─→ Personal DM to creator with clickable link
```

### 3. CR Link Generation
```python
# Automatic link generation based on your TFS configuration
Config.get_work_item_url("2579597")
# Returns: https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597
```

---

## Setup Checklist

### Option 1: Channel Notifications Only (Quickest)
- [ ] Create Teams webhook in channel
- [ ] Add `TEAMS_WEBHOOK_URL` to `.env`
- [ ] Start polling service
- [ ] ✅ Done! Channel gets notifications with CR links

### Option 2: Channel + Personal Notifications (Recommended)
- [ ] Complete Option 1
- [ ] Create Power Automate flow (10 min)
- [ ] Add `POWER_AUTOMATE_URL` to `.env`
- [ ] Test with `test_power_automate.py`
- [ ] ✅ Done! Both channel and personal notifications with CR links

---

## Configuration Required

### .env File
```bash
# Required for TFS/Azure DevOps Server
AZURE_DEVOPS_SERVER_URL=https://tfs.realpage.com/tfs
AZURE_DEVOPS_COLLECTION=Realpage
AZURE_DEVOPS_PROJECT=Change_Management
AZURE_DEVOPS_PAT=your_pat_token

# Required for channel notifications
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# Optional for personal notifications
POWER_AUTOMATE_URL=https://prod-xx.westus.logic.azure.com:443/workflows/...
```

---

## Example Notifications

### Teams Channel (Webhook)
```
┌─────────────────────────────────────────────────┐
│ ✅ CR Status Update: CR2579597                  │
├─────────────────────────────────────────────────┤
│ Change request status has changed.              │
│                                                 │
│ CR ID:             CR2579597                    │
│ Title:             Database Migration           │
│ Creator:           john.doe@company.com         │
│ Previous Status:   Pending CAB                  │
│ New Status:        Approved                     │
│                                                 │
│ [View CR in Azure DevOps] ← Button             │
└─────────────────────────────────────────────────┘
```

### Personal DM (Power Automate)
```
Flow bot  12:30 PM

🔔 CR Status Update

CR ID: CR2579597
Title: Database Migration for Production
Status Change: Pending CAB → Approved

View CR in Azure DevOps ← Clickable link
https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597

---
This is an automated notification from CAB Agent
```

---

## Testing

### Test Webhook
```bash
python test_webhook.py
```
Check Teams channel for notification with "View CR" button.

### Test Power Automate
```bash
python test_power_automate.py
```
Check Teams for personal DM from Flow bot with clickable link.

### Test End-to-End
```bash
# Start polling service
python start_polling.py

# Change a CR state in Azure DevOps
# Wait up to 5 minutes
# Check both channel and personal messages
```

---

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Teams Webhook | $0 |
| Power Automate | $0 (included with Office 365) |
| SQL Server (local) | $0 |
| Polling Service | $0 |
| OpenAI API | ~$5-10/month |
| **Total** | **~$5-10/month** |

---

## Benefits

✅ **No Azure Bot Service** - Zero subscription fees  
✅ **Dual notifications** - Channel + personal  
✅ **Clickable CR links** - Direct access to work items  
✅ **Free** - Only OpenAI API costs  
✅ **Easy setup** - 10-20 minutes total  
✅ **Flexible** - Can add/remove channels independently  

---

## Next Steps

1. **Review setup guide:** `docs/POWER_AUTOMATE_SETUP.md`
2. **Configure Power Automate flow** (10 minutes)
3. **Update .env file** with flow URL
4. **Test notifications** with test scripts
5. **Start polling service** and enjoy automated notifications!

---

## Support

- **Setup issues:** See `docs/POWER_AUTOMATE_SETUP.md` troubleshooting section
- **Configuration:** Check `.env.template` for all options
- **Architecture:** Review `docs/NON_AZURE_IMPLEMENTATION.md`
- **Testing:** Use `test_webhook.py` and `test_power_automate.py`
