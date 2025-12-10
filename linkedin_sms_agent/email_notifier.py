"""Email notification module for sending summary emails."""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import EmailConfig

logger = logging.getLogger(__name__)


def send_email(
    message: str,
    subject: str,
    to_email: str,
    from_email: str = None,
    smtp_config: EmailConfig = None
) -> None:
    """
    Send an email notification.
    
    Args:
        message: The message text to send.
        subject: Email subject line.
        to_email: Recipient email address.
        from_email: Sender email address (defaults to to_email if not provided).
        smtp_config: Email configuration (reused for SMTP settings). If None, will use from_email for SMTP.
        
    Raises:
        Exception: If email sending fails.
    """
    if not message or not message.strip():
        logger.info("Message is empty; not sending email.")
        return
    
    # Use to_email as from_email if not specified (send to self)
    if from_email is None:
        from_email = to_email
    
    # Determine SMTP settings - use smtp_config if provided (preferred)
    if smtp_config:
        # Convert IMAP host to SMTP host
        imap_host = smtp_config.host
        if "secureserver.net" in imap_host:
            # GoDaddy uses smtpout.secureserver.net for SMTP
            # NOTE: GoDaddy SMTP has been unreliable. Consider using Gmail for sending.
            smtp_host = "smtpout.secureserver.net"
            smtp_port = 465  # GoDaddy uses port 465 with SSL
            smtp_use_ssl = True
            logger.warning(
                "Using GoDaddy SMTP (secureserver.net). "
                "If this fails, consider setting SEND_SUMMARY_FROM_EMAIL to a Gmail account."
            )
        elif imap_host.startswith("imap."):
            smtp_host = imap_host.replace("imap.", "smtp.", 1)
            smtp_port = 587
            smtp_use_ssl = smtp_config.use_ssl
        elif imap_host == "outlook.office365.com":
            smtp_host = "smtp.office365.com"
            smtp_port = 587
            smtp_use_ssl = True
        elif imap_host == "imap.gmail.com":
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
            smtp_use_ssl = True
        else:
            # Try generic replacement
            smtp_host = imap_host.replace("imap.", "smtp.").replace("imap", "smtp")
            smtp_port = 587
            smtp_use_ssl = smtp_config.use_ssl
        
        # Use the account from smtp_config for authentication
        smtp_username = smtp_config.username
        smtp_password = smtp_config.password
        logger.info(f"Using SMTP config: username={smtp_username}, host={smtp_host}:{smtp_port}, SSL={smtp_use_ssl}")
        logger.debug(f"SMTP password length: {len(smtp_password) if smtp_password else 0}")
        # Note: We authenticate with smtp_config.username, but set From header to from_email
        # Some SMTP servers allow this if you're authenticated
    else:
        # Try to determine SMTP settings from email domain
        if "@gmail.com" in from_email.lower():
            smtp_host = "smtp.gmail.com"
            smtp_port = 587
            smtp_use_ssl = True
        elif "@outlook.com" in from_email.lower() or "@hotmail.com" in from_email.lower():
            smtp_host = "smtp-mail.outlook.com"
            smtp_port = 587
            smtp_use_ssl = True
        else:
            raise ValueError(
                f"Cannot determine SMTP settings for {from_email}. "
                f"Please ensure the notification email is in EMAIL_ACCOUNTS or provide smtp_config."
            )
        
        # Get password for the from_email account
        smtp_username = from_email
        smtp_password = (
            os.getenv(f"EMAIL_PASSWORD_{from_email}") or
            os.getenv(f"EMAIL_PASSWORD_{from_email.replace('@', '_').replace('.', '_')}") or
            os.getenv(f"EMAIL_PASSWORD_{from_email.split('@')[0]}")
        )
        
        if not smtp_password:
            raise ValueError(
                f"Could not find password for {from_email}. "
                f"Set EMAIL_PASSWORD_{from_email} in .env file."
            )
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body with proper formatting
        # Preserve line breaks and format for readability
        formatted_message = message.replace('\n', '\n')  # Ensure line breaks are preserved
        msg.attach(MIMEText(formatted_message, 'plain'))
        
        logger.debug(f"Connecting to SMTP server: {smtp_host}:{smtp_port}")
        logger.debug(f"SMTP username: {smtp_username}")
        logger.debug(f"SMTP password length: {len(smtp_password) if smtp_password else 0}")
        
        # Connect to SMTP server with timeout
        timeout_seconds = 30  # 30 second timeout
        if smtp_port == 465:
            # Use SMTP_SSL for port 465
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=timeout_seconds)
        else:
            # Use STARTTLS for port 587
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout_seconds)
            server.starttls()
        
        # Login and send
        logger.debug(f"Attempting SMTP login...")
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        logger.debug(f"Subject: {subject}")
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = str(e)
        is_godaddy = "secureserver.net" in str(smtp_host) if 'smtp_host' in locals() else False
        godaddy_note = ""
        if is_godaddy:
            godaddy_note = (
                "\n5. GoDaddy SMTP has been unreliable. "
                "Consider using SEND_SUMMARY_FROM_EMAIL with a Gmail account instead.\n"
            )
        logger.error(
            f"SMTP authentication failed for {from_email}. "
            f"Common causes:\n"
            f"1. Password is incorrect or expired\n"
            f"2. For Gmail: Use an App Password, not your regular password\n"
            f"3. For GoDaddy/custom domains: Verify the password is correct\n"
            f"4. Check that EMAIL_PASSWORD_{from_email} is set correctly in .env{godaddy_note}"
            f"Error details: {error_msg}"
        )
        raise
    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        error_msg = str(e)
        is_godaddy = "secureserver.net" in str(smtp_host) if 'smtp_host' in locals() else False
        if is_godaddy:
            logger.error(
                f"GoDaddy SMTP connection failed: {error_msg}\n"
                f"GoDaddy SMTP has been unreliable. "
                f"Consider setting SEND_SUMMARY_FROM_EMAIL to a Gmail account in .env"
            )
        else:
            logger.error(f"Failed to send email: {error_msg}")
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise

