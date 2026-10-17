# AttendCloud: A LAN-Based SaaS Attendance Management System
### Using HDFS and a Custom Cloud Controller

AttendCloud is a lightweight, high-performance Software-as-a-Service (SaaS) attendance management platform designed for Cloud Computing mini-projects. It operates locally over a Local Area Network (LAN), allowing instructors, students, and lab administrators to access attendance records from any device on the same Wi-Fi network without requiring third-party cloud hosting.

---

## 🌟 Key Features

1. **Executive SaaS Dashboard**:
   - Live KPI cards: Total enrolled students, today's attendance rate, present count, absent count.
   - Live Custom Cloud Controller status widget.
   - Real-time recent attendance feed.
2. **Student Management (Full CRUD)**:
   - Register, update, and search students by roll number, name, department, or status.
   - Automatically tracks historical attendance percentages per student.
3. **Daily Attendance Register**:
   - Single-click **"Mark All Present"** and **"Mark All Absent"** bulk controls.
   - Atomic SQLite upserts ensuring no duplicate attendance entries per day.
   - Remarks and notes for individual student tracking.
4. **Attendance Analytics & CSV Reporting**:
   - Multi-criteria filter: Date range, student, department, and status.
   - Direct-to-browser CSV spreadsheet export (Excel/Sheets ready with UTF-8 BOM).
5. **Custom Cloud Controller & HDFS Architecture**:
   - **Phase 1 (Current)**: Staged local cloud archival in the `exports/` directory with full database audit logging.
   - **Phase 2 (Hadoop Integration)**: Pre-wired WebHDFS REST API adapter ready for seamless upload to an Apache Hadoop cluster.
6. **Zero-Configuration LAN Access**:
   - Bound to `0.0.0.0:5000` with automated local IPv4 autodetection printed in the terminal on startup.

---

## 🏛️ System Architecture

```text
       +-------------------------------------------------------------+
       |                  LAN Clients (Phones / Laptops)             |
       |                   http://<HOST_LAN_IP>:5000                 |
       +------------------------------+------------------------------+
                                      | HTTP Requests
                                      v
       +-------------------------------------------------------------+
       |               AttendCloud Flask Application Server          |
       |                      (Host: 0.0.0.0, Port: 5000)            |
       +------------------------------+------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+------------------+                                    +--------------------+
| SQLite Database  |                                    | Custom Cloud       |
| data/attendcloud |                                    | Controller Engine  |
+------------------+                                    +---------+----------+
                                                                  |
                                      +---------------------------+---------------------------+
                                      |                                                       |
                                      v                                                       v
                         [Phase 1: Local Staging]                                [Phase 2: Live Cluster]
                         exports/attendance_*.csv                                Apache Hadoop HDFS
                         (Local Cloud Archive)                                   WebHDFS (:9870)
```

---

## 📁 Project Structure

```text
AttendCloud/
├── config.py                 # Configuration settings (paths, network port, HDFS parameters)
├── run.py                    # Entry point; detects LAN IP & launches server on 0.0.0.0
├── requirements.txt          # Python dependencies (Flask)
├── README.md                 # Project documentation and setup guide
│
├── app/
│   ├── __init__.py           # Flask app factory, blueprint registration & DB setup
│   ├── database.py           # SQLite connection pooling & auto-initialization
│   ├── schema.sql            # Table definitions (students, attendance, archive_logs)
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py      # Analytics & dashboard route
│   │   ├── students.py       # Student CRUD operations
│   │   ├── attendance.py     # Attendance marking and upsert logic
│   │   └── reports.py        # Date filters, CSV download, and HDFS trigger
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── export_service.py # Formats and writes CSV reports
│   │   └── hdfs_service.py   # Cloud Controller & WebHDFS archival adapter
│   │
│   ├── static/
│   │   ├── css/style.css     # Modern SaaS theme, cards, pill switches & animations
│   │   └── js/main.js        # Bulk attendance controls & live table search
│   │
│   └── templates/
│       ├── base.html         # Master layout with responsive navbar & alerts
│       ├── dashboard.html    # SaaS overview with statistics cards
│       ├── students/
│       │   ├── index.html    # Student directory table with search
│       │   └── form.html     # Add / Edit student form
│       ├── attendance/
│       │   └── mark.html     # Daily attendance register with pill switches
│       └── reports/
│           └── index.html    # Report filtering, CSV export & HDFS audit logs
│
├── data/
│   ├── .gitkeep
│   └── attendcloud.db        # SQLite database file (created automatically)
│
└── exports/
    ├── .gitkeep
    └── *.csv                 # Staged attendance exports & HDFS archives
```

