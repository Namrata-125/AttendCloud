from flask import Blueprint, render_template
from datetime import date
from app.database import get_db
from app.services.hdfs_service import CloudArchivalController

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    db = get_db()
    today_str = date.today().isoformat()

    # 1. Total Student Counts
    total_students = db.execute("SELECT COUNT(*) AS count FROM students").fetchone()['count']
    active_students = db.execute("SELECT COUNT(*) AS count FROM students WHERE status = 'Active'").fetchone()['count']
    inactive_students = total_students - active_students

    # 2. Today's Attendance Statistics
    today_stats = db.execute("""
        SELECT 
            COUNT(*) AS total_marked,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present_count,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent_count
        FROM attendance
        WHERE attendance_date = ?
    """, (today_str,)).fetchone()

    total_marked_today = today_stats['total_marked'] or 0
    present_today = today_stats['present_count'] or 0
    absent_today = today_stats['absent_count'] or 0

    if active_students > 0:
        attendance_rate_today = round((present_today / active_students) * 100, 1)
    else:
        attendance_rate_today = 0.0

    # 3. Overall All-Time Attendance Metrics
    all_time_stats = db.execute("""
        SELECT 
            COUNT(*) AS total_records,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS total_present
        FROM attendance
    """).fetchone()

    total_all_time = all_time_stats['total_records'] or 0
    total_present_all_time = all_time_stats['total_present'] or 0
    overall_percentage = round((total_present_all_time / total_all_time) * 100, 1) if total_all_time > 0 else 0.0

    # 4. Recent Attendance Activity
    recent_logs = db.execute("""
        SELECT 
            a.id,
            a.attendance_date,
            a.status,
            a.remarks,
            a.marked_at,
            s.roll_number,
            s.full_name,
            s.department
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.marked_at DESC, a.id DESC
        LIMIT 8
    """).fetchall()

    # 5. Cloud Archival & Controller Health
    cloud_controller = CloudArchivalController()
    cluster_status = cloud_controller.get_cluster_status()
    total_archives = db.execute("SELECT COUNT(*) AS count FROM archive_logs").fetchone()['count']

    return render_template(
        'dashboard.html',
        today_date=today_str,
        total_students=total_students,
        active_students=active_students,
        inactive_students=inactive_students,
        total_marked_today=total_marked_today,
        present_today=present_today,
        absent_today=absent_today,
        attendance_rate_today=attendance_rate_today,
        overall_percentage=overall_percentage,
        recent_logs=recent_logs,
        cluster_status=cluster_status,
        total_archives=total_archives
    )
