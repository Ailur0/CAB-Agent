"""Monitoring and health check system for the CAB Agent."""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database import get_session, ChangeRequest, CRStateHistory
from src.utils import get_logger

logger = get_logger(__name__)


class HealthMonitor:
    """
    Health monitoring system for the CAB Agent.
    
    Monitors:
    - Database connectivity
    - Sync service health
    - Task queue health
    - System resources (CPU, memory)
    - Agent performance
    """
    
    def __init__(self):
        self.last_check = None
        self.health_history = []
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            session = get_session()
            
            # Test query
            start_time = datetime.utcnow()
            count = session.query(ChangeRequest).count()
            query_time = (datetime.utcnow() - start_time).total_seconds()
            
            session.close()
            
            return {
                "status": "healthy",
                "total_crs": count,
                "query_time_seconds": query_time,
                "responsive": query_time < 5.0,  # Should respond within 5 seconds
            }
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    def check_sync_service_health(self) -> Dict[str, Any]:
        """Check sync service health and metrics."""
        try:
            from src.services.scalable_polling_service import scalable_polling_service
            
            metrics = scalable_polling_service.get_metrics()
            
            # Check if last sync was recent
            last_sync = metrics.get("last_sync_time")
            if last_sync:
                last_sync_dt = datetime.fromisoformat(last_sync)
                time_since_sync = (datetime.utcnow() - last_sync_dt).total_seconds()
                is_recent = time_since_sync < 600  # Within last 10 minutes
            else:
                is_recent = False
                time_since_sync = None
            
            return {
                "status": "healthy" if is_recent else "degraded",
                "last_sync_time": last_sync,
                "time_since_sync_seconds": time_since_sync,
                "total_synced": metrics.get("total_synced", 0),
                "total_updated": metrics.get("total_updated", 0),
                "total_errors": metrics.get("total_errors", 0),
                "last_sync_duration": metrics.get("last_sync_duration", 0),
            }
        except Exception as e:
            logger.error("Sync service health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    def check_task_queue_health(self) -> Dict[str, Any]:
        """Check Celery task queue health."""
        try:
            from src.services.task_queue import celery_app, CELERY_AVAILABLE
            
            if not CELERY_AVAILABLE:
                return {
                    "status": "not_configured",
                    "message": "Celery not installed",
                }
            
            # Check if workers are active
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            
            if not active_workers:
                return {
                    "status": "degraded",
                    "message": "No active workers",
                    "active_workers": 0,
                }
            
            # Get queue stats
            stats = inspect.stats()
            
            return {
                "status": "healthy",
                "active_workers": len(active_workers),
                "worker_stats": stats,
            }
        except Exception as e:
            logger.error("Task queue health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine health status
            status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "critical"
            elif cpu_percent > 75 or memory.percent > 75 or disk.percent > 80:
                status = "degraded"
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024 ** 3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 ** 3),
            }
        except Exception as e:
            logger.error("System resource check failed", error=str(e))
            return {
                "status": "unknown",
                "error": str(e),
            }
    
    def check_recent_activity(self) -> Dict[str, Any]:
        """Check recent CR activity."""
        try:
            session = get_session()
            
            # CRs created in last 24 hours
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_crs = (
                session.query(ChangeRequest)
                .filter(ChangeRequest.created_at >= yesterday)
                .count()
            )
            
            # State changes in last 24 hours
            recent_changes = (
                session.query(CRStateHistory)
                .filter(CRStateHistory.changed_at >= yesterday)
                .count()
            )
            
            # CRs by state
            states = {}
            state_counts = (
                session.query(ChangeRequest.state, session.query(ChangeRequest).filter_by(state=ChangeRequest.state).count())
                .group_by(ChangeRequest.state)
                .all()
            )
            
            session.close()
            
            return {
                "status": "healthy",
                "recent_crs_24h": recent_crs,
                "recent_changes_24h": recent_changes,
            }
        except Exception as e:
            logger.error("Recent activity check failed", error=str(e))
            return {
                "status": "unknown",
                "error": str(e),
            }
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        logger.info("Running health check")
        
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": self.check_database_health(),
            "sync_service": self.check_sync_service_health(),
            "task_queue": self.check_task_queue_health(),
            "system_resources": self.check_system_resources(),
            "recent_activity": self.check_recent_activity(),
        }
        
        # Determine overall status
        statuses = [
            health_report["database"]["status"],
            health_report["sync_service"]["status"],
            health_report["system_resources"]["status"],
        ]
        
        if "unhealthy" in statuses or "critical" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        health_report["overall_status"] = overall_status
        
        # Store in history
        self.health_history.append(health_report)
        if len(self.health_history) > 100:  # Keep last 100 checks
            self.health_history.pop(0)
        
        self.last_check = datetime.utcnow()
        
        logger.info("Health check complete", overall_status=overall_status)
        return health_report
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of health status."""
        if not self.last_check:
            return {"status": "no_data", "message": "No health checks performed yet"}
        
        latest = self.health_history[-1] if self.health_history else None
        
        if not latest:
            return {"status": "no_data", "message": "No health data available"}
        
        return {
            "overall_status": latest["overall_status"],
            "last_check": latest["timestamp"],
            "database_status": latest["database"]["status"],
            "sync_service_status": latest["sync_service"]["status"],
            "task_queue_status": latest["task_queue"]["status"],
            "system_resources_status": latest["system_resources"]["status"],
            "total_crs": latest["database"].get("total_crs", 0),
            "cpu_percent": latest["system_resources"].get("cpu_percent", 0),
            "memory_percent": latest["system_resources"].get("memory_percent", 0),
        }


# Create global health monitor instance
health_monitor = HealthMonitor()


def get_health_status() -> Dict[str, Any]:
    """Get current health status (convenience function)."""
    return health_monitor.get_overall_health()


def get_health_summary() -> Dict[str, Any]:
    """Get health summary (convenience function)."""
    return health_monitor.get_health_summary()


if __name__ == "__main__":
    print("\n🏥 Health Monitoring System")
    print("=" * 60)
    
    print("\nRunning health check...")
    health = get_health_status()
    
    print(f"\n📊 Overall Status: {health['overall_status'].upper()}")
    print("\nComponent Health:")
    print(f"  • Database: {health['database']['status']}")
    print(f"  • Sync Service: {health['sync_service']['status']}")
    print(f"  • Task Queue: {health['task_queue']['status']}")
    print(f"  • System Resources: {health['system_resources']['status']}")
    
    print("\nSystem Resources:")
    print(f"  • CPU: {health['system_resources'].get('cpu_percent', 0):.1f}%")
    print(f"  • Memory: {health['system_resources'].get('memory_percent', 0):.1f}%")
    print(f"  • Disk: {health['system_resources'].get('disk_percent', 0):.1f}%")
    
    if health['database']['status'] == 'healthy':
        print(f"\nDatabase:")
        print(f"  • Total CRs: {health['database'].get('total_crs', 0):,}")
        print(f"  • Query Time: {health['database'].get('query_time_seconds', 0):.3f}s")
    
    print()
