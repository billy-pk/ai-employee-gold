"""
File System Watcher implementation.

Monitors the Inbox folder for new files and creates action items in the vault.
Uses file hash tracking to prevent duplicate processing.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime

from .base_watcher import BaseWatcher
from ..utils.logger import get_logger
from ..utils.vault_helpers import generate_unique_id, safe_filename


class FileSystemWatcher(BaseWatcher):
    """
    Watches Inbox folder for new files.

    Scans the Inbox folder for new files and creates metadata markdown files
    in the Needs_Action folder. Uses file hashing to prevent duplicate processing.
    """

    # File extensions that can have text previews
    TEXT_EXTENSIONS = {'.txt', '.md', '.csv', '.json', '.xml', '.html', '.py', '.js', '.ts', '.yaml', '.yml', '.log'}
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'}
    DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}

    def __init__(self, check_interval: int = 60):
        """
        Initialize File System Watcher.

        Args:
            check_interval: Seconds between checks (default: 60)
        """
        self.logger = get_logger('FileSystemWatcher')
        super().__init__(check_interval)

        self.inbox = self.vault_path / 'Inbox'
        self.logs = self.vault_path / 'Logs'

        # Ensure directories exist
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

        # Track processed files
        self.processed_hashes_file = self.logs / 'processed_files.txt'
        self.processed_hashes = self._load_processed_hashes()

        self.logger.info("File System Watcher initialized")
        self.logger.info(f"Watching folder: {self.inbox}")
        self.logger.info(f"Previously processed files: {len(self.processed_hashes)}")

    def _load_processed_hashes(self) -> set:
        """
        Load set of previously processed file hashes.

        Returns:
            Set of file hashes that have been processed
        """
        if self.processed_hashes_file.exists():
            hashes = set(self.processed_hashes_file.read_text().splitlines())
            self.logger.debug(f"Loaded {len(hashes)} processed file hashes")
            return hashes

        self.logger.debug("No processed files record found - starting fresh")
        return set()

    def _save_processed_hash(self, file_hash: str):
        """
        Save a file hash as processed to prevent duplicate processing.

        Args:
            file_hash: Hash identifying the file
        """
        with open(self.processed_hashes_file, 'a') as f:
            f.write(f'{file_hash}\n')

        self.processed_hashes.add(file_hash)
        self.logger.debug(f"Saved processed hash: {file_hash}")

    def _get_file_hash(self, filepath: Path) -> str:
        """
        Generate hash based on filename, size, and modification time.

        This provides quick identification without reading entire file contents.

        Args:
            filepath: Path to the file

        Returns:
            MD5 hash string
        """
        stat = filepath.stat()
        hash_input = f"{filepath.name}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _get_content_preview(self, filepath: Path, max_chars: int = 500) -> str:
        """
        Get preview of file content if text-based.

        Args:
            filepath: Path to the file
            max_chars: Maximum characters to preview

        Returns:
            Content preview string
        """
        suffix = filepath.suffix.lower()

        if suffix in self.TEXT_EXTENSIONS:
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                if len(content) > max_chars:
                    return content[:max_chars] + '...'
                return content if content.strip() else "[Empty file]"
            except Exception as e:
                return f"[Could not read file: {e}]"

        elif suffix in self.IMAGE_EXTENSIONS:
            return "[Image file - no text preview available]"

        elif suffix in self.DOCUMENT_EXTENSIONS:
            return f"[{suffix.upper().replace('.', '')} document - no text preview available]"

        else:
            return f"[{suffix or 'Unknown'} file - no text preview available]"

    def _format_size(self, size_bytes: int) -> str:
        """
        Format bytes to human readable size.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human readable size string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _get_file_type(self, filepath: Path) -> str:
        """
        Get human-readable file type description.

        Args:
            filepath: Path to the file

        Returns:
            File type description
        """
        suffix = filepath.suffix.lower()

        type_map = {
            '.txt': 'Text Document',
            '.md': 'Markdown Document',
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.csv': 'CSV Data File',
            '.json': 'JSON Data File',
            '.xml': 'XML Data File',
            '.png': 'PNG Image',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.gif': 'GIF Image',
            '.py': 'Python Script',
            '.js': 'JavaScript File',
            '.html': 'HTML Document',
        }

        return type_map.get(suffix, f"{suffix.upper().replace('.', '')} File" if suffix else "Unknown File")

    def check_for_updates(self) -> list:
        """
        Check Inbox folder for new files.

        Returns:
            List of tuples (filepath, file_hash) for new files
        """
        new_files = []

        try:
            for filepath in self.inbox.iterdir():
                # Skip directories and hidden files
                if not filepath.is_file() or filepath.name.startswith('.'):
                    continue

                file_hash = self._get_file_hash(filepath)
                if file_hash not in self.processed_hashes:
                    new_files.append((filepath, file_hash))
                    self.logger.debug(f"New file detected: {filepath.name}")

        except Exception as e:
            self.logger.error(f"Error scanning Inbox: {e}")

        return new_files

    def create_action_file(self, item) -> Path:
        """
        Create a markdown action file for a dropped file.

        Args:
            item: Tuple of (filepath, file_hash)

        Returns:
            Path to created markdown file
        """
        filepath, file_hash = item

        try:
            stat = filepath.stat()
            timestamp = datetime.now().isoformat()
            unique_id = generate_unique_id("FILE")

            # Build markdown content
            content = f'''---
type: file_drop
original_name: "{filepath.name}"
original_path: Inbox/{filepath.name}
size: {stat.st_size}
extension: "{filepath.suffix}"
detected_at: {timestamp}
status: pending
file_id: {unique_id}
file_hash: {file_hash}
---

## File Information

- **Filename:** {filepath.name}
- **Size:** {self._format_size(stat.st_size)}
- **Type:** {self._get_file_type(filepath)}
- **Location:** Inbox/{filepath.name}

## Content Preview

{self._get_content_preview(filepath)}

## Suggested Actions

- [ ] Review file contents
- [ ] Process according to file type
- [ ] Archive after processing
'''

            # Create safe filename for action file
            safe_name = safe_filename(filepath.stem, max_length=30)
            action_filename = f"FILE_{safe_name}_{file_hash[:8]}.md"
            action_filepath = self.needs_action / action_filename

            # Write action file
            action_filepath.write_text(content, encoding='utf-8')
            self.logger.info(f"Created action file: {action_filename}")

            # Mark as processed
            self._save_processed_hash(file_hash)

            return action_filepath

        except Exception as e:
            self.logger.error(f"Error creating action file for {filepath.name}: {e}")
            raise


