# Company Handbook - AI Employee Gold

**Version:** 3.0 (Gold Tier)
**Last Updated:** 2026-02-06

---

## 1. Overview

This handbook documents the policies, procedures, and guidelines for the AI Employee system. The Gold tier includes advanced capabilities for financial management, social media, and business intelligence.

---

## 2. Approval Requirements

### 2.1 Always Requires Human Approval

The following actions **always** require explicit human approval before execution:

| Action Type | Approval Folder | Expiry |
|-------------|-----------------|--------|
| Send Email | `Pending_Approval/` | 24 hours |
| Post Tweet | `Pending_Approval/` | 24 hours |
| Create Invoice | `Pending_Approval/` | 48 hours |
| Record Payment | `Pending_Approval/` | 48 hours |
| Delete Any Data | `Pending_Approval/` | 24 hours |

### 2.2 Approval Workflow

1. AI creates approval request file in `Pending_Approval/`
2. Human reviews and adds `approved: true` to frontmatter
3. System executes action and moves file to `Done/`
4. Action is logged to `Audit/` with full details

### 2.3 Rejection Workflow

1. Human adds `approved: false` with `rejection_reason:`
2. System logs rejection and moves file to `Done/`
3. AI is notified of rejection reason for learning

---

## 3. Financial Policies

### 3.1 Odoo Integration

- **Connection:** JSON-RPC API with API key authentication
- **Timeout:** 30 seconds per request
- **Retry:** 3 attempts with exponential backoff
- **Sync Frequency:** Every 6 hours

### 3.2 Invoice Management

- All invoice creation requires approval
- Draft invoices can be created without approval
- Posting invoices requires approval
- Payment recording requires approval

### 3.3 Bank CSV Processing

- CSV files dropped in `Business/Transactions/` are automatically processed
- Supported formats: Generic, Chase, Bank of America
- Large transactions (>$500) are flagged for review
- Subscriptions are automatically detected and summarized

### 3.4 Data Retention

- Financial snapshots: Kept indefinitely
- Audit logs: 90 days (configurable)
- Processed files: Tracked in logs, originals kept

---

## 4. Social Media Policies

### 4.1 Twitter/X Integration

- **API:** Twitter API v2 with OAuth 1.0a
- **Rate Limits:** Respected via `wait_on_rate_limit`
- **Approval:** All tweets require approval before posting

### 4.2 Tweet Workflow

1. AI drafts tweet and creates approval request
2. Human reviews content, timing, and appropriateness
3. On approval, tweet is posted via API
4. Tweet is logged to `Social/Twitter/posted.md`
5. Engagement tracked in `Social/Twitter/engagement.md`

### 4.3 Scheduling

- Tweets can be scheduled for future posting
- Scheduled tweets stored in `Social/Twitter/scheduled_posts.md`
- System posts at scheduled time (requires running scheduler)

### 4.4 Content Guidelines

- Keep tweets under 280 characters
- Professional tone aligned with business goals
- No controversial or sensitive topics without explicit approval
- Always verify facts before posting

---

## 5. Audit & Compliance

### 5.1 Audit Logging

All significant actions are logged to `Audit/YYYY-MM-DD.json`:

```json
{
  "timestamp": "ISO-8601",
  "action_type": "email_send|invoice_create|tweet_post|...",
  "actor": "claude_code|system|human",
  "target": "description of target",
  "parameters": {},
  "approval_status": "pending|approved|rejected",
  "result": "success|failure",
  "result_details": {}
}
```

### 5.2 Log Retention

- Default: 90 days
- Configurable via `AUDIT_RETENTION_DAYS` environment variable
- Cleanup runs on 1st of each month

### 5.3 Audit Access

- All audit logs are human-readable JSON
- Can be queried via `AuditLogger.get_entries()` with filters
- Daily stats available via `AuditLogger.get_stats()`

---

## 6. Process Monitoring

### 6.1 Watchdog

The watchdog monitors these processes:

