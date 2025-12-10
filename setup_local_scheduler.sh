#!/bin/bash
# Quick setup script for local 10-minute scheduler on macOS

PROJECT_DIR="/Users/raviyeluru/linkedin_watcher_agent"
PLIST_FILE="$HOME/Library/LaunchAgents/com.notificationagent.plist"
LOGS_DIR="$PROJECT_DIR/logs"

echo "Setting up notification agent to run every 10 minutes..."

# Detect Python path (prefer pyenv, then venv, then system)
if [ -f "$PROJECT_DIR/.venv/bin/python3" ]; then
    PYTHON_PATH="$PROJECT_DIR/.venv/bin/python3"
    echo "✓ Using venv Python: $PYTHON_PATH"
elif command -v python3 &> /dev/null; then
    PYTHON_PATH=$(python3 -c "import sys; print(sys.executable)" 2>/dev/null)
    echo "✓ Using system Python: $PYTHON_PATH"
else
    PYTHON_PATH="/usr/bin/python3"
    echo "⚠ Using default Python: $PYTHON_PATH"
fi

# Verify Python has required packages
echo "Verifying Python installation..."
if ! "$PYTHON_PATH" -c "import feedparser, twilio, openai, dotenv" 2>/dev/null; then
    echo "⚠ WARNING: Required packages not found. Installing..."
    "$PYTHON_PATH" -m pip install -q -r "$PROJECT_DIR/requirements.txt" 2>/dev/null || {
        echo "❌ Failed to install packages. Please run: pip install -r requirements.txt"
        exit 1
    }
fi

# Create logs directory
mkdir -p "$LOGS_DIR"

# Create plist file
cat > "$PLIST_FILE" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.notificationagent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>-m</string>
        <string>linkedin_sms_agent.main</string>
        <string>--method</string>
        <string>email</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>StartInterval</key>
    <integer>600</integer>
    <key>StandardOutPath</key>
    <string>$LOGS_DIR/notification_agent.log</string>
    <key>StandardErrorPath</key>
    <string>$LOGS_DIR/notification_agent.error.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.pyenv/shims:$HOME/.pyenv/bin</string>
    </dict>
</dict>
</plist>
PLISTEOF

echo "✓ Created plist file: $PLIST_FILE"

# Unload if already exists
launchctl unload "$PLIST_FILE" 2>/dev/null

# Load the service
launchctl load "$PLIST_FILE"

echo "✓ Service loaded"
echo ""
echo "Service is now running every 10 minutes!"
echo ""
echo "Useful commands:"
echo "  Check status: launchctl list | grep notificationagent"
echo "  View logs: tail -f $LOGS_DIR/notification_agent.log"
echo "  Stop: launchctl unload $PLIST_FILE"
echo "  Start: launchctl load $PLIST_FILE"
