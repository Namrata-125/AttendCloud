import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database import get_db

students_bp = Blueprint('students', __name__, url_prefix='/students')

def is_valid_email(email):
    """Simple email syntax verification."""
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(regex, email) is not None

@students_bp.route('/')
def index():
    db = get_db()
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = """
        SELECT 
            s.*,
            COUNT(a.id) AS total_sessions,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (s.roll_number LIKE ? OR s.full_name LIKE ? OR s.email LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    if department:
        query += " AND s.department = ?"
        params.append(department)

    if status_filter:
        query += " AND s.status = ?"
        params.append(status_filter)

    query += " GROUP BY s.id ORDER BY s.roll_number ASC"

    students = db.execute(query, params).fetchall()

    # Distinct departments for filter dropdown
    departments = db.execute("SELECT DISTINCT department FROM students ORDER BY department ASC").fetchall()

    return render_template(
        'students/index.html',
        students=students,
        search=search,
        selected_department=department,
        selected_status=status_filter,
        departments=[d['department'] for d in departments if d['department']]
    )

@students_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip().upper()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        status = request.form.get('status', 'Active').strip()

        # Validation
        if not all([roll_number, full_name, email, department, semester]):
            flash("All required fields must be filled.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=False)

        if not is_valid_email(email):
            flash("Please provide a valid email address.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=False)

        db = get_db()
        # Check uniqueness
        existing_roll = db.execute("SELECT id FROM students WHERE roll_number = ?", (roll_number,)).fetchone()
        if existing_roll:
            flash(f"A student with Roll Number '{roll_number}' already exists.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=False)

        existing_email = db.execute("SELECT id FROM students WHERE email = ?", (email,)).fetchone()
        if existing_email:
            flash(f"Email '{email}' is already registered.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=False)

        try:
            db.execute("""
                INSERT INTO students (roll_number, full_name, email, department, semester, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (roll_number, full_name, email, department, semester, status))
            db.commit()
            flash(f"Student '{full_name}' ({roll_number}) added successfully!", "success")
            return redirect(url_for('students.index'))
        except Exception as e:
            flash(f"Database error while saving student: {str(e)}", "danger")
            return render_template('students/form.html', student=request.form, is_edit=False)

    return render_template('students/form.html', student={}, is_edit=False)

@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
def edit(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        flash("Student record not found.", "warning")
        return redirect(url_for('students.index'))

    if request.method == 'POST':
        roll_number = request.form.get('roll_number', '').strip().upper()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        status = request.form.get('status', 'Active').strip()

        if not all([roll_number, full_name, email, department, semester]):
            flash("All fields are required.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=True, student_id=student_id)

        if not is_valid_email(email):
            flash("Please provide a valid email address.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=True, student_id=student_id)

        # Uniqueness checks (excluding current student)
        existing_roll = db.execute("SELECT id FROM students WHERE roll_number = ? AND id != ?", (roll_number, student_id)).fetchone()
        if existing_roll:
            flash(f"Roll Number '{roll_number}' is already assigned to another student.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=True, student_id=student_id)

        existing_email = db.execute("SELECT id FROM students WHERE email = ? AND id != ?", (email, student_id)).fetchone()
        if existing_email:
            flash(f"Email '{email}' is used by another student.", "danger")
            return render_template('students/form.html', student=request.form, is_edit=True, student_id=student_id)

        try:
            db.execute("""
                UPDATE students 
                SET roll_number = ?, full_name = ?, email = ?, department = ?, semester = ?, status = ?
                WHERE id = ?
            """, (roll_number, full_name, email, department, semester, status, student_id))
            db.commit()
            flash(f"Updated record for '{full_name}' successfully.", "success")
            return redirect(url_for('students.index'))
        except Exception as e:
            flash(f"Error updating student: {str(e)}", "danger")
            return render_template('students/form.html', student=request.form, is_edit=True, student_id=student_id)

    return render_template('students/form.html', student=student, is_edit=True, student_id=student_id)

@students_bp.route('/<int:student_id>/delete', methods=['POST'])
def delete(student_id):
    db = get_db()
    student = db.execute("SELECT full_name, roll_number FROM students WHERE id = ?", (student_id,)).fetchone()
    if not student:
        flash("Student record not found.", "warning")
        return redirect(url_for('students.index'))

    try:
        db.execute("DELETE FROM students WHERE id = ?", (student_id,))
        db.commit()
        flash(f"Student '{student['full_name']}' ({student['roll_number']}) and related attendance records were deleted.", "info")
    except Exception as e:
        flash(f"Failed to delete student: {str(e)}", "danger")

    return redirect(url_for('students.index'))
