"""Configuration management."""

import os
from dataclasses import dataclass
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional


@dataclass
class EmailConfig:
    """Email/IMAP configuration."""
    host: str
    port: int
    username: str
    password: str   # or app-specific password / token
    use_ssl: bool
    folder: str     # e.g. "INBOX" or "[Gmail]/All Mail"
    from_filters: List[str]  # e.g. ["@linkedin.com"]
    subject_keywords: List[str]  # e.g. ["commented on", "shared a post"]
    max_emails_per_fetch: int = 10  # Maximum emails to fetch per account per run


@dataclass
class RSSConfig:
    """RSS feed configuration."""
    enabled: bool
    feeds: List[str]  # list of feed URLs


@dataclass
class TwilioConfig:
    """Twilio SMS configuration."""
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str


@dataclass
class LLMConfig:
    """LLM API configuration."""
    provider: str         # e.g. "openai" or "generic_http"
    api_key: str
    model: str
    base_url: Optional[str]  # allow custom endpoint
    max_tokens: int
    temperature: float


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    min_gap_minutes: int
    max_gap_minutes: int


@dataclass
class NotificationConfig:
    """Notification delivery configuration."""
    notification_email: Optional[str] = None  # Email address to send notifications to
    send_summary_from_email: Optional[str] = None  # Optional: email account to send summaries from (overrides from_email)
    send_summary_to_email: Optional[str] = None  # Optional: email address to send summaries to (overrides notification_email)


@dataclass
class AppConfig:
    """Complete application configuration."""
    db_path: str
    email: EmailConfig  # Primary email config (for backward compatibility)
    email_accounts: List[EmailConfig]  # List of all email accounts to monitor
    rss: RSSConfig
    twilio: TwilioConfig
    llm: LLMConfig
    scheduler: SchedulerConfig
    notification: NotificationConfig


