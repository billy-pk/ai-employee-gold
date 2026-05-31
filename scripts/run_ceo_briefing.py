#!/usr/bin/env python3
"""
CEO Briefing runner for cron.

Usage:
    python scripts/run_ceo_briefing.py

Cron example (run Sunday at 11 PM):
    0 23 * * 0 cd /path/to/ai-employee-gold && /path/to/uv run python scripts/run_ceo_briefing.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.briefings.ceo_briefing import CEOBriefingGenerator


STATE_FILE = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state/ceo_briefing.last_run')


def write_last_run(status: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {status}"
    )


def main():
    """Generate weekly CEO briefing."""
    print("=" * 50)
    print("CEO Weekly Briefing Generator")
    print("=" * 50)
    print()

    generator = CEOBriefingGenerator()
    result = generator.generate(period_days=7)

    if result['success']:
        print("[SUCCESS] Briefing generated")
        print(f"  Briefing: {result['briefing_path']}")
        print(f"  Data: {result['data_path']}")
        print()
        print("Summary:")
        for key, value in result['summary'].items():
            print(f"  - {key}: {value}")
        write_last_run('ok')
        return 0
    else:
        print(f"[ERROR] Generation failed: {result['error']}")
        write_last_run(f"error: {result['error']}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
