import subprocess
import os
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/auto-commit.log")
DRY_RUN_MODE = False

def log_message(message):
    if DRY_RUN_MODE:
        message = f"[DRY-RUN] {message}"
    print(message)
    with open(LOG_FILE, 'a') as f:
        f.write(message + '\n')

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    global DRY_RUN_MODE

    if len(sys.argv) < 2:
        log_message(f"date:{datetime.now()} :: Usage: {sys.argv[0]} <repository_path> [--dry-run]")
        sys.exit(1)

    repo_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    DRY_RUN_MODE = dry_run

    if not os.path.isdir(repo_path):
        log_message(f"date:{datetime.now()} :: Error: {repo_path} is not a valid directory")
        sys.exit(1)

    os.chdir(repo_path)

    file_count = len([f for f in os.listdir('.') if os.path.isfile(f)])
    mode = "DRY-RUN" if dry_run else "LIVE"
    log_message(f"date:{datetime.now()} :: Repository: {repo_path} | Mode: {mode} | Files in directory: {file_count}")
    returncode, stdout, stderr = run_command("git status --porcelain")

    if returncode != 0:
        log_message(f"date:{datetime.now()} :: Error getting git status: {stderr}")
        sys.exit(1)

    lines = stdout.strip().split('\n')
    if not stdout.strip():
        log_message(f"date:{datetime.now()} :: No changes found.")
        sys.exit(0)
        
    lines = stdout.strip().split('\n')
    first_item = None
    
    for line in lines:
        if line.startswith('??'):
            item = line[3:].rstrip('/')
            first_item = item
            break
    
    if not first_item:
        log_message(f"date:{datetime.now()} :: No untracked files or folders found.")
        sys.exit(0)

    log_message(f"date:{datetime.now()} :: Found untracked item: {first_item}")

    if dry_run:
        log_message(f"date:{datetime.now()} :: Would add: {first_item}")
        log_message(f"date:{datetime.now()} :: Would commit with message: 'added {first_item}'")
        log_message(f"date:{datetime.now()} :: Would push to remote")
        sys.exit(0)

    returncode, stdout, stderr = run_command(f"git add '{first_item}'")
    if returncode != 0:
        log_message(f"date:{datetime.now()} :: Failed to add {first_item}: {stderr}")
        sys.exit(1)

    returncode, stdout, stderr = run_command(f"git commit -m 'added {first_item}'")
    if returncode != 0:
        log_message(f"date:{datetime.now()} :: Failed to commit {first_item}: {stderr}")
        sys.exit(1)

    returncode, stdout, stderr = run_command("git push")
    if returncode != 0:
        log_message(f"date:{datetime.now()} ::  Failed to push: {stderr}")
        sys.exit(1)

    log_message(f"date:{datetime.now()} :: Successfully committed and pushed: {first_item}")

if __name__ == "__main__":
    main()
