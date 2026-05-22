# AI Employee - Gold Tier

**Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

[![Tests](https://img.shields.io/badge/tests-251%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)]()
[![Phase](https://img.shields.io/badge/phase-Gold-gold)]()

---

## What Does This App Do?

AI Employee is an **autonomous assistant** that runs in the background and manages your:

1. **Emails** - Monitors Gmail, creates action items, drafts replies (with your approval)
2. **Files** - Watches folders for new documents, processes them automatically
3. **Finances** - Parses bank CSV statements, detects subscriptions, flags large transactions
4. **Invoicing** - Creates and manages invoices in Odoo accounting software
5. **Social Media** - Posts tweets (with approval), tracks engagement metrics
6. **Business Intelligence** - Generates weekly CEO briefings with insights

### Key Principle: Human-in-the-Loop

The AI **never takes action without your approval**. It:
- Analyzes incoming data
- Creates plans and drafts
- Puts them in `Pending_Approval/` folder
- Waits for you to approve or reject
- Only then executes the action

---

## Do I Need to Run It Manually?

**No! Once cron is configured, everything runs automatically.**

### How It Works:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CRON SCHEDULER                               │
│                    (Runs automatically 24/7)                         │
└─────────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Gmail Watcher │      │Finance Watcher│      │   Watchdog    │
│  (every 2min) │      │  (every 5min) │      │  (every 5min) │
└───────┬───────┘      └───────┬───────┘      └───────────────┘
        │                      │
        ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      OBSIDIAN VAULT                                  │
│                                                                      │
│   Needs_Action/  →  Plans/  →  Pending_Approval/  →  Done/          │
│                                                                      │
│   YOU review and approve items in Pending_Approval/                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Automatic Schedule (Cron):

| Task | Frequency | What It Does |
|------|-----------|--------------|
| Gmail Watcher | Every 2 min | Checks for new emails |
| File Watcher | Every 1 min | Checks watched folders for new files |
| Finance Watcher | Every 5 min | Checks for new bank CSV files |
| Claude Processor | Every 5 min | Processes items in Needs_Action/ |
| Approval Executor | Every 1 min | Executes approved actions |
| Watchdog | Every 5 min | Monitors system health, restarts failed processes |
| Odoo Sync | Every 6 hours | Syncs financial data from Odoo |
| CEO Briefing | Sunday 11 PM | Generates weekly business report |

---

## How to Observe the System

### 1. Open Obsidian Vault

Your vault is at: `D:\AI_EMPLOYEE_VAULT` (or configured `VAULT_PATH`)

**Key files to watch:**

| File/Folder | What to Look For |
|-------------|------------------|
| `Dashboard.md` | System status, health, recent activity |
| `Needs_Action/` | New items waiting to be processed |
| `Pending_Approval/` | Items waiting for YOUR approval |
| `Done/` | Completed items (audit trail) |
| `Briefings/` | Weekly CEO briefings |
| `Audit/` | JSON logs of all actions taken |

### 2. Check Logs

```bash
# View Gmail Watcher logs
tail -f /tmp/gmail_watcher.log

# View Finance Watcher logs
tail -f /tmp/finance_watcher.log

# View Watchdog logs
tail -f /tmp/watchdog.log

# View Odoo sync logs
tail -f /tmp/odoo_sync.log

# View CEO briefing logs
tail -f /tmp/ceo_briefing.log

# View all Gold logs at once
tail -f /tmp/*.log
```

### 3. Manual Testing (Optional)

You can run any component manually to test it:

```bash
cd ~/vibe-coding-projects/ai-employee-gold

# Test Gmail Watcher (requires OAuth credentials)
uv run python scripts/run_gmail_watcher.py

# Test Gmail Watcher in dry-run mode (no Gmail connection needed)
uv run python scripts/run_gmail_watcher.py --dry-run

# Test Finance Watcher
uv run python scripts/run_finance_watcher.py

# Test Watchdog
uv run python scripts/run_watchdog.py

# Test Odoo Sync
uv run python scripts/run_odoo_sync.py

# Generate CEO Briefing now (instead of waiting for Sunday)
uv run python scripts/run_ceo_briefing.py
```

---

## Detailed Feature Guide

### 1. Gmail Watcher

**What it does:** Monitors your Gmail inbox for unread, important messages and creates action items in the vault automatically.

**Capabilities:**
- Detects new unread + important emails every 2 minutes
- Creates a markdown action file in `Needs_Action/` for each email (sender, subject, snippet)
- Tracks already-processed email IDs to avoid duplicates
- Supports dry-run mode for testing without a Gmail connection

**One-time setup (required before first run):**

See [`credentials/README.md`](credentials/README.md) for the full Gmail OAuth setup walkthrough. In short:
1. Enable Gmail API in Google Cloud Console and create an OAuth 2.0 Desktop app credential
2. Save the downloaded JSON as `credentials/gmail_credentials.json`
3. On first run a browser window opens for authorization — `credentials/token.pickle` is then saved automatically

**How to use:**
```bash
# First run (browser opens for OAuth)
uv run python scripts/run_gmail_watcher.py

# Dry-run (creates a test file without Gmail connection)
uv run python scripts/run_gmail_watcher.py --dry-run

# Custom check interval (default 120 seconds)
uv run python scripts/run_gmail_watcher.py --check-interval 60
```

**Where to see results:**
- `Needs_Action/EMAIL_*.md` - One file per detected email
- `Logs/processed_emails.txt` - IDs of already-processed emails (deduplication)
- `/tmp/gmail_watcher.log` - Processing logs

---

### 2. Finance Watcher

**What it does:** Monitors `Business/Transactions/` folder for bank CSV files.

**How to use:**
1. Download your bank statement as CSV
2. Drop it in `D:\AI_EMPLOYEE_VAULT\Business\Transactions\`
3. Within 5 minutes, Finance Watcher will:
   - Parse the CSV (supports Chase, Bank of America, generic formats)
   - Detect subscriptions (Netflix, Spotify, Adobe, etc.)
   - Flag large transactions (>$500)
   - Create a summary in `Needs_Action/FINANCE_*.md`

**Where to see results:**
- `Needs_Action/FINANCE_*.md` - Summary with flagged items
- `/tmp/finance_watcher.log` - Processing logs

---

### 3. Odoo Integration

**What it does:** Connects to your Odoo accounting system to manage invoices.

**Capabilities:**
- Create invoices
- Record payments
- View customer list
- Check account balances
- Sync financial data

**How to use:**
1. Ensure Odoo is running: `docker-compose up -d`
2. Access Odoo UI: http://localhost:8069
3. System syncs automatically every 6 hours
4. Manual sync: `uv run python scripts/run_odoo_sync.py`

**Where to see results:**
- `Data/Financial/FINANCIAL_SNAPSHOT_*.json` - Raw data
- `Briefs/FINANCIAL_BRIEF_*.md` - Human-readable summary
- `/tmp/odoo_sync.log` - Sync logs

---

### 4. Twitter/X Integration

**What it does:** Manages your Twitter/X account with a human-in-the-loop approval workflow.

**Capabilities:**
- Post tweets (requires your approval before posting)
- Schedule tweets for later
- Track engagement metrics (likes, retweets, impressions)
- Monitor mentions

**One-time setup (required before first run):**

See [`credentials/README.md`](credentials/README.md) for the full Twitter/X setup walkthrough. In short:
1. Create a Twitter developer app with **Read and Write** permissions
2. Generate API Key, API Secret, Access Token, Access Token Secret, and Bearer Token
3. Save all five values in `credentials/twitter_credentials.json`

**How tweet posting works:**
1. AI drafts a tweet → Creates `Pending_Approval/TWEET_*.md`
2. You review the tweet in Obsidian
3. Add `approved: true` to the frontmatter
4. Approval Executor (runs every 1 min) detects the approval and posts the tweet
5. Logged to `Social/Twitter/posted.md`

**Where to see results:**
- `Pending_Approval/TWEET_*.md` - Tweets awaiting your approval
- `Social/Twitter/posted.md` - Posted tweets log
- `Social/Twitter/engagement.md` - Engagement metrics
- `Social/Twitter/scheduled_posts.md` - Scheduled future tweets

---

### 5. CEO Briefing

**What it does:** Generates a weekly business intelligence report.

**When it runs:** Automatically every Sunday at 11 PM

**What it includes:**
- Financial summary (revenue, outstanding invoices, overdue)
- Social media metrics (followers, engagement, mentions)
- Task completion statistics
- Alerts and recommended actions
- Week-over-week comparisons

**How to generate manually:**
```bash
uv run python scripts/run_ceo_briefing.py
```

**Where to see results:**
- `Briefings/YYYY-MM-DD_Weekday_Briefing.md` - The briefing
- `Data/Briefings/BRIEFING_DATA_*.json` - Raw data for comparisons

---

### 6. Watchdog (System Monitor)

**What it does:** Monitors all watchers and restarts them if they crash.

**How it works:**
1. Checks PID files in `Logs/` folder
2. Verifies each process is running
3. Restarts any stopped processes
4. Updates `Dashboard.md` with health status
5. Alerts after 3 consecutive failures

**Where to see results:**
- `Dashboard.md` - System Health section
- `/tmp/watchdog.log` - Health check logs

---

### 7. Audit Logger

**What it does:** Logs every action for compliance and debugging.

**What gets logged:**
- Emails sent
- Invoices created
- Tweets posted
- Files processed
- All approvals/rejections

**Where to see results:**
- `Audit/YYYY-MM-DD.json` - Daily audit logs

**Retention:** 90 days (auto-cleanup on 1st of each month)

---

## Quick Reference: Vault Folder Structure

```
AI_EMPLOYEE_VAULT/
│
├── Dashboard.md           ← System status overview
├── Company_Handbook.md    ← Policies and procedures
│
├── Inbox/                 ← Raw incoming items
├── Needs_Action/          ← Items to be processed by AI
├── Plans/                 ← AI-generated plans
├── Pending_Approval/      ← ⭐ CHECK THIS - Items waiting for YOU
├── Done/                  ← Completed items
│
├── Business/
│   ├── Transactions/      ← Drop bank CSVs here
│   └── Odoo/              ← Odoo sync data
│
├── Social/
│   └── Twitter/
│       ├── scheduled_posts.md
│       ├── posted.md
│       └── engagement.md
│
├── Briefings/             ← CEO weekly briefings
├── Audit/                 ← Action logs (JSON)
├── Logs/
│   ├── processed_emails.txt  ← Gmail deduplication IDs
│   └── *.pid                 ← Process PID files (used by Watchdog)
└── Tasks/                 ← Multi-step task tracking
```

---

## Common Operations

### Start the System
```bash
# Start cron service (if not running)
sudo service cron start

# Verify cron is running
crontab -l
```

### Stop the System
```bash
# Remove all cron jobs (stops automation)
crontab -r

# Or just stop cron service
sudo service cron stop
```

### Check System Health
```bash
# Quick status check
uv run python scripts/run_watchdog.py

# Or check Dashboard.md in Obsidian
```

### Force Generate CEO Briefing
```bash
uv run python scripts/run_ceo_briefing.py
```

### Test a Component
```bash
# Run any script manually
uv run python scripts/run_finance_watcher.py
uv run python scripts/run_odoo_sync.py
```

### View Recent Activity
```bash
# Check audit logs
cat /mnt/d/AI_EMPLOYEE_VAULT/Audit/$(date +%Y-%m-%d).json | jq .

# Check recent logs
tail -50 /tmp/finance_watcher.log
```

---

## Troubleshooting

### Nothing is happening?
1. Check cron is running: `service cron status`
2. Check crontab exists: `crontab -l`
3. Check logs: `tail -f /tmp/*.log`

### Gmail not working?

- For credential errors, see [`credentials/README.md`](credentials/README.md#troubleshooting)
- **No emails appearing in Needs_Action/?** — only emails marked **both** unread and important in Gmail are picked up; mark them as Important in Gmail or adjust the query in `src/watchers/gmail_watcher.py`

### Twitter/X not working?

- For credential and API errors, see [`credentials/README.md`](credentials/README.md#troubleshooting-1)
- **Tweets not posting after approval?** — confirm `approved: true` is in the frontmatter of the `Pending_Approval/TWEET_*.md` file and check `tail -f /tmp/*.log | grep -i tweet`

### Odoo not connecting?
1. Ensure Docker is running: `docker ps`
2. Start Odoo: `cd ~/vibe-coding-projects/ai-employee-gold && docker-compose up -d`
3. Check Odoo UI: http://localhost:8069

### Want to see what's happening in real-time?
```bash
# Watch all logs
tail -f /tmp/*.log /mnt/d/AI_EMPLOYEE_VAULT/Logs/*.log
```

---

## Testing

```bash
# Run all 251 tests
uv run pytest

# Run specific component tests
uv run pytest tests/test_finance_watcher.py -v
uv run pytest tests/test_twitter_mcp.py -v
uv run pytest tests/test_ceo_briefing.py -v

# Run integration tests
uv run pytest tests/test_integration.py -v
```

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture diagrams
- [PRD.md](PRD.md) - Product requirements
- [TASKS.md](TASKS.md) - Implementation checklist
- [reports/gold_completion_report.md](reports/gold_completion_report.md) - Completion report

---

## Summary

| Question | Answer |
|----------|--------|
| Do I need to run it manually? | **No**, cron runs everything automatically |
| Where do I approve things? | `Pending_Approval/` folder in Obsidian |
| Where are the logs? | `/tmp/*.log` and `Audit/` folder |
| Where are the reports? | `Briefings/` folder |
| How do I stop it? | `crontab -r` or `sudo service cron stop` |
| How do I test it? | Run any script manually with `uv run python scripts/...` |

---

**AI Employee Gold v3.0** - Your autonomous business assistant.
