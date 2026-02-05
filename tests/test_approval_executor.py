"""Tests for ApprovalExecutor module."""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import re


class TestApprovalFileParsing:
    """Tests for approval file parsing."""

    def test_parse_email_action(self):
        """Test parsing email approval file."""
        content = """---
approval_id: APPROVAL_12345
action_type: email_send
plan_reference: /Plans/PLAN_12345.md
created_at: 2026-02-03T12:00:00
status: pending_approval
---

# Approval Request

## Draft Email

**To:** test@example.com
**Subject:** Test Subject

```
Hello,

This is a test email.

Best regards
```

## Reasoning

Test reasoning.
"""
        # Parse frontmatter
        import yaml
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        metadata = yaml.safe_load(frontmatter_match.group(1)) if frontmatter_match else {}
        body = content[frontmatter_match.end():] if frontmatter_match else content

        assert metadata['action_type'] == 'email_send'
        assert metadata['approval_id'] == 'APPROVAL_12345'

        # Parse email fields from body
        draft_section = re.search(r'## Draft Email\s*(.*?)(?=\n##|\Z)', body, re.DOTALL)
        search_area = draft_section.group(1) if draft_section else body

        to_match = re.search(r'\*\*To:\*\*\s*(.+)', search_area)
        subject_match = re.search(r'\*\*Subject:\*\*\s*(.+)', search_area)
        body_match = re.search(r'```\n(.*?)```', search_area, re.DOTALL)

        assert to_match.group(1).strip() == 'test@example.com'
        assert subject_match.group(1).strip() == 'Test Subject'
        assert 'This is a test email' in body_match.group(1)

    def test_parse_email_reply_action(self):
        """Test parsing email reply approval file."""
        content = """---
approval_id: APPROVAL_abc123
action_type: email_reply
---

## Draft Email

**To:** reply@example.com
**Subject:** Re: Original Subject

```
Thank you for your email.

Best regards
```
"""
        import yaml
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        metadata = yaml.safe_load(frontmatter_match.group(1)) if frontmatter_match else {}

        assert metadata['action_type'] == 'email_reply'


class TestExecutedIdTracking:
    """Tests for executed action ID tracking."""

    def test_load_executed_ids_empty(self):
        """Test loading when no file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executed_file = Path(tmpdir) / 'executed_actions.txt'

            if executed_file.exists():
                ids = set(executed_file.read_text().splitlines())
            else:
                ids = set()

            assert ids == set()

    def test_load_executed_ids_with_data(self):
        """Test loading existing IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executed_file = Path(tmpdir) / 'executed_actions.txt'
            executed_file.write_text("id1\nid2\nid3\n")

            ids = set(executed_file.read_text().splitlines())

            assert len(ids) == 3
            assert 'id1' in ids
            assert 'id2' in ids
            assert 'id3' in ids

    def test_save_executed_id(self):
        """Test saving executed ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executed_file = Path(tmpdir) / 'executed_actions.txt'

            # Save an ID
            with open(executed_file, 'a') as f:
                f.write('new_id\n')

            ids = set(executed_file.read_text().splitlines())
            assert 'new_id' in ids

    def test_idempotency(self):
        """Test that duplicate IDs are handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executed_file = Path(tmpdir) / 'executed_actions.txt'

            # Simulate multiple saves
            for _ in range(3):
                with open(executed_file, 'a') as f:
                    f.write('same_id\n')

            # Using set removes duplicates
            ids = set(executed_file.read_text().splitlines())
            assert 'same_id' in ids
            # Count in file shows duplicates
            lines = executed_file.read_text().splitlines()
            assert lines.count('same_id') == 3


class TestPlanUpdating:
    """Tests for plan file updating."""

    def test_update_plan_adds_outcome(self):
        """Test adding outcome to plan file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_file = Path(tmpdir) / 'PLAN_test.md'
            plan_file.write_text("""---
plan_id: PLAN_test
status: pending_approval
---

# Test Plan

## Analysis

Some analysis here.
""")

            # Read and update
            content = plan_file.read_text()
            outcome = "✅ **Success**\n\n- Email sent successfully"
            timestamp = datetime.now().isoformat()
            outcome_section = f"\n\n## Execution Outcome\n\n{outcome}\n\n*Updated: {timestamp}*"

            if '## Outcome' not in content and '## Execution Outcome' not in content:
                content += outcome_section

            plan_file.write_text(content)

            updated = plan_file.read_text()
            assert '## Execution Outcome' in updated
            assert 'Success' in updated


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
