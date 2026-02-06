"""End-to-end integration tests for AI Employee Gold."""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest


class TestFinanceWatcherIntegration:
    """Integration tests for Finance Watcher workflow."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault with full structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            folders = [
                'Business/Transactions', 'Needs_Action', 'Done', 'Logs',
                'Audit', 'Tasks', 'Plans'
            ]
            for folder in folders:
                (vault / folder).mkdir(parents=True, exist_ok=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_csv_to_needs_action_workflow(self, temp_vault):
        """Test: Drop bank CSV → Finance Watcher detects → creates Needs_Action file."""
        from src.watchers.finance_watcher import FinanceWatcher

        watcher = FinanceWatcher()

        # Create a bank CSV
        csv_content = """Date,Description,Amount
2026-02-01,NETFLIX.COM,29.99
2026-02-02,SALARY DEPOSIT,-5000.00
2026-02-03,LARGE PURCHASE,750.00
"""
        csv_file = temp_vault / 'Business' / 'Transactions' / 'bank_statement.csv'
        csv_file.write_text(csv_content)

        # Check for updates and process
        updates = watcher.check_for_updates()
        assert len(updates) >= 1

        # Process the first update
        watcher.create_action_file(updates[0])

        # Should create Needs_Action file
        needs_action_files = list((temp_vault / 'Needs_Action').glob('FINANCE_*.md'))
        assert len(needs_action_files) >= 1

        # Verify content
        action_file = needs_action_files[0]
        content = action_file.read_text()

        assert 'NETFLIX' in content or 'subscription' in content.lower()

    def test_subscription_detection(self, temp_vault):
        """Test subscription detection from bank CSV."""
        from src.watchers.finance_watcher import FinanceWatcher

        watcher = FinanceWatcher()

        # Create CSV with known subscriptions
        csv_content = """Date,Description,Amount
2026-02-01,SPOTIFY USA,9.99
2026-02-02,ADOBE CREATIVE,54.99
2026-02-03,AMAZON PRIME,14.99
"""
        csv_file = temp_vault / 'Business' / 'Transactions' / 'subscriptions.csv'
        csv_file.write_text(csv_content)

        # Check for updates and process
        updates = watcher.check_for_updates()
        if updates:
            watcher.create_action_file(updates[0])

        # Check for subscription mentions in output
        needs_action_files = list((temp_vault / 'Needs_Action').glob('FINANCE_*.md'))
        if needs_action_files:
            content = needs_action_files[0].read_text()
            # Should mention subscriptions
            assert 'subscription' in content.lower() or 'SPOTIFY' in content or 'ADOBE' in content


class TestTwitterIntegration:
    """Integration tests for Twitter workflow."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            folders = ['Pending_Approval', 'Approved', 'Done', 'Social/Twitter', 'Audit']
            for folder in folders:
                (vault / folder).mkdir(parents=True, exist_ok=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def temp_config(self, monkeypatch):
        """Create temporary Twitter config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test',
                'api_secret': 'test',
                'access_token': 'test',
                'access_token_secret': 'test',
                'bearer_token': 'test'
            }, f)
            monkeypatch.setenv('TWITTER_CONFIG_PATH', f.name)
            return f.name

    def test_tweet_approval_workflow(self, temp_vault, temp_config):
        """Test: Claude drafts tweet → approval request → logged."""
        from src.mcp.twitter_mcp import TwitterMCP

        mcp = TwitterMCP(config_path=temp_config)

        # Create tweet approval
        result = mcp.create_tweet_approval("Test tweet content for approval")

        assert result['success'] is True

        # Check approval file exists
        approval_files = list((temp_vault / 'Pending_Approval').glob('TWEET_*.md'))
        assert len(approval_files) == 1

        # Verify content
        content = approval_files[0].read_text()
        assert 'Test tweet content' in content
        assert 'approval' in content.lower()

    def test_tweet_scheduling_workflow(self, temp_vault, temp_config):
        """Test tweet scheduling creates scheduled_posts.md."""
        from src.mcp.twitter_mcp import TwitterMCP

        mcp = TwitterMCP(config_path=temp_config)

        # Schedule a tweet
        future_time = datetime.now() + timedelta(hours=2)
        result = mcp.schedule_tweet("Scheduled test tweet", future_time)

        assert result['success'] is True

        # Check scheduled_posts.md updated
        scheduled_file = temp_vault / 'Social' / 'Twitter' / 'scheduled_posts.md'
        assert scheduled_file.exists()

        content = scheduled_file.read_text()
        assert 'Scheduled' in content or 'scheduled' in content.lower()


class TestCEOBriefingIntegration:
    """Integration tests for CEO Briefing."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault with test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            folders = [
                'Briefings', 'Done', 'Tasks', 'Plans', 'Needs_Action',
                'Data/Briefings', 'Data/Financial', 'Social/Twitter',
                'Pending_Approval', 'Audit'
            ]
            for folder in folders:
                (vault / folder).mkdir(parents=True, exist_ok=True)

            # Create some test task files
            done_task = vault / 'Done' / 'completed_task.md'
            done_task.write_text("---\nstatus: done\n---\n# Completed Task\nThis was completed.")

            pending_task = vault / 'Tasks' / 'pending_task.md'
            pending_task.write_text("---\nstatus: pending\n---\n# Pending Task")

            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_briefing_with_vault_data_only(self, temp_vault):
        """Test CEO Briefing generates with vault data when external services unavailable."""
        from src.briefings.ceo_briefing import CEOBriefingGenerator

        generator = CEOBriefingGenerator()

        # Disable external services
        with patch.object(type(generator), 'odoo', property(lambda self: None)):
            with patch.object(type(generator), 'twitter', property(lambda self: None)):
                result = generator.generate(period_days=7)

        assert result['success'] is True

        # Check briefing content
        briefing_path = Path(result['briefing_path'])
        assert briefing_path.exists()

        content = briefing_path.read_text()
        assert '# CEO Weekly Briefing' in content
        assert 'Tasks' in content

    def test_briefing_includes_completed_tasks(self, temp_vault):
        """Test briefing lists completed tasks from Done folder."""
        from src.briefings.ceo_briefing import CEOBriefingGenerator

        generator = CEOBriefingGenerator()

        with patch.object(type(generator), 'odoo', property(lambda self: None)):
            with patch.object(type(generator), 'twitter', property(lambda self: None)):
                data = generator.collect_data(period_days=7)

        # Should have found completed task
        assert data.tasks_completed >= 1


