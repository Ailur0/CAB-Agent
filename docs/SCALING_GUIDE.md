# Scaling Guide for 90,000+ Change Requests

## Overview

This guide explains how to deploy and scale the CAB Agent to handle 90,000+ Change Requests efficiently.

## Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Optional: Celery for distributed processing
pip install celery redis

# Optional: Monitoring
pip install psutil flower
```

### 2. Start Redis (Required for Celery)

```bash
# Using Docker
docker run -d -p 6379:6379 redis

# Or install Redis locally
# Windows: https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# Mac: brew install redis
```

### 3. Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit .env and set:
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
BATCH_SIZE=100
MAX_WORKERS=10
```

### 4. Start Services

```bash
# Terminal 1: Start Celery Workers
celery -A src.services.task_queue worker --loglevel=info --concurrency=10

# Terminal 2: Start Celery Beat (Scheduler)
celery -A src.services.task_queue beat --loglevel=info

# Terminal 3: Start Bot/API
python src/bot/app.py

# Terminal 4 (Optional): Monitor with Flower
celery -A src.services.task_queue flower
# Open http://localhost:5555
```

## Scaling Strategies

### Small Scale (< 10,000 CRs)

**Configuration:**
```bash
BATCH_SIZE=50
MAX_WORKERS=5
INCREMENTAL_SYNC_MINUTES=10
```

**Infrastructure:**
- Single server
- Local Redis
- 2-3 Celery workers
- SQL Server Express

**Expected Performance:**
- Full sync: ~5 minutes
- Incremental sync: ~30 seconds
- Notifications: < 1 second delay

### Medium Scale (10,000 - 50,000 CRs)

**Configuration:**
```bash
BATCH_SIZE=100
MAX_WORKERS=10
INCREMENTAL_SYNC_MINUTES=5
```

**Infrastructure:**
- 1 App Server (4 CPU, 8GB RAM)
- Redis (standalone)
- 5-10 Celery workers
- SQL Server Standard

**Expected Performance:**
- Full sync: ~10 minutes
- Incremental sync: ~1 minute
- Notifications: < 2 second delay

### Large Scale (50,000 - 100,000 CRs)

**Configuration:**
```bash
BATCH_SIZE=200
MAX_WORKERS=20
INCREMENTAL_SYNC_MINUTES=5
FULL_SYNC_HOURS=168  # Weekly
```

**Infrastructure:**
- 2-3 App Servers (8 CPU, 16GB RAM each)
- Redis Cluster (HA)
- 20-30 Celery workers (distributed)
- SQL Server Enterprise / Azure SQL

**Expected Performance:**
- Full sync: ~15 minutes
- Incremental sync: ~2 minutes
- Notifications: < 3 second delay

### Enterprise Scale (100,000+ CRs)

**Configuration:**
```bash
BATCH_SIZE=500
MAX_WORKERS=50
INCREMENTAL_SYNC_MINUTES=3
FULL_SYNC_HOURS=168
```

**Infrastructure:**
- Load Balancer (Azure Load Balancer / AWS ALB)
- 5+ App Servers (16 CPU, 32GB RAM each)
- Redis Cluster (3+ nodes, HA)
- 50+ Celery workers (distributed across servers)
- Azure SQL / AWS RDS (Premium tier)
- Monitoring: Application Insights / CloudWatch

**Expected Performance:**
- Full sync: ~20 minutes
- Incremental sync: ~3 minutes
- Notifications: < 5 second delay

## Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes for fast queries
CREATE INDEX idx_cr_state ON change_requests(state);
CREATE INDEX idx_cr_created_by_email ON change_requests(created_by_email);
CREATE INDEX idx_cr_assigned_to ON change_requests(assigned_to);
CREATE INDEX idx_cr_last_synced ON change_requests(last_synced_at);
CREATE INDEX idx_cr_created_at ON change_requests(created_at);
CREATE INDEX idx_history_cr_id ON cr_state_history(cr_id);
CREATE INDEX idx_history_changed_at ON cr_state_history(changed_at);

-- Enable query result caching
-- SQL Server: Automatic in most cases
-- Consider columnstore indexes for analytics
```

### 2. Connection Pooling

```python
# In database.py, configure connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # Connections to keep open
    max_overflow=40,       # Additional connections if needed
    pool_pre_ping=True,    # Verify connections before use
    pool_recycle=3600,     # Recycle connections after 1 hour
)
```

### 3. Batch Size Tuning

Test different batch sizes to find optimal performance:

```bash
# Test with different batch sizes
BATCH_SIZE=50   # Lower memory, slower
BATCH_SIZE=100  # Balanced (recommended)
BATCH_SIZE=200  # Higher memory, faster
BATCH_SIZE=500  # High memory, fastest (requires 16GB+ RAM)
```

### 4. Worker Tuning

```bash
# CPU-bound tasks: workers = CPU cores
celery worker --concurrency=8

