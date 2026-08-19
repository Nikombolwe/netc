from django.shortcuts import render
from employees.models import Employee  # Hakikisha hii ipo sahihi

def admin_overview(request):
    # Inavuta wafanyakazi wote pekee bila kuangalia attendance
    all_employees = Employee.objects.all()
    
    context = {
        'all_employees': all_employees,
        'total_employees': all_employees.count(),
        'present_today': 0,
        'late_today': 0,
        'on_leave_or_absent': 0,
        'pending_requests': 0,
        'today_logs': [],  # Haina logs za attendance kwa sasa
    }
    return render(request, 'dashboard/admin_overview.html', context)