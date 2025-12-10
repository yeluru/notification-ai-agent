# Notification Agent (Email & SMS)

A production-quality Python agent that monitors email inboxes and RSS feeds for important notifications, summarizes them using an LLM, and sends concise summaries via **email or SMS**.

**Features:**
- ✅ Monitors multiple email accounts (Gmail, Outlook, Yahoo, custom domains)
- ✅ Fetches unread emails from last 15 minutes
- ✅ Individual LLM summarization for each email
- ✅ Sends one aggregate email summary
- ✅ Runs automatically every 15 minutes (cron/scheduler)
- ✅ Production-ready with error handling and logging

## Features

- **Email Monitoring** - IMAP-based email fetching with configurable filters
- **RSS Feed Support** - Monitor multiple RSS/Atom feeds
- **Smart Filtering** - Filter by sender domains and subject keywords
- **LLM Summarization** - Concise SMS-friendly summaries (2-3 lines)
- **SMS Notifications** - Twilio integration for SMS delivery
- **State Management** - SQLite database tracks seen items to avoid duplicates
- **Jitter Scheduling** - Randomized run times to avoid fixed patterns
- **Production Ready** - Error handling, logging, and clean architecture

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**

   Copy the example file and fill in your values:
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your actual credentials:

   See `.env.example` for all available configuration options.
   
   **Minimum required configuration:**
   ```bash
   # Email accounts to monitor
   EMAIL_ACCOUNTS=your-email@gmail.com
   EMAIL_PASSWORD_your-email@gmail.com=your-app-password
   
   # Notification settings
   SEND_SUMMARY_FROM_EMAIL=your-sender@gmail.com
   SEND_SUMMARY_TO_EMAIL=your-recipient@example.com
   
   # Twilio (required)
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_FROM_NUMBER=+1234567890
   TWILIO_TO_NUMBER=+0987654321
   
   # LLM (required)
   LLM_API_KEY=your_openai_api_key
   ```

   Or export them in your shell environment.

## Configuration Details

### Email Configuration

