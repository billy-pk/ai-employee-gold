#!/usr/bin/env python3
"""
Daily Odoo data sync runner for cron.

Usage:
    python scripts/run_odoo_sync.py

Cron example (run daily at 6 AM):
    0 6 * * * cd /path/to/ai-employee-gold && /path/to/uv run python scripts/run_odoo_sync.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.briefings.data_collectors import OdooDataCollector


STATE_FILE = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state/odoo_sync.last_run')


def write_last_run(status: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {status}"
    )


def main():
    """Run daily Odoo sync."""
    print("=" * 50)
    print("Daily Odoo Sync")
    print("=" * 50)

    collector = OdooDataCollector()
    result = collector.run_daily_sync()

    if result['success']:
        print("\n[SUCCESS] Sync completed")
        print(f"  Snapshot: {result['snapshot_path']}")
        print(f"  Brief: {result['brief_path']}")
        print("\nSummary:")
        for key, value in result['summary'].items():
            if isinstance(value, float):
                print(f"  - {key}: ${value:,.2f}")
            else:
                print(f"  - {key}: {value}")
        write_last_run('ok')
        return 0
    else:
        print(f"\n[ERROR] Sync failed: {result['error']}")
        write_last_run(f"error: {result['error']}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
