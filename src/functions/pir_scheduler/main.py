"""Scheduled function for PIR reminders and escalations."""

import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.utils import get_logger
from src.agents.pir_agent import check_pir_reminders, check_pir_escalations

logger = get_logger(__name__)


def pir_scheduler(request=None) -> Dict[str, Any]:
    """
    Scheduled function to check for PIR reminders and escalations.
    
    This function should be triggered by a scheduler (e.g., Cloud Scheduler, cron)
    every hour or as configured.
    
    Args:
        request: HTTP request object (for HTTP-triggered functions).
        
    Returns:
        Dictionary with execution status.
    """
    logger.info("PIR scheduler function triggered")
    
    try:
        # Check and send reminders
        reminder_result = check_pir_reminders()
        reminders_sent = reminder_result.get("reminders_sent", 0)
        
        # Check and send escalations
        escalation_result = check_pir_escalations()
        escalations_sent = escalation_result.get("escalations_sent", 0)
        
        logger.info(
            "PIR scheduler completed",
            reminders_sent=reminders_sent,
            escalations_sent=escalations_sent,
        )
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "reminders_sent": reminders_sent,
            "escalations_sent": escalations_sent,
        }
        
    except Exception as e:
        logger.error("Error in PIR scheduler function", error=str(e))
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


if __name__ == "__main__":
    print("\n⏰ PIR Scheduler Function")
    print("=" * 50)
    result = pir_scheduler()
    print(f"\nResult: {result}")
