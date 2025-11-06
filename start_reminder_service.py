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
    print("CAB AGENT - CR REMINDER SERVICE")
    print("=" * 70)
    print("\n🔔 Starting 15-minute reminder service...")
    print("   - Checks every 5 minutes for CRs starting soon")
    print("   - Sends Power Automate notification to CR creator")
    print("   - Includes link to update CR status\n")
    
    try:
        # Start the reminder scheduler
        scheduler = start_reminder_service(check_interval_minutes=5)
        
        print("✅ Reminder service started successfully!")
        print("\n📋 Service details:")
        print("   - Check interval: 5 minutes")
        print("   - Reminder window: 15 minutes before start")
        print("   - Target states: Approved, Scheduled")
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
