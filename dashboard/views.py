from django.shortcuts import render
from django.utils import timezone
from employees.models import Employee
from attendance.models import Attendance

# Ongeza Import ya RequestApplication
try:
    from leaves.models import RequestApplication
except ImportError:
    RequestApplication = None


def admin_overview(request):
    # 1. Tumia Local Time kuoanisha tarehe na ukanda wa muda
    today = timezone.localtime(timezone.now()).date()
    
    # 2. Wafanyakazi Wote pamoja na Idara zao
    all_employees = Employee.objects.all().select_related('department')
    total_employees = all_employees.count()
    
    # 3. Mahudhurio ya Leo
    today_logs = Attendance.objects.filter(attendance_date=today).select_related('employee', 'employee__department')
    
    # 4. Takwimu za Cards za Juu
    present_today = today_logs.count()
    late_today = today_logs.filter(status__iexact='LATE').count()
    on_leave_or_absent = max(0, total_employees - present_today)
    
    # 5. Hesabu ya Maombi Yaliyopo (Pending Au Maombi Yote)
    pending_requests = 0
    if RequestApplication is not None:
        # Inasoma maombi YOTE yanayosubiri idhini (Pending)
        pending_requests = RequestApplication.objects.filter(status='PENDING').count()
        
        # Kama unataka isome maombi yote bila kujali status (Pending/Approved/Rejected), tumia hii:
        # pending_requests = RequestApplication.objects.count()

    context = {
        'all_employees': all_employees,
        'total_employees': total_employees,
        'present_today': present_today,
        'late_today': late_today,
        'on_leave_or_absent': on_leave_or_absent,
        'pending_requests': pending_requests,  # Sasa itasoma idadi halisi
        'today_logs': today_logs,
    }
    return render(request, 'dashboards/admin_overview.html', context)