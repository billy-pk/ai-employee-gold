#!/usr/bin/env python3
"""
Watchdog Runner Script

Runs the Process Monitor in single-execution mode for cron.
Checks all watcher processes and restarts any that have failed.

Cron usage:
    */5 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_watchdog.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()


STATE_FILE = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state/watchdog.last_run')


def write_last_run(running: int, total: int, status: str):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {status} | processes:{running}/{total}"
    )


def main():
    print(f"\n{'='*50}")
    print(f"Watchdog - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    try:
        from src.watchdog.process_monitor import ProcessMonitor

        monitor = ProcessMonitor()
        results = monitor.run_once()

        # Print summary
        running = sum(1 for p in results['processes'].values() if p['running'])
        total = len(results['processes'])

        print(f"\nProcesses: {running}/{total} running")

        for key, status in results['processes'].items():
            emoji = '🟢' if status['running'] else '🔴'
            print(f"  {emoji} {status['name']}: {status['status']}")

        if results['restarts']:
            print(f"\nRestarts: {len(results['restarts'])}")
            for restart in results['restarts']:
                success = '✓' if restart['result'].get('success') else '✗'
                print(f"  {success} {restart['process']}")

        if results['alerts']:
            print(f"\n⚠️  ALERTS:")
            for alert in results['alerts']:
                print(f"  - {alert['message']}")

        write_last_run(running, total, 'ok')
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        write_last_run(0, 0, f'error: {e}')
        return 1

    finally:
        print(f"\n{'='*50}")
        print("=== End ===")


if __name__ == '__main__':
    sys.exit(main())
