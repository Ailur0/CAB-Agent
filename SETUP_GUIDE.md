# CAB Agent - Setup Guide (SQL Server)

## Architecture Overview

```
Azure DevOps API ←→ Polling Service ←→ SQL Server Database ←→ Teams Bot
                                              ↓
                                       Event Processor
                                              ↓
                                    Proactive Notifications
```

## Prerequisites

### 1. SQL Server
- **SQL Server Express** (free) or any SQL Server edition
- **SQL Server Management Studio (SSMS)** - You already have this!
- **ODBC Driver 17 for SQL Server**
  - Download: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### 2. Python
- Python 3.8 or higher
- pip package manager

### 3. Azure DevOps Access
- Personal Access Token (PAT) with Work Items read/write permissions

### 4. OpenAI API Key
- For AI/LLM functionality

---

## Phase 1: Database Setup (Start Here!)

### Step 1: Create Database in SSMS

```sql
-- Open SSMS and connect to localhost
-- Run this query:

CREATE DATABASE cab_agent;
GO

USE cab_agent;
GO
```

### Step 2: Configure Environment

1. Copy `.env.template` to `.env`:
   ```bash
   copy .env.template .env
   ```

2. Edit `.env` file:
   ```bash
   # SQL Server Database (Windows Authentication)
   DATABASE_URL=mssql+pyodbc://localhost/cab_agent?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

   # Azure DevOps
   AZURE_DEVOPS_SERVER_URL=https://tfs.realpage.com/tfs
   AZURE_DEVOPS_COLLECTION=Realpage
   AZURE_DEVOPS_PROJECT=Change_Management
   AZURE_DEVOPS_PAT=your_pat_token_here

   # OpenAI
   OPENAI_API_KEY=your_openai_key_here
   OPENAI_MODEL=gpt-4o
   ```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database

```bash
python setup_database.py
```

**Expected Output:**
```
======================================================================
CAB AGENT - DATABASE SETUP (SQL Server)
======================================================================

🔧 Setting up SQL Server database...
✅ Database tables created successfully!
✅ Database connection verified!

✨ Setup complete! Database is ready.

Tables created:
  - change_requests
  - cr_state_history
  - user_conversation_references
  - cr_notifications_sent
```

### Step 5: Verify in SSMS

```sql
-- In SSMS, run:
USE cab_agent;
GO

-- See all tables
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES;

-- Should show:
-- change_requests
-- cr_state_history
-- user_conversation_references
-- cr_notifications_sent
```

---

## Phase 2: Initial Data Sync

### Sync CRs from Azure DevOps

```bash
# Sync first 100 CRs (recommended for testing)
python sync_azure_devops.py --limit 100

# Or sync all CRs
python sync_azure_devops.py --all
```

**Expected Output:**
```
======================================================================
CAB AGENT - INITIAL DATABASE SYNC
======================================================================

📥 Fetching CRs from Azure DevOps...
✅ Found 247 CRs
   Limiting to first 100 CRs

💾 Syncing 100 CRs to database...
   [1/100] CR2579597 - ✅ Synced (Approved)
   [2/100] CR2579598 - ✅ Synced (Pending CAB)
   ...

======================================================================
SYNC COMPLETE
======================================================================
✅ Synced:  100
⏭️  Skipped: 0
❌ Errors:  0
📊 Total:   100
```

### Verify Data in SSMS

```sql
-- Check CR count
SELECT COUNT(*) AS total_crs FROM change_requests;

-- View some CRs
SELECT TOP 10 
    cr_id, 
    title, 
    state, 
    created_by_email,
    created_at
FROM change_requests
ORDER BY created_at DESC;

-- Check state distribution
SELECT 
    state, 
    COUNT(*) AS count
FROM change_requests
GROUP BY state
ORDER BY count DESC;
```

---

## Phase 3: Background Polling (Optional)

### Start Polling Service

Create `start_polling.py`:

