# Gold Phase - Implementation Tasks

**Status:** Not Started
**Prerequisites:** Silver phase complete ✅
**Blockers:** Odoo 19 CE not installed, Twitter API credentials not obtained

---

## Phase 0: External Setup (Manual / Outside Codebase)

> These are prerequisites that must be done before certain code tasks can begin.

### 0.1 Install Odoo Community Edition 19+
- [ ] **0.1.1** Pull Odoo 19 Docker image (`docker pull odoo:19`)
- [ ] **0.1.2** Create PostgreSQL container (`postgres:15`)
- [ ] **0.1.3** Run Odoo container linked to PostgreSQL, exposed on port 8069
- [ ] **0.1.4** Access `http://localhost:8069` and complete initial setup wizard
- [ ] **0.1.5** Create database `ai_employee_db`
- [ ] **0.1.6** Install Invoicing module
- [ ] **0.1.7** Create admin API key (Settings → Users → API Keys)
- [ ] **0.1.8** Create test customer "Client A"
- [ ] **0.1.9** Create test invoice for validation
- [ ] **0.1.10** Save credentials to `credentials/odoo_config.json`

**Blocks:** Phase 2 (Odoo MCP), Phase 4 (CEO Briefing Odoo data)

### 0.2 Obtain Twitter API Credentials
- [ ] **0.2.1** Create Twitter Developer Account at developer.twitter.com
- [ ] **0.2.2** Create a new Project
- [ ] **0.2.3** Create an App within the project
- [ ] **0.2.4** Generate API Key and API Secret
- [ ] **0.2.5** Generate Access Token and Access Token Secret
- [ ] **0.2.6** Generate Bearer Token
- [ ] **0.2.7** Test API connection (post + delete a test tweet)
- [ ] **0.2.8** Save credentials to `credentials/twitter_credentials.json`

**Blocks:** Phase 3 (Twitter MCP), Phase 4 (CEO Briefing social data)

---

## Phase 1: Foundation (No External Dependencies)

> Can be started immediately. No Odoo or Twitter needed.

### 1.1 Vault Folder Structure
- [ ] **1.1.1** Create `Business/` folder in vault
- [ ] **1.1.2** Create `Business/Transactions/` subfolder (for bank CSVs)
- [ ] **1.1.3** Create `Business/Odoo/` subfolder (for sync data)
- [ ] **1.1.4** Create `Business/Business_Goals.md` from PRD template (move existing `Business_Goals.md` into `Business/`)
- [ ] **1.1.5** Create `Social/` folder in vault
- [ ] **1.1.6** Create `Social/Twitter/` subfolder
- [ ] **1.1.7** Create `Social/Twitter/scheduled_posts.md` (empty template)
- [ ] **1.1.8** Create `Social/Twitter/posted.md` (empty template)
- [ ] **1.1.9** Create `Social/Twitter/engagement.md` (empty template)
- [ ] **1.1.10** Create `Briefings/` folder in vault
- [ ] **1.1.11** Create `Audit/` folder in vault
- [ ] **1.1.12** Create `Tasks/` folder in vault (for Ralph Wiggum task state files)
- [ ] **1.1.13** Update `Dashboard.md` — add System Health section from PRD template
- [ ] **1.1.14** Update `Company_Handbook.md` — add Gold phase rules (Odoo, Twitter, finance policies)

### 1.2 Project Configuration Updates
- [ ] **1.2.1** Update `pyproject.toml` — add Gold dependencies: `tweepy>=4.14.0`, `pandas>=2.0.0`, `schedule>=1.2.0`
- [ ] **1.2.2** Update `.env` template — add Odoo, Twitter, Watchdog, Ralph Wiggum variables
- [ ] **1.2.3** Update `.gitignore` — ensure `credentials/odoo_config.json`, `credentials/twitter_credentials.json` are excluded
- [ ] **1.2.4** Run `uv sync` to install new dependencies

### 1.3 Audit Logger (`src/utils/audit_logger.py`)
- [ ] **1.3.1** Create `src/utils/audit_logger.py`
- [ ] **1.3.2** Implement `AuditLogger` class with:
  - `log_action(action_type, actor, target, parameters, approval_status, result, result_details)`
  - JSON append to `/Audit/YYYY-MM-DD.json`
  - Append-only writes (never modify existing entries)