**Single Account (Default):**
- **EMAIL_HOST**: IMAP server hostname (e.g., `imap.gmail.com`, `outlook.office365.com`)
- **EMAIL_PORT**: IMAP port (usually 993 for SSL, 143 for non-SSL)
- **EMAIL_USERNAME**: Your email address
- **EMAIL_PASSWORD**: Your email password or app-specific password
  - For Gmail: Use an [App Password](https://support.google.com/accounts/answer/185833)
  - For Outlook: May need app password or OAuth
- **EMAIL_USE_SSL**: Set to `true` for SSL/TLS (recommended)
- **EMAIL_FOLDER**: IMAP folder to monitor (e.g., `INBOX`, `[Gmail]/All Mail`)
- **EMAIL_FROM_FILTERS**: Comma-separated list of sender filters (e.g., `@linkedin.com,@example.com`)
- **EMAIL_SUBJECT_KEYWORDS**: Comma-separated list of subject keywords to match

**Multiple Accounts (Recommended - Simple Format):**
The easiest way to add multiple accounts - just list them and provide passwords:

```bash
# List all email accounts to monitor
EMAIL_ACCOUNTS=account1@gmail.com,account2@gmail.com,account3@outlook.com

# Provide password for each account (use the full email as key)
EMAIL_PASSWORD_account1@gmail.com=app_password_1
EMAIL_PASSWORD_account2@gmail.com=app_password_2
EMAIL_PASSWORD_account3@outlook.com=app_password_3
```

All accounts will use the same EMAIL_HOST, EMAIL_PORT, EMAIL_USE_SSL settings. To add more accounts, just add them to EMAIL_ACCOUNTS and provide their passwords - no code changes needed!

**Alternative - Numbered Format:**
If you prefer, you can also use numbered suffixes:
- **EMAIL_HOST_1**: IMAP host for second account
- **EMAIL_USERNAME_1**: Email address for second account
- **EMAIL_PASSWORD_1**: Password/app password for second account
- **EMAIL_PORT_1**: Port for second account (optional, defaults to primary port)

For third account, use `_2` suffix, and so on. All accounts share the same filters (EMAIL_FROM_FILTERS, EMAIL_SUBJECT_KEYWORDS).

### RSS Configuration

- **RSS_ENABLED**: Set to `true` to enable RSS feeds
- **RSS_FEEDS**: Comma-separated list of RSS/Atom feed URLs

### Twilio Configuration

- **TWILIO_ACCOUNT_SID**: Your Twilio Account SID
- **TWILIO_AUTH_TOKEN**: Your Twilio Auth Token
- **TWILIO_FROM_NUMBER**: Twilio phone number (sender)
- **TWILIO_TO_NUMBER**: Your phone number (recipient)

### LLM Configuration

- **LLM_PROVIDER**: `openai` or `generic_http` (for OpenAI-compatible APIs)
- **LLM_API_KEY**: Your LLM API key
- **LLM_MODEL**: Model name (e.g., `gpt-4o-mini`, `gpt-4`)
- **LLM_BASE_URL**: Optional custom API endpoint
- **LLM_MAX_TOKENS**: Maximum tokens in summary (default: 1000, recommended: 2000 for multiple accounts)
- **LLM_TEMPERATURE**: Sampling temperature 0.0-1.0 (default: 0.2, lower is better for consistent summaries)

### Email Fetch Configuration

- **MAX_EMAILS_PER_ACCOUNT**: Maximum emails to fetch per account per run (default: 50)

### Scheduler Configuration

- **MIN_GAP_MINUTES**: Minimum minutes between runs (default: 30)
- **MAX_GAP_MINUTES**: Maximum minutes between runs (default: 120)

The agent uses jitter logic: if invoked frequently (e.g., every 10 minutes via cron), it will only actually run when the gap is appropriate.

### Notification Configuration

- **NOTIFICATION_METHOD**: `sms` (default) or `email`
- **NOTIFICATION_EMAIL**: Email address for email notifications (required if using email method)

## Usage

### Run Once (Manual)

```bash
# Email notifications (default with NOTIFICATION_METHOD=email)
python -m linkedin_sms_agent.main --method email

# SMS notifications
python -m linkedin_sms_agent.main --method sms

# Reset seen items to reprocess all emails
python -m linkedin_sms_agent.main --reset-seen-email
```

### Run Automatically (Cron)

**Local/Server Setup:**
```bash
# Add to crontab (runs every 15 minutes)
*/15 * * * * cd /path/to/project && /usr/bin/python3 -m linkedin_sms_agent.main --method email >> /var/log/agent.log 2>&1
```

**Render.com Deployment:**
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on deploying to Render.com as a cron job.

## How It Works

1. **Fetches Unread Emails** - Connects to all configured email accounts via IMAP
2. **Time Window** - Gets unread emails from last 15 minutes (configurable)
3. **Individual Summarization** - Each email is summarized individually by LLM
4. **Aggregate Summary** - All summaries combined into one email, grouped by account
5. **Sends Notification** - Sends aggregate summary via email (or SMS)
6. **Updates Database** - Marks items as seen to avoid duplicates

**Note:** The agent runs every 15 minutes (via cron) and processes unread emails from the last 15 minutes. No scheduler jitter - designed for fixed-interval cron jobs.

## Project Structure

```
linkedin_sms_agent/
├── __init__.py
├── config.py              # Configuration management
├── db.py                  # SQLite database operations
├── models.py              # Data models (EmailNotification, RSSItem)
├── email_client.py        # IMAP email fetching
├── rss_client.py          # RSS feed fetching
├── llm_client.py          # Abstract LLM interface
├── openai_client.py       # OpenAI and generic HTTP LLM clients
├── summarizer.py          # LLM prompt building and summarization
├── twilio_notifier.py     # Twilio SMS notifications
├── scheduler.py           # Jitter-based scheduling logic
└── main.py                # Main entry point
```

## Email Setup Examples

### Gmail

1. Enable 2-factor authentication
2. Generate an [App Password](https://support.google.com/accounts/answer/185833)
3. Use these settings:
   ```
   EMAIL_HOST=imap.gmail.com
   EMAIL_PORT=993
   EMAIL_USE_SSL=true
   EMAIL_FOLDER=INBOX
   EMAIL_PASSWORD=<your-app-password>
   ```

### Outlook/Office 365

1. Enable 2-factor authentication
2. Generate an app password
3. Use these settings:
   ```
   EMAIL_HOST=outlook.office365.com
   EMAIL_PORT=993
   EMAIL_USE_SSL=true
   EMAIL_FOLDER=INBOX
   EMAIL_PASSWORD=<your-app-password>
   ```

## Troubleshooting

### Email Connection Issues

- **"Authentication failed"**: Check username/password, use app password for 2FA accounts
- **"Cannot select folder"**: Verify folder name (case-sensitive for some servers)
- **"Connection timeout"**: Check firewall, verify host/port

### No Notifications Found

- Check email filters match your criteria
- Verify emails are unread (agent only checks UNSEEN messages)
- Check RSS feeds are accessible and valid

### SMS Not Sent

- Verify Twilio credentials are correct
- Check phone numbers are in E.164 format (+1234567890)
- Ensure Twilio account has SMS capabilities enabled

### LLM Errors

- Verify API key is correct
- Check model name is valid for your provider
- Verify API rate limits and quotas

## Logging

Set `LOG_LEVEL=DEBUG` in your environment for detailed logging:

```bash
LOG_LEVEL=DEBUG python -m linkedin_sms_agent.main
```

## Database Schema

The SQLite database contains:

**`seen_items` table:**
- `id` (TEXT): Item identifier
- `source` (TEXT): "email" or "rss"
- `first_seen_at` (TEXT): ISO 8601 timestamp
- Primary key: (id, source)

**`meta` table:**
- `key` (TEXT PRIMARY KEY): Metadata key
- `value` (TEXT): Metadata value
- Stores `last_run` timestamp

## Security Notes

- Never commit `.env` files or credentials to version control
- Use app-specific passwords for email accounts
- Store credentials securely (environment variables, secret managers)
- The agent only reads emails, never modifies or deletes them

## License

This is a personal project. Use at your own risk and responsibility.
