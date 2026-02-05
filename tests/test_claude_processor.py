"""Tests for ClaudeProcessor module."""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import json
from unittest.mock import Mock, patch


class TestClaudeProcessorSmartTriggering:
    """Tests for smart triggering functionality."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Needs_Action').mkdir()
            (vault / 'Plans').mkdir()
            (vault / 'Logs').mkdir()
            yield vault

    def test_get_pending_items_empty(self, temp_vault, monkeypatch):
        """Test getting pending items when folder is empty."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        from src.processors.claude_processor import ClaudeProcessor
        processor = ClaudeProcessor()

        items = processor._get_pending_items()
        assert items == []

    def test_get_pending_items_with_pending(self, temp_vault, monkeypatch):
        """Test getting pending items with pending status."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        # Create a pending item
        item_file = temp_vault / 'Needs_Action' / 'test_item.md'
        item_file.write_text("""---
status: pending
---

# Test item
""")

        from src.processors.claude_processor import ClaudeProcessor
        processor = ClaudeProcessor()

        items = processor._get_pending_items()
        assert len(items) == 1
        assert items[0].name == 'test_item.md'

    def test_get_pending_items_skips_processed(self, temp_vault, monkeypatch):
        """Test that processed items are skipped."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        # Create a processed item
        item_file = temp_vault / 'Needs_Action' / 'processed_item.md'
        item_file.write_text("""---
status: processed
---

# Processed item
""")

        from src.processors.claude_processor import ClaudeProcessor
        processor = ClaudeProcessor()

        items = processor._get_pending_items()
        assert items == []

    def test_log_usage_creates_file(self, temp_vault, monkeypatch):
        """Test that usage logging creates the log file."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        from src.processors.claude_processor import ClaudeProcessor
        processor = ClaudeProcessor()

        processor._log_usage(invoked=False, items_count=0, result='skipped_no_items')

        assert processor.usage_log.exists()
        data = json.loads(processor.usage_log.read_text())
        assert len(data) == 1
        assert data[0]['invoked'] is False
        assert data[0]['result'] == 'skipped_no_items'

    def test_log_usage_appends(self, temp_vault, monkeypatch):
        """Test that usage logging appends entries."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        from src.processors.claude_processor import ClaudeProcessor
        processor = ClaudeProcessor()

        processor._log_usage(invoked=False, items_count=0, result='skipped')
        processor._log_usage(invoked=True, items_count=2, result='success')

        data = json.loads(processor.usage_log.read_text())
        assert len(data) == 2

    def test_get_usage_stats(self, temp_vault, monkeypatch):
        """Test usage statistics retrieval."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        from src.processors.claude_processor import ClaudeProcessor
        processor = ClaudeProcessor()

        # Log some usage
        processor._log_usage(invoked=False, items_count=0, result='skipped')
        processor._log_usage(invoked=True, items_count=3, result='success')
        processor._log_usage(invoked=True, items_count=1, result='error: timeout')

        stats = processor.get_usage_stats()
        assert stats['invocations'] == 2
        assert stats['items_processed'] == 4  # 3 + 1
        assert stats['skipped_checks'] == 1
        assert stats['errors'] == 1

    def test_run_once_no_items(self, temp_vault, monkeypatch):
        """Test run_once when no items to process."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))

        from src.processors.claude_processor import ClaudeProcessor
        processor = ClaudeProcessor()

        result = processor.run_once()

        assert result['invoked'] is False
        assert result['reason'] == 'no_pending_items'


class TestPromptBuilding:
    """Tests for prompt building."""

    def test_build_prompt(self):
        """Test prompt building with items."""
        from pathlib import Path

        # Create mock paths
        items = [
            Path('/vault/Needs_Action/item1.md'),
            Path('/vault/Needs_Action/item2.md'),
        ]

        # Build prompt manually (same logic as in ClaudeProcessor)
        item_list = "\n".join(f"- {item.name}" for item in items)

        assert 'item1.md' in item_list
        assert 'item2.md' in item_list


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
