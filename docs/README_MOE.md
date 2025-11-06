# CAB Agent - Mixture of Experts Architecture

## 🎯 Overview

The CAB Agent now uses a **Mixture of Experts (MoE)** architecture with specialized AI agents and scalable infrastructure designed to handle **90,000+ Change Requests** efficiently.

## 🏗️ Architecture Highlights

### Mixture of Experts Pattern
- **Router Agent**: Intelligently routes requests to specialist agents
- **5 Specialist Agents**: CR Management, Validation, Approval, PIR, Notification
- **Multi-Agent Coordination**: Complex workflows handled by multiple agents

### Scalability Features
- **Batch Processing**: Process 100-500 CRs per batch
- **Worker Pools**: 10-50 parallel workers
- **Incremental Sync**: Only sync changed CRs (every 5 min)
- **Full Sync**: Complete sync weekly for consistency
- **Distributed Tasks**: Celery + Redis for horizontal scaling

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone and configure
git clone <repo-url>
cd CAB-Agent
cp .env.template .env
# Edit .env with your credentials

# 2. Start all services
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f app

# 5. Access Flower (Celery monitoring)
# Open http://localhost:5555
```

### Option 2: Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis
docker run -d -p 6379:6379 redis

# 3. Setup database
python setup_database.py

# 4. Start services (separate terminals)
# Terminal 1: Celery Worker
celery -A src.services.task_queue worker --loglevel=info --concurrency=10

# Terminal 2: Celery Beat (Scheduler)
celery -A src.services.task_queue beat --loglevel=info

# Terminal 3: Application
python src/bot/app.py

# Terminal 4: Flower (Optional)
celery -A src.services.task_queue flower
```

## 🤖 Specialist Agents

### 1. Router Agent
**Purpose**: Main orchestrator that routes requests to specialists

**Example Usage**:
```python
from src.agents.router_agent import router_agent

response = router_agent.run("Create a CR for database migration on Friday at 6pm")
print(response.text)
```

### 2. CR Management Agent
**Purpose**: CRUD operations for Change Requests

**Capabilities**:
- Create new CRs
- Update existing CRs
- Query CR details
- Retrieve CR history

**Example**:
```python
from src.agents.cr_management_agent import cr_management_agent

response = cr_management_agent.run("Create a CR for server patching")
```

### 3. Validation Agent
**Purpose**: Compliance validation and conflict detection

**Capabilities**:
- Validate CR completeness
- Check calendar conflicts
- Verify team availability
- Assess risk levels

**Example**:
```python
from src.agents.validation_agent import validation_agent

response = validation_agent.run("Validate CR12345 for compliance")
```

### 4. Approval Agent
**Purpose**: Approval workflows and timeout management

**Capabilities**:
- Send approval requests
- Track approval status
- Handle timeouts
- Escalate to management

**Example**:
```python
from src.agents.approval_agent import approval_agent

response = approval_agent.run("Send approval request for CR12345 to manager@example.com")
```

### 5. PIR Agent
**Purpose**: Post-Implementation Review tracking

**Capabilities**:
- Initiate PIR workflows
- Track PIR completion
- Send PIR reminders
- Escalate overdue PIRs

### 6. Notification Agent
**Purpose**: Stakeholder communication

**Capabilities**:
- Send Teams notifications
- Email notifications
- Approval requests
- Status updates

## 📊 Scalable Polling Service

### How It Works

```python
from src.services.scalable_polling_service import scalable_polling_service

# Start the service
scheduler = scalable_polling_service.start(
    incremental_interval_minutes=5,  # Incremental sync every 5 min
    full_sync_interval_hours=168,    # Full sync weekly
)

# Get metrics
metrics = scalable_polling_service.get_metrics()
print(f"Total synced: {metrics['total_synced']}")
print(f"Last sync duration: {metrics['last_sync_duration']}s")
```

### Performance for 90,000 CRs

| Sync Type | Frequency | Duration | CRs Processed |
|-----------|-----------|----------|---------------|
| Incremental | 5 minutes | 1-2 min | ~500-1000 (changed) |
| Full | Weekly | 15-20 min | 90,000 (all) |

