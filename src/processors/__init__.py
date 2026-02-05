"""
Processors module - Reasoning layer components.

Available processors:
- ClaudeProcessor: Trigger Claude Code for item processing
"""

from .claude_processor import ClaudeProcessor

__all__ = ['ClaudeProcessor']