# I/O-bound tasks (API calls): workers = 2-4x CPU cores
celery worker --concurrency=32

# Mixed workload: workers = 1.5-2x CPU cores
celery worker --concurrency=16
```

### 5. Redis Optimization

```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# For production, use Redis Cluster
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  --cluster-replicas 1
```

## Monitoring & Troubleshooting

### Health Check Endpoint

```python
# Add to your Flask/FastAPI app
from src.services.monitoring import get_health_status

@app.route('/health')
def health():
    return get_health_status()
```

### Monitor Celery Queue

```bash
# Check queue length
celery -A src.services.task_queue inspect active_queues

# Check active tasks
celery -A src.services.task_queue inspect active

# Check worker stats
celery -A src.services.task_queue inspect stats
```

### Common Issues

#### Issue: Sync is too slow
**Solution:**
- Increase `BATCH_SIZE`
- Increase `MAX_WORKERS`
- Add more Celery workers
- Check database query performance

#### Issue: High memory usage
**Solution:**
- Decrease `BATCH_SIZE`
- Decrease `MAX_WORKERS`
- Enable worker max tasks per child:
  ```bash
  celery worker --max-tasks-per-child=1000
  ```

#### Issue: API rate limiting
**Solution:**
- Increase delay between batches
- Reduce `MAX_WORKERS`
- Contact Azure DevOps support for higher limits

#### Issue: Database connection errors
**Solution:**
- Increase connection pool size
- Enable connection pooling
- Check database server resources
- Add read replicas for queries

#### Issue: Notifications delayed
**Solution:**
- Add more Celery workers
- Check Redis performance
- Optimize notification queries
- Use async notification processing

## Cost Optimization

### Azure Deployment

**Small Scale (~$200/month):**
- 1x B2s VM (2 CPU, 4GB) - $30/month
- Azure SQL Basic - $5/month
- Azure Cache for Redis Basic - $15/month
- Storage - $10/month
- Bandwidth - $20/month

**Medium Scale (~$500/month):**
- 2x D2s_v3 VM (2 CPU, 8GB) - $140/month
- Azure SQL S2 - $150/month
- Azure Cache for Redis Standard - $75/month
- Storage - $20/month
- Bandwidth - $50/month

**Large Scale (~$2000/month):**
- 5x D4s_v3 VM (4 CPU, 16GB) - $700/month
- Azure SQL S6 - $900/month
- Azure Cache for Redis Premium - $250/month
- Storage - $50/month
- Bandwidth - $100/month

### AWS Deployment

**Small Scale (~$180/month):**
- 1x t3.medium - $30/month
- RDS db.t3.small - $25/month
- ElastiCache t3.small - $15/month
- Storage - $10/month
- Data Transfer - $20/month

**Medium Scale (~$450/month):**
- 2x t3.large - $120/month
- RDS db.m5.large - $140/month
- ElastiCache m5.large - $70/month
- Storage - $20/month
- Data Transfer - $50/month

**Large Scale (~$1800/month):**
- 5x m5.xlarge - $600/month
- RDS db.m5.2xlarge - $700/month
- ElastiCache r5.large - $200/month
- Storage - $50/month
- Data Transfer - $100/month

## Deployment Checklist

### Pre-Deployment
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Redis installed and configured
- [ ] Environment variables set
- [ ] SSL certificates configured
- [ ] Firewall rules configured
- [ ] Backup strategy defined

### Deployment
- [ ] Deploy database schema
- [ ] Deploy application code
- [ ] Start Redis
- [ ] Start Celery workers
- [ ] Start Celery beat
- [ ] Start application server
- [ ] Verify health endpoint
- [ ] Run initial full sync

### Post-Deployment
- [ ] Monitor sync performance
- [ ] Monitor queue depth
- [ ] Monitor error rates
- [ ] Set up alerts
- [ ] Configure log aggregation
- [ ] Document runbooks
- [ ] Train operations team

## Maintenance

### Daily
- Check health dashboard
- Monitor error logs
- Verify sync completion

### Weekly
- Review performance metrics
- Check disk space
- Review failed tasks
- Optimize slow queries

### Monthly
- Database maintenance (reindex, update stats)
- Review and archive old logs
- Capacity planning review
- Security updates

### Quarterly
- Performance testing
- Disaster recovery drill
- Cost optimization review
- Architecture review

## Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Check health: `curl http://localhost:8000/health`
3. Check Celery: `celery -A src.services.task_queue inspect stats`
4. Review documentation: `ARCHITECTURE.md`
