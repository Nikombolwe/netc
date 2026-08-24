from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Department, OfficerPosition
from .forms import UserRegistrationForm, EmployeeProfileForm, OfficerProfileForm

# Import sahihi ya model ya Attendance
try:
    from attendance.models import Attendance
except ImportError:
    Attendance = None

try:
    from leaves.models import LeaveBalance, RequestApplication
except ImportError:
    LeaveBalance = None
    RequestApplication = None


# --------------------------------------------------------
# 1. USAJILI WA MTUMIAJI MPYA (ADD USER)
# --------------------------------------------------------
def add_user_view(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        emp_form = EmployeeProfileForm(request.POST)
        officer_form = OfficerProfileForm(request.POST)

        user_type = request.POST.get('user_type')
        fp_credential = request.POST.get('fingerprint_credential_id', '')

        if user_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    user.set_password(user_form.cleaned_data['password'])
                    user.save()

                    if user_type == 'officer':
                        if officer_form.is_valid():
                            officer = officer_form.save(commit=False)
                            officer.user = user
                            if hasattr(officer, 'fingerprint_id'):
                                officer.fingerprint_id = fp_credential
                            officer.save()
                            messages.success(request, f"Officer {officer.first_name} amesajiliwa kikamilifu!")
                            return redirect('add_user')
                        else:
                            raise ValueError(f"Kuna makosa kwenye fomu ya Officer: {officer_form.errors}")

                    elif user_type in ['employee', 'director']:
                        if emp_form.is_valid():
                            employee = emp_form.save(commit=False)
                            employee.user = user
                            if user_type == 'director':
                                employee.is_director = True
                            if hasattr(employee, 'fingerprint_id'):
                                employee.fingerprint_id = fp_credential
                            employee.save()
                            messages.success(request, f"{'Director' if user_type == 'director' else 'Employee'} {employee.first_name} amesajiliwa kikamilifu!")
                            return redirect('add_user')
                        else:
                            raise ValueError(f"Kuna makosa kwenye fomu ya Mfanyakazi: {emp_form.errors}")

            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, f"Kuna makosa kwenye taarifa za Akaunti: {user_form.errors}")

    else:
        user_form = UserRegistrationForm()
        emp_form = EmployeeProfileForm()
        officer_form = OfficerProfileForm()

    context = {
        'user_form': user_form,
        'emp_form': emp_form,
        'officer_form': officer_form,
        'departments': Department.objects.all(),
        'positions': OfficerPosition.objects.all(),
    }
    return render(request, 'employees/add_user.html', context)


# --------------------------------------------------------
# 2. DASHBOARD VIEWS
# --------------------------------------------------------

@login_required
def employee_dashboard(request):
    """Dashboard ya Mfanyakazi wa kawaida na Takwimu za Mahudhurio/Likizo"""
    user = request.user
    today = timezone.now().date()
    employee = getattr(user, 'employee_profile', None)
    
    # 1. Maombi ya Ruhusa na Likizo (POST Request)
    if request.method == 'POST' and RequestApplication is not None:
        req_type = request.POST.get('request_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')

        if not end_date:
            end_date = start_date

        if start_date and reason:
            RequestApplication.objects.create(
                user=user,
                request_type=req_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason
            )
            messages.success(request, "Ombi lako limetumwa kikamilifu!")
            return redirect('employee_dashboard')
        else:
            messages.error(request, "Tafadhali jaza tarehe na sababu ya ombi kikamilifu.")

    # 2. Salio la Likizo / Dharura
    balance = None
    if LeaveBalance is not None:
        balance, _ = LeaveBalance.objects.get_or_create(user=user)

    # 3. Takwimu za Mahudhurio za Mwezi Huu
    on_time_count = 0
    late_count = 0

    if Attendance is not None and employee:
        month_attendances = Attendance.objects.filter(
            employee=employee,
            attendance_date__year=today.year,
            attendance_date__month=today.month
        )

        # Inakamata kuchelewa ikiwa is_late=True AU status='LATE'
        late_count = month_attendances.filter(
            Q(is_late=True) | Q(status='LATE')
        ).count()

        # Inakamata waliowahi (status ni PRESENT na hawajachelewa)
        on_time_count = month_attendances.filter(
            status='PRESENT', 
            is_late=False
        ).count()

    # 4. Muhtasari wa Maombi ya Likizo/Ruhusa
    user_requests = RequestApplication.objects.filter(user=user) if RequestApplication is not None else []
    
    context = {
        'employee': employee,
        'balance': balance,
        'on_time_count': on_time_count,
        'late_count': late_count,
        'req_late_count': user_requests.filter(request_type='LATE_ARRIVAL').count() if user_requests else 0,
        'req_absence_count': user_requests.filter(request_type='ABSENCE').count() if user_requests else 0,
        'req_leave_count': user_requests.filter(request_type='ANNUAL_LEAVE').count() if user_requests else 0,
        'recent_requests': user_requests.order_by('-id')[:5] if user_requests else [],
    }
    return render(request, 'dashboards/employee_dashboard.html', context)


@login_required
def director_dashboard(request):
    """Dashboard ya Mkurugenzi wa Idara"""
    director = getattr(request.user, 'employee_profile', None)
    context = {
        'director': director,
    }
    return render(request, 'dashboards/director_dashboard.html', context)


@login_required
def officer_dashboard(request):
    """Dashboard ya Maofisa (Mwenyekiti, Katibu, Mhazini)"""
    officer = getattr(request.user, 'officer_profile', None)
    context = {
        'officer': officer,
    }
    return render(request, 'dashboards/officer_dashboard.html', context)