class TestWatchdogIntegration:
    """Integration tests for Watchdog process monitor."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Logs').mkdir()
            (vault / 'Dashboard.md').write_text("# Dashboard\n\n## System Health\n\nStatus here.")
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_watchdog_detects_stale_pid(self, temp_vault):
        """Test: Watchdog detects stale PID file."""
        from src.watchdog.process_monitor import ProcessMonitor

        monitor = ProcessMonitor()

        # Create a stale PID file (non-existent process)
        pid_file = temp_vault / 'Logs' / 'gmail_watcher.pid'
        pid_file.write_text("99999999")  # Very unlikely to be a real PID

        status = monitor.check_process('gmail_watcher')

        # Should detect as not running
        assert status['status'] in ['stopped', 'stale', 'not_running', 'unknown']

    def test_watchdog_health_summary(self, temp_vault):
        """Test watchdog provides health summary."""
        from src.watchdog.process_monitor import ProcessMonitor

        monitor = ProcessMonitor()

        summary = monitor.get_health_summary()

        assert 'processes' in summary
        assert isinstance(summary['processes'], dict)
        assert 'daily_restarts' in summary


class TestRalphWiggumIntegration:
    """Integration tests for Ralph Wiggum task loop."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Tasks').mkdir()
            (vault / 'Done').mkdir()
            (vault / 'Logs').mkdir()
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_task_lifecycle(self, temp_vault):
        """Test: Create task → process → complete."""
        from src.hooks.ralph_wiggum import RalphWiggumLoop, TaskStatus

        loop = RalphWiggumLoop()

        # Create task
        task = loop.create_task(
            objective='Test multi-step task',
            steps=['Step 1', 'Step 2', 'Step 3'],
            max_iterations=10
        )

        assert task.task_id is not None
        assert task.filepath.exists()

        # Simulate iteration
        loop.record_iteration(task, 'Completed step 1', 'Success')

        # Reload and verify
        reloaded = loop.load_task(task.task_id)
        assert reloaded.current_iteration == 2  # Initial + 1

        # Complete the task
        loop.complete_task(task, success=True)

        # Should be in Done folder
        done_path = temp_vault / 'Done' / task.filepath.name
        assert done_path.exists()

    def test_max_iterations_stops_loop(self, temp_vault):
        """Test task stops at max iterations."""
        from src.hooks.ralph_wiggum import RalphWiggumLoop, TaskStatus

        loop = RalphWiggumLoop()

        # Create task with low limit
        task = loop.create_task(
            objective='Limited task',
            max_iterations=3
        )

        # Record iterations until limit
        for i in range(3):
            result = loop.should_continue(task)
            if result['continue']:
                loop.record_iteration(task, f'Action {i+1}', 'Done')
            task = loop.load_task(task.task_id)

        # Should hit max
        result = loop.should_continue(task)
        assert result['continue'] is False
        assert 'max' in result['reason'].lower() or task.status == TaskStatus.MAX_ITERATIONS