### Configuration

```bash
# .env
BATCH_SIZE=100              # CRs per batch
MAX_WORKERS=10              # Parallel workers
INCREMENTAL_SYNC_MINUTES=5  # Incremental sync interval
FULL_SYNC_HOURS=168         # Full sync interval (weekly)
```

## 🔄 Distributed Task Queue

### Celery Tasks

```python
from src.services.task_queue import submit_cr_sync, submit_notification

# Sync a single CR asynchronously
task = submit_cr_sync("CR12345")
result = task.get(timeout=30)

# Send notification asynchronously
task = submit_notification(
    cr_id="CR12345",
    notification_type="approval_request",
    recipient="manager@example.com",
    cr_title="Database Migration",
    requester="user@example.com"
)
```

### Monitoring with Flower

```bash
# Start Flower
celery -A src.services.task_queue flower

# Open browser
http://localhost:5555
```

**Features**:
- Real-time task monitoring
- Worker statistics
- Task history
- Queue depth
- Success/failure rates

## 🏥 Health Monitoring

```python
from src.services.monitoring import get_health_status, get_health_summary

# Full health check
health = get_health_status()
print(f"Overall status: {health['overall_status']}")
print(f"Database: {health['database']['status']}")
print(f"Sync service: {health['sync_service']['status']}")

# Quick summary
summary = get_health_summary()
print(f"Total CRs: {summary['total_crs']}")
print(f"CPU: {summary['cpu_percent']}%")
print(f"Memory: {summary['memory_percent']}%")
```

### Health Check Endpoint

```python
# Add to your web app
from flask import Flask, jsonify
from src.services.monitoring import get_health_status

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify(get_health_status())

@app.route('/health/summary')
def health_summary():
    return jsonify(get_health_summary())
```

## 📈 Scaling Guide

### Small Scale (< 10,000 CRs)
- 1 server (4 CPU, 8GB RAM)
- 2-3 Celery workers
- Batch size: 50
- Cost: ~$200/month

### Medium Scale (10,000 - 50,000 CRs)
- 2 servers (8 CPU, 16GB RAM each)
- 5-10 Celery workers
- Batch size: 100
- Cost: ~$500/month

### Large Scale (50,000 - 100,000 CRs)
- 5 servers (16 CPU, 32GB RAM each)
- 20-30 Celery workers
- Batch size: 200
- Cost: ~$2000/month

See [SCALING_GUIDE.md](SCALING_GUIDE.md) for detailed scaling instructions.

## 🔧 Configuration

### Environment Variables

```bash
# Azure DevOps
AZURE_DEVOPS_ORG=your-org
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_PAT=your-personal-access-token

# Database
DATABASE_URL=mssql+pyodbc://sa:password@localhost:1433/CABAgent?driver=ODBC+Driver+18+for+SQL+Server

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Google ADK
GOOGLE_API_KEY=your-google-api-key
ADK_MODEL=gemini-2.0-flash-exp

# Polling Configuration
BATCH_SIZE=100
MAX_WORKERS=10
INCREMENTAL_SYNC_MINUTES=5
FULL_SYNC_HOURS=168

# Teams
TEAMS_WEBHOOK_URL=your-teams-webhook-url
```

## 📚 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture documentation
- [SCALING_GUIDE.md](SCALING_GUIDE.md) - Scaling and deployment guide
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Initial setup instructions

## 🧪 Testing

### Test Individual Agents

```python
# Test Router Agent
python -c "from src.agents.router_agent import router_agent; print(router_agent.run('What is the status of CR12345?').text)"

# Test CR Management Agent
python -c "from src.agents.cr_management_agent import cr_management_agent; print(cr_management_agent.run('Get details for CR12345').text)"

# Test Validation Agent
python -c "from src.agents.validation_agent import validation_agent; print(validation_agent.run('Validate CR12345').text)"
```

### Test Polling Service

```python
# Test incremental sync
python -c "from src.services.scalable_polling_service import scalable_polling_service; import asyncio; asyncio.run(scalable_polling_service.incremental_sync())"

# Test full sync
python -c "from src.services.scalable_polling_service import scalable_polling_service; import asyncio; asyncio.run(scalable_polling_service.full_sync())"
```

