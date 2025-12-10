"""LLM summarization for notifications."""

from typing import Sequence

from .config import LLMConfig
from .llm_client import LLMClient
from .models import EmailNotification, RSSItem


def build_summary_prompt(
    emails: Sequence[EmailNotification],
    rss_items: Sequence[RSSItem]
) -> str:
    """
    Build a prompt for summarizing notifications.
    
    Args:
        emails: Email notifications to summarize.
        rss_items: RSS items to summarize.
        
    Returns:
        A formatted prompt string.
    """
    prompt = """You are a notification assistant that creates clear, readable summaries.

I will give you new notification items from email and RSS feeds.
Create a well-formatted summary with proper line breaks and context.

CRITICAL FORMATTING REQUIREMENTS:
- You MUST include ALL items provided - do not filter anything out
- Group all emails by the monitored email account (the "Email:" field)
- All emails from the same monitored account should be listed together in one section
- Each email account section should start with "Email: [account]" followed by all emails for that account
- Within each account section, format each email as follows:
  
  Sender: [sender name or email]
  Time: [date/time in readable format]
  Subject: [email subject]
  Summary: [brief summary of the email content - keep it concise, no links]
  
- Add a blank line between each email within the same account
- Add a blank line between different email account sections
- Use plain text only (no markdown, no special characters)
- Keep summary lines under 150 characters
- Do NOT include links in the summary - keep it concise
- The "Email:" field shows which monitored inbox the email came from (useful when watching multiple accounts)
- For RSS items, use similar format with Source, Time, Title, Summary

Format example (emails grouped by monitored account):
Email: monitored-account1@gmail.com
Sender: John Doe
Time: Dec 8, 2025 3:45 PM
Subject: New Chrome extension available
Summary: Pictory extension lets you turn browser tabs into videos instantly.

Sender: Travel Deals
Time: Dec 8, 2025 2:30 PM
Subject: Year-end flight deals ending today
Summary: Up to ₹7,500 off flights available, ending today.

Email: monitored-account2@gmail.com
Sender: LinkedIn
Time: Dec 8, 2025 1:15 PM
Subject: New connection request
Summary: Someone wants to connect with you on LinkedIn.

CRITICAL - YOU MUST FOLLOW THESE RULES EXACTLY:
1. Count how many different email accounts are in the input (e.g., if you see "=== Account: hemsra@gmail.com ===" and "=== Account: rkyeluru@gmail.com ===", that's 2 accounts)
2. You MUST create a section for EACH account you see in the input
3. For each account section, you MUST include ALL emails shown for that account
4. DO NOT stop after one account - continue until you've covered ALL accounts
5. DO NOT truncate or skip emails - include every single one
6. Group ALL emails by their monitored email account
7. Start each account section with "Email: [account]" on its own line
8. List ALL emails for that account below, each with Sender, Time, Subject, Summary
9. Use a blank line between emails within the same account
10. Use a blank line between different account sections
11. If you see 3 accounts in the input, your output MUST have 3 "Email:" sections
12. If you see 10 emails for an account, your output MUST list all 10 emails for that account
13. Do NOT include links in summaries - keep summaries concise
14. The "Email:" field is the inbox being watched, NOT the notification recipient

"""
    
    if emails:
        # Group emails by account for better presentation
        from collections import defaultdict
        emails_by_account = defaultdict(list)
        for email in emails:
            account = email.email_account if hasattr(email, 'email_account') and email.email_account else "unknown"
            emails_by_account[account].append(email)
        
        prompt += "\nEmail notifications (grouped by monitored account):\n\n"
        for account, account_emails in emails_by_account.items():
            prompt += f"=== Account: {account} ===\n"
            for i, email in enumerate(account_emails, 1):
                # Extract sender name/domain for context
                sender_info = email.sender.split('<')[0].strip() if '<' in email.sender else email.sender
                # Parse and format the timestamp
                try:
                    from datetime import datetime
                    email_time = datetime.fromisoformat(email.received_at.replace("Z", "+00:00"))
                    time_str = email_time.strftime("%b %d, %Y %I:%M %p")
                except:
                    time_str = email.received_at
                prompt += f"  {i}. From: {sender_info} | Time: {time_str} | Subject: {email.subject}\n     Content: {email.snippet[:300]}\n\n"
            prompt += "\n"
    
    if rss_items:
        prompt += "\nRSS items:\n"
        for i, item in enumerate(rss_items, 1):
            prompt += f"{i}. Source: {item.source} | Title: {item.title}\n   Content: {item.snippet[:300]}\n\n"
    
    return prompt


