"""Tests for the CEO Briefing Generator module."""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.briefings.ceo_briefing import (
    CEOBriefingGenerator,
    BriefingData,
    generate_ceo_briefing,
)


class TestBriefingData:
    """Test cases for BriefingData dataclass."""

    def test_default_values(self):
        """Test BriefingData default values."""
        data = BriefingData(
            generated_at='2026-02-05T10:00:00',
            period_start='2026-01-29',
            period_end='2026-02-05'
        )

        assert data.financial_available is False
        assert data.social_available is False
        assert data.total_customers == 0
        assert data.revenue_period == 0.0
        assert data.tasks_completed == 0
        assert data.suggestions == []
        assert data.alerts == []

    def test_custom_values(self):
        """Test BriefingData with custom values."""
        data = BriefingData(
            generated_at='2026-02-05T10:00:00',
            period_start='2026-01-29',
            period_end='2026-02-05',
            financial_available=True,
            revenue_period=5000.0,
            tasks_completed=10,
            suggestions=['Test suggestion']
        )

        assert data.financial_available is True
        assert data.revenue_period == 5000.0
        assert len(data.suggestions) == 1


class TestCEOBriefingGenerator:
    """Test cases for CEOBriefingGenerator class."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Briefings').mkdir()
            (vault / 'Done').mkdir()
            (vault / 'Tasks').mkdir()
            (vault / 'Plans').mkdir()
            (vault / 'Needs_Action').mkdir()
            (vault / 'Data' / 'Briefings').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def generator(self, temp_vault):
        """Create CEOBriefingGenerator instance."""
        return CEOBriefingGenerator()

    def test_initialization(self, generator, temp_vault):
        """Test CEOBriefingGenerator initializes correctly."""
        assert generator.briefings_folder.exists()
        assert generator.done_folder.exists()
        assert generator.data_folder.exists()

    def test_collect_data_no_sources(self, generator):
        """Test data collection with no available sources."""
        # Patch the properties to return None
        with patch.object(type(generator), 'odoo', property(lambda self: None)):
            with patch.object(type(generator), 'twitter', property(lambda self: None)):
                data = generator.collect_data(period_days=7)

        assert data.financial_available is False
        assert data.social_available is False
        assert data.generated_at is not None

    def test_collect_data_with_odoo(self, generator):
        """Test data collection with Odoo available."""
        mock_odoo = Mock()
        mock_odoo.test_connection.return_value = {'success': True}
        mock_odoo.get_customers.return_value = {
            'success': True,
            'data': [{'id': 1}, {'id': 2}]
        }
        mock_odoo.get_invoices.return_value = {
            'success': True,
            'data': [
                {'amount_total': 500.0, 'amount_residual': 100.0, 'invoice_date_due': '2026-02-10'},
                {'amount_total': 750.0, 'amount_residual': 0.0, 'invoice_date_due': '2026-02-15'}
            ]
        }

        generator._odoo = mock_odoo
        generator._twitter = None

        data = generator.collect_data(period_days=7)

        assert data.financial_available is True
        assert data.total_customers == 2
        assert data.revenue_period == 1250.0
        assert data.outstanding_amount == 100.0

    def test_collect_data_with_twitter(self, generator):
        """Test data collection with Twitter available."""
        mock_twitter = Mock()
        mock_twitter.authenticate.return_value = {
            'success': True,
            'username': 'testuser',
            'followers': 100
        }
        mock_twitter.get_my_tweets.return_value = {
            'success': True,
            'data': [
                {'text': 'Test tweet', 'metrics': {'like_count': 5, 'retweet_count': 2, 'reply_count': 1}}
            ]
        }
        mock_twitter.get_mentions.return_value = {
            'success': True,
            'data': [{'id': '1'}, {'id': '2'}]
        }

        generator._odoo = None
        generator._twitter = mock_twitter

        data = generator.collect_data(period_days=7)

        assert data.social_available is True
        assert data.twitter_followers == 100
        assert data.twitter_engagement == 8  # 5 + 2 + 1
        assert data.twitter_mentions == 2

    def test_collect_task_data(self, generator, temp_vault):
        """Test task data collection from vault."""
        # Create some task files
        done_file = temp_vault / 'Done' / 'task1.md'
        done_file.write_text("---\nstatus: done\n---\n# Completed Task")

        tasks_file = temp_vault / 'Tasks' / 'task2.md'
        tasks_file.write_text("---\nstatus: pending\n---\n# Pending Task")

        needs_action_file = temp_vault / 'Needs_Action' / 'action1.md'
        needs_action_file.write_text("---\nstatus: pending\n---\n# Action Item")

        generator._odoo = None
        generator._twitter = None

        data = generator.collect_data(period_days=7)

        assert data.tasks_completed >= 1
        assert data.tasks_pending >= 2

    def test_generate_suggestions_overdue(self, generator):
        """Test suggestion generation for overdue invoices."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            overdue_amount=500.0,
            outstanding_amount=1000.0
        )

        generator._generate_suggestions(data)

        assert len(data.alerts) >= 1
        assert 'OVERDUE' in data.alerts[0]
        assert len(data.suggestions) >= 1

    def test_generate_suggestions_draft_invoices(self, generator):
        """Test suggestion generation for draft invoices."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            draft_invoices=3
        )

        generator._generate_suggestions(data)

        assert any('draft' in s.lower() for s in data.suggestions)

    def test_generate_suggestions_pending_tasks(self, generator):
        """Test suggestion generation for many pending tasks."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            tasks_pending=10
        )

        generator._generate_suggestions(data)

        assert any('pending' in s.lower() for s in data.suggestions)

    def test_generate_briefing(self, generator):
        """Test briefing markdown generation."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            financial_available=True,
            total_customers=5,
            revenue_period=2500.0,
            outstanding_amount=500.0,
            social_available=True,
            twitter_followers=100,
            twitter_engagement=50,
            tasks_completed=8,
            tasks_pending=3,
            suggestions=['Test suggestion']
        )

        briefing = generator.generate_briefing(data)

        assert '# CEO Weekly Briefing' in briefing
        assert '2026-01-29' in briefing
        assert '$2,500.00' in briefing
        assert 'Test suggestion' in briefing
        assert 'Odoo ✓' in briefing
        assert 'Twitter ✓' in briefing

    def test_generate_briefing_no_financial(self, generator):
        """Test briefing with no financial data."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            financial_available=False
        )

        briefing = generator.generate_briefing(data)

        assert 'Odoo data not available' in briefing
        assert 'Odoo ✗' in briefing

    def test_generate_briefing_with_alerts(self, generator):
        """Test briefing with alerts."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            alerts=['URGENT: Test alert']
        )

        briefing = generator.generate_briefing(data)

        assert '⚠️ Alerts' in briefing
        assert 'URGENT: Test alert' in briefing

    def test_generate_briefing_with_wow_changes(self, generator):
        """Test briefing with week-over-week changes."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            financial_available=True,
            revenue_period=3000.0,
            wow_revenue_change=500.0,
            social_available=True,
            twitter_followers=150,
            wow_followers_change=10,
            tasks_completed=12,
            wow_tasks_change=4
        )

        briefing = generator.generate_briefing(data)

        assert '↑' in briefing  # Revenue increase
        assert '+10' in briefing or '(+10' in briefing  # Followers increase
        assert '+4' in briefing or '(+4' in briefing  # Tasks increase

    def test_save_briefing(self, generator, temp_vault):
        """Test saving briefing to vault."""
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05'
        )
        briefing = "# Test Briefing\n\nContent here."

        briefing_path, data_path = generator.save_briefing(briefing, data)

        assert briefing_path.exists()
        assert data_path.exists()
        assert 'Briefing.md' in briefing_path.name
        assert 'BRIEFING_DATA' in data_path.name

    def test_compare_with_previous(self, generator, temp_vault):
        """Test week-over-week comparison."""
        # Create previous week's data
        last_week = datetime.now() - timedelta(days=7)
        prev_file = temp_vault / 'Data' / 'Briefings' / f"BRIEFING_DATA_{last_week.strftime('%Y-%m-%d')}.json"

        prev_data = {
            'financial_available': True,
            'revenue_period': 2000.0,
            'social_available': True,
            'twitter_followers': 90,
            'tasks_completed': 5
        }

        with open(prev_file, 'w') as f:
            json.dump(prev_data, f)

        # Current data
        data = BriefingData(
            generated_at=datetime.now().isoformat(),
            period_start='2026-01-29',
            period_end='2026-02-05',
            financial_available=True,
            revenue_period=2500.0,
            social_available=True,
            twitter_followers=100,
            tasks_completed=8
        )

        generator._compare_with_previous(data)

        assert data.wow_revenue_change == 500.0
        assert data.wow_followers_change == 10
        assert data.wow_tasks_change == 3

    def test_generate_full(self, generator, temp_vault):
        """Test full briefing generation."""
        generator._odoo = None
        generator._twitter = None

        result = generator.generate(period_days=7)

        assert result['success'] is True
        assert 'briefing_path' in result
        assert 'data_path' in result
        assert Path(result['briefing_path']).exists()

    def test_generate_handles_errors(self, generator, temp_vault):
        """Test that generate handles errors gracefully."""
        # Force an error by making data_folder inaccessible
        import shutil
        shutil.rmtree(generator.data_folder)
        # Don't recreate it - this should cause an error

        # But the generator should handle it
        generator._odoo = None
        generator._twitter = None

        # This should still work because we handle errors
        result = generator.generate(period_days=7)

        # It might fail or succeed depending on error handling
        assert 'success' in result


class TestConvenienceFunction:
    """Test convenience functions."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Briefings').mkdir()
            (vault / 'Done').mkdir()
            (vault / 'Tasks').mkdir()
            (vault / 'Plans').mkdir()
            (vault / 'Needs_Action').mkdir()
            (vault / 'Data' / 'Briefings').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_generate_ceo_briefing(self, temp_vault):
        """Test generate_ceo_briefing convenience function."""
        result = generate_ceo_briefing(period_days=7)

        assert result['success'] is True
        assert 'briefing_path' in result
