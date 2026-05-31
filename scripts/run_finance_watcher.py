#!/usr/bin/env python3
"""
Finance Watcher Runner Script

Runs the Finance Watcher in single-execution mode for cron.
Processes new bank CSV files and creates action items.

Cron usage:
    */5 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_finance_watcher.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


STATE_FILE = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state/finance_watcher.last_run')


def write_last_run(count: int, status: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {status} | files:{count}"
    )


def main():
    print(f"\n{'='*50}")
    print(f"Finance Watcher - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    try:
        from src.watchers.finance_watcher import FinanceWatcher

        watcher = FinanceWatcher()
        count = watcher.run_once()

        print(f"\nProcessed {count} CSV file(s)")
        write_last_run(count, 'ok')
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        write_last_run(0, f'error: {e}')
        return 1

    finally:
        print(f"\n{'='*50}")
        print("=== End ===")


if __name__ == '__main__':
    sys.exit(main())
