#!/usr/bin/env python3
"""
Claude Processor Cron Entry Point

Runs the Claude Processor once and exits.
Designed for cron execution every 5 minutes.

SMART TRIGGERING:
- Checks if there are items to process BEFORE invoking Claude
- If no items exist, exits immediately without using Claude quota
- Only invokes Claude when there's actual work to do

This design allows frequent cron scheduling without wasting Claude quota.

Cron entry:
*/5 * * * * cd ~/vibe-coding-projects/ai-employee && uv run python scripts/run_claude_processor.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_processor.log 2>&1
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.processors.claude_processor import ClaudeProcessor

STATE_FILE = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state/claude_processor.last_run')


def write_last_run(status: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {status}"
    )


def main():
    print(f"\n[{datetime.now().isoformat()}] === Claude Processor Start ===")

    try:
        processor = ClaudeProcessor()
        result = processor.run_once()

        if result.get('invoked'):
            if result.get('success'):
                print(f"[{datetime.now().isoformat()}] SUCCESS: Processed {result.get('items_count')} item(s)")
                write_last_run(f"ok | items:{result.get('items_count', 0)}")
            else:
                print(f"[{datetime.now().isoformat()}] ERROR: {result.get('error')}")
                write_last_run(f"error: {result.get('error')}")
                return 1
        else:
            print(f"[{datetime.now().isoformat()}] SKIPPED: {result.get('reason')}")
            write_last_run(f"skipped:{result.get('reason')}")

        return 0

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")
        write_last_run(f'error: {e}')
        return 1

    finally:
        print(f"[{datetime.now().isoformat()}] === Claude Processor End ===")


if __name__ == '__main__':
    sys.exit(main())
