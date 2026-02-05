"""
Base watcher abstract class.

Provides common functionality for all watcher implementations.
Watchers monitor external sources and create action items in the vault.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import logging
import time
import os
from dotenv import load_dotenv

load_dotenv()


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers.

    Watchers monitor external sources (Gmail, file system, etc.) and create
    markdown files in the vault's Needs_Action/ folder when new items are detected.
    """

    def __init__(self, check_interval: int = 60):
        """
        Initialize the watcher.

        Args:
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(os.getenv('VAULT_PATH', '/mnt/d/AI_EMPLOYEE_VAULT'))
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Initialized {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")

    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items to process.

        Returns:
            List of items to process (implementation-specific format)
        """
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create a markdown file in Needs_Action/ folder.

        Args:
            item: Item to process (implementation-specific format)

        Returns:
            Path to the created file
        """
        pass

    def run(self):
        """
        Main run loop - continuously check for updates.

        This method runs indefinitely, checking for updates at regular intervals.
        Press Ctrl+C to stop.
        """
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info("Press Ctrl+C to stop")

        try:
            while True:
                try:
                    self.logger.debug("Checking for updates...")
                    items = self.check_for_updates()

                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.logger.info(f"Created: {filepath.name}")
                            except Exception as e:
                                self.logger.error(f"Failed to create action file: {e}")
                    else:
                        self.logger.debug("No new items found")

                except Exception as e:
                    self.logger.error(f"Error during check: {e}")

                self.logger.debug(f"Sleeping for {self.check_interval}s...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Stopping watcher (KeyboardInterrupt)")
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            raise

    def run_once(self) -> int:
        """
        Single execution for cron - check and process, then exit.

        This method performs one check cycle and exits, suitable for
        cron-based scheduling instead of continuous operation.

        Returns:
            Number of items processed
        """
        self.logger.info(f"Running {self.__class__.__name__} (single execution)")

        try:
            items = self.check_for_updates()
            processed = 0

            if items:
                self.logger.info(f"Found {len(items)} new item(s)")
                for item in items:
                    try:
                        filepath = self.create_action_file(item)
                        self.logger.info(f"Created: {filepath.name}")
                        processed += 1
                    except Exception as e:
                        self.logger.error(f"Failed to create action file: {e}")
            else:
                self.logger.debug("No new items found")

            self.logger.info(f"Completed: {processed} item(s) processed")
            return processed

        except Exception as e:
            self.logger.error(f"Error during check: {e}")
            raise
