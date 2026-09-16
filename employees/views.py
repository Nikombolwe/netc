import csv
import logging
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import pytz
from django.core.mail import send_mail
from django.conf import settings

from .models import Department, OfficerPosition, Employee, Officer
from .forms import UserRegistrationForm, EmployeeProfileForm, OfficerProfileForm

# Helper Functions za SMS & Data Extraction
from utils.sms import send_sms_notification

# Logger setup kwa ajili ya kufuatilia makosa (Debugging)
logger = logging.getLogger(__name__)

# Import za App Zingine kwa Usalama
try:
    from attendance.models import Attendance
except ImportError:
    Attendance = None

try:
    from leaves.models import LeaveBalance, RequestApplication
except ImportError:
    LeaveBalance = None
    RequestApplication = None

try:
    from communications.models import SMSLog  # Model ya kuhifadhi status za SMS
except ImportError:
    SMSLog = None


# --------------------------------------------------------
# UTILITY / DECORATORS YA USALAMA (ACCESS CONTROL)
# --------------------------------------------------------
def is_officer(user):
    return user.is_authenticated and (user.is_superuser or hasattr(user, 'officer_profile'))

def is_director(user):
    return user.is_authenticated and (
        user.is_superuser or 
        (hasattr(user, 'employee_profile') and user.employee_profile and user.employee_profile.is_director)
    )


