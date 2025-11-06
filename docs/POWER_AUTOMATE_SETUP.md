# Power Automate Setup Guide - Personal Notifications with CR Links

## Overview

This guide shows how to add **personal Teams messages** with **clickable CR links** using Power Automate, while keeping your existing webhook channel notifications.

**What you get:**
- ✅ Personal DMs to CR creators (not just channel broadcasts)
- ✅ Clickable links to view CR in Azure DevOps/TFS
- ✅ No Azure Bot Service subscription needed
- ✅ Free (included with Office 365)

---

## Step 1: Create Power Automate Flow (10 minutes)

### 1.1 Create the Flow

1. Go to [Power Automate](https://make.powerautomate.com)
2. Click **"Create"** → **"Instant cloud flow"**
3. Name: `CAB Agent - Personal CR Notifications`
4. Trigger: **"When an HTTP request is received"**
5. Click **"Create"**

### 1.2 Configure HTTP Trigger

1. Click **"When an HTTP request is received"** step
2. Click **"Use sample payload to generate schema"**
3. Paste this JSON:

```json
{
  "user_email": "john.doe@company.com",
  "cr_id": "CR2579597",
  "title": "Database Migration for Production",
  "from_state": "Pending CAB",
  "to_state": "Approved",
  "cr_link": "https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597"
}
```

4. Click **"Done"** - schema will be auto-generated

### 1.3 Add Teams Message Action

1. Click **"+ New step"**
2. Search: **"Post message in a chat or channel"**
3. Select: **"Post as Flow bot to a user"** (Microsoft Teams connector)
4. Configure:
   - **Recipient**: Click in field → Select `user_email` from dynamic content
   - **Message**: Use this template (click "Add dynamic content" for bracketed items):

```
🔔 CR Status Update

**CR ID:** [cr_id]
**Title:** [title]
**Status Change:** [from_state] → [to_state]

[View CR in Azure DevOps]([cr_link])

---
_This is an automated notification from CAB Agent_
```

**Dynamic content mapping:**
- `[cr_id]` → Select **cr_id** from dynamic content
- `[title]` → Select **title** from dynamic content
- `[from_state]` → Select **from_state** from dynamic content
- `[to_state]` → Select **to_state** from dynamic content
- `[cr_link]` → Select **cr_link** from dynamic content

5. Click **"Save"** (top right)

### 1.4 Copy the Flow URL

1. After saving, click back on **"When an HTTP request is received"** step
2. Copy the **HTTP POST URL** (it looks like):
   ```
   https://prod-xx.westus.logic.azure.com:443/workflows/abc123.../triggers/manual/paths/invoke?...
   ```
3. Save this URL - you'll need it for configuration

---

## Step 2: Configure CAB Agent (5 minutes)

### 2.1 Update .env File

Add the Power Automate URL to your `.env` file:

```bash
# Power Automate Configuration (optional - for personal DM notifications)
POWER_AUTOMATE_URL=https://prod-xx.westus.logic.azure.com:443/workflows/YOUR_FLOW_URL_HERE
```

### 2.2 Verify Configuration

The code changes are already in place:
- ✅ `src/utils/config.py` - Config added
- ✅ `src/services/event_processor.py` - Notification function added
- ✅ Both webhook (channel) and Power Automate (personal) work together

---

## Step 3: Test the Setup (2 minutes)

### 3.1 Update Test Script

Edit `test_power_automate.py` and change the email:

```python
payload = {
    "user_email": "YOUR.EMAIL@company.com",  # CHANGE THIS
    "cr_id": "CR2579597",
    "title": "Test Database Migration",
    "from_state": "Pending CAB",
    "to_state": "Approved",
    "cr_link": "https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597"
}
```

### 3.2 Run Test

```bash
python test_power_automate.py
```

**Expected output:**
```
Sending test notification to Power Automate...
Flow URL: https://prod-xx...
Recipient: your.email@company.com
CR Link: https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597

✅ Success! Check your Teams for personal message from Flow bot.
```

### 3.3 Check Teams

You should receive a personal message from **Flow bot** with:
- CR ID and title
- Status change (Pending CAB → Approved)
- **Clickable link** to view CR in Azure DevOps

---

## Step 4: How It Works

### Architecture

```
CR State Change
    ↓
Event Processor detects change
    ↓
    ├─→ Teams Webhook → Channel notification (everyone sees)
    │
    └─→ Power Automate → Personal DM (only creator sees)
                         with clickable CR link
```

### Notification Flow

1. **Polling service** detects CR state change (every 5 minutes)
2. **Event processor** checks if notification should be sent
3. **Two notifications sent simultaneously:**
   - **Channel (webhook)**: Broadcast to Teams channel with "View CR" button
   - **Personal (Power Automate)**: DM to CR creator with clickable link
4. Both include the CR link: `https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/{work_item_id}`

---

## What You Get

### Teams Channel Notification (Webhook)
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
│ [View CR in Azure DevOps] ← Clickable button   │
└─────────────────────────────────────────────────┘
```

### Personal Teams Message (Power Automate)
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

## Customization

### Change Message Format

Edit the Power Automate flow message template:

**Simple version:**
```
🔔 CR [cr_id] is now [to_state]
View: [cr_link]
```

**Detailed version:**
```
🔔 CR Status Update

CR ID: [cr_id]
Title: [title]
Previous: [from_state]
Current: [to_state]
Creator: [user_email]

View CR: [cr_link]
```

### Add Conditional Formatting

In Power Automate, add a **Condition** step before the Teams message:

```
If to_state equals "Approved"
  → Send green message with ✅
If to_state equals "Rejected"
  → Send red message with ❌
```

### Add Approval Actions

Add **Approval** action in Power Automate:
1. After HTTP trigger, add **"Start and wait for an approval"**
2. Send approval to manager
3. Based on response, update CR in Azure DevOps

---

## Troubleshooting

### Issue: "Flow not triggering"

**Check:**
1. Flow is turned **ON** (toggle in Power Automate)
2. `POWER_AUTOMATE_URL` is correct in `.env`
3. No typos in the URL
4. Run `test_power_automate.py` to verify

**Debug:**
- Go to Power Automate → Your flow → **Run history**
- Check for errors or failed runs

### Issue: "User not receiving message"

**Check:**
1. User email is correct
2. User has Teams access
3. User has interacted with Flow bot before (send test message first)
4. Check Flow run history for delivery status

**Solution:**
- Have user send a message to Flow bot first
- Or change to **"Post to channel"** instead of **"Post to user"**

### Issue: "Link not clickable"

**Check:**
1. Message format uses Markdown: `[Text](URL)`
2. URL is complete (includes `https://`)
3. Teams supports Markdown links

**Alternative:**
- Use plain URL: Just paste the link without Markdown
- Teams will auto-detect and make it clickable

### Issue: "Wrong CR link"

**Check:**
1. `.env` has correct values:
   - `AZURE_DEVOPS_SERVER_URL=https://tfs.realpage.com/tfs`
   - `AZURE_DEVOPS_COLLECTION=Realpage`
   - `AZURE_DEVOPS_PROJECT=Change_Management`
2. CR ID format is correct (e.g., "CR2579597" → work item "2579597")

**Test:**
```python
from src.utils.config import Config
print(Config.get_work_item_url("2579597"))
# Should output: https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597
```

---

## Advanced: Add More Fields

### Update Flow Schema

Add more fields to the JSON schema:

```json
{
  "user_email": "john.doe@company.com",
  "cr_id": "CR2579597",
  "title": "Database Migration",
  "from_state": "Pending CAB",
  "to_state": "Approved",
  "cr_link": "https://...",
  "priority": "High",
  "risk_level": "Medium",
  "scheduled_date": "2025-11-10"
}
```

### Update event_processor.py

```python
payload = {
    "user_email": user_email,
    "cr_id": cr_id,
    "title": title,
    "from_state": from_state,
    "to_state": to_state,
    "cr_link": cr_link,
    "priority": cr_details.get("priority", "N/A"),
    "risk_level": cr_details.get("risk_level", "N/A"),
    "scheduled_date": cr_details.get("scheduled_start_date", "N/A")
}
```

### Update Flow Message

```
🔔 CR Status Update

CR ID: [cr_id]
Title: [title]
Priority: [priority]
Risk: [risk_level]
Scheduled: [scheduled_date]

Status: [from_state] → [to_state]

[View CR]([cr_link])
```

---

## Cost

| Component | Cost |
|-----------|------|
| Power Automate | $0 (included with Office 365) |
| Teams | $0 (included) |
| Flow bot messages | $0 (unlimited) |
| **Total** | **$0** |

---

## Summary

✅ **What you now have:**
- Channel notifications (webhook) for team awareness
- Personal DMs (Power Automate) for CR creators
- Clickable links to view CRs in Azure DevOps
- No Azure Bot Service subscription needed
- Zero additional cost

✅ **Next steps:**
1. Configure Power Automate flow (10 min)
2. Add `POWER_AUTOMATE_URL` to `.env`
3. Test with `test_power_automate.py`
4. Start polling service and enjoy notifications!

---

## References

- Main documentation: `docs/NON_AZURE_IMPLEMENTATION.md`
- Webhook setup: `WEBHOOK_SETUP.md` (if exists)
- Test script: `test_power_automate.py`
- Configuration: `.env.template`
