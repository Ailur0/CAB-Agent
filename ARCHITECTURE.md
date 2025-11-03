# CAB Agent Architecture - Mixture of Experts (MoE)

## Overview

The CAB Agent uses a **Mixture of Experts (MoE)** architecture with specialized agents and a scalable polling system designed to handle **90,000+ Change Requests** efficiently.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  (Teams Bot, Web API, CLI)                                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Router Agent (MoE)                        │
│  • Analyzes user requests                                    │
│  • Routes to appropriate specialist agent                    │
│  • Coordinates multi-agent workflows                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
        ▼               ▼               ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ CR Mgmt      │ │ Validation   │ │ Approval     │ │ Notification │
│ Agent        │ │ Agent        │ │ Agent        │ │ Agent        │
│              │ │              │ │              │ │              │
│ • Create CR  │ │ • Validate   │ │ • Approvals  │ │ • Teams      │
│ • Update CR  │ │ • Conflicts  │ │ • Timeouts   │ │ • Email      │
│ • Query CR   │ │ • Calendar   │ │ • Escalation │ │ • Reminders  │
│ • History    │ │ • Compliance │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │               │               │              │
        └───────────────┴───────────────┴──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tools & Services Layer                    │
│  • Azure DevOps API                                          │
│  • Calendar API                                              │
│  • Database (SQL Server)                                     │
│  • Teams Notifications                                       │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Scalable Background Processing                  │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Scalable Polling Service                       │        │
│  │  • Batch processing (100 CRs/batch)             │        │
│  │  • Worker pool (10 parallel workers)            │        │
│  │  • Incremental sync (every 5 min)               │        │
│  │  • Full sync (weekly)                           │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Distributed Task Queue (Celery + Redis)        │        │
│  │  • Async task processing                        │        │
│  │  • Horizontal scaling                           │        │
│  │  • Retry logic                                  │        │
│  │  • Periodic tasks                               │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Health Monitoring                              │        │
│  │  • Database health                              │        │
│  │  • Service health                               │        │
│  │  • Resource monitoring                          │        │
│  │  • Metrics & alerts                             │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Mixture of Experts (MoE) Pattern

### Router Agent
The **Router Agent** is the main orchestrator that:
1. Analyzes incoming user requests
2. Determines which specialist agent(s) to use
3. Delegates tasks to appropriate experts
4. Coordinates multi-agent workflows
5. Synthesizes responses from multiple agents

### Specialist Agents

#### 1. CR Management Agent
**Expertise**: CRUD operations for Change Requests
- Create new CRs
- Update existing CRs
- Query CR details
- Retrieve CR history

#### 2. Validation Agent
**Expertise**: Compliance validation and conflict detection
- Validate CR completeness
- Check calendar conflicts
- Verify team availability
- Assess risk levels

#### 3. Approval Agent
**Expertise**: Approval workflows and timeout management
- Send approval requests
- Track approval status
- Handle timeouts
- Escalate to management

#### 4. PIR Agent
**Expertise**: Post-Implementation Review tracking
- Initiate PIR workflows
- Track PIR completion
- Send PIR reminders
- Escalate overdue PIRs

#### 5. Notification Agent
**Expertise**: Stakeholder communication
- Send Teams notifications
- Email notifications
- Approval requests
- Status updates
- Reminders

## Scalability for 90,000+ CRs

### Challenge
With 90,000+ CRs, the system must:
- Continuously monitor all CRs for changes
- Process updates in real-time
- Notify users promptly
- Avoid API rate limiting
- Minimize resource usage

### Solution: Multi-Layered Approach

#### 1. Scalable Polling Service
```python
# Features:
- Batch Processing: 100 CRs per batch
- Worker Pool: 10 parallel workers
- Incremental Sync: Every 5 minutes (only changed CRs)
- Full Sync: Weekly (all CRs for consistency)
- Rate Limiting: 1-second delay between batches
```

**How it works:**
- **Incremental Sync**: Queries only CRs updated in last 24 hours
- **Batch Processing**: Processes CRs in chunks to avoid memory overload
- **Parallel Workers**: Uses ThreadPoolExecutor for concurrent API calls
- **Smart Scheduling**: Frequent incremental syncs + periodic full syncs

**Performance:**
- 90,000 CRs ÷ 100 per batch = 900 batches
- 900 batches × 1 second delay = 15 minutes for full sync
- Incremental sync (changed CRs only) = 1-2 minutes

#### 2. Distributed Task Queue (Celery)
```python
# Features:
- Async Processing: Non-blocking task execution
- Horizontal Scaling: Add more workers as needed
- Retry Logic: Automatic retry with exponential backoff
- Periodic Tasks: Scheduled sync jobs
```

**How it works:**
- Tasks are queued in Redis
- Multiple Celery workers process tasks in parallel
- Each worker can handle multiple tasks concurrently
- Failed tasks are automatically retried

**Scaling:**
- Start with 5-10 workers
- Monitor queue length
- Add more workers if queue grows
- Can scale to 50+ workers across multiple machines

