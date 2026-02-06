"""Tests for the Twitter MCP Server module."""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.mcp.twitter_mcp import (
    TwitterMCP,
    TwitterConfig,
    TwitterConnectionError,
    ScheduledTweet,
    get_twitter_mcp,
)


class TestTwitterConfig:
    """Test cases for TwitterConfig dataclass."""

    def test_config_creation(self):
        """Test TwitterConfig creation."""
        config = TwitterConfig(
            api_key='test_key',
            api_secret='test_secret',
            access_token='test_token',
            access_token_secret='test_token_secret',
            bearer_token='test_bearer'
        )

        assert config.api_key == 'test_key'
        assert config.api_secret == 'test_secret'
        assert config.access_token == 'test_token'
        assert config.access_token_secret == 'test_token_secret'
        assert config.bearer_token == 'test_bearer'


class TestScheduledTweet:
    """Test cases for ScheduledTweet dataclass."""

    def test_default_values(self):
        """Test ScheduledTweet default values."""
        tweet = ScheduledTweet(
            tweet_id='TWEET_abc123',
            content='Test tweet',
            scheduled_time=datetime.now() + timedelta(hours=1)
        )

        assert tweet.status == 'pending'
        assert tweet.posted_at is None
        assert tweet.twitter_id is None

    def test_custom_values(self):
        """Test ScheduledTweet with custom values."""
        tweet = ScheduledTweet(
            tweet_id='TWEET_abc123',
            content='Test tweet',
            scheduled_time=datetime.now(),
            status='posted',
            posted_at='2026-02-05T10:00:00',
            twitter_id='123456789'
        )

        assert tweet.status == 'posted'
        assert tweet.twitter_id == '123456789'


class TestTwitterMCPInitialization:
    """Test TwitterMCP initialization."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'access_token': 'test_token',
                'access_token_secret': 'test_token_secret',
                'bearer_token': 'test_bearer'
            }, f)
            return f.name

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Pending_Approval').mkdir()
            (vault / 'Social' / 'Twitter').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    def test_initialization_with_config(self, temp_config, temp_vault):
        """Test TwitterMCP initializes with config file."""
        mcp = TwitterMCP(config_path=temp_config)

        assert mcp.config.api_key == 'test_key'
        assert mcp._client is None  # Not connected yet

    def test_initialization_config_not_found(self, temp_vault):
        """Test TwitterMCP raises error when config not found."""
        with pytest.raises(FileNotFoundError):
            TwitterMCP(config_path='/nonexistent/path.json')


class TestTwitterMCPAuthentication:
    """Test TwitterMCP authentication."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'access_token': 'test_token',
                'access_token_secret': 'test_token_secret',
                'bearer_token': 'test_bearer'
            }, f)
            return f.name

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Pending_Approval').mkdir()
            (vault / 'Social' / 'Twitter').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def mcp(self, temp_config, temp_vault):
        """Create TwitterMCP instance."""
        return TwitterMCP(config_path=temp_config)

    def test_authenticate_success(self, mcp):
        """Test successful authentication."""
        mock_client = Mock()
        mock_user = Mock()
        mock_user.id = 12345
        mock_user.username = 'testuser'
        mock_user.name = 'Test User'
        mock_user.public_metrics = {'followers_count': 100}

        mock_response = Mock()
        mock_response.data = mock_user
        mock_client.get_me.return_value = mock_response

        with patch.object(mcp, '_get_client', return_value=mock_client):
            result = mcp.authenticate()

        assert result['success'] is True
        assert result['username'] == 'testuser'
        assert result['followers'] == 100

    def test_authenticate_failure(self, mcp):
        """Test authentication failure."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = None
        mock_client.get_me.return_value = mock_response

        with patch.object(mcp, '_get_client', return_value=mock_client):
            with pytest.raises(TwitterConnectionError):
                mcp.authenticate()


class TestTwitterMCPTweetOperations:
    """Test tweet-related operations."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'access_token': 'test_token',
                'access_token_secret': 'test_token_secret',
                'bearer_token': 'test_bearer'
            }, f)
            return f.name

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Pending_Approval').mkdir()
            (vault / 'Social' / 'Twitter').mkdir(parents=True)
            (vault / 'Audit').mkdir()
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def mcp(self, temp_config, temp_vault):
        """Create TwitterMCP instance."""
        return TwitterMCP(config_path=temp_config)

    def test_post_tweet_success(self, mcp):
        """Test posting a tweet."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = {'id': '123456789'}
        mock_client.create_tweet.return_value = mock_response

        with patch.object(mcp, '_get_client', return_value=mock_client):
            with patch.object(mcp.audit, 'log_tweet'):
                result = mcp.post_tweet('Hello, world!')

        assert result['success'] is True
        assert result['data']['tweet_id'] == '123456789'
        assert result['data']['content'] == 'Hello, world!'

    def test_post_tweet_too_long(self, mcp):
        """Test posting a tweet that's too long."""
        long_content = 'x' * 281

        result = mcp.post_tweet(long_content)

        assert result['success'] is False
        assert 'too long' in result['error']

    def test_delete_tweet(self, mcp):
        """Test deleting a tweet."""
        mock_client = Mock()
        mock_client.delete_tweet.return_value = True

        with patch.object(mcp, '_get_client', return_value=mock_client):
            with patch.object(mcp.audit, 'log_tweet'):
                result = mcp.delete_tweet('123456789')

        assert result['success'] is True

    def test_get_my_tweets(self, mcp):
        """Test getting user's tweets."""
        mock_client = Mock()
        mock_tweet = Mock()
        mock_tweet.id = '123'
        mock_tweet.text = 'Test tweet'
        mock_tweet.created_at = datetime.now()
        mock_tweet.public_metrics = {'like_count': 5, 'retweet_count': 2}

        mock_response = Mock()
        mock_response.data = [mock_tweet]
        mock_client.get_users_tweets.return_value = mock_response

        mcp._user_id = '12345'

        with patch.object(mcp, '_get_client', return_value=mock_client):
            result = mcp.get_my_tweets(count=10)

        assert result['success'] is True
        assert len(result['data']) == 1
        assert result['data'][0]['text'] == 'Test tweet'

    def test_get_engagement(self, mcp):
        """Test getting tweet engagement."""
        mock_client = Mock()
        mock_tweet = Mock()
        mock_tweet.text = 'Test tweet'
        mock_tweet.created_at = datetime.now()
        mock_tweet.public_metrics = {
            'like_count': 10,
            'retweet_count': 5,
            'reply_count': 3,
            'impression_count': 100
        }

        mock_response = Mock()
        mock_response.data = mock_tweet
        mock_client.get_tweet.return_value = mock_response

        with patch.object(mcp, '_get_client', return_value=mock_client):
            result = mcp.get_engagement('123456789')

        assert result['success'] is True
        assert result['data']['likes'] == 10
        assert result['data']['retweets'] == 5
        assert result['data']['impressions'] == 100

    def test_get_mentions(self, mcp):
        """Test getting mentions."""
        mock_client = Mock()
        mock_tweet = Mock()
        mock_tweet.id = '123'
        mock_tweet.text = '@testuser hello!'
        mock_tweet.author_id = '456'
        mock_tweet.created_at = datetime.now()

        mock_user = Mock()
        mock_user.id = '456'
        mock_user.username = 'mentioner'

        mock_response = Mock()
        mock_response.data = [mock_tweet]
        mock_response.includes = {'users': [mock_user]}
        mock_client.get_users_mentions.return_value = mock_response

        mcp._user_id = '12345'

        with patch.object(mcp, '_get_client', return_value=mock_client):
            result = mcp.get_mentions(count=10)

        assert result['success'] is True
        assert len(result['data']) == 1
        assert result['data'][0]['author_username'] == 'mentioner'


