# CEO Briefing Skill

## Purpose

Generate comprehensive weekly business intelligence briefings aggregating data from all connected systems.

## When to Use

Use this skill when:
- Preparing for weekly business reviews
- Need a consolidated view of business performance
- Checking on overdue invoices or pending tasks
- Reviewing social media engagement trends
- Getting proactive suggestions for business optimization

## Data Sources

The briefing aggregates data from:

1. **Odoo (Financial)**
   - Revenue and invoices
   - Outstanding and overdue amounts
   - Customer count
   - Draft invoices pending

2. **Twitter (Social)**
   - Follower count and changes
   - Engagement metrics (likes, retweets, replies)
   - Mention count
   - Top performing tweets

3. **Vault (Tasks)**
   - Completed tasks in period
   - Pending tasks count
   - Recently completed task list

4. **Bank Data (Expenses)**
   - Total expenses
   - Detected subscriptions
   - Large transactions

## Instructions

### Generating a Briefing

1. Run the briefing generator:
   ```bash
   python scripts/run_ceo_briefing.py
   ```

2. Or use the module directly:
   ```python
   from src.briefings.ceo_briefing import generate_ceo_briefing
   result = generate_ceo_briefing(period_days=7)
   ```

3. Output is saved to:
   - `Briefings/YYYY-MM-DD_Weekday_Briefing.md`
   - `Data/Briefings/BRIEFING_DATA_YYYY-MM-DD.json`

### Interpreting the Briefing

**Alerts Section** (⚠️)
- Critical items requiring immediate attention
- Overdue invoices
- System failures

**Executive Summary**
- Key metrics at a glance
- Week-over-week (WoW) changes indicated by ↑ or ↓

**Financial Overview**
- Revenue for the period
- Outstanding amounts to collect
- Invoice pipeline status

**Social Media**
- Engagement performance
- Follower growth
- Top performing content

**Tasks & Productivity**
- Work completed vs pending
- List of completed items

**Recommended Actions**
- Proactive suggestions based on data
- Prioritized action items

### Week-over-Week Comparison

The briefing automatically compares with previous week's data:
- Revenue change
- Follower growth
- Task completion rate

Previous data is stored in `Data/Briefings/` for trend analysis.

## Graceful Degradation

The briefing handles missing data sources gracefully:

- **Odoo unavailable**: Financial section shows "not available"
- **Twitter unavailable**: Social section shows "not available"
- **Bank data missing**: Expenses section omitted
- **Vault always available**: Tasks section always populated

Each section indicates its data source status in the footer.

## Scheduling

Recommended cron schedule (Sunday 11 PM):
```cron
0 23 * * 0 cd /path/to/project && uv run python scripts/run_ceo_briefing.py
```

This ensures the briefing is ready for Monday morning review.

## Example Output

```markdown
# CEO Weekly Briefing

**Period**: 2026-01-29 to 2026-02-05
**Generated**: 2026-02-05 23:00

## ⚠️ Alerts

- **OVERDUE: $500.00 past due - immediate follow-up recommended**

## Executive Summary

- **Revenue**: $2,500.00 (↑ $500.00 WoW)
- **Followers**: 150 (+12 WoW)
- **Tasks Completed**: 8 (+3 WoW)

## Financial Overview

| Metric | Value |
|--------|-------|
| Total Customers | 5 |
| Revenue (Period) | $2,500.00 |
| Outstanding | $1,000.00 |
| Overdue | $500.00 |
| New Invoices | 3 |
| Draft Invoices | 1 |

## Recommended Actions

1. Follow up on $1,000.00 in outstanding invoices
2. Send 1 draft invoice(s) waiting to be posted
3. Review 5 pending tasks - consider prioritizing

---

*Data sources: Odoo ✓, Twitter ✓, Bank Data ✗, Vault ✓*
```

## Tips

- Generate briefings consistently (same day each week) for meaningful WoW comparisons
- Review alerts first - they indicate urgent items
- Use the data file for custom analysis or dashboards
- Missing data sources don't block briefing generation
- Consider the period length based on business cycle (7 days default)

---
*Managed by CEO Briefing Generator*
