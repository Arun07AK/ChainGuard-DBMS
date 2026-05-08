# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**ChainGuard** — Digital Evidence Chain of Custody Management System.
UCS310 Database Management Systems final project, B.Tech CSE 2nd Year, TIET Patiala, Even Sem 2025–26.

Two deliverables:
1. **`ChainGuard_Complete.sql`** — Oracle 18c PL/SQL master script. Run top-to-bottom on Oracle Live SQL or db-fiddle.com.
2. **`chainguard-app/`** — Flask + SQLite + gunicorn web dashboard. Deployed on Railway with a persistent `/data` volume.

Live demo: https://chainguard-dbms-production.up.railway.app
GitHub: https://github.com/Arun07AK/ChainGuard-DBMS

## What's in the SQL master file

| Section | Content |
|---|---|
| DDL | 9 tables (Officers, Forensic_Labs, Storage_Facilities, Cases, Evidence, Custody_Transfers, Lab_Analysis, Court_Requisitions, Audit_Log) + 3 indexes + PK/FK/CHECK/UNIQUE/NOT NULL constraints |
| Seed data | 6 officers, 3 labs, 3 facilities, 5 cases, 12 evidence items, 16 transfers, 5 lab analyses, 4 court requisitions, 4 audit rows |
| Queries | 8 complex SELECTs (3-table joins, correlated subqueries, aggregates, HAVING, set ops) |
| Views | `v_active_cases`, `v_custody_chain`, `v_lab_pending`, `v_court_schedule` |
| Triggers | `trg_auto_first_custody` (auto first row on Evidence insert), `trg_tamper_lock` (BEFORE UPDATE/DELETE on sealed Custody_Transfers — raises `-20001`), `trg_evidence_audit` (logs every Evidence change) |
| Procedure | `sp_custody_transfer` — 3-step atomic handover with `SAVEPOINT sp_transfer_start` / `ROLLBACK TO` / `COMMIT`. Custom errors: `-20002` wrong custodian, `-20003` unauthorised officer |
| Function | `fn_validate_chain_integrity(evidence_id)` — cursor walk; returns `'INTACT'` or a `'BROKEN: …'` reason. Flags >30-day gaps |
| Package | `pkg_chainguard_reports` — `generate_case_report(case_id)`, `flag_overdue_evidence` |
| Tx demo | 4-step block: COMMIT, ROLLBACK, SAVEPOINT, tamper-detection |

There is also a small `pkg_bypass` package with a single boolean flag (`g_in_procedure`) that the trigger reads — `sp_custody_transfer` sets it before its own legitimate UPDATE so the tamper-lock trigger doesn't block the procedure. Raw human edits don't set the flag and get blocked.

## Flask app (`chainguard-app/`)

| File | Role |
|---|---|
| `app.py` | 10 page routes + 2 JSON API routes (`/api/status`, `/api/search`) |
| `init_db.py` | Builds `chainguard.db` from in-file SCHEMA + SEED constants. Honors `CHAINGUARD_DB_PATH` env var |
| `templates/` | 11 Jinja templates — base + dashboard + case (list/detail) + evidence (list/detail) + custody + lab + court + officers + audit |
| `requirements.txt` | flask 3.0.3, gunicorn 22.0.0 |
| `Procfile` | gunicorn boot command (Railway reads this) |
| `runtime.txt` | python-3.11.9 |
| `nixpacks.toml` | Repo-root config telling Railway to build from `chainguard-app/` subdir |

Page routes (no auth, read-mostly demo): `/`, `/cases`, `/cases/<id>`, `/evidence`, `/evidence/<id>`, `/custody`, `/lab`, `/court`, `/officers`, `/audit`. API routes: `/api/status` (5-s poll for status bar) and `/api/search?q=…` (Ctrl/⌘K palette).

Frontend is the **Forensic Operations Console** — Rajdhani (display) + Inter (body) + JetBrains Mono with `tabular-nums` for IDs/timestamps. Dark forensic palette. Top status bar with live counters, left rail with section count badges, command palette, custody-chain timeline (showpiece on `/evidence/<id>`), chain-integrity banner, audit terminal with severity glyphs, print stylesheet for evidentiary printouts. **No JS frameworks, no icon fonts, no CDN deps beyond Google Fonts.**

## Deployment

Railway, project name `chainguard`, service `ChainGuard-DBMS`. GitHub-connected — push to `main` triggers automatic build via `nixpacks.toml`. Persistent volume mounted at `/data`; the SQLite DB lives at `$CHAINGUARD_DB_PATH=/data/chainguard.db`. `init_db.py` auto-seeds on first boot only.

A separate plain-language explainer site (deployed to Vercel as `chainguard-explainer`) is **kept out of this repo on purpose**. Don't link it from this README, don't commit any explainer files here, and don't reference it in PR or commit messages.

## Conventions

- **Never add `Co-Authored-By: Claude` lines to commits.** Inherited from `~/CLAUDE.md`.
- **PYQ verbatim rule** doesn't apply here, but the spirit does: any number quoted in docs must match the actual seed (6/3/3/5/12/16/5/4/4 — see `init_db.py` and the SEED constant). Cross-check before claiming a count.
- Frontend stack is locked: pure HTML + CSS + vanilla JS. **Don't introduce React/Vue/Tailwind/Bootstrap/jQuery.**
- The Flask app is the demo layer; the SQL master file is the canonical artefact for the course. Behaviour-preserving rewrites of the Flask app are fine; do not change `ChainGuard_Complete.sql` casually — it's what the teacher will run on Oracle Live SQL.
- SQLite vs Oracle: Flask app uses SQLite-isms (`AUTOINCREMENT`, `julianday()`, `date('now', '-2 days')`). The Oracle script uses Oracle-isms (`SYSDATE`, `SYSTIMESTAMP`, `RAISE_APPLICATION_ERROR`, `CURSOR FOR LOOP`, packages). Don't accidentally cross-pollinate.

## Cross-project rules (inherited from `~/CLAUDE.md`)

- Never add `Co-Authored-By` lines.
- Chunked execution for big multi-file tasks.
- Verify numeric claims against source before stating them.
