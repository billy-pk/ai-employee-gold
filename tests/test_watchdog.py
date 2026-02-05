"""Tests for the Watchdog Process Monitor module."""

import os
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from src.watchdog.process_monitor import ProcessMonitor, WatchedProcess


class TestProcessMonitor:
    """Test cases for ProcessMonitor class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Logs' / 'pids').mkdir(parents=True)
            # Create minimal Dashboard.md
            (vault / 'Dashboard.md').write_text("""# Dashboard

## System Status

| Component | Status |
|-----------|--------|
| Test | Ready |

## Other Section
""")
            yield vault

    @pytest.fixture
    def monitor(self, temp_vault, monkeypatch):
        """Create a ProcessMonitor with temp vault."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))
        monkeypatch.setenv('WATCHDOG_MAX_RESTART_ATTEMPTS', '3')
        return ProcessMonitor()

    def test_initialization(self, monitor, temp_vault):
        """Test that ProcessMonitor initializes correctly."""
        assert monitor.vault_path == temp_vault
        assert monitor.max_restart_attempts == 3
        assert len(monitor.processes) == 3
        assert 'gmail_watcher' in monitor.processes
        assert 'filesystem_watcher' in monitor.processes
        assert 'finance_watcher' in monitor.processes

    def test_read_pid_file_not_exists(self, monitor):
        """Test reading non-existent PID file."""
        pid = monitor._read_pid_file('/nonexistent/file.pid')
        assert pid is None

    def test_read_pid_file_exists(self, monitor, temp_vault):
        """Test reading existing PID file."""
        pid_file = temp_vault / 'Logs' / 'pids' / 'test.pid'
        pid_file.write_text('12345')

        pid = monitor._read_pid_file(str(pid_file))
        assert pid == 12345

    def test_write_pid_file(self, monitor, temp_vault):
        """Test writing PID file."""
        pid_file = temp_vault / 'Logs' / 'pids' / 'test.pid'
        monitor._write_pid_file(str(pid_file), 54321)

        assert pid_file.exists()
        assert pid_file.read_text() == '54321'

    def test_remove_pid_file(self, monitor, temp_vault):
        """Test removing PID file."""
        pid_file = temp_vault / 'Logs' / 'pids' / 'test.pid'
        pid_file.write_text('12345')

        monitor._remove_pid_file(str(pid_file))
        assert not pid_file.exists()

    def test_is_process_running_current_process(self, monitor):
        """Test checking if current process is running."""
        current_pid = os.getpid()
        assert monitor._is_process_running(current_pid) is True

    def test_is_process_running_nonexistent(self, monitor):
        """Test checking if nonexistent process is running."""
        # Use a very high PID that's unlikely to exist
        fake_pid = 999999999
        assert monitor._is_process_running(fake_pid) is False

    def test_is_process_running_none(self, monitor):
        """Test checking None PID."""
        assert monitor._is_process_running(None) is False

    def test_check_process_no_pid_file(self, monitor):
        """Test checking process with no PID file."""
        result = monitor.check_process('gmail_watcher')

        assert result['name'] == 'Gmail Watcher'
        assert result['running'] is False
        assert result['pid'] is None

    def test_check_process_with_running_pid(self, monitor, temp_vault):
        """Test checking process with running PID."""
        # Create PID file with current process PID
        process = monitor.processes['gmail_watcher']
        pid_path = Path(process.pid_file)
        pid_path.write_text(str(os.getpid()))

        result = monitor.check_process('gmail_watcher')

        assert result['running'] is True
        assert result['pid'] == os.getpid()
        assert result['status'] == 'running'

    def test_check_process_with_stale_pid(self, monitor, temp_vault):
        """Test checking process with stale (dead) PID."""
        # Create PID file with fake PID
        process = monitor.processes['gmail_watcher']
        pid_path = Path(process.pid_file)
        pid_path.write_text('999999999')

        result = monitor.check_process('gmail_watcher')

        assert result['running'] is False
        assert result['status'] == 'stopped'

    def test_check_process_unknown(self, monitor):
        """Test checking unknown process."""
        result = monitor.check_process('unknown_process')
        assert 'error' in result

    def test_check_all(self, monitor):
        """Test checking all processes."""
        results = monitor.check_all()

        assert len(results) == 3
        assert 'gmail_watcher' in results
        assert 'filesystem_watcher' in results
        assert 'finance_watcher' in results

    def test_restart_process_exceeds_max_attempts(self, monitor):
        """Test restart when max attempts exceeded."""
        process = monitor.processes['gmail_watcher']
        process.failure_count = 3  # Already at max

        result = monitor.restart_process('gmail_watcher')

        assert result['success'] is False
        assert 'exceeded' in result['error'].lower()
        assert result.get('alert') is True
        assert process.status == 'failed'

    @patch('subprocess.Popen')
    def test_restart_process_success(self, mock_popen, monitor):
        """Test successful process restart."""
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc

        result = monitor.restart_process('gmail_watcher')

        assert result['success'] is True
        assert result['pid'] == 12345
        assert monitor.processes['gmail_watcher'].status == 'running'
        assert monitor.daily_restarts == 1

    @patch('subprocess.Popen')
    def test_restart_process_failure(self, mock_popen, monitor):
        """Test failed process restart."""
        mock_popen.side_effect = Exception("Failed to start")

        result = monitor.restart_process('gmail_watcher')

        assert result['success'] is False
        assert 'Failed to start' in result['error']
        assert monitor.processes['gmail_watcher'].failure_count == 1

    def test_run_health_check(self, monitor):
        """Test running health check."""
        results = monitor.run_health_check()

        assert 'timestamp' in results
        assert 'processes' in results
        assert 'restarts' in results
        assert 'alerts' in results
        assert len(results['processes']) == 3

    def test_daily_restart_tracking(self, monitor):
        """Test daily restart counter."""
        monitor._track_daily_restart()
        assert monitor.daily_restarts == 1

        monitor._track_daily_restart()
        assert monitor.daily_restarts == 2

    def test_daily_restart_reset(self, monitor):
        """Test daily restart counter reset."""
        from datetime import date, timedelta

        monitor.daily_restarts = 5
        monitor.daily_restart_date = date.today() - timedelta(days=1)

        monitor._track_daily_restart()

        assert monitor.daily_restarts == 1
        assert monitor.daily_restart_date == date.today()

    def test_get_health_summary(self, monitor):
        """Test getting health summary."""
        summary = monitor.get_health_summary()

        assert 'processes' in summary
        assert 'daily_restarts' in summary
        assert 'max_restart_attempts' in summary
        assert len(summary['processes']) == 3

    def test_update_dashboard(self, monitor, temp_vault):
        """Test dashboard update."""
        results = {
            'processes': {
                'gmail_watcher': {'running': True, 'status': 'running'},
                'filesystem_watcher': {'running': True, 'status': 'running'},
                'finance_watcher': {'running': False, 'status': 'stopped'},
            }
        }

        monitor._update_dashboard(results)

        content = (temp_vault / 'Dashboard.md').read_text()
        assert 'System Health' in content
        assert 'Gmail Watcher' in content
        assert 'Restarts Today' in content


class TestWatchedProcess:
    """Test cases for WatchedProcess dataclass."""

    def test_default_values(self):
        """Test WatchedProcess default values."""
        process = WatchedProcess(
            name='Test',
            script_path='/path/to/script.py',
            pid_file='/path/to/pid'
        )

        assert process.restart_command == []
        assert process.failure_count == 0
        assert process.last_check is None
        assert process.last_restart is None
        assert process.status == 'unknown'


class TestSingleton:
    """Test singleton pattern."""

    def test_get_watchdog_returns_same_instance(self, monkeypatch):
        """Test that get_watchdog returns singleton."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Logs' / 'pids').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(tmpdir))

            # Reset singleton
            import src.watchdog.process_monitor as module
            module._watchdog = None

            from src.watchdog.process_monitor import get_watchdog

            watchdog1 = get_watchdog()
            watchdog2 = get_watchdog()

            assert watchdog1 is watchdog2
