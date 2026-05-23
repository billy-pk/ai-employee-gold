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


STATE_FILE = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state/gmail_watcher.last_run')


def write_last_run(count: int, status: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {status} | emails:{count}"
    )


def main():
    print(f"\n[{datetime.now().isoformat()}] === Gmail Watcher Start ===")
    count = 0

    try:
        watcher = GmailWatcher()
        count = watcher.run_once()
        print(f"[{datetime.now().isoformat()}] Processed {count} email(s)")
        write_last_run(count, 'ok')
        return 0

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")
        write_last_run(count, f'error: {e}')
        return 1

    finally:
        print(f"[{datetime.now().isoformat()}] === Gmail Watcher End ===")


if __name__ == '__main__':
    sys.exit(main())
