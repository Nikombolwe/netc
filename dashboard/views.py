from django.shortcuts import render
from django.utils import timezone
from employees.models import Employee
from attendance.models import Attendance

def admin_overview(request):
    # 1. Tumia Local Time kuoanisha tarehe na ukanda wa muda
    today = timezone.localtime(timezone.now()).date()
    
    # 2. Wafanyakazi Wote pamoja na Idara zao
    all_employees = Employee.objects.all().select_related('department')
    total_employees = all_employees.count()
    
    # 3. Mahudhurio ya Leo (Tumeondoa 'officer' kuzuia kosa la MySQL)
    today_logs = Attendance.objects.filter(attendance_date=today).select_related('employee', 'employee__department')
    
    # 4. Takwimu za Cards za Juu
    present_today = today_logs.count()
    
    # Kadi ya waliochelewa (Inaangalia status='LATE' kwa usahihi)
    late_today = today_logs.filter(status__iexact='LATE').count()
    
    # Waliokosa / Likizo
    on_leave_or_absent = max(0, total_employees - present_today)
    
    context = {
        'all_employees': all_employees,
        'total_employees': total_employees,
        'present_today': present_today,
        'late_today': late_today,  # Sasa itasoma 3
        'on_leave_or_absent': on_leave_or_absent,
        'pending_requests': 0,
        'today_logs': today_logs,
    }
    return render(request, 'dashboards/admin_overview.html', context)