from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from datetime import date, timedelta
from app.database import get_db
from app.services.export_service import generate_attendance_csv
from app.services.hdfs_service import CloudArchivalController

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
def index():
    db = get_db()

    # Default date range: past 14 days up to today
    default_end = date.today().isoformat()
    default_start = (date.today() - timedelta(days=14)).isoformat()

    start_date = request.args.get('start_date', default_start).strip()
    end_date = request.args.get('end_date', default_end).strip()
    student_id = request.args.get('student_id', '').strip()
    department = request.args.get('department', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = """
        SELECT 
            a.id,
            a.attendance_date,
            a.status,
            a.remarks,
            a.marked_at,
            s.id AS student_id,
            s.roll_number,
            s.full_name,
            s.email,
            s.department,
            s.semester
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.attendance_date BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if student_id:
        query += " AND s.id = ?"
        params.append(student_id)

    if department:
        query += " AND s.department = ?"
        params.append(department)

    if status_filter:
        query += " AND a.status = ?"
        params.append(status_filter)

    query += " ORDER BY a.attendance_date DESC, s.roll_number ASC"

    records = db.execute(query, params).fetchall()

    # Aggregated metrics for this query
    total_records = len(records)
    total_present = sum(1 for r in records if r['status'] == 'Present')
    total_absent = sum(1 for r in records if r['status'] == 'Absent')
    attendance_rate = round((total_present / total_records * 100), 1) if total_records > 0 else 0.0

    # Options for filters
    all_students = db.execute("SELECT id, roll_number, full_name FROM students ORDER BY roll_number ASC").fetchall()
    departments = db.execute("SELECT DISTINCT department FROM students ORDER BY department ASC").fetchall()

    # Archival audit logs (last 5)
    recent_archives = db.execute("""
        SELECT * FROM archive_logs ORDER BY created_at DESC LIMIT 6
    """).fetchall()

    cloud_status = CloudArchivalController().get_cluster_status()

    return render_template(
        'reports/index.html',
        records=records,
        start_date=start_date,
        end_date=end_date,
        selected_student_id=student_id,
        selected_department=department,
        selected_status=status_filter,
        total_records=total_records,
        total_present=total_present,
        total_absent=total_absent,
        attendance_rate=attendance_rate,
        all_students=all_students,
        departments=[d['department'] for d in departments if d['department']],
        recent_archives=recent_archives,
        cloud_status=cloud_status
    )

@reports_bp.route('/export-csv')
def export_csv():
    db = get_db()
    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat()).strip()
    end_date = request.args.get('end_date', date.today().isoformat()).strip()
    student_id = request.args.get('student_id', '').strip()
    department = request.args.get('department', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = """
        SELECT 
            a.attendance_date,
            a.status,
            a.remarks,
            a.marked_at,
            s.roll_number,
            s.full_name,
            s.email,
            s.department,
            s.semester
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.attendance_date BETWEEN ? AND ?
    """
    params = [start_date, end_date]

    if student_id:
        query += " AND s.id = ?"
        params.append(student_id)

    if department:
        query += " AND s.department = ?"
        params.append(department)

    if status_filter:
        query += " AND a.status = ?"
        params.append(status_filter)

    query += " ORDER BY a.attendance_date DESC, s.roll_number ASC"
    records = db.execute(query, params).fetchall()

    if not records:
        flash("No attendance records found matching the filter criteria to export.", "warning")
        return redirect(url_for('reports.index', start_date=start_date, end_date=end_date))

    csv_info = generate_attendance_csv(records, filename_prefix=f"attendcloud_{start_date}_to_{end_date}")

    return send_file(
        csv_info['filepath'],
        mimetype='text/csv',
        as_attachment=True,
        download_name=csv_info['filename']
    )

@reports_bp.route('/archive-hdfs', methods=['POST'])
def archive_hdfs():
    db = get_db()
    start_date = request.form.get('start_date', '').strip()
    end_date = request.form.get('end_date', '').strip()
    student_id = request.form.get('student_id', '').strip()
    department = request.form.get('department', '').strip()
    status_filter = request.form.get('status', '').strip()

    query = """
        SELECT 
            a.attendance_date,
            a.status,
            a.remarks,
            a.marked_at,
            s.roll_number,
            s.full_name,
            s.email,
            s.department,
            s.semester
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE 1=1
    """
    params = []

    if start_date and end_date:
        query += " AND a.attendance_date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
        date_range_label = f"{start_date} to {end_date}"
    else:
        date_range_label = "All Time"

    if student_id:
        query += " AND s.id = ?"
        params.append(student_id)

    if department:
        query += " AND s.department = ?"
        params.append(department)

    if status_filter:
        query += " AND a.status = ?"
        params.append(status_filter)

    records = db.execute(query, params).fetchall()

    if not records:
        flash("Cannot archive empty dataset. Please adjust filter parameters.", "warning")
        return redirect(url_for('reports.index'))

    # Generate CSV staging file
    csv_info = generate_attendance_csv(records, filename_prefix="hdfs_archive_dataset")

    # Delegate to Cloud Controller & HDFS Service
    controller = CloudArchivalController()
    archive_result = controller.archive_report(
        filepath=csv_info['filepath'],
        filename=csv_info['filename'],
        record_count=csv_info['record_count'],
        date_range=date_range_label
    )

    if archive_result.get('success'):
        flash(
            f"Archival Processed: {archive_result['message']} (Target: {archive_result['destination']})",
            "info"
        )
    else:
        flash(f"Archival Notice: {archive_result['message']}", "warning")

    return redirect(url_for('reports.index', start_date=start_date, end_date=end_date))
