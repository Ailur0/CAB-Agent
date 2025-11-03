"""Test email service functionality."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.email_service import email_service


def test_email_configuration():
    """Test email service configuration."""
    print("\n" + "=" * 60)
    print("TEST: Email Service Configuration")
    print("=" * 60)
    
    print(f"\nSMTP Server: {email_service.smtp_server}")
    print(f"SMTP Port: {email_service.smtp_port}")
    print(f"Use SSL: {email_service.use_ssl}")
    print(f"Username: {email_service.username}")
    print(f"From Email: {email_service.from_email}")
    print(f"From Name: {email_service.from_name}")
    print(f"Is Active: {email_service.is_active}")
    print(f"Max Retries: {email_service.max_retries}")
    print(f"Retry Delay: {email_service.retry_delay_minutes} minutes")


def test_send_simple_email():
    """Test sending a simple email."""
    print("\n" + "=" * 60)
    print("TEST: Send Simple Email")
    print("=" * 60)
    
    # Replace with your test email
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipped - no email provided")
        return
    
    result = email_service.send_email(
        to_email=test_email,
        subject="CAB Agent - Test Email",
        body_html="""
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email from the CAB Agent system.</p>
            <p>If you received this, the email service is working correctly!</p>
        </body>
        </html>
        """,
        body_text="This is a test email from the CAB Agent system.",
    )
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")


def test_send_pir_request_email():
    """Test sending a PIR request email."""
    print("\n" + "=" * 60)
    print("TEST: Send PIR Request Email")
    print("=" * 60)
    
    # Replace with your test email
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipped - no email provided")
        return
    
    result = email_service.send_pir_request_email(
        reviewer_email=test_email,
        cr_id="CR12345",
        cr_title="Test Database Migration",
        requester="test.user@example.com",
    )
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")


def test_send_pir_reminder_email():
    """Test sending a PIR reminder email."""
    print("\n" + "=" * 60)
    print("TEST: Send PIR Reminder Email")
    print("=" * 60)
    
    # Replace with your test email
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipped - no email provided")
        return
    
    result = email_service.send_pir_reminder_email(
        reviewer_email=test_email,
        cr_id="CR12345",
        cr_title="Test Database Migration",
        hours_pending=25,
    )
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")


def test_send_pir_escalation_email():
    """Test sending a PIR escalation email."""
    print("\n" + "=" * 60)
    print("TEST: Send PIR Escalation Email")
    print("=" * 60)
    
    # Replace with your test email
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipped - no email provided")
        return
    
    result = email_service.send_pir_escalation_email(
        manager_email=test_email,
        cr_id="CR12345",
        cr_title="Test Database Migration",
        requester="test.user@example.com",
        hours_overdue=50,
    )
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")


def test_send_pir_completion_email():
    """Test sending a PIR completion email."""
    print("\n" + "=" * 60)
    print("TEST: Send PIR Completion Email")
    print("=" * 60)
    
    # Replace with your test email
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("Skipped - no email provided")
        return
    
    result = email_service.send_pir_completion_email(
        requester_email=test_email,
        cr_id="CR12345",
        cr_title="Test Database Migration",
        reviewer="reviewer@example.com",
        comments="All tests passed. No issues found during implementation.",
    )
    
    print(f"\nResult: {result}")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")


def run_all_tests():
    """Run all email service tests."""
    print("\n" + "=" * 70)
    print("EMAIL SERVICE TEST SUITE")
    print("=" * 70)
    
    test_email_configuration()
    
    print("\n" + "=" * 70)
    print("INTERACTIVE EMAIL TESTS")
    print("=" * 70)
    print("\nThe following tests will send actual emails.")
    print("Enter your email address to receive test emails.")
    print("Press Enter to skip any test.")
    
    test_send_simple_email()
    test_send_pir_request_email()
    test_send_pir_reminder_email()
    test_send_pir_escalation_email()
    test_send_pir_completion_email()
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
