"""
Gmail Watcher implementation.

Monitors Gmail for unread, important messages and creates action items in the vault.
Uses Gmail API with OAuth 2.0 authentication.
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path
from datetime import datetime
import os
import pickle
import argparse

from .base_watcher import BaseWatcher
from ..utils.logger import get_logger

# Gmail API scopes - readonly for Bronze phase
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for important unread messages.

    Queries Gmail API for messages matching 'is:unread is:important' and creates
    markdown files in the vault's Needs_Action/ folder.
    """

    def __init__(self, check_interval: int = 120):
        """
        Initialize Gmail Watcher.

        Args:
            check_interval: Seconds between Gmail checks (default: 120)
        """
        # Set up logger before calling super().__init__
        self.logger = get_logger('GmailWatcher')

        super().__init__(check_interval)

        self.creds = self._get_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.processed_ids = self._load_processed_ids()

        self.logger.info(f"Gmail Watcher initialized")
        self.logger.info(f"Previously processed emails: {len(self.processed_ids)}")

    def _get_credentials(self):
        """
        Get Gmail API credentials using OAuth 2.0 flow.

        Returns:
            Valid credentials object

        Raises:
            FileNotFoundError: If credentials file not found
        """
        creds = None
        token_path = Path('credentials/token.pickle')
        creds_path = Path(os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials/gmail_credentials.json'))

        self.logger.debug(f"Credentials path: {creds_path}")
        self.logger.debug(f"Token path: {token_path}")

        # Load cached token if it exists
        if token_path.exists():
            self.logger.debug("Loading cached token...")
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

                self.logger.info("Starting OAuth flow...")
                self.logger.info("A browser window will open - please authorize the application")
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)

            # Save the credentials for next run
            self.logger.debug("Saving token...")
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.logger.info("Gmail API credentials validated")
        return creds

    def _load_processed_ids(self) -> set:
        """
        Load set of previously processed email IDs.

        Returns:
            Set of email IDs that have been processed
        """
        processed_file = self.vault_path / 'Logs' / 'processed_emails.txt'

        if processed_file.exists():
            ids = set(processed_file.read_text().splitlines())
            self.logger.debug(f"Loaded {len(ids)} processed email IDs")
            return ids

        self.logger.debug("No processed emails file found - starting fresh")
        return set()

    def _save_processed_id(self, email_id: str):
        """
        Save an email ID as processed to prevent duplicate processing.

        Args:
            email_id: Gmail message ID
        """
        processed_file = self.vault_path / 'Logs' / 'processed_emails.txt'
        processed_file.parent.mkdir(parents=True, exist_ok=True)

        with open(processed_file, 'a') as f:
            f.write(f'{email_id}\n')

        self.processed_ids.add(email_id)
        self.logger.debug(f"Saved processed ID: {email_id}")

    def check_for_updates(self) -> list:
        """
        Check Gmail for new unread, important messages.

        Returns:
            List of message dicts with 'id' and 'threadId' keys
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important'
            ).execute()

            messages = results.get('messages', [])
            self.logger.debug(f"Found {len(messages)} unread important messages")

            # Filter out already processed messages
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]
            self.logger.debug(f"Found {len(new_messages)} new messages (not yet processed)")

            return new_messages

        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    def create_action_file(self, message) -> Path:
        """
        Create a markdown action file for an email message.

        Args:
            message: Gmail message dict with 'id' key

        Returns:
            Path to created markdown file
        """
        try:
            # Get full message details
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}

            sender = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date = headers.get('Date', 'Unknown')

            # Get email snippet
            snippet = msg.get('snippet', '')

            # Create markdown content
            content = f'''---
type: email
from: {sender}
subject: {subject}
date: {date}
received: {datetime.now().isoformat()}
priority: high
status: pending
gmail_id: {message['id']}
---

## Email Content

{snippet}

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
'''

            # Create filename (use timestamp + first 8 chars of message ID)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"EMAIL_{timestamp}_{message['id'][:8]}.md"
            filepath = self.needs_action / filename

            # Write file
            filepath.write_text(content, encoding='utf-8')
            self.logger.info(f"Created action file: {filename}")

            # Mark as processed
            self._save_processed_id(message['id'])

            return filepath

        except Exception as e:
            self.logger.error(f"Error creating action file for message {message['id']}: {e}")
            raise


def create_dry_run_test_file():
    """Create a test email file without Gmail connection."""
    from dotenv import load_dotenv
    load_dotenv()

    vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))
    test_file = vault_path / 'Needs_Action' / f'TEST_EMAIL_dry_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    test_file.parent.mkdir(parents=True, exist_ok=True)

    content = f'''---
type: email
from: test@example.com
subject: Test Email (Dry Run)
date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}
received: {datetime.now().isoformat()}
priority: high
status: pending
gmail_id: dry_run_test
---

## Email Content

This is a test email created in dry-run mode. No actual Gmail connection was made.

This demonstrates the format that will be used for real emails detected by the Gmail Watcher.

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
'''

    test_file.write_text(content, encoding='utf-8')
    print(f'✓ Created test file: {test_file}')
    return test_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Gmail Watcher - Monitor Gmail for important messages'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Create test file without Gmail connection'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=120,
        help='Seconds between Gmail checks (default: 120)'
    )

    args = parser.parse_args()

    if args.dry_run:
        print('=== DRY RUN MODE ===')
        print('Creating test email file without Gmail connection...')
        create_dry_run_test_file()
        print('\nDry run complete. Check vault Needs_Action/ folder in Obsidian.')
    else:
        print('=== GMAIL WATCHER ===')
        print(f'Check interval: {args.check_interval} seconds')
        print('Starting Gmail monitoring...')
        print('Press Ctrl+C to stop')
        print()

        watcher = GmailWatcher(check_interval=args.check_interval)
        watcher.run()
