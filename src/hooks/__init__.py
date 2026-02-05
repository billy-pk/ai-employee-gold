"""
Hooks - Claude Code integration hooks and loops.

Provides task persistence mechanisms like the Ralph Wiggum loop.
"""

from .ralph_wiggum import RalphWiggumLoop, TaskState, create_task, get_task

__all__ = ['RalphWiggumLoop', 'TaskState', 'create_task', 'get_task']
