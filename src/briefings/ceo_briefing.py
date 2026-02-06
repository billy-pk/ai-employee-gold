"""
CEO Briefing Generator - Weekly business intelligence report.

Aggregates data from all sources (Odoo, Twitter, bank data, tasks)
and generates a comprehensive briefing with insights and suggestions.
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
    list_files_in_folder,
    ensure_folder_exists,
)


@dataclass
class BriefingData:
    """Aggregated data for CEO briefing."""
    generated_at: str
    period_start: str
    period_end: str

    # Financial data (from Odoo)
    financial_available: bool = False
    total_customers: int = 0
    revenue_period: float = 0.0
    outstanding_amount: float = 0.0
    overdue_amount: float = 0.0
    draft_invoices: int = 0
    new_invoices: int = 0

    # Social data (from Twitter)
    social_available: bool = False
    twitter_followers: int = 0
    twitter_engagement: int = 0
    twitter_mentions: int = 0
    top_tweet: Optional[str] = None

    # Task data (from vault)
    tasks_completed: int = 0
    tasks_pending: int = 0
    completed_task_list: list[str] = field(default_factory=list)

    # Finance data (from bank CSVs)
    bank_data_available: bool = False
    total_expenses: float = 0.0
    subscriptions_detected: list[dict] = field(default_factory=list)
    large_transactions: list[dict] = field(default_factory=list)

    # Suggestions
    suggestions: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)

    # Week-over-week changes
    wow_revenue_change: Optional[float] = None
    wow_followers_change: Optional[int] = None
    wow_tasks_change: Optional[int] = None


class CEOBriefingGenerator:
    """
    Generates weekly CEO briefings with business intelligence.

    Features:
    - Aggregates data from multiple sources
    - Graceful degradation when sources unavailable
    - Week-over-week comparisons
    - Proactive suggestions and alerts
    """

    def __init__(self):
        """Initialize the CEO Briefing Generator."""
        self.logger = get_logger('CEOBriefing')

        # Lazy-loaded data collectors
        self._odoo = None
        self._twitter = None

        # Folders
        self.briefings_folder = get_vault_folder('Briefings')
        self.done_folder = get_vault_folder('Done')
        self.tasks_folder = get_vault_folder('Tasks')
        self.plans_folder = get_vault_folder('Plans')
        self.needs_action_folder = get_vault_folder('Needs_Action')
        self.data_folder = get_vault_folder('Data/Briefings')

        ensure_folder_exists(self.data_folder)

        self.logger.info("CEO Briefing Generator initialized")

    @property
    def odoo(self):
        """Lazy load Odoo MCP."""
        if self._odoo is None:
            try:
                from ..mcp.odoo_mcp import get_odoo_mcp
                self._odoo = get_odoo_mcp()
            except Exception as e:
                self.logger.warning(f"Odoo MCP not available: {e}")
        return self._odoo

    @property
    def twitter(self):
        """Lazy load Twitter MCP."""
        if self._twitter is None:
            try:
                from ..mcp.twitter_mcp import get_twitter_mcp
                self._twitter = get_twitter_mcp()
            except Exception as e:
                self.logger.warning(f"Twitter MCP not available: {e}")
        return self._twitter

    def collect_data(self, period_days: int = 7) -> BriefingData:
        """
        Collect data from all sources for the briefing.

        Args:
            period_days: Number of days to include in the report

        Returns:
            BriefingData with all collected information
        """
        now = datetime.now()
        period_start = now - timedelta(days=period_days)

        data = BriefingData(
            generated_at=now.isoformat(),
            period_start=period_start.strftime('%Y-%m-%d'),
            period_end=now.strftime('%Y-%m-%d')
        )

        # Collect from each source with graceful fallback
        self._collect_financial_data(data, period_days)
        self._collect_social_data(data)
        self._collect_task_data(data, period_start)
        self._collect_bank_data(data, period_start)
        self._generate_suggestions(data)
        self._compare_with_previous(data)

        return data

    def _collect_financial_data(self, data: BriefingData, period_days: int):
        """Collect financial data from Odoo."""
        if not self.odoo:
            self.logger.info("Skipping financial data - Odoo not available")
            return

        try:
            # Test connection
            conn = self.odoo.test_connection()
            if not conn.get('success'):
                self.logger.warning("Odoo connection failed")
                return

            data.financial_available = True

            # Customers
            customers = self.odoo.get_customers(limit=1000)
            if customers['success']:
                data.total_customers = len(customers['data'])

            # Invoices
            invoices = self.odoo.get_invoices(period_days=period_days, status='posted')
            if invoices['success']:
                data.new_invoices = len(invoices['data'])
                data.revenue_period = sum(
                    inv.get('amount_total', 0) for inv in invoices['data']
                )
                data.outstanding_amount = sum(
                    inv.get('amount_residual', 0) for inv in invoices['data']
                )

                # Check for overdue
                today = datetime.now().date()
                for inv in invoices['data']:
                    due_date_str = inv.get('invoice_date_due')
                    if due_date_str:
                        try:
                            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                            if due_date < today and inv.get('amount_residual', 0) > 0:
                                data.overdue_amount += inv.get('amount_residual', 0)
                        except (ValueError, TypeError):
                            pass

            # Draft invoices
            drafts = self.odoo.get_invoices(period_days=90, status='draft')
            if drafts['success']:
                data.draft_invoices = len(drafts['data'])

            self.logger.info(f"Collected financial data: ${data.revenue_period:,.2f} revenue")

        except Exception as e:
            self.logger.error(f"Error collecting financial data: {e}")

    def _collect_social_data(self, data: BriefingData):
        """Collect social media data from Twitter."""
        if not self.twitter:
            self.logger.info("Skipping social data - Twitter not available")
            return

        try:
            # Authenticate
            auth = self.twitter.authenticate()
            if not auth.get('success'):
                self.logger.warning("Twitter authentication failed")
                return

            data.social_available = True
            data.twitter_followers = auth.get('followers', 0)

            # Recent tweets
            tweets = self.twitter.get_my_tweets(count=20)
            if tweets['success']:
                for tweet in tweets['data']:
                    metrics = tweet.get('metrics', {})
                    data.twitter_engagement += (
                        metrics.get('like_count', 0) +
                        metrics.get('retweet_count', 0) +
                        metrics.get('reply_count', 0)
                    )

                # Top tweet
                if tweets['data']:
                    top = max(
                        tweets['data'],
                        key=lambda t: sum([
                            t.get('metrics', {}).get('like_count', 0),
                            t.get('metrics', {}).get('retweet_count', 0) * 2
                        ])
                    )
                    data.top_tweet = top['text'][:100]

            # Mentions
            mentions = self.twitter.get_mentions(count=50)
            if mentions['success']:
                data.twitter_mentions = len(mentions['data'])

            self.logger.info(f"Collected social data: {data.twitter_followers} followers")

        except Exception as e:
            self.logger.error(f"Error collecting social data: {e}")

    def _collect_task_data(self, data: BriefingData, period_start: datetime):
        """Collect task completion data from vault."""
        try:
            # Completed tasks (in Done folder)
            done_files = list_files_in_folder('Done', '*.md')
            for filepath in done_files:
                try:
                    stat = filepath.stat()
                    if datetime.fromtimestamp(stat.st_mtime) >= period_start:
                        data.tasks_completed += 1
                        # Get task name from file
                        metadata, body = read_markdown_file(filepath)
                        title = filepath.stem
                        if '# ' in body:
                            title = body.split('# ')[1].split('\n')[0][:50]
                        data.completed_task_list.append(title)
                except Exception:
                    continue

            # Pending tasks
            task_files = list_files_in_folder('Tasks', '*.md')
            data.tasks_pending = len(task_files)

            # Also check Needs_Action
            needs_action = list_files_in_folder('Needs_Action', '*.md')
            data.tasks_pending += len(needs_action)

            self.logger.info(f"Collected task data: {data.tasks_completed} completed, {data.tasks_pending} pending")

        except Exception as e:
            self.logger.error(f"Error collecting task data: {e}")

    def _collect_bank_data(self, data: BriefingData, period_start: datetime):
        """Collect bank/finance data from processed vault files."""
        try:
            # Look for finance action files
            finance_files = list_files_in_folder('Needs_Action', 'FINANCE_*.md')
            finance_files.extend(list_files_in_folder('Done', 'FINANCE_*.md'))

            for filepath in finance_files:
                try:
                    stat = filepath.stat()
                    if datetime.fromtimestamp(stat.st_mtime) >= period_start:
                        data.bank_data_available = True
                        metadata, body = read_markdown_file(filepath)

                        # Extract total from metadata if available
                        if 'total_amount' in metadata:
                            data.total_expenses += abs(float(metadata.get('total_amount', 0)))

                        # Look for subscriptions in body
                        if 'Subscription' in body or 'subscription' in body:
                            # Parse subscription mentions
                            lines = body.split('\n')
                            for line in lines:
                                if 'subscription' in line.lower() and '$' in line:
                                    data.subscriptions_detected.append({
                                        'description': line.strip()[:100]
                                    })

                        # Look for large transactions
                        if 'Large Transaction' in body or 'large transaction' in body:
                            lines = body.split('\n')
                            for line in lines:
                                if 'large' in line.lower() and '$' in line:
                                    data.large_transactions.append({
                                        'description': line.strip()[:100]
                                    })

                except Exception:
                    continue

            if data.bank_data_available:
                self.logger.info(f"Collected bank data: ${data.total_expenses:,.2f} expenses")

        except Exception as e:
            self.logger.error(f"Error collecting bank data: {e}")

    def _generate_suggestions(self, data: BriefingData):
        """Generate proactive suggestions based on collected data."""
        # Outstanding invoices
        if data.outstanding_amount > 0:
            data.suggestions.append(
                f"Follow up on ${data.outstanding_amount:,.2f} in outstanding invoices"
            )

        # Overdue invoices - alert
        if data.overdue_amount > 0:
            data.alerts.append(
                f"OVERDUE: ${data.overdue_amount:,.2f} past due - immediate follow-up recommended"
            )

        # Draft invoices
        if data.draft_invoices > 0:
            data.suggestions.append(
                f"Send {data.draft_invoices} draft invoice(s) waiting to be posted"
            )

        # Pending tasks
        if data.tasks_pending > 5:
            data.suggestions.append(
                f"Review {data.tasks_pending} pending tasks - consider prioritizing or delegating"
            )

        # Social engagement
        if data.social_available and data.twitter_mentions > 10:
            data.suggestions.append(
                f"High engagement: {data.twitter_mentions} mentions to respond to"
            )

        # Subscriptions review (if detected)
        if len(data.subscriptions_detected) > 3:
            data.suggestions.append(
                f"Review {len(data.subscriptions_detected)} active subscriptions for optimization"
            )

    def _compare_with_previous(self, data: BriefingData):
        """Compare with previous week's briefing data."""
        try:
            # Look for last week's data
            last_week = datetime.now() - timedelta(days=7)
            last_week_str = last_week.strftime('%Y-%m-%d')

            # Try to find previous briefing data
            prev_file = self.data_folder / f"BRIEFING_DATA_{last_week_str}.json"

            # Also check nearby dates
            for offset in range(0, 4):
                check_date = last_week - timedelta(days=offset)
                check_file = self.data_folder / f"BRIEFING_DATA_{check_date.strftime('%Y-%m-%d')}.json"
                if check_file.exists():
                    prev_file = check_file
                    break

            if prev_file.exists():
                with open(prev_file) as f:
                    prev_data = json.load(f)

                # Calculate changes
                if data.financial_available and prev_data.get('financial_available'):
                    prev_revenue = prev_data.get('revenue_period', 0)
                    if prev_revenue > 0:
                        data.wow_revenue_change = data.revenue_period - prev_revenue

                if data.social_available and prev_data.get('social_available'):
                    prev_followers = prev_data.get('twitter_followers', 0)
                    data.wow_followers_change = data.twitter_followers - prev_followers

                prev_completed = prev_data.get('tasks_completed', 0)
                data.wow_tasks_change = data.tasks_completed - prev_completed

                self.logger.info("Loaded previous week data for comparison")

        except Exception as e:
            self.logger.debug(f"No previous data for comparison: {e}")

    def generate_briefing(self, data: BriefingData) -> str:
        """
        Generate the CEO briefing markdown.

        Args:
            data: BriefingData with all collected information

        Returns:
            Formatted markdown briefing
        """
        lines = [
            f"# CEO Weekly Briefing",
            "",
            f"**Period**: {data.period_start} to {data.period_end}",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
        ]

        # Alerts section (if any)
        if data.alerts:
            lines.extend([
                "## ⚠️ Alerts",
                "",
            ])
            for alert in data.alerts:
                lines.append(f"- **{alert}**")
            lines.append("")

        # Executive Summary
        lines.extend([
            "## Executive Summary",
            "",
        ])

        summary_items = []
        if data.financial_available:
            summary_items.append(f"**Revenue**: ${data.revenue_period:,.2f}")
            if data.wow_revenue_change is not None:
                direction = "↑" if data.wow_revenue_change > 0 else "↓"
                summary_items[-1] += f" ({direction} ${abs(data.wow_revenue_change):,.2f} WoW)"

        if data.social_available:
            summary_items.append(f"**Followers**: {data.twitter_followers:,}")
            if data.wow_followers_change is not None:
                direction = "+" if data.wow_followers_change > 0 else ""
                summary_items[-1] += f" ({direction}{data.wow_followers_change} WoW)"

        summary_items.append(f"**Tasks Completed**: {data.tasks_completed}")
        if data.wow_tasks_change is not None:
            direction = "+" if data.wow_tasks_change > 0 else ""
            summary_items[-1] += f" ({direction}{data.wow_tasks_change} WoW)"

        for item in summary_items:
            lines.append(f"- {item}")
        lines.append("")

        # Financial Section
        if data.financial_available:
            lines.extend([
                "## Financial Overview",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Total Customers | {data.total_customers} |",
                f"| Revenue (Period) | ${data.revenue_period:,.2f} |",
                f"| Outstanding | ${data.outstanding_amount:,.2f} |",
                f"| Overdue | ${data.overdue_amount:,.2f} |",
                f"| New Invoices | {data.new_invoices} |",
                f"| Draft Invoices | {data.draft_invoices} |",
                "",
            ])
        else:
            lines.extend([
                "## Financial Overview",
                "",
                "*Odoo data not available*",
                "",
            ])

        # Social Section
        if data.social_available:
            lines.extend([
                "## Social Media",
                "",
                f"- **Followers**: {data.twitter_followers:,}",
                f"- **Engagement (20 tweets)**: {data.twitter_engagement:,} interactions",
                f"- **Mentions**: {data.twitter_mentions}",
                "",
            ])
            if data.top_tweet:
                lines.extend([
                    "**Top Tweet**:",
                    f"> {data.top_tweet}",
                    "",
                ])
        else:
            lines.extend([
                "## Social Media",
                "",
                "*Twitter data not available*",
                "",
            ])

        # Tasks Section
        lines.extend([
            "## Tasks & Productivity",
            "",
            f"- **Completed this period**: {data.tasks_completed}",
            f"- **Pending**: {data.tasks_pending}",
            "",
        ])

        if data.completed_task_list:
            lines.append("**Recently Completed**:")
            for task in data.completed_task_list[:10]:
                lines.append(f"- {task}")
            lines.append("")

        # Bank/Expenses Section
        if data.bank_data_available:
            lines.extend([
                "## Expenses & Subscriptions",
                "",
                f"- **Total Expenses**: ${data.total_expenses:,.2f}",
                f"- **Subscriptions Detected**: {len(data.subscriptions_detected)}",
                "",
            ])

            if data.large_transactions:
                lines.append("**Large Transactions**:")
                for tx in data.large_transactions[:5]:
                    lines.append(f"- {tx['description']}")
                lines.append("")

        # Suggestions Section
        if data.suggestions:
            lines.extend([
                "## Recommended Actions",
                "",
            ])
            for i, suggestion in enumerate(data.suggestions, 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            "*Generated by AI Employee - CEO Briefing Module*",
            "",
            f"*Data sources: "
            f"{'Odoo ✓' if data.financial_available else 'Odoo ✗'}, "
            f"{'Twitter ✓' if data.social_available else 'Twitter ✗'}, "
            f"{'Bank Data ✓' if data.bank_data_available else 'Bank Data ✗'}, "
            f"Vault ✓*"
        ])

        return '\n'.join(lines)

    def save_briefing(self, briefing: str, data: BriefingData) -> tuple[Path, Path]:
        """
        Save the briefing and its data to the vault.

        Args:
            briefing: Markdown briefing content
            data: BriefingData used to generate the briefing

        Returns:
            Tuple of (briefing_path, data_path)
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        weekday = datetime.now().strftime('%A')

        # Save briefing markdown
        briefing_filename = f"{date_str}_{weekday}_Briefing.md"
        briefing_path = self.briefings_folder / briefing_filename

        metadata = {
            'type': 'ceo_briefing',
            'date': date_str,
            'period_start': data.period_start,
            'period_end': data.period_end,
            'generated_at': data.generated_at,
        }

        write_markdown_file(briefing_path, metadata, briefing)
        self.logger.info(f"Saved briefing: {briefing_path}")

        # Save data for future comparisons
        data_filename = f"BRIEFING_DATA_{date_str}.json"
        data_path = self.data_folder / data_filename

        with open(data_path, 'w') as f:
            json.dump(asdict(data), f, indent=2, default=str)

        self.logger.info(f"Saved briefing data: {data_path}")

        return briefing_path, data_path

    def generate(self, period_days: int = 7) -> dict:
        """
        Generate a complete CEO briefing.

        Args:
            period_days: Number of days to include

        Returns:
            Dict with success status and file paths
        """
        self.logger.info(f"Generating CEO briefing for last {period_days} days")

        try:
            # Collect data
            data = self.collect_data(period_days)

            # Generate briefing
            briefing = self.generate_briefing(data)

            # Save files
            briefing_path, data_path = self.save_briefing(briefing, data)

            self.logger.info("CEO briefing generated successfully")

            return {
                'success': True,
                'briefing_path': str(briefing_path),
                'data_path': str(data_path),
                'summary': {
                    'financial_available': data.financial_available,
                    'social_available': data.social_available,
                    'tasks_completed': data.tasks_completed,
                    'alerts': len(data.alerts),
                    'suggestions': len(data.suggestions)
                }
            }

        except Exception as e:
            self.logger.error(f"Briefing generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Convenience function
def generate_ceo_briefing(period_days: int = 7) -> dict:
    """Generate a CEO briefing."""
    generator = CEOBriefingGenerator()
    return generator.generate(period_days)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='CEO Briefing Generator')
    parser.add_argument('--days', type=int, default=7, help='Period in days (default: 7)')
    parser.add_argument('--preview', action='store_true', help='Preview without saving')

    args = parser.parse_args()

    generator = CEOBriefingGenerator()

    print(f"=== Generating CEO Briefing (last {args.days} days) ===")
    print()

    if args.preview:
        data = generator.collect_data(args.days)
        briefing = generator.generate_briefing(data)
        print(briefing)
    else:
        result = generator.generate(args.days)
        if result['success']:
            print(f"Briefing saved: {result['briefing_path']}")
            print(f"Data saved: {result['data_path']}")
            print()
            print("Summary:")
            for key, value in result['summary'].items():
                print(f"  {key}: {value}")
        else:
            print(f"Error: {result['error']}")
