"""
Audit Logger - Comprehensive structured audit logging for all system actions.

Provides append-only JSON logging to /Audit/YYYY-MM-DD.json files with:
- All action types (email, invoice, tweet, etc.)
- Actor tracking (claude_code, human, system)
- Full parameter logging
- Approval status tracking
- 90-day retention cleanup
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
from filelock import FileLock

from dotenv import load_dotenv

from src.utils.logger import get_logger

load_dotenv()


class AuditLogger:
    """
    Structured audit logger for all system actions.

    Writes append-only JSON entries to daily log files in the Audit folder.
    Thread-safe using file locks to prevent corruption.
    """

    def __init__(self):
        self.logger = get_logger('AuditLogger')
        self.vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))
        self.audit_dir = self.vault_path / 'Audit'
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = 90

    def _get_today_file(self) -> Path:
        """Get the path to today's audit log file."""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.audit_dir / f'{today}.json'

    def _get_lock_file(self, audit_file: Path) -> Path:
        """Get the lock file path for an audit file."""
        return audit_file.with_suffix('.json.lock')

    def _read_audit_file(self, filepath: Path) -> dict:
        """Read an audit file, creating empty structure if needed."""
        if not filepath.exists():
            return {'entries': []}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'entries' not in data:
                    data['entries'] = []
                return data
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error reading audit file {filepath}: {e}")
            # Return empty but don't overwrite corrupted file
            return {'entries': [], '_read_error': str(e)}

    def _write_audit_file(self, filepath: Path, data: dict) -> None:
        """Write audit data to file (append-only semantics via full rewrite)."""
        # Remove any error markers before writing
        data.pop('_read_error', None)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def log_action(
        self,
        action_type: str,
        actor: str,
        target: str,
        parameters: Optional[dict] = None,
        approval_status: Optional[str] = None,
        approved_by: Optional[str] = None,
        approved_at: Optional[str] = None,
        result: str = 'pending',
        result_details: Optional[dict] = None
    ) -> dict:
        """
        Log an action to the audit trail.

        Args:
            action_type: Type of action (email_send, invoice_create, tweet_post, etc.)
            actor: Who performed the action (claude_code, human, system)
            target: Target of the action (email address, customer ID, etc.)
            parameters: Additional parameters for the action
            approval_status: Approval status (pending, approved, rejected, not_required)
            approved_by: Who approved (if applicable)
            approved_at: When approved (if applicable)
            result: Result status (pending, success, failure)
            result_details: Additional result information

        Returns:
            The logged entry dictionary
        """
        entry = {
            'timestamp': datetime.now().isoformat() + 'Z',
            'action_type': action_type,
            'actor': actor,
            'target': target,
            'parameters': parameters or {},
            'approval_status': approval_status,
            'result': result,
            'result_details': result_details or {}
        }

        # Add optional approval fields if provided
        if approved_by:
            entry['approved_by'] = approved_by
        if approved_at:
            entry['approved_at'] = approved_at

        # Get today's audit file
        audit_file = self._get_today_file()
        lock_file = self._get_lock_file(audit_file)

        try:
            # Use file lock to prevent concurrent writes
            with FileLock(lock_file, timeout=10):
                data = self._read_audit_file(audit_file)
                data['entries'].append(entry)
                self._write_audit_file(audit_file, data)

            self.logger.debug(f"Audit logged: {action_type} by {actor} -> {target}")

        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
            # Don't raise - audit logging should not break the system

        return entry

    def log_email_send(
        self,
        to: str,
        subject: str,
        actor: str = 'claude_code',
        approval_status: str = 'approved',
        result: str = 'success',
        message_id: Optional[str] = None,
        has_attachment: bool = False,
        error: Optional[str] = None
    ) -> dict:
        """Convenience method for logging email sends."""
        return self.log_action(
            action_type='email_send',
            actor=actor,
            target=to,
            parameters={
                'subject': subject,
                'has_attachment': has_attachment
            },
            approval_status=approval_status,
            result=result,
            result_details={
                'message_id': message_id,
                'error': error
            } if message_id or error else None
        )

    def log_invoice_create(
        self,
        customer_id: int,
        invoice_id: Optional[int] = None,
        amount: Optional[float] = None,
        actor: str = 'claude_code',
        approval_status: str = 'approved',
        result: str = 'success',
        error: Optional[str] = None
    ) -> dict:
        """Convenience method for logging invoice creation."""
        return self.log_action(
            action_type='invoice_create',
            actor=actor,
            target=str(customer_id),
            parameters={
                'amount': amount
            },
            approval_status=approval_status,
            result=result,
            result_details={
                'invoice_id': invoice_id,
                'error': error
            } if invoice_id or error else None
        )

    def log_tweet_post(
        self,
        content: str,
        actor: str = 'claude_code',
        approval_status: str = 'approved',
        approved_by: str = 'human',
        approved_at: Optional[str] = None,
        result: str = 'success',
        tweet_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> dict:
        """Convenience method for logging tweet posts."""
        return self.log_action(
            action_type='tweet_post',
            actor=actor,
            target='twitter',
            parameters={
                'content': content[:100] + '...' if len(content) > 100 else content,
                'character_count': len(content)
            },
            approval_status=approval_status,
            approved_by=approved_by,
            approved_at=approved_at,
            result=result,
            result_details={
                'tweet_id': tweet_id,
                'error': error
            } if tweet_id or error else None
        )

    def log_tweet(
        self,
        action: str,
        tweet_id: str,
        content: str = '',
        actor: str = 'claude_code',
        result: str = 'success',
        error: Optional[str] = None
    ) -> dict:
        """Convenience method for logging any tweet action."""
        return self.log_action(
            action_type=f'tweet_{action}',
            actor=actor,
            target=tweet_id,
            parameters={
                'content': content[:50] + '...' if len(content) > 50 else content,
            } if content else {},
            approval_status='approved' if action == 'post' else 'not_required',
            result=result,
            result_details={'error': error} if error else None
        )

    def log_file_process(
        self,
        filename: str,
        action: str,
        actor: str = 'system',
        result: str = 'success',
        details: Optional[dict] = None
    ) -> dict:
        """Convenience method for logging file processing."""
        return self.log_action(
            action_type='file_process',
            actor=actor,
            target=filename,
            parameters={'action': action},
            approval_status='not_required',
            result=result,
            result_details=details
        )

    def get_entries(
        self,
        date: Optional[str] = None,
        action_type: Optional[str] = None,
        actor: Optional[str] = None,
        result: Optional[str] = None
    ) -> list[dict]:
        """
        Get audit entries with optional filtering.

        Args:
            date: Date string (YYYY-MM-DD) or None for today
            action_type: Filter by action type
            actor: Filter by actor
            result: Filter by result status

        Returns:
            List of matching audit entries
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        audit_file = self.audit_dir / f'{date}.json'
        data = self._read_audit_file(audit_file)
        entries = data.get('entries', [])

        # Apply filters
        if action_type:
            entries = [e for e in entries if e.get('action_type') == action_type]
        if actor:
            entries = [e for e in entries if e.get('actor') == actor]
        if result:
            entries = [e for e in entries if e.get('result') == result]

        return entries

    def get_stats(self, date: Optional[str] = None) -> dict:
        """
        Get statistics for a date's audit entries.

        Args:
            date: Date string (YYYY-MM-DD) or None for today

        Returns:
            Dictionary with counts by action_type, actor, and result
        """
        entries = self.get_entries(date)

        stats = {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'total_entries': len(entries),
            'by_action_type': {},
            'by_actor': {},
            'by_result': {}
        }

        for entry in entries:
            # Count by action type
            action_type = entry.get('action_type', 'unknown')
            stats['by_action_type'][action_type] = stats['by_action_type'].get(action_type, 0) + 1

            # Count by actor
            actor = entry.get('actor', 'unknown')
            stats['by_actor'][actor] = stats['by_actor'].get(actor, 0) + 1

            # Count by result
            result = entry.get('result', 'unknown')
            stats['by_result'][result] = stats['by_result'].get(result, 0) + 1

        return stats

    def cleanup_old_logs(self) -> int:
        """
        Remove audit logs older than retention period (90 days).

        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        for filepath in self.audit_dir.glob('*.json'):
            # Skip lock files
            if filepath.suffix == '.lock':
                continue

            try:
                # Parse date from filename
                date_str = filepath.stem  # YYYY-MM-DD
                file_date = datetime.strptime(date_str, '%Y-%m-%d')

                if file_date < cutoff_date:
                    filepath.unlink()
                    # Also remove lock file if exists
                    lock_file = filepath.with_suffix('.json.lock')
                    if lock_file.exists():
                        lock_file.unlink()

                    deleted_count += 1
                    self.logger.info(f"Deleted old audit log: {filepath.name}")

            except (ValueError, OSError) as e:
                self.logger.warning(f"Could not process audit file {filepath}: {e}")

        return deleted_count


# Singleton instance for easy import
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the singleton AuditLogger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
