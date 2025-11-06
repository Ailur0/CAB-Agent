# CAB Agent – Non-Azure Implementation Playbook

> **Goal:** Deliver proactive change-request notifications and self-service CR support **without relying on any Azure subscription services.**
>
> This playbook consolidates every viable architecture path, their requirements, and how they fit together so you can deploy the CAB Agent entirely on-premises or with non-Azure SaaS offerings.

---

## 1. Core Capabilities (Always Required)

| Capability | Description | Recommended Non-Azure Choice | Notes |
|------------|-------------|-------------------------------|-------|
| Change Request Source | System of record for CRs | **Azure DevOps Server / TFS** (existing) | Requires PAT; works without Azure subscription |
| Data Store | Persist CRs, state history, notifications | **SQL Server Express**, **MySQL**, or **SQLite** | All run locally; SQL Server pairs well with SSMS |
| Initial Sync | Populate DB with historical CRs | `sync_azure_devops.py` | Works with any database back-end |
| Incremental Updates | Detect CR changes | `polling_service.py` (APScheduler) | Polling interval configurable |
| Event Rules | Determine when to notify | `EVENT_RULES` in `event_processor.py` | Independent of delivery channel |
| Notification Layer | Deliver messages to users | Multiple options (Sections 2 & 3) | Mix-and-match |
| Observability | Logs + simple metrics | Python logging + database tables | Easily extend with ELK/Prometheus |

---

## 2. Notification & Messaging Options (No Azure Subscription Needed)

### 2.1 Teams Channel Notifications (Current Baseline)
- **Mechanism:** Microsoft Teams **Incoming Webhook**
- **Audience:** Entire channel (e.g., CAB Notifications)
- **Files Involved:** `src/services/teams_webhook.py`, `.env` (`TEAMS_WEBHOOK_URL`)
- **Cost:** Free (included with Teams)
- **Pros:** Easiest to set up, 10-minute configuration, zero code changes in Teams
- **Cons:** Broadcast only; cannot DM individuals; no interactive cards

### 2.2 Teams Personal Messages via Power Automate ⭐ RECOMMENDED
- **Mechanism:** `When an HTTP request is received` flow → `Post as Flow bot to a user`
- **Audience:** Individual CR creator / owner
- **Requirements:** Office 365 with Power Automate (included in most plans)
- **Implementation:**
  1. Create HTTP-triggered flow in Power Automate (10 min setup)
  2. Add `POWER_AUTOMATE_URL` to `.env`
  3. Flow automatically posts DM via Flow bot (no Azure Bot Service needed)
  4. Includes clickable CR links: `https://tfs.realpage.com/tfs/Realpage/Change_Management/_workitems/edit/{id}`
- **Pros:** True proactive personal notifications; clickable CR links; still Azure-free; free with Office 365
- **Cons:** Flow bot branding; depends on Power Automate licensing
- **Setup Guide:** See `docs/POWER_AUTOMATE_SETUP.md` for complete instructions

### 2.3 Teams Emails with Flow (Fallback)
- Same HTTP-trigger flow can send **Outlook emails** instead of Teams DMs
- Good for users not actively on Teams

### 2.4 Slack Bot
- **Mechanism:** Slack App + Bot Token (`slack_sdk`)
- **Audience:** Channels or users (DMs)
- **Implementation Outline:**
  - Create Slack app (free)
  - Use bot token in `.env`
  - Replace Teams notifier with Slack notifier module
- **Pros:** Robust API, great developer experience, unlimited DMs
- **Cons:** Requires Slack workspace (free tier okay, but message history limit)

### 2.5 Slack Incoming Webhook (Broadcast Only)
- Equivalent to Teams webhook for channels
- Minimal setup, ideal if Slack already in use

### 2.6 Discord Bot
- **Mechanism:** `discord.py`
- **Audience:** Channels or DMs
- **Pros:** Totally free, great for engineering teams already on Discord
- **Cons:** Less enterprise-oriented, but simple to implement

### 2.7 Email (SMTP)
- **Mechanism:** Company SMTP relay or services like SendGrid (free tier)
- **Use Cases:** Audit trail, fallback when chat fails, stakeholders who prefer email
- **Implementation:** `smtplib` or vendor SDK

### 2.8 SMS / WhatsApp (Twilio / MessageBird)
- **Mechanism:** REST API to SMS gateway
- **Pros:** Reach on-call engineers instantly
- **Cons:** Paid per message; use selectively