def summarize_email_individual(
    email: EmailNotification,
    client: LLMClient,
    config: LLMConfig
) -> str:
    """
    Summarize a single email individually using LLM.
    
    Args:
        email: Email notification to summarize.
        client: LLM client instance.
        config: LLM configuration.
        
    Returns:
        A concise summary string for this email.
    """
    prompt = f"""Summarize this email in a very concise way (maximum 2-3 sentences, under 100 words).

From: {email.sender}
Subject: {email.subject}
Content: {email.snippet[:500]}

Provide a brief, concise summary focusing on the key information. Do not include links or unnecessary details."""
    
    summary = client.complete(
        prompt,
        max_tokens=150,  # Shorter for individual summaries
        temperature=config.temperature
    )
    
    return summary.strip()


def summarize_notifications(
    emails: Sequence[EmailNotification],
    rss_items: Sequence[RSSItem],
    client: LLMClient,
    config: LLMConfig,
    summarize_individually: bool = True
) -> str:
    """
    Summarize notifications using an LLM client.
    
    Args:
        emails: Email notifications to summarize.
        rss_items: RSS items to summarize.
        client: LLM client instance.
        config: LLM configuration.
        summarize_individually: If True, summarize each email individually then aggregate.
        
    Returns:
        A summary string (may be empty if no items).
    """
    if not emails and not rss_items:
        return ""
    
    if summarize_individually:
        # Summarize each email individually, then aggregate
        from collections import defaultdict
        from datetime import datetime
        
        emails_by_account = defaultdict(list)
        for email in emails:
            account = email.email_account if hasattr(email, 'email_account') and email.email_account else "unknown"
            emails_by_account[account].append(email)
        
        # Summarize each email individually
        aggregated_summary = []
        for account in sorted(emails_by_account.keys()):
            account_emails = sorted(emails_by_account[account], key=lambda e: e.received_at, reverse=True)
            aggregated_summary.append(f"Email: {account}\n")
            
            for email in account_emails:
                try:
                    # Format time
                    email_time = datetime.fromisoformat(email.received_at.replace("Z", "+00:00"))
                    time_str = email_time.strftime("%b %d, %Y %I:%M %p")
                except:
                    time_str = email.received_at
                
                sender_info = email.sender.split('<')[0].strip() if '<' in email.sender else email.sender
                
                # Get individual summary
                individual_summary = summarize_email_individual(email, client, config)
                
                aggregated_summary.append(f"Sender: {sender_info}")
                aggregated_summary.append(f"Time: {time_str}")
                aggregated_summary.append(f"Subject: {email.subject}")
                aggregated_summary.append(f"Summary: {individual_summary}")
                aggregated_summary.append("")  # Blank line between emails
            
            aggregated_summary.append("")  # Blank line between accounts
        
        return "\n".join(aggregated_summary)
    else:
        # Original batch summarization
        from collections import defaultdict
        emails_by_account = defaultdict(list)
        for email in emails:
            account = email.email_account if hasattr(email, 'email_account') and email.email_account else "unknown"
            emails_by_account[account].append(email)
        
        sorted_emails_by_account = {}
        for account, account_emails in emails_by_account.items():
            sorted_account_emails = sorted(account_emails, key=lambda e: e.received_at, reverse=True)[:10]
            sorted_emails_by_account[account] = sorted_account_emails
        
        account_order = sorted(
            sorted_emails_by_account.keys(),
            key=lambda acc: sorted_emails_by_account[acc][0].received_at if sorted_emails_by_account[acc] else "",
            reverse=True
        )
        
        grouped_emails = []
        for account in account_order:
            grouped_emails.extend(sorted_emails_by_account[account])
        
        sorted_rss = sorted(rss_items, key=lambda r: r.published_at, reverse=True)[:5]
        
        prompt = build_summary_prompt(grouped_emails, sorted_rss)
        summary = client.complete(
            prompt,
            max_tokens=config.max_tokens,
            temperature=config.temperature
        )
        
        return summary.strip()

