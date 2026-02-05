"""Tests for the data collectors module."""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.briefings.data_collectors import (
    OdooDataCollector,
    FinancialSnapshot,
    collect_odoo_data,
    generate_financial_brief,
)


class TestFinancialSnapshot:
    """Test cases for FinancialSnapshot dataclass."""

    def test_default_values(self):
        """Test FinancialSnapshot default values."""
        snapshot = FinancialSnapshot(timestamp='2026-02-05T10:00:00')

        assert snapshot.total_customers == 0
        assert snapshot.total_invoiced_30d == 0.0
        assert snapshot.total_outstanding == 0.0
        assert snapshot.draft_invoices == 0
        assert snapshot.posted_invoices_30d == 0
        assert snapshot.overdue_invoices == 0
        assert snapshot.overdue_amount == 0.0
        assert snapshot.recent_payments == []
        assert snapshot.top_customers == []
        assert snapshot.needs_attention == []

    def test_custom_values(self):
        """Test FinancialSnapshot with custom values."""
        snapshot = FinancialSnapshot(
            timestamp='2026-02-05T10:00:00',
            total_customers=10,
            total_invoiced_30d=5000.0,
            total_outstanding=1000.0,
            draft_invoices=2,
            posted_invoices_30d=5,
            overdue_invoices=1,
            overdue_amount=500.0
        )

        assert snapshot.total_customers == 10
        assert snapshot.total_invoiced_30d == 5000.0
        assert snapshot.overdue_amount == 500.0


