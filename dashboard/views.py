from django.shortcuts import render
from django.utils import timezone
from employees.models import Employee
from attendance.models import Attendance  # Tumeongeza import hii

def admin_overview(request):
    today = timezone.now().date()
    
    # 1. Wafanyakazi Wote
    all_employees = Employee.objects.all()
    total_employees = all_employees.count()
    
    # 2. Mahudhurio ya Leo
    today_logs = Attendance.objects.filter(attendance_date=today).select_related('employee')
    
    # 3. Takwimu za Cards za Juu
    present_today = today_logs.count()
    late_today = today_logs.filter(is_late=True).count()
    
    context = {
        'all_employees': all_employees,
        'total_employees': total_employees,
        'present_today': present_today,
        'late_today': late_today,
        'on_leave_or_absent': 0,
        'pending_requests': 0,
        'today_logs': today_logs,  # Sasa hivi inabeba mahudhurio ya leo
    }
    return render(request, 'dashboard/admin_overview.html', context)