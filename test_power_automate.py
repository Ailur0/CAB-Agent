"""Test Power Automate personal notification with CR link."""

import requests
from dotenv import load_dotenv
import os

load_dotenv()

flow_url = os.getenv("POWER_AUTOMATE_URL")

if not flow_url:
    print("❌ POWER_AUTOMATE_URL not configured in .env file")
    print("\nTo configure:")
    print("1. Create Power Automate flow (see docs/NON_AZURE_IMPLEMENTATION.md)")
    print("2. Add to .env: POWER_AUTOMATE_URL=https://prod-xx...")
    exit(1)

# Test payload with CR link
payload = {
    "user_email": "your.email@company.com",  # CHANGE THIS to your email
    "cr_id": "CR2579597",
    "title": "Test Database Migration",
    "from_state": "Pending CAB",
    "to_state": "Approved",
    "cr_link": "https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/2579597"
}

print("Sending test notification to Power Automate...")
print(f"Flow URL: {flow_url[:50]}...")
print(f"Recipient: {payload['user_email']}")
print(f"CR Link: {payload['cr_link']}\n")

response = requests.post(flow_url, json=payload)

if response.status_code == 202:
    print("✅ Success! Check your Teams for personal message from Flow bot.")
    print("\nThe message should include:")
    print("  - CR ID: CR2579597")
    print("  - Status change: Pending CAB → Approved")
    print("  - Clickable link to view CR in Azure DevOps")
else:
    print(f"❌ Failed: {response.status_code}")
    print(f"Response: {response.text}")
    print("\nTroubleshooting:")
    print("1. Verify flow URL is correct")
    print("2. Check flow is turned ON in Power Automate")
    print("3. Ensure user email is valid")
    print("4. Check flow run history for errors")
