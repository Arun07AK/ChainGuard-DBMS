"""
ChainGuard Flask Application
Run: python app.py
"""
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from datetime import datetime
import sqlite3, os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chainguard-secret-2025')
DB_PATH = os.environ.get(
    'CHAINGUARD_DB_PATH',
    os.path.join(os.path.dirname(__file__), 'chainguard.db'),
)
os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)
if not os.path.exists(DB_PATH):
    import init_db
    init_db.DB_PATH = DB_PATH
    init_db.init()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

def q(sql, args=()):
    return get_db().execute(sql, args).fetchall()

def q1(sql, args=()):
    return get_db().execute(sql, args).fetchone()

# ── Dashboard ────────────────────────────────────────────────
@app.route('/')
def dashboard():
    stats = {
        'total_cases':    q1("SELECT COUNT(*) FROM Cases")[0],
        'open_cases':     q1("SELECT COUNT(*) FROM Cases WHERE Status IN ('OPEN','UNDER_INVESTIGATION')")[0],
        'total_evidence': q1("SELECT COUNT(*) FROM Evidence")[0],
        'pending_transfers': q1("SELECT COUNT(*) FROM Custody_Transfers WHERE Status='PENDING'")[0],
        'lab_active':     q1("SELECT COUNT(*) FROM Lab_Analysis WHERE Status IN ('PENDING','IN_PROGRESS')")[0],
        'court_upcoming': q1("SELECT COUNT(*) FROM Court_Requisitions WHERE Status IN ('PENDING','APPROVED')")[0],
    }
    recent_transfers = q("""
        SELECT ct.Transfer_Date, e.Description, e.Tamper_Seal,
               f.Name AS From_Off, t.Name AS To_Off,
               ct.Status, ct.Is_Sealed
        FROM Custody_Transfers ct
        JOIN Evidence e ON ct.Evidence_ID = e.Evidence_ID
        JOIN Officers f ON ct.From_Officer_ID = f.Officer_ID
        JOIN Officers t ON ct.To_Officer_ID   = t.Officer_ID
        ORDER BY ct.Transfer_ID DESC LIMIT 6
    """)
    overdue = q("""
        SELECT e.Evidence_ID, e.Description, e.Tamper_Seal,
               c.FIR_Number, ct.Transfer_Date,
               f.Name AS From_Off, t.Name AS Assigned_To
        FROM Custody_Transfers ct
        JOIN Evidence e ON ct.Evidence_ID = e.Evidence_ID
        JOIN Cases c    ON e.Case_ID = c.Case_ID
        JOIN Officers f ON ct.From_Officer_ID = f.Officer_ID
        JOIN Officers t ON ct.To_Officer_ID   = t.Officer_ID
        WHERE ct.Status='PENDING' AND ct.Transfer_Date < date('now','-2 days')
    """)
    category_dist = q("""
        SELECT Category, COUNT(*) AS cnt FROM Evidence GROUP BY Category ORDER BY cnt DESC
    """)
    return render_template('dashboard.html', stats=stats,
                           recent_transfers=recent_transfers,
                           overdue=overdue,
                           category_dist=category_dist)

# ── Cases ────────────────────────────────────────────────────
@app.route('/cases')
def cases():
    rows = q("""
        SELECT c.*, o.Name AS Officer_Name,
               COUNT(e.Evidence_ID) AS Evidence_Count
        FROM Cases c
        JOIN Officers o ON c.Investigating_Officer_ID = o.Officer_ID
        LEFT JOIN Evidence e ON c.Case_ID = e.Case_ID
        GROUP BY c.Case_ID
        ORDER BY c.Date_Reported DESC
    """)
    return render_template('cases.html', cases=rows)

@app.route('/cases/<int:case_id>')
def case_detail(case_id):
    case = q1("""
        SELECT c.*, o.Name AS Officer_Name, o.Badge_Number, o.Department
        FROM Cases c JOIN Officers o ON c.Investigating_Officer_ID = o.Officer_ID
        WHERE c.Case_ID = ?
    """, (case_id,))
    if not case:
        flash('Case not found.', 'error')
        return redirect(url_for('cases'))
    evidence = q("""
        SELECT e.*, o.Name AS Custodian_Name, o.Badge_Number,
               sf.Facility_Name
        FROM Evidence e
        JOIN Officers o ON e.Current_Custodian_ID = o.Officer_ID
        LEFT JOIN Storage_Facilities sf ON e.Facility_ID = sf.Facility_ID
        WHERE e.Case_ID = ?
        ORDER BY e.Evidence_ID
    """, (case_id,))
    return render_template('case_detail.html', case=case, evidence=evidence)

