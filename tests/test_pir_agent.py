"""Tests for PIR agent functionality."""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.pir_agent import (
    identify_pir_reviewers,
    initiate_pir_tracking,
    check_pir_reminders,
    check_pir_escalations,
    complete_pir,
    get_pir_analytics,
    get_pending_pirs,
)
from src.database import init_database, get_session, PIRTracking


def test_identify_pir_reviewers():
    """Test PIR reviewer identification."""
    print("\n" + "=" * 60)
    print("TEST: Identify PIR Reviewers")
    print("=" * 60)
    
    # This would need a real CR ID from your Azure DevOps
    # For testing, you can use a mock CR ID
    result = identify_pir_reviewers("CR12345")
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Reviewers found: {result.get('count', 0)}")
    
    if result.get("reviewers"):
        for reviewer in result["reviewers"]:
            print(f"  - {reviewer.get('name')} ({reviewer.get('role')}): {reviewer.get('email')}")


def test_initiate_pir_tracking():
    """Test PIR tracking initiation."""
    print("\n" + "=" * 60)
    print("TEST: Initiate PIR Tracking")
    print("=" * 60)
    
    result = initiate_pir_tracking(
        cr_id="CR12345",
        cr_title="Test Database Migration",
        requester_email="test.user@example.com",
    )
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    
    if result.get("status") == "success":
        print(f"PIR ID: {result.get('pir_id')}")
        print(f"Reviewers notified: {result.get('reviewers_notified')}")
        print(f"Reminder due at: {result.get('reminder_due_at')}")
        print(f"Escalation due at: {result.get('escalation_due_at')}")


def test_get_pending_pirs():
    """Test getting pending PIRs."""
    print("\n" + "=" * 60)
    print("TEST: Get Pending PIRs")
    print("=" * 60)
    
    result = get_pending_pirs()
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Pending PIRs: {result.get('count', 0)}")
    
    if result.get("pending_pirs"):
        for pir in result["pending_pirs"]:
            print(f"\n  CR: {pir['cr_id']}")
            print(f"  Title: {pir['cr_title']}")
            print(f"  Status: {pir['status']}")
            print(f"  Hours pending: {pir['hours_pending']}")
            print(f"  Reminder sent: {pir['reminder_sent']}")
            print(f"  Escalation sent: {pir['escalation_sent']}")


def test_check_pir_reminders():
    """Test PIR reminder checking."""
    print("\n" + "=" * 60)
    print("TEST: Check PIR Reminders")
    print("=" * 60)
    
    result = check_pir_reminders()
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Reminders sent: {result.get('reminders_sent', 0)}")


def test_check_pir_escalations():
    """Test PIR escalation checking."""
    print("\n" + "=" * 60)
    print("TEST: Check PIR Escalations")
    print("=" * 60)
    
    result = check_pir_escalations()
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Escalations sent: {result.get('escalations_sent', 0)}")


def test_complete_pir():
    """Test PIR completion."""
    print("\n" + "=" * 60)
    print("TEST: Complete PIR")
    print("=" * 60)
    
    result = complete_pir(
        cr_id="CR12345",
        reviewer_email="reviewer@example.com",
        comments="All tests passed. No issues found during implementation.",
    )
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    
    if result.get("status") == "success":
        print(f"Completed by: {result.get('completed_by')}")
        print(f"Completion time: {result.get('completion_time_hours')} hours")


def test_get_pir_analytics():
    """Test PIR analytics."""
    print("\n" + "=" * 60)
    print("TEST: Get PIR Analytics (Last 30 Days)")
    print("=" * 60)
    
    result = get_pir_analytics(days=30)
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    
    if result.get("status") == "success":
        print(f"\nPIR Metrics:")
        print(f"  Total PIRs: {result.get('total_pirs')}")
        print(f"  Completed: {result.get('completed')}")
        print(f"  Pending: {result.get('pending')}")
        print(f"  Escalated: {result.get('escalated')}")
        print(f"  Completion rate: {result.get('completion_rate')}%")
        print(f"  Avg completion time: {result.get('avg_completion_time_hours')} hours")
        print(f"  SLA compliance rate: {result.get('sla_compliance_rate')}%")
        print(f"  Within SLA count: {result.get('within_sla_count')}")


