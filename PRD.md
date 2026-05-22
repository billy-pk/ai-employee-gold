# Product Requirements Document (PRD)
# Personal AI Employee - Digital FTE System

**Version:** 3.0  
**Project Codename:** Digital FTE  
**Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

---

## 1. Executive Summary

The Personal AI Employee is an autonomous AI agent system that proactively manages personal and business affairs. Unlike traditional chatbots that wait for user input, this system actively monitors communications, finances, and social media—then takes action or requests approval when needed.

The system operates on a local-first architecture using Claude Code as the reasoning engine and Obsidian as the management dashboard, ensuring privacy while maintaining full autonomy capabilities.

**Value Proposition:** A Digital FTE works ~8,760 hours annually vs. a human's ~2,000 hours, with 85-90% cost reduction per task ($0.25-$0.50 vs. $3.00-$6.00).

**Current Phase:** Gold (Autonomous Employee) - Full business integration with Odoo accounting, social media automation, and autonomous multi-step task completion.

**Previous Phases:** 
- Bronze ✅ Completed
- Silver ✅ Completed

---

## 2. Gold Phase Overview

### 2.1 What's New in Gold

| Component | Silver (Completed) | Gold (New) |
|-----------|-------------------|------------|
| **Watchers** | Gmail + File System | + Finance Watcher (Bank CSV) |
| **MCP Servers** | Email MCP | + Odoo MCP + Twitter/X MCP |
| **Accounting** | None | Odoo Community integration |
| **Social Media** | None | Twitter/X posting & summaries |
| **Business Intelligence** | None | Weekly CEO Briefing |
| **Task Persistence** | Single-pass | Ralph Wiggum loop (multi-step) |
| **Error Recovery** | Basic | Watchdog + graceful degradation |
| **Audit Logging** | Basic logs | Comprehensive structured audit |

### 2.2 Gold Phase Goals

1. **Full Business Integration:** Connect personal and business domains via Odoo
2. **Social Media Presence:** Automated Twitter/X posting with summaries
3. **Financial Visibility:** Bank CSV import + Odoo accounting data
4. **Proactive Insights:** Weekly CEO Briefing with actionable recommendations
5. **Task Persistence:** Ralph Wiggum loop for autonomous multi-step completion
6. **Production Reliability:** Watchdog monitoring + graceful degradation
7. **Compliance Ready:** Comprehensive audit logging for all actions

---

## 3. System Architecture

### 3.1 Development Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                         WINDOWS                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    OBSIDIAN                              │   │
│   │                 (Windows App)                            │   │
│   │                                                          │   │
│   │   Vault: D:\AI_EMPLOYEE_VAULT                           │   │
│   │                                                          │   │
│   │   - View Dashboard.md & CEO Briefings                   │   │
│   │   - Review Plans\ and Approvals                         │   │
│   │   - Monitor Business\ and Social\ folders               │   │
│   │   - Drop Bank CSVs in Transactions\                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                 ODOO COMMUNITY                           │   │
│   │              (localhost:8069)                            │   │
│   │                                                          │   │
│   │   - Invoicing & Accounting                              │   │
│   │   - Customer Management                                  │   │
│   │   - Financial Reports                                    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                         WSL / BASH                               │
├────────────────────────────┬────────────────────────────────────┤
│                            │                                     │
│   TERMINAL 1               │   TERMINAL 2                       │
│   (Development)            │   (Execution)                      │
│                            │                                     │
│   Location:                │   Location:                        │
│   ~/vibe-coding-projects/  │   /mnt/d/AI_EMPLOYEE_VAULT         │
│     ai-employee            │                                     │
│                            │                                     │
│   Purpose:                 │   Purpose:                         │
│   - Write Python code      │   - Run Claude Code on vault       │
│   - Develop MCP servers    │   - Execute Ralph Wiggum loops     │
│   - Configure watchers     │   - Generate CEO Briefings         │
│   - Manage cron + watchdog │   - Process multi-step tasks       │
│                            │                                     │
└────────────────────────────┴────────────────────────────────────┘
```

### 3.2 Path Mapping Reference

| Context | Path |
|---------|------|
| Windows (Obsidian) | `D:\AI_EMPLOYEE_VAULT` |
| Windows (Odoo) | `http://localhost:8069` |
| WSL (Vault Access) | `/mnt/d/AI_EMPLOYEE_VAULT` |
| WSL (Code Project) | `~/vibe-coding-projects/ai-employee` |

### 3.3 Core Components (Gold)

| Component | Technology | Location | Status |
|-----------|------------|----------|--------|
| **The Brain** | Claude Code | Terminal 2 | Silver ✅ |
| **The Memory/GUI** | Obsidian | `D:\AI_EMPLOYEE_VAULT` | Silver ✅ |
| **Gmail Watcher** | Python | `src/watchers/` | Silver ✅ |
| **File System Watcher** | Python | `src/watchers/` | Silver ✅ |
| **Finance Watcher** | Python | `src/watchers/` | **Gold NEW** |
| **Email MCP** | Python | `src/mcp/` | Silver ✅ |
| **Odoo MCP** | Python | `src/mcp/` | **Gold NEW** |
| **Twitter/X MCP** | Python | `src/mcp/` | **Gold NEW** |
| **Claude Processor** | Python + CLI | `src/processors/` | Silver ✅ |
| **Approval Executor** | Python | `src/executors/` | Silver ✅ |
| **CEO Briefing Generator** | Python + Claude | `src/briefings/` | **Gold NEW** |
| **Ralph Wiggum Loop** | Claude Code Hook | `src/hooks/` | **Gold NEW** |
| **Watchdog** | Python | `src/watchdog/` | **Gold NEW** |
| **Cron Scheduler** | crontab | WSL | Silver ✅ (extended) |