# ── Evidence ─────────────────────────────────────────────────
@app.route('/evidence')
def evidence_list():
    cat = request.args.get('category', '')
    status = request.args.get('status', '')
    sql = """
        SELECT e.*, c.FIR_Number, c.Crime_Type,
               o.Name AS Custodian_Name, o.Badge_Number
        FROM Evidence e
        JOIN Cases c    ON e.Case_ID = c.Case_ID
        JOIN Officers o ON e.Current_Custodian_ID = o.Officer_ID
        WHERE 1=1
    """
    args = []
    if cat:
        sql += " AND e.Category = ?"
        args.append(cat)
    sql += " ORDER BY e.Evidence_ID"
    rows = q(sql, args)
    categories = [r[0] for r in q("SELECT DISTINCT Category FROM Evidence ORDER BY Category")]
    return render_template('evidence.html', evidence=rows,
                           categories=categories, selected_cat=cat)

@app.route('/evidence/<int:ev_id>')
def evidence_detail(ev_id):
    ev = q1("""
        SELECT e.*, c.FIR_Number, c.Crime_Type, c.Status AS Case_Status,
               o.Name AS Custodian_Name, o.Badge_Number, o.Department,
               sf.Facility_Name, sf.Facility_Type
        FROM Evidence e
        JOIN Cases c    ON e.Case_ID = c.Case_ID
        JOIN Officers o ON e.Current_Custodian_ID = o.Officer_ID
        LEFT JOIN Storage_Facilities sf ON e.Facility_ID = sf.Facility_ID
        WHERE e.Evidence_ID = ?
    """, (ev_id,))
    if not ev:
        flash('Evidence not found.', 'error')
        return redirect(url_for('evidence_list'))
    transfers = q("""
        SELECT ct.*, f.Name AS From_Off, f.Badge_Number AS From_Badge,
               t.Name AS To_Off, t.Badge_Number AS To_Badge
        FROM Custody_Transfers ct
        JOIN Officers f ON ct.From_Officer_ID = f.Officer_ID
        JOIN Officers t ON ct.To_Officer_ID   = t.Officer_ID
        WHERE ct.Evidence_ID = ?
        ORDER BY ct.Transfer_Date ASC, ct.Transfer_ID ASC
    """, (ev_id,))
    analyses = q("""
        SELECT la.*, fl.Lab_Name, o.Name AS Analyst_Name
        FROM Lab_Analysis la
        JOIN Forensic_Labs fl ON la.Lab_ID = fl.Lab_ID
        JOIN Officers o ON la.Analyst_Officer_ID = o.Officer_ID
        WHERE la.Evidence_ID = ?
        ORDER BY la.Start_Date DESC
    """, (ev_id,))
    chain_ok = validate_chain(ev_id)
    return render_template('evidence_detail.html', ev=ev,
                           transfers=transfers, analyses=analyses,
                           chain_status=chain_ok)

def validate_chain(ev_id):
    transfers = q("""
        SELECT Transfer_ID, From_Officer_ID, To_Officer_ID, Transfer_Date, Reason
        FROM Custody_Transfers WHERE Evidence_ID = ?
        ORDER BY Transfer_Date ASC, Transfer_ID ASC
    """, (ev_id,))
    if not transfers:
        return 'BROKEN: No records found'
    prev_to = None
    for i, t in enumerate(transfers):
        if i == 0:
            if t['From_Officer_ID'] != t['To_Officer_ID']:
                return 'BROKEN: First record not INITIAL_COLLECTION'
        else:
            if prev_to != t['From_Officer_ID']:
                return f'BROKEN: Gap at Transfer_ID={t["Transfer_ID"]}'
        prev_to = t['To_Officer_ID']
    return 'INTACT'

# ── Custody Chain ─────────────────────────────────────────────
@app.route('/custody')
def custody():
    transfers = q("""
        SELECT ct.Transfer_ID, ct.Transfer_Date, ct.Location,
               ct.Reason, ct.Status, ct.Is_Sealed,
               ct.Evidence_Condition,
               e.Evidence_ID, e.Description AS Evidence_Desc, e.Tamper_Seal,
               c.FIR_Number,
               f.Name AS From_Off, t.Name AS To_Off
        FROM Custody_Transfers ct
        JOIN Evidence e ON ct.Evidence_ID     = e.Evidence_ID
        JOIN Cases c    ON e.Case_ID          = c.Case_ID
        JOIN Officers f ON ct.From_Officer_ID = f.Officer_ID
        JOIN Officers t ON ct.To_Officer_ID   = t.Officer_ID
        ORDER BY ct.Transfer_ID DESC
    """)
    return render_template('custody.html', transfers=transfers)

# ── Lab Analysis ──────────────────────────────────────────────
@app.route('/lab')
def lab():
    rows = q("""
        SELECT la.*, e.Description AS Evidence_Desc, e.Tamper_Seal,
               c.FIR_Number, fl.Lab_Name, o.Name AS Analyst_Name,
               CASE WHEN la.End_Date IS NOT NULL
                    THEN CAST((julianday(la.End_Date) - julianday(la.Start_Date)) AS INTEGER)
                    ELSE CAST((julianday('now') - julianday(la.Start_Date)) AS INTEGER)
               END AS Days_In_Lab
        FROM Lab_Analysis la
        JOIN Evidence e     ON la.Evidence_ID       = e.Evidence_ID
        JOIN Cases c        ON e.Case_ID            = c.Case_ID
        JOIN Forensic_Labs fl ON la.Lab_ID          = fl.Lab_ID
        JOIN Officers o     ON la.Analyst_Officer_ID = o.Officer_ID
        ORDER BY la.Analysis_ID DESC
    """)
    return render_template('lab.html', analyses=rows)

