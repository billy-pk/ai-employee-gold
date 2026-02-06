# AI Employee Gold - System Architecture

## Overview

AI Employee Gold is an autonomous AI agent system that manages personal and business affairs through a combination of watchers, MCP servers, and intelligent processing loops.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                                                                              │
│    Obsidian Vault          Claude Code CLI          Cron Scheduler          │
│    (Human Review)          (Direct Commands)        (Automated Tasks)       │
└──────────┬──────────────────────┬─────────────────────────┬────────────────┘
           │                      │                         │
           ▼                      ▼                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            APPROVAL LAYER                                     │
│                                                                               │
│   Pending_Approval/     →    Human Review    →    Approval Executor          │
│   (TWEET_*.md, EMAIL_*.md, INVOICE_*.md)         (Executes approved actions) │
└───────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                             MCP SERVERS                                       │
│                                                                               │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │  Email MCP   │    │  Odoo MCP    │    │ Twitter MCP  │                  │
│   │              │    │              │    │              │                  │
│   │ • Send email │    │ • Invoices   │    │ • Post tweet │                  │
│   │ • Rate limit │    │ • Payments   │    │ • Mentions   │                  │
│   │ • Validation │    │ • Customers  │    │ • Engagement │                  │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│          │                   │                   │                           │
│          └───────────────────┴───────────────────┘                           │
│                              │                                                │
│                              ▼                                                │
│                    ┌──────────────────┐                                      │
│                    │   Audit Logger   │                                      │
│                    │                  │                                      │
│                    │ • All actions    │                                      │
│                    │ • JSON format    │                                      │
│                    │ • 90-day retain  │                                      │
│                    └──────────────────┘                                      │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              WATCHERS                                         │
│                                                                               │
│   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐              │
│   │ Gmail Watcher  │   │   Filesystem   │   │    Finance     │              │
│   │                │   │    Watcher     │   │    Watcher     │              │
│   │ • Check inbox  │   │                │   │                │              │
│   │ • New emails   │   │ • New files    │   │ • Bank CSVs    │              │
│   │ • Create tasks │   │ • Attachments  │   │ • Subscriptions│              │
│   └────────┬───────┘   └────────┬───────┘   └────────┬───────┘              │
│            │                    │                    │                       │
│            └────────────────────┴────────────────────┘                       │
│                                 │                                            │
│                                 ▼                                            │
│                       ┌──────────────────┐                                   │
│                       │   Needs_Action/  │                                   │
│                       │                  │                                   │
│                       │ Creates tasks    │                                   │
│                       │ for processing   │                                   │
│                       └──────────────────┘                                   │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER                                    │
│                                                                               │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │                    Claude Processor                                 │    │
│   │                                                                     │    │
│   │  • Reads Needs_Action items                                        │    │
│   │  • Builds prompts with context                                     │    │
│   │  • Calls Claude API                                                │    │
│   │  • Generates plans and actions                                     │    │
│   │  • Creates approval requests                                       │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                 │                                            │
│                                 ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │                    Ralph Wiggum Loop                                │    │
│   │                                                                     │    │
│   │  • Multi-step task execution                                       │    │
│   │  • Iteration tracking                                              │    │
│   │  • Auto-continuation until complete                                │    │
│   │  • Max iterations safety                                           │    │
│   └────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           MONITORING LAYER                                    │
│                                                                               │
│   ┌────────────────────────┐        ┌────────────────────────┐              │
│   │       Watchdog         │        │    CEO Briefing        │              │
│   │                        │        │                        │              │
│   │ • Process monitoring   │        │ • Weekly summaries     │              │
│   │ • Auto-restart failed  │        │ • Multi-source data    │              │
│   │ • Health dashboard     │        │ • WoW comparisons      │              │
│   │ • Alert on failures    │        │ • Suggestions          │              │
│   └────────────────────────┘        └────────────────────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Watchers (`src/watchers/`)

Watchers continuously monitor for new items to process.

| Watcher | Input Source | Output |
|---------|--------------|--------|
| Gmail Watcher | Gmail inbox | `Needs_Action/EMAIL_*.md` |
| Filesystem Watcher | Watched folders | `Needs_Action/FILE_*.md` |
| Finance Watcher | `Business/Transactions/` | `Needs_Action/FINANCE_*.md` |

**Key Features:**
- Deduplication via hash tracking
- Atomic file operations
- Graceful error handling

### 2. MCP Servers (`src/mcp/`)

Model Context Protocol servers provide tool interfaces for Claude.

#### Email MCP (`email_mcp.py`)
```python
# Tools exposed:
- send_email(to, subject, body)
- reply_to_email(thread_id, body)
```

#### Odoo MCP (`odoo_mcp.py`)
```python
# Tools exposed:
- create_invoice(customer_id, lines, due_date)
- get_invoices(period, status)
- create_payment(invoice_id, amount, date)
- get_customers()
```