def _parse_list_env(key: str, default: List[str]) -> List[str]:
    """Parse comma-separated list from environment variable."""
    value = os.getenv(key, "")
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config() -> AppConfig:
    """
    Load configuration from environment variables.
    
    Raises:
        ValueError: If required configuration values are missing.
    """
    # Database
    db_path = os.getenv("DB_PATH", "agent_state.db")
    
    # Email configuration - support multiple accounts
    # Primary account (backward compatible)
    email_host = os.getenv("EMAIL_HOST")
    email_port = int(os.getenv("EMAIL_PORT", "993"))
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_use_ssl = os.getenv("EMAIL_USE_SSL", "true").lower() == "true"
    email_folder = os.getenv("EMAIL_FOLDER", "INBOX")
    # Email filters - if empty, all emails are accepted
    email_from_filters = _parse_list_env("EMAIL_FROM_FILTERS", [])
    email_subject_keywords = _parse_list_env("EMAIL_SUBJECT_KEYWORDS", [])
    
    # Email fetch configuration (needed before creating EmailConfig objects)
    max_emails_per_account = int(os.getenv("MAX_EMAILS_PER_ACCOUNT", "10"))
    
    # Multiple email accounts support
    # Support two formats:
    # 1. Simple list format: EMAIL_ACCOUNTS=user1@gmail.com,user2@gmail.com
    #    Then use: EMAIL_PASSWORD_user1@gmail.com, EMAIL_PASSWORD_user2@gmail.com
    # 2. Numbered format: EMAIL_USERNAME_1, EMAIL_PASSWORD_1, etc.
    email_accounts_list = []
    
    # Check for simple list format first
    accounts_list_str = os.getenv("EMAIL_ACCOUNTS", "")
    if accounts_list_str:
        # Simple format: comma-separated list of email addresses
        account_addresses = [acc.strip() for acc in accounts_list_str.split(",") if acc.strip()]
        
        for account_addr in account_addresses:
            # For each account, look for password with account as key
            # Format: EMAIL_PASSWORD_user@gmail.com or EMAIL_PASSWORD_user_gmail_com
            account_key = account_addr.replace("@", "_").replace(".", "_")
            account_password = (
                os.getenv(f"EMAIL_PASSWORD_{account_addr}") or
                os.getenv(f"EMAIL_PASSWORD_{account_key}") or
                os.getenv(f"EMAIL_PASSWORD_{account_addr.split('@')[0]}")  # Just username part
            )
            # Remove spaces from password (Yahoo app passwords often have spaces)
            if account_password:
                account_password = account_password.replace(" ", "")
            
            if account_password:
                # Auto-detect IMAP host based on email domain
                account_domain = account_addr.split("@")[1].lower() if "@" in account_addr else ""
                
                # Auto-detect IMAP host based on domain
                if account_domain == "gmail.com":
                    default_host = "imap.gmail.com"
                elif account_domain in ["outlook.com", "hotmail.com", "live.com"]:
                    default_host = "outlook.office365.com"
                elif account_domain in ["yahoo.com", "yahoo.co.uk", "yahoo.co.jp", "ymail.com", "rocketmail.com"]:
                    default_host = "imap.mail.yahoo.com"
                elif account_domain.endswith(".com") or account_domain.endswith(".org") or account_domain.endswith(".net"):
                    # For custom domains, try imap.domain.com
                    default_host = f"imap.{account_domain}"
                else:
                    default_host = "imap.gmail.com"  # Fallback
                
                # Use account-specific host override, or auto-detected host (don't use primary email_host as fallback)
                account_host = (
                    os.getenv(f"EMAIL_HOST_{account_addr}") or
                    os.getenv(f"EMAIL_HOST_{account_key}") or
                    default_host  # Use auto-detected host, not primary email_host
                )
                account_port = int(
                    os.getenv(f"EMAIL_PORT_{account_addr}") or
                    os.getenv(f"EMAIL_PORT_{account_key}") or
                    str(email_port)
                )
                account_use_ssl = (
                    os.getenv(f"EMAIL_USE_SSL_{account_addr}") or
                    os.getenv(f"EMAIL_USE_SSL_{account_key}") or
                    str(email_use_ssl)
                ).lower() == "true"
                account_folder = (
                    os.getenv(f"EMAIL_FOLDER_{account_addr}") or
                    os.getenv(f"EMAIL_FOLDER_{account_key}") or
                    email_folder
                )
                
                email_accounts_list.append(EmailConfig(
                    host=account_host,
                    port=account_port,
                    username=account_addr,
                    password=account_password,
                    use_ssl=account_use_ssl,
                    folder=account_folder,
                    from_filters=email_from_filters,
                    subject_keywords=email_subject_keywords,
                    max_emails_per_fetch=max_emails_per_account,
                ))
    
    # If no list format, check for primary + numbered accounts
    if not email_accounts_list:
        # Add primary account if configured
        if email_host and email_username and email_password:
            email_accounts_list.append(EmailConfig(
                host=email_host,
                port=email_port,
                username=email_username,
                password=email_password,
                use_ssl=email_use_ssl,
                folder=email_folder,
                from_filters=email_from_filters,
                subject_keywords=email_subject_keywords,
                max_emails_per_fetch=max_emails_per_account,
            ))
        
        # Check for additional accounts (EMAIL_HOST_1, EMAIL_USERNAME_1, EMAIL_PASSWORD_1, etc.)
        account_num = 1
        while True:
            account_host = os.getenv(f"EMAIL_HOST_{account_num}")
            account_username = os.getenv(f"EMAIL_USERNAME_{account_num}")
            account_password = os.getenv(f"EMAIL_PASSWORD_{account_num}")
            
            if not (account_host and account_username and account_password):
                break  # No more accounts
            
            account_port = int(os.getenv(f"EMAIL_PORT_{account_num}", str(email_port)))
            account_use_ssl = os.getenv(f"EMAIL_USE_SSL_{account_num}", str(email_use_ssl)).lower() == "true"
            account_folder = os.getenv(f"EMAIL_FOLDER_{account_num}", email_folder)
            
            email_accounts_list.append(EmailConfig(
                host=account_host,
                port=account_port,
                username=account_username,
                password=account_password,
                use_ssl=account_use_ssl,
                folder=account_folder,
                from_filters=email_from_filters,  # Shared filters
                subject_keywords=email_subject_keywords,  # Shared keywords
                max_emails_per_fetch=max_emails_per_account,
            ))
            account_num += 1
    
    # Validate at least one account is configured
    if not email_accounts_list:
        raise ValueError("Missing required email configuration. Set EMAIL_HOST, EMAIL_USERNAME, EMAIL_PASSWORD")
    
    # Primary email config (first account for backward compatibility)
    primary_email = email_accounts_list[0]
    
    # RSS configuration
    rss_enabled = os.getenv("RSS_ENABLED", "false").lower() == "true"
    rss_feeds = _parse_list_env("RSS_FEEDS", [])
    
    # Twilio configuration
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")
    twilio_to_number = os.getenv("TWILIO_TO_NUMBER")
    
    # LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_base_url = os.getenv("LLM_BASE_URL")
    llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))  # Increased for multiple accounts
    llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    
    # Scheduler configuration
    min_gap_minutes = int(os.getenv("MIN_GAP_MINUTES", "30"))
    max_gap_minutes = int(os.getenv("MAX_GAP_MINUTES", "120"))
    
    # Notification configuration
    notification_email = os.getenv("NOTIFICATION_EMAIL")
    send_summary_from_email = os.getenv("SEND_SUMMARY_FROM_EMAIL")  # Optional: email account to send summaries from
    send_summary_to_email = os.getenv("SEND_SUMMARY_TO_EMAIL")  # Optional: email address to send summaries to
    
    # Validate required fields
    missing = []
    # Email validation is now handled above (in email_accounts_list creation)
    if not twilio_account_sid:
        missing.append("TWILIO_ACCOUNT_SID")
    if not twilio_auth_token:
        missing.append("TWILIO_AUTH_TOKEN")
    if not twilio_from_number:
        missing.append("TWILIO_FROM_NUMBER")
    if not twilio_to_number:
        missing.append("TWILIO_TO_NUMBER")
    if not llm_api_key:
        missing.append("LLM_API_KEY")
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    
    return AppConfig(
        db_path=db_path,
        email=primary_email,  # Primary account for backward compatibility
        email_accounts=email_accounts_list,  # All accounts to monitor
        rss=RSSConfig(
            enabled=rss_enabled,
            feeds=rss_feeds,
        ),
        twilio=TwilioConfig(
            account_sid=twilio_account_sid,
            auth_token=twilio_auth_token,
            from_number=twilio_from_number,
            to_number=twilio_to_number,
        ),
        llm=LLMConfig(
            provider=llm_provider,
            api_key=llm_api_key,
            model=llm_model,
            base_url=llm_base_url,
            max_tokens=llm_max_tokens,
            temperature=llm_temperature,
        ),
        scheduler=SchedulerConfig(
            min_gap_minutes=min_gap_minutes,
            max_gap_minutes=max_gap_minutes,
        ),
        notification=NotificationConfig(
            notification_email=notification_email,
            send_summary_from_email=send_summary_from_email,
            send_summary_to_email=send_summary_to_email,
        ),
    )

