"""
Executors module - Action layer components.

Available executors:
- ApprovalExecutor: Execute approved actions
"""

from .approval_executor import ApprovalExecutor

__all__ = ['ApprovalExecutor']
