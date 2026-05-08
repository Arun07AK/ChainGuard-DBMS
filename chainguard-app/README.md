# ChainGuard

**Digital Evidence Chain of Custody Management System**  
Course: UCS310 – Database Management Systems | B.Tech 2nd Year | 2025–26

🌐 **Live demo:** https://chainguard-dbms-production.up.railway.app
🎤 **Plain-language explainer (for viva):** https://chainguard-explainer.vercel.app

---

## Overview

ChainGuard is a database-driven system that tracks every piece of criminal evidence from crime scene collection to court presentation. It enforces an immutable, tamper-evident audit trail using Oracle PL/SQL as the primary backend.

This repository contains:
- **`ChainGuard_Complete.sql`** — Full Oracle SQL/PL/SQL implementation (run on Oracle Live SQL / FreeSQL)
- **`chainguard-app/`** — Flask web dashboard (SQLite-backed demo)

---

## Oracle SQL Implementation (`ChainGuard_Complete.sql`)

Run the script top-to-bottom on [livesql.oracle.com](https://livesql.oracle.com) or [db-fiddle.com](https://db-fiddle.com) (Oracle 18c).

### What's inside

| Section | Contents |
|---------|----------|
| DDL | 9 tables with PK/FK/CHECK/UNIQUE/NOT NULL constraints + 3 indexes |
| DML | Realistic sample data — 6 officers, 5 cases, 12 evidence items, 16 transfers |
| Queries | 8 complex SELECTs — 3-table joins, correlated subqueries, aggregates, HAVING |
| Views | `v_active_cases`, `v_custody_chain`, `v_lab_pending`, `v_court_schedule` |
| Triggers | `trg_auto_first_custody`, `trg_tamper_lock`, `trg_evidence_audit` |
| Procedure | `sp_custody_transfer` — atomic transfer with SAVEPOINT/ROLLBACK/COMMIT |
| Function | `fn_validate_chain_integrity` — cursor-based chain walk |
| Package | `pkg_chainguard_reports` — case report + overdue alert via cursors |
| Transaction demo | 4-step block showing COMMIT, ROLLBACK, SAVEPOINT, tamper detection |

### Schema (9 tables)

```
Officers → Cases → Evidence → Custody_Transfers
                           → Lab_Analysis → Forensic_Labs
                           → Court_Requisitions
Storage_Facilities
Audit_Log
```

---

## Flask Web Dashboard (`chainguard-app/`)

A Python Flask app with SQLite backend for visual demo purposes.

### Setup

```bash
cd chainguard-app
pip install flask
python init_db.py     # creates chainguard.db with sample data
python app.py         # starts server on http://localhost:5050
```

### Pages

| Route | Page |
|-------|------|
| `/` | Dashboard — stats, overdue alerts, recent transfers |
| `/cases` | All cases with status and evidence count |
| `/cases/<id>` | Case detail with evidence breakdown |
| `/evidence` | Evidence registry with category filter |
| `/evidence/<id>` | Evidence detail with full custody chain timeline |
| `/custody` | All custody transfer records |
| `/lab` | Lab analysis records |
| `/court` | Court requisitions |
| `/officers` | Officer roster with activity stats |
| `/audit` | Audit log with tamper attempt highlighting |

---

## Author

**Arun AK** — B.Tech CSE, Thapar University (Roll: 1024170121)
