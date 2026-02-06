"""
Twitter MCP Server - Interact with Twitter/X via API v2.

Provides tweet posting, engagement tracking, and scheduling
with approval workflow, audit logging, and rate limit handling.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

import tweepy
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

from ..utils.logger import get_logger
from ..utils.vault_helpers import (
    get_vault_folder,
    write_markdown_file,
    read_markdown_file,
    generate_unique_id,
)
from ..utils.audit_logger import get_audit_logger


@dataclass
class TwitterConfig:
    """Twitter API configuration."""
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: str


@dataclass
class ScheduledTweet:
    """A tweet scheduled for future posting."""
    tweet_id: str
    content: str
    scheduled_time: datetime
    status: str = 'pending'  # pending, approved, posted, cancelled
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    posted_at: Optional[str] = None
    twitter_id: Optional[str] = None


class TwitterConnectionError(Exception):
    """Raised when Twitter connection fails."""
    pass


class TwitterOperationError(Exception):
    """Raised when a Twitter operation fails."""
    pass


class TwitterRateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class TwitterMCP:
    """
    Twitter MCP Server for social media operations.

    Features:
    - Post tweets (with approval workflow)
    - Get recent tweets and engagement metrics
    - Monitor mentions
    - Schedule tweets for later posting
    - Rate limit handling
    - Comprehensive audit logging
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Twitter MCP Server.

        Args:
            config_path: Path to twitter_credentials.json
        """
        self.logger = get_logger('TwitterMCP')
        self.audit = get_audit_logger()

        # Load configuration
        if config_path is None:
            config_path = os.getenv('TWITTER_CONFIG_PATH', 'credentials/twitter_credentials.json')

        self.config = self._load_config(config_path)

        # Initialize clients
        self._client = None
        self._api = None
        self._user_id = None
        self._username = None

        # Rate limit tracking
        self._rate_limit_reset = {}

        # Folders
        self.pending_folder = get_vault_folder('Pending_Approval')
        self.social_folder = get_vault_folder('Social/Twitter')
        self.scheduled_tweets: dict[str, ScheduledTweet] = {}

        self.logger.info("Twitter MCP initialized")

    def _load_config(self, config_path: str) -> TwitterConfig:
        """Load Twitter configuration from JSON file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Twitter config not found at {config_path}\n"
                f"Please create the file with api_key, api_secret, access_token, "
                f"access_token_secret, and bearer_token"
            )

        with open(path) as f:
            data = json.load(f)

        return TwitterConfig(
            api_key=data['api_key'],
            api_secret=data['api_secret'],
            access_token=data['access_token'],
            access_token_secret=data['access_token_secret'],
            bearer_token=data['bearer_token']
        )

    def _get_client(self) -> tweepy.Client:
        """Get or create Twitter API v2 client."""
        if self._client is None:
            self._client = tweepy.Client(
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_token_secret,
                bearer_token=self.config.bearer_token,
                wait_on_rate_limit=True
            )
        return self._client

    def _check_rate_limit(self, endpoint: str) -> bool:
        """Check if rate limit allows request."""
        if endpoint in self._rate_limit_reset:
            reset_time = self._rate_limit_reset[endpoint]
            if datetime.now() < reset_time:
                wait_seconds = (reset_time - datetime.now()).total_seconds()
                self.logger.warning(f"Rate limited on {endpoint}, waiting {wait_seconds:.0f}s")
                return False
        return True

    def _handle_rate_limit(self, endpoint: str, reset_time: datetime):
        """Record rate limit for endpoint."""
        self._rate_limit_reset[endpoint] = reset_time
        self.logger.warning(f"Rate limit hit for {endpoint}, resets at {reset_time}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((tweepy.TweepyException,))
    )
    def authenticate(self) -> dict:
        """
        Authenticate and get current user info.

        Returns:
            Dict with user info
        """
        try:
            client = self._get_client()
            me = client.get_me(user_fields=['public_metrics', 'created_at'])

            if me.data:
                self._user_id = me.data.id
                self._username = me.data.username
                self.logger.info(f"Authenticated as @{self._username}")
                return {
                    'success': True,
                    'user_id': str(me.data.id),
                    'username': me.data.username,
                    'name': me.data.name,
                    'followers': me.data.public_metrics.get('followers_count', 0) if me.data.public_metrics else 0
                }
            else:
                raise TwitterConnectionError("Failed to get user info")

        except tweepy.TweepyException as e:
            raise TwitterConnectionError(f"Authentication failed: {str(e)}")

    def _safe_execute(self, operation: str, func, *args, **kwargs) -> dict:
        """
        Execute with graceful error handling.

        Args:
            operation: Name of operation for logging
            func: Function to call
            *args, **kwargs: Function arguments

        Returns:
            Dict with 'success', 'data' or 'error'
        """
        try:
            result = func(*args, **kwargs)
            return {'success': True, 'data': result}
        except tweepy.TooManyRequests as e:
            self.logger.error(f"Rate limit exceeded: {e}")
            return {'success': False, 'error': 'Rate limit exceeded', 'retry_after': 900}
        except tweepy.Forbidden as e:
            self.logger.error(f"Forbidden: {e}")
            return {'success': False, 'error': f'Forbidden: {str(e)}'}
        except tweepy.TweepyException as e:
            self.logger.error(f"Twitter error: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected error in {operation}: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== Tweet Operations ====================

    def post_tweet(self, content: str, reply_to: Optional[str] = None) -> dict:
        """
        Post a tweet.

        Args:
            content: Tweet text (max 280 characters)
            reply_to: Optional tweet ID to reply to

        Returns:
            Dict with 'success', 'data' (tweet info) or 'error'
        """
        if len(content) > 280:
            return {'success': False, 'error': f'Tweet too long: {len(content)} chars (max 280)'}

        def _post():
            client = self._get_client()
            kwargs = {'text': content}
            if reply_to:
                kwargs['in_reply_to_tweet_id'] = reply_to

            response = client.create_tweet(**kwargs)
            return response.data

        result = self._safe_execute('post_tweet', _post)

        if result['success']:
            tweet_data = result['data']
            tweet_id = tweet_data['id']

            # Log to audit
            self.audit.log_tweet(
                action='post',
                tweet_id=tweet_id,
                content=content[:50],
                result='success'
            )

            # Log to posted.md
            self._log_posted_tweet(tweet_id, content)

            self.logger.info(f"Posted tweet: {tweet_id}")
            result['data'] = {
                'tweet_id': tweet_id,
                'content': content,
                'posted_at': datetime.now().isoformat()
            }

        return result

    def delete_tweet(self, tweet_id: str) -> dict:
        """
        Delete a tweet.

        Args:
            tweet_id: ID of tweet to delete

        Returns:
            Dict with 'success' or 'error'
        """
        def _delete():
            client = self._get_client()
            return client.delete_tweet(tweet_id)

        result = self._safe_execute('delete_tweet', _delete)

        if result['success']:
            self.audit.log_tweet(
                action='delete',
                tweet_id=tweet_id,
                content='',
                result='success'
            )
            self.logger.info(f"Deleted tweet: {tweet_id}")

        return result

    def get_my_tweets(self, count: int = 10) -> dict:
        """
        Get recent tweets from authenticated user.

        Args:
            count: Number of tweets to retrieve (max 100)

        Returns:
            Dict with 'success', 'data' (list of tweets) or 'error'
        """
        count = min(count, 100)

        def _get_tweets():
            client = self._get_client()
            if not self._user_id:
                self.authenticate()

            response = client.get_users_tweets(
                id=self._user_id,
                max_results=count,
                tweet_fields=['created_at', 'public_metrics', 'text']
            )
            return response.data if response.data else []

        result = self._safe_execute('get_my_tweets', _get_tweets)

        if result['success']:
            tweets = []
            for tweet in result['data']:
                tweets.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'metrics': tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                })
            result['data'] = tweets
            self.logger.info(f"Retrieved {len(tweets)} tweets")

        return result

    def get_engagement(self, tweet_id: str) -> dict:
        """
        Get engagement metrics for a tweet.

        Args:
            tweet_id: Tweet ID

        Returns:
            Dict with 'success', 'data' (metrics) or 'error'
        """
        def _get_metrics():
            client = self._get_client()
            response = client.get_tweet(
                tweet_id,
                tweet_fields=['public_metrics', 'created_at', 'text']
            )
            return response.data

        result = self._safe_execute('get_engagement', _get_metrics)

        if result['success'] and result['data']:
            tweet = result['data']
            metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
            result['data'] = {
                'tweet_id': tweet_id,
                'text': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
                'likes': metrics.get('like_count', 0),
                'retweets': metrics.get('retweet_count', 0),
                'replies': metrics.get('reply_count', 0),
                'impressions': metrics.get('impression_count', 0),
                'created_at': tweet.created_at.isoformat() if tweet.created_at else None
            }
            self.logger.info(f"Got metrics for tweet {tweet_id}: {metrics.get('like_count', 0)} likes")

        return result

    def get_mentions(self, count: int = 20) -> dict:
        """
        Get recent mentions of authenticated user.

        Args:
            count: Number of mentions to retrieve

        Returns:
            Dict with 'success', 'data' (list of mentions) or 'error'
        """
        count = min(count, 100)

        def _get_mentions():
            client = self._get_client()
            if not self._user_id:
                self.authenticate()

            response = client.get_users_mentions(
                id=self._user_id,
                max_results=count,
                tweet_fields=['created_at', 'author_id', 'text'],
                expansions=['author_id']
            )
            return {
                'tweets': response.data if response.data else [],
                'users': {u.id: u for u in response.includes.get('users', [])} if response.includes else {}
            }

        result = self._safe_execute('get_mentions', _get_mentions)

        if result['success']:
            data = result['data']
            mentions = []
            for tweet in data['tweets']:
                author = data['users'].get(tweet.author_id, None)
                mentions.append({
                    'id': tweet.id,
                    'text': tweet.text,
                    'author_id': tweet.author_id,
                    'author_username': author.username if author else 'unknown',
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None
                })
            result['data'] = mentions
            self.logger.info(f"Retrieved {len(mentions)} mentions")

        return result

    # ==================== Scheduling ====================

    def schedule_tweet(self, content: str, scheduled_time: datetime) -> dict:
        """
        Schedule a tweet for later posting.

        Args:
            content: Tweet text
            scheduled_time: When to post

        Returns:
            Dict with 'success', 'data' (schedule info) or 'error'
        """
        if len(content) > 280:
            return {'success': False, 'error': f'Tweet too long: {len(content)} chars'}

        if scheduled_time <= datetime.now():
            return {'success': False, 'error': 'Scheduled time must be in the future'}

        tweet_id = generate_unique_id('TWEET')

        scheduled = ScheduledTweet(
            tweet_id=tweet_id,
            content=content,
            scheduled_time=scheduled_time
        )

        self.scheduled_tweets[tweet_id] = scheduled

        # Save to scheduled_posts.md
        self._update_scheduled_posts()

        self.logger.info(f"Scheduled tweet {tweet_id} for {scheduled_time}")

        return {
            'success': True,
            'data': {
                'tweet_id': tweet_id,
                'content': content,
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'pending'
            }
        }

    def get_scheduled_tweets(self) -> list[ScheduledTweet]:
        """Get all scheduled tweets."""
        return list(self.scheduled_tweets.values())

    def cancel_scheduled_tweet(self, tweet_id: str) -> dict:
        """Cancel a scheduled tweet."""
        if tweet_id not in self.scheduled_tweets:
            return {'success': False, 'error': f'Tweet {tweet_id} not found'}

        self.scheduled_tweets[tweet_id].status = 'cancelled'
        self._update_scheduled_posts()

        return {'success': True, 'data': {'tweet_id': tweet_id, 'status': 'cancelled'}}

    def process_scheduled_tweets(self) -> list[dict]:
        """
        Process any scheduled tweets that are due.

        Returns:
            List of results for processed tweets
        """
        results = []
        now = datetime.now()

        for tweet_id, scheduled in list(self.scheduled_tweets.items()):
            if scheduled.status == 'approved' and scheduled.scheduled_time <= now:
                result = self.post_tweet(scheduled.content)
                if result['success']:
                    scheduled.status = 'posted'
                    scheduled.posted_at = datetime.now().isoformat()
                    scheduled.twitter_id = result['data']['tweet_id']
                else:
                    scheduled.status = 'failed'

                results.append({
                    'tweet_id': tweet_id,
                    'result': result
                })

        self._update_scheduled_posts()
        return results

    # ==================== Approval Workflow ====================

    def create_tweet_approval(self, content: str, scheduled_time: Optional[datetime] = None) -> dict:
        """
        Create a tweet approval request.

        Args:
            content: Tweet text
            scheduled_time: Optional scheduled time

        Returns:
            Dict with approval file info
        """
        if len(content) > 280:
            return {'success': False, 'error': f'Tweet too long: {len(content)} chars'}

        tweet_id = generate_unique_id('TWEET')

        metadata = {
            'type': 'tweet_approval',
            'tweet_id': tweet_id,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'character_count': len(content),
        }

        if scheduled_time:
            metadata['scheduled_time'] = scheduled_time.isoformat()

        body = f"""# Tweet Approval Request

## Content

{content}

## Details

- **Characters**: {len(content)}/280
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{f"- **Scheduled**: {scheduled_time.strftime('%Y-%m-%d %H:%M')}" if scheduled_time else "- **Post immediately upon approval**"}

## Instructions

To approve this tweet:
1. Review the content above
2. Move this file to `Approved/` folder

To reject:
1. Move this file to `Done/` folder
2. Or delete the file

---
*Generated by Twitter MCP*
"""

        filepath = self.pending_folder / f"TWEET_{tweet_id}.md"
        write_markdown_file(filepath, metadata, body)

        self.logger.info(f"Created tweet approval request: {tweet_id}")

        return {
            'success': True,
            'data': {
                'tweet_id': tweet_id,
                'filepath': str(filepath),
                'content': content,
                'status': 'pending_approval'
            }
        }

    # ==================== Utility Methods ====================

    def _log_posted_tweet(self, tweet_id: str, content: str):
        """Log a posted tweet to posted.md."""
        posted_file = self.social_folder / 'posted.md'

        entry = f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        entry += f"**Tweet ID**: {tweet_id}\n\n"
        entry += f"> {content}\n\n"
        entry += "---\n"

        if posted_file.exists():
            current = posted_file.read_text()
            # Insert after header
            if '# Posted Tweets' in current:
                parts = current.split('# Posted Tweets', 1)
                new_content = parts[0] + '# Posted Tweets' + entry + parts[1].lstrip()
            else:
                new_content = current + entry
        else:
            new_content = "# Posted Tweets\n" + entry

        posted_file.write_text(new_content)

    def _update_scheduled_posts(self):
        """Update scheduled_posts.md with current schedule."""
        scheduled_file = self.social_folder / 'scheduled_posts.md'

        lines = [
            "# Scheduled Tweets",
            "",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
            "",
        ]

        pending = [s for s in self.scheduled_tweets.values() if s.status in ('pending', 'approved')]
        if pending:
            lines.extend([
                "## Upcoming",
                "",
                "| ID | Scheduled | Status | Preview |",
                "|-----|-----------|--------|---------|",
            ])
            for tweet in sorted(pending, key=lambda x: x.scheduled_time):
                preview = tweet.content[:30] + '...' if len(tweet.content) > 30 else tweet.content
                lines.append(
                    f"| {tweet.tweet_id} | {tweet.scheduled_time.strftime('%Y-%m-%d %H:%M')} | "
                    f"{tweet.status} | {preview} |"
                )
            lines.append("")

        posted = [s for s in self.scheduled_tweets.values() if s.status == 'posted']
        if posted:
            lines.extend([
                "## Recently Posted",
                "",
            ])
            for tweet in sorted(posted, key=lambda x: x.posted_at or '', reverse=True)[:5]:
                lines.append(f"- {tweet.tweet_id}: Posted at {tweet.posted_at}")
            lines.append("")

        scheduled_file.write_text('\n'.join(lines))

    def test_connection(self) -> dict:
        """Test connection to Twitter API."""
        return self.authenticate()

    def get_summary(self) -> dict:
        """
        Get a summary of Twitter activity.

        Returns:
            Dict with account stats
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'connected': False,
            'username': None,
            'recent_tweets': 0,
            'total_engagement': 0,
            'pending_scheduled': 0,
        }

        # Authenticate
        auth = self.authenticate()
        if auth['success']:
            summary['connected'] = True
            summary['username'] = auth['username']
            summary['followers'] = auth.get('followers', 0)

        # Recent tweets
        tweets = self.get_my_tweets(count=10)
        if tweets['success']:
            summary['recent_tweets'] = len(tweets['data'])
            for tweet in tweets['data']:
                metrics = tweet.get('metrics', {})
                summary['total_engagement'] += (
                    metrics.get('like_count', 0) +
                    metrics.get('retweet_count', 0) +
                    metrics.get('reply_count', 0)
                )

        # Scheduled tweets
        summary['pending_scheduled'] = len([
            s for s in self.scheduled_tweets.values()
            if s.status in ('pending', 'approved')
        ])

        return summary


# Singleton instance
_twitter_mcp: Optional[TwitterMCP] = None


def get_twitter_mcp() -> TwitterMCP:
    """Get the singleton TwitterMCP instance."""
    global _twitter_mcp
    if _twitter_mcp is None:
        _twitter_mcp = TwitterMCP()
    return _twitter_mcp


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Twitter MCP Server')
    parser.add_argument('--test', action='store_true', help='Test connection')
    parser.add_argument('--summary', action='store_true', help='Show summary')
    parser.add_argument('--tweets', action='store_true', help='List recent tweets')
    parser.add_argument('--mentions', action='store_true', help='List recent mentions')
    parser.add_argument('--post', metavar='TEXT', help='Post a tweet (for testing)')

    args = parser.parse_args()

    mcp = TwitterMCP()

    if args.test:
        print("=== Twitter Connection Test ===")
        result = mcp.test_connection()
        if result['success']:
            print(f"Connected as @{result['username']}")
            print(f"Followers: {result.get('followers', 'N/A')}")
        else:
            print(f"Connection failed: {result.get('error')}")

    elif args.summary:
        print("=== Twitter Summary ===")
        summary = mcp.get_summary()
        print(f"Connected: {summary['connected']}")
        print(f"Username: @{summary.get('username', 'N/A')}")
        print(f"Followers: {summary.get('followers', 'N/A')}")
        print(f"Recent tweets: {summary['recent_tweets']}")
        print(f"Total engagement: {summary['total_engagement']}")
        print(f"Scheduled: {summary['pending_scheduled']}")

    elif args.tweets:
        print("=== Recent Tweets ===")
        result = mcp.get_my_tweets(count=5)
        if result['success']:
            for tweet in result['data']:
                print(f"\n{tweet['id']}:")
                print(f"  {tweet['text'][:60]}...")
                metrics = tweet.get('metrics', {})
                print(f"  Likes: {metrics.get('like_count', 0)}, "
                      f"RTs: {metrics.get('retweet_count', 0)}")
        else:
            print(f"Error: {result['error']}")

    elif args.mentions:
        print("=== Recent Mentions ===")
        result = mcp.get_mentions(count=5)
        if result['success']:
            for mention in result['data']:
                print(f"\n@{mention['author_username']}:")
                print(f"  {mention['text'][:60]}...")
        else:
            print(f"Error: {result['error']}")

    elif args.post:
        print(f"Posting: {args.post}")
        result = mcp.post_tweet(args.post)
        if result['success']:
            print(f"Posted! Tweet ID: {result['data']['tweet_id']}")
        else:
            print(f"Error: {result['error']}")

    else:
        print("Twitter MCP Server")
        print("Use --test, --summary, --tweets, --mentions, or --post")