### 2.9 Web Dashboard Notifications
- **Mechanism:** Web UI with real-time feed (Flask/FastAPI + polling/SignalR)
- **Pros:** Permanent historical view, custom filters
- **Cons:** Requires building UI; complements chat instead of replacing it

---

## 3. User Query Interfaces (No Azure Bot Framework)

| Channel | Description | How to Implement | Difficulty |
|---------|-------------|------------------|------------|
| Web Dashboard | React/Vue + FastAPI backend querying SQL | Build REST endpoints using existing DB models | ⭐⭐☆ |
| Command-Line Tool | `query_cr.py CR12345` | Direct DB/API lookups, prints table/text | ⭐☆☆ |
| Slack/Discord Bot | Same as notification bot; add slash commands or DM handlers | Use Slack Events API / Discord commands | ⭐⭐☆ |
| Power Automate Chat | Trigger Flow bot manually; call CAB API | Low code, limited flexibility | ⭐⭐☆ |
| Email Query | Users email special inbox; script replies with CR data | Parse emails + auto-response | ⭐⭐⭐ |
| Agentspace / Dialogflow CX | Conversational AI on GCP | Requires webhook integration | ⭐⭐⭐ |

> **Tip:** You can combine channel notifications (Teams webhook) with user queries in Slack or web dashboard. The database + polling layers are channel-agnostic.

---

## 4. AI & Automation Options Without Azure

| Option | Description | Cost | Notes |
|--------|-------------|------|-------|
| **OpenAI API (direct)** | Use `openai` Python client for GPT-4o / GPT-4o-mini | ~$5-10/mo typical | Already integrated (`test_agent_direct.py`) |
| **OpenAI via Azure?** | *Not needed* | — | Avoid to stay Azure-free |
| **Open-source LLM (Local)** | Ollama, LM Studio, or Hugging Face models | Free (compute cost only) | Works offline; integrate via REST server |
| **Google Vertex AI / Agentspace** | Dialogflow CX / Agentspace for conversational UI | Pay-as-you-go (~$10/mo) | No Azure dependency; requires GCP project |
| **Anthropic Claude** | Claude API for specialized workflows | Pay-per-use | Alternative to OpenAI |
| **No LLM (Rules only)** | Pure deterministic workflows | Free | Use event rules + templates |

> You can toggle between AI providers using an abstraction layer (e.g., `src/services/ai_client.py`) that reads provider type from `.env`.

---

## 5. Hosting & Infrastructure (Azure-Free)

| Deployment Target | Description | Notes |
|-------------------|-------------|-------|
| **Local Windows Workstation** | Run polling + scripts as background tasks | Ideal for PoC and small teams |
| **On-Prem Windows Server** | Scheduled tasks / NSSM-run services | Stable long-running environment |
| **Docker on Windows/Linux** | Use `docker-compose.yml` provided | Add SQL Server, Redis containers |
| **Internal Kubernetes** | Optional; run services as deployments | No dependency on Azure Kubernetes |
| **Hybrid** | Poller on-prem, notifications via SaaS (Slack, Power Automate) | Most flexible option |

> **Reminder:** Azure DevOps Server / TFS already lives on-prem; all API calls stay within corporate network when running locally.

---

## 6. Database Choices (No Azure SQL)

| Database | Pros | Cons | How to Configure |
|----------|------|------|------------------|
| **SQL Server Express** | Free, integrates with SSMS, strong tooling | Windows-focused | `DATABASE_URL=mssql+pyodbc://localhost/cab_agent?...` |
| **MySQL / MariaDB** | Cross-platform, mature | Need MySQL Workbench | `mysql+pymysql://user:pass@localhost/cab_agent` |
| **PostgreSQL** | Advanced features, PL/pgSQL | Requires pgAdmin | `postgresql+psycopg2://user:pass@localhost/cab_agent` |
| **SQLite** | Zero setup, file-based | Not great for multi-user concurrency | `sqlite:///cab_agent.db` |

The ORM layer (`src/database.py`) works with any SQLAlchemy-compatible backend by changing only the connection string.

---

## 7. Implementation Recipes (Choose Your Path)

### Recipe A – "Minimum Viable" (Channel Notifications Only)
1. Install SQL Server Express
2. Configure `.env` with database + PAT + `TEAMS_WEBHOOK_URL`
3. Run `python setup_database.py`
4. Run `python sync_azure_devops.py --limit 100`
5. Start polling: `python start_polling.py`
6. Result: Channel-level change notifications