- [ ] **1.3.3** Implement 90-day retention cleanup method
- [ ] **1.3.4** Write tests `tests/test_audit_logger.py`
- [ ] **1.3.5** Integrate audit logger into existing `approval_executor.py` (log email sends)

### 1.4 Finance Watcher (`src/watchers/finance_watcher.py`)
- [ ] **1.4.1** Create `src/watchers/finance_watcher.py` extending `BaseWatcher`
- [ ] **1.4.2** Implement CSV detection — watch `Business/Transactions/` for new `.csv` files
- [ ] **1.4.3** Implement CSV parsing — handle Generic, Chase, Bank of America formats (auto-detect columns)
- [ ] **1.4.4** Implement subscription detection — match transaction descriptions against known patterns (Netflix, Spotify, Adobe, etc.)
- [ ] **1.4.5** Implement large transaction flagging (configurable threshold, default >$500)
- [ ] **1.4.6** Generate `Needs_Action/FINANCE_[date]_[hash].md` with summary, flagged items, and action checklist
- [ ] **1.4.7** Track processed CSV files to avoid re-processing (append to `Logs/processed_finances.txt`)
- [ ] **1.4.8** Create `scripts/run_finance_watcher.py`
- [ ] **1.4.9** Write tests `tests/test_finance_watcher.py` — include sample CSVs for each supported format
- [ ] **1.4.10** Manual test: drop a sample CSV in vault and verify output

### 1.5 Watchdog Process Monitor (`src/watchdog/process_monitor.py`)
- [ ] **1.5.1** Create `src/watchdog/__init__.py`
- [ ] **1.5.2** Create `src/watchdog/process_monitor.py`
- [ ] **1.5.3** Implement `ProcessMonitor` class:
  - Check PID files for Gmail Watcher, FileSystem Watcher, Finance Watcher
  - Detect stale PID files (process no longer running)
  - Restart failed watchers via subprocess
- [ ] **1.5.4** Implement failure tracking — alert after 3 consecutive restart failures
- [ ] **1.5.5** Implement health status output — update Dashboard.md health section
- [ ] **1.5.6** Implement logging to `Logs/watchdog.log`
- [ ] **1.5.7** Create `scripts/run_watchdog.py`
- [ ] **1.5.8** Write tests `tests/test_watchdog.py`
- [ ] **1.5.9** Manual test: kill a watcher process and verify watchdog restarts it

### 1.6 Ralph Wiggum Loop (`src/hooks/ralph_wiggum.py`)
- [ ] **1.6.1** Create `src/hooks/__init__.py`
- [ ] **1.6.2** Create `src/hooks/ralph_wiggum.py`
- [ ] **1.6.3** Implement stop hook logic:
  - Read task state file from `/Tasks/TASK_[id].md`
  - Check if task file has been moved to `/Done/`
  - Check if `max_iterations` reached
  - If not complete and under limit: block exit, re-inject prompt
  - If complete or over limit: allow exit
- [ ] **1.6.4** Implement iteration logging — update task file's iteration log table
- [ ] **1.6.5** Create `skills/ralph-wiggum/SKILL.md` from PRD template
- [ ] **1.6.6** Write tests `tests/test_ralph_wiggum.py`
- [ ] **1.6.7** Manual test: create a multi-step task and verify loop behavior

---

## Phase 2: Odoo Integration (Requires Phase 0.1 Complete)

### 2.1 Odoo MCP Server (`src/mcp/odoo_mcp.py`)
- [ ] **2.1.1** Create `src/mcp/odoo_mcp.py`
- [ ] **2.1.2** Implement Odoo JSON-RPC connection class:
  - `authenticate()` — connect using API key
  - Connection pooling / session reuse
  - 30-second timeout per request
  - Exponential backoff retry (via tenacity)
- [ ] **2.1.3** Implement `create_invoice(customer_id, lines, due_date)`
- [ ] **2.1.4** Implement `get_invoices(period, status)` — list invoices for period
- [ ] **2.1.5** Implement `get_invoice(invoice_id)` — single invoice details
- [ ] **2.1.6** Implement `create_payment(invoice_id, amount, date)`
- [ ] **2.1.7** Implement `get_customers()` — list all customers
- [ ] **2.1.8** Implement `get_customer(customer_id)` — single customer details
- [ ] **2.1.9** Implement `get_account_balance(account_id)` — check balances
- [ ] **2.1.10** Implement `get_journal_entries(period)` — transactions for reporting
- [ ] **2.1.11** Implement graceful failure — return error objects instead of crashing
- [ ] **2.1.12** Integrate audit logging for all Odoo operations
- [ ] **2.1.13** Write tests `tests/test_odoo_mcp.py` (mock JSON-RPC calls)
- [ ] **2.1.14** Integration test: create invoice in real Odoo, verify via UI

