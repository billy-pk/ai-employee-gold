"""
Finance Watcher - Monitor bank CSV imports and analyze transactions.

Watches Business/Transactions/ folder for new CSV files and:
- Parses transactions from multiple bank formats (Generic, Chase, Bank of America)
- Detects recurring subscriptions using pattern matching
- Flags large transactions above a configurable threshold
- Creates action files in Needs_Action/ for review
"""

import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

from .base_watcher import BaseWatcher
from ..utils.logger import get_logger
from ..utils.vault_helpers import (
    get_vault_folder,
    write_markdown_file,
    generate_unique_id,
)

load_dotenv()


# Known subscription patterns for automatic detection
SUBSCRIPTION_PATTERNS = [
    {'pattern': r'netflix', 'name': 'Netflix', 'category': 'entertainment'},
    {'pattern': r'spotify', 'name': 'Spotify', 'category': 'entertainment'},
    {'pattern': r'adobe', 'name': 'Adobe Creative Cloud', 'category': 'software'},
    {'pattern': r'microsoft.*365|office.*365', 'name': 'Microsoft 365', 'category': 'software'},
    {'pattern': r'google.*storage|google.*one', 'name': 'Google One', 'category': 'cloud'},
    {'pattern': r'dropbox', 'name': 'Dropbox', 'category': 'cloud'},
    {'pattern': r'icloud', 'name': 'Apple iCloud', 'category': 'cloud'},
    {'pattern': r'amazon.*prime', 'name': 'Amazon Prime', 'category': 'shopping'},
    {'pattern': r'hulu', 'name': 'Hulu', 'category': 'entertainment'},
    {'pattern': r'disney.*plus|disney\+', 'name': 'Disney+', 'category': 'entertainment'},
    {'pattern': r'hbo.*max', 'name': 'HBO Max', 'category': 'entertainment'},
    {'pattern': r'youtube.*prem', 'name': 'YouTube Premium', 'category': 'entertainment'},
    {'pattern': r'github', 'name': 'GitHub', 'category': 'software'},
    {'pattern': r'slack', 'name': 'Slack', 'category': 'software'},
    {'pattern': r'zoom', 'name': 'Zoom', 'category': 'software'},
    {'pattern': r'notion', 'name': 'Notion', 'category': 'software'},
    {'pattern': r'1password|onepassword', 'name': '1Password', 'category': 'software'},
    {'pattern': r'lastpass', 'name': 'LastPass', 'category': 'software'},
    {'pattern': r'chatgpt|openai', 'name': 'OpenAI/ChatGPT', 'category': 'software'},
    {'pattern': r'anthropic|claude', 'name': 'Anthropic', 'category': 'software'},
    {'pattern': r'aws|amazon.*web', 'name': 'AWS', 'category': 'cloud'},
    {'pattern': r'digitalocean', 'name': 'DigitalOcean', 'category': 'cloud'},
    {'pattern': r'heroku', 'name': 'Heroku', 'category': 'cloud'},
    {'pattern': r'vercel', 'name': 'Vercel', 'category': 'cloud'},
    {'pattern': r'gym|fitness|planet.*fitness|anytime', 'name': 'Gym Membership', 'category': 'health'},
]