# --------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------
def get_client_ip(request):
    """Inapata Real IP Address ya mteja aliyeunganishwa kwenye mfumo"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_tz_now():
    """Inarudisha muda wa sasa wa Tanzania (East Africa Time)"""
    tz = pytz.timezone('Africa/Dar_es_Salaam')
    return timezone.now().astimezone(tz)


def extract_contact_info(obj):
    """Inasaidia kupata phone number na email kutoka kwa Employee/Officer/User"""
    if not obj:
        return None, None
    
    phone = getattr(obj, 'phone_number', None) or getattr(obj, 'phone', None)
    email = getattr(obj, 'email', None)

    if hasattr(obj, 'user') and obj.user:
        if not phone:
            phone = getattr(obj.user, 'phone_number', None) or getattr(obj.user, 'phone', None)
        if not email:
            email = obj.user.email

    return phone, email


def get_employee_full_name(employee):
    """Inarudisha jina kamili la mfanyakazi kwa usalama bila kujali muundo wake"""
    if not employee:
        return "N/A"
    if hasattr(employee, 'full_name') and not callable(employee.full_name):
        return employee.full_name
    if hasattr(employee, 'get_full_name') and callable(employee.get_full_name):
        return employee.get_full_name()
    
    first = getattr(employee, 'first_name', '')
    last = getattr(employee, 'last_name', '')
    combined = f"{first} {last}".strip()
    return combined if combined else getattr(employee, 'employee_code', 'N/A')


# --------------------------------------------------------
# 1. USAJILI WA MTUMIAJI MPYA (ADD USER)
# --------------------------------------------------------
#@login_required
#@user_passes_test(is_officer)
def add_user_view(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        user_type = request.POST.get('user_type')
        fp_credential = request.POST.get('fingerprint_credential_id', '')

        emp_form = EmployeeProfileForm(request.POST) if user_type in ['employee', 'director'] else None
        officer_form = OfficerProfileForm(request.POST) if user_type == 'officer' else None

        forms_valid = user_form.is_valid()
        if emp_form:
            forms_valid = forms_valid and emp_form.is_valid()
        if officer_form:
            forms_valid = forms_valid and officer_form.is_valid()

        if forms_valid:
            try:
                with transaction.atomic():
                    raw_password = user_form.cleaned_data['password']
                    username = user_form.cleaned_data['username']

                    user = user_form.save(commit=False)
                    user.set_password(raw_password)
                    user.save()

                    phone_number = None
                    full_name = ""
                    emp_code = ""

                    if user_type == 'officer':
                        officer = officer_form.save(commit=False)
                        officer.user = user
                        if hasattr(officer, 'fingerprint_id'):
                            officer.fingerprint_id = fp_credential
                        officer.save()
                        
                        phone_number, _ = extract_contact_info(officer)
                        full_name = get_employee_full_name(officer)
                        emp_code = getattr(officer, 'officer_code', getattr(officer, 'employee_code', 'N/A'))
                        messages.success(request, f"Officer {full_name} amesajiliwa kikamilifu!")

                    elif user_type in ['employee', 'director']:
                        employee = emp_form.save(commit=False)
                        employee.user = user
                        if user_type == 'director':
                            employee.is_director = True
                        if hasattr(employee, 'fingerprint_id'):
                            employee.fingerprint_id = fp_credential
                        employee.save()
                        
                        phone_number, _ = extract_contact_info(employee)
                        full_name = get_employee_full_name(employee)
                        emp_code = getattr(employee, 'employee_code', 'N/A')

                        # Tengeneza LeaveBalance ya kuanzia (28 Annual, 12 Emergency) moja kwa moja
                        if LeaveBalance is not None:
                            LeaveBalance.objects.get_or_create(
                                user=user,
                                defaults={
                                    'annual_leave_days': 28,
                                    'emergency_leave_count': 12
                                }
                            )

                        role_label = 'Director' if user_type == 'director' else 'Employee'
                        messages.success(request, f"{role_label} {full_name} amesajiliwa kikamilifu!")

                    if phone_number:
                        sms_message = (
                            f"Habari {full_name}, akaunti yako ya Smart Attendance imefunguliwa.\n"
                            f"Username: {username}\n"
                            f"Password: {raw_password}\n"
                            f"Employee Code: {emp_code}\n"
                            f"Itumie hii kwenye mfumo wa mahudhurio."
                        )
                        send_sms_notification(phone_number, sms_message)

                    return redirect('employees:add_user')

            except Exception as e:
                logger.error(f"[Add User Error]: {str(e)}", exc_info=True)
                messages.error(request, "Kumetokea kosa la kiufundi wakati wa kusajili. Tafadhali jaribu tena.")
        else:
            all_errors = {**user_form.errors}
            if emp_form: all_errors.update(emp_form.errors)
            if officer_form: all_errors.update(officer_form.errors)
            
            clean_errors = ", ".join([f"{field}: {', '.join(errors)}" for field, errors in all_errors.items()])
            messages.error(request, f"Kuna makosa kwenye fomu: {clean_errors}")

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
# 2. EMPLOYEE DASHBOARD (Imeboreshwa kuonyesha data vizuri)
# --------------------------------------------------------
@login_required
def employee_dashboard(request):
    user = request.user
    tz_now = get_tz_now()
    today = tz_now.date()
    employee = getattr(user, 'employee_profile', None)
    
    if request.method == 'POST' and RequestApplication is not None and 'request_type' in request.POST:
        req_type = request.POST.get('request_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or start_date
        reason = request.POST.get('reason')

        if start_date and reason:
            # Hakiki sheria za dharura (Emergency Leave): isizidi mara 1 kwa mwezi na isizidi 12 kwa mwaka
            if req_type == 'EMERGENCY_LEAVE' or req_type == 'EMERGENCY':
                current_month = tz_now.month
                current_year = tz_now.year
                
                # Angalia kama amewahi kuomba dharura mwezi huu
                existing_emergency_this_month = RequestApplication.objects.filter(
                    Q(employee=employee) if employee else Q(user=user),
                    Q(request_type='EMERGENCY_LEAVE') | Q(request_type='EMERGENCY'),
                    start_date__month=current_month,
                    start_date__year=current_year
                ).exists()

                if existing_emergency_this_month:
                    messages.error(request, "Umeshawahi kuomba ruhusa ya dharura kwa mwezi huu. Huruhusiwi kuomba zaidi ya mara moja kwa mwezi!")
                    return redirect('employees:employee_dashboard')

                # Angalia salio la dharura kama lipo
                if LeaveBalance is not None:
                    bal_obj = LeaveBalance.objects.filter(user=user).first()
                    if bal_obj and getattr(bal_obj, 'emergency_leave_count', 0) <= 0:
                        messages.error(request, "Salio lako la siku za dharura limekwisha!")
                        return redirect('employees:employee_dashboard')

            # Tunahakikisha inatumia user au employee kulingana na muundo wa model
            req_data = {
                'request_type': req_type,
                'start_date': start_date,
                'end_date': end_date,
                'reason': reason,
                'status': 'PENDING'
            }
            if 'user' in [f.name for f in RequestApplication._meta.get_fields()]:
                req_data['user'] = user
            elif 'employee' in [f.name for f in RequestApplication._meta.get_fields()] and employee:
                req_data['employee'] = employee

            RequestApplication.objects.create(**req_data)

            emp_phone, _ = extract_contact_info(employee or user)
            full_name = get_employee_full_name(employee) if employee else (f"{user.first_name} {user.last_name}".strip() or user.username)

            if emp_phone:
                msg_emp = f"Habari {full_name}, ombi lako la ruhusa la tarehe {start_date} limepokelewa kikamilifu na linashughulikiwa."
                send_sms_notification(emp_phone, msg_emp)

            if employee and getattr(employee, 'department', None):
                director = Employee.objects.filter(
                    department=employee.department, 
                    is_director=True
                ).first()

                if director:
                    dir_phone, _ = extract_contact_info(director)
                    if dir_phone:
                        msg_dir = f"TAARIFA: Mfanyakazi {full_name} wa idara yako ameomba ruhusa kuanzia {start_date}. Tafadhali ingia kwenye mfumo kuisimamia."
                        send_sms_notification(dir_phone, msg_dir)

            messages.success(request, "Ombi limetumwa na taarifa za SMS zimetumwa kikamilifu!")
            return redirect('employees:employee_dashboard')
        else:
            messages.error(request, "Tafadhali jaza tarehe na sababu ya ombi kikamilifu.")

    # Kuboresha urudishwaji wa LeaveBalance dynamically kwa kutumia get_or_create
    balance = None
    if LeaveBalance is not None and user:
        balance, _ = LeaveBalance.objects.get_or_create(
            user=user,
            defaults={'annual_leave_days': 28, 'emergency_leave_count': 12}
        )

    on_time_count, late_count, today_attendance_record = 0, 0, None

    if Attendance is not None and employee:
        month_attendances = Attendance.objects.filter(
            employee=employee,
            attendance_date__year=today.year,
            attendance_date__month=today.month
        )
        late_count = month_attendances.filter(Q(is_late=True) | Q(status='LATE')).count()
        on_time_count = month_attendances.filter(status='PRESENT', is_late=False).count()
        today_attendance_record = month_attendances.filter(attendance_date=today).first()

    # Kupata maombi ya mtumiaji kwa kuzingatia uwanja uliopo kwenye RequestApplication
    user_requests = []
    if RequestApplication is not None:
        field_names = [f.name for f in RequestApplication._meta.get_fields()]
        if 'user' in field_names:
            user_requests = RequestApplication.objects.filter(user=user)
        elif 'employee' in field_names and employee:
            user_requests = RequestApplication.objects.filter(employee=employee)
    
    context = {
        'employee': employee,
        'balance': balance,
        'on_time_count': on_time_count,
        'late_count': late_count,
        'today_attendance': today_attendance_record,
        'req_late_count': user_requests.filter(Q(request_type='LATE_ARRIVAL') | Q(request_type='LATE')).count() if user_requests else 0,
        'req_absence_count': user_requests.filter(Q(request_type='ABSENCE') | Q(request_type='ABSENT')).count() if user_requests else 0,
        'req_leave_count': user_requests.filter(Q(request_type='ANNUAL_LEAVE') | Q(request_type='LEAVE')).count() if user_requests else 0,
        'recent_requests': user_requests.order_by('-id')[:5] if user_requests else [],
    }
    return render(request, 'dashboards/employee_dashboard.html', context)


# --------------------------------------------------------
# 3. DIRECTOR DASHBOARD & APPROVAL ACTIONS
# --------------------------------------------------------
@login_required
@user_passes_test(is_director)
def director_dashboard(request):
    user = request.user
    tz_now = get_tz_now()
    today = tz_now.date()
    director = getattr(user, 'employee_profile', None)

    director_name = get_employee_full_name(director) if director else (f"{user.first_name} {user.last_name}".strip() or user.username)
    
    target_department = None
    if director:
        target_department = director.department or director.managed_departments.first()

    dept_name = target_department.name if target_department else "Hajawekwa Idara"

    if request.method == 'POST' and RequestApplication is not None:
        req_type = request.POST.get('request_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or start_date
        reason = request.POST.get('reason')

        if start_date and reason:
            req_data = {
                'request_type': req_type,
                'start_date': start_date,
                'end_date': end_date,
                'reason': reason,
                'status': 'PEND_OFF'
            }
            field_names = [f.name for f in RequestApplication._meta.get_fields()]
            if 'user' in field_names:
                req_data['user'] = user
            elif 'employee' in field_names and director:
                req_data['employee'] = director

            RequestApplication.objects.create(**req_data)

            dir_phone, _ = extract_contact_info(director or user)
            if dir_phone:
                msg_dir = f"Habari {director_name}, ombi lako la ruhusa la tarehe {start_date} limepokelewa na limewasilishwa kwa Maofisa."
                send_sms_notification(dir_phone, msg_dir)

            for officer in Officer.objects.all():
                off_phone, _ = extract_contact_info(officer)
                if off_phone:
                    msg_off = f"TAARIFA: Mkurugenzi {director_name} (Idara ya {dept_name}) ameomba ruhusa kuanzia {start_date}. Tafadhali ingia kwenye mfumo kuisimamia."
                    send_sms_notification(off_phone, msg_off)

            messages.success(request, "Ombi lako limetumwa moja kwa moja kwa Maofisa!")
            return redirect('employees:director_dashboard')
        else:
            messages.error(request, "Tafadhali jaza tarehe na sababu ya ombi kikamilifu.")

    balance = None
    if LeaveBalance is not None and user:
        balance, _ = LeaveBalance.objects.get_or_create(
            user=user,
            defaults={'annual_leave_days': 28, 'emergency_leave_count': 12}
        )

    on_time_count, late_count = 0, 0

    if Attendance is not None and director:
        month_attendances = Attendance.objects.filter(
            employee=director,
            attendance_date__year=today.year,
            attendance_date__month=today.month
        )
        late_count = month_attendances.filter(Q(is_late=True) | Q(status='LATE')).count()
        on_time_count = month_attendances.filter(status='PRESENT', is_late=False).count()

    my_requests = []
    if RequestApplication is not None:
        field_names = [f.name for f in RequestApplication._meta.get_fields()]
        if 'user' in field_names:
            my_requests = RequestApplication.objects.filter(user=user).order_by('-id')[:5]
        elif 'employee' in field_names and director:
            my_requests = RequestApplication.objects.filter(employee=director).order_by('-id')[:5]

    department_employees, pending_dept_requests = [], []

    if target_department:
        department_employees = Employee.objects.filter(department=target_department).exclude(user=user)
        if RequestApplication is not None:
            field_names = [f.name for f in RequestApplication._meta.get_fields()]
            if 'user' in field_names:
                pending_dept_requests = RequestApplication.objects.filter(
                    user__employee_profile__department=target_department,
                    status='PENDING'
                ).exclude(user=user).order_by('-id')
            elif 'employee' in field_names:
                pending_dept_requests = RequestApplication.objects.filter(
                    employee__department=target_department,
                    status='PENDING'
                ).exclude(employee=director).order_by('-id')

    context = {
        'director': director,
        'director_name': director_name,
        'dept_name': dept_name,
        'balance': balance,
        'on_time_count': on_time_count,
        'late_count': late_count,
        'my_requests': my_requests,
        'department_employees': department_employees,
        'pending_requests': pending_dept_requests,
    }
    return render(request, 'dashboards/director_dashboard.html', context)


@login_required
@user_passes_test(is_director)
@require_POST
def director_process_request(request, request_id, action):
    if RequestApplication is None:
        return redirect('employees:director_dashboard')

    leave_req = get_object_or_404(RequestApplication, id=request_id)
    emp_user = getattr(leave_req, 'user', getattr(leave_req.employee, 'user', None) if hasattr(leave_req, 'employee') else None)
    employee = getattr(emp_user, 'employee_profile', getattr(leave_req, 'employee', None))
    
    emp_phone, _ = extract_contact_info(employee or emp_user)
    full_name = get_employee_full_name(employee) if employee else (f"{emp_user.first_name} {emp_user.last_name}".strip() or emp_user.username if emp_user else "Mfanyakazi")

    if action == 'reject':
        leave_req.status = 'DIR_REJ'
        leave_req.save()

        if emp_phone:
            msg = f"Habari {full_name}, ombi lako la ruhusa la tarehe {leave_req.start_date} LIMEKATALIWA na Mkurugenzi wako wa Idara."
            send_sms_notification(emp_phone, msg)

        messages.info(request, "Ombi limekataliwa na SMS imetumwa kwa Mfanyakazi.")

    elif action == 'approve':
        leave_req.status = 'PEND_OFF'
        leave_req.save()

        if emp_phone:
            msg_emp = f"Habari {full_name}, Mkurugenzi amethibitisha ombi lako la ruhusa ({leave_req.start_date}). Ombi limetumwa kwa Maofisa kwa idhini ya mwisho."
            send_sms_notification(emp_phone, msg_emp)

        for officer in Officer.objects.all():
            off_phone, _ = extract_contact_info(officer)
            if off_phone:
                msg_officer = f"TAARIFA: Kuna ombi jipya la ruhusa la mfanyakazi {full_name} linalosubiri idhini ya Maofisa. Tafadhali ingia kwenye mfumo."
                send_sms_notification(off_phone, msg_officer)

        messages.success(request, "Ombi limethibitishwa na kuwasilishwa kwa Maofisa!")

    return redirect('employees:director_dashboard')


# --------------------------------------------------------
# 4. OFFICER DASHBOARD & BULK SMS & REPORTS
# --------------------------------------------------------
@login_required
@user_passes_test(is_officer)
def officer_dashboard(request):
    officer = getattr(request.user, 'officer_profile', None)
    tz_now = get_tz_now()
    today = tz_now.date()

    pending_requests = RequestApplication.objects.filter(status='PEND_OFF').order_by('-id') if RequestApplication else []

    selected_month = request.GET.get('month', str(today.month))
    selected_year = request.GET.get('year', str(today.year))
    selected_employee = request.GET.get('employee', 'ALL')
    search_query = request.GET.get('search', '').strip()

    attendances = []
    if Attendance:
        attendances = Attendance.objects.all().select_related('employee', 'employee__department')
        if selected_month and selected_month != 'ALL':
            try:
                attendances = attendances.filter(attendance_date__month=int(selected_month))
            except ValueError:
                pass
        if selected_year:
            try:
                attendances = attendances.filter(attendance_date__year=int(selected_year))
            except ValueError:
                pass
        if selected_employee and selected_employee != 'ALL':
            attendances = attendances.filter(employee_id=selected_employee)
        if search_query:
            attendances = attendances.filter(
                Q(employee__first_name__icontains=search_query) |
                Q(employee__last_name__icontains=search_query) |
                Q(employee__employee_code__icontains=search_query)
            )
        attendances = attendances.order_by('-attendance_date')[:100]

    if request.method == 'POST' and 'send_bulk_sms' in request.POST:
        target_group = request.POST.get('target_group')
        message_text = request.POST.get('message_text')

        if target_group and message_text:
            if target_group == 'DIRECTORS':
                recipients = Employee.objects.filter(is_director=True)
            elif target_group == 'STAFF':
                recipients = Employee.objects.filter(is_director=False)
            else:
                recipients = Employee.objects.all()

            sent_count, fail_count = 0, 0

            for emp in recipients:
                phone, _ = extract_contact_info(emp)
                if phone:
                    sms_response = send_sms_notification(phone, message_text)
                    is_sent, status_str = False, 'FAILED'
                    
                    if isinstance(sms_response, dict):
                        if sms_response.get('status') == 'success':
                            is_sent, status_str = True, 'DELIVERED'
                    elif sms_response is True:
                        is_sent, status_str = True, 'DELIVERED'

                    if SMSLog is not None:
                        try:
                            SMSLog.objects.create(
                                sender=request.user,
                                recipient_name=get_employee_full_name(emp),
                                phone_number=phone,
                                message=message_text,
                                status=status_str,
                                target_group=target_group
                            )
                        except Exception as log_err:
                            logger.error(f"[SMSLog Creation Error]: {str(log_err)}")

                    if is_sent:
                        sent_count += 1
                    else:
                        fail_count += 1

            current_officer_name = get_employee_full_name(officer) if officer else request.user.username
            
            for off in Officer.objects.exclude(user=request.user):
                off_phone, _ = extract_contact_info(off)
                if off_phone:
                    copy_msg = f"[NAKALA YA UJUMBE]\nImetumwa na: {current_officer_name}\nKundi: {target_group}\n\n{message_text}"
                    send_sms_notification(off_phone, copy_msg)
                    
                    if SMSLog is not None:
                        try:
                            SMSLog.objects.create(
                                sender=request.user,
                                recipient_name=f"Nakala: {get_employee_full_name(off)}",
                                phone_number=off_phone,
                                message=copy_msg,
                                status='DELIVERED',
                                target_group=f"CC: {target_group}"
                            )
                        except Exception:
                            pass

            messages.success(request, f"SMS Zimetumwa kwa walengwa! Zilizofika: {sent_count}, Nakala zimetumwa kwa Maofisa wenzako.")
            return redirect('employees:officer_dashboard')
        else:
            messages.error(request, "Tafadhali jaza kundi na ujumbe wa SMS kikamilifu.")

    sms_logs = SMSLog.objects.all().order_by('-created_at')[:20] if SMSLog is not None else []
    all_employees = Employee.objects.all().order_by('first_name', 'last_name')

    context = {
        'officer': officer,
        'pending_requests': pending_requests,
        'attendances': attendances,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_employee': selected_employee,
        'search_query': search_query,
        'sms_logs': sms_logs,
        'all_employees': all_employees,
        'months': range(1, 13),
        'years': range(today.year - 2, today.year + 1),
    }
    return render(request, 'dashboards/officer_dashboard.html', context)


@login_required
@user_passes_test(is_officer)
@require_POST
def officer_process_request(request, request_id, action):
    if RequestApplication is None:
        return redirect('employees:officer_dashboard')

    leave_req = get_object_or_404(RequestApplication, id=request_id)
    emp_user = getattr(leave_req, 'user', getattr(leave_req.employee, 'user', None) if hasattr(leave_req, 'employee') else None)
    employee = getattr(emp_user, 'employee_profile', getattr(leave_req, 'employee', None))
    
    emp_phone, emp_email = extract_contact_info(employee or emp_user)
    full_name = get_employee_full_name(employee) if employee else (f"{emp_user.first_name} {emp_user.last_name}".strip() or emp_user.username if emp_user else "Mfanyakazi")

    if action == 'reject':
        leave_req.status = 'REJECTED'
        leave_req.save()

        if emp_phone:
            msg = f"Habari {full_name}, ombi lako la ruhusa la tarehe {leave_req.start_date} LIMEKATALIWA katika hatua ya Maofisa."
            send_sms_notification(emp_phone, msg)

        messages.info(request, "Ombi limekataliwa.")

    elif action == 'approve':
        leave_req.status = 'APPROVED'
        leave_req.save()

        # Kupunguza siku za dharura au likizo kwenye LeaveBalance pindi ombi linapoidhinishwa rasmi
        if LeaveBalance is not None and emp_user:
            bal_obj = LeaveBalance.objects.filter(user=emp_user).first()
            if bal_obj:
                req_type = getattr(leave_req, 'request_type', '')
                if req_type in ['EMERGENCY_LEAVE', 'EMERGENCY']:
                    if bal_obj.emergency_leave_count > 0:
                        bal_obj.emergency_leave_count -= 1
                        bal_obj.save()
                elif req_type in ['ANNUAL_LEAVE', 'LEAVE']:
                    # Hapa unaweza kuhesabu siku kulingana na end_date - start_date kama ipo
                    days_diff = 1
                    try:
                        if leave_req.end_date and leave_req.start_date:
                            delta = leave_req.end_date - leave_req.start_date
                            days_diff = max(1, delta.days + 1)
                    except Exception:
                        pass
                    if bal_obj.annual_leave_days >= days_diff:
                        bal_obj.annual_leave_days -= days_diff
                        bal_obj.save()

        if emp_phone:
            msg_approved = f"Hongera {full_name}! Ombi lako la ruhusa la tarehe {leave_req.start_date} LIMEKUBALIWA kikamilifu."
            send_sms_notification(emp_phone, msg_approved)

        if emp_email:
            email_subject = "HATI YA IDHINI YA RUHUSA - NETC HQ"
            email_body = (
                f"Ndugu {full_name},\n\n"
                f"Tunapenda kukutaarifu kuwa ombi lako la ruhusa limekubaliwa kikamilifu.\n\n"
                f"TAARIFA ZA RUHUSA:\n"
                f"- Aina ya Ombi: {getattr(leave_req, 'get_request_type_display', lambda: leave_req.request_type)()}\n"
                f"- Tarehe ya Kuanza: {leave_req.start_date}\n"
                f"- Tarehe ya Kumaliza: {leave_req.end_date}\n"
                f"- Sababu: {leave_req.reason}\n\n"
                f"Wako,\n"
                f"Uongozi wa NETC HQ"
            )
            try:
                send_mail(
                    subject=email_subject,
                    message=email_body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'NETC HQ <info@netcadventist.org>'),
                    recipient_list=[emp_email],
                    fail_silently=True
                )
            except Exception as e:
                logger.error(f"[Email Send Error]: {str(e)}")

        messages.success(request, "Idhini ya mwisho imetolewa, SMS na Email zimetumwa kwa Mfanyakazi!")

    return redirect('employees:officer_dashboard')


# --------------------------------------------------------
# 5. KU-PRINT / EXPORT RIPOTI YA MAHUDHURIO (CSV)
# --------------------------------------------------------
@login_required
@user_passes_test(is_officer)
def export_attendance_csv(request):
    if not Attendance:
        return HttpResponse("Attendance Model haijapatikana.")

    tz_now = get_tz_now()
    today = tz_now.date()
    month = request.GET.get('month', str(today.month))
    year = request.GET.get('year', str(today.year))
    employee_id = request.GET.get('employee', 'ALL')

    attendances = Attendance.objects.all().select_related('employee', 'employee__department')
    if month and month != 'ALL':
        try:
            attendances = attendances.filter(attendance_date__month=int(month))
        except ValueError:
            pass
    if year:
        try:
            attendances = attendances.filter(attendance_date__year=int(year))
        except ValueError:
            pass
    if employee_id and employee_id != 'ALL':
        attendances = attendances.filter(employee_id=employee_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Ripoti_Mahudhurio_{month}_{year}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Kodi ya Mfanyakazi', 'Jina Kamili', 'Idara', 'Tarehe', 'Muda wa Kuingia', 'Muda wa Kutoka', 'Hali (Status)'])

    for att in attendances:
        dept_name = att.employee.department.name if att.employee and att.employee.department else "Haina Idara"
        emp_name = get_employee_full_name(att.employee)
        emp_code = att.employee.employee_code if att.employee else "N/A"
        
        t_in = getattr(att, 'check_in_time', None) or '-'
        t_out = getattr(att, 'check_out_time', None) or '-'
        status_val = 'LATE' if getattr(att, 'is_late', False) else getattr(att, 'status', '-')
        
        writer.writerow([
            emp_code,
            emp_name,
            dept_name,
            getattr(att, 'attendance_date', '-'),
            t_in,
            t_out,
            status_val
        ])

    return response