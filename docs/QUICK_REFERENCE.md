# Quick Reference - CAB Agent MoE Architecture

## 🚀 Quick Start Commands

### Docker (Recommended)
```bash
docker-compose up -d              # Start all services
docker-compose ps                 # Check status
docker-compose logs -f app        # View logs
docker-compose down               # Stop all services
```

### Manual Start
```bash
# Terminal 1: Redis
docker run -d -p 6379:6379 redis

# Terminal 2: Celery Worker
celery -A src.services.task_queue worker --loglevel=info --concurrency=10

# Terminal 3: Celery Beat
celery -A src.services.task_queue beat --loglevel=info

# Terminal 4: App
python src/bot/app.py

# Terminal 5: Flower (Optional)
celery -A src.services.task_queue flower
```

## 🤖 Agent Quick Reference

### Router Agent (Main Orchestrator)
```python
from src.agents.router_agent import router_agent
router_agent.run("Your request here")
```

### Specialist Agents
```python
# CR Management
from src.agents.cr_management_agent import cr_management_agent
cr_management_agent.run("Create a CR for server patching")

# Validation
from src.agents.validation_agent import validation_agent
validation_agent.run("Validate CR12345 for compliance")

# Notification
from src.agents.notification_agent import notification_agent
notification_agent.run("Send notification to user@example.com about CR12345")

# Approval (existing)
from src.agents.approval_agent import approval_agent
approval_agent.run("Send approval request for CR12345")

# PIR (existing)
from src.agents.pir_agent import pir_agent
pir_agent.run("Initiate PIR for CR12345")
```

## 📊 Scalable Polling

### Start Polling Service
```python
from src.services.scalable_polling_service import scalable_polling_service

# Start with default settings
scheduler = scalable_polling_service.start()

# Custom settings
scheduler = scalable_polling_service.start(
    incremental_interval_minutes=5,
    full_sync_interval_hours=168
)

# Get metrics
metrics = scalable_polling_service.get_metrics()
```

### Manual Sync
```python
import asyncio
from src.services.scalable_polling_service import scalable_polling_service

# Incremental sync
asyncio.run(scalable_polling_service.incremental_sync())

# Full sync
asyncio.run(scalable_polling_service.full_sync())
```

## 🔄 Task Queue

### Submit Tasks
```python
from src.services.task_queue import (
    submit_cr_sync,
    submit_batch_sync,
    submit_notification
)

# Sync single CR
task = submit_cr_sync("CR12345")
result = task.get(timeout=30)

# Sync batch
task = submit_batch_sync(["CR12345", "CR12346", "CR12347"])
result = task.get(timeout=300)

# Send notification
task = submit_notification(
    cr_id="CR12345",
    notification_type="approval_request",
    recipient="manager@example.com",
    cr_title="Database Migration",
    requester="user@example.com"
)
```

### Monitor Tasks
```bash
# Celery CLI
celery -A src.services.task_queue inspect active
celery -A src.services.task_queue inspect stats
celery -A src.services.task_queue inspect active_queues

# Flower UI
http://localhost:5555
```

## 🏥 Health Monitoring

### Check Health
```python
from src.services.monitoring import get_health_status, get_health_summary

# Full health check
health = get_health_status()

# Quick summary
summary = get_health_summary()
```

### Health Endpoints
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/summary
```

## ⚙️ Configuration

### Environment Variables (.env)
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

# Google ADK
GOOGLE_API_KEY=your-key
ADK_MODEL=gemini-2.0-flash-exp
```

### Scaling Presets

**Small (< 10k CRs)**
```bash
BATCH_SIZE=50
MAX_WORKERS=5
INCREMENTAL_SYNC_MINUTES=10
```

**Medium (10k - 50k CRs)**
```bash
BATCH_SIZE=100
MAX_WORKERS=10
INCREMENTAL_SYNC_MINUTES=5
```

**Large (50k - 100k CRs)**
```bash
BATCH_SIZE=200
MAX_WORKERS=20
INCREMENTAL_SYNC_MINUTES=5
```

## 🐛 Troubleshooting

### Check Services
```bash
# Redis
redis-cli ping

# Database
python -c "from src.database import get_session; s = get_session(); print('DB OK')"

# Celery
celery -A src.services.task_queue inspect ping
```

### Common Fixes

**Celery not starting**
```bash
# Check Redis
redis-cli ping

# Check broker URL
echo $CELERY_BROKER_URL
```

**Slow sync**
```bash
# Increase batch size
export BATCH_SIZE=200

# Increase workers
export MAX_WORKERS=20
```

**High memory**
```bash
# Decrease batch size
export BATCH_SIZE=50

# Limit worker tasks
celery worker --max-tasks-per-child=1000
```

## 📈 Performance Metrics

### Expected Performance (90k CRs)

| Metric | Value |
|--------|-------|
| Full Sync Duration | 15-20 min |
| Incremental Sync | 1-2 min |
| Batch Size | 100 CRs |
| Workers | 10 parallel |
| Sync Frequency | 5 min |

### Monitoring Metrics
- Total CRs synced
- Sync duration
- Error rate
- CPU/Memory usage
- Queue depth
- Active workers

## 🔗 Useful URLs

| Service | URL |
|---------|-----|
| Application | http://localhost:8000 |
| Health Check | http://localhost:8000/health |
| Flower (Celery UI) | http://localhost:5555 |
| Redis | localhost:6379 |
| SQL Server | localhost:1433 |

## 📚 Documentation

- **ARCHITECTURE.md** - Detailed architecture
- **SCALING_GUIDE.md** - Scaling & deployment
- **README_MOE.md** - Getting started
- **IMPLEMENTATION_SUMMARY.md** - What was built
- **QUICK_REFERENCE.md** - This file

## 🎯 Common Tasks

### Deploy to Production
```bash
# 1. Configure environment
cp .env.template .env
# Edit .env

# 2. Build and start
docker-compose up -d

# 3. Verify
docker-compose ps
curl http://localhost:8000/health
```

### Scale Workers
```bash
# Scale to 20 workers
docker-compose up -d --scale celery_worker=20

# Or manually
celery -A src.services.task_queue worker --concurrency=20
```

### Monitor Performance
```bash
# Flower UI
open http://localhost:5555

# Health check
watch -n 5 'curl -s http://localhost:8000/health/summary | jq'

# Logs
docker-compose logs -f --tail=100 app
```

### Backup & Restore
```bash
# Backup database
docker exec cab_agent_db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P YourStrong@Passw0rd \
  -Q "BACKUP DATABASE CABAgent TO DISK='/var/opt/mssql/backup.bak'"

# Restore database
docker exec cab_agent_db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P YourStrong@Passw0rd \
  -Q "RESTORE DATABASE CABAgent FROM DISK='/var/opt/mssql/backup.bak'"
```

## 💡 Tips

1. **Start small**: Begin with default settings, tune based on metrics
2. **Monitor first**: Use Flower and health checks before scaling
3. **Incremental sync**: Faster than full sync for regular updates
4. **Batch size**: Balance between speed and memory
5. **Workers**: More workers = faster, but more resources
6. **Logs**: Check logs regularly for errors
7. **Alerts**: Set up alerts for critical metrics
8. **Backups**: Regular database backups

## 🆘 Emergency Commands

### Stop Everything
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart app
docker-compose restart celery_worker
```

### Clear Queue
```bash
celery -A src.services.task_queue purge
```

### Reset Database
```bash
python setup_database.py --reset
```

### Check Disk Space
```bash
df -h
docker system df
```