class FinanceWatcher(BaseWatcher):
    """
    Finance Watcher - Monitor and analyze bank CSV imports.

    Watches Business/Transactions/ folder for new CSV files and processes
    them to detect subscriptions, flag large transactions, and create
    review action files.
    """

    def __init__(self, check_interval: int = 60):
        """
        Initialize Finance Watcher.

        Args:
            check_interval: Seconds between checks (default: 60)
        """
        self.logger = get_logger('FinanceWatcher')
        super().__init__(check_interval)

        # Watch folder
        self.watch_folder = os.getenv('FINANCE_WATCH_FOLDER', 'Business/Transactions')
        self.transactions_dir = self.vault_path / self.watch_folder

        # Large transaction threshold
        self.large_threshold = float(os.getenv('FINANCE_LARGE_TRANSACTION_THRESHOLD', '500'))

        # Track processed files
        self.logs = get_vault_folder('Logs')
        self.processed_file = self.logs / 'processed_finances.txt'
        self.processed_hashes = self._load_processed_hashes()

        # Ensure watch folder exists
        self.transactions_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Watching: {self.transactions_dir}")
        self.logger.info(f"Large transaction threshold: ${self.large_threshold}")
        self.logger.info(f"Previously processed files: {len(self.processed_hashes)}")

    def _load_processed_hashes(self) -> set:
        """Load set of previously processed file hashes."""
        if self.processed_file.exists():
            hashes = set(self.processed_file.read_text().splitlines())
            return {h for h in hashes if h}  # Filter empty lines
        return set()

    def _save_processed_hash(self, file_hash: str):
        """Save a file hash as processed."""
        with open(self.processed_file, 'a') as f:
            f.write(f'{file_hash}\n')
        self.processed_hashes.add(file_hash)

    def _compute_file_hash(self, filepath: Path) -> str:
        """Compute MD5 hash of file content for deduplication."""
        content = filepath.read_bytes()
        return hashlib.md5(content).hexdigest()

    def _find_csv_files(self) -> list[Path]:
        """
        Find all CSV files in the transactions folder (including subfolders).

        Returns:
            List of CSV file paths
        """
        csv_files = []
        for csv_file in self.transactions_dir.rglob('*.csv'):
            csv_files.append(csv_file)
        return csv_files

    def check_for_updates(self) -> list:
        """
        Check for new CSV files to process.

        Returns:
            List of new CSV file paths
        """
        new_files = []

        for csv_file in self._find_csv_files():
            file_hash = self._compute_file_hash(csv_file)
            if file_hash not in self.processed_hashes:
                new_files.append((csv_file, file_hash))
                self.logger.debug(f"New CSV found: {csv_file.name}")

        return new_files

    def _detect_csv_format(self, df: pd.DataFrame) -> str:
        """
        Auto-detect CSV format based on columns.

        Args:
            df: Pandas DataFrame with CSV data

        Returns:
            Format name: 'generic', 'chase', or 'bank_of_america'
        """
        columns_lower = [c.lower() for c in df.columns]

        # Chase: Posting Date, Description, Amount, Type
        if 'posting date' in columns_lower and 'type' in columns_lower:
            return 'chase'

        # Bank of America: Date, Description, Amount, Running Bal
        if 'running bal' in columns_lower or 'running balance' in columns_lower:
            return 'bank_of_america'

        # Generic: Date, Description, Amount, Balance
        return 'generic'

    def _normalize_columns(self, df: pd.DataFrame, format_type: str) -> pd.DataFrame:
        """
        Normalize columns to standard format: date, description, amount, balance.

        Args:
            df: Original DataFrame
            format_type: Detected format type

        Returns:
            DataFrame with normalized columns
        """
        # Create a copy to avoid modifying original
        df = df.copy()

        # Map columns based on format
        column_mapping = {
            'generic': {
                'date': 'date',
                'description': 'description',
                'amount': 'amount',
                'balance': 'balance'
            },
            'chase': {
                'posting date': 'date',
                'description': 'description',
                'amount': 'amount',
                'type': 'type'
            },
            'bank_of_america': {
                'date': 'date',
                'description': 'description',
                'amount': 'amount',
                'running bal': 'balance',
                'running balance': 'balance'
            }
        }

        mapping = column_mapping.get(format_type, column_mapping['generic'])

        # Rename columns (case-insensitive)
        rename_dict = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in mapping:
                rename_dict[col] = mapping[col_lower]

        df = df.rename(columns=rename_dict)

        return df

    def _parse_amount(self, value) -> float:
        """Parse amount value, handling various formats."""
        if pd.isna(value):
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        # String processing
        value = str(value).strip()

        # Remove currency symbols and commas
        value = re.sub(r'[$,]', '', value)

        # Handle parentheses for negative (accounting format)
        if value.startswith('(') and value.endswith(')'):
            value = '-' + value[1:-1]

        try:
            return float(value)
        except ValueError:
            return 0.0

    def _parse_csv(self, filepath: Path) -> dict:
        """
        Parse a bank CSV file and extract transactions.

        Args:
            filepath: Path to the CSV file

        Returns:
            Dict with transactions and metadata
        """
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode CSV with common encodings")

            # Skip empty files
            if df.empty:
                return {'error': 'Empty CSV file', 'transactions': []}

            # Detect format and normalize
            format_type = self._detect_csv_format(df)
            df = self._normalize_columns(df, format_type)

            # Parse transactions
            transactions = []
            for _, row in df.iterrows():
                amount = self._parse_amount(row.get('amount', 0))

                txn = {
                    'date': str(row.get('date', '')),
                    'description': str(row.get('description', '')),
                    'amount': amount,
                    'balance': self._parse_amount(row.get('balance', 0)) if 'balance' in row else None
                }
                transactions.append(txn)

            return {
                'filepath': filepath,
                'format': format_type,
                'transaction_count': len(transactions),
                'transactions': transactions
            }

        except Exception as e:
            self.logger.error(f"Failed to parse CSV {filepath}: {e}")
            return {'error': str(e), 'transactions': [], 'filepath': filepath}

    def _detect_subscriptions(self, transactions: list) -> list:
        """
        Detect subscription transactions using pattern matching.

        Args:
            transactions: List of transaction dicts

        Returns:
            List of detected subscriptions with metadata
        """
        detected = []

        for txn in transactions:
            description = txn.get('description', '').lower()

            for pattern_info in SUBSCRIPTION_PATTERNS:
                if re.search(pattern_info['pattern'], description, re.IGNORECASE):
                    detected.append({
                        **txn,
                        'subscription_name': pattern_info['name'],
                        'category': pattern_info['category']
                    })
                    break  # Only match first pattern

        return detected

    def _flag_large_transactions(self, transactions: list) -> list:
        """
        Flag transactions exceeding the threshold.

        Args:
            transactions: List of transaction dicts

        Returns:
            List of large transactions
        """
        large = []

        for txn in transactions:
            amount = abs(txn.get('amount', 0))
            if amount >= self.large_threshold:
                large.append(txn)

        return large

    def _calculate_summary(self, transactions: list) -> dict:
        """
        Calculate transaction summary statistics.

        Args:
            transactions: List of transaction dicts

        Returns:
            Summary dict with totals
        """
        total_income = sum(t['amount'] for t in transactions if t['amount'] > 0)
        total_expenses = sum(abs(t['amount']) for t in transactions if t['amount'] < 0)
        net = total_income - total_expenses

        return {
            'transaction_count': len(transactions),
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net': net
        }

    def create_action_file(self, item: tuple) -> Path:
        """
        Create a finance action file for review.

        Args:
            item: Tuple of (csv_path, file_hash)

        Returns:
            Path to the created action file
        """
        csv_path, file_hash = item

        # Parse CSV
        result = self._parse_csv(csv_path)

        if result.get('error') and not result.get('transactions'):
            # Create error action file
            return self._create_error_file(csv_path, file_hash, result['error'])

        transactions = result['transactions']

        # Analyze transactions
        subscriptions = self._detect_subscriptions(transactions)
        large_txns = self._flag_large_transactions(transactions)
        summary = self._calculate_summary(transactions)

        # Generate action file
        action_id = generate_unique_id('FINANCE')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"FINANCE_{timestamp}_{file_hash[:8]}.md"

        metadata = {
            'type': 'finance_review',
            'action_id': action_id,
            'source_file': csv_path.name,
            'source_path': str(csv_path.relative_to(self.vault_path)),
            'format_detected': result['format'],
            'transaction_count': summary['transaction_count'],
            'detected_at': datetime.now().isoformat(),
            'status': 'pending',
            'priority': 'normal' if not large_txns else 'high',
        }

        # Build body
        body = self._build_action_body(
            csv_path, result, subscriptions, large_txns, summary
        )

        # Write file
        filepath = self.needs_action / filename
        write_markdown_file(filepath, metadata, body)

        # Mark as processed
        self._save_processed_hash(file_hash)

        self.logger.info(f"Created action file: {filename}")
        self.logger.info(f"  Transactions: {summary['transaction_count']}")
        self.logger.info(f"  Subscriptions detected: {len(subscriptions)}")
        self.logger.info(f"  Large transactions: {len(large_txns)}")

        return filepath

    def _create_error_file(self, csv_path: Path, file_hash: str, error: str) -> Path:
        """Create an error action file for a malformed CSV."""
        action_id = generate_unique_id('FINANCE_ERROR')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"FINANCE_ERROR_{timestamp}_{file_hash[:8]}.md"

        metadata = {
            'type': 'finance_error',
            'action_id': action_id,
            'source_file': csv_path.name,
            'detected_at': datetime.now().isoformat(),
            'status': 'pending',
            'priority': 'high',
        }

        body = f"""# Finance Import Error

## Source File

- **File:** {csv_path.name}
- **Path:** {csv_path}

## Error

```
{error}
```

## Actions

- [ ] Review the CSV file format
- [ ] Fix or re-export from bank
- [ ] Re-import corrected file
"""

        filepath = self.needs_action / filename
        write_markdown_file(filepath, metadata, body)

        # Mark as processed (to avoid repeated errors)
        self._save_processed_hash(file_hash)

        return filepath

    def _build_action_body(
        self,
        csv_path: Path,
        result: dict,
        subscriptions: list,
        large_txns: list,
        summary: dict
    ) -> str:
        """Build the markdown body for the action file."""
        lines = [
            f"# Finance Review: {csv_path.name}",
            "",
            "## Source",
            "",
            f"- **File:** {csv_path.name}",
            f"- **Path:** {csv_path.relative_to(self.vault_path)}",
            f"- **Format:** {result['format']}",
            f"- **Imported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Summary",
            "",
            f"- **Transactions:** {summary['transaction_count']}",
            f"- **Total Income:** ${summary['total_income']:,.2f}",
            f"- **Total Expenses:** ${summary['total_expenses']:,.2f}",
            f"- **Net:** ${summary['net']:+,.2f}",
            "",
        ]

        # Subscriptions section
        if subscriptions:
            lines.extend([
                "## Flagged Transactions",
                "",
                "### Subscriptions Detected",
                "",
                "| Date | Description | Amount | Service | Category |",
                "|------|-------------|--------|---------|----------|",
            ])
            for sub in subscriptions:
                lines.append(
                    f"| {sub['date']} | {sub['description'][:30]} | "
                    f"${abs(sub['amount']):,.2f} | {sub['subscription_name']} | "
                    f"{sub['category']} |"
                )
            lines.append("")

        # Large transactions section
        if large_txns:
            lines.extend([
                f"### Large Transactions (> ${self.large_threshold:,.0f})",
                "",
                "| Date | Description | Amount |",
                "|------|-------------|--------|",
            ])
            for txn in large_txns:
                amount_str = f"${txn['amount']:+,.2f}" if txn['amount'] > 0 else f"-${abs(txn['amount']):,.2f}"
                lines.append(
                    f"| {txn['date']} | {txn['description'][:40]} | {amount_str} |"
                )
            lines.append("")

        # Actions checklist
        lines.extend([
            "## Actions",
            "",
            "- [ ] Review flagged subscriptions",
            "- [ ] Verify large transactions",
            "- [ ] Categorize uncategorized transactions",
            "- [ ] Reconcile with Odoo invoices (if applicable)",
            "",
        ])

        return '\n'.join(lines)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Finance Watcher - Monitor bank CSV imports'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for cron)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )

    args = parser.parse_args()

    watcher = FinanceWatcher(check_interval=args.interval)

    if args.once:
        print("=== Finance Watcher (Single Run) ===")
        count = watcher.run_once()
        print(f"\nProcessed: {count} file(s)")
    else:
        print("=== Finance Watcher ===")
        watcher.run()
