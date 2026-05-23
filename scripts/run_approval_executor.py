#!/usr/bin/env python3
"""
Approval Executor Cron Entry Point

Runs the Approval Executor once and exits.
Designed for cron execution every 1 minute.

Checks the Approved folder for files that the user has moved there,
and executes the approved actions (e.g., sending emails).

Cron entry:
*/1 * * * * cd ~/vibe-coding-projects/ai-employee && uv run python scripts/run_approval_executor.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_executor.log 2>&1
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.executors.approval_executor import ApprovalExecutor

STATE_FILE = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state/approval_executor.last_run')


def write_last_run(processed: int, success: int, status: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {status} | processed:{processed} success:{success}"
    )


def main():
    print(f"\n[{datetime.now().isoformat()}] === Approval Executor Start ===")

    try:
        executor = ApprovalExecutor()
        result = executor.run_once()

        processed = result.get('processed', 0)
        success = result.get('success', 0)
        failed = result.get('failed', 0)
        print(f"[{datetime.now().isoformat()}] Processed: {processed}, Success: {success}, Failed: {failed}")
        write_last_run(processed, success, 'error' if failed > 0 else 'ok')

        if failed > 0:
            return 1

        return 0

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")
        write_last_run(0, 0, f'error: {e}')
        return 1

    finally:
        print(f"[{datetime.now().isoformat()}] === Approval Executor End ===")


if __name__ == '__main__':
    sys.exit(main())