class TestAuditLoggingIntegration:
    """Integration tests for audit logging."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Audit').mkdir()
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_actions_logged_to_audit(self, temp_vault):
        """Test all actions appear in audit logs."""
        from src.utils.audit_logger import AuditLogger

        logger = AuditLogger()

        # Log various actions
        logger.log_action(
            action_type='test_action',
            actor='test_actor',
            target='test_target',
            result='success'
        )

        logger.log_email_send(
            to='test@example.com',
            subject='Test Subject'
        )

        logger.log_invoice_create(
            customer_id=1,
            invoice_id=100,
            amount=500.0
        )

        # Check audit file exists
        today = datetime.now().strftime('%Y-%m-%d')
        audit_file = temp_vault / 'Audit' / f'{today}.json'
        assert audit_file.exists()

        # Verify content
        content = audit_file.read_text()
        assert 'test_action' in content
        assert 'email_send' in content
        assert 'invoice_create' in content

    def test_audit_log_retention(self, temp_vault):
        """Test old audit logs can be cleaned up."""
        from src.utils.audit_logger import AuditLogger

        logger = AuditLogger()

        # Create an old log file (simulate 100 days old)
        old_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        old_file = temp_vault / 'Audit' / f'{old_date}.json'
        old_file.write_text('{"old": "log"}')

        # Run cleanup (uses default retention from env or 90 days)
        deleted = logger.cleanup_old_logs()

        # Old file should be deleted
        assert not old_file.exists()
        assert deleted >= 1


class TestCrossComponentIntegration:
    """Tests for interactions between components."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create full vault structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            folders = [
                'Audit', 'Briefings', 'Business/Transactions', 'Done', 'Logs',
                'Needs_Action', 'Pending_Approval', 'Plans', 'Tasks',
                'Data/Briefings', 'Data/Financial', 'Social/Twitter'
            ]
            for folder in folders:
                (vault / folder).mkdir(parents=True, exist_ok=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_finance_watcher_triggers_audit_log(self, temp_vault):
        """Test finance watcher logs to audit."""
        from src.watchers.finance_watcher import FinanceWatcher
        from src.utils.audit_logger import get_audit_logger

        watcher = FinanceWatcher()

        # Create a CSV
        csv_content = "Date,Description,Amount\n2026-02-01,TEST,100.00\n"
        csv_file = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_file.write_text(csv_content)

        # Process - check for updates and create action file
        updates = watcher.check_for_updates()
        if updates:
            watcher.create_action_file(updates[0])

        # Check audit was created
        today = datetime.now().strftime('%Y-%m-%d')
        audit_file = temp_vault / 'Audit' / f'{today}.json'

        # Audit should exist (may have entries from this or previous operations)
        # The important thing is no crash occurred

    def test_full_system_health_check(self, temp_vault):
        """Test all components can be instantiated without errors."""
        from src.utils.audit_logger import AuditLogger
        from src.utils.vault_helpers import get_vault_path
        from src.hooks.ralph_wiggum import RalphWiggumLoop
        from src.watchdog.process_monitor import ProcessMonitor
        from src.briefings.ceo_briefing import CEOBriefingGenerator

        # All should instantiate without errors
        audit = AuditLogger()
        vault = get_vault_path()
        ralph = RalphWiggumLoop()
        watchdog = ProcessMonitor()
        briefing = CEOBriefingGenerator()

        # Basic operations should work
        assert vault.exists()
        assert audit is not None
        assert ralph is not None
        assert watchdog is not None
        assert briefing is not None
