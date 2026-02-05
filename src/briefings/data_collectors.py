"""
Data collectors for daily briefings.

Collects data from Odoo and other sources, stores in the vault,
and generates formatted briefings for the morning brief.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field, asdict

from dotenv import load_dotenv

load_dotenv()

from ..utils.logger import get_logger
from ..utils.vault_helpers import (
    get_vault_folder,
    write_markdown_file,
    read_markdown_file,
    ensure_folder_exists,
)
from ..mcp.odoo_mcp import OdooMCP, get_odoo_mcp


@dataclass
class FinancialSnapshot:
    """Snapshot of financial data from Odoo."""
    timestamp: str
    total_customers: int = 0
    total_invoiced_30d: float = 0.0
    total_outstanding: float = 0.0
    draft_invoices: int = 0
    posted_invoices_30d: int = 0
    overdue_invoices: int = 0
    overdue_amount: float = 0.0
    recent_payments: list[dict] = field(default_factory=list)
    top_customers: list[dict] = field(default_factory=list)
    needs_attention: list[str] = field(default_factory=list)


class OdooDataCollector:
    """
    Collects financial data from Odoo for daily briefings.

    Features:
    - Pulls customer, invoice, and payment data
    - Calculates key metrics (outstanding, overdue, etc.)
    - Stores snapshots in the vault for trend analysis
    - Generates human-readable financial briefs
    """

    def __init__(self):
        """Initialize the Odoo data collector."""
        self.logger = get_logger('OdooDataCollector')
        self.odoo = get_odoo_mcp()
        self.data_folder = get_vault_folder('Data/Financial')
        self.briefs_folder = get_vault_folder('Briefs')

        # Ensure folders exist
        ensure_folder_exists(self.data_folder)
        ensure_folder_exists(self.briefs_folder)

        self.logger.info("Odoo Data Collector initialized")

    def collect_snapshot(self) -> FinancialSnapshot:
        """
        Collect a snapshot of current financial data.

        Returns:
            FinancialSnapshot with current Odoo data
        """
        self.logger.info("Collecting financial snapshot from Odoo")

        snapshot = FinancialSnapshot(
            timestamp=datetime.now().isoformat()
        )

        # Get customer count
        customers = self.odoo.get_customers(limit=1000)
        if customers['success']:
            snapshot.total_customers = len(customers['data'])
            # Get top customers by invoice amount
            snapshot.top_customers = self._get_top_customers(customers['data'][:10])

        # Get invoice stats for last 30 days
        invoices = self.odoo.get_invoices(period_days=30, status='posted')
        if invoices['success']:
            snapshot.posted_invoices_30d = len(invoices['data'])
            snapshot.total_invoiced_30d = sum(
                inv.get('amount_total', 0) for inv in invoices['data']
            )
            snapshot.total_outstanding = sum(
                inv.get('amount_residual', 0) for inv in invoices['data']
            )

            # Check for overdue invoices
            today = datetime.now().date()
            overdue = []
            for inv in invoices['data']:
                due_date_str = inv.get('invoice_date_due')
                if due_date_str:
                    try:
                        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                        if due_date < today and inv.get('amount_residual', 0) > 0:
                            overdue.append(inv)
                    except (ValueError, TypeError):
                        pass

            snapshot.overdue_invoices = len(overdue)
            snapshot.overdue_amount = sum(
                inv.get('amount_residual', 0) for inv in overdue
            )

            # Add overdue to needs_attention
            if snapshot.overdue_amount > 0:
                snapshot.needs_attention.append(
                    f"${snapshot.overdue_amount:,.2f} overdue from {snapshot.overdue_invoices} invoices"
                )

        # Get draft invoices
        draft_invoices = self.odoo.get_invoices(period_days=90, status='draft')
        if draft_invoices['success']:
            snapshot.draft_invoices = len(draft_invoices['data'])
            if snapshot.draft_invoices > 0:
                draft_total = sum(
                    inv.get('amount_total', 0) for inv in draft_invoices['data']
                )
                snapshot.needs_attention.append(
                    f"{snapshot.draft_invoices} draft invoices (${draft_total:,.2f}) need to be sent"
                )

        self.logger.info(f"Collected snapshot: {snapshot.total_customers} customers, "
                         f"${snapshot.total_invoiced_30d:,.2f} invoiced (30d)")

        return snapshot

    def _get_top_customers(self, customers: list[dict]) -> list[dict]:
        """Get simplified list of top customers."""
        result = []
        for c in customers[:5]:
            result.append({
                'id': c.get('id'),
                'name': c.get('name'),
                'email': c.get('email')
            })
        return result

    def save_snapshot(self, snapshot: FinancialSnapshot) -> Path:
        """
        Save a snapshot to the vault.

        Args:
            snapshot: FinancialSnapshot to save

        Returns:
            Path to saved file
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"FINANCIAL_SNAPSHOT_{date_str}.json"
        filepath = self.data_folder / filename

        with open(filepath, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2, default=str)

        self.logger.info(f"Saved financial snapshot: {filepath}")
        return filepath

    def load_snapshot(self, date_str: Optional[str] = None) -> Optional[FinancialSnapshot]:
        """
        Load a snapshot from the vault.

        Args:
            date_str: Date in YYYY-MM-DD format, or None for today

        Returns:
            FinancialSnapshot or None if not found
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        filename = f"FINANCIAL_SNAPSHOT_{date_str}.json"
        filepath = self.data_folder / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath) as f:
                data = json.load(f)

            return FinancialSnapshot(**data)
        except Exception as e:
            self.logger.error(f"Failed to load snapshot: {e}")
            return None

    def get_previous_snapshot(self, days_back: int = 7) -> Optional[FinancialSnapshot]:
        """
        Get the most recent previous snapshot for comparison.

        Args:
            days_back: How many days to look back

        Returns:
            FinancialSnapshot or None if not found
        """
        for i in range(1, days_back + 1):
            date = datetime.now() - timedelta(days=i)
            snapshot = self.load_snapshot(date.strftime('%Y-%m-%d'))
            if snapshot:
                return snapshot
        return None

    def generate_brief(self, snapshot: FinancialSnapshot) -> str:
        """
        Generate a human-readable financial brief.

        Args:
            snapshot: Current FinancialSnapshot

        Returns:
            Markdown formatted brief
        """
        lines = [
            "# Financial Brief",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
            "## Summary",
            "",
            f"- **Total Customers**: {snapshot.total_customers}",
            f"- **Invoiced (30d)**: ${snapshot.total_invoiced_30d:,.2f}",
            f"- **Outstanding**: ${snapshot.total_outstanding:,.2f}",
            f"- **Draft Invoices**: {snapshot.draft_invoices}",
            f"- **Posted Invoices (30d)**: {snapshot.posted_invoices_30d}",
            "",
        ]

        # Add overdue section if applicable
        if snapshot.overdue_amount > 0:
            lines.extend([
                "## Overdue",
                "",
                f"**{snapshot.overdue_invoices}** invoices are overdue, "
                f"totaling **${snapshot.overdue_amount:,.2f}**.",
                "",
            ])

        # Add needs attention
        if snapshot.needs_attention:
            lines.extend([
                "## Needs Attention",
                "",
            ])
            for item in snapshot.needs_attention:
                lines.append(f"- {item}")
            lines.append("")

        # Compare with previous snapshot
        previous = self.get_previous_snapshot()
        if previous:
            lines.extend([
                "## Trends (vs. last week)",
                "",
            ])

            # Calculate changes
            customer_change = snapshot.total_customers - previous.total_customers
            invoice_change = snapshot.total_invoiced_30d - previous.total_invoiced_30d
            outstanding_change = snapshot.total_outstanding - previous.total_outstanding

            if customer_change != 0:
                direction = "+" if customer_change > 0 else ""
                lines.append(f"- Customers: {direction}{customer_change}")

            if invoice_change != 0:
                direction = "+" if invoice_change > 0 else ""
                lines.append(f"- Invoiced: {direction}${invoice_change:,.2f}")

            if outstanding_change != 0:
                direction = "+" if outstanding_change > 0 else ""
                lines.append(f"- Outstanding: {direction}${outstanding_change:,.2f}")

            lines.append("")

        # Top customers
        if snapshot.top_customers:
            lines.extend([
                "## Top Customers",
                "",
            ])
            for i, c in enumerate(snapshot.top_customers[:5], 1):
                lines.append(f"{i}. {c['name']} ({c.get('email', 'no email')})")
            lines.append("")

        lines.extend([
            "---",
            "*Data from Odoo*"
        ])

        return '\n'.join(lines)

    def save_brief(self, brief: str) -> Path:
        """
        Save a brief to the vault.

        Args:
            brief: Markdown formatted brief

        Returns:
            Path to saved file
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"FINANCIAL_BRIEF_{date_str}.md"
        filepath = self.briefs_folder / filename

        metadata = {
            'type': 'financial_brief',
            'date': date_str,
            'generated_at': datetime.now().isoformat()
        }

        write_markdown_file(filepath, metadata, brief)

        self.logger.info(f"Saved financial brief: {filepath}")
        return filepath

    def run_daily_sync(self) -> dict:
        """
        Run the full daily sync process.

        Returns:
            Dict with sync results
        """
        self.logger.info("Starting daily Odoo sync")

        try:
            # Test connection first
            connection = self.odoo.test_connection()
            if not connection['success']:
                return {
                    'success': False,
                    'error': f"Odoo connection failed: {connection.get('error')}"
                }

            # Collect snapshot
            snapshot = self.collect_snapshot()

            # Save snapshot
            snapshot_path = self.save_snapshot(snapshot)

            # Generate and save brief
            brief = self.generate_brief(snapshot)
            brief_path = self.save_brief(brief)

            self.logger.info("Daily Odoo sync completed successfully")

            return {
                'success': True,
                'snapshot_path': str(snapshot_path),
                'brief_path': str(brief_path),
                'summary': {
                    'customers': snapshot.total_customers,
                    'invoiced_30d': snapshot.total_invoiced_30d,
                    'outstanding': snapshot.total_outstanding,
                    'overdue': snapshot.overdue_amount,
                    'needs_attention': len(snapshot.needs_attention)
                }
            }

        except Exception as e:
            self.logger.error(f"Daily sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Convenience functions
def collect_odoo_data() -> FinancialSnapshot:
    """Collect current Odoo financial data."""
    collector = OdooDataCollector()
    return collector.collect_snapshot()


def generate_financial_brief() -> str:
    """Generate a financial brief from current Odoo data."""
    collector = OdooDataCollector()
    snapshot = collector.collect_snapshot()
    return collector.generate_brief(snapshot)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Odoo Data Collector')
    parser.add_argument('--sync', action='store_true', help='Run daily sync')
    parser.add_argument('--snapshot', action='store_true', help='Collect snapshot only')
    parser.add_argument('--brief', action='store_true', help='Generate brief only')

    args = parser.parse_args()

    collector = OdooDataCollector()

    if args.sync:
        print("=== Running Daily Odoo Sync ===")
        result = collector.run_daily_sync()
        if result['success']:
            print(f"Snapshot saved: {result['snapshot_path']}")
            print(f"Brief saved: {result['brief_path']}")
            print(f"\nSummary:")
            for key, value in result['summary'].items():
                if isinstance(value, float):
                    print(f"  {key}: ${value:,.2f}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"Sync failed: {result['error']}")

    elif args.snapshot:
        print("=== Collecting Financial Snapshot ===")
        snapshot = collector.collect_snapshot()
        path = collector.save_snapshot(snapshot)
        print(f"Saved to: {path}")
        print(f"Customers: {snapshot.total_customers}")
        print(f"Invoiced (30d): ${snapshot.total_invoiced_30d:,.2f}")
        print(f"Outstanding: ${snapshot.total_outstanding:,.2f}")

    elif args.brief:
        print("=== Generating Financial Brief ===")
        snapshot = collector.collect_snapshot()
        brief = collector.generate_brief(snapshot)
        path = collector.save_brief(brief)
        print(f"Saved to: {path}")
        print()
        print(brief)

    else:
        print("Odoo Data Collector")
        print("Use --sync, --snapshot, or --brief")
