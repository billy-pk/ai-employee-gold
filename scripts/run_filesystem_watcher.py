#!/usr/bin/env python3
"""
File System Watcher Cron Entry Point

Runs the File System Watcher once and exits.
Designed for cron execution every 1 minute.

Cron entry:
*/1 * * * * cd ~/vibe-coding-projects/ai-employee && uv run python scripts/run_filesystem_watcher.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_filesystem.log 2>&1
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.watchers.filesystem_watcher import FileSystemWatcher


def main():
    print(f"\n[{datetime.now().isoformat()}] === File System Watcher Start ===")

    try:
        watcher = FileSystemWatcher()
        count = watcher.run_once()
        print(f"[{datetime.now().isoformat()}] Processed {count} file(s)")
        return 0

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")
        return 1

    finally:
        print(f"[{datetime.now().isoformat()}] === File System Watcher End ===")


if __name__ == '__main__':
    sys.exit(main())
