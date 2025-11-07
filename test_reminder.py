"""Test CR reminder notification via Power Automate."""

import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

load_dotenv()

flow_url = os.getenv("POWER_AUTOMATE_URL")

if not flow_url:
    print("❌ POWER_AUTOMATE_URL not configured in .env file")
    print("\nTo configure:")
    print("1. Create Power Automate flow (see docs/REMINDER_SERVICE_SETUP.md)")
    print("2. Add to .env: POWER_AUTOMATE_URL=https://prod-xx...")
    exit(1)

# Calculate scheduled start time (15 minutes from now)
scheduled_start = datetime.utcnow() + timedelta(minutes=15)
scheduled_start_str = scheduled_start.strftime("%Y-%m-%d %H:%M UTC")

# Test payload for reminder
payload = {
    "user_email": "your.email@company.com",  # CHANGE THIS to your email
    "cr_id": "CR2579597",
    "title": "Test Database Migration",
    "scheduled_start": scheduled_start_str,
    "current_state": "Approved",
    "cr_link": "https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597",
    "notification_type": "reminder_15min"
}

print("=" * 70)
print("CAB AGENT - REMINDER NOTIFICATION TEST")
print("=" * 70)
print("\nSending test reminder to Power Automate...")
print(f"\n📧 Recipient: {payload['user_email']}")
print(f"🔔 CR ID: {payload['cr_id']}")
print(f"⏰ Scheduled Start: {payload['scheduled_start']}")
print(f"🔗 CR Link: {payload['cr_link']}")
print(f"\n🌐 Flow URL: {flow_url[:50]}...\n")

response = requests.post(flow_url, json=payload)

print("=" * 70)
if response.status_code == 202:
    print("✅ SUCCESS!")
    print("=" * 70)
    print("\n📱 Check your Teams for a personal message from Flow bot.")
    print("\nThe message should include:")
    print("  ⏰ Reminder that CR starts in 15 minutes")
    print("  📋 CR ID: CR2579597")
    print("  📝 Title: Test Database Migration")
    print("  🕐 Scheduled Start: " + scheduled_start_str)
    print("  📊 Current Status: Approved")
    print("  🔗 Clickable link to update CR status")
    print("\n💡 If you don't see it:")
    print("  1. Check Power Automate run history")
    print("  2. Verify user_email matches your Teams account")
    print("  3. Ensure flow is turned ON")
else:
    print("❌ FAILED")
    print("=" * 70)
    print(f"\n❌ Status Code: {response.status_code}")
    print(f"📄 Response: {response.text}\n")
    print("Troubleshooting:")
    print("  1. Verify POWER_AUTOMATE_URL is correct")
    print("  2. Check flow is turned ON in Power Automate")
    print("  3. Ensure flow owner has per-user license")
    print("  4. Verify JSON schema matches payload")
    print("  5. Check flow run history for detailed errors")

print("\n" + "=" * 70 + "\n")