### 3.4 Complete Data Flow (Gold)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PERCEPTION LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Gmail        File System      Bank CSV        Twitter/X API    │
│    ↓              ↓               ↓                 ↓           │
│  Gmail        FileSystem      Finance          (Read-only)      │
│  Watcher      Watcher         Watcher          for summaries    │
│    ↓              ↓               ↓                 ↓           │
│    └──────────────┴───────────────┴─────────────────┘           │
│                           ↓                                      │
│                 /Needs_Action/*.md                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     REASONING LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Claude Processor (with Ralph Wiggum Loop)                     │
│       ↓                                                          │
│   1. Check: Items in /Needs_Action/?                            │
│   2. Create task state file                                     │
│   3. Start Ralph Wiggum loop:                                   │
│      a. Claude processes task                                   │
│      b. Claude tries to exit                                    │
│      c. Stop hook: Is task in /Done?                           │
│         - NO → Re-inject prompt, continue                       │
│         - YES → Allow exit, task complete                       │
│   4. Generate Plans, create approval requests                   │
│   5. Update Dashboard                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                  HUMAN-IN-THE-LOOP LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   /Pending_Approval/                                            │
│       ↓                                                          │
│   Human reviews in Obsidian                                     │
│       ↓                                                          │
│   Move to /Approved/ or /Rejected/                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ACTION LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Approval Executor                                             │
│       ↓                                                          │
│   ┌─────────────┬─────────────┬─────────────┐                   │
│   │  Email MCP  │  Odoo MCP   │ Twitter MCP │                   │
│   │             │             │             │                   │
│   │ Send emails │ Create inv. │ Post tweets │                   │
│   │ Reply       │ Record pay. │ Get metrics │                   │
│   │             │ Get balance │             │                   │
│   └─────────────┴─────────────┴─────────────┘                   │
│                           ↓                                      │
│                   External Actions                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS INTELLIGENCE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CEO Briefing Generator (Weekly - Sunday Night)                │
│       ↓                                                          │
│   Data Sources:                                                  │
│   - Odoo MCP → Invoices, Revenue, Account Balances             │
│   - Bank CSV → Expenses, Subscriptions                          │
│   - /Done/ folder → Completed Tasks                             │
│   - /Plans/ folder → Bottleneck Analysis                        │
│   - Twitter/X → Social Media Summary                            │
│       ↓                                                          │
│   Output: /Briefings/YYYY-MM-DD_Monday_Briefing.md             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   RELIABILITY LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Watchdog Process                                              │
│   - Monitor all watcher processes                               │
│   - Restart failed components                                   │
│   - Alert on persistent failures                                │
│   - Log health status                                           │
│                                                                  │
│   Comprehensive Audit Logging                                   │
│   - All actions logged to /Audit/                               │
│   - Structured JSON format                                      │
│   - 90-day retention                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 Folder Structure (Gold)

```
D:\AI_EMPLOYEE_VAULT\
├── Dashboard.md                 # Real-time status (Silver)
├── Company_Handbook.md          # Rules of engagement (Silver)
│
├── Inbox\                       # File drops (Silver)
├── Needs_Action\                # Items to process (Silver)
├── Plans\                       # Claude's action plans (Silver)
├── Pending_Approval\            # Awaiting human review (Silver)
├── Approved\                    # Human-approved actions (Silver)
├── Rejected\                    # Human-rejected actions (Silver)
├── Done\                        # Completed items (Silver)
├── Logs\                        # Activity logs (Silver)
│
├── Business\                    # NEW: Business domain
│   ├── Business_Goals.md        # Objectives & KPIs
│   ├── Transactions\            # Bank CSV imports
│   │   └── 2026-01\
│   │       └── bank_export.csv
│   └── Odoo\                    # Odoo sync data
│       ├── invoices.md          # Recent invoices
│       ├── customers.md         # Customer list
│       └── accounts.md          # Account balances
│
├── Social\                      # NEW: Social media
│   └── Twitter\
│       ├── scheduled_posts.md   # Queued posts
│       ├── posted.md            # Posted content
│       └── engagement.md        # Metrics & summaries
│
├── Briefings\                   # NEW: CEO Briefings
│   └── 2026-01-06_Monday_Briefing.md
│
├── Audit\                       # NEW: Comprehensive audit logs
│   └── 2026-01-07.json
│
└── .skills\                     # Agent Skills (symlink)
```

### 3.6 Code Project Structure (Gold)

```
~/vibe-coding-projects/ai-employee-gold/
├── .env                         # Environment variables
├── .gitignore                   # Git exclusions
├── pyproject.toml               # UV project configuration
├── README.md                    # Project documentation
├── ARCHITECTURE.md              # NEW: Architecture documentation
├── credentials/                 # OAuth credentials (gitignored)
│   ├── gmail_credentials.json
│   ├── twitter_credentials.json # NEW
│   └── odoo_config.json         # NEW
├── src/
│   ├── __init__.py
│   ├── watchers/
│   │   ├── __init__.py
│   │   ├── base_watcher.py
│   │   ├── gmail_watcher.py
│   │   ├── filesystem_watcher.py
│   │   └── finance_watcher.py   # NEW: Bank CSV watcher
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── email_mcp.py
│   │   ├── odoo_mcp.py          # NEW: Odoo integration
│   │   └── twitter_mcp.py       # NEW: Twitter/X integration
│   ├── processors/
│   │   ├── __init__.py
│   │   └── claude_processor.py
│   ├── executors/
│   │   ├── __init__.py
│   │   └── approval_executor.py
│   ├── briefings/               # NEW
│   │   ├── __init__.py
│   │   ├── ceo_briefing.py      # Briefing generator
│   │   └── data_collectors.py   # Data source collectors
│   ├── hooks/                   # NEW
│   │   ├── __init__.py
│   │   └── ralph_wiggum.py      # Stop hook implementation
│   ├── watchdog/                # NEW
│   │   ├── __init__.py
│   │   └── process_monitor.py   # Process health monitoring
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── vault_helpers.py
│       └── audit_logger.py      # NEW: Structured audit logging
├── skills/
│   ├── item-processor/
│   │   └── SKILL.md
│   ├── ceo-briefing/            # NEW
│   │   └── SKILL.md
│   └── social-poster/           # NEW
│       └── SKILL.md
├── scripts/
│   ├── run_gmail_watcher.py
│   ├── run_filesystem_watcher.py
│   ├── run_finance_watcher.py   # NEW
│   ├── run_claude_processor.py
│   ├── run_approval_executor.py
│   ├── run_ceo_briefing.py      # NEW
│   └── run_watchdog.py          # NEW
└── tests/
    ├── test_gmail_watcher.py
    ├── test_odoo_mcp.py         # NEW
    └── test_twitter_mcp.py      # NEW
```

---

## 4. Odoo Community Integration

### 4.1 Overview

Odoo Community Edition provides free, self-hosted ERP capabilities. Gold tier integrates with Odoo for:
- Invoice management
- Customer tracking
- Payment recording
- Financial reporting

### 4.2 Odoo Setup Requirements

| Component | Requirement |
|-----------|-------------|
| **Odoo Version** | 19+ (Community Edition) |
| **Installation** | Local (Windows/WSL) or Docker |
| **Database** | PostgreSQL |
| **Access URL** | `http://localhost:8069` |
| **API** | JSON-RPC (External API) |

### 4.3 Odoo MCP Capabilities

| Capability | Method | Use Case |
|------------|--------|----------|
| `create_invoice` | Create | Generate customer invoices |
| `get_invoices` | Read | List invoices for period |
| `get_invoice` | Read | Get single invoice details |
| `create_payment` | Create | Record payment received |
| `get_customers` | Read | List all customers |
| `get_customer` | Read | Get customer details |
| `get_account_balance` | Read | Check account balances |
| `get_journal_entries` | Read | Get transactions for reporting |

### 4.4 Odoo Configuration Template

**credentials/odoo_config.json:**
```json
{
  "url": "http://localhost:8069",
  "database": "ai_employee_db",
  "username": "admin",
  "api_key": "your_api_key_here"
}
```

### 4.5 Odoo Data Sync

The system syncs Odoo data to the vault for offline access and CEO Briefing:

| Odoo Data | Vault Location | Sync Frequency |
|-----------|----------------|----------------|
| Recent Invoices | `/Business/Odoo/invoices.md` | Every 6 hours |
| Customer List | `/Business/Odoo/customers.md` | Daily |
| Account Balances | `/Business/Odoo/accounts.md` | Every 6 hours |

### 4.6 Invoice Vault Template

**Business/Odoo/invoices.md:**
```markdown
---
last_synced: 2026-01-07T10:00:00Z
source: odoo
period: 2026-01
---

# Invoices - January 2026

## Summary
- **Total Invoiced:** $15,000
- **Paid:** $12,000
- **Outstanding:** $3,000

## Recent Invoices

| ID | Customer | Amount | Status | Due Date |
|----|----------|--------|--------|----------|
| INV-001 | Client A | $5,000 | Paid | 2026-01-15 |
| INV-002 | Client B | $3,000 | Paid | 2026-01-20 |
| INV-003 | Client C | $7,000 | Outstanding | 2026-01-25 |

---
*Synced from Odoo by AI Employee*
```

---

## 5. Twitter/X Integration

### 5.1 Overview

Twitter/X integration enables:
- Posting tweets (with approval)
- Reading engagement metrics
- Generating social media summaries for CEO Briefing

### 5.2 Twitter API Requirements

| Component | Requirement |
|-----------|-------------|
| **API Version** | Twitter API v2 |
| **Access Level** | Basic (Free) or Pro |
| **Authentication** | OAuth 2.0 |
| **Rate Limits** | Varies by tier |

### 5.3 Twitter MCP Capabilities

| Capability | Method | Approval Required |
|------------|--------|-------------------|
| `post_tweet` | Write | ✅ Yes (always) |
| `get_my_tweets` | Read | No |
| `get_engagement` | Read | No |
| `schedule_tweet` | Write | ✅ Yes |
| `get_mentions` | Read | No |

### 5.4 Twitter Configuration Template

**credentials/twitter_credentials.json:**
```json
{
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "access_token": "your_access_token",
  "access_token_secret": "your_access_token_secret",
  "bearer_token": "your_bearer_token"
}
```

### 5.5 Twitter Approval Workflow

All tweets require human approval:

```
Claude drafts tweet
        ↓
Creates /Pending_Approval/TWEET_*.md
        ↓
Human reviews in Obsidian
        ↓
Move to /Approved/ to post
        ↓
Twitter MCP posts tweet
        ↓
Log to /Social/Twitter/posted.md
```

### 5.6 Tweet Approval Template

**Pending_Approval/TWEET_[id].md:**
```markdown
---
action_id: tweet_20260107_001
action_type: tweet_post
created_at: 2026-01-07T10:30:00Z
expires_at: 2026-01-08T10:30:00Z
status: pending
---

# Approval Required: Post Tweet

## Tweet Content

```
🚀 Excited to share our latest project milestone! 

We've automated 80% of our invoicing workflow using AI.

#AI #Automation #Productivity
```

## Character Count
142 / 280

## Context

- **Triggered By:** Weekly social media schedule
- **Plan Reference:** /Plans/PLAN_social_weekly.md

## Instructions

**To APPROVE:** Move this file to `/Approved/` folder
**To REJECT:** Move this file to `/Rejected/` folder
```

### 5.7 Social Media Summary Template

**Social/Twitter/engagement.md:**
```markdown
---
last_updated: 2026-01-07T10:00:00Z
period: 2026-01-01 to 2026-01-07
---

# Twitter Engagement Summary

## This Week

- **Tweets Posted:** 5
- **Total Impressions:** 2,450
- **Engagements:** 87
- **New Followers:** 12

## Top Performing Tweet

> "🚀 Excited to share our latest project milestone!"
> - Impressions: 850
> - Likes: 23
> - Retweets: 5

## Engagement Rate
3.5% (above average)

---
*Generated by AI Employee*
```

---

## 6. Finance Watcher & Bank CSV Import

### 6.1 Overview

The Finance Watcher monitors the Transactions folder for bank CSV exports and parses them for:
- Expense tracking
- Subscription detection
- CEO Briefing data

### 6.2 Bank CSV Import Workflow

```
Download CSV from bank website
        ↓
Drop in D:\AI_EMPLOYEE_VAULT\Business\Transactions\2026-01\
        ↓
Finance Watcher detects new file
        ↓
Parses transactions
        ↓
Creates /Needs_Action/FINANCE_*.md for review
        ↓
Updates transaction summary
        ↓
Available for CEO Briefing
```

### 6.3 Supported CSV Formats

The Finance Watcher should handle common bank export formats:

| Bank Type | Expected Columns |
|-----------|------------------|
| Generic | Date, Description, Amount, Balance |
| Chase | Posting Date, Description, Amount, Type |
| Bank of America | Date, Description, Amount, Running Bal |

### 6.4 Transaction Action File Template

**Needs_Action/FINANCE_[date]_[hash].md:**
```markdown
---
type: finance_import
source_file: bank_export_2026-01.csv
import_date: 2026-01-07T10:00:00Z
transaction_count: 45
status: pending_review
---

# Bank Import: January 2026

## Summary

- **Transactions:** 45
- **Total Income:** $12,500
- **Total Expenses:** $3,200
- **Net:** +$9,300

## Flagged Transactions

### Subscriptions Detected

| Date | Description | Amount | Status |
|------|-------------|--------|--------|
| 01/05 | NETFLIX.COM | $15.99 | Review |
| 01/07 | ADOBE *CREATIVE | $54.99 | Review |

### Large Transactions (> $500)

| Date | Description | Amount |
|------|-------------|--------|
| 01/03 | CLIENT A PAYMENT | +$5,000 |
| 01/06 | OFFICE RENT | -$1,200 |

## Actions

- [ ] Review flagged subscriptions
- [ ] Categorize uncategorized transactions
- [ ] Reconcile with Odoo invoices
```

### 6.5 Subscription Detection Patterns

```yaml
# Subscription patterns for detection
subscriptions:
  - pattern: "netflix"
    name: "Netflix"
    category: "entertainment"
  - pattern: "spotify"
    name: "Spotify"
    category: "entertainment"
  - pattern: "adobe"
    name: "Adobe Creative Cloud"
    category: "software"
  - pattern: "notion"
    name: "Notion"
    category: "productivity"
  - pattern: "slack"
    name: "Slack"
    category: "communication"
  - pattern: "github"
    name: "GitHub"
    category: "development"
  - pattern: "aws"
    name: "Amazon Web Services"
    category: "infrastructure"
```

---

## 7. Ralph Wiggum Loop (Task Persistence)

### 7.1 Overview

The Ralph Wiggum pattern keeps Claude working on multi-step tasks until completion, rather than exiting after each step.

### 7.2 How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   RALPH WIGGUM LOOP                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Orchestrator creates task state file                       │
│      /Tasks/TASK_[id].md with status: in_progress               │
│                                                                  │
│   2. Claude starts working on task                              │
│                                                                  │
│   3. Claude attempts to exit                                    │
│                                                                  │
│   4. Stop hook intercepts exit:                                 │
│      - Check: Is task file in /Done/?                          │
│      - Check: Is max_iterations reached?                        │
│                                                                  │
│   5. If NOT complete and under max iterations:                  │
│      - Block exit                                               │
│      - Show Claude its previous output                          │
│      - Re-inject the prompt                                     │
│      - Continue loop                                            │
│                                                                  │
│   6. If complete OR max iterations:                             │
│      - Allow exit                                               │
│      - Log completion status                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Completion Strategies

**Strategy 1: File Movement (Recommended)**
- Task is complete when the task file moves to `/Done/`
- Natural part of workflow
- Orchestrator creates state file programmatically

**Strategy 2: Promise-Based**
- Claude outputs `<promise>TASK_COMPLETE</promise>`
- Simpler but requires Claude to remember

### 7.4 Task State File Template

**Tasks/TASK_[id].md:**
```markdown
---
task_id: task_20260107_001
created_at: 2026-01-07T10:30:00Z
status: in_progress
max_iterations: 10
current_iteration: 0
completion_strategy: file_movement
---

# Task: Process Invoice Request

## Objective

Generate and send invoice to Client A for January services.

## Steps Required

- [ ] Lookup client in Odoo
- [ ] Calculate invoice amount
- [ ] Create invoice in Odoo
- [ ] Generate PDF
- [ ] Create email approval request
- [ ] (After approval) Send email with invoice

## Completion Criteria

Task file moved to /Done/ when:
- Invoice created in Odoo
- Email approval request created
- OR max iterations reached (fail state)

## Iteration Log

| # | Timestamp | Action | Result |
|---|-----------|--------|--------|
| 1 | 10:30:00 | Started task | In progress |

---
*Managed by Ralph Wiggum Loop*
```

### 7.5 Ralph Wiggum Usage

```bash
# Start a Ralph Wiggum loop for a task
claude -p "Process the task in /Tasks/TASK_20260107_001.md. \
  Follow the steps in order. \
  When complete, move the task file to /Done/." \
  --max-iterations 10
```

### 7.6 Ralph Wiggum Skill Template

**skills/ralph-wiggum/SKILL.md:**
```markdown
# Ralph Wiggum Task Processor

## Purpose

Process multi-step tasks autonomously until completion.

## Instructions

1. Read the task file from /Tasks/
2. Check current iteration count
3. Execute the next incomplete step
4. Update the iteration log
5. Check completion criteria:
   - All steps complete? → Move to /Done/
   - Blocked by approval? → Create approval request, wait
   - Error occurred? → Log error, continue if recoverable
6. If not complete and under max iterations, continue

## Completion Signals

When all steps are complete:
1. Update task status to "complete"
2. Move task file to /Done/
3. Update Dashboard.md

## Error Handling

If a step fails:
1. Log the error in iteration log
2. Determine if recoverable
3. If recoverable: retry with backoff
4. If not recoverable: mark task as "failed", move to /Done/
```

---

## 8. Weekly CEO Briefing

### 8.1 Overview

The CEO Briefing is generated every Sunday night, summarizing the week's business activity.

### 8.2 Data Sources

| Source | Data Provided | Collection Method |
|--------|---------------|-------------------|
| **Odoo MCP** | Revenue, invoices, payments | API call |
| **Bank CSV** | Expenses, subscriptions | Parse from vault |
| **Done Folder** | Completed tasks | Scan folder |
| **Plans Folder** | Bottleneck analysis | Analyze duration |
| **Twitter MCP** | Social engagement | API call |

### 8.3 Briefing Generation Schedule

| Day | Time | Action |
|-----|------|--------|
| Sunday | 23:00 | Cron triggers CEO Briefing generator |
| Sunday | 23:05 | Collect data from all sources |
| Sunday | 23:15 | Claude generates briefing |
| Sunday | 23:30 | Briefing saved to /Briefings/ |
| Monday | Morning | Human reviews in Obsidian |

### 8.4 CEO Briefing Template

**Briefings/YYYY-MM-DD_Monday_Briefing.md:**
```markdown
---
generated: 2026-01-06T23:30:00Z
period: 2025-12-30 to 2026-01-05
version: gold
---

# Monday Morning CEO Briefing

## Executive Summary

[High-level 2-3 sentence summary of the week]

---

## 💰 Revenue (from Odoo)

| Metric | This Week | MTD | Target | Status |
|--------|-----------|-----|--------|--------|
| Revenue | $X,XXX | $X,XXX | $XX,XXX | 🟢 On Track |
| Invoices Sent | X | X | - | - |
| Invoices Paid | X | X | - | - |
| Outstanding | $X,XXX | - | - | ⚠️ Follow Up |

### Invoices This Week

| Customer | Amount | Status |
|----------|--------|--------|
| Client A | $X,XXX | Paid |
| Client B | $X,XXX | Outstanding |

---

## 💸 Expenses (from Bank CSV)

| Category | This Week | MTD | Budget | Status |
|----------|-----------|-----|--------|--------|
| Total Expenses | $X,XXX | $X,XXX | $X,XXX | 🟢 Under |
| Subscriptions | $XXX | $XXX | $XXX | 🟡 Review |
| One-time | $X,XXX | - | - | - |

### Subscription Audit

| Service | Monthly Cost | Last Used | Recommendation |
|---------|--------------|-----------|----------------|
| Notion | $15 | 45 days ago | ❌ Cancel |
| Slack | $12 | Active | ✅ Keep |
| Adobe | $55 | Active | ✅ Keep |

**Potential Savings:** $15/month by canceling unused subscriptions

---

## ✅ Completed Tasks (from Done folder)

| Task | Completed | Duration |
|------|-----------|----------|
| Client A invoice | Jan 3 | 1 day |
| Project Alpha milestone | Jan 4 | 3 days |
| Weekly social posts | Jan 5 | 1 day |

**Total Completed:** X tasks

---

## ⚠️ Bottlenecks (from Plans analysis)

| Task | Expected | Actual | Delay | Cause |
|------|----------|--------|-------|-------|
| Client B proposal | 2 days | 5 days | +3 days | Awaiting client input |

**Recommendation:** Follow up with Client B for requirements

---

## 📱 Social Media (from Twitter)

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Posts | X | X | +X |
| Impressions | X,XXX | X,XXX | +XX% |
| Engagements | XX | XX | +XX% |
| New Followers | X | X | +X |

**Top Post:** "[Tweet content preview...]"

---

## 🎯 Proactive Suggestions

### Cost Optimization
1. **Cancel Notion** - No activity in 45 days. Save $15/month.
   - [ACTION] Approval request created: /Pending_Approval/CANCEL_notion.md

### Revenue Opportunities
2. **Follow up on outstanding invoices** - $X,XXX outstanding
   - Client B: $X,XXX (7 days overdue)

### Upcoming Deadlines
3. **Project Alpha delivery** - Jan 15 (9 days)
4. **Quarterly tax prep** - Jan 31 (25 days)

---

## 📊 Week-over-Week Comparison

| Metric | Last Week | This Week | Trend |
|--------|-----------|-----------|-------|
| Revenue | $X,XXX | $X,XXX | 📈 +XX% |
| Expenses | $X,XXX | $X,XXX | 📉 -XX% |
| Tasks Done | X | X | 📈 +X |
| Response Time | Xh | Xh | 📈 Faster |

---

*Generated by AI Employee v3.0 (Gold)*
*Next briefing: [Next Monday date]*
```

### 8.5 Business Goals Template

**Business/Business_Goals.md:**
```markdown
---
last_updated: 2026-01-07
review_frequency: weekly
---

# Business Goals - Q1 2026

## Revenue Targets

| Period | Target | Current | Status |
|--------|--------|---------|--------|
| January | $10,000 | $4,500 | In Progress |
| Q1 | $30,000 | $4,500 | In Progress |

## Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |

## Active Projects

| Project | Due Date | Budget | Status |
|---------|----------|--------|--------|
| Project Alpha | Jan 15 | $2,000 | In Progress |
| Project Beta | Jan 30 | $3,500 | Not Started |

## Subscription Audit Rules

Flag for review if:
- No login/usage in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool

## Clients

| Client | Rate | Payment Terms |
|--------|------|---------------|
| Client A | $150/hr | Net 15 |
| Client B | $125/hr | Net 30 |
| Client C | $175/hr | Net 15 |
```

---

## 9. Error Recovery & Watchdog

### 9.1 Error Categories

| Category | Examples | Recovery Strategy |
|----------|----------|-------------------|
| **Transient** | Network timeout, API rate limit | Exponential backoff retry |
| **Authentication** | Expired token, revoked access | Alert human, pause operations |
| **Logic** | Claude misinterprets task | Human review queue |
| **Data** | Corrupted file, missing field | Quarantine + alert |
| **System** | Process crash, disk full | Watchdog restart + alert |

### 9.2 Watchdog Process

The watchdog monitors all critical processes and restarts them if they fail.

**Monitored Processes:**

| Process | Check Method | Restart Action |
|---------|--------------|----------------|
| Gmail Watcher | PID file check | Restart script |
| FileSystem Watcher | PID file check | Restart script |
| Finance Watcher | PID file check | Restart script |
| Cron service | `service cron status` | Alert only |

### 9.3 Watchdog Schedule

```
# Cron entry for watchdog
*/5 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_watchdog.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/watchdog.log 2>&1
```

### 9.4 Graceful Degradation

| Component Failed | System Behavior |
|------------------|-----------------|
| Gmail API down | Queue emails locally, process when restored |
| Odoo unavailable | Skip Odoo operations, log warning, continue |
| Twitter API down | Queue tweets, retry later |
| Claude quota exceeded | Skip processing, alert user |
| Bank CSV malformed | Quarantine file, alert user |

### 9.5 Health Status Template

**Dashboard.md (Health Section):**
```markdown
## System Health