### Recipe B – "Personal + Channel" (Teams + Power Automate)
1. Complete Recipe A
2. Create Power Automate HTTP-trigger flow
3. Add `POWER_AUTOMATE_URL` to `.env`
4. Implement `send_power_automate_notification()`
5. Result: Channel broadcast + individual DMs

### Recipe C – "Slack-First"
1. Register Slack app (Bot + incoming webhook)
2. Add Slack notifier module (channel + DM)
3. Replace Teams webhook calls
4. Optional: Add slash commands for CR lookup

### Recipe D – "Email-First"
1. Configure SMTP credentials in `.env`
2. Implement `send_email_notification()` in event processor
3. Use email as primary + Teams webhook as secondary

### Recipe E – "Self-Service Dashboard"
1. Build REST API (FastAPI) for CR queries using DB models
2. Create simple React or plain HTML dashboard
3. Optional: Add login via company SSO (no Azure AD required if using ADFS)
4. Keep background polling for data freshness

### Recipe F – "Conversational AI Without Azure"
1. Choose AI provider (OpenAI direct, Vertex AI, Anthropic)
2. Update `test_agent_direct.py` to call provider
3. Wire AI responses to Slack/Discord/Web UI
4. Use Power Automate for proactive channel notifications

---

## 8. Decision Matrix

| Requirement | Recommended Stack |
|-------------|-------------------|
| **Fastest deployment** | Recipe A (Teams Webhook only) |
| **Personal notifications** | Recipe B (Teams + Power Automate) |
| **Non-Microsoft shop** | Recipe C (Slack) or Discord |
| **Executives need email** | Recipe D (Email) |
| **Self-service portal** | Recipe E (Web dashboard) |
| **Conversational AI** | Recipe F + Slack/Discord UI |
| **Offline / Air-gapped** | SQLite + Email (no SaaS dependencies) |

---

## 9. Roadmap Without Azure

1. **Phase 0 – Foundation**
   - Database setup (SQL Server Express)
   - Initial + incremental sync running on schedule
   - Event processor logging

2. **Phase 1 – Channel Awareness**
   - Teams webhook notifications live
   - Dashboard or email digest for audit

3. **Phase 2 – Personal Engagement**
   - Power Automate DMs or Slack/Discord DMs
   - Opt-in preferences stored in DB (`user_notification_preferences` table)

4. **Phase 3 – Conversational Interface**
   - Choose chat platform (Slack, Discord, web)
   - Expose query endpoints or AI assistant

5. **Phase 4 – Advanced Automation**
   - Autonomic actions (auto-approve low-risk CRs)
   - Machine-learning risk predictions (local models)
   - KPI dashboards for CAB performance

---

## 10. Key Takeaways

- 🟢 Azure subscription is **not required** for any mission-critical component.
- 🔀 Notification, AI, and UI layers are modular—swap Teams for Slack, webhook for Power Automate, or OpenAI for on-prem models with isolated changes.
- 💰 Baseline ongoing cost can stay around **$5–10/month** (OpenAI usage) or $0 if using local models.
- 🧱 Database + polling service form the constant core across all variants.
- 🔄 Power Automate, Slack bots, email, and dashboards can be **added incrementally** without re-architecting.

---

## 11. Next Steps Checklist

- [ ] Decide on notification channels (Teams channel, personal DM, Slack, Email)
- [ ] Confirm database engine (SQL Server Express vs MySQL vs SQLite)
- [ ] Configure `.env` for chosen stack
- [ ] Update `event_processor.py` to call relevant notifier(s)
- [ ] Validate with test scripts (`test_webhook.py`, Power Automate test, etc.)
- [ ] Document internal runbooks for operations team

---

## 12. Reference Files

- `WEBHOOK_SETUP.md` – Teams webhook setup & testing
- `POWER_AUTOMATE_GUIDE.md` – Add personal DMs via Flow
- `SETUP_GUIDE.md` – Database + sync instructions
- `ARCHITECTURE.md` – Platform-wide diagrams (Mermaid)
- `docs/EMAIL_INTEGRATION.md` – SMTP & email template guidance
- `README_MOE.md` – Scalable multi-agent architecture

> Keep this playbook updated as you add new channels or automation paths. The CAB Agent is intentionally modular—feel free to plug in any tooling that fits your team’s reality **without ever needing Azure Bot Service or other subscription-only Azure resources.**