class TestTwitterMCPScheduling:
    """Test tweet scheduling operations."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'access_token': 'test_token',
                'access_token_secret': 'test_token_secret',
                'bearer_token': 'test_bearer'
            }, f)
            return f.name

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Pending_Approval').mkdir()
            (vault / 'Social' / 'Twitter').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def mcp(self, temp_config, temp_vault):
        """Create TwitterMCP instance."""
        return TwitterMCP(config_path=temp_config)

    def test_schedule_tweet(self, mcp):
        """Test scheduling a tweet."""
        future_time = datetime.now() + timedelta(hours=2)

        result = mcp.schedule_tweet('Scheduled tweet', future_time)

        assert result['success'] is True
        assert 'tweet_id' in result['data']
        assert result['data']['status'] == 'pending'

    def test_schedule_tweet_past_time(self, mcp):
        """Test scheduling a tweet in the past."""
        past_time = datetime.now() - timedelta(hours=1)

        result = mcp.schedule_tweet('Past tweet', past_time)

        assert result['success'] is False
        assert 'future' in result['error']

    def test_schedule_tweet_too_long(self, mcp):
        """Test scheduling a tweet that's too long."""
        future_time = datetime.now() + timedelta(hours=1)

        result = mcp.schedule_tweet('x' * 281, future_time)

        assert result['success'] is False
        assert 'too long' in result['error']

    def test_get_scheduled_tweets(self, mcp):
        """Test getting scheduled tweets."""
        future_time = datetime.now() + timedelta(hours=1)
        mcp.schedule_tweet('Tweet 1', future_time)
        mcp.schedule_tweet('Tweet 2', future_time + timedelta(hours=1))

        scheduled = mcp.get_scheduled_tweets()

        assert len(scheduled) == 2

    def test_cancel_scheduled_tweet(self, mcp):
        """Test cancelling a scheduled tweet."""
        future_time = datetime.now() + timedelta(hours=1)
        result = mcp.schedule_tweet('To cancel', future_time)
        tweet_id = result['data']['tweet_id']

        cancel_result = mcp.cancel_scheduled_tweet(tweet_id)

        assert cancel_result['success'] is True
        assert mcp.scheduled_tweets[tweet_id].status == 'cancelled'

    def test_cancel_nonexistent_tweet(self, mcp):
        """Test cancelling a tweet that doesn't exist."""
        result = mcp.cancel_scheduled_tweet('TWEET_nonexistent')

        assert result['success'] is False
        assert 'not found' in result['error']


