"""Tests for the Audit Logger module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.utils.audit_logger import AuditLogger


class TestAuditLogger:
    """Test cases for AuditLogger class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Audit').mkdir()
            yield vault

    @pytest.fixture
    def audit_logger(self, temp_vault, monkeypatch):
        """Create an AuditLogger with temp vault."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))
        return AuditLogger()

    def test_initialization(self, audit_logger, temp_vault):
        """Test that AuditLogger initializes correctly."""
        assert audit_logger.audit_dir == temp_vault / 'Audit'
        assert audit_logger.audit_dir.exists()
        assert audit_logger.retention_days == 90

    def test_log_action_creates_file(self, audit_logger):
        """Test that log_action creates audit file."""
        entry = audit_logger.log_action(
            action_type='test_action',
            actor='test_actor',
            target='test_target'
        )

        assert entry['action_type'] == 'test_action'
        assert entry['actor'] == 'test_actor'
        assert entry['target'] == 'test_target'

        # Check file was created
        today = datetime.now().strftime('%Y-%m-%d')
        audit_file = audit_logger.audit_dir / f'{today}.json'
        assert audit_file.exists()

    def test_log_action_appends_entries(self, audit_logger):
        """Test that multiple log_action calls append to the same file."""
        audit_logger.log_action('action1', 'actor1', 'target1')
        audit_logger.log_action('action2', 'actor2', 'target2')
        audit_logger.log_action('action3', 'actor3', 'target3')

        entries = audit_logger.get_entries()
        assert len(entries) == 3
        assert entries[0]['action_type'] == 'action1'
        assert entries[2]['action_type'] == 'action3'

    def test_log_action_with_parameters(self, audit_logger):
        """Test logging with parameters and result details."""
        entry = audit_logger.log_action(
            action_type='email_send',
            actor='claude_code',
            target='user@example.com',
            parameters={'subject': 'Test Subject', 'has_attachment': True},
            approval_status='approved',
            approved_by='human',
            result='success',
            result_details={'message_id': 'msg123'}
        )

        assert entry['parameters']['subject'] == 'Test Subject'
        assert entry['parameters']['has_attachment'] is True
        assert entry['approval_status'] == 'approved'
        assert entry['approved_by'] == 'human'
        assert entry['result'] == 'success'
        assert entry['result_details']['message_id'] == 'msg123'

    def test_log_email_send(self, audit_logger):
        """Test convenience method for email logging."""
        entry = audit_logger.log_email_send(
            to='client@example.com',
            subject='Invoice #123',
            message_id='msg456',
            has_attachment=True
        )

        assert entry['action_type'] == 'email_send'
        assert entry['target'] == 'client@example.com'
        assert entry['parameters']['subject'] == 'Invoice #123'
        assert entry['parameters']['has_attachment'] is True
        assert entry['result_details']['message_id'] == 'msg456'

    def test_log_invoice_create(self, audit_logger):
        """Test convenience method for invoice logging."""
        entry = audit_logger.log_invoice_create(
            customer_id=7,
            invoice_id=123,
            amount=500.00
        )

        assert entry['action_type'] == 'invoice_create'
        assert entry['target'] == '7'
        assert entry['parameters']['amount'] == 500.00
        assert entry['result_details']['invoice_id'] == 123

    def test_log_tweet_post(self, audit_logger):
        """Test convenience method for tweet logging."""
        entry = audit_logger.log_tweet_post(
            content='This is a test tweet!',
            tweet_id='1234567890',
            approved_by='human'
        )

        assert entry['action_type'] == 'tweet_post'
        assert entry['target'] == 'twitter'
        assert entry['parameters']['character_count'] == 21
        assert entry['result_details']['tweet_id'] == '1234567890'
        assert entry['approved_by'] == 'human'

    def test_log_tweet_truncates_long_content(self, audit_logger):
        """Test that long tweet content is truncated in log."""
        long_content = 'x' * 200
        entry = audit_logger.log_tweet_post(content=long_content)

        assert len(entry['parameters']['content']) == 103  # 100 chars + '...'
        assert entry['parameters']['content'].endswith('...')
        assert entry['parameters']['character_count'] == 200

    def test_get_entries_with_filters(self, audit_logger):
        """Test filtering entries by action_type, actor, result."""
        audit_logger.log_action('email_send', 'claude_code', 'a@b.com', result='success')
        audit_logger.log_action('email_send', 'human', 'c@d.com', result='success')
        audit_logger.log_action('invoice_create', 'claude_code', '1', result='failure')

        # Filter by action_type
        email_entries = audit_logger.get_entries(action_type='email_send')
        assert len(email_entries) == 2

        # Filter by actor
        claude_entries = audit_logger.get_entries(actor='claude_code')
        assert len(claude_entries) == 2

        # Filter by result
        success_entries = audit_logger.get_entries(result='success')
        assert len(success_entries) == 2

        # Combined filters
        filtered = audit_logger.get_entries(action_type='email_send', actor='claude_code')
        assert len(filtered) == 1

    def test_get_stats(self, audit_logger):
        """Test statistics generation."""
        audit_logger.log_action('email_send', 'claude_code', 't1', result='success')
        audit_logger.log_action('email_send', 'claude_code', 't2', result='success')
        audit_logger.log_action('invoice_create', 'human', 't3', result='failure')

        stats = audit_logger.get_stats()

        assert stats['total_entries'] == 3
        assert stats['by_action_type']['email_send'] == 2
        assert stats['by_action_type']['invoice_create'] == 1
        assert stats['by_actor']['claude_code'] == 2
        assert stats['by_actor']['human'] == 1
        assert stats['by_result']['success'] == 2
        assert stats['by_result']['failure'] == 1

    def test_cleanup_old_logs(self, audit_logger):
        """Test that old logs are cleaned up after retention period."""
        # Create an old log file (91 days ago)
        old_date = datetime.now() - timedelta(days=91)
        old_file = audit_logger.audit_dir / f'{old_date.strftime("%Y-%m-%d")}.json'
        old_file.write_text('{"entries": []}')

        # Create a recent log file (today)
        audit_logger.log_action('test', 'test', 'test')

        # Run cleanup
        deleted = audit_logger.cleanup_old_logs()

        assert deleted == 1
        assert not old_file.exists()
        assert audit_logger._get_today_file().exists()

    def test_cleanup_preserves_recent_logs(self, audit_logger):
        """Test that recent logs are not deleted."""
        # Create log files within retention period
        for days_ago in [0, 30, 60, 89]:
            date = datetime.now() - timedelta(days=days_ago)
            file = audit_logger.audit_dir / f'{date.strftime("%Y-%m-%d")}.json'
            file.write_text('{"entries": []}')

        deleted = audit_logger.cleanup_old_logs()

        assert deleted == 0
        assert len(list(audit_logger.audit_dir.glob('*.json'))) == 4

    def test_handles_corrupted_file(self, audit_logger):
        """Test that corrupted files don't crash the logger."""
        # Create corrupted file
        today = datetime.now().strftime('%Y-%m-%d')
        audit_file = audit_logger.audit_dir / f'{today}.json'
        audit_file.write_text('not valid json {{{')

        # Should not raise
        entry = audit_logger.log_action('test', 'test', 'test')
        assert entry['action_type'] == 'test'

    def test_timestamp_format(self, audit_logger):
        """Test that timestamps are in ISO format with Z suffix."""
        entry = audit_logger.log_action('test', 'test', 'test')

        assert 'timestamp' in entry
        assert entry['timestamp'].endswith('Z')
        # Should be parseable
        ts = entry['timestamp'].rstrip('Z')
        datetime.fromisoformat(ts)


class TestAuditLoggerSingleton:
    """Test singleton pattern."""

    def test_get_audit_logger_returns_same_instance(self, monkeypatch):
        """Test that get_audit_logger returns singleton."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('VAULT_PATH', tmpdir)

            # Reset singleton
            import src.utils.audit_logger as module
            module._audit_logger = None

            from src.utils.audit_logger import get_audit_logger

            logger1 = get_audit_logger()
            logger2 = get_audit_logger()

            assert logger1 is logger2
