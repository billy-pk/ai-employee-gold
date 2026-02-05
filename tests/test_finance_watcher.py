"""Tests for the Finance Watcher module."""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import pandas as pd

from src.watchers.finance_watcher import FinanceWatcher, SUBSCRIPTION_PATTERNS


# Sample CSV data for different formats
SAMPLE_GENERIC_CSV = """Date,Description,Amount,Balance
01/05/2026,NETFLIX.COM,-15.99,1234.56
01/06/2026,CLIENT A PAYMENT,5000.00,6234.56
01/07/2026,ADOBE *CREATIVE,-54.99,6179.57
01/08/2026,OFFICE RENT,-1200.00,4979.57
01/09/2026,GROCERY STORE,-85.50,4894.07
"""

SAMPLE_CHASE_CSV = """Posting Date,Description,Amount,Type
01/05/2026,NETFLIX.COM,-15.99,Sale
01/06/2026,DIRECT DEPOSIT,5000.00,Payment
01/07/2026,SPOTIFY PREMIUM,-9.99,Sale
01/08/2026,RESTAURANT,-45.00,Sale
"""

SAMPLE_BOA_CSV = """Date,Description,Amount,Running Bal
01/05/2026,GITHUB INC,-4.00,1000.00
01/06/2026,WIRE TRANSFER,2500.00,3500.00
01/07/2026,1PASSWORD,-35.88,3464.12
01/08/2026,LARGE EQUIPMENT,-750.00,2714.12
"""


