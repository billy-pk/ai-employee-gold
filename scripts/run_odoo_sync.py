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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.briefings.data_collectors import OdooDataCollector


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
        return 0
    else:
        print(f"\n[ERROR] Sync failed: {result['error']}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
