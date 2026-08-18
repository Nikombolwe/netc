from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from employees.models import Employee
from attendance.models import AttendanceRecord
from leaves.models import LeaveRequest

@login_required
@user_passes_test(lambda u: u.role == 'ADMIN')
def admin_overview(request):
    today = timezone.now().date()
    
    context = {
        'total_employees': Employee.objects.filter(is_active_employee=True).count(),
        'present_today': AttendanceRecord.objects.filter(date=today, status='PRESENT').count(),
        'late_today': AttendanceRecord.objects.filter(date=today, status='LATE').count(),
        'on_leave_or_absent': AttendanceRecord.objects.filter(date=today, status__in=['ABSENT', 'ON_LEAVE']).count(),
        'pending_requests': LeaveRequest.objects.filter(status='PENDING').count(),
        'today_logs': AttendanceRecord.objects.filter(date=today).select_related('employee', 'employee__department').order_by('-check_in'),
    }
    return render(request, 'dashboard/admin_overview.html', context)