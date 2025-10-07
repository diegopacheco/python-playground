#!/bin/bash

REPO_BASE=~/Documents/git/diegopacheco
SCRIPT_PATH=/Users/diegopacheco/Documents/git/diegopacheco/python-playground/auto-commit/auto-commit.sh
PLIST_PATH=~/Library/LaunchAgents/com.autocommit.plist
LOG_FILE=~/auto-commit.log

echo "Cleaning up previous log file..."
echo "" > "$LOG_FILE"
echo "Log file cleaned: $LOG_FILE"
echo ""

echo "Scanning repositories with uncommitted files..."
echo ""
repos=()
counter=1
for dir in "$REPO_BASE"/*; do
    if [ -d "$dir/.git" ]; then
        cd "$dir"
        status=$(git status --porcelain 2>/dev/null)
        if [ -n "$status" ]; then
            change_count=$(echo "$status" | wc -l | xargs)
            repos+=("$dir")
            echo "$counter) $(basename "$dir") [$change_count changes]"
            ((counter++))
        fi
    fi
done
cd - > /dev/null

if [ ${#repos[@]} -eq 0 ]; then
    echo "No repositories with uncommitted files found."
    exit 0
fi
echo ""
read -p "Select repository number: " selection

if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt "${#repos[@]}" ]; then
    echo "Invalid selection"
    exit 1
fi

SELECTED_REPO="${repos[$((selection-1))]}"
echo ""
echo "Selected repository: $SELECTED_REPO"
echo ""

if [ -f "$PLIST_PATH" ]; then
    echo "Unloading existing background job..."
    launchctl unload "$PLIST_PATH" 2>/dev/null
fi

echo "Creating LaunchAgent plist..."
cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.autocommit</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_PATH</string>
        <string>$SELECTED_REPO</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>10</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/diegopacheco/auto-commit-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/diegopacheco/auto-commit-stderr.log</string>
</dict>
</plist>
EOF

echo "Loading LaunchAgent..."
launchctl load "$PLIST_PATH"

echo ""
echo "Background job installed successfully!"
echo "Repository: $SELECTED_REPO"
echo "Schedule: Daily at 00:10"
echo ""

echo "Background process status:"
launchctl list | grep autocommit
echo ""

CURRENT_HOUR=$(date +%H)
CURRENT_MINUTE=$(date +%M)
if [ "$CURRENT_HOUR" -lt 0 ] || ( [ "$CURRENT_HOUR" -eq 0 ] && [ "$CURRENT_MINUTE" -lt 10 ] ); then
    NEXT_RUN=$(date +"%Y-%m-%d 00:10:00")
else
    NEXT_RUN=$(date -v+1d +"%Y-%m-%d 00:10:00")
fi
echo "Next scheduled run: $NEXT_RUN"
echo ""

if [ -f "$LOG_FILE" ]; then
    echo "Current logs from $LOG_FILE:"
    cat "$LOG_FILE"
else
    echo "No logs yet in $LOG_FILE"
fi
