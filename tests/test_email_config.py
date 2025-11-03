"""Test email service configuration (non-interactive)."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.email_service import email_service


def test_email_configuration():
    """Test email service configuration."""
    print("\n" + "=" * 60)
    print("EMAIL SERVICE CONFIGURATION TEST")
    print("=" * 60)
    
    print(f"\n[OK] SMTP Configuration:")
    print(f"   Server: {email_service.smtp_server}")
    print(f"   Port: {email_service.smtp_port}")
    print(f"   Use SSL: {email_service.use_ssl}")
    print(f"   Username: {email_service.username}")
    print(f"   From Email: {email_service.from_email}")
    print(f"   From Name: {email_service.from_name}")
    
    print(f"\n[OK] Service Settings:")
    print(f"   Is Active: {email_service.is_active}")
    print(f"   Max Retries: {email_service.max_retries}")
    print(f"   Retry Delay: {email_service.retry_delay_minutes} minutes")
    
    # Validate configuration
    errors = []
    
    if not email_service.smtp_server:
        errors.append("SMTP_SERVER is not configured")
    
    if not email_service.smtp_port:
        errors.append("SMTP_PORT is not configured")
    
    if not email_service.from_email:
        errors.append("SMTP_FROM_EMAIL is not configured")
    
    if email_service.is_active and not email_service.username:
        print("\n[WARN] SMTP_USERNAME is not set (may be required for authentication)")
    
    if email_service.is_active and not email_service.password:
        print("\n[WARN] SMTP_PASSWORD is not set (may be required for authentication)")
    
    if errors:
        print("\n[ERROR] Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("\n[OK] Configuration is valid!")
        print("\nTo test email sending, use:")
        print("   python tests/test_email_service.py")
        print("\nOr send a test email programmatically:")
        print("   from src.utils.email_service import email_service")
        print("   email_service.send_email('your@email.com', 'Test', '<h1>Test</h1>')")
        return True


if __name__ == "__main__":
    success = test_email_configuration()
    sys.exit(0 if success else 1)
