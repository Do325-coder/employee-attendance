import calendar
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import AttendanceForm, EmployeeForm
from .models import Attendance, Employee, Salary

CENT = Decimal("0.01")


def period(request):
    """Month/year filter shared by report, attendance log and payroll."""
    today = timezone.localdate()
    try:
        month, year = int(request.GET.get("month", today.month)), int(request.GET.get("year", today.year))
        if not 1 <= month <= 12:
            raise ValueError
    except ValueError:
        month, year = today.month, today.year
    return {
        "month": month, "year": year,
        "months": [(i, calendar.month_name[i]) for i in range(1, 13)],
        "years": range(today.year - 3, today.year + 2),
    }


def summary(month, year):
    """Per-employee attendance totals + salary: net = basic - (absent_days x per_day_pay)."""
    f = Q(attendance__date__month=month, attendance__date__year=year)
    emps = Employee.objects.filter(is_active=True).annotate(
        present=Count("attendance", filter=f & Q(attendance__status="P")),
        half=Count("attendance", filter=f & Q(attendance__status="H")),
        absent=Count("attendance", filter=f & Q(attendance__status="A")),
        leave=Count("attendance", filter=f & Q(attendance__status="L")),
    )
    days = calendar.monthrange(year, month)[1]
    rows = []
    for e in emps:
        per_day = (e.basic_salary / days).quantize(CENT)
        absent_days = Decimal(e.absent) + Decimal(e.half) / 2
        deduction = min((absent_days * per_day).quantize(CENT), e.basic_salary)
        rows.append({"emp": e, "present": e.present, "half": e.half, "absent": e.absent,
                     "leave": e.leave, "absent_days": absent_days, "per_day": per_day,
                     "deduction": deduction, "net": e.basic_salary - deduction})
    return rows


@login_required
def dashboard(request):
    today = timezone.localdate()
    total = Employee.objects.filter(is_active=True).count()
    recs = Attendance.objects.filter(date=today, emp__is_active=True)
    ctx = {
        "total": total,
        "present": recs.filter(status__in=["P", "H"]).count(),
        "absent": recs.filter(status="A").count(),
        "leave": recs.filter(status="L").count(),
        "unmarked": total - recs.count(),
        "payroll": Salary.objects.filter(month=today.month, year=today.year).aggregate(t=Sum("net"))["t"] or 0,
        "recent": recs.select_related("emp")[:8],
        "today": today,
    }
    return render(request, "dashboard.html", ctx)


# ---------- Employees ----------
class Base(LoginRequiredMixin, SuccessMessageMixin):
    template_name = "form.html"
    title = ""

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx["title"] = self.title
        return ctx


class EmployeeList(LoginRequiredMixin, ListView):
    template_name = "employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        qs = Employee.objects.all()
        q, status = self.request.GET.get("q", ""), self.request.GET.get("status", "")
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(designation__icontains=q))
        if status in ("active", "inactive"):
            qs = qs.filter(is_active=status == "active")
        return qs

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx.update(q=self.request.GET.get("q", ""), status=self.request.GET.get("status", ""))
        return ctx


class EmployeeCreate(Base, CreateView):
    model, form_class, title = Employee, EmployeeForm, "Add employee"
    success_url, success_message = reverse_lazy("employee_list"), "Employee added."


class EmployeeUpdate(Base, UpdateView):
    model, form_class, title = Employee, EmployeeForm, "Edit employee"
    success_url, success_message = reverse_lazy("employee_list"), "Employee updated."


class EmployeeDelete(Base, DeleteView):
    model, title, template_name = Employee, "Delete employee", "confirm_delete.html"
    success_url, success_message = reverse_lazy("employee_list"), "Employee deleted."


# ---------- Attendance ----------
@login_required
def attendance_today(request):
    today = timezone.localdate()
    if request.method == "POST":
        emp = get_object_or_404(Employee, pk=request.POST.get("emp_id"))
        action = request.POST.get("action")
        now = timezone.localtime().time().replace(microsecond=0)
        rec, _ = Attendance.objects.get_or_create(emp=emp, date=today)
        if action == "check_in":
            rec.check_in, rec.status = now, "P"
        elif action == "check_out":
            rec.check_out = now
        elif action in ("A", "H", "L"):
            rec.status = action
            if action in ("A", "L"):
                rec.check_in = rec.check_out = None
        rec.save()
        messages.success(request, f"{emp.name}: updated.")
        return redirect("attendance_today")
    records = {a.emp_id: a for a in Attendance.objects.filter(date=today)}
    rows = [(e, records.get(e.id)) for e in Employee.objects.filter(is_active=True)]
    return render(request, "attendance_today.html", {"rows": rows, "today": today})


class AttendanceList(LoginRequiredMixin, ListView):
    template_name = "attendance_list.html"
    context_object_name = "records"

    def get_queryset(self):
        p = period(self.request)
        qs = Attendance.objects.select_related("emp").filter(date__month=p["month"], date__year=p["year"])
        emp = self.request.GET.get("emp")
        return qs.filter(emp_id=emp) if emp else qs

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx.update(period(self.request))
        ctx.update(employees=Employee.objects.all(), emp=self.request.GET.get("emp", ""))
        return ctx


class AttendanceCreate(Base, CreateView):
    model, form_class, title = Attendance, AttendanceForm, "Add attendance entry"
    success_url, success_message = reverse_lazy("attendance_list"), "Attendance saved."


class AttendanceUpdate(Base, UpdateView):
    model, form_class, title = Attendance, AttendanceForm, "Edit attendance entry"
    success_url, success_message = reverse_lazy("attendance_list"), "Attendance updated."


class AttendanceDelete(Base, DeleteView):
    model, title, template_name = Attendance, "Delete attendance entry", "confirm_delete.html"
    success_url, success_message = reverse_lazy("attendance_list"), "Entry deleted."


# ---------- Reports & payroll ----------
@login_required
def monthly_report(request):
    p = period(request)
    rows = summary(p["month"], p["year"])
    p.update(rows=rows, total_net=sum(r["net"] for r in rows), total_ded=sum(r["deduction"] for r in rows),
             month_name=calendar.month_name[p["month"]])
    return render(request, "report.html", p)


@login_required
def payroll(request):
    p = period(request)
    if request.method == "POST":
        for r in summary(p["month"], p["year"]):
            Salary.objects.update_or_create(
                emp=r["emp"], month=p["month"], year=p["year"],
                defaults={"absent_days": r["absent_days"], "per_day_pay": r["per_day"],
                          "gross": r["emp"].basic_salary, "deduction": r["deduction"], "net": r["net"]})
        messages.success(request, "Payroll generated.")
        return redirect(f"{request.path}?month={p['month']}&year={p['year']}")
    slips = Salary.objects.select_related("emp").filter(month=p["month"], year=p["year"])
    p.update(slips=slips, total=slips.aggregate(t=Sum("net"))["t"] or 0,
             month_name=calendar.month_name[p["month"]])
    return render(request, "payroll.html", p)


@login_required
def slip(request, pk):
    s = get_object_or_404(Salary.objects.select_related("emp"), pk=pk)
    f = Q(date__month=s.month, date__year=s.year)
    counts = s.emp.attendance.aggregate(
        present=Count("id", filter=f & Q(status="P")), half=Count("id", filter=f & Q(status="H")),
        absent=Count("id", filter=f & Q(status="A")), leave=Count("id", filter=f & Q(status="L")))
    return render(request, "slip.html", {"s": s, "c": counts, "month_name": calendar.month_name[s.month]})
