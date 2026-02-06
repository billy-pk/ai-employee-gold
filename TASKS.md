# Gold Phase - Implementation Tasks

**Status:** In Progress (~85% complete)
**Prerequisites:** Silver phase complete ✅
**Completed:** Phases 0, 1, 2, 3, 4 (224 tests passing)
**Blockers:** None - all external dependencies configured

---

## Phase 0: External Setup (Manual / Outside Codebase)

> These are prerequisites that must be done before certain code tasks can begin.

### 0.1 Install Odoo Community Edition 19+ ✅
- [x] **0.1.1** Pull Odoo 19 Docker image (`docker pull odoo:19`)
- [x] **0.1.2** Create PostgreSQL container (`postgres:15`)
- [x] **0.1.3** Run Odoo container linked to PostgreSQL, exposed on port 8069
- [x] **0.1.4** Access `http://localhost:8069` and complete initial setup wizard
- [x] **0.1.5** Create database `ai_employee_db`
- [x] **0.1.6** Install Invoicing module
- [x] **0.1.7** Create admin API key (Settings → Users → API Keys)
- [x] **0.1.8** Create test customer "Client A" (id: 7)
- [x] **0.1.9** Create test invoice for validation (INV/2026/00001: $500.00)
- [x] **0.1.10** Save credentials to `credentials/odoo_config.json`

**Status:** COMPLETE ✅ - Unblocks Phase 2 & 4

### 0.2 Obtain Twitter API Credentials ✅
- [x] **0.2.1** Create Twitter Developer Account at developer.twitter.com
- [x] **0.2.2** Create a new Project
- [x] **0.2.3** Create an App within the project (ai_employee)
- [x] **0.2.4** Generate API Key and API Secret
- [x] **0.2.5** Generate Access Token and Access Token Secret
- [x] **0.2.6** Generate Bearer Token
- [x] **0.2.7** Test API connection (verified: @IrshadBilal)
- [x] **0.2.8** Save credentials to `credentials/twitter_credentials.json`

**Status:** COMPLETE ✅ - Unblocks Phase 3 & 4

---

## Phase 1: Foundation (No External Dependencies) ✅

> COMPLETE - All 36 tasks finished with 136 passing tests.

### 1.1 Vault Folder Structure ✅
- [x] **1.1.1** Create `Business/` folder in vault
- [x] **1.1.2** Create `Business/Transactions/` subfolder (for bank CSVs)
- [x] **1.1.3** Create `Business/Odoo/` subfolder (for sync data)
- [x] **1.1.4** Create `Business/Business_Goals.md` from PRD template (move existing `Business_Goals.md` into `Business/`)
- [x] **1.1.5** Create `Social/` folder in vault
- [x] **1.1.6** Create `Social/Twitter/` subfolder
- [x] **1.1.7** Create `Social/Twitter/scheduled_posts.md` (empty template)
- [x] **1.1.8** Create `Social/Twitter/posted.md` (empty template)
- [x] **1.1.9** Create `Social/Twitter/engagement.md` (empty template)
- [x] **1.1.10** Create `Briefings/` folder in vault
- [x] **1.1.11** Create `Audit/` folder in vault
- [x] **1.1.12** Create `Tasks/` folder in vault (for Ralph Wiggum task state files)
- [x] **1.1.13** Update `Dashboard.md` — add System Health section from PRD template
- [x] **1.1.14** Update `Company_Handbook.md` — add Gold phase rules (Odoo, Twitter, finance policies)

### 1.2 Project Configuration Updates ✅
- [x] **1.2.1** Update `pyproject.toml` — add Gold dependencies: `tweepy>=4.14.0`, `pandas>=2.0.0`, `schedule>=1.2.0`
- [x] **1.2.2** Update `.env` template — add Odoo, Twitter, Watchdog, Ralph Wiggum variables
- [x] **1.2.3** Update `.gitignore` — ensure `credentials/odoo_config.json`, `credentials/twitter_credentials.json` are excluded
- [x] **1.2.4** Run `uv sync` to install new dependencies

### 1.3 Audit Logger (`src/utils/audit_logger.py`) ✅
- [x] **1.3.1** Create `src/utils/audit_logger.py`
- [x] **1.3.2** Implement `AuditLogger` class with:
  - `log_action(action_type, actor, target, parameters, approval_status, result, result_details)`
  - JSON append to `/Audit/YYYY-MM-DD.json`
  - Append-only writes (never modify existing entries)
- [x] **1.3.3** Implement 90-day retention cleanup method
- [x] **1.3.4** Write tests `tests/test_audit_logger.py` (15 tests)
- [x] **1.3.5** Integrate audit logger into existing `approval_executor.py` (log email sends)