### Test Health Monitoring

```bash
python src/services/monitoring.py
```

## 🚨 Monitoring & Alerts

### Key Metrics to Monitor

1. **Sync Performance**
   - CRs synced per minute
   - Sync duration
   - Error rate

2. **Queue Depth**
   - Pending tasks
   - Active workers
   - Failed tasks

3. **System Resources**
   - CPU usage
   - Memory usage
   - Disk space

4. **Database Performance**
   - Query response time
   - Connection pool usage
   - Deadlocks

### Setting Up Alerts

```python
# Example: Alert if error rate > 5%
from src.services.monitoring import health_monitor

health = health_monitor.get_overall_health()
error_rate = health['sync_service']['total_errors'] / max(health['sync_service']['total_synced'], 1)

if error_rate > 0.05:
    # Send alert
    print(f"⚠️ High error rate: {error_rate*100:.1f}%")
```

## 🔄 Workflow Examples

### Example 1: Create and Validate CR

```python
from src.agents.router_agent import router_agent

# Router automatically coordinates multiple agents
response = router_agent.run(
    "Create a CR for database migration on Friday at 6pm and validate it for conflicts"
)
print(response.text)
```

**What happens**:
1. Router analyzes request
2. Delegates to Validation Agent (check conflicts)
3. Delegates to CR Management Agent (create CR)
4. Synthesizes response

### Example 2: Approve CR

```python
from src.agents.router_agent import router_agent

response = router_agent.run(
    "Send approval request for CR12345 to manager@example.com"
)
print(response.text)
```

**What happens**:
1. Router delegates to Approval Agent
2. Approval Agent sends notification
3. Tracks approval status
4. Returns confirmation

### Example 3: Background Sync

```
Scheduler triggers incremental sync (every 5 min)
  ↓
Scalable Polling Service queries changed CRs
  ↓
Batch Processor splits into 100-CR batches
  ↓
Worker Pool fetches CR details in parallel
  ↓
Database updates CR states
  ↓
Event Processor detects state changes
  ↓
Notification Agent sends Teams notifications
  ↓
Users receive proactive notifications
```

## 🛠️ Troubleshooting

### Common Issues

**Issue**: Celery workers not starting
```bash
# Check Redis connection
redis-cli ping

# Check Celery configuration
celery -A src.services.task_queue inspect ping
```

**Issue**: Slow sync performance
```bash
# Increase batch size
export BATCH_SIZE=200

# Increase workers
export MAX_WORKERS=20

# Check database indexes
python -c "from src.database import engine; print(engine.execute('SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(\'change_requests\')').fetchall())"
```

**Issue**: High memory usage
```bash
# Decrease batch size
export BATCH_SIZE=50

# Limit worker tasks
celery -A src.services.task_queue worker --max-tasks-per-child=1000
```

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f app`
2. Check health: `curl http://localhost:8000/health`
3. Check Celery: `celery -A src.services.task_queue inspect stats`
4. Review documentation: [ARCHITECTURE.md](ARCHITECTURE.md)

## 🎉 What's New

### Mixture of Experts Architecture
- ✅ Router Agent for intelligent request routing
- ✅ 5 specialized agents (CR Mgmt, Validation, Approval, PIR, Notification)
- ✅ Multi-agent coordination for complex workflows

### Scalability for 90,000+ CRs
- ✅ Batch processing (100-500 CRs per batch)
- ✅ Worker pools (10-50 parallel workers)
- ✅ Incremental sync (only changed CRs)
- ✅ Full sync (weekly for consistency)
- ✅ Distributed task queue (Celery + Redis)

### Monitoring & Health Checks
- ✅ Health monitoring system
- ✅ Metrics tracking
- ✅ Flower UI for Celery monitoring
- ✅ Resource monitoring (CPU, memory, disk)

### DevOps
- ✅ Docker support
- ✅ Docker Compose for easy deployment
- ✅ Comprehensive documentation
- ✅ Scaling guide

## 📝 License

[Your License Here]