#### Twitter MCP (`twitter_mcp.py`)
```python
# Tools exposed:
- post_tweet(content)
- get_my_tweets(count)
- get_engagement(tweet_id)
- get_mentions(count)
- schedule_tweet(content, time)
```

### 3. Approval System

All sensitive actions flow through the approval system:

```
Action Request → Pending_Approval/*.md → Human Review → Approved/Rejected
                                                              │
                                                              ▼
                                              Approval Executor → Action → Audit Log
```

### 4. Data Flow

#### Bank CSV Processing
```
Business/Transactions/*.csv
        │
        ▼
Finance Watcher (detect format, parse, analyze)
        │
        ▼
Needs_Action/FINANCE_*.md (flagged items, subscriptions)
        │
        ▼
Claude Processor (generates plan)
        │
        ▼
Plans/*.md → Actions → Pending_Approval/ → Done/
```

#### Tweet Workflow
```
User Request or Schedule
        │
        ▼
Twitter MCP (create_tweet_approval)
        │
        ▼
Pending_Approval/TWEET_*.md
        │
        ▼
Human Review (approved: true/false)
        │
        ▼
Approval Executor → Twitter MCP.post_tweet() → Audit Log
        │
        ▼
Social/Twitter/posted.md (logged)
```

### 5. CEO Briefing Data Sources

```
┌─────────────────┐
│   Odoo MCP      │──→ Revenue, Invoices, Customers
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Finance Data  │──→ Expenses, Subscriptions (from CSVs)
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Done/ Folder  │──→ Completed Tasks
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Twitter MCP   │──→ Engagement Metrics
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           CEO Briefing Generator        │
│                                         │
│  • Aggregates all sources               │
│  • Calculates WoW changes               │
│  • Generates suggestions                │
│  • Outputs Briefings/YYYY-MM-DD_*.md    │
└─────────────────────────────────────────┘
```

### 6. Scheduled Tasks (Cron)

| Task | Schedule | Script |
|------|----------|--------|
| Finance Watcher | `*/5 * * * *` | `scripts/run_finance_watcher.py` |
| Watchdog | `*/5 * * * *` | `scripts/run_watchdog.py` |
| Odoo Sync | `0 */6 * * *` | `scripts/run_odoo_sync.py` |
| CEO Briefing | `0 23 * * 0` | `scripts/run_ceo_briefing.py` |
| Audit Cleanup | `0 1 1 * *` | Inline Python |

## Directory Structure

```
ai-employee-gold/
├── src/
│   ├── briefings/          # CEO Briefing & Data Collectors
│   │   ├── __init__.py
│   │   ├── ceo_briefing.py
│   │   └── data_collectors.py
│   ├── hooks/              # Claude Code hooks
│   │   ├── __init__.py
│   │   └── ralph_wiggum.py
│   ├── mcp/                # MCP Servers
│   │   ├── __init__.py
│   │   ├── email_mcp.py
│   │   ├── odoo_mcp.py
│   │   └── twitter_mcp.py
│   ├── utils/              # Utilities
│   │   ├── __init__.py
│   │   ├── audit_logger.py
│   │   └── vault_helpers.py
│   ├── watchdog/           # Process monitoring
│   │   ├── __init__.py
│   │   └── process_monitor.py
│   └── watchers/           # File/Email watchers
│       ├── __init__.py
│       ├── base_watcher.py
│       ├── filesystem_watcher.py
│       ├── finance_watcher.py
│       └── gmail_watcher.py
├── scripts/                # Cron-runnable scripts
├── skills/                 # Claude Code skills
├── tests/                  # Test suite (251 tests)
├── vault/                  # Obsidian vault
├── credentials/            # API credentials (gitignored)
└── config/                 # Configuration files
```

## Security Model

### Approval Gates
- All external actions require human approval
- Approval files have 24-48 hour expiry
- Rejected actions are logged with reason

### Audit Trail
- Every action logged to `Audit/YYYY-MM-DD.json`
- Immutable append-only logs
- 90-day retention (configurable)

### Credential Management
- All credentials in `credentials/` (gitignored)
- Environment variables for configuration
- No secrets in codebase

### Rate Limiting
- Email: 50 sends per day
- Twitter: API rate limits respected
- Claude: Usage logged and tracked

## Graceful Degradation

The system continues operating when services are unavailable:

| Service Down | System Behavior |
|--------------|-----------------|
| Odoo | Skip financial data, CEO briefing marks as unavailable |
| Twitter | Queue tweets, retry later, skip engagement data |
| Gmail | Queue emails locally, process when restored |
| Claude | Skip processing, alert user, maintain state |

## Testing

```bash
# Run all tests
uv run pytest

# Run specific module tests
uv run pytest tests/test_twitter_mcp.py -v

# Run integration tests
uv run pytest tests/test_integration.py -v

# Run graceful degradation tests
uv run pytest tests/test_graceful_degradation.py -v
```

**Test Coverage:** 251 tests across all components
