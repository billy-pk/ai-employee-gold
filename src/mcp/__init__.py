"""
MCP (Model Context Protocol) servers module.

Provides action execution capabilities:
- EmailMCP: Send emails via Gmail API
"""

from .email_mcp import EmailMCP

__all__ = ['EmailMCP']
