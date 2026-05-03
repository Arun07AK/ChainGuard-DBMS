"""
ChainGuard — SQLite database initialiser.
Run once: python init_db.py
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'chainguard.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS Officers (
    Officer_ID          INTEGER PRIMARY KEY AUTOINCREMENT,
    Name                TEXT NOT NULL,
    Badge_Number        TEXT NOT NULL UNIQUE,
    Rank                TEXT NOT NULL,
    Department          TEXT NOT NULL,
    Authorization_Level TEXT NOT NULL CHECK(Authorization_Level IN ('OFFICER','ANALYST','SUPERVISOR','ADMIN')),
    Phone               TEXT,
    Email               TEXT
);

CREATE TABLE IF NOT EXISTS Forensic_Labs (
    Lab_ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Lab_Name      TEXT NOT NULL,
    Location      TEXT NOT NULL,
    Specialization TEXT,
    Contact_Phone TEXT
);

CREATE TABLE IF NOT EXISTS Storage_Facilities (
    Facility_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
    Facility_Name TEXT NOT NULL,
    Location      TEXT NOT NULL,
    Capacity      INTEGER NOT NULL,
    Facility_Type TEXT NOT NULL CHECK(Facility_Type IN ('COLD_STORAGE','SECURE_VAULT','EVIDENCE_ROOM','DIGITAL_VAULT'))
);

CREATE TABLE IF NOT EXISTS Cases (
    Case_ID                  INTEGER PRIMARY KEY AUTOINCREMENT,
    FIR_Number               TEXT NOT NULL UNIQUE,
    Crime_Type               TEXT NOT NULL,
    Date_Reported            TEXT NOT NULL,
    Status                   TEXT NOT NULL DEFAULT 'OPEN' CHECK(Status IN ('OPEN','CLOSED','UNDER_INVESTIGATION','ARCHIVED')),
    Investigating_Officer_ID INTEGER NOT NULL REFERENCES Officers(Officer_ID),
    Description              TEXT
);

CREATE TABLE IF NOT EXISTS Evidence (
    Evidence_ID          INTEGER PRIMARY KEY AUTOINCREMENT,
    Case_ID              INTEGER NOT NULL REFERENCES Cases(Case_ID),
    Description          TEXT NOT NULL,
    Category             TEXT NOT NULL CHECK(Category IN ('WEAPON','BIOLOGICAL','ELECTRONIC','DOCUMENT','NARCOTIC','OTHER')),
    Condition            TEXT NOT NULL DEFAULT 'INTACT' CHECK(Condition IN ('INTACT','DAMAGED','DEGRADED','CONTAMINATED')),
    Date_Collected       TEXT NOT NULL,
    Current_Location     TEXT NOT NULL,
    Current_Custodian_ID INTEGER NOT NULL REFERENCES Officers(Officer_ID),
    Facility_ID          INTEGER REFERENCES Storage_Facilities(Facility_ID),
    Tamper_Seal          TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Custody_Transfers (
    Transfer_ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Evidence_ID        INTEGER NOT NULL REFERENCES Evidence(Evidence_ID),
    From_Officer_ID    INTEGER NOT NULL REFERENCES Officers(Officer_ID),
    To_Officer_ID      INTEGER NOT NULL REFERENCES Officers(Officer_ID),
    Transfer_Date      TEXT NOT NULL DEFAULT (date('now')),
    Location           TEXT NOT NULL,
    Reason             TEXT NOT NULL,
    Evidence_Condition TEXT NOT NULL CHECK(Evidence_Condition IN ('INTACT','DAMAGED','DEGRADED','CONTAMINATED')),
    Status             TEXT NOT NULL DEFAULT 'PENDING' CHECK(Status IN ('PENDING','COMPLETED','CANCELLED')),
    Is_Sealed          TEXT NOT NULL DEFAULT 'N' CHECK(Is_Sealed IN ('Y','N'))
);

CREATE TABLE IF NOT EXISTS Lab_Analysis (
    Analysis_ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    Evidence_ID        INTEGER NOT NULL REFERENCES Evidence(Evidence_ID),
    Lab_ID             INTEGER NOT NULL REFERENCES Forensic_Labs(Lab_ID),
    Analyst_Officer_ID INTEGER NOT NULL REFERENCES Officers(Officer_ID),
    Start_Date         TEXT NOT NULL,
    End_Date           TEXT,
    Findings           TEXT,
    Status             TEXT NOT NULL DEFAULT 'PENDING' CHECK(Status IN ('PENDING','IN_PROGRESS','COMPLETED'))
);

CREATE TABLE IF NOT EXISTS Court_Requisitions (
    Requisition_ID  INTEGER PRIMARY KEY AUTOINCREMENT,
    Evidence_ID     INTEGER NOT NULL REFERENCES Evidence(Evidence_ID),
    Case_ID         INTEGER NOT NULL REFERENCES Cases(Case_ID),
    Court_Name      TEXT NOT NULL,
    Hearing_Date    TEXT NOT NULL,
    Requested_By_ID INTEGER NOT NULL REFERENCES Officers(Officer_ID),
    Status          TEXT NOT NULL DEFAULT 'PENDING' CHECK(Status IN ('PENDING','APPROVED','RETURNED','REJECTED')),
    Request_Date    TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS Audit_Log (
    Log_ID           INTEGER PRIMARY KEY AUTOINCREMENT,
    Table_Name       TEXT NOT NULL,
    Operation        TEXT NOT NULL CHECK(Operation IN ('INSERT','UPDATE','DELETE')),
    Record_ID        INTEGER NOT NULL,
    Officer_ID       INTEGER REFERENCES Officers(Officer_ID),
    Action_Timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    Old_Value        TEXT,
    New_Value        TEXT,
    IP_Note          TEXT
);
"""

SEED = """
INSERT INTO Officers VALUES (1,'Rajesh Kumar Sharma','DL-OFC-001','Sub-Inspector','Delhi Police - Crime Branch','OFFICER','9811001001','rkumar@dcp.gov.in');
INSERT INTO Officers VALUES (2,'Priya Nair','DL-ANA-002','Forensic Analyst','CFSL New Delhi','ANALYST','9811002002','pnair@cfsl.gov.in');
INSERT INTO Officers VALUES (3,'Vikram Singh Rathore','DL-SUP-003','Inspector','Delhi Police - Homicide Division','SUPERVISOR','9811003003','vsrathore@dcp.gov.in');
INSERT INTO Officers VALUES (4,'Anita Desai','MH-OFC-004','Constable','Mumbai Police - Evidence Cell','OFFICER','9822004004','adesai@mp.gov.in');
INSERT INTO Officers VALUES (5,'Mohammed Irfan','MH-ANA-005','Senior Analyst','FSL Mumbai','ANALYST','9822005005','mirfan@fsl.gov.in');
INSERT INTO Officers VALUES (6,'Sunita Chauhan','DL-ADM-006','DCP','Delhi Police Headquarters','ADMIN','9811006006','schauhan@dcp.gov.in');

INSERT INTO Forensic_Labs VALUES (1,'Central Forensic Science Laboratory','Lodhi Road, New Delhi','DNA, Toxicology, Digital Forensics','01124360823');
INSERT INTO Forensic_Labs VALUES (2,'Forensic Science Laboratory Mumbai','Santacruz East, Mumbai','Ballistics, Narcotics Analysis','02226149100');
INSERT INTO Forensic_Labs VALUES (3,'Regional FSL Chandigarh','Sector 26, Chandigarh','Document Examination, Fingerprints','01722640500');

INSERT INTO Storage_Facilities VALUES (1,'Delhi Police Malkhana - Central','Tis Hazari, New Delhi',500,'EVIDENCE_ROOM');
INSERT INTO Storage_Facilities VALUES (2,'CFSL Secure Bio-Storage Vault','Lodhi Road, New Delhi',50,'COLD_STORAGE');
INSERT INTO Storage_Facilities VALUES (3,'Cyber Crime Digital Evidence Vault','CGO Complex, New Delhi',200,'DIGITAL_VAULT');

INSERT INTO Cases VALUES (1,'FIR/DL/2025/001','Murder','2025-01-15','UNDER_INVESTIGATION',3,'Body found at Dwarka Sector 12. Suspected homicide.');
INSERT INTO Cases VALUES (2,'FIR/DL/2025/002','Narcotics Seizure','2025-02-20','OPEN',1,'Large quantity of heroin seized at IGI Airport terminal.');
INSERT INTO Cases VALUES (3,'FIR/MH/2025/003','Bank Fraud','2025-03-05','OPEN',3,'Fraudulent transactions totalling Rs 2.4 crore at Andheri branch.');
INSERT INTO Cases VALUES (4,'FIR/DL/2024/089','Robbery','2024-11-10','CLOSED',1,'Armed robbery at jewellery shop in Karol Bagh. Case solved.');
INSERT INTO Cases VALUES (5,'FIR/DL/2025/005','Cybercrime','2025-04-01','UNDER_INVESTIGATION',6,'Ransomware attack on government portal. Digital forensics ongoing.');

INSERT INTO Evidence VALUES (1,1,'Kitchen knife, 18cm blade, bloodstained','WEAPON','INTACT','2025-01-15','Delhi Police Malkhana - Central',1,1,'SEAL-EV-001');
INSERT INTO Evidence VALUES (2,1,'Blood sample from crime scene - type AB+','BIOLOGICAL','INTACT','2025-01-15','CFSL Bio-Storage Vault',2,2,'SEAL-EV-002');
INSERT INTO Evidence VALUES (3,1,'Victim mobile phone - Samsung Galaxy S23','ELECTRONIC','DAMAGED','2025-01-16','CFSL Digital Lab',2,3,'SEAL-EV-003');
INSERT INTO Evidence VALUES (4,2,'Heroin 2.3kg in vacuum-sealed packets','NARCOTIC','INTACT','2025-02-20','FSL Mumbai Narcotics Unit',5,1,'SEAL-EV-004');
INSERT INTO Evidence VALUES (5,2,'Forged customs clearance documents','DOCUMENT','INTACT','2025-02-20','Delhi Police Malkhana - Central',1,1,'SEAL-EV-005');
INSERT INTO Evidence VALUES (6,3,'Laptop - Dell Latitude, suspect laptop','ELECTRONIC','INTACT','2025-03-06','Cyber Crime Digital Evidence Vault',6,3,'SEAL-EV-006');
INSERT INTO Evidence VALUES (7,3,'Bank transaction printouts - 47 pages','DOCUMENT','INTACT','2025-03-06','Delhi Police Malkhana - Central',3,1,'SEAL-EV-007');
INSERT INTO Evidence VALUES (8,4,'Revolver - .32 calibre, 3 rounds fired','WEAPON','INTACT','2024-11-10','Delhi Police Malkhana - Central',3,1,'SEAL-EV-008');
INSERT INTO Evidence VALUES (9,4,'CCTV footage from shop - USB drive','ELECTRONIC','INTACT','2024-11-10','Delhi Police Malkhana - Central',3,1,'SEAL-EV-009');
INSERT INTO Evidence VALUES (10,5,'Infected USB drive used in ransomware attack','ELECTRONIC','INTACT','2025-04-02','Cyber Crime Digital Evidence Vault',6,3,'SEAL-EV-010');
INSERT INTO Evidence VALUES (11,5,'Server access logs - printed 200 pages','DOCUMENT','INTACT','2025-04-02','CGO Complex, New Delhi',6,NULL,'SEAL-EV-011');
INSERT INTO Evidence VALUES (12,1,'Fingerprints lifted from door handle - 3 sets','OTHER','INTACT','2025-01-15','CFSL New Delhi',2,NULL,'SEAL-EV-012');

INSERT INTO Custody_Transfers VALUES (1,1,1,1,'2025-01-15','Delhi Police Malkhana - Central','INITIAL_COLLECTION','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (2,1,1,3,'2025-01-16','Delhi Police HQ','Transfer to supervising officer for case review','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (3,1,3,2,'2025-01-18','CFSL New Delhi','Sent to forensic lab for DNA analysis on blade','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (4,2,1,1,'2025-01-15','Crime Scene - Dwarka','INITIAL_COLLECTION','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (5,2,1,2,'2025-01-15','Crime Scene - Dwarka','Immediate transfer to forensic analyst for preservation','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (6,2,2,2,'2025-01-20','CFSL New Delhi','Re-catalogued after preliminary DNA typing','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (7,3,2,2,'2025-01-16','CFSL Digital Lab','INITIAL_COLLECTION','DAMAGED','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (8,4,1,1,'2025-02-20','FSL Mumbai Narcotics Unit','INITIAL_COLLECTION','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (9,4,1,5,'2025-02-21','IGI Airport Police Post','Transfer to FSL Mumbai for chemical analysis','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (10,5,1,1,'2025-02-20','Delhi Police Malkhana - Central','INITIAL_COLLECTION','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (11,6,6,6,'2025-03-06','Cyber Crime Digital Evidence Vault','INITIAL_COLLECTION','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (12,6,6,5,'2025-03-08','Cyber Crime Unit, Delhi','Sent to FSL for digital forensics analysis','INTACT','PENDING','N');
INSERT INTO Custody_Transfers VALUES (13,7,3,3,'2025-03-06','Delhi Police Malkhana - Central','INITIAL_COLLECTION','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (14,8,3,3,'2024-11-10','Delhi Police Malkhana - Central','INITIAL_COLLECTION','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (15,8,3,1,'2024-11-11','Delhi Police HQ','Transfer for ballistics examination','INTACT','COMPLETED','Y');
INSERT INTO Custody_Transfers VALUES (16,8,1,3,'2024-11-25','Delhi Police Malkhana','Returned after ballistics report - stored in Malkhana','INTACT','COMPLETED','Y');

INSERT INTO Lab_Analysis VALUES (1,1,1,2,'2025-01-19','2025-01-30','DNA profile extracted from blade. Match with victim 99.7% confidence. Fingerprints of unknown subject detected.','COMPLETED');
INSERT INTO Lab_Analysis VALUES (2,2,1,2,'2025-01-19',NULL,'Blood sample categorised AB+. DNA extraction in progress.','IN_PROGRESS');
INSERT INTO Lab_Analysis VALUES (3,4,2,5,'2025-02-22','2025-03-05','Substance confirmed as diacetylmorphine (heroin), purity 84.2%. Weight 2.287kg net.','COMPLETED');
INSERT INTO Lab_Analysis VALUES (4,8,1,2,'2024-11-12','2024-11-20','Revolver identified as .32 bore SBML. Three rounds fired. Ballistics match to spent cartridges at scene.','COMPLETED');
INSERT INTO Lab_Analysis VALUES (5,6,3,2,'2025-04-05',NULL,NULL,'PENDING');

INSERT INTO Court_Requisitions VALUES (1,1,1,'Sessions Court Delhi - Court No. 7','2025-06-15',3,'APPROVED','2025-05-01');
INSERT INTO Court_Requisitions VALUES (2,2,1,'Sessions Court Delhi - Court No. 7','2025-06-15',3,'PENDING','2025-05-01');
INSERT INTO Court_Requisitions VALUES (3,8,4,'Additional Sessions Court Delhi - Court No. 12','2025-02-10',1,'RETURNED','2025-01-20');
INSERT INTO Court_Requisitions VALUES (4,4,2,'Special NDPS Court Mumbai','2025-07-20',5,'PENDING','2025-05-10');

INSERT INTO Audit_Log VALUES (1,'EVIDENCE','INSERT',1,1,'2025-01-15 10:00:00',NULL,'EV_ID=1|Case=1|Cat=WEAPON|Cust=1|Seal=SEAL-EV-001',NULL);
INSERT INTO Audit_Log VALUES (2,'EVIDENCE','INSERT',2,2,'2025-01-15 10:05:00',NULL,'EV_ID=2|Case=1|Cat=BIOLOGICAL|Cust=2|Seal=SEAL-EV-002',NULL);
INSERT INTO Audit_Log VALUES (3,'EVIDENCE','UPDATE',3,2,'2025-01-18 14:30:00','Cust=2|Loc=CFSL Digital Lab|Cond=DAMAGED','Cust=2|Loc=CFSL Digital Lab|Cond=DAMAGED',NULL);
INSERT INTO Audit_Log VALUES (4,'CUSTODY_TRANSFERS','UPDATE',1,NULL,'2025-01-16 09:00:00',NULL,NULL,'TAMPER ATTEMPT on Transfer_ID=1');
"""

def init():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing DB.")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.executescript(SEED)
    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")

if __name__ == '__main__':
    init()