| Process | PID File | Restart Command |
|---------|----------|-----------------|
| Gmail Watcher | `Logs/gmail_watcher.pid` | `scripts/run_gmail_watcher.py` |
| Filesystem Watcher | `Logs/filesystem_watcher.pid` | `scripts/run_fs_watcher.py` |
| Finance Watcher | `Logs/finance_watcher.pid` | `scripts/run_finance_watcher.py` |

### 6.2 Failure Handling

- 3 consecutive restart failures trigger an alert
- Alerts update `Dashboard.md` health section
- Daily restart count is tracked and reset at midnight

### 6.3 Health Checks

- Run every 5 minutes via cron
- Status visible on `Dashboard.md`
- Full health summary available via `ProcessMonitor.get_health_summary()`

---

## 7. Task Management

### 7.1 Ralph Wiggum Loop

For complex, multi-step tasks:

1. Create task file in `Tasks/TASK_[id].md`
2. Define objective and optional steps
3. Set `max_iterations` (default: 10)
4. AI works on task, logging each iteration
5. Task completes when objective met or max iterations reached
6. Completed tasks move to `Done/`

### 7.2 Task States

| Status | Description |
|--------|-------------|
| `pending` | Not yet started |
| `in_progress` | Currently being worked on |
| `completed` | Successfully finished |
| `blocked` | Waiting on external dependency |
| `max_iterations` | Hit iteration limit |
| `failed` | Could not complete |

---

## 8. CEO Briefings

### 8.1 Generation Schedule

- Weekly briefings: Sunday at 23:00
- On-demand via `/ceo-briefing` skill

### 8.2 Content Sources

| Source | Data Collected |
|--------|---------------|
| Odoo | Revenue, invoices, payments, customers |
| Bank CSVs | Expenses, subscriptions |
| Done Folder | Completed tasks |
| Twitter | Engagement metrics, mentions |

### 8.3 Week-over-Week Comparison

- Revenue change
- Task completion rate
- Social engagement trends
- Outstanding invoice changes

### 8.4 Graceful Degradation

If a data source is unavailable:
- System continues with available data
- Unavailable sections marked accordingly
- No errors thrown, just warnings logged

---

## 9. Folder Structure

```
vault/
├── Audit/                    # Daily JSON audit logs
├── Briefings/                # CEO weekly briefings
├── Business/
│   ├── Transactions/         # Bank CSV files
│   ├── Odoo/                  # Odoo sync data
│   └── Business_Goals.md     # Current objectives
├── Data/
│   ├── Briefings/            # Briefing data files (JSON)
│   └── Financial/            # Financial snapshots
├── Done/                     # Completed items
├── Logs/                     # Process logs and PID files
├── Needs_Action/             # Items requiring attention
├── Pending_Approval/         # Awaiting human approval
├── Plans/                    # Active plans
├── Quarantine/               # Malformed/suspicious files
├── Social/
│   └── Twitter/
│       ├── scheduled_posts.md
│       ├── posted.md
│       └── engagement.md
├── Tasks/                    # Active task files
├── Dashboard.md              # System overview
└── Company_Handbook.md       # This file
```

---

## 10. Emergency Procedures

### 10.1 System Overload

If system is processing too many items:
1. Stop cron jobs: `crontab -r`
2. Review `Logs/` for issues
3. Clear `Needs_Action/` queue if necessary
4. Restart cron jobs selectively

### 10.2 API Failures

If external APIs fail:
1. Check API status pages (Twitter, Gmail)
2. Verify credentials in `credentials/`
3. Check rate limits in audit logs
4. System will retry automatically

### 10.3 Data Recovery

If data is corrupted:
1. Check `Quarantine/` for isolated files
2. Review `Audit/` logs for recent actions
3. Restore from backups if necessary

---

## 11. Contact & Support

- **System Issues:** Check `Dashboard.md` health section
- **Audit Questions:** Review `Audit/` logs
- **Policy Changes:** Update this handbook

---

_This handbook is maintained as part of the AI Employee Gold codebase._
