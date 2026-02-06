"""Briefings module - Daily data collection and reporting."""

from .data_collectors import (
    OdooDataCollector,
    TwitterDataCollector,
    FinancialSnapshot,
    SocialSnapshot,
    collect_odoo_data,
    collect_twitter_data,
    generate_financial_brief,
    generate_engagement_summary,
)

from .ceo_briefing import (
    CEOBriefingGenerator,
    BriefingData,
    generate_ceo_briefing,
)

__all__ = [
    'OdooDataCollector',
    'TwitterDataCollector',
    'FinancialSnapshot',
    'SocialSnapshot',
    'collect_odoo_data',
    'collect_twitter_data',
    'generate_financial_brief',
    'generate_engagement_summary',
    'CEOBriefingGenerator',
    'BriefingData',
    'generate_ceo_briefing',
]
