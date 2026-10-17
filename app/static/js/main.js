/**
 * AttendCloud Frontend Interactivity
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss flash alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 6000);
    });

    // 2. Attendance Page: Bulk Mark Controls
    const markAllPresentBtn = document.getElementById('btn-mark-all-present');
    const markAllAbsentBtn = document.getElementById('btn-mark-all-absent');

    if (markAllPresentBtn) {
        markAllPresentBtn.addEventListener('click', () => {
            const presentRadios = document.querySelectorAll('input[type="radio"][value="Present"]');
            presentRadios.forEach(radio => {
                radio.checked = true;
            });
            updateAttendanceSummaryCounter();
        });
    }

    if (markAllAbsentBtn) {
        markAllAbsentBtn.addEventListener('click', () => {
            const absentRadios = document.querySelectorAll('input[type="radio"][value="Absent"]');
            absentRadios.forEach(radio => {
                radio.checked = true;
            });
            updateAttendanceSummaryCounter();
        });
    }

    // Attach change listener to radio buttons to update live summary count
    const attendanceRadios = document.querySelectorAll('.attendance-toggle-group input[type="radio"]');
    attendanceRadios.forEach(radio => {
        radio.addEventListener('change', updateAttendanceSummaryCounter);
    });

    function updateAttendanceSummaryCounter() {
        const presentCount = document.querySelectorAll('input[type="radio"][value="Present"]:checked').length;
        const absentCount = document.querySelectorAll('input[type="radio"][value="Absent"]:checked').length;
        
        const presentCounterEl = document.getElementById('live-present-counter');
        const absentCounterEl = document.getElementById('live-absent-counter');
        
        if (presentCounterEl) presentCounterEl.textContent = presentCount;
        if (absentCounterEl) absentCounterEl.textContent = absentCount;
    }

    // 3. Client-side Quick Table Search (for instant filtering)
    const quickSearchInput = document.getElementById('table-quick-search');
    if (quickSearchInput) {
        quickSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const tableRows = document.querySelectorAll('.filterable-table tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // 4. Confirmation on Delete Form
    const deleteForms = document.querySelectorAll('.confirm-delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const name = form.getAttribute('data-student-name') || 'this student';
            const confirmed = confirm(`Are you sure you want to delete ${name}? All corresponding attendance records will be removed.`);
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});
