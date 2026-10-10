from django import forms

from .models import Attendance, Employee

D = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
T = forms.TimeInput(attrs={"type": "time"}, format="%H:%M")


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["name", "designation", "basic_salary", "email", "phone", "joined_on", "is_active"]
        widgets = {"joined_on": D}


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["emp", "date", "status", "check_in", "check_out"]
        widgets = {"date": D, "check_in": T, "check_out": T}
        labels = {"emp": "Employee"}
