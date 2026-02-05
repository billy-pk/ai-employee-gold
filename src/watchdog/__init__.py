"""
Watchdog - Process monitoring and health management.

Monitors watcher processes and restarts failed components.
"""

from .process_monitor import ProcessMonitor, get_watchdog

__all__ = ['ProcessMonitor', 'get_watchdog']
