"""Tests for vault_helpers module."""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from src.utils.vault_helpers import (
    parse_frontmatter,
    format_frontmatter,
    generate_unique_id,
    generate_timestamp_id,
    safe_filename,
    read_markdown_file,
    write_markdown_file,
    update_frontmatter,
)


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_parse_with_frontmatter(self):
        content = """---
title: Test
status: pending
---

# Body content
"""
        metadata, body = parse_frontmatter(content)
        assert metadata['title'] == 'Test'
        assert metadata['status'] == 'pending'
        assert '# Body content' in body

    def test_parse_without_frontmatter(self):
        content = "# Just body content\n\nNo frontmatter here."
        metadata, body = parse_frontmatter(content)
        assert metadata == {}
        assert content == body

    def test_parse_empty_frontmatter(self):
        content = """---
---

Body only
"""
        metadata, body = parse_frontmatter(content)
        assert metadata == {}
        assert 'Body only' in body


class TestFormatFrontmatter:
    """Tests for format_frontmatter function."""

    def test_format_with_metadata(self):
        metadata = {'title': 'Test', 'status': 'pending'}
        body = "# Content"
        result = format_frontmatter(metadata, body)
        assert result.startswith('---\n')
        assert 'title: Test' in result
        assert '# Content' in result

    def test_format_without_metadata(self):
        metadata = {}
        body = "# Content"
        result = format_frontmatter(metadata, body)
        assert result == "# Content"


class TestGenerateIds:
    """Tests for ID generation functions."""

    def test_generate_unique_id_with_prefix(self):
        id1 = generate_unique_id("FILE")
        assert id1.startswith("FILE_")
        assert len(id1) == 13  # FILE_ + 8 chars

    def test_generate_unique_id_without_prefix(self):
        id1 = generate_unique_id()
        assert len(id1) == 8

    def test_generate_unique_ids_are_unique(self):
        ids = [generate_unique_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_generate_timestamp_id(self):
        id1 = generate_timestamp_id("PLAN")
        assert id1.startswith("PLAN_")
        assert datetime.now().strftime("%Y%m%d") in id1


class TestSafeFilename:
    """Tests for safe_filename function."""

    def test_safe_filename_basic(self):
        assert safe_filename("hello world") == "hello_world"

    def test_safe_filename_special_chars(self):
        assert safe_filename("test@#$%file") == "test_file"

    def test_safe_filename_max_length(self):
        long_name = "a" * 100
        result = safe_filename(long_name, max_length=20)
        assert len(result) == 20

    def test_safe_filename_consecutive_underscores(self):
        result = safe_filename("test___file")
        assert result == "test_file"


class TestReadWriteMarkdown:
    """Tests for read/write markdown functions."""

    def test_write_and_read_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.md"
            metadata = {'status': 'pending', 'type': 'test'}
            body = "# Test Content\n\nThis is a test."

            write_markdown_file(filepath, metadata, body)
            assert filepath.exists()

            read_metadata, read_body = read_markdown_file(filepath)
            assert read_metadata['status'] == 'pending'
            assert read_metadata['type'] == 'test'
            assert '# Test Content' in read_body

    def test_update_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.md"
            write_markdown_file(filepath, {'status': 'pending'}, "Body")

            update_frontmatter(filepath, {'status': 'processed', 'new_field': 'value'})

            metadata, _ = read_markdown_file(filepath)
            assert metadata['status'] == 'processed'
            assert metadata['new_field'] == 'value'

    def test_read_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            read_markdown_file(Path("/nonexistent/file.md"))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
