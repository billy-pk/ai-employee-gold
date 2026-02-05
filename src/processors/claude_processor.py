"""
Claude Processor - Trigger Claude Code for item processing.

Implements SMART TRIGGERING to optimize Claude usage quota:
- Checks if items exist before invoking Claude
- If no items: exits immediately (no quota used)
- If items exist: invokes Claude for processing

This design allows frequent cron scheduling (every 5 minutes)
without wasting Claude quota on empty checks.
"""

import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from ..utils.logger import get_logger
from ..utils.vault_helpers import (
    get_vault_path,
    get_vault_folder,
    get_pending_items,
    read_markdown_file,
    log_to_vault,
)


class ClaudeProcessor:
    """
    Claude Processor with Smart Triggering.

    Invokes Claude Code to process items in Needs_Action folder.
    Only calls Claude when there are actual items to process,
    saving quota for when it's needed.
    """

    def __init__(self, model: str = "sonnet", timeout: int = 300):
        """
        Initialize Claude Processor.

        Args:
            model: Claude model to use (sonnet/opus). Default: sonnet for efficiency
            timeout: Timeout in seconds for Claude invocation (default: 300 = 5 min)
        """
        self.logger = get_logger('ClaudeProcessor')
        self.vault_path = get_vault_path()
        self.needs_action = get_vault_folder('Needs_Action')
        self.logs = get_vault_folder('Logs')
        self.plans = get_vault_folder('Plans')

        self.model = model
        self.timeout = timeout
        self.usage_log = self.logs / 'claude_usage.json'

        self.logger.info("Claude Processor initialized")
        self.logger.info(f"Model: {model}, Timeout: {timeout}s")

    def _get_pending_items(self) -> list[Path]:
        """
        Get list of unprocessed items in Needs_Action.

        Returns:
            List of file paths with status: pending
        """
        return get_pending_items('Needs_Action')

    def _log_usage(
        self,
        invoked: bool,
        items_count: int,
        result: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ):
        """
        Log Claude usage for tracking.

        Args:
            invoked: Whether Claude was actually invoked
            items_count: Number of items to process
            result: Result status (success/error/skipped)
            duration_seconds: How long the invocation took
        """
        usage_data = []
        if self.usage_log.exists():
            try:
                usage_data = json.loads(self.usage_log.read_text())
            except Exception:
                usage_data = []

        entry = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'invoked': invoked,
            'items_count': items_count,
            'result': result,
            'model': self.model if invoked else None,
            'duration_seconds': duration_seconds,
        }

        usage_data.append(entry)

        # Keep only last 1000 entries
        usage_data = usage_data[-1000:]
        self.usage_log.write_text(json.dumps(usage_data, indent=2))

        # Also log to vault
        if invoked:
            log_to_vault(f"Claude invoked: {items_count} items, result={result}", "claude_processor")
        else:
            log_to_vault(f"Claude skipped: no pending items", "claude_processor")

    def _build_prompt(self, items: list[Path]) -> str:
        """
        Build the prompt for Claude Code.

        Args:
            items: List of item file paths to process

        Returns:
            Prompt string
        """
        item_list = "\n".join(f"- {item.name}" for item in items)

        prompt = f"""Process the following items from /Needs_Action/ folder:

{item_list}

For EACH item:

1. Read the item file content
2. Read /Company_Handbook.md for processing rules
3. Analyze the content and determine:
   - Priority level (High/Normal/Low)
   - Required actions
   - Whether an email response is needed

4. Create a Plan file in /Plans/ folder with:
   - Your analysis and reasoning
   - List of proposed actions
   - Set action_required: true if email needs to be sent

5. If email action is needed:
   - Create an approval request in /Pending_Approval/
   - Include the draft email content
   - Reference the Plan file

6. Update /Dashboard.md with:
   - Increment processed count
   - Add recent activity entry
   - Update last processed timestamp

7. Mark the item as processed by changing its frontmatter from status: pending to status: processed

Be concise but thorough. Explain your reasoning in the Plan file.
"""
        return prompt

    def _invoke_claude(self, items: list[Path]) -> dict:
        """
        Invoke Claude Code to process items.

        Args:
            items: List of item file paths

        Returns:
            Dict with 'success', 'stdout', 'stderr' or 'error'
        """
        prompt = self._build_prompt(items)

        # Build command
        cmd = [
            'claude',
            '-p', prompt,
            '--model', self.model,
            '--allowedTools', 'Read', 'Edit', 'Write', 'Bash(ls:*)',
            '--print'
        ]

        self.logger.info(f"Invoking Claude ({self.model}) for {len(items)} items...")
        start_time = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            duration = (datetime.now() - start_time).total_seconds()

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'duration': duration,
            }

        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                'success': False,
                'error': f'Claude invocation timed out after {self.timeout} seconds',
                'duration': duration,
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'Claude CLI not found. Is claude-code installed?',
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def get_usage_stats(self, date: Optional[str] = None) -> dict:
        """
        Get usage statistics for a given date.

        Args:
            date: Date string (YYYY-MM-DD). Default: today

        Returns:
            Dict with usage statistics
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        if not self.usage_log.exists():
            return {
                'date': date,
                'invocations': 0,
                'items_processed': 0,
                'skipped_checks': 0,
                'errors': 0,
            }

        try:
            usage_data = json.loads(self.usage_log.read_text())
            day_data = [e for e in usage_data if e.get('date') == date]

            return {
                'date': date,
                'invocations': sum(1 for e in day_data if e.get('invoked')),
                'items_processed': sum(e.get('items_count', 0) for e in day_data if e.get('invoked')),
                'skipped_checks': sum(1 for e in day_data if not e.get('invoked')),
                'errors': sum(1 for e in day_data if e.get('result', '').startswith('error')),
            }
        except Exception:
            return {
                'date': date,
                'invocations': 0,
                'items_processed': 0,
                'skipped_checks': 0,
                'errors': 0,
            }

    def run_once(self) -> dict:
        """
        Single execution for cron - process items if any exist.

        This implements SMART TRIGGERING:
        - If no items: exit immediately (no Claude call, no quota used)
        - If items exist: invoke Claude for processing

        Returns:
            Dict with execution results
        """
        self.logger.info("Starting check...")

        # SMART TRIGGERING: Check if there are items to process
        items = self._get_pending_items()

        if not items:
            # NO ITEMS - Exit without invoking Claude (saves quota!)
            self.logger.info("No pending items. Skipping Claude invocation.")
            self._log_usage(invoked=False, items_count=0, result='skipped_no_items')
            return {
                'invoked': False,
                'reason': 'no_pending_items',
                'items_count': 0,
            }

        # ITEMS EXIST - Invoke Claude
        self.logger.info(f"Found {len(items)} pending items. Invoking Claude...")

        result = self._invoke_claude(items)

        if result['success']:
            self.logger.info(f"Successfully processed {len(items)} items.")
            self._log_usage(
                invoked=True,
                items_count=len(items),
                result='success',
                duration_seconds=result.get('duration')
            )
            return {
                'invoked': True,
                'success': True,
                'items_count': len(items),
                'duration': result.get('duration'),
            }
        else:
            error = result.get('error') or result.get('stderr', 'Unknown error')
            self.logger.error(f"Error: {error}")
            self._log_usage(
                invoked=True,
                items_count=len(items),
                result=f'error: {error[:100]}',
                duration_seconds=result.get('duration')
            )
            return {
                'invoked': True,
                'success': False,
                'items_count': len(items),
                'error': error,
                'duration': result.get('duration'),
            }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Claude Processor - Process items with smart triggering'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for cron)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show usage statistics for today'
    )
    parser.add_argument(
        '--model',
        default='sonnet',
        choices=['sonnet', 'opus'],
        help='Claude model to use (default: sonnet)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Check for items but do not invoke Claude'
    )

    args = parser.parse_args()

    processor = ClaudeProcessor(model=args.model)

    if args.stats:
        stats = processor.get_usage_stats()
        print(f"=== Claude Usage Stats ({stats['date']}) ===")
        print(f"Invocations: {stats['invocations']}")
        print(f"Items processed: {stats['items_processed']}")
        print(f"Skipped checks: {stats['skipped_checks']}")
        print(f"Errors: {stats['errors']}")
    elif args.dry_run:
        items = processor._get_pending_items()
        print(f"=== Dry Run ===")
        print(f"Pending items: {len(items)}")
        for item in items:
            print(f"  - {item.name}")
        if items:
            print("\nWould invoke Claude to process these items.")
        else:
            print("\nNo items to process. Claude would NOT be invoked.")
    elif args.once:
        print("=== Claude Processor (Single Run) ===")
        result = processor.run_once()
        print(f"\nResult: {result}")
    else:
        print("Claude Processor")
        print("Use --once for single execution, --stats for usage stats, or --dry-run to check items")
