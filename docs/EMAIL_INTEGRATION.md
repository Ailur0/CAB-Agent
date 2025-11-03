# Email Integration for PIR Notifications

## Overview

The PIR system now supports **dual-channel notifications** via both Email (SMTP) and Microsoft Teams. Email is the primary notification channel with Teams as a backup.

## Configuration

### Email Settings in `.env`

Add these settings to your `.env` file:

```bash
# Email/SMTP Configuration
SMTP_SERVER=mail.realpage.com
SMTP_PORT=25
SMTP_USE_SSL=true
SMTP_USERNAME=bsamala
SMTP_PASSWORD=your_password_here
SMTP_FROM_EMAIL=bonagiri.anish@realpage.com
SMTP_FROM_NAME=CAB Agent System
EMAIL_IS_ACTIVE=true
EMAIL_MAX_RETRIES=3
EMAIL_RETRY_DELAY_MINUTES=5
```

### Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `SMTP_SERVER` | SMTP server hostname | mail.realpage.com |
| `SMTP_PORT` | SMTP server port | 25 |
| `SMTP_USE_SSL` | Use SSL/TLS encryption | true |
| `SMTP_USERNAME` | SMTP authentication username | - |
| `SMTP_PASSWORD` | SMTP authentication password | - |
| `SMTP_FROM_EMAIL` | Sender email address | - |
| `SMTP_FROM_NAME` | Sender display name | CAB Agent System |
| `EMAIL_IS_ACTIVE` | Enable/disable email sending | true |
| `EMAIL_MAX_RETRIES` | Max retry attempts on failure | 3 |
| `EMAIL_RETRY_DELAY_MINUTES` | Delay between retries | 5 |

## Email Templates

### 1. PIR Request Email

**Sent when:** CR moves to "Awaiting PIR" state

**Recipients:** PIR reviewers

**Content:**
- Change Request ID and title
- Requester information
- Instructions for completion
- 48-hour escalation warning

### 2. PIR Reminder Email

**Sent when:** 24 hours after PIR initiated (no completion)

**Recipients:** PIR reviewers

**Content:**
- CR details
- Hours pending
- Urgency indicators
- 24-hour escalation warning

### 3. PIR Escalation Email

**Sent when:** 48 hours after PIR initiated (no completion)

**Recipients:** Change Manager

**Content:**
- CR details
- Requester information
- Hours overdue
- Action required notice

### 4. PIR Completion Email

**Sent when:** PIR is completed

**Recipients:** Change requester

**Content:**
- CR details
- Reviewer information
- PIR comments
- Closure confirmation

## Email Service Architecture

### EmailService Class (`src/utils/email_service.py`)

**Core Methods:**
- `send_email()` - Generic email sending with retry logic
- `send_pir_request_email()` - PIR request notification
- `send_pir_reminder_email()` - PIR reminder notification
- `send_pir_escalation_email()` - PIR escalation notification
- `send_pir_completion_email()` - PIR completion notification

**Features:**
- HTML email templates with professional styling
- Automatic retry on SMTP failures
- SSL/TLS support
- CC and BCC support
- Plain text fallback

### Integration with PIR Agent

All PIR notification functions in `src/tools/notification_tool.py` now:
1. Send email via `EmailService`
2. Also send Teams notification (if available)
3. Return email result as primary status

## Testing

### Test Email Configuration

```bash
python tests/test_email_service.py
```

This will:
1. Display current email configuration
2. Prompt for test email address
3. Send sample emails for each notification type

### Manual Test

```python
from src.utils.email_service import email_service

# Test simple email
result = email_service.send_email(
    to_email="your.email@example.com",
    subject="Test Email",
    body_html="<h1>Test</h1><p>This is a test.</p>"
)

print(result)
```

### Test PIR Notification

```python
from src.tools import notify_pir_request

result = notify_pir_request(
    reviewer_email="reviewer@example.com",
    cr_id="CR12345",
    cr_title="Test CR",
    requester="requester@example.com"
)

print(result)
```

## Troubleshooting

### Emails Not Sending

**Check:**
1. `EMAIL_IS_ACTIVE=true` in `.env`
2. SMTP credentials are correct
3. SMTP server is accessible from your network
4. Firewall allows outbound SMTP connections

**View Logs:**
```bash
# Check logs for email errors
tail -f logs/app.log | grep -i email
```

### SMTP Authentication Errors

**Common Issues:**
- Incorrect username/password
- Account requires app-specific password
- Two-factor authentication enabled

**Solution:**
- Verify credentials with IT
- Use app-specific password if required
- Check SMTP server documentation

### SSL/TLS Errors

**Port 25:** Usually no SSL (set `SMTP_USE_SSL=false`)
**Port 465:** SMTP_SSL (set `SMTP_USE_SSL=true`)
**Port 587:** STARTTLS (set `SMTP_USE_SSL=true`)

### Retry Logic

If email fails, the system will:
1. Retry up to `EMAIL_MAX_RETRIES` times
2. Wait `EMAIL_RETRY_DELAY_MINUTES` between retries
3. Log each attempt
4. Return error if all retries fail

## Email vs Teams Notifications

| Feature | Email | Teams |
|---------|-------|-------|
| Delivery | SMTP | Bot/Webhook |
| Reliability | High | Medium |
| Formatting | HTML | Markdown |
| Attachments | Yes | Limited |
| Read Receipts | Optional | No |
| Conversation | Threading | Chat |

**Recommendation:** Use both channels for redundancy. Email is primary, Teams is backup.

## Security Best Practices

1. **Never commit passwords** to version control
2. **Use environment variables** for all credentials
3. **Enable SSL/TLS** when possible
4. **Rotate passwords** regularly
5. **Use app-specific passwords** for service accounts
6. **Monitor failed login attempts**
7. **Restrict SMTP relay** to authorized IPs

## Production Deployment

### 1. Update `.env` with Production Credentials

```bash
SMTP_SERVER=mail.realpage.com
SMTP_PORT=25
SMTP_USERNAME=production_service_account
SMTP_PASSWORD=secure_production_password
SMTP_FROM_EMAIL=cab.agent@realpage.com
SMTP_FROM_NAME=CAB Agent - Production
```

### 2. Test Email Delivery

```bash
python tests/test_email_service.py
```

### 3. Monitor Email Logs

```bash
# Watch for email errors
tail -f logs/app.log | grep -E "(email|smtp)" -i
```

### 4. Set Up Alerts

Configure monitoring for:
- Failed email deliveries
- SMTP authentication failures
- High retry rates
- Email queue buildup

## Email Metrics

Track these metrics for email notifications:

- **Delivery Rate**: Emails sent / Emails attempted
- **Bounce Rate**: Bounced emails / Emails sent
- **Retry Rate**: Retries / Total attempts
- **Average Delivery Time**: Time from trigger to delivery

## Support

For email-related issues:

1. Check logs in `logs/` directory
2. Verify SMTP configuration in `.env`
3. Test with `tests/test_email_service.py`
4. Contact IT for SMTP server issues
5. Review `src/utils/email_service.py` for code issues

## Future Enhancements

- [ ] Email templates from database
- [ ] Attachment support for PIR documents
- [ ] Email tracking and analytics
- [ ] Bounce handling and retry logic
- [ ] Email queue for high volume
- [ ] HTML email designer
- [ ] Email preview before sending
- [ ] Unsubscribe functionality