class TestFinanceWatcher:
    """Test cases for FinanceWatcher class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Business' / 'Transactions').mkdir(parents=True)
            (vault / 'Needs_Action').mkdir()
            (vault / 'Logs').mkdir()
            yield vault

    @pytest.fixture
    def watcher(self, temp_vault, monkeypatch):
        """Create a FinanceWatcher with temp vault."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))
        monkeypatch.setenv('FINANCE_LARGE_TRANSACTION_THRESHOLD', '500')
        return FinanceWatcher()

    def test_initialization(self, watcher, temp_vault):
        """Test that FinanceWatcher initializes correctly."""
        assert watcher.transactions_dir == temp_vault / 'Business' / 'Transactions'
        assert watcher.large_threshold == 500.0
        assert watcher.processed_hashes == set()

    def test_detect_generic_format(self, watcher, temp_vault):
        """Test detection of generic CSV format."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        df = pd.read_csv(csv_path)
        format_type = watcher._detect_csv_format(df)
        assert format_type == 'generic'

    def test_detect_chase_format(self, watcher, temp_vault):
        """Test detection of Chase CSV format."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'chase.csv'
        csv_path.write_text(SAMPLE_CHASE_CSV)

        df = pd.read_csv(csv_path)
        format_type = watcher._detect_csv_format(df)
        assert format_type == 'chase'

    def test_detect_boa_format(self, watcher, temp_vault):
        """Test detection of Bank of America CSV format."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'boa.csv'
        csv_path.write_text(SAMPLE_BOA_CSV)

        df = pd.read_csv(csv_path)
        format_type = watcher._detect_csv_format(df)
        assert format_type == 'bank_of_america'

    def test_parse_csv_generic(self, watcher, temp_vault):
        """Test parsing generic CSV format."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        result = watcher._parse_csv(csv_path)

        assert result['format'] == 'generic'
        assert result['transaction_count'] == 5
        assert len(result['transactions']) == 5

        # Check first transaction
        first_txn = result['transactions'][0]
        assert first_txn['amount'] == -15.99
        assert 'NETFLIX' in first_txn['description']

    def test_parse_amount_formats(self, watcher):
        """Test parsing various amount formats."""
        assert watcher._parse_amount(15.99) == 15.99
        assert watcher._parse_amount('15.99') == 15.99
        assert watcher._parse_amount('$15.99') == 15.99
        assert watcher._parse_amount('-$15.99') == -15.99
        assert watcher._parse_amount('$1,234.56') == 1234.56
        assert watcher._parse_amount('(15.99)') == -15.99  # Accounting format
        assert watcher._parse_amount('') == 0.0
        assert watcher._parse_amount(None) == 0.0

    def test_detect_subscriptions(self, watcher, temp_vault):
        """Test subscription detection."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        result = watcher._parse_csv(csv_path)
        subscriptions = watcher._detect_subscriptions(result['transactions'])

        # Should detect Netflix and Adobe
        assert len(subscriptions) == 2

        names = [s['subscription_name'] for s in subscriptions]
        assert 'Netflix' in names
        assert 'Adobe Creative Cloud' in names

    def test_detect_subscriptions_all_patterns(self, watcher):
        """Test that all subscription patterns are valid regex."""
        import re
        for pattern_info in SUBSCRIPTION_PATTERNS:
            # Should not raise
            re.compile(pattern_info['pattern'], re.IGNORECASE)

    def test_flag_large_transactions(self, watcher, temp_vault):
        """Test large transaction flagging."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        result = watcher._parse_csv(csv_path)
        large = watcher._flag_large_transactions(result['transactions'])

        # Should flag CLIENT A PAYMENT ($5000) and OFFICE RENT ($1200)
        assert len(large) == 2

        amounts = [abs(t['amount']) for t in large]
        assert 5000.00 in amounts
        assert 1200.00 in amounts

    def test_calculate_summary(self, watcher):
        """Test transaction summary calculation."""
        transactions = [
            {'amount': 5000.00},
            {'amount': -15.99},
            {'amount': -54.99},
            {'amount': 1000.00},
            {'amount': -100.00}
        ]

        summary = watcher._calculate_summary(transactions)

        assert summary['transaction_count'] == 5
        assert summary['total_income'] == 6000.00
        assert summary['total_expenses'] == 170.98
        assert abs(summary['net'] - 5829.02) < 0.01

    def test_check_for_updates_finds_new_files(self, watcher, temp_vault):
        """Test that check_for_updates finds new CSV files."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        updates = watcher.check_for_updates()

        assert len(updates) == 1
        assert updates[0][0] == csv_path

    def test_check_for_updates_skips_processed(self, watcher, temp_vault):
        """Test that processed files are skipped."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        # Process file
        updates = watcher.check_for_updates()
        file_hash = updates[0][1]
        watcher._save_processed_hash(file_hash)

        # Check again - should be empty
        updates = watcher.check_for_updates()
        assert len(updates) == 0

    def test_create_action_file(self, watcher, temp_vault):
        """Test action file creation."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        updates = watcher.check_for_updates()
        action_file = watcher.create_action_file(updates[0])

        assert action_file.exists()
        assert action_file.parent == watcher.needs_action
        assert action_file.name.startswith('FINANCE_')

        # Check content
        content = action_file.read_text()
        assert 'Finance Review' in content
        assert 'test.csv' in content
        assert 'Subscriptions Detected' in content
        assert 'Netflix' in content
        assert 'Large Transactions' in content

    def test_create_action_file_marks_processed(self, watcher, temp_vault):
        """Test that creating action file marks CSV as processed."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        updates = watcher.check_for_updates()
        watcher.create_action_file(updates[0])

        # Should not find the file again
        updates = watcher.check_for_updates()
        assert len(updates) == 0

    def test_run_once_processes_files(self, watcher, temp_vault):
        """Test single execution mode."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'test.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        count = watcher.run_once()

        assert count == 1
        action_files = list(watcher.needs_action.glob('FINANCE_*.md'))
        assert len(action_files) == 1

    def test_finds_csv_in_subfolders(self, watcher, temp_vault):
        """Test that CSV files in subfolders are found."""
        subfolder = temp_vault / 'Business' / 'Transactions' / '2026-01'
        subfolder.mkdir()
        csv_path = subfolder / 'bank_export.csv'
        csv_path.write_text(SAMPLE_GENERIC_CSV)

        updates = watcher.check_for_updates()
        assert len(updates) == 1
        assert updates[0][0] == csv_path

    def test_handles_empty_csv(self, watcher, temp_vault):
        """Test handling of empty CSV files."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'empty.csv'
        csv_path.write_text('')

        result = watcher._parse_csv(csv_path)
        assert 'error' in result

    def test_handles_malformed_csv(self, watcher, temp_vault):
        """Test handling of malformed CSV files."""
        csv_path = temp_vault / 'Business' / 'Transactions' / 'bad.csv'
        csv_path.write_text('not,a,valid\ncsv,file,format\nwith,wrong,data')

        # Should not raise, just return what it can parse
        result = watcher._parse_csv(csv_path)
        assert 'transactions' in result


class TestSubscriptionPatterns:
    """Test subscription pattern matching."""

    def test_netflix_pattern(self):
        """Test Netflix detection."""
        import re
        pattern = next(p for p in SUBSCRIPTION_PATTERNS if p['name'] == 'Netflix')
        assert re.search(pattern['pattern'], 'NETFLIX.COM', re.IGNORECASE)
        assert re.search(pattern['pattern'], 'Netflix Inc', re.IGNORECASE)

    def test_adobe_pattern(self):
        """Test Adobe detection."""
        import re
        pattern = next(p for p in SUBSCRIPTION_PATTERNS if p['name'] == 'Adobe Creative Cloud')
        assert re.search(pattern['pattern'], 'ADOBE *CREATIVE', re.IGNORECASE)
        assert re.search(pattern['pattern'], 'Adobe Inc', re.IGNORECASE)

    def test_microsoft_pattern(self):
        """Test Microsoft 365 detection."""
        import re
        pattern = next(p for p in SUBSCRIPTION_PATTERNS if p['name'] == 'Microsoft 365')
        assert re.search(pattern['pattern'], 'MICROSOFT 365', re.IGNORECASE)
        assert re.search(pattern['pattern'], 'OFFICE 365', re.IGNORECASE)
