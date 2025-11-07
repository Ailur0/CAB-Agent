"""Start the CR reminder service."""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

from src.services.reminder_service import start_reminder_service
from src.utils import get_logger

logger = get_logger(__name__)


async def main():
    """Main entry point for reminder service."""
    print("\n" + "=" * 70)
    print("CAB AGENT - COMPREHENSIVE CR REMINDER SERVICE")
    print("=" * 70)
    print("\n🔔 Starting multi-state reminder service...")
    print("   Flow 1: Approved State")
    print("     - 20min before start: Remind to transition to In Progress")
    print("     - At start time: Follow-up if still Approved")
    print("\n   Flow 2: In Progress State")
    print("     - 20min before end: Remind to fill results")
    print("     - At end time: Request status/extension if incomplete")
    print("\n   Flow 3: Awaiting PIR State")
    print("     - Daily reminders to complete PIR\n")
    
    try:
        # Start the reminder scheduler
        scheduler = start_reminder_service(check_interval_minutes=5)
        
        print("✅ Reminder service started successfully!")
        print("\n📋 Service details:")
        print("   - Approved/In Progress check: Every 5 minutes")
        print("   - Awaiting PIR check: Every hour")
        print("   - Notification method: Power Automate → Teams")
        print("\n💡 Press Ctrl+C to stop\n")
        
        # Keep the service running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping reminder service...")
        scheduler.shutdown()
        print("✅ Service stopped\n")
    except Exception as e:
        logger.error("Reminder service failed", error=str(e))
        print(f"\n❌ Error: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