### 2.2 Odoo Data Sync
- [ ] **2.2.1** Create `src/briefings/data_collectors.py` — Odoo data collector
- [ ] **2.2.2** Implement sync logic:
  - Fetch recent invoices → write `Business/Odoo/invoices.md`
  - Fetch customer list → write `Business/Odoo/customers.md`
  - Fetch account balances → write `Business/Odoo/accounts.md`
- [ ] **2.2.3** Add YAML frontmatter with `last_synced` timestamp
- [ ] **2.2.4** Create `scripts/run_odoo_sync.py`
- [ ] **2.2.5** Test sync: run script and verify markdown files in vault

---

## Phase 3: Twitter/X Integration (Requires Phase 0.2 Complete)

### 3.1 Twitter MCP Server (`src/mcp/twitter_mcp.py`)
- [ ] **3.1.1** Create `src/mcp/twitter_mcp.py`
- [ ] **3.1.2** Implement Twitter API v2 client using tweepy:
  - OAuth 2.0 authentication
  - Rate limit handling (respect API limits, queue when exceeded)
- [ ] **3.1.3** Implement `post_tweet(content)` — post a tweet (always requires prior approval)
- [ ] **3.1.4** Implement `get_my_tweets(count)` — list recent tweets
- [ ] **3.1.5** Implement `get_engagement(tweet_id)` — get metrics for a tweet
- [ ] **3.1.6** Implement `get_mentions(count)` — list recent mentions
- [ ] **3.1.7** Implement `schedule_tweet(content, scheduled_time)` — queue for later posting
- [ ] **3.1.8** Implement tweet approval workflow:
  - Generate `Pending_Approval/TWEET_[id].md` from template
  - On approval, execute via `post_tweet`
  - Log to `Social/Twitter/posted.md`
- [ ] **3.1.9** Integrate audit logging for all Twitter operations
- [ ] **3.1.10** Write tests `tests/test_twitter_mcp.py` (mock tweepy calls)
- [ ] **3.1.11** Integration test: post and delete a test tweet

### 3.2 Social Media Summary
- [ ] **3.2.1** Add Twitter data collector to `src/briefings/data_collectors.py`
- [ ] **3.2.2** Implement engagement summary generation → update `Social/Twitter/engagement.md`
- [ ] **3.2.3** Create `skills/social-poster/SKILL.md` from PRD template
- [ ] **3.2.4** Test: generate summary from real Twitter data

---

## Phase 4: Business Intelligence (Requires Phases 1-3)

### 4.1 CEO Briefing Generator (`src/briefings/ceo_briefing.py`)
- [ ] **4.1.1** Create `src/briefings/__init__.py`
- [ ] **4.1.2** Create `src/briefings/ceo_briefing.py`
- [ ] **4.1.3** Implement data collection orchestrator — gather from all sources:
  - Odoo MCP → revenue, invoices, payments (graceful skip if unavailable)
  - Bank CSV data → expenses, subscriptions (from parsed vault data)
  - Done folder → completed tasks count and details
  - Plans folder → bottleneck analysis (compare expected vs actual duration)
  - Twitter MCP → social engagement metrics (graceful skip if unavailable)
