from datetime import date, datetime

from django.db import models


class Employee(models.Model):
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    joined_on = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "employee"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Attendance(models.Model):
    STATUS = [("P", "Present"), ("A", "Absent"), ("H", "Half day"), ("L", "Leave")]
    emp = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField(default=date.today)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS, default="P")

    class Meta:
        db_table = "attendance"
        unique_together = ("emp", "date")
        ordering = ["-date", "emp__name"]

    @property
    def hours(self):
        if self.check_in and self.check_out:
            a = datetime.combine(self.date, self.check_in)
            b = datetime.combine(self.date, self.check_out)
            return round((b - a).total_seconds() / 3600, 2)
        return None


class Salary(models.Model):
    emp = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="salaries")
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    absent_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    per_day_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross = models.DecimalField(max_digits=10, decimal_places=2)
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net = models.DecimalField(max_digits=10, decimal_places=2)
    generated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "salary"
        unique_together = ("emp", "month", "year")
        ordering = ["-year", "-month", "emp__name"]
