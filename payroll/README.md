# PayTrack: Employee Attendance and Payroll (Django)

Track daily attendance and generate monthly salary slips.
Stack: Python, Django, SQL (SQLite), HTML, CSS.

## Run it
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py seed_demo      # optional: demo login + 5 employees + this month's attendance
python manage.py runserver
```
Open http://127.0.0.1:8000/ and sign in with `admin` / `admin123` (created by `seed_demo`).
To make your own login instead: `python manage.py createsuperuser`.

## Menu
- **Dashboard**: today's counts, net payroll, latest check-ins
- **Employees**: list with search/filter, add, edit, delete
- **Attendance**: today's check-in/out (with half day, leave, absent), attendance log with month/year/employee filter, manual entries
- **Reports**: monthly attendance report with deductions (print-friendly)
- **Payroll**: generate salary register for a month, open a printable salary slip (Print, then Save as PDF)
- Light/dark theme toggle, mobile-friendly menu

## Salary formula
`per_day_pay = basic / days in month`
`absent_days = absent + half-days / 2` (paid leave is not deducted)
`net = basic - (absent_days x per_day_pay)`

## Files
- `core/models.py`: Employee, Attendance, Salary (tables `employee`, `attendance`, `salary`)
- `core/views.py`: pages, filters, GROUP BY style aggregation, payroll
- `core/templates/`: HTML; `core/static/css/style.css`: styling and print CSS
- `schema.sql`: standalone SQL schema, sample data and report queries
- `payroll_project/settings.py`: set `TIME_ZONE` to yours

## Deliverables checklist
Source code, `schema.sql` (or `db.sqlite3` after running the steps above), 5-6 screenshots, this README.
