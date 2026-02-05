#!/usr/bin/env python3
"""
Gmail Watcher Cron Entry Point

Runs the Gmail Watcher once and exits.
Designed for cron execution every 2 minutes.

Cron entry:
*/2 * * * * cd ~/vibe-coding-projects/ai-employee && uv run python scripts/run_gmail_watcher.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_gmail.log 2>&1
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.watchers.gmail_watcher import GmailWatcher


def main():
    print(f"\n[{datetime.now().isoformat()}] === Gmail Watcher Start ===")

    try:
        watcher = GmailWatcher()
        count = watcher.run_once()
        print(f"[{datetime.now().isoformat()}] Processed {count} email(s)")
        return 0

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")
        return 1

    finally:
        print(f"[{datetime.now().isoformat()}] === Gmail Watcher End ===")


if __name__ == '__main__':
    sys.exit(main())