def create_test_file():
    """Create a test file in Inbox for testing the watcher."""
    from dotenv import load_dotenv
    load_dotenv()

    vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))
    inbox = vault_path / 'Inbox'
    inbox.mkdir(parents=True, exist_ok=True)

    test_file = inbox / f'test_file_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    test_file.write_text(f'''Test file created at {datetime.now().isoformat()}

This is a test file to verify the File System Watcher is working correctly.

It should be detected and create an action item in the Needs_Action folder.
''')

    print(f'✓ Created test file: {test_file}')
    return test_file


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='File System Watcher - Monitor Inbox for new files'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Create a test file in Inbox'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for cron)'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=60,
        help='Seconds between checks (default: 60)'
    )

    args = parser.parse_args()

    if args.test:
        print('=== CREATE TEST FILE ===')
        create_test_file()
        print('\nTest file created. Run watcher to process it.')
    elif args.once:
        print('=== FILE SYSTEM WATCHER (Single Run) ===')
        from dotenv import load_dotenv
        load_dotenv()
        watcher = FileSystemWatcher()
        count = watcher.run_once()
        print(f'\nProcessed {count} file(s)')
    else:
        print('=== FILE SYSTEM WATCHER ===')
        print(f'Check interval: {args.check_interval} seconds')
        print('Starting Inbox monitoring...')
        print('Press Ctrl+C to stop')
        print()

        from dotenv import load_dotenv
        load_dotenv()
        watcher = FileSystemWatcher(check_interval=args.check_interval)
        watcher.run()