class TestTwitterMCPApproval:
    """Test tweet approval workflow."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'access_token': 'test_token',
                'access_token_secret': 'test_token_secret',
                'bearer_token': 'test_bearer'
            }, f)
            return f.name

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Pending_Approval').mkdir()
            (vault / 'Social' / 'Twitter').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def mcp(self, temp_config, temp_vault):
        """Create TwitterMCP instance."""
        return TwitterMCP(config_path=temp_config)

    def test_create_tweet_approval(self, mcp, temp_vault):
        """Test creating a tweet approval request."""
        result = mcp.create_tweet_approval('Test tweet for approval')

        assert result['success'] is True
        assert 'tweet_id' in result['data']
        assert result['data']['status'] == 'pending_approval'

        # Check file was created
        filepath = Path(result['data']['filepath'])
        assert filepath.exists()

    def test_create_tweet_approval_too_long(self, mcp):
        """Test creating approval for too-long tweet."""
        result = mcp.create_tweet_approval('x' * 281)

        assert result['success'] is False
        assert 'too long' in result['error']

    def test_create_tweet_approval_with_schedule(self, mcp, temp_vault):
        """Test creating scheduled tweet approval."""
        future_time = datetime.now() + timedelta(hours=2)

        result = mcp.create_tweet_approval('Scheduled approval', scheduled_time=future_time)

        assert result['success'] is True

        # Check file contains scheduled time
        filepath = Path(result['data']['filepath'])
        content = filepath.read_text()
        assert 'Scheduled' in content


class TestTwitterMCPUtility:
    """Test utility methods."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'access_token': 'test_token',
                'access_token_secret': 'test_token_secret',
                'bearer_token': 'test_bearer'
            }, f)
            return f.name

    @pytest.fixture
    def temp_vault(self, monkeypatch):
        """Create temporary vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Pending_Approval').mkdir()
            (vault / 'Social' / 'Twitter').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            yield vault

    @pytest.fixture
    def mcp(self, temp_config, temp_vault):
        """Create TwitterMCP instance."""
        return TwitterMCP(config_path=temp_config)

    def test_test_connection(self, mcp):
        """Test connection test."""
        mock_client = Mock()
        mock_user = Mock()
        mock_user.id = 12345
        mock_user.username = 'testuser'
        mock_user.name = 'Test User'
        mock_user.public_metrics = {'followers_count': 50}

        mock_response = Mock()
        mock_response.data = mock_user
        mock_client.get_me.return_value = mock_response

        with patch.object(mcp, '_get_client', return_value=mock_client):
            result = mcp.test_connection()

        assert result['success'] is True
        assert result['username'] == 'testuser'

    def test_get_summary(self, mcp):
        """Test getting summary."""
        # Mock authenticate
        with patch.object(mcp, 'authenticate', return_value={
            'success': True,
            'username': 'testuser',
            'followers': 100
        }):
            # Mock get_my_tweets
            with patch.object(mcp, 'get_my_tweets', return_value={
                'success': True,
                'data': [
                    {'metrics': {'like_count': 5, 'retweet_count': 2, 'reply_count': 1}}
                ]
            }):
                summary = mcp.get_summary()

        assert summary['connected'] is True
        assert summary['username'] == 'testuser'
        assert summary['recent_tweets'] == 1
        assert summary['total_engagement'] == 8  # 5 + 2 + 1


class TestSingletonInstance:
    """Test singleton pattern."""

    def test_get_twitter_mcp_returns_same_instance(self, monkeypatch):
        """Test get_twitter_mcp returns singleton."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'api_key': 'test_key',
                'api_secret': 'test_secret',
                'access_token': 'test_token',
                'access_token_secret': 'test_token_secret',
                'bearer_token': 'test_bearer'
            }, f)
            config_path = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            (vault / 'Pending_Approval').mkdir()
            (vault / 'Social' / 'Twitter').mkdir(parents=True)
            monkeypatch.setenv('VAULT_PATH', str(vault))
            monkeypatch.setenv('TWITTER_CONFIG_PATH', config_path)

            # Reset singleton
            import src.mcp.twitter_mcp as twitter_module
            twitter_module._twitter_mcp = None

            mcp1 = get_twitter_mcp()
            mcp2 = get_twitter_mcp()

            assert mcp1 is mcp2
