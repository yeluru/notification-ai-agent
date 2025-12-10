"""Data models for notifications."""

from dataclasses import dataclass, field


@dataclass
class EmailNotification:
    """Represents an email notification."""
    id: str            # message-id or UID string
    sender: str        # "Name <email>"
    subject: str
    snippet: str       # short plain-text snippet
    received_at: str   # ISO8601 UTC
    email_account: str = ""  # Email account this was fetched from
    links: list[str] = field(default_factory=list)  # List of URLs found in the email


@dataclass
class RSSItem:
    """Represents an RSS feed item."""
    id: str            # guid or link
    source: str        # feed title or URL
    title: str
    snippet: str       # short description/content
    published_at: str  # ISO8601 UTC

