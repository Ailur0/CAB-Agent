"""Setup SQL Server database for CAB Agent."""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

load_dotenv()

from sqlalchemy import text

from src.database import init_database, get_session
from src.utils import get_logger

logger = get_logger(__name__)


def setup():
    """Initialize database and create tables."""
    print("\n" + "=" * 70)
    print("CAB AGENT - DATABASE SETUP (SQL Server)")
    print("=" * 70)
    
    print("\n🔧 Setting up SQL Server database...")
    print("\nPrerequisites:")
    print("  1. SQL Server is installed and running")
    print("  2. Database 'cab_agent' exists (or will be created)")
    print("  3. You have appropriate permissions")
    print("  4. ODBC Driver 17 for SQL Server is installed")
    
    input("\nPress Enter to continue...")
    
    try:
        # Create tables
        engine = init_database()
        print("\n✅ Database tables created successfully!")
        
        # Test connection
        session = get_session()
        try:
            result = session.execute(text("SELECT 1 AS test")).fetchone()
            print(f"✅ Database connection verified! Result: {result}")
        finally:
            session.close()
        
        print("\n✨ Setup complete! Database is ready.")
        print("\nTables created:")
        print("  - change_requests")
        print("  - cr_state_history")
        print("  - user_conversation_references")
        print("  - cr_notifications_sent")
        
        print("\n📊 You can view these tables in SSMS:")
        print("  1. Open SQL Server Management Studio")
        print("  2. Connect to localhost")
        print("  3. Expand Databases → cab_agent → Tables")
        
    except Exception as e:
        print(f"\n❌ Error setting up database: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure SQL Server is running")
        print("  2. Create database manually in SSMS:")
        print("     CREATE DATABASE cab_agent;")
        print("  3. Check DATABASE_URL in .env file")
        print("  4. Verify Windows Authentication is enabled")
        print("  5. Install ODBC Driver 17:")
        print("     https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
        raise


if __name__ == "__main__":
    setup()