---

## 🚀 Setup & Execution Guide

### Step 1: Open Terminal in Project Folder
Ensure you are inside the `AttendCloud` directory:
```powershell
cd c:\Users\ndaav\OneDrive\Documents\AttendCloud
```

### Step 2: (Optional) Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application
```powershell
python run.py
```

---

## 🌐 Accessing over Local Area Network (LAN)

When `python run.py` executes, it detects your computer's local IP address and displays:
```text
=================================================================
  AttendCloud: LAN-Based SaaS Attendance Management System
  Powered by Custom Cloud Controller & SQLite (HDFS Ready)
=================================================================
  [+] Local Access URL   : http://localhost:5000
  [+] LAN Access URL     : http://192.168.1.15:5000
  [+] Server Binding     : 0.0.0.0:5000
  [+] Cloud Controller   : AttendCloud-Primary-Controller (Online)
  [+] HDFS Architecture  : Phase 1 (Local Cloud Staging Active)
=================================================================
```

### To access from your phone or another laptop:
1. Connect the mobile phone or secondary laptop to the **same Wi-Fi network**.
2. Open any web browser (Chrome, Safari, Firefox).
3. Type the **LAN Access URL** (e.g. `http://192.168.1.15:5000`).
4. If Windows Firewall prompts for network access on first launch, click **Allow access for Private Networks**.

---

## 🐘 Apache Hadoop HDFS Integration (Phase 2 - Fully Operational)

The storage pipeline in `app/services/hdfs_service.py` is fully integrated and tested with Apache Hadoop via WebHDFS:

1. **Dual Storage Workflow**:
   - **Local Staging**: Whenever an attendance dataset is archived, it is formatted with Excel-compatible UTF-8 BOM encoding and staged in the local `exports/` directory.
   - **Live Cloud Archival**: When `HDFS_ENABLED` is `True`, the Cloud Controller connects to the WebHDFS REST API (`:9870`), requests file creation from the NameNode, resolves DataNode redirection endpoints, and streams the dataset directly to HDFS storage (`hdfs://<NAMENODE>:9000/attendcloud/archive/`).
   - **Audit Trail**: Every archival operation records timestamp, record count, file size, storage destination, and synchronization status in SQLite's `archive_logs` table.

2. **Cluster Configuration (`config.py` / Environment Variables)**:
   ```powershell
   $env:HDFS_ENABLED="True"
   $env:HDFS_NAMENODE_HOST="127.0.0.1"
   $env:HDFS_NAMENODE_PORT="9870"
   $env:HDFS_USER="ndaav"
   $env:HDFS_ARCHIVE_DIR="/attendcloud/archive"
   ```

3. **Starting the Hadoop HDFS Cluster (WSL / Linux)**:
   Ensure the Hadoop DFS daemons are active:
   ```bash
   start-dfs.sh
   # Verify that NameNode, DataNode, and SecondaryNameNode are running:
   jps
   ```

4. **Troubleshooting & Permissions**:
   - **HTTP 403 Forbidden (`AccessControlException`)**: Occurs if the HDFS archive directory does not grant write permissions to the configured user. Resolve by granting write access:
     ```bash
     hdfs dfs -chmod 777 /attendcloud/archive
     ```
   - **DataNode Redirect Host Resolution**: In WSL/virtualized clusters, the NameNode may redirect to an internal domain name (`.localdomain`). The Cloud Controller automatically resolves and routes DataNode transfers to reachable host endpoints (`127.0.0.1` / LAN IP).

5. **Verifying HDFS Files**:
   ```bash
   hdfs dfs -ls /attendcloud/archive
   hdfs dfs -cat /attendcloud/archive/<filename>.csv
   ```
