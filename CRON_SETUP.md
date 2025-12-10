# Automatic 15-Minute Email Agent Setup

## Overview
The agent now runs automatically every 15 minutes, checking for UNREAD emails from the last 15 minutes, summarizing each individually, and sending one aggregate email.

## Setup Instructions

### macOS (using launchd)

1. Create a plist file: `~/Library/LaunchAgents/com.emailagent.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.emailagent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>-m</string>
        <string>linkedin_sms_agent.main</string>
        <string>--method</string>
        <string>email</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/raviyeluru/linkedin_watcher_agent</string>
    <key>StartInterval</key>
    <integer>900</integer>
    <key>StandardOutPath</key>
    <string>/Users/raviyeluru/linkedin_watcher_agent/logs/email_agent.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/raviyeluru/linkedin_watcher_agent/logs/email_agent.error.log</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

2. Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.emailagent.plist
```

3. Check status:
```bash
launchctl list | grep emailagent
```

### Linux (using cron)

1. Edit crontab:
```bash
crontab -e
```

2. Add this line:
```
*/15 * * * * cd /path/to/linkedin_watcher_agent && /usr/bin/python3 -m linkedin_sms_agent.main --method email >> /var/log/email_agent.log 2>&1
```

## Configuration

Set in `.env`:
- `EMAIL_CHECK_MINUTES=15` - How many minutes back to check for unread emails
- `SEND_SUMMARY_FROM_EMAIL=hemsra@gmail.com` - Email to send summaries from
- `SEND_SUMMARY_TO_EMAIL=raviyeluru@compsciprep.com` - Email to send summaries to

## How It Works

1. **Every 15 minutes**: Agent wakes up (via cron/launchd)
2. **Fetches UNREAD emails**: From last 15 minutes from all configured accounts
3. **Top 10 per account**: Gets up to 10 most recent unread emails per account
4. **Individual summarization**: Each email is summarized individually by LLM
5. **Aggregate email**: All summaries combined into one email, grouped by account
6. **Sends summary**: To `SEND_SUMMARY_TO_EMAIL`

## Manual Testing

Run manually to test:
```bash
python -m linkedin_sms_agent.main --method email
```

## Troubleshooting

- Check logs: `/var/log/email_agent.log` or `logs/email_agent.log`
- Verify cron is running: `crontab -l`
- Test IMAP connection manually
- Check that emails are actually unread in your inbox
