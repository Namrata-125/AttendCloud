import csv
import os
from datetime import datetime
from config import Config

def generate_attendance_csv(records, filename_prefix="attendance_report"):
    """
    Generate a formatted CSV attendance report file in the exports staging directory.
    
    :param records: List of sqlite3.Row or dict records containing attendance details
    :param filename_prefix: Prefix for generated report filename
    :return: dict with {filepath, filename, record_count, file_size_bytes}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_filename = f"{filename_prefix}_{timestamp}.csv"
    os.makedirs(Config.EXPORTS_DIR, exist_ok=True)
    filepath = os.path.join(Config.EXPORTS_DIR, clean_filename)

    fieldnames = [
        'Roll Number',
        'Student Name',
        'Email',
        'Department',
        'Semester',
        'Date',
        'Status',
        'Remarks',
        'Marked At'
    ]

    with open(filepath, mode='w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in records:
            writer.writerow({
                'Roll Number': row['roll_number'],
                'Student Name': row['full_name'],
                'Email': row['email'] if 'email' in row.keys() else '',
                'Department': row['department'],
                'Semester': row['semester'],
                'Date': row['attendance_date'],
                'Status': row['status'],
                'Remarks': row['remarks'] or '',
                'Marked At': row['marked_at']
            })

    file_size_bytes = os.path.getsize(filepath)

    return {
        'filename': clean_filename,
        'filepath': filepath,
        'record_count': len(records),
        'file_size_bytes': file_size_bytes
    }
