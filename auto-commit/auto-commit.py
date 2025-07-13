import subprocess
import os
import sys
from datetime import datetime

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    repo_path = "/home/diego/git/diegopacheco/python-playground"
    os.chdir(repo_path)
    returncode, stdout, stderr = run_command("git status --porcelain")
    
    if returncode != 0:
        print(f"date:{datetime.now()} :: Error getting git status: {stderr}")
        sys.exit(1)
    
    lines = stdout.strip().split('\n')
    
    if not stdout.strip():
        print("date:{datetime.now()} :: No changes found.")
        sys.exit(0)
        
    lines = stdout.strip().split('\n')
    first_item = None
    
    for line in lines:
        if line.startswith('??'):
            item = line[3:].rstrip('/')
            first_item = item
            break
    
    if not first_item:
        print(f"date:{datetime.now()} :: No untracked files or folders found.")
        sys.exit(0)
    
    print(f"date:{datetime.now()} :: Found untracked item: {first_item}")
    
    returncode, stdout, stderr = run_command(f"git add '{first_item}'")
    if returncode != 0:
        print(f"date:{datetime.now()} :: Failed to add {first_item}: {stderr}")
        sys.exit(1)
    
    returncode, stdout, stderr = run_command(f"git commit -m 'added {first_item}'")
    if returncode != 0:
        print(f"date:{datetime.now()} :: Failed to commit {first_item}: {stderr}")
        sys.exit(1)
    
    returncode, stdout, stderr = run_command("git push")
    if returncode != 0:
        print(f"date:{datetime.now()} ::  Failed to push: {stderr}")
        sys.exit(1)

    print(f"date:{datetime.now()} :: Successfully committed and pushed: {first_item}")

if __name__ == "__main__":
    main()