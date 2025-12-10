"""Twilio SMS notification module."""

import logging

from .config import TwilioConfig

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio library not installed. Install with: pip install twilio")


def send_sms(message: str, config: TwilioConfig) -> None:
    """
    Send an SMS via Twilio.
    
    Args:
        message: The message text to send.
        config: Twilio configuration.
        
    Raises:
        ImportError: If Twilio library is not installed.
        Exception: If SMS sending fails.
    """
    if not TWILIO_AVAILABLE:
        raise ImportError(
            "Twilio library not installed. Install with: pip install twilio"
        )
    
    if not message or not message.strip():
        logger.info("Message is empty; not sending SMS.")
        return
    
    try:
        client = Client(config.account_sid, config.auth_token)
        message_obj = client.messages.create(
            body=message,
            from_=config.from_number,
            to=config.to_number
        )
        logger.info(f"SMS sent successfully. SID: {message_obj.sid}")
        # Log truncated message for debugging (first 50 chars)
        logger.debug(f"Message preview: {message[:50]}...")
    except Exception as e:
        error_str = str(e)
        if "20003" in error_str or "Authenticate" in error_str or "401" in error_str:
            logger.error(
                "Twilio authentication failed (Error 20003).\n"
                "Common causes:\n"
                "1. TWILIO_ACCOUNT_SID is incorrect or missing\n"
                "2. TWILIO_AUTH_TOKEN is incorrect or missing\n"
                "3. Credentials may have been regenerated - check your Twilio dashboard\n"
                "4. Account may be suspended or inactive\n\n"
                f"Current Account SID (first 10 chars): {config.account_sid[:10]}...\n"
                f"Check your .env file and Twilio dashboard: https://console.twilio.com/"
            )
        else:
            logger.error(f"Failed to send SMS: {e}")
        raise