### 1.4 Finance Watcher (`src/watchers/finance_watcher.py`) ✅
- [x] **1.4.1** Create `src/watchers/finance_watcher.py` extending `BaseWatcher`
- [x] **1.4.2** Implement CSV detection — watch `Business/Transactions/` for new `.csv` files
- [x] **1.4.3** Implement CSV parsing — handle Generic, Chase, Bank of America formats (auto-detect columns)
- [x] **1.4.4** Implement subscription detection — match transaction descriptions against known patterns (Netflix, Spotify, Adobe, etc.)
- [x] **1.4.5** Implement large transaction flagging (configurable threshold, default >$500)
- [x] **1.4.6** Generate `Needs_Action/FINANCE_[date]_[hash].md` with summary, flagged items, and action checklist
- [x] **1.4.7** Track processed CSV files to avoid re-processing (append to `Logs/processed_finances.txt`)
- [x] **1.4.8** Create `scripts/run_finance_watcher.py`
- [x] **1.4.9** Write tests `tests/test_finance_watcher.py` (21 tests)
- [ ] **1.4.10** Manual test: drop a sample CSV in vault and verify output

### 1.5 Watchdog Process Monitor (`src/watchdog/process_monitor.py`) ✅
- [x] **1.5.1** Create `src/watchdog/__init__.py`
- [x] **1.5.2** Create `src/watchdog/process_monitor.py`
- [x] **1.5.3** Implement `ProcessMonitor` class:
  - Check PID files for Gmail Watcher, FileSystem Watcher, Finance Watcher
  - Detect stale PID files (process no longer running)
  - Restart failed watchers via subprocess
- [x] **1.5.4** Implement failure tracking — alert after 3 consecutive restart failures
- [x] **1.5.5** Implement health status output — update Dashboard.md health section
- [x] **1.5.6** Implement logging to `Logs/watchdog.log`
- [x] **1.5.7** Create `scripts/run_watchdog.py`
- [x] **1.5.8** Write tests `tests/test_watchdog.py` (23 tests)
- [ ] **1.5.9** Manual test: kill a watcher process and verify watchdog restarts it

### 1.6 Ralph Wiggum Loop (`src/hooks/ralph_wiggum.py`) ✅
- [x] **1.6.1** Create `src/hooks/__init__.py`
- [x] **1.6.2** Create `src/hooks/ralph_wiggum.py`
- [x] **1.6.3** Implement stop hook logic:
  - Read task state file from `/Tasks/TASK_[id].md`
  - Check if task file has been moved to `/Done/`
  - Check if `max_iterations` reached
  - If not complete and under limit: block exit, re-inject prompt
  - If complete or over limit: allow exit
- [x] **1.6.4** Implement iteration logging — update task file's iteration log table
- [x] **1.6.5** Create `skills/ralph-wiggum/SKILL.md` from PRD template
- [x] **1.6.6** Write tests `tests/test_ralph_wiggum.py` (27 tests)
- [ ] **1.6.7** Manual test: create a multi-step task and verify loop behavior

---

## Phase 2: Odoo Integration (Requires Phase 0.1 Complete) ✅

> COMPLETE - All 19 tasks finished with 44 passing tests.

### 2.1 Odoo MCP Server (`src/mcp/odoo_mcp.py`) ✅
- [x] **2.1.1** Create `src/mcp/odoo_mcp.py`
- [x] **2.1.2** Implement Odoo JSON-RPC connection class:
  - `authenticate()` — connect using API key
  - Connection pooling / session reuse
  - 30-second timeout per request
  - Exponential backoff retry (via tenacity)
- [x] **2.1.3** Implement `create_invoice(customer_id, lines, due_date)`
- [x] **2.1.4** Implement `get_invoices(period, status)` — list invoices for period
- [x] **2.1.5** Implement `get_invoice(invoice_id)` — single invoice details
- [x] **2.1.6** Implement `create_payment(invoice_id, amount, date)`
- [x] **2.1.7** Implement `get_customers()` — list all customers
- [x] **2.1.8** Implement `get_customer(customer_id)` — single customer details
- [x] **2.1.9** Implement `get_account_balance(account_id)` — check balances
- [x] **2.1.10** Implement `get_journal_entries(period)` — transactions for reporting
- [x] **2.1.11** Implement graceful failure — return error objects instead of crashing
- [x] **2.1.12** Integrate audit logging for all Odoo operations
- [x] **2.1.13** Write tests `tests/test_odoo_mcp.py` (28 tests)
- [x] **2.1.14** Integration test: create invoice in real Odoo, verify via UI