| Component | Status | Last Check | Last Error |
|-----------|--------|------------|------------|
| Gmail Watcher | 🟢 Running | 10:30 | None |
| FileSystem Watcher | 🟢 Running | 10:30 | None |
| Finance Watcher | 🟢 Running | 10:30 | None |
| Claude Processor | 🟢 Running | 10:25 | None |
| Approval Executor | 🟢 Running | 10:30 | None |
| Odoo Connection | 🟢 Connected | 10:00 | None |
| Twitter Connection | 🟢 Connected | 10:00 | None |
| Watchdog | 🟢 Active | 10:30 | None |

**Last Watchdog Run:** 2026-01-07 10:30:00
**Restarts Today:** 0
```

---

## 10. Comprehensive Audit Logging

### 10.1 Audit Log Requirements

Every action must be logged with:
- Timestamp
- Action type
- Actor (claude_code, human, system)
- Target (recipient, file, etc.)
- Parameters
- Approval status
- Result

### 10.2 Audit Log Format

**Audit/YYYY-MM-DD.json:**
```json
{
  "entries": [
    {
      "timestamp": "2026-01-07T10:30:00Z",
      "action_type": "email_send",
      "actor": "claude_code",
      "target": "client@example.com",
      "parameters": {
        "subject": "Invoice #123",
        "has_attachment": true
      },
      "approval_status": "approved",
      "approved_by": "human",
      "approved_at": "2026-01-07T10:25:00Z",
      "result": "success",
      "result_details": {
        "message_id": "abc123"
      }
    },
    {
      "timestamp": "2026-01-07T11:00:00Z",
      "action_type": "odoo_create_invoice",
      "actor": "claude_code",
      "target": "Client A",
      "parameters": {
        "amount": 1500.00,
        "currency": "USD"
      },
      "approval_status": "auto_approved",
      "approved_by": "system",
      "result": "success",
      "result_details": {
        "invoice_id": "INV-2026-001"
      }
    },
    {
      "timestamp": "2026-01-07T12:00:00Z",
      "action_type": "tweet_post",
      "actor": "claude_code",
      "target": "twitter_timeline",
      "parameters": {
        "content": "Excited to share...",
        "character_count": 142
      },
      "approval_status": "approved",
      "approved_by": "human",
      "approved_at": "2026-01-07T11:55:00Z",
      "result": "success",
      "result_details": {
        "tweet_id": "1234567890"
      }
    }
  ]
}
```

### 10.3 Audit Log Retention

| Log Type | Retention | Location |
|----------|-----------|----------|
| Audit logs | 90 days | `/Audit/` |
| Activity logs | 30 days | `/Logs/` |
| Cron logs | 7 days | `/Logs/cron_*.log` |

---

## 11. Functional Requirements (Gold Phase)

### 11.1 Finance Watcher

#### FR-G1: Bank CSV Import
- **Description:** Monitor Transactions folder for new bank CSV files
- **Trigger:** New `.csv` file in `/Business/Transactions/`
- **Process:**
  1. Detect new CSV file
  2. Parse transactions
  3. Detect subscriptions using patterns
  4. Flag large transactions
  5. Create action file in `/Needs_Action/`
- **Output:** Finance review file with summaries and flags

### 11.2 Odoo Integration

#### FR-G2: Odoo MCP Server
- **Description:** MCP server for Odoo JSON-RPC operations
- **Capabilities:** Create/read invoices, payments, customers, accounts
- **Authentication:** API key from config file
- **Error Handling:** Graceful failure with logging

#### FR-G3: Odoo Data Sync
- **Description:** Periodic sync of Odoo data to vault
- **Frequency:** Every 6 hours
- **Data:** Invoices, customers, account balances
- **Output:** Markdown files in `/Business/Odoo/`

### 11.3 Twitter/X Integration

#### FR-G4: Twitter MCP Server
- **Description:** MCP server for Twitter API v2 operations
- **Capabilities:** Post tweets, get engagement, list tweets
- **Approval:** All posts require human approval
- **Rate Limits:** Respect Twitter API limits

#### FR-G5: Social Media Summary
- **Description:** Generate engagement summaries
- **Frequency:** Daily
- **Output:** Update `/Social/Twitter/engagement.md`

### 11.4 CEO Briefing

#### FR-G6: Weekly Briefing Generation
- **Description:** Generate comprehensive business briefing
- **Trigger:** Cron job Sunday 23:00
- **Data Sources:** Odoo, Bank CSV, Done folder, Plans, Twitter
- **Output:** `/Briefings/YYYY-MM-DD_Monday_Briefing.md`

### 11.5 Ralph Wiggum Loop

#### FR-G7: Task Persistence
- **Description:** Keep Claude working on multi-step tasks until completion
- **Implementation:** Stop hook that checks task status
- **Completion:** Task file moved to `/Done/`
- **Max Iterations:** Configurable (default 10)

### 11.6 Watchdog

#### FR-G8: Process Monitoring
- **Description:** Monitor and restart failed watcher processes
- **Check Frequency:** Every 5 minutes
- **Actions:** Restart failed processes, alert on persistent failures
- **Logging:** Health status to Dashboard and logs

### 11.7 Audit Logging

#### FR-G9: Comprehensive Audit Trail
- **Description:** Log all system actions in structured format
- **Format:** JSON with standard schema
- **Retention:** 90 days
- **Location:** `/Audit/YYYY-MM-DD.json`

---

## 12. Non-Functional Requirements (Gold)

### 12.1 Security

#### NFR-G1: Odoo Credentials
- API key stored in `credentials/odoo_config.json`
- Never stored in vault
- File excluded from git

#### NFR-G2: Twitter Credentials
- OAuth tokens in `credentials/twitter_credentials.json`
- Never stored in vault
- File excluded from git

#### NFR-G3: Audit Integrity
- Audit logs append-only
- No modification of historical entries
- Checksums for integrity verification (optional)

### 12.2 Reliability

#### NFR-G4: Watchdog Monitoring
- All critical processes monitored
- Auto-restart on failure
- Alert after 3 consecutive failures

#### NFR-G5: Graceful Degradation
- System continues if non-critical components fail
- Clear error messages in Dashboard
- Queue operations for later retry

### 12.3 Performance

#### NFR-G6: Briefing Generation
- Complete within 15 minutes
- Handle large data volumes (1000+ transactions)

#### NFR-G7: Odoo API Calls
- Timeout after 30 seconds
- Retry with exponential backoff

---

## 13. Technical Specifications (Gold)

### 13.1 New Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # Existing (Silver)
    "google-auth-oauthlib",
    "google-auth-httplib2",
    "google-api-python-client",
    "python-dotenv",
    "watchdog>=3.0.0",
    "email-validator>=2.0.0",
    "tenacity>=8.0.0",
    
    # New (Gold)
    "xmlrpc-client",          # Odoo JSON-RPC (built-in, but explicit)
    "tweepy>=4.14.0",         # Twitter API
    "pandas>=2.0.0",          # CSV parsing for bank imports
    "schedule>=1.2.0",        # Optional: Python-based scheduling
]
```

