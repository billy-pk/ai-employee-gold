"""Tests for the Odoo MCP Server module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest

from src.mcp.odoo_mcp import (
    OdooMCP,
    OdooConfig,
    OdooConnectionError,
    OdooOperationError,
    get_odoo_mcp,
)


class TestOdooConfig:
    """Test cases for OdooConfig dataclass."""

    def test_config_defaults(self):
        """Test OdooConfig default values."""
        config = OdooConfig(
            url='http://localhost:8069',
            database='test_db',
            username='admin',
            api_key='test_key'
        )

        assert config.url == 'http://localhost:8069'
        assert config.database == 'test_db'
        assert config.username == 'admin'
        assert config.api_key == 'test_key'
        assert config.timeout == 30  # default

    def test_config_custom_timeout(self):
        """Test OdooConfig with custom timeout."""
        config = OdooConfig(
            url='http://localhost:8069',
            database='test_db',
            username='admin',
            api_key='test_key',
            timeout=60
        )

        assert config.timeout == 60


class TestOdooMCPInitialization:
    """Test OdooMCP initialization."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key',
                'timeout': 30
            }, f)
            return f.name

    def test_initialization_with_config(self, temp_config):
        """Test OdooMCP initializes with config file."""
        mcp = OdooMCP(config_path=temp_config)

        assert mcp.config.url == 'http://localhost:8069'
        assert mcp.config.database == 'test_db'
        assert mcp._uid is None  # Not authenticated yet

    def test_initialization_config_not_found(self):
        """Test OdooMCP raises error when config not found."""
        with pytest.raises(FileNotFoundError):
            OdooMCP(config_path='/nonexistent/path.json')


class TestOdooMCPAuthentication:
    """Test OdooMCP authentication."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    @pytest.fixture
    def mcp(self, temp_config):
        """Create OdooMCP instance."""
        return OdooMCP(config_path=temp_config)

    def test_authenticate_success(self, mcp):
        """Test successful authentication."""
        mock_common = Mock()
        mock_common.authenticate.return_value = 2  # uid

        with patch.object(mcp, '_get_common', return_value=mock_common):
            uid = mcp.authenticate()

        assert uid == 2
        assert mcp._uid == 2

    def test_authenticate_caches_uid(self, mcp):
        """Test that authenticate caches uid."""
        mcp._uid = 5  # Pre-set

        uid = mcp.authenticate()

        assert uid == 5  # Returns cached value

    def test_authenticate_failure(self, mcp):
        """Test authentication failure."""
        mock_common = Mock()
        mock_common.authenticate.return_value = False

        with patch.object(mcp, '_get_common', return_value=mock_common):
            with pytest.raises(OdooConnectionError, match="invalid credentials"):
                mcp.authenticate()


class TestOdooMCPCustomerOperations:
    """Test customer-related operations."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    @pytest.fixture
    def mcp(self, temp_config):
        """Create authenticated OdooMCP instance."""
        mcp = OdooMCP(config_path=temp_config)
        mcp._uid = 2  # Pre-authenticate
        return mcp

    def test_get_customers(self, mcp):
        """Test getting customers."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 1, 'name': 'Customer A', 'email': 'a@test.com'},
            {'id': 2, 'name': 'Customer B', 'email': 'b@test.com'},
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_customers(limit=10)

        assert result['success'] is True
        assert len(result['data']) == 2
        assert result['data'][0]['name'] == 'Customer A'

    def test_get_customer(self, mcp):
        """Test getting single customer."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 7, 'name': 'Client A', 'email': 'clienta@test.com', 'total_invoiced': 500}
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_customer(7)

        assert result['success'] is True
        assert result['data']['id'] == 7
        assert result['data']['name'] == 'Client A'

    def test_get_customer_not_found(self, mcp):
        """Test getting non-existent customer."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = []

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_customer(999)

        assert result['success'] is False
        assert 'not found' in result['error']

    def test_search_customer(self, mcp):
        """Test searching customers by name."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 7, 'name': 'Client A', 'email': 'clienta@test.com'}
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.search_customer('Client')

        assert result['success'] is True
        assert len(result['data']) == 1