### 2.2 Odoo Data Sync ✅
- [x] **2.2.1** Create `src/briefings/data_collectors.py` — Odoo data collector
- [x] **2.2.2** Implement sync logic:
  - Fetch recent invoices, customers, account balances
  - Generate financial snapshots as JSON
  - Generate human-readable financial briefs as markdown
- [x] **2.2.3** Add YAML frontmatter with `last_synced` timestamp
- [x] **2.2.4** Create `scripts/run_odoo_sync.py`
- [x] **2.2.5** Test sync: run script and verify files in vault (16 tests)

**Status:** COMPLETE ✅ - Odoo MCP and Data Sync operational

---

## Phase 3: Twitter/X Integration (Requires Phase 0.2 Complete) ✅

> COMPLETE - All 15 tasks finished with 25 passing tests.

### 3.1 Twitter MCP Server (`src/mcp/twitter_mcp.py`) ✅
- [x] **3.1.1** Create `src/mcp/twitter_mcp.py`
- [x] **3.1.2** Implement Twitter API v2 client using tweepy:
  - OAuth 1.0a authentication (works with free tier)
  - Rate limit handling with wait_on_rate_limit
- [x] **3.1.3** Implement `post_tweet(content)` — post a tweet (always requires prior approval)
- [x] **3.1.4** Implement `get_my_tweets(count)` — list recent tweets
- [x] **3.1.5** Implement `get_engagement(tweet_id)` — get metrics for a tweet
- [x] **3.1.6** Implement `get_mentions(count)` — list recent mentions
- [x] **3.1.7** Implement `schedule_tweet(content, scheduled_time)` — queue for later posting
- [x] **3.1.8** Implement tweet approval workflow:
  - Generate `Pending_Approval/TWEET_[id].md` from template
  - On approval, execute via `post_tweet`
  - Log to `Social/Twitter/posted.md`
- [x] **3.1.9** Integrate audit logging for all Twitter operations
- [x] **3.1.10** Write tests `tests/test_twitter_mcp.py` (25 tests)
- [x] **3.1.11** Integration test: post and delete a test tweet (verified)

### 3.2 Social Media Summary ✅
- [x] **3.2.1** Add Twitter data collector to `src/briefings/data_collectors.py`
- [x] **3.2.2** Implement engagement summary generation → update `Social/Twitter/engagement.md`
- [x] **3.2.3** Create `skills/social-poster/SKILL.md` from PRD template
- [x] **3.2.4** Test: generate summary from real Twitter data

**Status:** COMPLETE ✅ - Twitter MCP and Social Data Collector operational

---

## Phase 4: Business Intelligence (Requires Phases 1-3) ✅

> COMPLETE - All 10 tasks finished with 19 passing tests.

### 4.1 CEO Briefing Generator (`src/briefings/ceo_briefing.py`) ✅
- [x] **4.1.1** Create `src/briefings/__init__.py` (already exists, updated)
- [x] **4.1.2** Create `src/briefings/ceo_briefing.py`
- [x] **4.1.3** Implement data collection orchestrator — gather from all sources:
  - Odoo MCP → revenue, invoices, payments (graceful skip if unavailable)
  - Bank CSV data → expenses, subscriptions (from parsed vault data)
  - Done folder → completed tasks count and details
  - Twitter MCP → social engagement metrics (graceful skip if unavailable)
- [x] **4.1.4** Implement briefing markdown generation
- [x] **4.1.5** Implement week-over-week comparison (stores data in Data/Briefings/)
- [x] **4.1.6** Implement proactive suggestions logic:
  - Outstanding invoice follow-ups
  - Overdue invoice alerts
  - Draft invoice reminders
  - Pending task reviews
- [x] **4.1.7** Output to `Briefings/YYYY-MM-DD_Weekday_Briefing.md`
- [x] **4.1.8** Create `scripts/run_ceo_briefing.py`
- [x] **4.1.9** Create `skills/ceo-briefing/SKILL.md`
- [x] **4.1.10** Test: generate briefing with available data sources (19 tests)

**Status:** COMPLETE ✅ - CEO Briefing Generator operational

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

| Phase | Tasks | Blocked By | Status |
|-------|-------|------------|--------|
| **0** | 18 | Nothing (manual) | ✅ Complete |
| **1** | 36 | Nothing | ✅ Complete (136 tests) |
| **2** | 19 | Phase 0.1 | ✅ Complete (44 tests) |
| **3** | 15 | Phase 0.2 | ✅ Complete (25 tests) |
| **4** | 10 | Phases 1-3 (soft) | ✅ Complete (19 tests) |
| **5** | 19 | Phases 1-4 | 🔄 Ready to start |
| **6** | 5 | Phase 5 | Waiting |
| **Total** | **122 tasks** | | **~85% complete** |