### 13.2 Cron Configuration (Gold)

```bash
# Existing (Silver)
*/2 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_gmail_watcher.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_gmail.log 2>&1
*/1 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_filesystem_watcher.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_filesystem.log 2>&1
*/5 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_claude_processor.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_processor.log 2>&1
*/1 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_approval_executor.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_executor.log 2>&1

# New (Gold)
*/5 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_finance_watcher.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_finance.log 2>&1
*/5 * * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_watchdog.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/watchdog.log 2>&1
0 */6 * * * cd ~/vibe-coding-projects/ai-employee && python scripts/run_odoo_sync.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_odoo.log 2>&1
0 23 * * 0 cd ~/vibe-coding-projects/ai-employee && python scripts/run_ceo_briefing.py >> /mnt/d/AI_EMPLOYEE_VAULT/Logs/cron_briefing.log 2>&1
```

### 13.3 Environment Variables (Gold)

```bash
# .env additions for Gold

# Odoo Configuration
ODOO_URL=http://localhost:8069
ODOO_DATABASE=ai_employee_db
ODOO_USERNAME=admin
ODOO_API_KEY=your_api_key

# Twitter Configuration
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Watchdog Configuration
WATCHDOG_CHECK_INTERVAL=300
WATCHDOG_MAX_RESTART_ATTEMPTS=3

# Ralph Wiggum Configuration
RALPH_MAX_ITERATIONS=10
RALPH_COMPLETION_STRATEGY=file_movement
```

