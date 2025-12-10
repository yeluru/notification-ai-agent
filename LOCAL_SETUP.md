# Local Setup - Run Every 10 Minutes on macOS

This guide shows how to run the notification agent every 10 minutes on your Mac.

## Option 1: Using launchd (Recommended for macOS)

launchd is the native macOS scheduler and is more reliable than cron.

### Step 1: Create a plist file

Create the file: `~/Library/LaunchAgents/com.notificationagent.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.notificationagent</string>
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
    <integer>600</integer>
    <key>StandardOutPath</key>
    <string>/Users/raviyeluru/linkedin_watcher_agent/logs/notification_agent.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/raviyeluru/linkedin_watcher_agent/logs/notification_agent.error.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

**Important:** Update the paths:
- `WorkingDirectory`: Change to your actual project path
- `StandardOutPath` and `StandardErrorPath`: Change to your desired log paths

### Step 2: Create logs directory

```bash
mkdir -p /Users/raviyeluru/linkedin_watcher_agent/logs
```

### Step 3: Load the service

```bash
launchctl load ~/Library/LaunchAgents/com.notificationagent.plist
```

### Step 4: Check status

```bash
launchctl list | grep notificationagent
```

### Useful Commands

**Start the service:**
```bash
launchctl start com.notificationagent
```

**Stop the service:**
```bash
launchctl stop com.notificationagent
```

**Unload (remove) the service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.notificationagent.plist
```

**View logs:**
```bash
tail -f /Users/raviyeluru/linkedin_watcher_agent/logs/notification_agent.log
```

## Option 2: Using Cron (Alternative)

### Step 1: Edit crontab

```bash
crontab -e
```

### Step 2: Add this line

```bash
*/10 * * * * cd /Users/raviyeluru/linkedin_watcher_agent && /usr/bin/python3 -m linkedin_sms_agent.main --method email >> /Users/raviyeluru/linkedin_watcher_agent/logs/cron.log 2>&1
```

**Important:** Update the path to match your project directory.

### Step 3: Create logs directory

```bash
mkdir -p /Users/raviyeluru/linkedin_watcher_agent/logs
```

### Step 4: Verify crontab

```bash
crontab -l
```

## Testing

Before setting up the scheduler, test manually:

```bash
cd /Users/raviyeluru/linkedin_watcher_agent
python3 -m linkedin_sms_agent.main --method email
```

## Troubleshooting

### launchd not running

1. Check if service is loaded:
   ```bash
   launchctl list | grep notificationagent
   ```

2. Check logs:
   ```bash
   tail -f ~/Library/LaunchAgents/com.notificationagent.plist
   cat /Users/raviyeluru/linkedin_watcher_agent/logs/notification_agent.error.log
   ```

3. Reload the service:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.notificationagent.plist
   launchctl load ~/Library/LaunchAgents/com.notificationagent.plist
   ```

### Cron not running

1. Check if cron is enabled (macOS may require permission):
   ```bash
   # Grant Full Disk Access to Terminal/your terminal app in System Preferences > Security & Privacy
   ```

2. Check cron logs:
   ```bash
   tail -f /Users/raviyeluru/linkedin_watcher_agent/logs/cron.log
   ```

3. Verify crontab:
   ```bash
   crontab -l
   ```

### Python path issues

If you're using a virtual environment, update the plist or crontab to use the venv Python:

```bash
# In plist, change:
<string>/Users/raviyeluru/linkedin_watcher_agent/.venv/bin/python3</string>

# Or in crontab:
*/10 * * * * cd /Users/raviyeluru/linkedin_watcher_agent && .venv/bin/python3 -m linkedin_sms_agent.main --method email >> logs/cron.log 2>&1
```

## Schedule Options

- **Every 10 minutes**: `*/10 * * * *` (cron) or `StartInterval: 600` (launchd)
- **Every 15 minutes**: `*/15 * * * *` (cron) or `StartInterval: 900` (launchd)
- **Every 5 minutes**: `*/5 * * * *` (cron) or `StartInterval: 300` (launchd)

## Recommendation

**Use launchd** - It's more reliable on macOS, handles system restarts better, and provides better logging.