```python
"""Start background polling service."""
import asyncio
from src.services.polling_service import start_polling_service

async def main():
    print("Starting polling service...")
    scheduler = start_polling_service(interval_minutes=5)
    
    print("Polling service running. Press Ctrl+C to stop.")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping polling service...")
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python start_polling.py
```

This will:
- Sync CRs every 5 minutes
- Detect state changes
- Log changes to `cr_state_history` table
- Trigger notifications (when Teams bot is configured)

---

## Phase 4: Teams Bot Setup (Later)

### Prerequisites
- Azure subscription
- Azure Bot Service registered
- Bot added to Teams

### Configuration

Add to `.env`:
```bash
MICROSOFT_APP_ID=your_bot_app_id
MICROSOFT_APP_PASSWORD=your_bot_app_password
AZURE_CLIENT_ID=your_azure_app_client_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_TENANT_ID=your_azure_tenant_id
```

### Start Bot

```bash
python -m src.bot.app
```

---

## Useful SQL Queries

### Check Recent Changes
```sql
SELECT TOP 20
    h.cr_id,
    h.field_name,
    h.old_value,
    h.new_value,
    h.changed_at
FROM cr_state_history h
ORDER BY h.changed_at DESC;
```

### Find CRs by State
```sql
SELECT cr_id, title, created_by_email, created_at
FROM change_requests
WHERE state = 'Pending CAB'
ORDER BY created_at DESC;
```

### Check Conversation References
```sql
SELECT 
    user_id,
    email,
    name,
    last_interaction_at
FROM user_conversation_references
ORDER BY last_interaction_at DESC;
```

### Check Sent Notifications
```sql
SELECT TOP 20
    cr_id,
    event_type,
    recipient_email,
    sent_at
FROM cr_notifications_sent
ORDER BY sent_at DESC;
```

---

## Troubleshooting

### Database Connection Issues

**Error:** "Can't open database"
```bash
# Solution: Create database manually in SSMS
CREATE DATABASE cab_agent;
```

**Error:** "Login failed for user"
```bash
# Solution: Use Windows Authentication
DATABASE_URL=mssql+pyodbc://localhost/cab_agent?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
```

**Error:** "ODBC Driver not found"
```bash
# Solution: Install ODBC Driver 17
# Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

### Azure DevOps Connection Issues

**Error:** "Authentication failed"
```bash
# Solution: Check your PAT token
# Generate new PAT: https://tfs.realpage.com/tfs/_usersSettings/tokens
```

**Error:** "No CRs found"
```bash
# Solution: Check project name and collection
AZURE_DEVOPS_PROJECT=Change_Management
AZURE_DEVOPS_COLLECTION=Realpage
```

---

## File Structure

```
CAB Agent/
├── .env                          # Your configuration (create from .env.template)
├── .env.template                 # Template for configuration
├── requirements.txt              # Python dependencies
├── setup_database.py             # Database initialization script
├── sync_azure_devops.py          # Initial sync script
├── test_agent_direct.py          # Test OpenAI agent
├── SETUP_GUIDE.md               # This file
│
├── src/
│   ├── database.py              # Database models (NEW)
│   ├── bot/                     # Teams bot
│   │   ├── app.py              # Bot server
│   │   ├── bot.py              # Bot logic
│   │   └── state/              # Conversation state
│   │       └── conversation_state_manager.py  # Now uses database!
│   ├── services/                # Background services (NEW)
│   │   ├── polling_service.py  # Sync service
│   │   └── event_processor.py  # Notification logic
│   ├── tools/                   # Azure DevOps tools
│   │   └── azure_devops_tool.py
│   └── utils/                   # Utilities
│       └── config.py
│
└── tests/                       # Tests
```

---

## What's Next?

1. ✅ **Phase 1 Complete:** Database setup and initial sync
2. ⏳ **Phase 2:** Background polling (optional)
3. ⏳ **Phase 3:** Azure Bot configuration
4. ⏳ **Phase 4:** Proactive notifications

---

## Support

For issues or questions:
1. Check SSMS for database connectivity
2. Verify `.env` configuration
3. Check logs in console output
4. Review error messages carefully