#### 3. Database Optimization
```sql
-- Indexes for fast queries
CREATE INDEX idx_cr_state ON change_requests(state);
CREATE INDEX idx_cr_created_by ON change_requests(created_by_email);
CREATE INDEX idx_cr_last_synced ON change_requests(last_synced_at);
CREATE INDEX idx_history_cr_id ON cr_state_history(cr_id);
```

**Optimizations:**
- Indexed columns for fast filtering
- Batch inserts/updates
- Connection pooling
- Query result caching

#### 4. Event-Driven Notifications
Instead of polling for every notification:
- Detect changes during sync
- Queue notification tasks asynchronously
- Process notifications in background
- Deduplicate notifications (prevent spam)

## Deployment Architecture

### Development
```
Single Machine:
- Router Agent + Specialist Agents
- Scalable Polling Service (local)
- SQLite/SQL Server (local)
- Redis (Docker)
- 1-2 Celery workers
```

### Production
```
Multi-Tier:
- Load Balancer
  ├─ App Server 1 (Router + Agents)
  ├─ App Server 2 (Router + Agents)
  └─ App Server 3 (Router + Agents)

- Background Processing
  ├─ Celery Worker Pool (10+ workers)
  ├─ Redis Cluster (HA)
  └─ Scheduler (Celery Beat)

- Data Layer
  ├─ SQL Server (Azure SQL / AWS RDS)
  └─ Redis Cache (Azure Cache / ElastiCache)

- Monitoring
  ├─ Health Check Endpoint
  ├─ Metrics Dashboard (Flower, Prometheus)
  └─ Alerting (PagerDuty, Slack)
```

## Request Flow Examples

### Example 1: Create CR
```
User: "Create a CR for database migration on Friday at 6pm"
  ↓
Router Agent: Analyzes request
  ↓
Router: Delegates to Validation Agent
  ↓
Validation Agent: Checks for conflicts
  ↓
Router: Delegates to CR Management Agent
  ↓
CR Management Agent: Creates CR in Azure DevOps
  ↓
Router: Synthesizes response
  ↓
User: "CR12345 created successfully"
```

### Example 2: Validate and Approve
```
User: "Validate and send approval for CR12345"
  ↓
Router Agent: Analyzes request (multi-step)
  ↓
Router: Delegates to Validation Agent
  ↓
Validation Agent: Validates CR compliance
  ↓
Router: Delegates to Approval Agent
  ↓
Approval Agent: Sends approval request
  ↓
Router: Synthesizes response
  ↓
User: "CR12345 validated. Approval request sent to manager@example.com"
```

### Example 3: Background Sync
```
Scheduler: Triggers incremental sync (every 5 min)
  ↓
Scalable Polling Service: Queries changed CRs
  ↓
Batch Processor: Splits into 100-CR batches
  ↓
Worker Pool: Fetches CR details in parallel
  ↓
Database: Updates CR states
  ↓
Event Processor: Detects state changes
  ↓
Notification Agent: Sends Teams notifications
  ↓
Users: Receive proactive notifications
```

## Configuration

### Environment Variables
```bash
# Azure DevOps
AZURE_DEVOPS_ORG=your-org
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_PAT=your-pat

# Database
DATABASE_URL=mssql+pyodbc://...

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Polling
BATCH_SIZE=100
MAX_WORKERS=10
INCREMENTAL_SYNC_MINUTES=5
FULL_SYNC_HOURS=168

# Monitoring
HEALTH_CHECK_INTERVAL=60
```

## Monitoring & Metrics

### Key Metrics
- **Sync Performance**: CRs synced per minute
- **Queue Depth**: Pending tasks in Celery queue
- **Error Rate**: Failed syncs / total syncs
- **Response Time**: API response times
- **Resource Usage**: CPU, memory, disk

### Health Checks
- Database connectivity
- Sync service status
- Task queue status
- System resources
- Recent activity

### Alerts
- Sync failures > 5%
- Queue depth > 1000
- CPU/Memory > 90%
- Database connection failures

## Best Practices

### For 90,000+ CRs
1. **Use Incremental Sync**: Only sync changed CRs frequently
2. **Batch Processing**: Process in chunks to avoid memory issues
3. **Parallel Workers**: Use worker pools for concurrent processing
4. **Rate Limiting**: Add delays to avoid API throttling
5. **Monitoring**: Track metrics and set up alerts
6. **Caching**: Cache frequently accessed data
7. **Indexing**: Ensure database indexes are optimized
8. **Horizontal Scaling**: Add more workers as needed

### For Agent Design
1. **Single Responsibility**: Each agent has one clear purpose
2. **Loose Coupling**: Agents communicate through router
3. **Error Handling**: Graceful degradation on failures
4. **Logging**: Comprehensive logging for debugging
5. **Testing**: Unit tests for each agent

## Future Enhancements

1. **Machine Learning**: Predict CR approval likelihood
2. **Auto-Scheduling**: Suggest optimal change windows
3. **Risk Scoring**: ML-based risk assessment
4. **Chatbot Integration**: Slack, Discord support
5. **Analytics Dashboard**: Real-time CR analytics
6. **Multi-Region**: Deploy across multiple regions
7. **Event Streaming**: Use Kafka for real-time events
