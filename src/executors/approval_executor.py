"""
Approval Executor - Execute approved actions.

Monitors the Approved folder and executes human-approved actions.
Supports email sending through the Email MCP server.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

from ..utils.logger import get_logger
from ..utils.vault_helpers import (
    get_vault_path,
    get_vault_folder,
    read_markdown_file,
    update_frontmatter,
    move_to_folder,
    log_to_vault,
)
from ..mcp.email_mcp import EmailMCP
from ..utils.audit_logger import get_audit_logger


class ApprovalExecutor:
    """
    Approval Executor - Execute approved actions.

    Monitors the Approved folder for files moved there by the user,
    parses action details, and executes them via appropriate MCP servers.
    """

    def __init__(self):
        """Initialize Approval Executor."""
        self.logger = get_logger('ApprovalExecutor')
        self.vault_path = get_vault_path()
        self.approved = get_vault_folder('Approved')
        self.done = get_vault_folder('Done')
        self.rejected = get_vault_folder('Rejected')
        self.logs = get_vault_folder('Logs')
        self.plans = get_vault_folder('Plans')

        # Track executed actions (idempotency)
        self.executed_file = self.logs / 'executed_actions.txt'
        self.executed_ids = self._load_executed_ids()

        # Initialize MCP servers
        self._email_mcp = None  # Lazy initialization

        # Initialize audit logger
        self.audit_logger = get_audit_logger()

        self.logger.info("Approval Executor initialized")
        self.logger.info(f"Previously executed actions: {len(self.executed_ids)}")

    @property
    def email_mcp(self) -> EmailMCP:
        """Lazy initialize Email MCP server."""
        if self._email_mcp is None:
            self._email_mcp = EmailMCP()
        return self._email_mcp

    def _load_executed_ids(self) -> set:
        """
        Load set of previously executed action IDs.

        Returns:
            Set of action IDs that have been executed
        """
        if self.executed_file.exists():
            ids = set(self.executed_file.read_text().splitlines())
            self.logger.debug(f"Loaded {len(ids)} executed action IDs")
            return ids

        self.logger.debug("No executed actions file found - starting fresh")
        return set()

    def _save_executed_id(self, action_id: str):
        """
        Save an action ID as executed to prevent duplicate execution.

        Args:
            action_id: Unique action identifier
        """
        with open(self.executed_file, 'a') as f:
            f.write(f'{action_id}\n')

        self.executed_ids.add(action_id)
        self.logger.debug(f"Saved executed ID: {action_id}")

    def _parse_approval_file(self, filepath: Path) -> dict:
        """
        Parse approval file and extract action details.

        Args:
            filepath: Path to the approval file

        Returns:
            Dict with action details
        """
        try:
            metadata, body = read_markdown_file(filepath)
        except Exception as e:
            self.logger.error(f"Failed to read approval file {filepath}: {e}")
            return {'error': str(e)}

        result = {
            'action_id': metadata.get('action_id', filepath.stem),
            'action_type': metadata.get('action_type', 'unknown'),
            'plan_reference': metadata.get('plan_reference'),
            'created_at': metadata.get('created_at'),
            'expires_at': metadata.get('expires_at'),
            'filepath': filepath,
        }

        # Parse email-specific fields
        if result['action_type'] in ('email_send', 'email_reply', 'email'):
            # Try to get from frontmatter first
            result['to'] = metadata.get('to')
            result['subject'] = metadata.get('subject')
            result['reply_to_id'] = metadata.get('reply_to_id')

            # Fallback: parse from body content - look in Draft Email section first
            draft_section = re.search(r'## Draft Email\s*(.*?)(?=\n##|\Z)', body, re.DOTALL)
            search_area = draft_section.group(1) if draft_section else body

            if not result['to']:
                to_match = re.search(r'\*\*To:\*\*\s*(.+)', search_area)
                result['to'] = to_match.group(1).strip() if to_match else None

            if not result['subject']:
                subject_match = re.search(r'\*\*Subject:\*\*\s*(.+)', search_area)
                result['subject'] = subject_match.group(1).strip() if subject_match else None

            if not result['reply_to_id']:
                reply_match = re.search(r'\*\*Reply-To Message ID:\*\*\s*(.+)', body)
                result['reply_to_id'] = reply_match.group(1).strip() if reply_match else None

            # Extract email body (between ``` markers)
            body_match = re.search(r'```\n(.*?)```', search_area, re.DOTALL)
            result['body'] = body_match.group(1).strip() if body_match else None

        return result

    def _update_plan(self, plan_reference: Optional[str], outcome: str):
        """
        Update the referenced plan with execution outcome.

        Args:
            plan_reference: Path to the plan file
            outcome: Outcome description
        """
        if not plan_reference:
            return

        # Handle both relative and absolute paths
        plan_path = plan_reference.lstrip('/')
        if not plan_path.startswith(str(self.vault_path)):
            plan_path = self.vault_path / plan_path

        plan_path = Path(plan_path)

        if not plan_path.exists():
            self.logger.warning(f"Plan file not found: {plan_path}")
            return

        try:
            metadata, body = read_markdown_file(plan_path)

            # Update metadata
            metadata['status'] = 'completed'

            # Add outcome section
            timestamp = datetime.now().isoformat()
            outcome_section = f"\n\n## Execution Outcome\n\n{outcome}\n\n*Updated: {timestamp}*"

            # Check if outcome section exists
            if '## Outcome' in body or '## Execution Outcome' in body:
                # Replace existing outcome
                body = re.sub(
                    r'## (Execution )?Outcome.*$',
                    outcome_section.strip(),
                    body,
                    flags=re.DOTALL
                )
            else:
                body += outcome_section

            # Write back
            from ..utils.vault_helpers import write_markdown_file
            write_markdown_file(plan_path, metadata, body)

            self.logger.info(f"Updated plan: {plan_path.name}")

        except Exception as e:
            self.logger.error(f"Failed to update plan: {e}")

    def _log_execution(self, action: dict, result: dict):
        """
        Log execution result to daily log file.

        Args:
            action: Action details dict
            result: Execution result dict
        """
        log_file = self.logs / f"executions_{datetime.now().strftime('%Y-%m-%d')}.log"

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_id': action.get('action_id'),
            'action_type': action.get('action_type'),
            'success': result.get('success'),
            'message_id': result.get('message_id'),
            'error': result.get('error'),
        }

        with open(log_file, 'a') as f:
            f.write(f"{log_entry}\n")

        # Also log to vault
        status = "SUCCESS" if result.get('success') else "FAILED"
        log_to_vault(
            f"Executed {action.get('action_type')}: {status} - {action.get('action_id')}",
            "approval_executor"
        )

    def execute_action(self, filepath: Path) -> dict:
        """
        Execute a single approved action.

        Args:
            filepath: Path to the approved action file

        Returns:
            Dict with execution result
        """
        self.logger.info(f"Processing: {filepath.name}")

        action = self._parse_approval_file(filepath)

        if 'error' in action:
            return {'success': False, 'error': action['error']}

        # Check if already executed (idempotency)
        if action['action_id'] in self.executed_ids:
            self.logger.info(f"Skipping (already executed): {action['action_id']}")
            # Move to done anyway
            move_to_folder(filepath, 'Done')
            return {'success': True, 'skipped': True, 'reason': 'already_executed'}

        self.logger.info(f"Executing: {action['action_type']} - {action['action_id']}")

        # Execute based on action type
        if action['action_type'] in ('email_send', 'email_reply', 'email'):
            result = self._execute_email_action(action)
        else:
            result = {
                'success': False,
                'error': f"Unknown action type: {action['action_type']}"
            }

        # Log execution
        self._log_execution(action, result)

        # Update plan
        if result.get('success'):
            outcome = f"✅ **Success**\n\n- Action: {action['action_type']}\n- Message ID: {result.get('message_id', 'N/A')}"
            self._save_executed_id(action['action_id'])
            # Move to Done
            move_to_folder(filepath, 'Done')
        else:
            outcome = f"❌ **Failed**\n\n- Action: {action['action_type']}\n- Error: {result.get('error', 'Unknown error')}"
            # Keep in Approved for retry or move to Rejected
            # For now, move to Rejected on failure
            move_to_folder(filepath, 'Rejected')

        self._update_plan(action.get('plan_reference'), outcome)

        return result

    def _execute_email_action(self, action: dict) -> dict:
        """
        Execute an email send action.

        Args:
            action: Action details dict

        Returns:
            Dict with execution result
        """
        # Validate required fields
        if not action.get('to'):
            return {'success': False, 'error': 'Missing recipient (to)'}
        if not action.get('subject'):
            return {'success': False, 'error': 'Missing subject'}
        if not action.get('body'):
            return {'success': False, 'error': 'Missing email body'}

        # Check dry run mode
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

        # Send email
        result = self.email_mcp.send_email(
            to=action['to'],
            subject=action['subject'],
            body=action['body'],
            reply_to_message_id=action.get('reply_to_id'),
            dry_run=dry_run
        )

        # Audit log the email send
        self.audit_logger.log_email_send(
            to=action['to'],
            subject=action['subject'],
            actor='claude_code',
            approval_status='approved',
            result='success' if result.get('success') else 'failure',
            message_id=result.get('message_id'),
            error=result.get('error')
        )

        return result

    def get_pending_approvals(self) -> list[Path]:
        """
        Get list of files in Approved folder.

        Returns:
            List of file paths awaiting execution
        """
        return list(self.approved.glob('*.md'))

    def run_once(self) -> dict:
        """
        Single execution for cron - process approved actions, then exit.

        Returns:
            Dict with execution summary
        """
        self.logger.info("Starting check...")

        approved_files = self.get_pending_approvals()

        if not approved_files:
            self.logger.info("No approved actions to execute.")
            return {
                'processed': 0,
                'success': 0,
                'failed': 0,
            }

        self.logger.info(f"Found {len(approved_files)} approved action(s)")

        success_count = 0
        failed_count = 0

        for filepath in approved_files:
            try:
                result = self.execute_action(filepath)
                if result.get('success'):
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self.logger.error(f"Error executing {filepath.name}: {e}")
                failed_count += 1

        summary = {
            'processed': len(approved_files),
            'success': success_count,
            'failed': failed_count,
        }

        self.logger.info(f"Completed: {summary}")
        return summary


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Approval Executor - Execute approved actions'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for cron)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List pending approvals'
    )

    args = parser.parse_args()

    executor = ApprovalExecutor()

    if args.list:
        approvals = executor.get_pending_approvals()
        print(f"=== Pending Approvals: {len(approvals)} ===")
        for filepath in approvals:
            print(f"  - {filepath.name}")
    elif args.once:
        print("=== Approval Executor (Single Run) ===")
        result = executor.run_once()
        print(f"\nResult: {result}")
    else:
        print("Approval Executor")
        print("Use --once for single execution or --list to see pending approvals")
