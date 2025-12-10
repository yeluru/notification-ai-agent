"""IMAP email client for fetching notifications."""

import email.message
import email.utils
import imaplib
import logging
import re
import time
from datetime import datetime, timedelta
from email.header import decode_header
from typing import List, Optional, Tuple
from html import unescape

from .config import EmailConfig
from .models import EmailNotification

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def _decode_header_value(header_value: str) -> str:
    """Decode email header value (handles encoded words)."""
    if not header_value:
        return ""
    
    decoded_parts = decode_header(header_value)
    decoded_string = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            try:
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            except:
                decoded_string += part.decode('utf-8', errors='ignore')
        else:
            decoded_string += part
    
    return decoded_string.strip()


def _extract_links(text: str) -> List[str]:
    """Extract URLs from text."""
    # Pattern to match URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
    links = re.findall(url_pattern, text)
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    return unique_links[:5]  # Limit to first 5 links


def _extract_plain_text(body: str) -> str:
    """Extract plain text from HTML or return as-is."""
    # Simple HTML tag removal
    text = re.sub(r'<[^>]+>', '', body)
    # Decode HTML entities
    text = unescape(text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _get_text_from_message(msg: email.message.Message) -> Tuple[str, str]:
    """
    Extract plain text and HTML from email message.
    
    Returns:
        Tuple of (text_content, html_content)
    """
    text_content = ""
    html_content = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and not text_content:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        text_content = payload.decode(charset, errors='ignore')
                    except:
                        pass
            elif content_type == "text/html" and not html_content:
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        html_content = payload.decode(charset, errors='ignore')
                    except:
                        pass
        # Fallback to HTML if no plain text
        if not text_content and html_content:
            text_content = _extract_plain_text(html_content)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            content_type = msg.get_content_type()
            try:
                charset = msg.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='ignore')
                if content_type == "text/html":
                    html_content = content
                    text_content = _extract_plain_text(content)
                else:
                    text_content = content
            except:
                text_content = payload.decode('utf-8', errors='ignore')
    
    return text_content, html_content


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse email date header to UTC datetime."""
    if not date_str:
        return None
    
    try:
        # Parse email date (handles timezone)
        date_tuple = email.utils.parsedate_tz(date_str)
        if date_tuple:
            timestamp = email.utils.mktime_tz(date_tuple)
            # mktime_tz returns UTC timestamp, so fromtimestamp with UTC
            dt = datetime.utcfromtimestamp(timestamp)
            return dt
    except Exception as e:
        logger.debug(f"Error parsing date '{date_str}': {e}")
    
    return None


def _matches_filters(sender: str, subject: str, config: EmailConfig) -> bool:
    """
    Check if email matches configured filters.
    
    Filter logic:
    - If no filters configured, accept all emails
    - If only from_filters configured, match emails from those senders
    - If only subject_keywords configured, match emails with those keywords
    - If both configured, match emails that have EITHER from filter OR subject keyword (OR logic)
    """
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    
    # If no filters configured, accept all emails
    if not config.from_filters and not config.subject_keywords:
        return True
    
    # Check from filters (if configured)
    from_match = False
    if config.from_filters:
        from_match = any(
            filter_str.lower() in sender_lower
            for filter_str in config.from_filters
        )
    
    # Check subject keywords (if configured)
    subject_match = False
    if config.subject_keywords:
        subject_match = any(
            keyword.lower() in subject_lower
            for keyword in config.subject_keywords
        )
    
    # If both filters are configured, use OR logic (match if either matches)
    if config.from_filters and config.subject_keywords:
        return from_match or subject_match
    
    # If only one type is configured, use that
    if config.from_filters:
        return from_match
    if config.subject_keywords:
        return subject_match
    
    return True


def fetch_notifications(
    config: EmailConfig,
    minutes_back: int = 15,
    skip_filters: bool = False
) -> List[EmailNotification]:
    """
    Fetch UNREAD email notifications from the last N minutes.
    
    Args:
        config: Email configuration.
        minutes_back: Number of minutes to look back for emails (default: 15).
        skip_filters: If True, skip filter matching and return all unread emails.
        
    Returns:
        List of EmailNotification objects (unread emails from last N minutes).
    """
    notifications = []
    mail = None
    
    # Retry logic for network operations
    for attempt in range(MAX_RETRIES):
        try:
            # Connect to IMAP server
            if config.use_ssl:
                mail = imaplib.IMAP4_SSL(config.host, config.port)
            else:
                mail = imaplib.IMAP4(config.host, config.port)
            
            # Login
            try:
                mail.login(config.username, config.password)
                break  # Success, exit retry loop
            except imaplib.IMAP4.error as e:
                error_msg = str(e)
                is_yahoo = "yahoo.com" in config.username.lower() or "imap.mail.yahoo.com" in config.host.lower()
                
                if "AUTHENTICATIONFAILED" in error_msg or "Invalid credentials" in error_msg or "Lookup failed" in error_msg:
                    if is_yahoo:
                        logger.error(
                            f"Yahoo IMAP authentication failed for {config.username}.\n"
                            f"Error: {error_msg}\n\n"
                            f"Common causes:\n"
                            f"1. You MUST use a Yahoo App Password, not your regular password.\n"
                            f"   - Go to: https://login.yahoo.com/account/security\n"
                            f"   - Enable 2-Step Verification (required)\n"
                            f"   - Generate App Password: Account Security > App Passwords\n"
                            f"   - Select 'Mail' and your device\n"
                            f"   - Copy the 16-character password\n"
                            f"2. Remove spaces from the app password in .env file\n"
                            f"   - If password is 'abcd efgh ijkl mnop', use 'abcdefghijklmnop'\n"
                            f"3. Verify IMAP is enabled in Yahoo account settings\n"
                            f"4. Make sure 2-Step Verification is enabled (required for app passwords)\n"
                            f"5. Check that EMAIL_PASSWORD_{config.username} is set correctly in .env"
                        )
                    else:
                        logger.error(
                            f"IMAP authentication failed for {config.username}. Common causes:\n"
                            "1. For Gmail: You MUST use an App Password, not your regular password.\n"
                            "   Generate one at: https://myaccount.google.com/apppasswords\n"
                            "   (Requires 2-Step Verification to be enabled)\n"
                            "2. Check that EMAIL_USERNAME is your full email address\n"
                            "3. Verify EMAIL_HOST and EMAIL_PORT are correct\n"
                            "4. For Outlook: May need to enable 'Less secure apps' or use OAuth"
                        )
                raise  # Don't retry authentication failures
        except (imaplib.IMAP4.error, OSError, ConnectionError) as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                logger.error(f"Failed to connect after {MAX_RETRIES} attempts: {e}")
                raise
    
    if mail is None:
        raise ConnectionError("Failed to establish IMAP connection")
    
    try:
        
        # Select folder
        status, _ = mail.select(config.folder)
        if status != "OK":
            logger.error(f"Failed to select folder: {config.folder}")
            mail.close()
            mail.logout()
            return []
        
        # Build IMAP search criteria for UNREAD emails from last N minutes
        search_criteria = ["UNSEEN"]  # Only unread emails
        
        # Calculate date for last N minutes
        minutes_ago = datetime.utcnow() - timedelta(minutes=minutes_back)
        date_str = minutes_ago.strftime("%d-%b-%Y")
        search_criteria.append(f"SINCE {date_str}")
        
        logger.info(f"Searching for UNREAD emails since {date_str} (last {minutes_back} minutes) from {config.username}")
        
        # Search for unread messages
        search_query = " ".join(search_criteria)
        status, message_numbers = mail.search(None, search_query)
        
        if status != "OK" or not message_numbers[0]:
            mail.close()
            mail.logout()
            return []
        
        message_ids = message_numbers[0].split()
        
        # Reverse to get newest first, then limit to max_emails_per_fetch
        message_ids.reverse()
        total_found = len(message_ids)
        max_emails = getattr(config, 'max_emails_per_fetch', 10)
        if total_found > max_emails:
            message_ids = message_ids[:max_emails]
            logger.info(f"Found {total_found} emails, limiting to {max_emails} most recent from {config.username}")
        else:
            logger.info(f"Found {total_found} emails to process from {config.username}")
        
        if not message_ids:
            logger.debug(f"No emails found matching criteria for {config.username}")
            mail.close()
            mail.logout()
            return []
        
        logger.info(f"Found {len(message_ids)} emails to process from {config.username}")
        
        # Process each message and apply filters
        processed = 0
        for msg_id in message_ids:
            try:
                # Fetch message
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                
                if status != "OK":
                    logger.warning(f"Failed to fetch message {msg_id}")
                    continue
                
                # Parse message
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Extract headers
                from_header = _decode_header_value(msg.get("From", ""))
                subject = _decode_header_value(msg.get("Subject", ""))
                message_id_header = msg.get("Message-ID", "")
                date_header = msg.get("Date", "")
                
                # Apply filters only if not skipping
                if not skip_filters and not _matches_filters(from_header, subject, config):
                    logger.debug(f"Skipping email: From={from_header[:40]}, Subject={subject[:40]} (doesn't match filters)")
                    processed += 1
                    continue
                
                # Get unique ID
                unique_id = message_id_header.strip("<>") if message_id_header else str(msg_id.decode())
                
                # Extract text snippet and HTML
                text_content, html_content = _get_text_from_message(msg)
                snippet = text_content[:600].strip()
                if len(text_content) > 600:
                    snippet += "..."
                
                # Extract links from both HTML and plain text (HTML has more reliable links)
                links = []
                if html_content:
                    # Extract from HTML (more reliable)
                    links = _extract_links(html_content)
                if not links and text_content:
                    # Fallback to plain text
                    links = _extract_links(text_content)
                
                # Parse date
                received_dt = _parse_date(date_header)
                if not received_dt:
                    received_dt = datetime.utcnow()
                
                received_at = received_dt.isoformat() + "Z"
                
                notifications.append(EmailNotification(
                    id=unique_id,
                    sender=from_header,
                    subject=subject,
                    snippet=snippet,
                    received_at=received_at,
                    email_account=config.username,
                    links=links,
                ))
                processed += 1
                logger.debug(f"Added email: From={from_header[:40]}, Subject={subject[:40]}")
                
            except Exception as e:
                logger.debug(f"Error processing message {msg_id}: {e}")
                processed += 1
                continue
        
        # Close connection gracefully, handling server disconnects
        try:
            mail.close()
        except Exception as e:
            logger.debug(f"Error closing mailbox (may be disconnected): {e}")
        
        try:
            mail.logout()
        except Exception as e:
            logger.debug(f"Error logging out (connection may be closed): {e}")
        
        logger.info(f"Extracted {len(notifications)} matching emails from {config.username}")
        
    except Exception as e:
        logger.error(f"Error fetching email notifications from {config.username}: {e}", exc_info=True)
        # Ensure connection is closed on error
        if mail:
            try:
                mail.close()
            except:
                pass
            try:
                mail.logout()
            except:
                pass
        raise
    finally:
        # Ensure connection is always closed
        if mail:
            try:
                mail.close()
            except:
                pass
            try:
                mail.logout()
            except:
                pass
    
    return notifications