---

## 14. Gold Phase Deliverables

### 14.1 Required Deliverables

**Vault Updates:**
- [ ] Create `Business\` folder structure
- [ ] Create `Business\Business_Goals.md`
- [ ] Create `Business\Transactions\` for bank CSVs
- [ ] Create `Business\Odoo\` for Odoo sync data
- [ ] Create `Social\Twitter\` folder structure
- [ ] Create `Briefings\` folder
- [ ] Create `Audit\` folder
- [ ] Update `Dashboard.md` with health monitoring section
- [ ] Update `Company_Handbook.md` with Gold rules

**Odoo Setup:**
- [ ] Install Odoo Community Edition 19+
- [ ] Create database for AI Employee
- [ ] Configure API access
- [ ] Create test customers and invoices

**Code Deliverables:**
- [ ] `src/watchers/finance_watcher.py`
- [ ] `src/mcp/odoo_mcp.py`
- [ ] `src/mcp/twitter_mcp.py`
- [ ] `src/briefings/ceo_briefing.py`
- [ ] `src/briefings/data_collectors.py`
- [ ] `src/hooks/ralph_wiggum.py`
- [ ] `src/watchdog/process_monitor.py`
- [ ] `src/utils/audit_logger.py`
- [ ] `scripts/run_finance_watcher.py`
- [ ] `scripts/run_odoo_sync.py`
- [ ] `scripts/run_ceo_briefing.py`
- [ ] `scripts/run_watchdog.py`

**Skills:**
- [ ] `skills/ceo-briefing/SKILL.md`
- [ ] `skills/social-poster/SKILL.md`
- [ ] `skills/ralph-wiggum/SKILL.md` (or use plugin)

**Documentation:**
- [ ] `ARCHITECTURE.md` - System architecture documentation
- [ ] `README.md` - Updated with Gold features
- [ ] Demo video (5-10 minutes)

**Configuration:**
- [ ] Update `.env` with Gold variables
- [ ] Configure Twitter API credentials
- [ ] Configure Odoo connection
- [ ] Update crontab with Gold jobs

### 14.2 Acceptance Criteria

1. **Odoo Integration:**
   - Successfully connect to Odoo via JSON-RPC
   - Create invoices programmatically
   - Retrieve financial data for CEO Briefing
   - Sync data to vault periodically

2. **Twitter/X Integration:**
   - Post tweets with human approval
   - Retrieve engagement metrics
   - Generate social media summaries

3. **Finance Watcher:**
   - Detect new bank CSV files
   - Parse transactions correctly
   - Identify subscriptions
   - Flag large transactions

4. **CEO Briefing:**
   - Generate comprehensive briefing weekly
   - Include all data sources
   - Provide actionable recommendations

5. **Ralph Wiggum Loop:**
   - Keep Claude working on multi-step tasks
   - Detect task completion correctly
   - Respect max iteration limit

6. **Watchdog:**
   - Monitor all watcher processes
   - Restart failed processes
   - Log health status

7. **Audit Logging:**
   - Log all actions in structured format
   - Maintain 90-day retention
   - Include all required fields

---

## 15. User Stories (Gold)

### US-G1: Weekly Business Review
**As a** business owner  
**I want** a comprehensive weekly briefing generated automatically  
**So that** I can start Monday with full visibility into my business

**Acceptance Criteria:**
- Briefing generated every Sunday night
- Includes revenue, expenses, tasks, bottlenecks
- Provides actionable recommendations
- Available in Obsidian Monday morning

### US-G2: Automated Invoicing
**As a** freelancer  
**I want** Claude to create invoices in Odoo based on my requests  
**So that** I can focus on client work instead of admin

**Acceptance Criteria:**
- Request invoice via email or file drop
- Claude creates invoice in Odoo
- Invoice details logged in vault
- Human approval for sending

### US-G3: Social Media Management
**As a** business owner  
**I want** to schedule and post tweets with AI assistance  
**So that** I maintain social presence without manual effort

**Acceptance Criteria:**
- Draft tweets based on business activity
- Human approval before posting
- Track engagement metrics
- Summarize in CEO Briefing

### US-G4: Expense Tracking
**As a** business owner  
**I want** bank transactions automatically analyzed  
**So that** I can identify unused subscriptions and control costs

**Acceptance Criteria:**
- Drop bank CSV in vault
- Automatic parsing and categorization
- Flag subscriptions for review
- Include in CEO Briefing

### US-G5: Multi-Step Task Completion
**As a** user  
**I want** Claude to complete complex tasks autonomously  
**So that** I don't need to prompt for each step

**Acceptance Criteria:**
- Define multi-step task
- Claude works through steps automatically
- Pauses for approval when needed
- Completes or reports failure

---

## 16. Operational Guidelines (Gold)

### 16.1 Human Oversight Schedule

| Frequency | Action | Duration |
|-----------|--------|----------|
| **Continuous** | Review approval requests | As needed |
| **Daily** | Check Dashboard health status | 2 minutes |
| **Weekly** | Review CEO Briefing | 15 minutes |
| **Weekly** | Review audit logs | 10 minutes |
| **Monthly** | Full system audit | 1 hour |
| **Quarterly** | Security review | 2 hours |

### 16.2 Odoo Best Practices

- Regularly backup Odoo database
- Review auto-created invoices
- Reconcile Odoo with bank statements monthly
- Keep customer data updated

### 16.3 Twitter Best Practices

- Review all tweets before approval
- Monitor engagement for unusual activity
- Respond to mentions manually (Gold doesn't auto-reply)
- Keep brand voice consistent

### 16.4 When to Intervene

- Watchdog reports persistent failures
- CEO Briefing shows concerning trends
- Unusual transactions in bank import
- Twitter engagement drops significantly
- Odoo connection fails repeatedly

---

## 17. Success Metrics (Gold)

### 17.1 Business Metrics

| Metric | Target |
|--------|--------|
| Invoice generation time | < 5 minutes |
| CEO Briefing accuracy | > 95% |
| Subscription detection rate | > 90% |
| Tweet approval rate | > 80% |

### 17.2 Reliability Metrics

| Metric | Target |
|--------|--------|
| System uptime | > 99% |
| Watchdog recovery rate | > 95% |
| Failed restarts | < 5% |
| Data sync success | > 99% |

### 17.3 Efficiency Metrics

| Metric | Target |
|--------|--------|
| Ralph Wiggum completion rate | > 90% |
| Average task iterations | < 5 |
| Claude quota per briefing | < 3 calls |

---

## 18. Risks and Mitigations (Gold)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Odoo server down | High | Graceful degradation, queue operations |
| Twitter API rate limited | Medium | Respect limits, queue posts |
| Bank CSV format changes | Medium | Flexible parsing, manual fallback |
| Ralph Wiggum infinite loop | High | Max iteration limit, timeout |
| Watchdog fails to restart | Medium | Alert human, manual intervention |
| Audit log corruption | High | Append-only, backups |
| Incorrect CEO Briefing | Medium | Human review, data validation |

---

## 19. Future Phases

### Platinum Tier: Always-On Cloud
- Cloud deployment (24/7 operation)
- Cloud + Local split (delegation)
- Vault sync via Git
- Enhanced security for cloud operations

### Beyond: Advanced Features
- Multi-user support
- Voice interface
- Mobile app integration
- Advanced analytics and ML predictions

---

## 20. Appendix

### Appendix A: Odoo Installation Guide

**Option 1: Docker (Recommended for Development)**
```bash
# Pull Odoo image
docker pull odoo:19

