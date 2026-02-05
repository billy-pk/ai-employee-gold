"""Briefings module - Daily data collection and reporting."""

from .data_collectors import (
    OdooDataCollector,
    collect_odoo_data,
    generate_financial_brief,
)

__all__ = [
    'OdooDataCollector',
    'collect_odoo_data',
    'generate_financial_brief',
]