# ── Court Requisitions ────────────────────────────────────────
@app.route('/court')
def court():
    rows = q("""
        SELECT cr.*, e.Description AS Evidence_Desc, e.Tamper_Seal,
               c.FIR_Number, c.Crime_Type,
               o.Name AS Requested_By
        FROM Court_Requisitions cr
        JOIN Evidence e ON cr.Evidence_ID     = e.Evidence_ID
        JOIN Cases c    ON cr.Case_ID         = c.Case_ID
        JOIN Officers o ON cr.Requested_By_ID = o.Officer_ID
        ORDER BY cr.Hearing_Date ASC
    """)
    return render_template('court.html', requisitions=rows)

# ── Officers ──────────────────────────────────────────────────
@app.route('/officers')
def officers():
    rows = q("""
        SELECT o.*,
               COUNT(DISTINCT e.Evidence_ID) AS Evidence_Held,
               COUNT(DISTINCT ct.Transfer_ID) AS Transfers_Made
        FROM Officers o
        LEFT JOIN Evidence e ON o.Officer_ID = e.Current_Custodian_ID
        LEFT JOIN Custody_Transfers ct ON o.Officer_ID = ct.From_Officer_ID
        GROUP BY o.Officer_ID
        ORDER BY o.Officer_ID
    """)
    return render_template('officers.html', officers=rows)

# ── Audit Log ─────────────────────────────────────────────────
@app.route('/audit')
def audit():
    rows = q("""
        SELECT al.*, o.Name AS Officer_Name
        FROM Audit_Log al
        LEFT JOIN Officers o ON al.Officer_ID = o.Officer_ID
        ORDER BY al.Log_ID DESC
    """)
    return render_template('audit.html', logs=rows)

# ── /api/status ───────────────────────────────────────────────
@app.route('/api/status')
def api_status():
    open_cases = q1(
        "SELECT COUNT(*) FROM Cases WHERE Status IN ('OPEN','UNDER_INVESTIGATION')"
    )[0]
    pending_transfers = q1(
        "SELECT COUNT(*) FROM Custody_Transfers WHERE Status='PENDING'"
    )[0]
    tamper_attempts = q1(
        "SELECT COUNT(*) FROM Audit_Log WHERE UPPER(IP_Note) LIKE '%TAMPER%'"
    )[0]
    return jsonify({
        'open_cases':        open_cases,
        'pending_transfers': pending_transfers,
        'tamper_attempts':   tamper_attempts,
        'server_time':       datetime.utcnow().isoformat(timespec='seconds') + 'Z',
    })


# ── /api/search ───────────────────────────────────────────────
@app.route('/api/search')
def api_search():
    term = (request.args.get('q') or '').strip()
    if not term:
        return jsonify({'results': []})
    like = f'%{term}%'
    results = []

    for r in q("""
        SELECT Case_ID, FIR_Number, Crime_Type, Status
        FROM Cases
        WHERE FIR_Number LIKE ? OR Crime_Type LIKE ?
        ORDER BY Case_ID DESC LIMIT 6
    """, (like, like)):
        results.append({
            'type':     'case',
            'id':       r['Case_ID'],
            'label':    r['FIR_Number'],
            'sublabel': f"{r['Crime_Type']} · {r['Status']}",
            'url':      url_for('case_detail', case_id=r['Case_ID']),
        })

    is_num = term.lstrip('#').isdigit()
    ev_rows = q("""
        SELECT Evidence_ID, Tamper_Seal, Description, Category
        FROM Evidence
        WHERE Tamper_Seal LIKE ? OR Description LIKE ?
              OR (? != 0 AND Evidence_ID = ?)
        ORDER BY Evidence_ID DESC LIMIT 6
    """, (like, like, 1 if is_num else 0, int(term.lstrip('#')) if is_num else 0))
    for r in ev_rows:
        desc = (r['Description'] or '')[:60]
        results.append({
            'type':     'evidence',
            'id':       r['Evidence_ID'],
            'label':    f"#{r['Evidence_ID']:04d} · {r['Tamper_Seal'] or '—'}",
            'sublabel': f"{r['Category']} · {desc}",
            'url':      url_for('evidence_detail', ev_id=r['Evidence_ID']),
        })

    for r in q("""
        SELECT Officer_ID, Name, Badge_Number, Rank, Department
        FROM Officers
        WHERE Badge_Number LIKE ? OR Name LIKE ?
        ORDER BY Officer_ID LIMIT 6
    """, (like, like)):
        results.append({
            'type':     'officer',
            'id':       r['Officer_ID'],
            'label':    f"{r['Name']} · {r['Badge_Number']}",
            'sublabel': f"{r['Rank']} · {r['Department']}",
            'url':      url_for('officers'),
        })

    return jsonify({'results': results[:15]})


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5050)), host='0.0.0.0')
