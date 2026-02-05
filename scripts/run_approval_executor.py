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


def main():
    print(f"\n[{datetime.now().isoformat()}] === Approval Executor Start ===")

    try:
        executor = ApprovalExecutor()
        result = executor.run_once()

        print(f"[{datetime.now().isoformat()}] Processed: {result.get('processed')}, Success: {result.get('success')}, Failed: {result.get('failed')}")

        if result.get('failed', 0) > 0:
            return 1

        return 0

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")
        return 1

    finally:
        print(f"[{datetime.now().isoformat()}] === Approval Executor End ===")


if __name__ == '__main__':
    sys.exit(main())
