import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Department, OfficerPosition, Employee, Officer
from .forms import UserRegistrationForm, EmployeeProfileForm, OfficerProfileForm

# Helper Functions za SMS & Data Extraction
from utils.sms import send_sms_notification

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
# HELPER FUNCTION FOR PHONE & EMAIL EXTRACTION
# --------------------------------------------------------
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
    """Inarudisha jina kamili la mfanyakazi kwa usalama bila kujali kama linaitwa full_name au first/last name"""
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
@login_required
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
                            messages.success(request, f"Officer {get_employee_full_name(officer)} amesajiliwa kikamilifu!")
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
                            messages.success(request, f"{'Director' if user_type == 'director' else 'Employee'} {get_employee_full_name(employee)} amesajiliwa kikamilifu!")
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
# 2. EMPLOYEE DASHBOARD (KUTUMA OMBI + SMS)
# --------------------------------------------------------
@login_required
def employee_dashboard(request):
    """Dashboard ya Mfanyakazi: Kutuma Maombi & Kuona Takwimu"""
    user = request.user
    today = timezone.now().date()
    employee = getattr(user, 'employee_profile', None)
    
    if request.method == 'POST' and RequestApplication is not None:
        req_type = request.POST.get('request_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or start_date
        reason = request.POST.get('reason')

        if start_date and reason:
            RequestApplication.objects.create(
                user=user,
                request_type=req_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                status='PENDING'
            )

            emp_phone, _ = extract_contact_info(employee or user)
            full_name = get_employee_full_name(employee) if employee else (f"{user.first_name} {user.last_name}".strip() or user.username)

            if emp_phone:
                msg_emp = f"Habari {full_name}, ombi lako la ruhusa la tarehe {start_date} limepokelewa kikamilifu na linashughulikiwa."
                send_sms_notification(emp_phone, msg_emp)

            if employee and hasattr(employee, 'department') and employee.department:
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
            return redirect('employee_dashboard')
        else:
            messages.error(request, "Tafadhali jaza tarehe na sababu ya ombi kikamilifu.")

    balance = LeaveBalance.objects.filter(user=user).first() if LeaveBalance else None
    on_time_count = 0
    late_count = 0

    if Attendance is not None and employee:
        month_attendances = Attendance.objects.filter(
            employee=employee,
            attendance_date__year=today.year,
            attendance_date__month=today.month
        )
        late_count = month_attendances.filter(Q(is_late=True) | Q(status='LATE')).count()
        on_time_count = month_attendances.filter(status='PRESENT', is_late=False).count()

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


# --------------------------------------------------------
# 3. DIRECTOR DASHBOARD & APPROVAL ACTIONS
# --------------------------------------------------------
@login_required
def director_dashboard(request):
    """Dashboard ya Mkurugenzi"""
    user = request.user
    today = timezone.now().date()
    director = getattr(user, 'employee_profile', None)

    director_name = get_employee_full_name(director) if director else (f"{user.first_name} {user.last_name}".strip() or user.username)
    
    target_department = None
    if director:
        if director.department:
            target_department = director.department
        else:
            target_department = director.managed_departments.first()

    dept_name = target_department.name if target_department else "Hajawekwa Idara"

    if request.method == 'POST' and RequestApplication is not None:
        req_type = request.POST.get('request_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date') or start_date
        reason = request.POST.get('reason')

        if start_date and reason:
            RequestApplication.objects.create(
                user=user,
                request_type=req_type,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                status='PEND_OFF'
            )

            dir_phone, _ = extract_contact_info(director or user)

            if dir_phone:
                msg_dir = f"Habari {director_name}, ombi lako la ruhusa la tarehe {start_date} limepokelewa na limewasilishwa kwa Maofisa."
                send_sms_notification(dir_phone, msg_dir)

            officers = Officer.objects.all()
            for officer in officers:
                off_phone, _ = extract_contact_info(officer)
                if off_phone:
                    msg_off = f"TAARIFA: Mkurugenzi {director_name} (Idara ya {dept_name}) ameomba ruhusa kuanzia {start_date}. Tafadhali ingia kwenye mfumo kuisimamia."
                    send_sms_notification(off_phone, msg_off)

            messages.success(request, "Ombi lako limetumwa moja kwa moja kwa Maofisa!")
            return redirect('director_dashboard')
        else:
            messages.error(request, "Tafadhali jaza tarehe na sababu ya ombi kikamilifu.")

    balance = LeaveBalance.objects.filter(user=user).first() if LeaveBalance else None
    on_time_count = 0
    late_count = 0

    if Attendance is not None and director:
        month_attendances = Attendance.objects.filter(
            employee=director,
            attendance_date__year=today.year,
            attendance_date__month=today.month
        )
        late_count = month_attendances.filter(Q(is_late=True) | Q(status='LATE')).count()
        on_time_count = month_attendances.filter(status='PRESENT', is_late=False).count()

    my_requests = RequestApplication.objects.filter(user=user).order_by('-id')[:5] if RequestApplication is not None else []

    department_employees = []
    pending_dept_requests = []

    if target_department:
        department_employees = Employee.objects.filter(
            department=target_department
        ).exclude(user=user)

        if RequestApplication is not None:
            pending_dept_requests = RequestApplication.objects.filter(
                user__employee_profile__department=target_department,
                status='PENDING'
            ).exclude(user=user).order_by('-id')

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
def director_process_request(request, request_id, action):
    """Mkurugenzi Anapokubali au Kukataa Ombi la Mfanyakazi Wake"""
    if RequestApplication is None:
        return redirect('director_dashboard')

    leave_req = get_object_or_404(RequestApplication, id=request_id)
    emp_user = leave_req.user
    employee = getattr(emp_user, 'employee_profile', None)
    
    emp_phone, _ = extract_contact_info(employee or emp_user)
    full_name = get_employee_full_name(employee) if employee else (f"{emp_user.first_name} {emp_user.last_name}".strip() or emp_user.username)

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

        officers = Officer.objects.all()
        for officer in officers:
            off_phone, _ = extract_contact_info(officer)
            if off_phone:
                msg_officer = f"TAARIFA: Kuna ombi jipya la ruhusa la mfanyakazi {full_name} linalosubiri idhini ya Maofisa. Tafadhali ingia kwenye mfumo."
                send_sms_notification(off_phone, msg_officer)

        messages.success(request, "Ombi limethibitishwa na kuwasilishwa kwa Maofisa!")

    return redirect('director_dashboard')


# --------------------------------------------------------
# 4. OFFICER DASHBOARD & BULK SMS & REPORTS
# --------------------------------------------------------
@login_required
def officer_dashboard(request):
    """Dashboard ya Maofisa (Mwenyekiti, Katibu, Mhazini, n.k.)"""
    officer = getattr(request.user, 'officer_profile', None)
    today = timezone.now().date()

    pending_requests = []
    if RequestApplication:
        pending_requests = RequestApplication.objects.filter(status='PEND_OFF').order_by('-id')

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

    # KUSHUGHULIKIA KUTUMA SMS NA KUHIFADHI HISTORIA KWENYE DATABASE
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

            sent_count = 0
            fail_count = 0

            # 1. Tuma kwa walengwa wakuu
            for emp in recipients:
                phone, _ = extract_contact_info(emp)
                if phone:
                    sms_response = send_sms_notification(phone, message_text)
                    
                    is_sent = False
                    status_str = 'FAILED'
                    
                    if isinstance(sms_response, dict):
                        if sms_response.get('status') == 'success':
                            is_sent = True
                            status_str = 'DELIVERED'
                    elif sms_response is True:
                        is_sent = True
                        status_str = 'DELIVERED'

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
                            print(f"[SMSLog Creation Error]: {str(log_err)}")

                    if is_sent:
                        sent_count += 1
                    else:
                        fail_count += 1

            # 2. KUHAKIKISHA MAOVISA WENGINE WOTE (Mwenyekiti, Katibu, Mhazini, n.k.) WANAPATA NAKALA (CC)
            # Tunapata jina la mtumaji wa sasa ili tusimtumie tena ujumbe wa kujirudia kama yeye ndiye aliyetuma
            current_officer_name = get_employee_full_name(officer) if officer else request.user.username
            
            all_officers = Officer.objects.exclude(user=request.user)
            for off in all_officers:
                off_phone, _ = extract_contact_info(off)
                if off_phone:
                    copy_msg = f"[NAKALA YA UJUMBE]\nImetumwa na: {current_officer_name}\nKundi: {target_group}\n\n{message_text}"
                    send_sms_notification(off_phone, copy_msg)
                    
                    # Hifadhi pia kwenye logi za SMS ili viongozi wenzao wazione kwenye mfumo
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
            return redirect('officer_dashboard')
        else:
            messages.error(request, "Tafadhali jaza kundi na ujumbe wa SMS kikamilifu.")

    sms_logs = []
    if SMSLog is not None:
        try:
            sms_logs = SMSLog.objects.all().order_by('-created_at')[:20]
        except Exception as e:
            print(f"[SMSLog Fetch Error]: {str(e)}")
            sms_logs = []

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
def officer_process_request(request, request_id, action):
    """Ofisa Anapotoa Idhini ya Mwisho"""
    if RequestApplication is None:
        return redirect('officer_dashboard')

    leave_req = get_object_or_404(RequestApplication, id=request_id)
    emp_user = leave_req.user
    employee = getattr(emp_user, 'employee_profile', None)
    
    emp_phone, emp_email = extract_contact_info(employee or emp_user)
    full_name = get_employee_full_name(employee) if employee else (f"{emp_user.first_name} {emp_user.last_name}".strip() or emp_user.username)

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

        if emp_phone:
            msg_approved = f"Hongera {full_name}! Ombi lako la ruhusa la tarehe {leave_req.start_date} LIMEKUBALIWA kikamilifu."
            send_sms_notification(emp_phone, msg_approved)

        if emp_email:
            email_subject = "HATI YA IDHINI YA RUHUSA - NETC HQ"
            email_body = (
                f"Ndugu {full_name},\n\n"
                f"Tunapenda kukutaarifu kuwa ombi lako la ruhusa limekubaliwa kikamilifu.\n\n"
                f"TAARIFA ZA RUHUSA:\n"
                f"- Aina ya Ombi: {leave_req.get_request_type_display() if hasattr(leave_req, 'get_request_type_display') else leave_req.request_type}\n"
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
                print(f"[Email Send Error]: {str(e)}")

        messages.success(request, "Idhini ya mwisho imetolewa, SMS na Email zimetumwa kwa Mfanyakazi!")

    return redirect('officer_dashboard')


# --------------------------------------------------------
# 5. KU-PRINT / EXPORT RIPOTI YA MAHUDHURIO (CSV/EXCEL)
# --------------------------------------------------------
@login_required
def export_attendance_csv(request):
    """Ina-download Ripoti ya Mahudhurio kwa Mwezi, Mwaka, au Mfanyakazi mmoja"""
    if not Attendance:
        return HttpResponse("Attendance Model haijapatikana.")

    today = timezone.now().date()
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
        
        t_in = getattr(att, 'time_in', None) or getattr(att, 'timestamp', None) or '-'
        t_out = getattr(att, 'time_out', None) or '-'
        
        writer.writerow([
            emp_code,
            emp_name,
            dept_name,
            getattr(att, 'attendance_date', '-'),
            t_in,
            t_out,
            'LATE' if getattr(att, 'is_late', False) else getattr(att, 'status', '-')
        ])

    return response