def create_test_pir_data():
    """Create test PIR data for testing."""
    print("\n" + "=" * 60)
    print("Creating Test PIR Data")
    print("=" * 60)
    
    session = get_session()
    
    try:
        # Create a test PIR that needs reminder
        pir1 = PIRTracking(
            cr_id="CR99901",
            cr_title="Test CR - Needs Reminder",
            requester_email="user1@example.com",
            status="pending",
            initiated_at=datetime.utcnow() - timedelta(hours=25),
            reminder_due_at=datetime.utcnow() - timedelta(hours=1),
            escalation_due_at=datetime.utcnow() + timedelta(hours=23),
            reminder_sent=0,
            escalation_sent=0,
            reviewer_count=2,
        )
        
        # Create a test PIR that needs escalation
        pir2 = PIRTracking(
            cr_id="CR99902",
            cr_title="Test CR - Needs Escalation",
            requester_email="user2@example.com",
            status="pending",
            initiated_at=datetime.utcnow() - timedelta(hours=50),
            reminder_due_at=datetime.utcnow() - timedelta(hours=26),
            escalation_due_at=datetime.utcnow() - timedelta(hours=2),
            reminder_sent=1,
            reminder_sent_at=datetime.utcnow() - timedelta(hours=26),
            escalation_sent=0,
            reviewer_count=2,
        )
        
        # Create a completed PIR
        pir3 = PIRTracking(
            cr_id="CR99903",
            cr_title="Test CR - Completed",
            requester_email="user3@example.com",
            status="completed",
            initiated_at=datetime.utcnow() - timedelta(hours=20),
            reminder_due_at=datetime.utcnow() + timedelta(hours=4),
            escalation_due_at=datetime.utcnow() + timedelta(hours=28),
            reminder_sent=0,
            escalation_sent=0,
            completed_at=datetime.utcnow() - timedelta(hours=2),
            completed_by="reviewer@example.com",
            completion_time_hours=18,
            reviewer_count=2,
        )
        
        session.add(pir1)
        session.add(pir2)
        session.add(pir3)
        session.commit()
        
        print("\n✅ Test PIR data created successfully!")
        print(f"  - CR99901: Needs reminder")
        print(f"  - CR99902: Needs escalation")
        print(f"  - CR99903: Completed")
        
    except Exception as e:
        print(f"\n❌ Error creating test data: {e}")
        session.rollback()
    finally:
        session.close()


def cleanup_test_data():
    """Clean up test PIR data."""
    print("\n" + "=" * 60)
    print("Cleaning Up Test Data")
    print("=" * 60)
    
    session = get_session()
    
    try:
        # Delete test PIRs
        session.query(PIRTracking).filter(
            PIRTracking.cr_id.in_(["CR99901", "CR99902", "CR99903", "CR12345"])
        ).delete(synchronize_session=False)
        
        session.commit()
        print("\n✅ Test data cleaned up successfully!")
        
    except Exception as e:
        print(f"\n❌ Error cleaning up test data: {e}")
        session.rollback()
    finally:
        session.close()


def run_all_tests():
    """Run all PIR agent tests."""
    print("\n" + "=" * 70)
    print("PIR AGENT TEST SUITE")
    print("=" * 70)
    
    # Initialize database
    print("\nInitializing database...")
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database may already exist: {e}")
    
    # Create test data
    create_test_pir_data()
    
    # Run tests
    test_get_pending_pirs()
    test_check_pir_reminders()
    test_check_pir_escalations()
    test_get_pir_analytics()
    
    # Note: These tests require actual Azure DevOps integration
    # test_identify_pir_reviewers()
    # test_initiate_pir_tracking()
    # test_complete_pir()
    
    # Cleanup
    cleanup_test_data()
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
