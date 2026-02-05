"""
Odoo MCP Server - Interact with Odoo via JSON-RPC/XML-RPC.

Provides invoice, payment, customer, and accounting capabilities
with retry logic, audit logging, and graceful error handling.
"""

import os
import json
import xmlrpc.client
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

from ..utils.logger import get_logger
from ..utils.vault_helpers import get_vault_folder
from ..utils.audit_logger import get_audit_logger


@dataclass
class OdooConfig:
    """Odoo connection configuration."""
    url: str
    database: str
    username: str
    api_key: str
    timeout: int = 30


class OdooConnectionError(Exception):
    """Raised when Odoo connection fails."""
    pass


class OdooOperationError(Exception):
    """Raised when an Odoo operation fails."""
    pass


class OdooMCP:
    """
    Odoo MCP Server for accounting and business operations.

    Features:
    - Create and retrieve invoices
    - Record payments
    - Manage customers
    - Check account balances
    - Get journal entries for reporting
    - Comprehensive audit logging
    - Graceful error handling
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Odoo MCP Server.

        Args:
            config_path: Path to odoo_config.json (default: credentials/odoo_config.json)
        """
        self.logger = get_logger('OdooMCP')
        self.audit = get_audit_logger()

        # Load configuration
        if config_path is None:
            config_path = os.getenv('ODOO_CONFIG_PATH', 'credentials/odoo_config.json')

        self.config = self._load_config(config_path)

        # Initialize connection (lazy)
        self._uid = None
        self._common = None
        self._models = None

        self.logger.info("Odoo MCP initialized")
        self.logger.info(f"Server: {self.config.url}")
        self.logger.info(f"Database: {self.config.database}")

    def _load_config(self, config_path: str) -> OdooConfig:
        """Load Odoo configuration from JSON file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Odoo config not found at {config_path}\n"
                f"Please create the file with url, database, username, and api_key"
            )

        with open(path) as f:
            data = json.load(f)

        return OdooConfig(
            url=data['url'],
            database=data['database'],
            username=data['username'],
            api_key=data['api_key'],
            timeout=data.get('timeout', 30)
        )

    def _get_common(self) -> xmlrpc.client.ServerProxy:
        """Get or create common endpoint proxy."""
        if self._common is None:
            self._common = xmlrpc.client.ServerProxy(
                f'{self.config.url}/xmlrpc/2/common',
                allow_none=True
            )
        return self._common

    def _get_models(self) -> xmlrpc.client.ServerProxy:
        """Get or create models endpoint proxy."""
        if self._models is None:
            self._models = xmlrpc.client.ServerProxy(
                f'{self.config.url}/xmlrpc/2/object',
                allow_none=True
            )
        return self._models

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, xmlrpc.client.Fault))
    )
    def authenticate(self) -> int:
        """
        Authenticate with Odoo and get user ID.

        Returns:
            User ID (uid)

        Raises:
            OdooConnectionError: If authentication fails
        """
        if self._uid is not None:
            return self._uid

        try:
            common = self._get_common()
            uid = common.authenticate(
                self.config.database,
                self.config.username,
                self.config.api_key,
                {}
            )

            if not uid:
                raise OdooConnectionError("Authentication failed - invalid credentials")

            self._uid = uid
            self.logger.info(f"Authenticated with Odoo (uid: {uid})")
            return uid

        except xmlrpc.client.Fault as e:
            raise OdooConnectionError(f"Odoo XML-RPC error: {e.faultString}")
        except Exception as e:
            raise OdooConnectionError(f"Connection error: {str(e)}")

    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Execute an Odoo model method.

        Args:
            model: Odoo model name (e.g., 'res.partner')
            method: Method to call (e.g., 'search_read')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Method result

        Raises:
            OdooOperationError: If operation fails
        """
        uid = self.authenticate()
        models = self._get_models()

        try:
            result = models.execute_kw(
                self.config.database,
                uid,
                self.config.api_key,
                model,
                method,
                list(args),
                kwargs if kwargs else {}
            )
            return result

        except xmlrpc.client.Fault as e:
            raise OdooOperationError(f"Odoo error: {e.faultString}")
        except Exception as e:
            raise OdooOperationError(f"Operation error: {str(e)}")

    def _safe_execute(self, model: str, method: str, *args, **kwargs) -> dict:
        """
        Execute with graceful error handling - returns dict with success/error.

        Args:
            model: Odoo model name
            method: Method to call
            *args, **kwargs: Method arguments

        Returns:
            Dict with 'success', 'data' or 'error'
        """
        try:
            result = self._execute(model, method, *args, **kwargs)
            return {'success': True, 'data': result}
        except (OdooConnectionError, OdooOperationError) as e:
            self.logger.error(f"Odoo operation failed: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== Customer Operations ====================

    def get_customers(self, limit: int = 100) -> dict:
        """
        Get list of all customers.

        Args:
            limit: Maximum number of customers to return

        Returns:
            Dict with 'success' and 'data' (list of customers) or 'error'
        """
        result = self._safe_execute(
            'res.partner',
            'search_read',
            [['customer_rank', '>', 0]],
            fields=['id', 'name', 'email', 'phone', 'street', 'city', 'country_id'],
            limit=limit
        )

        if result['success']:
            self.logger.info(f"Retrieved {len(result['data'])} customers")

        return result

    def get_customer(self, customer_id: int) -> dict:
        """
        Get details of a single customer.

        Args:
            customer_id: Odoo partner ID

        Returns:
            Dict with 'success' and 'data' (customer dict) or 'error'
        """
        result = self._safe_execute(
            'res.partner',
            'read',
            [customer_id],
            fields=['id', 'name', 'email', 'phone', 'street', 'city', 'country_id',
                    'total_invoiced', 'credit', 'debit']
        )

        if result['success'] and result['data']:
            result['data'] = result['data'][0]
            self.logger.info(f"Retrieved customer: {result['data'].get('name')}")
        elif result['success']:
            result = {'success': False, 'error': f'Customer {customer_id} not found'}

        return result

    def search_customer(self, name: str) -> dict:
        """
        Search for customers by name.

        Args:
            name: Name to search for (partial match)

        Returns:
            Dict with 'success' and 'data' (list of customers) or 'error'
        """
        result = self._safe_execute(
            'res.partner',
            'search_read',
            [['name', 'ilike', name], ['customer_rank', '>', 0]],
            fields=['id', 'name', 'email']
        )

        if result['success']:
            self.logger.info(f"Found {len(result['data'])} customers matching '{name}'")

        return result

    # ==================== Invoice Operations ====================

    def create_invoice(
        self,
        customer_id: int,
        lines: list[dict],
        due_date: Optional[str] = None
    ) -> dict:
        """
        Create a new customer invoice.

        Args:
            customer_id: Odoo partner ID
            lines: List of invoice line dicts with 'name', 'quantity', 'price_unit'
            due_date: Due date in YYYY-MM-DD format (optional)

        Returns:
            Dict with 'success', 'data' (invoice info) or 'error'

        Example:
            create_invoice(7, [
                {'name': 'Consulting Services', 'quantity': 10, 'price_unit': 150.00}
            ])
        """
        # Get default sales journal
        journal_result = self._safe_execute(
            'account.journal',
            'search_read',
            [['type', '=', 'sale']],
            fields=['id', 'name'],
            limit=1
        )

        if not journal_result['success'] or not journal_result['data']:
            return {'success': False, 'error': 'No sales journal found'}

        journal_id = journal_result['data'][0]['id']

        # Build invoice lines
        invoice_lines = []
        for line in lines:
            invoice_lines.append((0, 0, {
                'name': line.get('name', 'Service'),
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('price_unit', 0),
            }))

        # Build invoice data
        invoice_data = {
            'move_type': 'out_invoice',
            'partner_id': customer_id,
            'journal_id': journal_id,
            'invoice_line_ids': invoice_lines,
        }

        if due_date:
            invoice_data['invoice_date_due'] = due_date

        # Create invoice
        result = self._safe_execute('account.move', 'create', invoice_data)

        if result['success']:
            invoice_id = result['data']
            # Get invoice details
            invoice_info = self._safe_execute(
                'account.move',
                'read',
                [invoice_id],
                fields=['id', 'name', 'amount_total', 'state', 'partner_id']
            )

            if invoice_info['success'] and invoice_info['data']:
                invoice = invoice_info['data'][0]
                result['data'] = {
                    'invoice_id': invoice_id,
                    'name': invoice.get('name'),
                    'amount_total': invoice.get('amount_total'),
                    'state': invoice.get('state'),
                    'customer': invoice.get('partner_id', [None, 'Unknown'])[1]
                }

                # Audit log
                self.audit.log_invoice_create(
                    customer_id=customer_id,
                    invoice_id=invoice_id,
                    amount=invoice.get('amount_total'),
                    result='success'
                )

                self.logger.info(f"Created invoice: {invoice.get('name')} for ${invoice.get('amount_total')}")

        return result

    def confirm_invoice(self, invoice_id: int) -> dict:
        """
        Confirm (post) a draft invoice.

        Args:
            invoice_id: Invoice ID to confirm

        Returns:
            Dict with 'success' or 'error'
        """
        result = self._safe_execute('account.move', 'action_post', [invoice_id])

        if result['success']:
            self.logger.info(f"Confirmed invoice: {invoice_id}")

        return result

    def get_invoices(
        self,
        period_days: int = 30,
        status: Optional[str] = None
    ) -> dict:
        """
        Get list of invoices for a period.

        Args:
            period_days: Number of days to look back (default: 30)
            status: Filter by status ('draft', 'posted', 'cancel') or None for all

        Returns:
            Dict with 'success' and 'data' (list of invoices) or 'error'
        """
        domain = [['move_type', '=', 'out_invoice']]

        # Date filter
        start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        domain.append(['create_date', '>=', start_date])

        # Status filter
        if status:
            domain.append(['state', '=', status])

        result = self._safe_execute(
            'account.move',
            'search_read',
            domain,
            fields=['id', 'name', 'partner_id', 'amount_total', 'amount_residual',
                    'state', 'invoice_date', 'invoice_date_due', 'payment_state'],
            order='create_date desc'
        )

        if result['success']:
            self.logger.info(f"Retrieved {len(result['data'])} invoices")

        return result

    def get_invoice(self, invoice_id: int) -> dict:
        """
        Get details of a single invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Dict with 'success' and 'data' (invoice dict) or 'error'
        """
        result = self._safe_execute(
            'account.move',
            'read',
            [invoice_id],
            fields=['id', 'name', 'partner_id', 'amount_total', 'amount_residual',
                    'state', 'invoice_date', 'invoice_date_due', 'payment_state',
                    'invoice_line_ids']
        )

        if result['success'] and result['data']:
            result['data'] = result['data'][0]

            # Get invoice lines
            if result['data'].get('invoice_line_ids'):
                lines_result = self._safe_execute(
                    'account.move.line',
                    'read',
                    result['data']['invoice_line_ids'],
                    fields=['name', 'quantity', 'price_unit', 'price_subtotal']
                )
                if lines_result['success']:
                    result['data']['lines'] = lines_result['data']

            self.logger.info(f"Retrieved invoice: {result['data'].get('name')}")
        elif result['success']:
            result = {'success': False, 'error': f'Invoice {invoice_id} not found'}

        return result

    # ==================== Payment Operations ====================

    def create_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_date: Optional[str] = None
    ) -> dict:
        """
        Record a payment for an invoice.

        Args:
            invoice_id: Invoice ID to pay
            amount: Payment amount
            payment_date: Payment date in YYYY-MM-DD format (default: today)

        Returns:
            Dict with 'success', 'data' (payment info) or 'error'
        """
        # Get invoice details
        invoice_result = self.get_invoice(invoice_id)
        if not invoice_result['success']:
            return invoice_result

        invoice = invoice_result['data']

        # Get default payment journal (bank)
        journal_result = self._safe_execute(
            'account.journal',
            'search_read',
            [['type', '=', 'bank']],
            fields=['id', 'name'],
            limit=1
        )

        if not journal_result['success'] or not journal_result['data']:
            return {'success': False, 'error': 'No bank journal found'}

        journal_id = journal_result['data'][0]['id']

        # Create payment
        payment_data = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': invoice['partner_id'][0] if invoice.get('partner_id') else None,
            'amount': amount,
            'journal_id': journal_id,
            'date': payment_date or datetime.now().strftime('%Y-%m-%d'),
        }

        result = self._safe_execute('account.payment', 'create', payment_data)

        if result['success']:
            payment_id = result['data']

            # Confirm the payment
            self._safe_execute('account.payment', 'action_post', [payment_id])

            result['data'] = {
                'payment_id': payment_id,
                'amount': amount,
                'invoice_id': invoice_id,
                'date': payment_data['date']
            }

            # Audit log
            self.audit.log_action(
                action_type='payment_create',
                actor='claude_code',
                target=str(invoice_id),
                parameters={'amount': amount},
                approval_status='approved',
                result='success',
                result_details={'payment_id': payment_id}
            )

            self.logger.info(f"Created payment: ${amount} for invoice {invoice_id}")

        return result

    # ==================== Account Operations ====================

    def get_account_balance(self, account_id: Optional[int] = None) -> dict:
        """
        Get account balance(s).

        Args:
            account_id: Specific account ID, or None for all receivable/payable

        Returns:
            Dict with 'success' and 'data' (balance info) or 'error'
        """
        if account_id:
            domain = [['id', '=', account_id]]
        else:
            # Get receivable and payable accounts
            domain = [['account_type', 'in', ['asset_receivable', 'liability_payable']]]

        result = self._safe_execute(
            'account.account',
            'search_read',
            domain,
            fields=['id', 'name', 'code', 'account_type', 'current_balance']
        )

        if result['success']:
            self.logger.info(f"Retrieved {len(result['data'])} account balances")

        return result

    def get_journal_entries(self, period_days: int = 30) -> dict:
        """
        Get journal entries for reporting.

        Args:
            period_days: Number of days to look back

        Returns:
            Dict with 'success' and 'data' (list of entries) or 'error'
        """
        start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')

        result = self._safe_execute(
            'account.move',
            'search_read',
            [['date', '>=', start_date], ['state', '=', 'posted']],
            fields=['id', 'name', 'date', 'move_type', 'amount_total', 'partner_id', 'journal_id'],
            order='date desc',
            limit=500
        )

        if result['success']:
            self.logger.info(f"Retrieved {len(result['data'])} journal entries")

        return result

    # ==================== Utility Methods ====================

    def test_connection(self) -> dict:
        """
        Test connection to Odoo.

        Returns:
            Dict with connection status and server info
        """
        try:
            common = self._get_common()
            version = common.version()
            uid = self.authenticate()

            return {
                'success': True,
                'connected': True,
                'server_version': version.get('server_version'),
                'uid': uid,
                'database': self.config.database
            }
        except Exception as e:
            return {
                'success': False,
                'connected': False,
                'error': str(e)
            }

    def get_summary(self) -> dict:
        """
        Get a summary of key Odoo data for reporting.

        Returns:
            Dict with customer count, invoice totals, etc.
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'customers': 0,
            'invoices_draft': 0,
            'invoices_posted': 0,
            'total_invoiced': 0,
            'total_outstanding': 0,
        }

        # Customer count
        customers = self.get_customers(limit=1000)
        if customers['success']:
            summary['customers'] = len(customers['data'])

        # Invoice stats
        invoices = self.get_invoices(period_days=365, status='posted')
        if invoices['success']:
            summary['invoices_posted'] = len(invoices['data'])
            summary['total_invoiced'] = sum(inv.get('amount_total', 0) for inv in invoices['data'])
            summary['total_outstanding'] = sum(inv.get('amount_residual', 0) for inv in invoices['data'])

        draft_invoices = self.get_invoices(period_days=365, status='draft')
        if draft_invoices['success']:
            summary['invoices_draft'] = len(draft_invoices['data'])

        return summary


# Singleton instance
_odoo_mcp: Optional[OdooMCP] = None


def get_odoo_mcp() -> OdooMCP:
    """Get the singleton OdooMCP instance."""
    global _odoo_mcp
    if _odoo_mcp is None:
        _odoo_mcp = OdooMCP()
    return _odoo_mcp


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Odoo MCP Server')
    parser.add_argument('--test', action='store_true', help='Test connection')
    parser.add_argument('--summary', action='store_true', help='Show summary')
    parser.add_argument('--customers', action='store_true', help='List customers')
    parser.add_argument('--invoices', action='store_true', help='List recent invoices')

    args = parser.parse_args()

    mcp = OdooMCP()

    if args.test:
        print("=== Odoo Connection Test ===")
        result = mcp.test_connection()
        if result['success']:
            print(f"✓ Connected to Odoo {result['server_version']}")
            print(f"  Database: {result['database']}")
            print(f"  User ID: {result['uid']}")
        else:
            print(f"✗ Connection failed: {result['error']}")

    elif args.summary:
        print("=== Odoo Summary ===")
        summary = mcp.get_summary()
        print(f"Customers: {summary['customers']}")
        print(f"Invoices (posted): {summary['invoices_posted']}")
        print(f"Invoices (draft): {summary['invoices_draft']}")
        print(f"Total invoiced: ${summary['total_invoiced']:,.2f}")
        print(f"Outstanding: ${summary['total_outstanding']:,.2f}")

    elif args.customers:
        print("=== Customers ===")
        result = mcp.get_customers()
        if result['success']:
            for c in result['data']:
                print(f"  {c['id']}: {c['name']} ({c.get('email', 'no email')})")
        else:
            print(f"Error: {result['error']}")

    elif args.invoices:
        print("=== Recent Invoices ===")
        result = mcp.get_invoices(period_days=90)
        if result['success']:
            for inv in result['data']:
                customer = inv.get('partner_id', [None, 'Unknown'])[1]
                print(f"  {inv['name']}: {customer} - ${inv['amount_total']:,.2f} ({inv['state']})")
        else:
            print(f"Error: {result['error']}")

    else:
        print("Odoo MCP Server")
        print("Use --test, --summary, --customers, or --invoices")
