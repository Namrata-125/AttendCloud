-- AttendCloud Database Schema
-- Relational SQLite schema for students, daily attendance, and archival audit logs

PRAGMA foreign_keys = ON;

-- 1. Students Table
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_number TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    semester TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
    remarks TEXT,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE(student_id, attendance_date)
);

-- 3. Cloud / HDFS Archival Audit Logs Table
CREATE TABLE IF NOT EXISTS archive_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    record_count INTEGER DEFAULT 0,
    date_range TEXT,
    archive_type TEXT NOT NULL DEFAULT 'Local Staging' CHECK(archive_type IN ('Local Staging', 'HDFS Live', 'HDFS Simulated')),
    hdfs_destination TEXT,
    status TEXT NOT NULL DEFAULT 'Stored_Local' CHECK(status IN ('Stored_Local', 'Synced_HDFS', 'Pending_HDFS_Config')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Helpful indices for rapid querying on large attendance sheets
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_number);

-- Seed initial demonstration students if table is empty
INSERT OR IGNORE INTO students (id, roll_number, full_name, email, department, semester, status) VALUES
(1, 'CS2026-001', 'Aarav Sharma', 'aarav.sharma@attendcloud.local', 'Computer Science', 'Semester 6', 'Active'),
(2, 'CS2026-002', 'Diya Patel', 'diya.patel@attendcloud.local', 'Computer Science', 'Semester 6', 'Active'),
(3, 'CS2026-003', 'Rohan Verma', 'rohan.verma@attendcloud.local', 'Information Technology', 'Semester 6', 'Active'),
(4, 'CS2026-004', 'Sneha Kulkarni', 'sneha.k@attendcloud.local', 'Computer Science', 'Semester 6', 'Active'),
(5, 'CS2026-005', 'Vikram Malhotra', 'vikram.m@attendcloud.local', 'Cloud Computing', 'Semester 8', 'Active');