class TestOdooDataCollector:
    """Test cases for OdooDataCollector class."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Data' / 'Financial').mkdir(parents=True)
            (vault / 'Briefs').mkdir()
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def mock_odoo(self):
        """Create mock Odoo MCP."""
        mock = Mock()
        mock.test_connection.return_value = {
            'success': True,
            'connected': True,
            'server_version': '19.0'
        }
        mock.get_customers.return_value = {
            'success': True,
            'data': [
                {'id': 7, 'name': 'Client A', 'email': 'a@test.com'},
                {'id': 8, 'name': 'Client B', 'email': 'b@test.com'}
            ]
        }
        mock.get_invoices.return_value = {
            'success': True,
            'data': [
                {
                    'id': 1,
                    'name': 'INV/2026/00001',
                    'amount_total': 500.0,
                    'amount_residual': 100.0,
                    'invoice_date_due': '2026-02-01'
                },
                {
                    'id': 2,
                    'name': 'INV/2026/00002',
                    'amount_total': 750.0,
                    'amount_residual': 0.0,
                    'invoice_date_due': '2026-02-10'
                }
            ]
        }
        return mock

    @pytest.fixture
    def temp_config(self):
        """Create temporary Odoo config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    def test_initialization(self, temp_vault, temp_config, monkeypatch):
        """Test OdooDataCollector initializes correctly."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            assert collector.data_folder.exists()
            assert collector.briefs_folder.exists()

    def test_collect_snapshot(self, temp_vault, temp_config, mock_odoo, monkeypatch):
        """Test collecting a financial snapshot."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp', return_value=mock_odoo):
            collector = OdooDataCollector()
            snapshot = collector.collect_snapshot()

        assert snapshot.total_customers == 2
        assert snapshot.posted_invoices_30d == 2
        assert snapshot.total_invoiced_30d == 1250.0
        assert snapshot.total_outstanding == 100.0

    def test_collect_snapshot_with_overdue(self, temp_vault, temp_config, monkeypatch):
        """Test collecting snapshot detects overdue invoices."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        # Create mock with overdue invoice
        mock_odoo = Mock()
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        mock_odoo.get_customers.return_value = {'success': True, 'data': []}
        mock_odoo.get_invoices.return_value = {
            'success': True,
            'data': [{
                'id': 1,
                'name': 'INV/2026/00001',
                'amount_total': 500.0,
                'amount_residual': 500.0,  # Unpaid
                'invoice_date_due': yesterday  # Overdue
            }]
        }

        with patch('src.briefings.data_collectors.get_odoo_mcp', return_value=mock_odoo):
            collector = OdooDataCollector()
            snapshot = collector.collect_snapshot()

        assert snapshot.overdue_invoices == 1
        assert snapshot.overdue_amount == 500.0
        assert len(snapshot.needs_attention) > 0

    def test_save_snapshot(self, temp_vault, temp_config, monkeypatch):
        """Test saving a snapshot."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            snapshot = FinancialSnapshot(
                timestamp=datetime.now().isoformat(),
                total_customers=5,
                total_invoiced_30d=2500.0
            )

            path = collector.save_snapshot(snapshot)

            assert path.exists()
            with open(path) as f:
                data = json.load(f)
            assert data['total_customers'] == 5
            assert data['total_invoiced_30d'] == 2500.0

    def test_load_snapshot(self, temp_vault, temp_config, monkeypatch):
        """Test loading a snapshot."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            # Save a snapshot first
            original = FinancialSnapshot(
                timestamp=datetime.now().isoformat(),
                total_customers=10,
                total_invoiced_30d=5000.0
            )
            collector.save_snapshot(original)

            # Load it
            loaded = collector.load_snapshot()

            assert loaded is not None
            assert loaded.total_customers == 10
            assert loaded.total_invoiced_30d == 5000.0

    def test_load_snapshot_not_found(self, temp_vault, temp_config, monkeypatch):
        """Test loading non-existent snapshot."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            loaded = collector.load_snapshot('2020-01-01')

            assert loaded is None

    def test_generate_brief(self, temp_vault, temp_config, monkeypatch):
        """Test generating a financial brief."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            snapshot = FinancialSnapshot(
                timestamp=datetime.now().isoformat(),
                total_customers=5,
                total_invoiced_30d=2500.0,
                total_outstanding=500.0,
                draft_invoices=2,
                posted_invoices_30d=3,
                overdue_invoices=1,
                overdue_amount=200.0,
                needs_attention=['Test attention item'],
                top_customers=[{'id': 1, 'name': 'Test Customer', 'email': 'test@test.com'}]
            )

            brief = collector.generate_brief(snapshot)

            assert '# Financial Brief' in brief
            assert 'Total Customers**: 5' in brief
            assert '$2,500.00' in brief
            assert 'Overdue' in brief
            assert '$200.00' in brief
            assert 'Test attention item' in brief
            assert 'Test Customer' in brief

    def test_save_brief(self, temp_vault, temp_config, monkeypatch):
        """Test saving a brief."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            brief = "# Test Brief\n\nThis is a test."
            path = collector.save_brief(brief)

            assert path.exists()
            assert path.suffix == '.md'

    def test_run_daily_sync_success(self, temp_vault, temp_config, mock_odoo, monkeypatch):
        """Test successful daily sync."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp', return_value=mock_odoo):
            collector = OdooDataCollector()
            result = collector.run_daily_sync()

        assert result['success'] is True
        assert 'snapshot_path' in result
        assert 'brief_path' in result
        assert result['summary']['customers'] == 2

    def test_run_daily_sync_connection_failure(self, temp_vault, temp_config, monkeypatch):
        """Test daily sync with connection failure."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        mock_odoo = Mock()
        mock_odoo.test_connection.return_value = {
            'success': False,
            'error': 'Connection refused'
        }

        with patch('src.briefings.data_collectors.get_odoo_mcp', return_value=mock_odoo):
            collector = OdooDataCollector()
            result = collector.run_daily_sync()

        assert result['success'] is False
        assert 'Connection refused' in result['error']

    def test_get_top_customers(self, temp_vault, temp_config, monkeypatch):
        """Test getting top customers."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            customers = [
                {'id': 1, 'name': 'A', 'email': 'a@test.com', 'extra': 'data'},
                {'id': 2, 'name': 'B', 'email': 'b@test.com'},
            ]

            top = collector._get_top_customers(customers)

            assert len(top) == 2
            assert top[0]['name'] == 'A'
            assert 'extra' not in top[0]  # Should be simplified

    def test_get_previous_snapshot(self, temp_vault, temp_config, monkeypatch):
        """Test getting previous snapshot for comparison."""
        monkeypatch.setenv('ODOO_CONFIG_PATH', temp_config)

        with patch('src.briefings.data_collectors.get_odoo_mcp') as mock_get_odoo:
            mock_get_odoo.return_value = Mock()
            collector = OdooDataCollector()

            # Save a snapshot for yesterday
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y-%m-%d')

            snapshot = FinancialSnapshot(
                timestamp=yesterday.isoformat(),
                total_customers=3
            )

            filename = f"FINANCIAL_SNAPSHOT_{yesterday_str}.json"
            filepath = collector.data_folder / filename
            with open(filepath, 'w') as f:
                json.dump({
                    'timestamp': snapshot.timestamp,
                    'total_customers': snapshot.total_customers,
                    'total_invoiced_30d': 0,
                    'total_outstanding': 0,
                    'draft_invoices': 0,
                    'posted_invoices_30d': 0,
                    'overdue_invoices': 0,
                    'overdue_amount': 0,
                    'recent_payments': [],
                    'top_customers': [],
                    'needs_attention': []
                }, f)

            previous = collector.get_previous_snapshot()

            assert previous is not None
            assert previous.total_customers == 3


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Data' / 'Financial').mkdir(parents=True)
            (vault / 'Briefs').mkdir()
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def temp_config(self, monkeypatch):
        """Create temporary Odoo config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            monkeypatch.setenv('ODOO_CONFIG_PATH', f.name)
            return f.name

    def test_collect_odoo_data(self, temp_vault, temp_config):
        """Test collect_odoo_data convenience function."""
        mock_odoo = Mock()
        mock_odoo.get_customers.return_value = {'success': True, 'data': []}
        mock_odoo.get_invoices.return_value = {'success': True, 'data': []}

        with patch('src.briefings.data_collectors.get_odoo_mcp', return_value=mock_odoo):
            snapshot = collect_odoo_data()

            assert isinstance(snapshot, FinancialSnapshot)

    def test_generate_financial_brief(self, temp_vault, temp_config):
        """Test generate_financial_brief convenience function."""
        mock_odoo = Mock()
        mock_odoo.get_customers.return_value = {'success': True, 'data': []}
        mock_odoo.get_invoices.return_value = {'success': True, 'data': []}

        with patch('src.briefings.data_collectors.get_odoo_mcp', return_value=mock_odoo):
            brief = generate_financial_brief()

            assert isinstance(brief, str)
            assert '# Financial Brief' in brief
