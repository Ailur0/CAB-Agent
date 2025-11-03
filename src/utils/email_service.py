"""Email service for sending notifications via SMTP."""

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils import Config, get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        """Initialize email service with configuration."""
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.use_ssl = Config.SMTP_USE_SSL
        self.username = Config.SMTP_USERNAME
        self.password = Config.SMTP_PASSWORD
        self.from_email = Config.SMTP_FROM_EMAIL
        self.from_name = Config.SMTP_FROM_NAME
        self.is_active = Config.EMAIL_IS_ACTIVE
        self.max_retries = Config.EMAIL_MAX_RETRIES
        self.retry_delay_minutes = Config.EMAIL_RETRY_DELAY_MINUTES
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body (optional, will be generated from HTML if not provided)
            cc: List of CC email addresses
            bcc: List of BCC email addresses
            
        Returns:
            Dictionary with status and message
        """
        if not self.is_active:
            logger.warning("Email service is not active")
            return {
                "status": "disabled",
                "message": "Email service is disabled in configuration",
            }
        
        logger.info("Sending email", to=to_email, subject=subject)
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add plain text version
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Build recipient list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Send email with retries
            for attempt in range(self.max_retries):
                try:
                    if self.use_ssl:
                        # Use SMTP_SSL for port 465
                        if self.smtp_port == 465:
                            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30) as server:
                                if self.username and self.password:
                                    server.login(self.username, self.password)
                                server.send_message(msg)
                        # Use STARTTLS for other ports
                        else:
                            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                                server.starttls()
                                if self.username and self.password:
                                    server.login(self.username, self.password)
                                server.send_message(msg)
                    else:
                        # No SSL/TLS
                        with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                            if self.username and self.password:
                                server.login(self.username, self.password)
                            server.send_message(msg)
                    
                    logger.info("Email sent successfully", to=to_email, attempt=attempt + 1)
                    
                    return {
                        "status": "success",
                        "message": "Email sent successfully",
                        "to": to_email,
                        "subject": subject,
                    }
                    
                except smtplib.SMTPException as e:
                    logger.warning(
                        f"SMTP error on attempt {attempt + 1}/{self.max_retries}",
                        error=str(e),
                        to=to_email,
                    )
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(self.retry_delay_minutes * 60)
                    else:
                        raise
            
        except Exception as e:
            logger.error("Failed to send email", error=str(e), to=to_email)
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}",
                "to": to_email,
            }
    
    def send_pir_request_email(
        self,
        reviewer_email: str,
        cr_id: str,
        cr_title: str,
        requester: str,
    ) -> Dict[str, Any]:
        """Send PIR request email to reviewer."""
        subject = f"PIR Required: {cr_id} - {cr_title}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #0078D4;">📋 Post Implementation Review Required</h2>
                
                <p>A change request has been completed and requires your review.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Change Request:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Title:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_title}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Requested by:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{requester}</td>
                    </tr>
                </table>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⏰ Important:</strong> This PIR will be escalated if not completed within 48 hours.</p>
                </div>
                
                <p>Please complete the Post Implementation Review at your earliest convenience.</p>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                    This is an automated notification from the CAB Agent System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(reviewer_email, subject, html_body)
    
    def send_pir_reminder_email(
        self,
        reviewer_email: str,
        cr_id: str,
        cr_title: str,
        hours_pending: int,
    ) -> Dict[str, Any]:
        """Send PIR reminder email to reviewer."""
        subject = f"PIR Reminder: {cr_id} - {cr_title}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #FFC107;">⏰ PIR Reminder</h2>
                
                <p>This is a reminder that a Post Implementation Review is still pending your completion.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Change Request:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Title:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_title}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Pending for:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{hours_pending} hours</td>
                    </tr>
                </table>
                
                <div style="background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
                    <p style="margin: 0;"><strong>⚠️ Escalation Warning:</strong> This will be escalated to management if not completed within 24 hours.</p>
                </div>
                
                <p>Please complete this PIR as soon as possible to avoid escalation.</p>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                    This is an automated reminder from the CAB Agent System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(reviewer_email, subject, html_body)
    
    def send_pir_escalation_email(
        self,
        manager_email: str,
        cr_id: str,
        cr_title: str,
        requester: str,
        hours_overdue: int,
    ) -> Dict[str, Any]:
        """Send PIR escalation email to Change Manager."""
        subject = f"🚨 PIR Escalation: {cr_id} - {cr_title}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #DC3545;">🚨 PIR Escalation Required</h2>
                
                <p>A Post Implementation Review has not been completed within the SLA timeframe and requires your attention.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Change Request:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Title:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_title}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Requested by:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{requester}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Overdue by:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd; color: #dc3545;"><strong>{hours_overdue} hours</strong></td>
                    </tr>
                </table>
                
                <div style="background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Action Required:</strong> Please follow up with the assigned reviewers or complete the PIR yourself.</p>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                    This is an automated escalation from the CAB Agent System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(manager_email, subject, html_body)
    
    def send_pir_completion_email(
        self,
        requester_email: str,
        cr_id: str,
        cr_title: str,
        reviewer: str,
        comments: str = "",
    ) -> Dict[str, Any]:
        """Send PIR completion email to requester."""
        subject = f"✅ PIR Completed: {cr_id} - {cr_title}"
        
        comments_html = ""
        if comments:
            comments_html = f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Comments:</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{comments}</td>
            </tr>
            """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #28A745;">✅ PIR Completed</h2>
                
                <p>The Post Implementation Review for your change request has been completed.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Change Request:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Title:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{cr_title}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Reviewed by:</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{reviewer}</td>
                    </tr>
                    {comments_html}
                </table>
                
                <div style="background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Status:</strong> Your change request has been closed.</p>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                    This is an automated notification from the CAB Agent System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(requester_email, subject, html_body)


# Create singleton instance
email_service = EmailService()


if __name__ == "__main__":
    print("\n📧 Email Service Test")
    print("=" * 50)
    print(f"SMTP Server: {email_service.smtp_server}:{email_service.smtp_port}")
    print(f"From: {email_service.from_name} <{email_service.from_email}>")
    print(f"Active: {email_service.is_active}")
    print()
