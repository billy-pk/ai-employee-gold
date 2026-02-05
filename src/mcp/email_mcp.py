"""
Email MCP Server - Send emails via Gmail API.

Provides email sending capabilities with rate limiting,
logging, and support for replies (threading).
"""

import os
import base64
import json
import pickle
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email_validator import validate_email, EmailNotValidError
from tenacity import retry, stop_after_attempt, wait_exponential

from dotenv import load_dotenv

load_dotenv()

from ..utils.logger import get_logger
from ..utils.vault_helpers import get_vault_folder


# Gmail API scopes - includes send capability
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]


class EmailMCP:
    """
    Email MCP Server for sending emails via Gmail API.

    Features:
    - Send new emails
    - Reply to existing emails (in-thread)
    - Rate limiting (configurable)
    - Comprehensive logging
    - Email validation
    """

    def __init__(self, max_emails_per_hour: int = 10):
        """
        Initialize Email MCP Server.

        Args:
            max_emails_per_hour: Maximum emails allowed per hour (default: 10)
        """
        self.logger = get_logger('EmailMCP')
        self.vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))
        self.logs = get_vault_folder('Logs')

        # Rate limiting
        self.max_emails_per_hour = max_emails_per_hour
        self.sent_log_file = self.logs / 'email_sends.json'

        # Initialize Gmail API
        self.creds = self._get_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)

        self.logger.info("Email MCP initialized")
        self.logger.info(f"Rate limit: {max_emails_per_hour} emails/hour")

    def _get_credentials(self):
        """
        Get Gmail API credentials with send scope.

        Returns:
            Valid credentials object

        Raises:
            FileNotFoundError: If credentials file not found
        """
        creds = None
        # Use separate token file for send-capable credentials
        token_path = Path('credentials/token_send.pickle')
        creds_path = Path(os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials/gmail_credentials.json'))

        self.logger.debug(f"Credentials path: {creds_path}")
        self.logger.debug(f"Token path: {token_path}")

        # Load cached token if it exists
        if token_path.exists():
            self.logger.debug("Loading cached send token...")
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired token...")
                creds.refresh(Request())
            else:
                if not creds_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials not found at {creds_path}\n"
                        f"Please follow setup instructions in credentials/README.md"
                    )

                self.logger.info("Starting OAuth flow for email sending...")
                self.logger.info("A browser window will open - please authorize the application")
                self.logger.info("Make sure to grant EMAIL SENDING permission!")
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for next run
            self.logger.debug("Saving send token...")
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.logger.info("Gmail API credentials (with send) validated")
        return creds

    def _check_rate_limit(self) -> tuple[bool, int]:
        """
        Check if we're within rate limits.

        Returns:
            Tuple of (is_allowed, emails_sent_this_hour)
        """
        if not self.sent_log_file.exists():
            return True, 0

        try:
            sends = json.loads(self.sent_log_file.read_text())
            one_hour_ago = datetime.now().timestamp() - 3600
            recent_sends = [s for s in sends if s.get('timestamp', 0) > one_hour_ago]
            count = len(recent_sends)
            return count < self.max_emails_per_hour, count
        except Exception as e:
            self.logger.warning(f"Error reading send log: {e}")
            return True, 0

    def _log_send(
        self,
        to: str,
        subject: str,
        success: bool,
        message_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Log email send attempt.

        Args:
            to: Recipient email
            subject: Email subject
            success: Whether send was successful
            message_id: Gmail message ID if successful
            error: Error message if failed
        """
        sends = []
        if self.sent_log_file.exists():
            try:
                sends = json.loads(self.sent_log_file.read_text())
            except Exception:
                sends = []

        sends.append({
            'timestamp': datetime.now().timestamp(),
            'datetime': datetime.now().isoformat(),
            'to': to,
            'subject': subject,
            'success': success,
            'message_id': message_id,
            'error': error,
        })

        # Keep only last 100 entries
        sends = sends[-100:]
        self.sent_log_file.write_text(json.dumps(sends, indent=2))

        # Also log to vault log
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Email {status}: To={to}, Subject={subject[:50]}...")

    def _validate_email(self, email: str) -> tuple[bool, str]:
        """
        Validate an email address.

        Args:
            email: Email address to validate

        Returns:
            Tuple of (is_valid, normalized_email_or_error)
        """
        try:
            result = validate_email(email, check_deliverability=False)
            return True, result.normalized
        except EmailNotValidError as e:
            return False, str(e)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _send_message(self, message_body: dict) -> dict:
        """
        Send message with retry logic.

        Args:
            message_body: Gmail API message body

        Returns:
            Gmail API response
        """
        return self.service.users().messages().send(
            userId='me',
            body=message_body
        ).execute()

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_message_id: Optional[str] = None,
        dry_run: bool = False
    ) -> dict:
        """
        Send an email via Gmail API.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            reply_to_message_id: If replying, the original message ID
            dry_run: If True, validate but don't send

        Returns:
            Dict with 'success', 'message_id' or 'error'
        """
        self.logger.info(f"Send request: to={to}, subject={subject[:50]}...")

        # Validate email
        is_valid, result = self._validate_email(to)
        if not is_valid:
            error = f"Invalid email address: {result}"
            self.logger.error(error)
            self._log_send(to, subject, False, error=error)
            return {'success': False, 'error': error}

        normalized_email = result

        # Check rate limit
        is_allowed, sent_count = self._check_rate_limit()
        if not is_allowed:
            error = f"Rate limit exceeded ({sent_count}/{self.max_emails_per_hour} emails/hour)"
            self.logger.error(error)
            self._log_send(to, subject, False, error=error)
            return {'success': False, 'error': error}

        # Dry run mode
        if dry_run:
            self.logger.info("DRY RUN - email would be sent")
            return {
                'success': True,
                'dry_run': True,
                'message': f"Would send to {normalized_email}: {subject}"
            }

        try:
            # Create message
            message = MIMEText(body)
            message['to'] = normalized_email
            message['subject'] = subject

            # Handle threading for replies
            thread_id = None
            if reply_to_message_id:
                try:
                    # Get original message for threading
                    original = self.service.users().messages().get(
                        userId='me',
                        id=reply_to_message_id,
                        format='metadata',
                        metadataHeaders=['Message-ID', 'References', 'Subject']
                    ).execute()

                    headers = {h['name']: h['value'] for h in original.get('payload', {}).get('headers', [])}

                    if 'Message-ID' in headers:
                        message['In-Reply-To'] = headers['Message-ID']
                        refs = headers.get('References', '')
                        message['References'] = f"{refs} {headers['Message-ID']}".strip()

                    thread_id = original.get('threadId')
                    self.logger.debug(f"Replying to thread: {thread_id}")

                except Exception as e:
                    self.logger.warning(f"Could not get original message for threading: {e}")

            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Build send body
            send_body = {'raw': raw}
            if thread_id:
                send_body['threadId'] = thread_id

            # Send with retry
            result = self._send_message(send_body)

            message_id = result.get('id')
            self.logger.info(f"Email sent successfully: {message_id}")
            self._log_send(normalized_email, subject, True, message_id=message_id)

            return {'success': True, 'message_id': message_id}

        except Exception as e:
            error = str(e)
            self.logger.error(f"Failed to send email: {error}")
            self._log_send(to, subject, False, error=error)
            return {'success': False, 'error': error}

    def get_rate_limit_status(self) -> dict:
        """
        Get current rate limit status.

        Returns:
            Dict with rate limit information
        """
        is_allowed, sent_count = self._check_rate_limit()
        return {
            'emails_sent_this_hour': sent_count,
            'max_emails_per_hour': self.max_emails_per_hour,
            'remaining': self.max_emails_per_hour - sent_count,
            'can_send': is_allowed
        }


def test_email_mcp():
    """Test the Email MCP server."""
    print("=== Email MCP Test ===\n")

    mcp = EmailMCP()

    # Check rate limit status
    status = mcp.get_rate_limit_status()
    print(f"Rate Limit Status:")
    print(f"  Sent this hour: {status['emails_sent_this_hour']}")
    print(f"  Remaining: {status['remaining']}")
    print(f"  Can send: {status['can_send']}")
    print()

    # Dry run test
    result = mcp.send_email(
        to="test@example.com",
        subject="Test Email from AI Employee",
        body="This is a test email.",
        dry_run=True
    )
    print(f"Dry run result: {result}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Email MCP Server')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--status', action='store_true', help='Show rate limit status')

    args = parser.parse_args()

    if args.test:
        test_email_mcp()
    elif args.status:
        mcp = EmailMCP()
        status = mcp.get_rate_limit_status()
        print(f"Emails sent this hour: {status['emails_sent_this_hour']}/{status['max_emails_per_hour']}")
        print(f"Remaining: {status['remaining']}")
        print(f"Can send: {'Yes' if status['can_send'] else 'No'}")
    else:
        print("Email MCP Server")
        print("Use --test for test mode or --status for rate limit info")
