from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import date
from app.database import get_db

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/', methods=['GET', 'POST'])
def mark():
    db = get_db()
    
    # Selected date defaults to current local date
    selected_date = request.args.get('date', date.today().isoformat()).strip()
    department = request.args.get('department', '').strip()

    if request.method == 'POST':
        # Target date from post form
        post_date = request.form.get('attendance_date', selected_date).strip()
        if not post_date:
            post_date = date.today().isoformat()

        # Collect student entries
        student_ids = request.form.getlist('student_ids')
        if not student_ids:
            flash("No students were selected for attendance marking.", "warning")
            return redirect(url_for('attendance.mark', date=post_date, department=department))

        marked_count = 0
        present_count = 0
        absent_count = 0

        for s_id in student_ids:
            status = request.form.get(f'status_{s_id}', 'Absent')
            remarks = request.form.get(f'remarks_{s_id}', '').strip()

            if status not in ('Present', 'Absent'):
                status = 'Absent'

            # Atomic Upsert into attendance table
            db.execute("""
                INSERT INTO attendance (student_id, attendance_date, status, remarks, marked_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id, attendance_date) DO UPDATE SET
                    status = excluded.status,
                    remarks = excluded.remarks,
                    marked_at = CURRENT_TIMESTAMP
            """, (s_id, post_date, status, remarks))

            marked_count += 1
            if status == 'Present':
                present_count += 1
            else:
                absent_count += 1

        db.commit()
        flash(
            f"Attendance successfully recorded for {marked_count} students on {post_date}! "
            f"({present_count} Present, {absent_count} Absent)",
            "success"
        )
        return redirect(url_for('attendance.mark', date=post_date, department=department))

    # GET Request: Fetch students and their recorded status for the selected date
    query = """
        SELECT 
            s.id,
            s.roll_number,
            s.full_name,
            s.department,
            s.semester,
            a.status AS current_status,
            a.remarks AS current_remarks
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND a.attendance_date = ?
        WHERE s.status = 'Active'
    """
    params = [selected_date]

    if department:
        query += " AND s.department = ?"
        params.append(department)

    query += " ORDER BY s.roll_number ASC"
    students_attendance = db.execute(query, params).fetchall()

    # Department list for quick filter
    departments = db.execute("SELECT DISTINCT department FROM students WHERE status = 'Active' ORDER BY department ASC").fetchall()

    # Stats for the day
    total_active = len(students_attendance)
    marked_present = sum(1 for s in students_attendance if s['current_status'] == 'Present')
    marked_absent = sum(1 for s in students_attendance if s['current_status'] == 'Absent')
    unmarked = total_active - (marked_present + marked_absent)

    return render_template(
        'attendance/mark.html',
        selected_date=selected_date,
        selected_department=department,
        students=students_attendance,
        departments=[d['department'] for d in departments if d['department']],
        total_active=total_active,
        marked_present=marked_present,
        marked_absent=marked_absent,
        unmarked=unmarked
    )
