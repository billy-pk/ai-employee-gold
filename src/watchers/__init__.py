"""
Watchers module - Monitor external sources for new items.

Available watchers:
- GmailWatcher: Monitor Gmail for important unread emails
- FileSystemWatcher: Monitor Inbox folder for new files
"""

from .base_watcher import BaseWatcher
from .gmail_watcher import GmailWatcher
from .filesystem_watcher import FileSystemWatcher

__all__ = ['BaseWatcher', 'GmailWatcher', 'FileSystemWatcher']
