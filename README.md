# AI Employee - Gold Tier

**Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

## Overview

The Personal AI Employee is an autonomous AI agent system that proactively manages personal and business affairs. Unlike traditional chatbots that wait for user input, this system actively monitors communications, finances, and social media—then takes action or requests approval when needed.

**Phase:** Gold (Autonomous Employee)

## Gold Tier Features

| Component | Description |
|-----------|-------------|
| **Finance Watcher** | Monitor bank CSV imports, detect subscriptions, flag large transactions |
| **Odoo MCP** | Full accounting integration - invoices, payments, customers, balances |
| **Twitter/X MCP** | Social media posting (with approval) and engagement tracking |
| **CEO Briefing** | Weekly business intelligence report with actionable insights |
| **Ralph Wiggum Loop** | Task persistence for autonomous multi-step completion |
| **Watchdog** | Process monitoring with auto-restart and health reporting |
| **Audit Logging** | Comprehensive structured logging with 90-day retention |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PERCEPTION LAYER                             │
│  Gmail Watcher │ FileSystem Watcher │ Finance Watcher           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                     REASONING LAYER                              │
│  Claude Processor (with Ralph Wiggum Loop)                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                  HUMAN-IN-THE-LOOP LAYER                         │
│  Obsidian Vault: Pending_Approval → Approved/Rejected           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ACTION LAYER                                │
│  Email MCP │ Odoo MCP │ Twitter MCP                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│               BUSINESS INTELLIGENCE LAYER                        │
│  CEO Briefing Generator (Weekly)                                │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Obsidian (for vault management)
- Gmail API credentials
- Odoo Community Edition 19+ (for accounting features)
- Twitter Developer API credentials (for social features)

## Quick Start

### 1. Clone and Setup

```bash
cd ~/vibe-coding-projects/ai-employee-gold
uv sync
cp .env.example .env
# Edit .env with your configuration
```

### 2. Configure Credentials

```bash
# Gmail (required)
# Place gmail_credentials.json in credentials/

# Odoo (for accounting features)
# Create credentials/odoo_config.json

# Twitter (for social features)
# Create credentials/twitter_credentials.json
```

### 3. Setup Obsidian Vault

Create vault at `D:\AI_EMPLOYEE_VAULT` (Windows) or configure `VAULT_PATH` in `.env`.

Required folder structure:
```
AI_EMPLOYEE_VAULT/
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── Plans/
├── Pending_Approval/
├── Approved/
├── Rejected/
├── Done/
├── Logs/
├── Business/
│   ├── Transactions/
│   └── Odoo/
├── Social/
│   └── Twitter/
├── Briefings/
├── Audit/
└── Tasks/
```

### 4. Run Components

```bash
# Individual watchers
uv run python scripts/run_gmail_watcher.py
uv run python scripts/run_filesystem_watcher.py
uv run python scripts/run_finance_watcher.py

# Processor and executor
uv run python scripts/run_claude_processor.py
uv run python scripts/run_approval_executor.py

# Monitoring
uv run python scripts/run_watchdog.py

# Business intelligence
uv run python scripts/run_ceo_briefing.py
```

### 5. Configure Cron (Automated Operation)

```bash
# Edit crontab
crontab -e

# Add these entries:
*/2 * * * * cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_gmail_watcher.py
*/1 * * * * cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_filesystem_watcher.py
*/5 * * * * cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_finance_watcher.py
*/5 * * * * cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_claude_processor.py
*/1 * * * * cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_approval_executor.py
*/5 * * * * cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_watchdog.py
0 */6 * * * cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_odoo_sync.py
0 23 * * 0 cd ~/vibe-coding-projects/ai-employee-gold && uv run python scripts/run_ceo_briefing.py
```

## Project Structure

```
ai-employee-gold/
├── src/
│   ├── watchers/        # Gmail, FileSystem, Finance watchers
│   ├── mcp/             # Email, Odoo, Twitter MCP servers
│   ├── processors/      # Claude processor
│   ├── executors/       # Approval executor
│   ├── briefings/       # CEO Briefing generator
│   ├── hooks/           # Ralph Wiggum loop
│   ├── watchdog/        # Process monitor
│   └── utils/           # Logging, vault helpers, audit
├── scripts/             # Runner scripts
├── skills/              # Claude Code skills
├── tests/               # Test suite
├── credentials/         # API credentials (gitignored)
├── PRD.md              # Product Requirements Document
├── TASKS.md            # Implementation task list
└── README.md           # This file
```

## Documentation

- [PRD.md](PRD.md) - Full product requirements and specifications
- [TASKS.md](TASKS.md) - Implementation task breakdown

## Development Status

See [TASKS.md](TASKS.md) for current progress.

## License

Private - All rights reserved.
