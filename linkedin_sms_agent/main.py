"""Main entry point for the notification agent."""

import argparse
import logging
import os
import sys
from datetime import datetime

from .config import AppConfig, load_config
from .db import clear_seen_items, get_meta, get_seen_ids, init_db, mark_seen, set_meta
from .email_client import fetch_notifications
from .email_notifier import send_email
from .rss_client import fetch_items
# Scheduler removed - using cron for 15-minute intervals
from .summarizer import summarize_notifications
from .twilio_notifier import send_sms
from .llm_client import LLMClient
from .openai_client import OpenAILLMClient, GenericHTTPLLMClient

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def _create_llm_client(config: AppConfig) -> LLMClient:
    """Create an LLM client based on configuration."""
    if config.llm.provider == "openai":
        return OpenAILLMClient(config.llm)
    else:
        return GenericHTTPLLMClient(config.llm)


def run_once(args=None) -> None:
    """Run the notification agent once."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        
        # Initialize database
        logger.info(f"Initializing database at {config.db_path}...")
        conn = init_db(config.db_path)
        
        # Clear seen items if requested
        if args and args.reset_seen:
            logger.info("Clearing all seen items from database...")
            clear_seen_items(conn)
            logger.info("All seen items cleared.")
        elif args and args.reset_seen_email:
            logger.info("Clearing email seen items from database...")
            clear_seen_items(conn, source="email")
            logger.info("Email seen items cleared.")
        
        # For automatic 15-minute runs, we fetch UNREAD emails from last 15 minutes
        # Scheduling is handled by cron (every 15 minutes) - no need to check last_run
        minutes_back = int(os.getenv("EMAIL_CHECK_MINUTES", "15"))  # Default 15 minutes
        
        logger.info(f"Starting notification fetch (checking last {minutes_back} minutes for UNREAD emails)...")
        
        # Fetch email notifications from all configured accounts
        # Get UNREAD emails from last 15 minutes, skip filters
        all_email_notifications = []
        logger.info(f"Monitoring {len(config.email_accounts)} email account(s)...")
        
        for email_config in config.email_accounts:
            logger.info(f"Fetching UNREAD emails from {email_config.username}...")
            try:
                account_emails = fetch_notifications(
                    email_config, 
                    minutes_back=minutes_back,
                    skip_filters=True  # Get all unread emails, no filtering
                )
                logger.info(f"Found {len(account_emails)} unread emails from {email_config.username}")
                all_email_notifications.extend(account_emails)
            except Exception as e:
                logger.error(f"Error fetching emails from {email_config.username}: {e}", exc_info=True)
                continue  # Continue with other accounts even if one fails
        
        logger.info(f"Total emails found across all accounts: {len(all_email_notifications)}")
        email_notifications = all_email_notifications
        
        # Fetch RSS items
        rss_items = []
        if config.rss.enabled:
            logger.info("Fetching RSS feeds...")
            rss_items = fetch_items(config.rss)
            logger.info(f"Found {len(rss_items)} RSS items")
        
        # Since we're fetching UNREAD emails, we still check database to avoid duplicates
        # But we process all unread emails from the time window
        seen_ids = get_seen_ids(conn)
        
        # Filter to new items (not seen before)
        new_emails = [
            email for email in email_notifications
            if (email.id, "email") not in seen_ids
        ]
        new_rss = [
            item for item in rss_items
            if (item.id, "rss") not in seen_ids
        ]
        
        total_new = len(new_emails) + len(new_rss)
        logger.info(
            f"Found {total_new} new unread items "
            f"({len(new_emails)} emails, {len(new_rss)} RSS items)"
        )
        
        if total_new == 0:
            logger.info("No new unread items found; exiting.")
            conn.close()
            return
        
        # Sort by timestamp (newest first)
        new_emails.sort(key=lambda e: e.received_at, reverse=True)
        new_rss.sort(key=lambda r: r.published_at, reverse=True)
        
        # Summarize using LLM
        logger.info("Summarizing notifications with LLM...")
        try:
            llm_client = _create_llm_client(config)
            summary = summarize_notifications(
                new_emails,
                new_rss,
                llm_client,
                config.llm,
                summarize_individually=True  # Summarize each email individually
            )
            
            if summary and summary.strip():
                # Check if LLM said "no notable updates" but we have items
                if "no notable updates" in summary.lower() and total_new > 0:
                    logger.warning(
                        f"LLM returned 'No notable updates' but we have {total_new} new items. "
                        f"Creating fallback summary..."
                    )
                    # Create a simple fallback summary listing all items
                    fallback_lines = []
                    for email in new_emails[:10]:  # Limit to 10
                        sender_short = email.sender.split('<')[0].strip() if '<' in email.sender else email.sender[:30]
                        subject_short = email.subject[:80]
                        fallback_lines.append(f"Email from {sender_short}: {subject_short}")
                    for rss in new_rss[:10]:
                        fallback_lines.append(f"RSS {rss.source}: {rss.title[:80]}")
                    
                    summary = "\n\n".join(fallback_lines)
                    logger.info(f"Using fallback summary with {len(fallback_lines)} items")
                
                logger.info(f"Generated summary ({len(summary)} chars)")
                logger.debug(f"Summary: {summary[:200]}...")
                
                # Determine notification method from command line or config
                notification_method = os.getenv("NOTIFICATION_METHOD", "sms").lower()
                
                if notification_method == "email":
                    # Determine recipient email: SEND_SUMMARY_TO_EMAIL > command line --email > NOTIFICATION_EMAIL > default
                    notification_email = (
                        config.notification.send_summary_to_email or
                        os.getenv("NOTIFICATION_EMAIL") or
                        config.notification.notification_email or
                        config.email.username
                    )
                    # Get from_email from command line argument or use notification_email
                    from_email = os.getenv("NOTIFICATION_EMAIL") or notification_email
                    
                    # Check if SEND_SUMMARY_FROM_EMAIL is set - use that account to send from
                    send_from_email = config.notification.send_summary_from_email
                    if send_from_email:
                        from_email = send_from_email
                        logger.info(f"Using SEND_SUMMARY_FROM_EMAIL: {from_email} to send summary")
                    
                    # Find SMTP config for the sending email account
                    # Check if sending email is in monitored accounts
                    smtp_config_for_sending = None
                    for email_config in config.email_accounts:
                        if email_config.username.lower() == from_email.lower():
                            smtp_config_for_sending = email_config
                            break
                    
                    # If notification email is in monitored accounts, use it
                    # Otherwise, check if we have password for it in env vars
                    if not smtp_config_for_sending:
                        # Check if password exists for this email
                        password_key = f"EMAIL_PASSWORD_{from_email}"
                        password = os.getenv(password_key) or os.getenv(f"EMAIL_PASSWORD_{from_email.replace('@', '_').replace('.', '_')}")
                        
                        # Strip whitespace in case .env has extra spaces
                        if password:
                            password = password.strip()
                        
                        if password:
                            # Create a temporary config for this email
                            # Use the actual IMAP host from environment or auto-detect
                            email_domain = from_email.split("@")[1].lower() if "@" in from_email else ""
                            account_key = from_email.replace("@", "_").replace(".", "_")
                            
                            # Try to get the actual IMAP host from env vars first
                            imap_host = (
                                os.getenv(f"EMAIL_HOST_{from_email}") or
                                os.getenv(f"EMAIL_HOST_{account_key}")
                            )
                            
                            # If not found, auto-detect based on domain
                            if not imap_host:
                                if email_domain == "gmail.com":
                                    imap_host = "imap.gmail.com"
                                elif email_domain in ["outlook.com", "hotmail.com", "live.com"]:
                                    imap_host = "outlook.office365.com"
                                else:
                                    # For custom domains, try imap.domain.com
                                    imap_host = f"imap.{email_domain}"
                            
                            # Get port and SSL settings, with defaults
                            imap_port = int(
                                os.getenv(f"EMAIL_PORT_{from_email}") or
                                os.getenv(f"EMAIL_PORT_{account_key}") or
                                str(config.email_accounts[0].port)
                            )
                            imap_use_ssl = (
                                os.getenv(f"EMAIL_USE_SSL_{from_email}") or
                                os.getenv(f"EMAIL_USE_SSL_{account_key}") or
                                str(config.email_accounts[0].use_ssl)
                            ).lower() == "true"
                            
                            from .config import EmailConfig
                            smtp_config_for_sending = EmailConfig(
                                host=imap_host,  # Use IMAP host, email_notifier will convert to SMTP
                                port=imap_port,
                                username=from_email,
                                password=password,
                                use_ssl=imap_use_ssl,
                                folder=config.email_accounts[0].folder,
                                from_filters=config.email_accounts[0].from_filters,
                                subject_keywords=config.email_accounts[0].subject_keywords,
                                max_emails_per_fetch=config.email_accounts[0].max_emails_per_fetch,
                            )
                            logger.info(f"Found password for {from_email}, using IMAP host: {imap_host}")
                        else:
                            # No password found, use first monitored account
                            smtp_config_for_sending = config.email_accounts[0]
                            from_email = smtp_config_for_sending.username
                            logger.warning(
                                f"Notification email {notification_email} not in monitored accounts and no password found. "
                                f"Sending from {from_email} to {notification_email} instead."
                            )
                    
                    logger.info(f"Sending email notification from {from_email} to {notification_email}...")
                    send_email(
                        message=summary,
                        subject="Notification Summary",
                        to_email=notification_email,
                        from_email=from_email,  # Send from/to same address if possible
                        smtp_config=smtp_config_for_sending
                    )
                    logger.info("Email sent successfully.")
                else:
                    # Send via SMS (default)
                    logger.info("Sending SMS notification...")
                    try:
                        send_sms(summary, config.twilio)
                        logger.info("SMS sent successfully.")
                    except Exception as sms_error:
                        logger.warning(f"SMS failed: {sms_error}")
                        # Fallback to email if SMS fails and email is configured
                        if config.notification.notification_email or config.email.username:
                            logger.info("Falling back to email notification...")
                            # Determine recipient email: SEND_SUMMARY_TO_EMAIL > NOTIFICATION_EMAIL > default
                            notification_email = (
                                config.notification.send_summary_to_email or
                                os.getenv("NOTIFICATION_EMAIL") or
                                config.notification.notification_email or
                                config.email.username
                            )
                            from_email = os.getenv("NOTIFICATION_EMAIL") or notification_email
                            
                            # Check if SEND_SUMMARY_FROM_EMAIL is set - use that account to send from
                            if config.notification.send_summary_from_email:
                                from_email = config.notification.send_summary_from_email
                                logger.info(f"Using SEND_SUMMARY_FROM_EMAIL: {from_email} to send summary")
                            
                            # Find appropriate SMTP config
                            smtp_config_for_sending = None
                            actual_from_email = from_email
                            
                            for email_config in config.email_accounts:
                                if email_config.username.lower() == from_email.lower():
                                    smtp_config_for_sending = email_config
                                    break
                            
                            if not smtp_config_for_sending:
                                smtp_config_for_sending = config.email_accounts[0]
                                actual_from_email = smtp_config_for_sending.username
                            
                            send_email(
                                message=summary,
                                subject="Notification Summary",
                                to_email=notification_email,
                                from_email=actual_from_email,
                                smtp_config=smtp_config_for_sending
                            )
                            logger.info("Email sent successfully as fallback.")
                        else:
                            raise  # Re-raise if no email fallback available
            else:
                logger.info("Summary is empty; not sending notification.")
        
        except Exception as e:
            logger.error(f"Error during summarization or SMS sending: {e}")
            # Don't mark items as seen if we failed to process them
            conn.close()
            sys.exit(1)
        
        # Mark items as seen (so they won't be processed again)
        logger.info("Marking items as seen...")
        items_to_mark = (
            [(email.id, "email") for email in new_emails] +
            [(item.id, "rss") for item in new_rss]
        )
        mark_seen(conn, items_to_mark)
        # Note: We don't update last_run anymore since we use time-based window
        conn.close()
        
        logger.info("Run completed successfully.")
    
    except Exception as e:
        logger.error(f"Fatal error in run_once: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Email and RSS notification agent that sends SMS or email summaries"
    )
    parser.add_argument(
        "--method",
        choices=["sms", "email"],
        default=None,
        help="Notification method: 'sms' or 'email' (default: from NOTIFICATION_METHOD env var or 'sms')"
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Email address to send notifications to (overrides NOTIFICATION_EMAIL env var)"
    )
    parser.add_argument(
        "--reset-seen",
        action="store_true",
        help="Clear all seen items from database before processing (allows reprocessing of previously seen emails)"
    )
    parser.add_argument(
        "--reset-seen-email",
        action="store_true",
        help="Clear only email seen items from database before processing"
    )
    
    args = parser.parse_args()
    
    # Set environment variable if method is specified
    if args.method:
        os.environ["NOTIFICATION_METHOD"] = args.method
    
    # Set notification email if specified
    if args.email:
        os.environ["NOTIFICATION_EMAIL"] = args.email
    
    run_once(args)


if __name__ == "__main__":
    main()