# Create PostgreSQL container
docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo \
  -e POSTGRES_DB=postgres --name db postgres:15

# Run Odoo
docker run -p 8069:8069 --name odoo --link db:db -t odoo:19
```

**Option 2: Windows Installation**
1. Download Odoo 19 Community from odoo.com
2. Run installer
3. Configure PostgreSQL connection
4. Access at http://localhost:8069

### Appendix B: Twitter API Setup

1. Create Twitter Developer Account at developer.twitter.com
2. Create a new Project and App
3. Generate API keys and tokens
4. Enable OAuth 2.0
5. Request appropriate access level (Basic/Pro)

### Appendix C: Bank CSV Format Examples

**Generic Format:**
```csv
Date,Description,Amount,Balance
01/05/2026,NETFLIX.COM,-15.99,1234.56
01/06/2026,CLIENT A PAYMENT,5000.00,6234.56
```

**Chase Format:**
```csv
Posting Date,Description,Amount,Type,Balance
01/05/2026,NETFLIX.COM,-15.99,DEBIT,1234.56
```

### Appendix D: Environment Setup Checklist (Gold)

**Odoo Setup:**
1. [ ] Install Odoo Community 19+
2. [ ] Create database
3. [ ] Create admin user
4. [ ] Generate API key
5. [ ] Test API connection
6. [ ] Create test customer
7. [ ] Create test invoice

**Twitter Setup:**
1. [ ] Create developer account
2. [ ] Create project and app
3. [ ] Generate API keys
4. [ ] Generate access tokens
5. [ ] Generate bearer token
6. [ ] Test API connection
7. [ ] Post test tweet (delete after)

**Vault Setup:**
1. [ ] Create `Business\` folder structure
2. [ ] Create `Social\Twitter\` structure
3. [ ] Create `Briefings\` folder
4. [ ] Create `Audit\` folder
5. [ ] Create `Business_Goals.md`
6. [ ] Update `Dashboard.md`
7. [ ] Update `Company_Handbook.md`

**Code Setup:**
1. [ ] Install new dependencies
2. [ ] Create all new source files
3. [ ] Create all new scripts
4. [ ] Create new skills
5. [ ] Update crontab
6. [ ] Test each component individually
7. [ ] Test end-to-end flow

---

**Document Control:**
- Author: AI Employee Project Team
- Status: Draft v3.0
- Phase: Gold (Autonomous Employee)
- Key Features: Odoo Integration, Twitter/X, CEO Briefing, Ralph Wiggum Loop, Watchdog
