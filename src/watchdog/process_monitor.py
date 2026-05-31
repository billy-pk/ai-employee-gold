"""
Process Monitor - Monitor and restart failed watcher processes.

The Watchdog monitors all critical watcher processes via PID files,
detects failures, restarts processes, and alerts on persistent issues.
"""

import os
import signal
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from dotenv import load_dotenv

from ..utils.logger import get_logger
from ..utils.vault_helpers import get_vault_folder, log_to_vault

load_dotenv()


@dataclass
class WatchedProcess:
    """Configuration for a watched process."""
    name: str
    script_path: str
    pid_file: str
    restart_command: list[str] = field(default_factory=list)
    failure_count: int = 0
    last_check: Optional[datetime] = None
    last_restart: Optional[datetime] = None
    status: str = 'unknown'  # running, stopped, restarting, failed


class ProcessMonitor:
    """
    Process Monitor - Monitor and restart failed watcher processes.

    Monitors PID files for each watcher, checks if processes are alive,
    restarts failed processes, and tracks consecutive failures.
    """

    def __init__(self):
        """Initialize Process Monitor."""
        self.logger = get_logger('ProcessMonitor')
        self.vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))
        self.project_root = Path(__file__).parent.parent.parent
        self.logs = get_vault_folder('Logs')

        # Configuration
        self.check_interval = int(os.getenv('WATCHDOG_CHECK_INTERVAL', '60'))
        self.max_restart_attempts = int(os.getenv('WATCHDOG_MAX_RESTART_ATTEMPTS', '3'))

        # PID directory
        self.pid_dir = self.logs / 'pids'
        self.pid_dir.mkdir(parents=True, exist_ok=True)

        # Define watched processes
        self.processes = self._init_watched_processes()

        # Track restarts for the day
        self.daily_restarts = 0
        self.daily_restart_date = datetime.now().date()

        self.logger.info("Process Monitor initialized")
        self.logger.info(f"Monitoring {len(self.processes)} processes")
        self.logger.info(f"Max restart attempts: {self.max_restart_attempts}")

    def _init_watched_processes(self) -> dict[str, WatchedProcess]:
        """Initialize the list of processes to monitor."""
        scripts_dir = self.project_root / 'scripts'
        python_path = sys.executable

        processes = {
            'gmail_watcher': WatchedProcess(
                name='Gmail Watcher',
                script_path=str(scripts_dir / 'run_gmail_watcher.py'),
                pid_file=str(self.pid_dir / 'gmail_watcher.pid'),
                restart_command=[python_path, str(scripts_dir / 'run_gmail_watcher.py')]
            ),
            'filesystem_watcher': WatchedProcess(
                name='FileSystem Watcher',
                script_path=str(scripts_dir / 'run_filesystem_watcher.py'),
                pid_file=str(self.pid_dir / 'filesystem_watcher.pid'),
                restart_command=[python_path, str(scripts_dir / 'run_filesystem_watcher.py')]
            ),
            'finance_watcher': WatchedProcess(
                name='Finance Watcher',
                script_path=str(scripts_dir / 'run_finance_watcher.py'),
                pid_file=str(self.pid_dir / 'finance_watcher.pid'),
                restart_command=[python_path, str(scripts_dir / 'run_finance_watcher.py')]
            ),
        }

        return processes

    def _read_pid_file(self, pid_file: str) -> Optional[int]:
        """Read PID from a PID file."""
        pid_path = Path(pid_file)
        if not pid_path.exists():
            return None

        try:
            content = pid_path.read_text().strip()
            return int(content) if content else None
        except (ValueError, IOError) as e:
            self.logger.warning(f"Error reading PID file {pid_file}: {e}")
            return None

    def _write_pid_file(self, pid_file: str, pid: int):
        """Write PID to a PID file."""
        pid_path = Path(pid_file)
        pid_path.write_text(str(pid))

    def _remove_pid_file(self, pid_file: str):
        """Remove a PID file."""
        pid_path = Path(pid_file)
        if pid_path.exists():
            pid_path.unlink()

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with the given PID is running."""
        if pid is None:
            return False

        try:
            # Send signal 0 to check if process exists
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we don't have permission to signal it
            return True

    def check_process(self, process_key: str) -> dict:
        """
        Check the status of a single process.

        Args:
            process_key: Key of the process in self.processes

        Returns:
            Status dict with 'running', 'pid', 'status' fields
        """
        process = self.processes.get(process_key)
        if not process:
            return {'error': f'Unknown process: {process_key}'}

        pid = self._read_pid_file(process.pid_file)
        running = self._is_process_running(pid) if pid else False

        process.last_check = datetime.now()

        if running:
            process.status = 'running'
            process.failure_count = 0  # Reset on successful check
        else:
            if process.status == 'restarting':
                # Restart didn't work
                process.failure_count += 1
            process.status = 'stopped'

        return {
            'name': process.name,
            'running': running,
            'pid': pid,
            'status': process.status,
            'failure_count': process.failure_count
        }

    def restart_process(self, process_key: str) -> dict:
        """
        Restart a failed process.

        Args:
            process_key: Key of the process to restart

        Returns:
            Result dict with success status
        """
        process = self.processes.get(process_key)
        if not process:
            return {'success': False, 'error': f'Unknown process: {process_key}'}

        # Check if we've exceeded max restart attempts
        if process.failure_count >= self.max_restart_attempts:
            self.logger.error(
                f"{process.name} has failed {process.failure_count} times. "
                f"Manual intervention required."
            )
            process.status = 'failed'
            return {
                'success': False,
                'error': f'Max restart attempts ({self.max_restart_attempts}) exceeded',
                'alert': True
            }

        self.logger.info(f"Restarting {process.name}...")
        process.status = 'restarting'

        try:
            # Remove old PID file
            self._remove_pid_file(process.pid_file)

            # Start new process
            # Note: In cron mode, we run once and exit, so we don't actually
            # keep processes running. This is more for demonstration.
            # In a real scenario, you'd use a process manager like supervisord.
            proc = subprocess.Popen(
                process.restart_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Write new PID file
            self._write_pid_file(process.pid_file, proc.pid)

            process.last_restart = datetime.now()
            process.status = 'running'

            # Track daily restarts
            self._track_daily_restart()

            self.logger.info(f"{process.name} restarted with PID {proc.pid}")
            log_to_vault(f"Restarted {process.name} (PID: {proc.pid})", "watchdog")

            return {'success': True, 'pid': proc.pid}

        except Exception as e:
            self.logger.error(f"Failed to restart {process.name}: {e}")
            process.failure_count += 1
            process.status = 'stopped'
            return {'success': False, 'error': str(e)}

    def _track_daily_restart(self):
        """Track daily restart count, resetting at midnight."""
        today = datetime.now().date()
        if today != self.daily_restart_date:
            self.daily_restarts = 0
            self.daily_restart_date = today
        self.daily_restarts += 1

    def check_all(self) -> dict:
        """
        Check all monitored processes.

        Returns:
            Dict with status of all processes
        """
        results = {}
        for process_key in self.processes:
            results[process_key] = self.check_process(process_key)
        return results

    def run_health_check(self) -> dict:
        """
        Run a complete health check cycle.

        Checks all processes, restarts failed ones, and returns summary.

        Returns:
            Summary dict with check results and actions taken
        """
        self.logger.info("Running health check...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'processes': {},
            'restarts': [],
            'alerts': []
        }

        for process_key, process in self.processes.items():
            status = self.check_process(process_key)
            results['processes'][process_key] = status

            # Attempt restart if process is not running
            if not status['running'] and process.status != 'failed':
                restart_result = self.restart_process(process_key)
                results['restarts'].append({
                    'process': process.name,
                    'result': restart_result
                })

                if restart_result.get('alert'):
                    results['alerts'].append({
                        'process': process.name,
                        'message': f'{process.name} has exceeded max restart attempts',
                        'failure_count': process.failure_count
                    })

        # Update dashboard
        self._update_dashboard(results)

        # Log summary
        running_count = sum(1 for p in results['processes'].values() if p['running'])
        self.logger.info(
            f"Health check complete: {running_count}/{len(self.processes)} processes running"
        )

        if results['restarts']:
            self.logger.info(f"Restarts attempted: {len(results['restarts'])}")

        if results['alerts']:
            for alert in results['alerts']:
                self.logger.warning(f"ALERT: {alert['message']}")

        return results

    def _update_dashboard(self, results: dict):
        """
        Update the Dashboard.md with current health status.

        Args:
            results: Health check results
        """
        dashboard_path = self.vault_path / 'Dashboard.md'

        if not dashboard_path.exists():
            self.logger.warning("Dashboard.md not found - skipping update")
            return

        state_dir = Path('/mnt/d/AI_EMPLOYEE_VAULT/.state')
        state_files = {
            'gmail_watcher': 'gmail_watcher.last_run',
            'filesystem_watcher': 'filesystem_watcher.last_run',
            'finance_watcher': 'finance_watcher.last_run',
            'approval_executor': 'approval_executor.last_run',
            'claude_processor': 'claude_processor.last_run',
        }

        def read_last_run(key: str) -> str:
            path = state_dir / state_files.get(key, '')
            if path.exists():
                line = path.read_text().strip()
                return line.split(' | ')[0]  # just the timestamp part
            return '-'

        try:
            content = dashboard_path.read_text()

            # Build health table
            health_lines = [
                "## System Health",
                "",
                "| Service | Status | Restarts | Last Run |",
                "|---------|--------|----------|----------|",
            ]

            for process_key, process in self.processes.items():
                status = results['processes'].get(process_key, {})
                status_emoji = '🟢' if status.get('running') else '🔴'
                status_text = status.get('status', 'unknown').title()
                last_run = read_last_run(process_key)

                health_lines.append(
                    f"| {process.name} | {status_emoji} {status_text} | "
                    f"{process.failure_count} | {last_run} |"
                )

            health_lines.extend([
                "",
                f"**Last Watchdog Run:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Restarts Today:** {self.daily_restarts}",
            ])

            health_section = '\n'.join(health_lines)

            import re

            # Replace existing health section or append
            health_pattern = r'## System Health\n.*?(?=\n## |\n---|\Z)'
            if re.search(health_pattern, content, re.DOTALL):
                content = re.sub(health_pattern, lambda _: health_section, content, flags=re.DOTALL)
            else:
                status_match = re.search(r'(## System Status\n.*?)(\n## |\n---|\Z)', content, re.DOTALL)
                if status_match:
                    insert_pos = status_match.end(1)
                    content = content[:insert_pos] + '\n\n' + health_section + content[insert_pos:]

            # Also update Last Run column in the System Status table (3-column rows only)
            status_last_run = {
                'Gmail Watcher':      read_last_run('gmail_watcher'),
                'FileSystem Watcher': read_last_run('filesystem_watcher'),
                'Finance Watcher':    read_last_run('finance_watcher'),
            }
            for component, last_run in status_last_run.items():
                if last_run == '-':
                    continue
                # (?=\s*\n) ensures we only match 3-column rows — 4-column rows
                # (like System Health) have more content after the third pipe
                content = re.sub(
                    rf'\| {re.escape(component)} \|[^|]+\| [^|]+ \|(?=\s*\n)',
                    lambda m, lr=last_run: m.group(0).rsplit('|', 2)[0] + f'| {lr} |',
                    content
                )

            dashboard_path.write_text(content)
            self.logger.debug("Dashboard updated with health status")

        except Exception as e:
            self.logger.error(f"Failed to update dashboard: {e}")

    def get_health_summary(self) -> dict:
        """
        Get a summary of system health without running checks.

        Returns:
            Summary dict
        """
        return {
            'processes': {
                key: {
                    'name': proc.name,
                    'status': proc.status,
                    'failure_count': proc.failure_count,
                    'last_check': proc.last_check.isoformat() if proc.last_check else None,
                    'last_restart': proc.last_restart.isoformat() if proc.last_restart else None
                }
                for key, proc in self.processes.items()
            },
            'daily_restarts': self.daily_restarts,
            'max_restart_attempts': self.max_restart_attempts
        }

    def run_once(self) -> dict:
        """
        Single execution for cron - run health check and exit.

        Returns:
            Health check results
        """
        self.logger.info("Watchdog running (single execution mode)")
        return self.run_health_check()


# Singleton instance
_watchdog: Optional[ProcessMonitor] = None


def get_watchdog() -> ProcessMonitor:
    """Get the singleton ProcessMonitor instance."""
    global _watchdog
    if _watchdog is None:
        _watchdog = ProcessMonitor()
    return _watchdog


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Process Monitor - Monitor and restart watcher processes'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for cron)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status'
    )

    args = parser.parse_args()

    monitor = ProcessMonitor()

    if args.status:
        print("=== Process Status ===")
        results = monitor.check_all()
        for key, status in results.items():
            emoji = '🟢' if status['running'] else '🔴'
            print(f"  {emoji} {status['name']}: {status['status']} (PID: {status['pid']})")
    elif args.once:
        print("=== Watchdog (Single Run) ===")
        results = monitor.run_once()
        print(f"\nProcesses checked: {len(results['processes'])}")
        print(f"Restarts attempted: {len(results['restarts'])}")
        print(f"Alerts: {len(results['alerts'])}")
    else:
        print("Process Monitor")
        print("Use --once for single execution or --status to see current status")
