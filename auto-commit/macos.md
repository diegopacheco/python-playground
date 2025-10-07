## macOS Background Process Setup

### Using LaunchAgent

Create a LaunchAgent plist file:

```bash
nano ~/Library/LaunchAgents/com.autocommit.plist
```

Add the following configuration:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.autocommit</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/diegopacheco/Documents/git/diegopacheco/python-playground/auto-commit/auto-commit.sh</string>
        <string>/Users/diegopacheco/Documents/git/diegopacheco/php-playground/</string>
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
```

### Load and manage the LaunchAgent

Load the agent:
```bash
launchctl load ~/Library/LaunchAgents/com.autocommit.plist
```

Unload the agent:
```bash
launchctl unload ~/Library/LaunchAgents/com.autocommit.plist
```

Check if running:
```bash
launchctl list | grep autocommit
```

### Using Cron

Edit crontab:
```bash
crontab -e
```

Add this line:
```bash
10 0 * * * /Users/diegopacheco/Documents/git/diegopacheco/python-playground/auto-commit/auto-commit.sh /Users/diegopacheco/Documents/git/diegopacheco/php-playground/ >> /Users/diegopacheco/auto-commit.log 2>&1
```

List cron jobs:
```bash
crontab -l
```

Remove all cron jobs:
```bash
crontab -r
```