class TestOdooMCPInvoiceOperations:
    """Test invoice-related operations."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    @pytest.fixture
    def mcp(self, temp_config):
        """Create authenticated OdooMCP instance."""
        mcp = OdooMCP(config_path=temp_config)
        mcp._uid = 2
        return mcp

    def test_create_invoice(self, mcp):
        """Test creating an invoice."""
        mock_models = Mock()
        # Mock journal search
        mock_models.execute_kw.side_effect = [
            [{'id': 1, 'name': 'Customer Invoices'}],  # Journal search
            5,  # Invoice create returns ID
            [{'id': 5, 'name': 'INV/2026/00005', 'amount_total': 1500.0, 'state': 'draft', 'partner_id': [7, 'Client A']}]  # Invoice read
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            with patch.object(mcp.audit, 'log_invoice_create'):
                result = mcp.create_invoice(
                    customer_id=7,
                    lines=[
                        {'name': 'Consulting', 'quantity': 10, 'price_unit': 150.0}
                    ]
                )

        assert result['success'] is True
        assert result['data']['invoice_id'] == 5
        assert result['data']['amount_total'] == 1500.0

    def test_create_invoice_no_journal(self, mcp):
        """Test invoice creation fails without journal."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = []  # No journal found

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.create_invoice(customer_id=7, lines=[])

        assert result['success'] is False
        assert 'No sales journal' in result['error']

    def test_confirm_invoice(self, mcp):
        """Test confirming an invoice."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = True

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.confirm_invoice(5)

        assert result['success'] is True

    def test_get_invoices(self, mcp):
        """Test getting invoices."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 1, 'name': 'INV/2026/00001', 'amount_total': 500.0, 'state': 'posted'},
            {'id': 2, 'name': 'INV/2026/00002', 'amount_total': 750.0, 'state': 'draft'},
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_invoices(period_days=30)

        assert result['success'] is True
        assert len(result['data']) == 2

    def test_get_invoices_with_status_filter(self, mcp):
        """Test getting invoices with status filter."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 1, 'name': 'INV/2026/00001', 'amount_total': 500.0, 'state': 'posted'}
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_invoices(period_days=30, status='posted')

        assert result['success'] is True

    def test_get_invoice(self, mcp):
        """Test getting single invoice."""
        mock_models = Mock()
        mock_models.execute_kw.side_effect = [
            [{'id': 1, 'name': 'INV/2026/00001', 'amount_total': 500.0, 'invoice_line_ids': [1, 2]}],
            [
                {'name': 'Service A', 'quantity': 5, 'price_unit': 50.0, 'price_subtotal': 250.0},
                {'name': 'Service B', 'quantity': 5, 'price_unit': 50.0, 'price_subtotal': 250.0}
            ]
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_invoice(1)

        assert result['success'] is True
        assert result['data']['name'] == 'INV/2026/00001'
        assert len(result['data']['lines']) == 2


class TestOdooMCPPaymentOperations:
    """Test payment-related operations."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    @pytest.fixture
    def mcp(self, temp_config):
        """Create authenticated OdooMCP instance."""
        mcp = OdooMCP(config_path=temp_config)
        mcp._uid = 2
        return mcp

    def test_create_payment(self, mcp):
        """Test creating a payment."""
        mock_models = Mock()
        mock_models.execute_kw.side_effect = [
            # get_invoice
            [{'id': 1, 'name': 'INV/2026/00001', 'partner_id': [7, 'Client A'], 'invoice_line_ids': []}],
            # Journal search
            [{'id': 2, 'name': 'Bank'}],
            # Payment create
            10,
            # Payment post
            True
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            with patch.object(mcp.audit, 'log_action'):
                result = mcp.create_payment(invoice_id=1, amount=500.0)

        assert result['success'] is True
        assert result['data']['payment_id'] == 10
        assert result['data']['amount'] == 500.0

    def test_create_payment_no_bank_journal(self, mcp):
        """Test payment creation fails without bank journal."""
        mock_models = Mock()
        mock_models.execute_kw.side_effect = [
            # get_invoice
            [{'id': 1, 'name': 'INV/2026/00001', 'partner_id': [7, 'Client A'], 'invoice_line_ids': []}],
            # Journal search - empty
            []
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.create_payment(invoice_id=1, amount=500.0)

        assert result['success'] is False
        assert 'No bank journal' in result['error']


class TestOdooMCPAccountOperations:
    """Test account-related operations."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    @pytest.fixture
    def mcp(self, temp_config):
        """Create authenticated OdooMCP instance."""
        mcp = OdooMCP(config_path=temp_config)
        mcp._uid = 2
        return mcp

    def test_get_account_balance(self, mcp):
        """Test getting account balance."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 1, 'name': 'Receivable', 'code': '121000', 'current_balance': 500.0}
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_account_balance()

        assert result['success'] is True
        assert len(result['data']) == 1
        assert result['data'][0]['current_balance'] == 500.0

    def test_get_account_balance_specific(self, mcp):
        """Test getting specific account balance."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 5, 'name': 'Checking', 'code': '101000', 'current_balance': 10000.0}
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_account_balance(account_id=5)

        assert result['success'] is True

    def test_get_journal_entries(self, mcp):
        """Test getting journal entries."""
        mock_models = Mock()
        mock_models.execute_kw.return_value = [
            {'id': 1, 'name': 'INV/2026/00001', 'date': '2026-02-01', 'amount_total': 500.0},
            {'id': 2, 'name': 'BILL/2026/00001', 'date': '2026-02-02', 'amount_total': 200.0}
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp.get_journal_entries(period_days=30)

        assert result['success'] is True
        assert len(result['data']) == 2


class TestOdooMCPUtilityMethods:
    """Test utility methods."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    @pytest.fixture
    def mcp(self, temp_config):
        """Create OdooMCP instance."""
        return OdooMCP(config_path=temp_config)

    def test_test_connection_success(self, mcp):
        """Test connection test success."""
        mock_common = Mock()
        mock_common.version.return_value = {'server_version': '19.0-20260118'}
        mock_common.authenticate.return_value = 2

        with patch.object(mcp, '_get_common', return_value=mock_common):
            result = mcp.test_connection()

        assert result['success'] is True
        assert result['connected'] is True
        assert result['server_version'] == '19.0-20260118'
        assert result['uid'] == 2

    def test_test_connection_failure(self, mcp):
        """Test connection test failure."""
        mock_common = Mock()
        mock_common.version.side_effect = ConnectionError("Connection refused")

        with patch.object(mcp, '_get_common', return_value=mock_common):
            result = mcp.test_connection()

        assert result['success'] is False
        assert result['connected'] is False
        assert 'Connection refused' in result['error']

    def test_get_summary(self, mcp):
        """Test getting summary."""
        mcp._uid = 2

        mock_models = Mock()
        mock_models.execute_kw.side_effect = [
            # Customers
            [{'id': 7, 'name': 'Client A'}],
            # Posted invoices
            [
                {'id': 1, 'amount_total': 500.0, 'amount_residual': 100.0},
                {'id': 2, 'amount_total': 750.0, 'amount_residual': 0.0}
            ],
            # Draft invoices
            [{'id': 3, 'amount_total': 200.0}]
        ]

        with patch.object(mcp, '_get_models', return_value=mock_models):
            summary = mcp.get_summary()

        assert summary['customers'] == 1
        assert summary['invoices_posted'] == 2
        assert summary['invoices_draft'] == 1
        assert summary['total_invoiced'] == 1250.0
        assert summary['total_outstanding'] == 100.0


class TestOdooMCPErrorHandling:
    """Test error handling."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            return f.name

    @pytest.fixture
    def mcp(self, temp_config):
        """Create authenticated OdooMCP instance."""
        mcp = OdooMCP(config_path=temp_config)
        mcp._uid = 2
        return mcp

    def test_safe_execute_connection_error(self, mcp):
        """Test safe_execute handles connection errors."""
        mock_models = Mock()
        mock_models.execute_kw.side_effect = ConnectionError("Network error")

        with patch.object(mcp, '_get_models', return_value=mock_models):
            result = mcp._safe_execute('res.partner', 'search', [])

        assert result['success'] is False
        assert 'Network error' in result['error']

    def test_execute_operation_error(self, mcp):
        """Test execute raises OdooOperationError on fault."""
        import xmlrpc.client
        mock_models = Mock()
        mock_models.execute_kw.side_effect = xmlrpc.client.Fault(1, "Access denied")

        with patch.object(mcp, '_get_models', return_value=mock_models):
            with pytest.raises(OdooOperationError, match="Access denied"):
                mcp._execute('res.partner', 'search', [])


class TestSingletonInstance:
    """Test singleton pattern."""

    def test_get_odoo_mcp_returns_same_instance(self, monkeypatch):
        """Test get_odoo_mcp returns singleton."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'url': 'http://localhost:8069',
                'database': 'test_db',
                'username': 'admin',
                'api_key': 'test_key'
            }, f)
            config_path = f.name

        monkeypatch.setenv('ODOO_CONFIG_PATH', config_path)

        # Reset singleton
        import src.mcp.odoo_mcp as odoo_module
        odoo_module._odoo_mcp = None

        mcp1 = get_odoo_mcp()
        mcp2 = get_odoo_mcp()

        assert mcp1 is mcp2
