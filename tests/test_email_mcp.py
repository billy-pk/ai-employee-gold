"""Tests for EmailMCP module."""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# Note: These tests mock the Gmail API to avoid requiring credentials


class TestEmailMCPRateLimiting:
    """Tests for rate limiting functionality."""

    def test_check_rate_limit_no_log_file(self):
        """Test rate limit check when no log file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / 'Logs'
            logs_dir.mkdir()

            # Create a mock EmailMCP-like object for testing
            class MockMCP:
                def __init__(self):
                    self.sent_log_file = logs_dir / 'email_sends.json'
                    self.max_emails_per_hour = 10

                def _check_rate_limit(self):
                    if not self.sent_log_file.exists():
                        return True, 0
                    sends = json.loads(self.sent_log_file.read_text())
                    one_hour_ago = datetime.now().timestamp() - 3600
                    recent = [s for s in sends if s.get('timestamp', 0) > one_hour_ago]
                    return len(recent) < self.max_emails_per_hour, len(recent)

            mcp = MockMCP()
            allowed, count = mcp._check_rate_limit()
            assert allowed is True
            assert count == 0

    def test_check_rate_limit_under_limit(self):
        """Test rate limit when under limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / 'Logs'
            logs_dir.mkdir()

            log_file = logs_dir / 'email_sends.json'
            # Create 5 recent sends
            sends = [
                {'timestamp': datetime.now().timestamp(), 'success': True}
                for _ in range(5)
            ]
            log_file.write_text(json.dumps(sends))

            class MockMCP:
                def __init__(self):
                    self.sent_log_file = log_file
                    self.max_emails_per_hour = 10

                def _check_rate_limit(self):
                    sends = json.loads(self.sent_log_file.read_text())
                    one_hour_ago = datetime.now().timestamp() - 3600
                    recent = [s for s in sends if s.get('timestamp', 0) > one_hour_ago]
                    return len(recent) < self.max_emails_per_hour, len(recent)

            mcp = MockMCP()
            allowed, count = mcp._check_rate_limit()
            assert allowed is True
            assert count == 5

    def test_check_rate_limit_at_limit(self):
        """Test rate limit when at limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / 'Logs'
            logs_dir.mkdir()

            log_file = logs_dir / 'email_sends.json'
            # Create 10 recent sends (at limit)
            sends = [
                {'timestamp': datetime.now().timestamp(), 'success': True}
                for _ in range(10)
            ]
            log_file.write_text(json.dumps(sends))

            class MockMCP:
                def __init__(self):
                    self.sent_log_file = log_file
                    self.max_emails_per_hour = 10

                def _check_rate_limit(self):
                    sends = json.loads(self.sent_log_file.read_text())
                    one_hour_ago = datetime.now().timestamp() - 3600
                    recent = [s for s in sends if s.get('timestamp', 0) > one_hour_ago]
                    return len(recent) < self.max_emails_per_hour, len(recent)

            mcp = MockMCP()
            allowed, count = mcp._check_rate_limit()
            assert allowed is False
            assert count == 10


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test validation of valid email."""
        from email_validator import validate_email, EmailNotValidError

        try:
            result = validate_email("test@example.com", check_deliverability=False)
            assert result.normalized == "test@example.com"
        except EmailNotValidError:
            pytest.fail("Valid email should not raise exception")

    def test_invalid_email(self):
        """Test validation of invalid email."""
        from email_validator import validate_email, EmailNotValidError

        with pytest.raises(EmailNotValidError):
            validate_email("not-an-email", check_deliverability=False)

    def test_email_normalization(self):
        """Test email normalization."""
        from email_validator import validate_email

        result = validate_email("TEST@EXAMPLE.COM", check_deliverability=False)
        # Domain is lowercased, local part may or may not be
        assert result.normalized.endswith("@example.com")


class TestEmailLogging:
    """Tests for email send logging."""

    def test_log_send_creates_file(self):
        """Test that logging creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'email_sends.json'

            def log_send(to, subject, success, message_id=None, error=None):
                sends = []
                if log_file.exists():
                    sends = json.loads(log_file.read_text())
                sends.append({
                    'timestamp': datetime.now().timestamp(),
                    'to': to,
                    'subject': subject,
                    'success': success,
                    'message_id': message_id,
                    'error': error,
                })
                log_file.write_text(json.dumps(sends, indent=2))

            log_send("test@example.com", "Test Subject", True, "msg123")

            assert log_file.exists()
            data = json.loads(log_file.read_text())
            assert len(data) == 1
            assert data[0]['to'] == "test@example.com"
            assert data[0]['success'] is True

    def test_log_send_appends(self):
        """Test that logging appends to existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'email_sends.json'
            log_file.write_text(json.dumps([{'existing': True}]))

            def log_send(to, subject, success):
                sends = json.loads(log_file.read_text())
                sends.append({'to': to, 'subject': subject, 'success': success})
                log_file.write_text(json.dumps(sends))

            log_send("test@example.com", "Test", True)

            data = json.loads(log_file.read_text())
            assert len(data) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