- [ ] **4.1.4** Implement briefing markdown generation from PRD template
- [ ] **4.1.5** Implement week-over-week comparison (requires storing previous week's data)
- [ ] **4.1.6** Implement proactive suggestions logic:
  - Unused subscription detection (no activity in 30+ days)
  - Outstanding invoice follow-ups
  - Upcoming deadlines from Plans
- [ ] **4.1.7** Output to `Briefings/YYYY-MM-DD_Monday_Briefing.md`
- [ ] **4.1.8** Create `scripts/run_ceo_briefing.py`
- [ ] **4.1.9** Create `skills/ceo-briefing/SKILL.md` from PRD template
- [ ] **4.1.10** Test: generate briefing with available data sources (gracefully handle missing ones)

---

## Phase 5: Integration, Cron & Hardening

### 5.1 Cron Configuration
- [ ] **5.1.1** Add Finance Watcher to crontab (`*/5 * * * *`)
- [ ] **5.1.2** Add Watchdog to crontab (`*/5 * * * *`)
- [ ] **5.1.3** Add Odoo Sync to crontab (`0 */6 * * *`) — only after Odoo is set up
- [ ] **5.1.4** Add CEO Briefing to crontab (`0 23 * * 0` — Sunday 23:00)
- [ ] **5.1.5** Verify all cron jobs run without errors

### 5.2 Graceful Degradation
- [ ] **5.2.1** Verify system continues if Odoo is unavailable (skip Odoo operations, log warning)
- [ ] **5.2.2** Verify system continues if Twitter API is down (queue tweets, retry later)
- [ ] **5.2.3** Verify system continues if Gmail API is down (queue emails locally)
- [ ] **5.2.4** Verify system continues if Claude quota is exceeded (skip processing, alert user)
- [ ] **5.2.5** Verify malformed bank CSV is quarantined with user alert

### 5.3 End-to-End Testing
- [ ] **5.3.1** Test: Drop bank CSV → Finance Watcher detects → creates Needs_Action file → Claude processes → generates plan
- [ ] **5.3.2** Test: Email requests invoice → Claude creates Odoo invoice → approval request → human approves → email sent
- [ ] **5.3.3** Test: Claude drafts tweet → approval request → human approves → tweet posted → logged
- [ ] **5.3.4** Test: CEO Briefing generates with all available data sources
- [ ] **5.3.5** Test: Kill a watcher → Watchdog detects → restarts it
- [ ] **5.3.6** Test: Multi-step task via Ralph Wiggum loop completes autonomously
- [ ] **5.3.7** Verify all actions appear in Audit logs

### 5.4 Dashboard & Handbook Updates
- [ ] **5.4.1** Final Dashboard.md update — verify health section reflects all Gold components
- [ ] **5.4.2** Final Company_Handbook.md update — ensure all Gold policies documented
- [ ] **5.4.3** Verify Obsidian renders all new vault files correctly

---

## Phase 6: Documentation & Delivery

### 6.1 Documentation
- [ ] **6.1.1** Create `ARCHITECTURE.md` — system architecture with diagrams
- [ ] **6.1.2** Update `README.md` — add Gold features, setup instructions, usage
- [ ] **6.1.3** Write Gold phase completion report (`reports/gold_completion_report.md`)

### 6.2 Final Validation
- [ ] **6.2.1** Run full test suite (`pytest tests/`)
- [ ] **6.2.2** Verify all acceptance criteria from PRD Section 14.2
- [ ] **6.2.3** Commit and tag release `v3.0-gold`

---

## Dependency Graph

```
Phase 0.1 (Odoo Setup) ──────────────────→ Phase 2 (Odoo MCP + Sync)──┐
                                                                        ├→ Phase 4 (CEO Briefing)
Phase 0.2 (Twitter Setup) ───────────────→ Phase 3 (Twitter MCP) ──────┘
                                                                        ↓
Phase 1 (Foundation: Audit, Finance,  ───→ Phase 5 (Integration + Cron)
         Watchdog, Ralph Wiggum)                                        ↓
                                                                  Phase 6 (Docs)
```

**Key:** Phase 1 can start immediately. Phases 2 and 3 are blocked by external setup. Phase 4 needs data sources from Phases 2-3 (but can gracefully degrade). Phases 5-6 are final integration.

---

## Summary

| Phase | Tasks | Blocked By | Scope |
|-------|-------|------------|-------|
| **0** | 18 | Nothing (manual) | Odoo install, Twitter API setup |
| **1** | 36 | Nothing | Vault, config, audit, finance watcher, watchdog, Ralph Wiggum |
| **2** | 19 | Phase 0.1 | Odoo MCP server, Odoo data sync |
| **3** | 15 | Phase 0.2 | Twitter MCP server, social media summary |
| **4** | 10 | Phases 1-3 (soft) | CEO Briefing generator |
| **5** | 19 | Phases 1-4 | Cron, degradation testing, E2E tests |
| **6** | 5 | Phase 5 | Architecture docs, README, final validation |
| **Total** | **122 tasks** | | |
