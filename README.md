# ChainGuard

**Digital Evidence Chain of Custody Management System**
UCS310 — Database Management Systems · B.Tech CSE 2nd Year · 2025–26
TIET Patiala

---

## 📄 Project Report

**[ChainGuard-Project-Report.pdf](./ChainGuard-Project-Report.pdf)** — full report submission.

## 🌐 Live Demo

**https://chainguard-dbms-production.up.railway.app**

All ten dashboard pages are live. Top status bar polls every 5 s, Ctrl/⌘ K opens a command palette across cases, evidence, and officers.

## 📜 Oracle SQL/PL-SQL

**[`ChainGuard_Complete.sql`](./ChainGuard_Complete.sql)** — single-file, run top-to-bottom on [Oracle Live SQL](https://livesql.oracle.com).

| Section | Contents |
|---|---|
| DDL | 9 tables · 3 indexes · PK / FK / CHECK / UNIQUE / NOT NULL |
| Seed | 6 officers · 5 cases · 12 evidence items · 16 transfers · 5 lab analyses · 4 court requisitions |
| Queries | 8 complex SELECTs (3-table joins, correlated subqueries, aggregates, HAVING, set ops) |
| Views | `v_active_cases` · `v_custody_chain` · `v_lab_pending` · `v_court_schedule` |
| Triggers | `trg_auto_first_custody` · `trg_tamper_lock` (raises -20001) · `trg_evidence_audit` |
| Procedure | `sp_custody_transfer` — atomic 3-step transfer (SAVEPOINT / ROLLBACK / COMMIT) |
| Function | `fn_validate_chain_integrity` — cursor walk; returns `INTACT` or `BROKEN: …` |
| Package | `pkg_chainguard_reports` — case report + overdue alerts |
| Tx demo | 4-step block: COMMIT, ROLLBACK, SAVEPOINT, tamper detection |

## 🖥️ Flask Web Dashboard

Source in **[`chainguard-app/`](./chainguard-app)**. Local run:

```bash
cd chainguard-app
pip install -r requirements.txt
python init_db.py
python app.py
# open http://localhost:5050
```

10 pages (`/`, `/cases`, `/cases/<id>`, `/evidence`, `/evidence/<id>`, `/custody`, `/lab`, `/court`, `/officers`, `/audit`) plus 2 JSON APIs (`/api/status`, `/api/search`). Forensic operations console aesthetic — Rajdhani / Inter / JetBrains Mono. No JS framework.

## 👥 Team

| Member | Roll | Role |
|---|---|---|
| **Arun AK** *(Team Leader)* | 1024170121 | PL/SQL backend, Flask dashboard, Railway deployment |
| Vansh Kapil | — | Schema design, ER modelling, normalization, queries |
| Tikshan Garg | — | Sample data, trigger/transaction testing, report compilation |

---

*Course: UCS310 Database Management Systems · TIET Patiala · Even Sem 2025–26*
