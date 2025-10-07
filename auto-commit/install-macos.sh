#!/bin/bash

REPO_BASE=~/Documents/git/diegopacheco
SCRIPT_PATH=/Users/diegopacheco/Documents/git/diegopacheco/python-playground/auto-commit/auto-commit.sh
PLIST_PATH=~/Library/LaunchAgents/com.autocommit.plist

echo "Available repositories:"
echo ""
repos=()
counter=1
for dir in "$REPO_BASE"/*; do
    if [ -d "$dir" ]; then
        repos+=("$dir")
        echo "$counter) $(basename "$dir")"
        ((counter++))
    fi
done
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
echo "Check status with: launchctl list | grep autocommit"
