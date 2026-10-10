import random
from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import Attendance, Employee


class Command(BaseCommand):
    help = "Create demo login (admin / admin123), employees and this month's attendance."

    def handle(self, *args, **opts):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
        people = [("Asha Verma", "Accountant", 32000), ("Ravi Kumar", "Developer", 55000),
                  ("Meena Rao", "HR Executive", 38000), ("Suresh Babu", "Designer", 42000),
                  ("Lakshmi Devi", "Manager", 70000)]
        for n, d, s in people:
            Employee.objects.get_or_create(name=n, defaults={"designation": d, "basic_salary": s})
        today = date.today()
        day = today.replace(day=1)
        while day <= today:
            if day.weekday() < 6:  # Mon-Sat
                for e in Employee.objects.all():
                    st = random.choices("PAHL", [80, 8, 6, 6])[0]
                    ci, co = (time(9, random.randint(0, 30)), time(17, random.randint(0, 45))) if st in "PH" else (None, None)
                    Attendance.objects.get_or_create(emp=e, date=day, defaults={"status": st, "check_in": ci, "check_out": co})
            day += timedelta(days=1)
        self.stdout.write(self.style.SUCCESS("Demo data ready. Login: admin / admin123"))
