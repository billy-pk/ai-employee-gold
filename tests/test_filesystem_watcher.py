"""Tests for FileSystemWatcher module."""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from src.watchers.filesystem_watcher import FileSystemWatcher


class TestFileSystemWatcher:
    """Tests for FileSystemWatcher class."""

    @pytest.fixture
    def temp_vault(self):
        """Create a temporary vault structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Inbox').mkdir()
            (vault / 'Needs_Action').mkdir()
            (vault / 'Logs').mkdir()
            yield vault

    @pytest.fixture
    def watcher(self, temp_vault, monkeypatch):
        """Create a FileSystemWatcher with temp vault."""
        monkeypatch.setenv('VAULT_PATH', str(temp_vault))
        return FileSystemWatcher()

    def test_init(self, watcher, temp_vault):
        """Test watcher initialization."""
        assert watcher.inbox == temp_vault / 'Inbox'
        assert watcher.needs_action == temp_vault / 'Needs_Action'
        assert watcher.processed_hashes == set()

    def test_get_file_hash(self, watcher, temp_vault):
        """Test file hash generation."""
        test_file = temp_vault / 'Inbox' / 'test.txt'
        test_file.write_text("Hello World")

        hash1 = watcher._get_file_hash(test_file)
        assert len(hash1) == 32  # MD5 hex digest

        # Same file should produce same hash
        hash2 = watcher._get_file_hash(test_file)
        assert hash1 == hash2

    def test_format_size(self, watcher):
        """Test size formatting."""
        assert watcher._format_size(500) == "500.0 B"
        assert watcher._format_size(1024) == "1.0 KB"
        assert watcher._format_size(1024 * 1024) == "1.0 MB"
        assert watcher._format_size(1024 * 1024 * 1024) == "1.0 GB"

    def test_get_content_preview_text(self, watcher, temp_vault):
        """Test content preview for text files."""
        test_file = temp_vault / 'Inbox' / 'test.txt'
        test_file.write_text("Hello World")

        preview = watcher._get_content_preview(test_file)
        assert preview == "Hello World"

    def test_get_content_preview_long_text(self, watcher, temp_vault):
        """Test content preview truncation."""
        test_file = temp_vault / 'Inbox' / 'test.txt'
        test_file.write_text("x" * 1000)

        preview = watcher._get_content_preview(test_file, max_chars=100)
        assert len(preview) == 103  # 100 chars + '...'
        assert preview.endswith('...')

    def test_get_content_preview_image(self, watcher, temp_vault):
        """Test content preview for image files."""
        test_file = temp_vault / 'Inbox' / 'test.png'
        test_file.write_bytes(b'\x89PNG\r\n')

        preview = watcher._get_content_preview(test_file)
        assert 'Image file' in preview

    def test_check_for_updates_empty(self, watcher):
        """Test check when inbox is empty."""
        updates = watcher.check_for_updates()
        assert updates == []

    def test_check_for_updates_new_file(self, watcher, temp_vault):
        """Test detection of new file."""
        test_file = temp_vault / 'Inbox' / 'new_file.txt'
        test_file.write_text("New content")

        updates = watcher.check_for_updates()
        assert len(updates) == 1
        assert updates[0][0] == test_file

    def test_check_for_updates_skips_processed(self, watcher, temp_vault):
        """Test that processed files are skipped."""
        test_file = temp_vault / 'Inbox' / 'test.txt'
        test_file.write_text("Content")

        # Process once
        updates1 = watcher.check_for_updates()
        for filepath, file_hash in updates1:
            watcher._save_processed_hash(file_hash)

        # Should not find it again
        updates2 = watcher.check_for_updates()
        assert len(updates2) == 0

    def test_create_action_file(self, watcher, temp_vault):
        """Test action file creation."""
        test_file = temp_vault / 'Inbox' / 'test_doc.txt'
        test_file.write_text("Test document content")
        file_hash = watcher._get_file_hash(test_file)

        action_file = watcher.create_action_file((test_file, file_hash))

        assert action_file.exists()
        assert action_file.parent == watcher.needs_action

        content = action_file.read_text()
        assert 'type: file_drop' in content
        assert 'test_doc.txt' in content
        assert 'status: pending' in content

    def test_run_once(self, watcher, temp_vault):
        """Test single execution."""
        test_file = temp_vault / 'Inbox' / 'test.txt'
        test_file.write_text("Content")

        count = watcher.run_once()
        assert count == 1
        assert len(list(watcher.needs_action.glob('*.md'))) == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
