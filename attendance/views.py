import json
import datetime
from datetime import time, timedelta
import requests

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps

from employees.models import Employee, Officer
from .models import Attendance


# =====================================================================
# UTILITY FUNCTIONS (SDASMS & EMAIL NOTIFICATIONS)
# =====================================================================

def send_sms_notification(phone_number, message_text):
    """
    Function ya kutuma SMS kwa kutumia SDASMS API na Sender ID ya NETC HQ.
    """
    if not phone_number:
        print("[SDASMS Alert]: Namba ya simu haijatolewa/haipo kwenye profile ya mtumiaji!")
        return

    # Safisha namba ya simu iwe kwenye format ya 255...
    phone_number = str(phone_number).strip().replace('+', '').replace(' ', '')
    if phone_number.startswith('0'):
        phone_number = '255' + phone_number[1:]

    API_TOKEN = "167|2eiLhXwLf3x4SEb1pACaQiCMiKpUXh2RcEuR4tQhf9be8aad"
    URL = "https://my.sdasms.com/api/v3/sms/send"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "recipient": phone_number,
        "message": message_text,
        "sender_id": "NETC HQ"
    }

    try:
        response = requests.post(URL, json=payload, headers=headers, timeout=10, verify=False)
        res_data = response.json()
        print(f"[SDASMS Response to {phone_number}]: {res_data}")
    except Exception as e:
        print(f"[SDASMS Error]: {str(e)}")


def send_email_notification(subject, message, recipient_list):
    """Function ya kutuma Email kwa kutumia SMTP ya NETC HQ."""
    valid_recipients = [email for email in recipient_list if email and '@' in str(email)]
    
    if not valid_recipients:
        print("[Email Alert]: Hakuna email halali iliyopatikana kwenye list!")
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'NETC HQ <info@netcadventist.org>'),
            recipient_list=valid_recipients,
            fail_silently=False
        )
        print(f"[Email Success]: Ujumbe umeenda vizuri kwenda: {valid_recipients}")
    except Exception as e:
        print(f"[Email Error]: Imeshindwa kutuma kwenda {valid_recipients}. Sababu: {str(e)}")


def extract_phone_and_email(obj):
    """
    Function inayosaidia kutafuta kwa usalama namba ya simu na email 
    kwenye Model yoyote (Employee, Officer, User, Director).
    """
    if not obj:
        return None, None

    phone = None
    email = None

    for p_attr in ['phone_number', 'phone', 'mobile', 'telephone']:
        if hasattr(obj, p_attr) and getattr(obj, p_attr):
            phone = getattr(obj, p_attr)
            break

    for e_attr in ['email', 'email_address']:
        if hasattr(obj, e_attr) and getattr(obj, e_attr):
            email = getattr(obj, e_attr)
            break

    if hasattr(obj, 'user') and obj.user:
        if not phone:
            for p_attr in ['phone_number', 'phone', 'mobile']:
                if hasattr(obj.user, p_attr) and getattr(obj.user, p_attr):
                    phone = getattr(obj.user, p_attr)
                    break
        if not email and hasattr(obj.user, 'email'):
            email = obj.user.email

    return phone, email


def process_attendance_rules(employee, now_datetime, attendance_record):
    """Kipengele kinachoshughulikia maonyo, mahesabu ya mwezi, na pongezi."""
    today = now_datetime.date()
    current_month = today.month
    current_year = today.year

    full_name = f"{employee.first_name} {employee.last_name}"
    time_str = now_datetime.strftime('%I:%M %p')

    emp_phone, emp_email = extract_phone_and_email(employee)

    # 1. MFANYAKAZI AMECHELEWA (LATE)
    if attendance_record.status == 'LATE':
        late_count = Attendance.objects.filter(
            employee=employee,
            attendance_date__month=current_month,
            attendance_date__year=current_year,
            status='LATE'
        ).count()

        emp_msg = f"Habari {full_name}, tunatumaini unaendelea vizuri. Leo umeingia kazini saa {time_str}, baada ya muda rasmi wa kufika ambao ni 08:00 AM. Tunakukumbusha kwa upendo umuhimu wa kuwahi kazini na kutunza muda. Maranatha!"
        send_sms_notification(emp_phone, emp_msg)

        emp_email_subject = f"TAARIFA YA KUCHELEWA KAZINI - {today.strftime('%d/%m/%Y')}"
        emp_email_body = (
            f"Habari {full_name},\n\n"
            f"Unataarifiwa kuwa leo tarehe {today.strftime('%d-%m-%Y')} "
            f"umeingia kazini saa {time_str}, baada ya muda rasmi wa kuanza kazi "
            f"ambao ni saa 08:00 AM.\n\n"
            f"Kumbukumbu za mfumo zinaonyesha kuwa hii ni mara yako ya ({late_count}) kuchelewa katika mwezi wa {today.strftime('%B %Y')}.\n\n"
            f"Tafadhali chukua hatua stahiki kuhakikisha hali hii haijirudii.\n\n"
            f"Wako katika utumishi,\nKatibu wa Conference\nNETC HQ"
        )
        send_email_notification(emp_email_subject, emp_email_body, [emp_email])

        director_obj = None
        if hasattr(employee, 'department') and employee.department:
            dept = employee.department
            for attr in ['director', 'head_of_department', 'manager', 'head', 'leader']:
                if hasattr(dept, attr) and getattr(dept, attr):
                    director_obj = getattr(dept, attr)
                    break
            
            if not director_obj:
                director_obj = Employee.objects.filter(
                    department=dept, job_title__icontains='Mkurugenzi'
                ).first() or Employee.objects.filter(
                    department=dept, job_title__icontains='Director'
                ).first() or Employee.objects.filter(
                    department=dept, is_director=True
                ).first()

        director_phone, director_email = extract_phone_and_email(director_obj)

        if director_obj and director_obj.pk != employee.pk:
            dir_msg = f"Taarifa ya Mahudhurio: Mfanyakazi {full_name} wa idara yako amechelewa kufika kazini leo na aliingia saa {time_str}. Hii ni mara yake ya {late_count} kuchelewa mwezi huu."
            if director_phone:
                send_sms_notification(director_phone, dir_msg)
            if director_email:
                send_email_notification(f"TAARIFA YA IDARA: Kuchelewa kwa {full_name}", dir_msg, [director_email])

        if late_count >= 3:
            warning_email_body = (
                f"Ndugu {full_name},\n\nTAARIFA YA ONYO KUHUSU KUCHELEWA KAZINI\n\n"
                f"Rekodi zinaonyesha umechelewa mara {late_count} mwezi huu wa {today.strftime('%B %Y')}. "
                f"Tafadhali zingatia muda wa kufika kazini.\n\nMaranatha!\nNETC HQ"
            )
            send_email_notification("BARUA YA ONYO - KUCHELEWA KAZINI", warning_email_body, [emp_email])

    # 2. MFANYAKAZI AMEWAHI (PRESENT)
    elif attendance_record.status == 'PRESENT':
        past_4_logs = Attendance.objects.filter(
            employee=employee, attendance_date__lt=today
        ).order_by('-attendance_date')[:3]

        presents_streak = 1 
        for log in past_4_logs:
            if log.status == 'PRESENT':
                presents_streak += 1
            else:
                break

        if presents_streak == 4:
            congrats_msg = f"Hongera sana {full_name}! Umefanikiwa kuwahi kazini siku 4 mfululizo. Hongera kwa uwajibikaji mwema!"
            send_sms_notification(emp_phone, congrats_msg)


# =====================================================================
# HELPER TO DETECT USER TYPE & REDIRECT CORRECTLY (SALAMA KABISA)
# =====================================================================
def get_user_dashboard_redirect(user, employee=None):
    """
    Husaidia kutambua kwa usahihi kabisa kama mtumiaji ni Director/Admin 
    au ni Mfanyakazi wa kawaida, na kumpeleka kwenye dashboard yake sahihi.
    """
    if not user.is_authenticated:
        return redirect('login')
    
    is_director = False
    
    # 1. Angalia kupitia Django Groups rasmi za uongozi pekee au kama ni superuser
    if user.is_superuser:
        is_director = True
    elif user.groups.filter(name__icontains='Director').exists() or user.groups.filter(name__icontains='Administrator').exists() or user.groups.filter(name__icontains='Administrators').exists():
        is_director = True
    
    # 2. Angalia kupitia Employee Profile kama ni Director au Mkuu wa Idara halisi
    if not is_director and employee:
        if getattr(employee, 'is_director', False):
            is_director = True
        elif employee.job_title and ('director' in employee.job_title.lower() or 'mkurugenzi' in employee.job_title.lower()):
            is_director = True
        else:
            dept_check = apps.get_model('employees', 'Department')
            if dept_check:
                try:
                    if dept_check.objects.filter(head_of_department=employee).exists():
                        is_director = True
                except Exception:
                    pass

    # KAMA NI DIRECTOR AU ADMIN HALISI
    if is_director:
        try:
            return redirect('director_dashboard')
        except Exception:
            try:
                return redirect('employees:director_dashboard')
            except Exception:
                return redirect('/employees/dashboard/director/')
    
    # KAMA NI MFANYAKAZI WA KAWADA (REGULAR EMPLOYEE) - HAPA NDIPO ILIPOSIMAMA SAHIHI
    else:
        try:
            return redirect('employee_dashboard')
        except Exception:
            try:
                return redirect('dashboard:employee_dashboard')
            except Exception:
                # IMEREKEBISHWA: Inatua moja kwa moja kwenye URL sahihi ya mfanyakazi badala ya admin dashboard
                return redirect('/employees/dashboard/employee/')


# =====================================================================
# MAIN VIEWS
# =====================================================================

def employee_checkin_view(request):
    """View inayohudumia ukurasa wa HTML wa Check-In / Check-Out kwenye Dashboard."""
    now_datetime = timezone.localtime(timezone.now())
    today = now_datetime.date()
    current_month = today.month
    current_year = today.year

    employee = None
    officer = None

    if hasattr(request.user, 'employee') and request.user.employee:
        employee = request.user.employee
    elif hasattr(request.user, 'officer') and request.user.officer:
        officer = request.user.officer
    else:
        employee = Employee.objects.filter(user=request.user).first()
        if not employee:
            officer = Officer.objects.filter(user=request.user).first()

    balance = None
    if employee:
        for app_label in ['leave', 'leaves']:
            try:
                LeaveBalanceModel = apps.get_model(app_label, 'LeaveBalance')
                if LeaveBalanceModel:
                    balance = LeaveBalanceModel.objects.filter(employee=employee).first()
                    if balance:
                        break
            except Exception:
                continue

    if request.method == 'POST':
        user_code = request.POST.get('employee_code', '').strip()
        action = request.POST.get('action')

        if not user_code and (employee or officer):
            user_code = employee.employee_code if employee else officer.officer_code

        if not user_code:
            messages.error(request, "Tafadhali ingiza Code yako!")
            return get_user_dashboard_redirect(request.user, employee)

        target_employee = Employee.objects.filter(employee_code__iexact=user_code).first() or \
                          Employee.objects.filter(fingerprint_id=user_code).first()

        target_officer = None
        if not target_employee:
            target_officer = Officer.objects.filter(officer_code__iexact=user_code).first() or \
                             Officer.objects.filter(fingerprint_id=user_code).first()

        if not target_employee and not target_officer:
            messages.error(request, f"Mtumiaji mwenye code ({user_code}) hajapatikana!")
            return get_user_dashboard_redirect(request.user, employee)

        active_emp = target_employee
        active_off = target_officer
        full_name = f"{active_emp.first_name} {active_emp.last_name}" if active_emp else f"{active_off.first_name} {active_off.last_name}"

        now_time = now_datetime.time()
        weekday = today.weekday() 

        if weekday == 5:
            messages.error(request, f"Habari {full_name}, leo ni siku ya Sabato (Jumamosi). Mfumo wa mahudhurio umefungwa!")
            return get_user_dashboard_redirect(request.user, employee)

        is_optional_day = (weekday == 4 or weekday == 6)

        filter_kwargs = {'attendance_date': today}
        if active_emp:
            filter_kwargs['employee'] = active_emp
        else:
            filter_kwargs['officer'] = active_off

        attendance = Attendance.objects.filter(**filter_kwargs).first()

        if action == 'check_in':
            if attendance:
                time_str = attendance.check_in_time.strftime('%I:%M %p') if attendance.check_in_time else ""
                messages.error(request, f"Habari {full_name}, tayari umefanya Check-In leo saa {time_str}!")
            else:
                cutoff_time = time(8, 5, 0)
                status = 'PRESENT' if (is_optional_day or now_time <= cutoff_time) else 'LATE'
                note = "Umewahi!" if status == 'PRESENT' else "Umechelewa!"

                attendance = Attendance.objects.create(
                    **filter_kwargs,
                    check_in_time=now_time,
                    status=status
                )

                if active_emp:
                    process_attendance_rules(active_emp, now_datetime, attendance)

                messages.success(request, f"Karibu {full_name}! Check-In yako imefanikiwa saa {now_datetime.strftime('%I:%M %p')}. {note}")

        elif action == 'check_out':
            if not attendance:
                messages.error(request, f"Habari {full_name}, huwezi ku-check out kabla ya ku-check in!")
            elif attendance.check_out_time:
                time_str = attendance.check_out_time.strftime('%I:%M %p')
                messages.error(request, f"Habari {full_name}, tayari umeshafanya Check-Out leo saa {time_str}!")
            else:
                closing_time = time(17, 30, 0)
                early_out_warning = " (Umetoka kabla ya muda rasmi wa 05:30 PM!)" if (now_time < closing_time and not is_optional_day) else ""

                attendance.check_out_time = now_time

                dt_in = datetime.datetime.combine(today, attendance.check_in_time)
                dt_out = datetime.datetime.combine(today, now_time)
                duration = dt_out - dt_in
                
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60

                if hasattr(attendance, 'hours_worked'):
                    attendance.hours_worked = duration

                attendance.save()

                messages.success(
                    request,
                    f"Kwaheri {full_name}! Check-Out imefanikiwa saa {now_datetime.strftime('%I:%M %p')}.{early_out_warning} "
                    f"Umeshafanya kazi kwa masaa {hours} na dakika {minutes} leo."
                )

        return get_user_dashboard_redirect(request.user, employee)

    context = {
        'employee': employee,
        'officer': officer,
        'on_time_count': 0,
        'late_count': 0,
        'today_attendance': None,
        'balance': balance,
    }

    target_filter = {}
    if employee:
        target_filter['employee'] = employee
    elif officer:
        target_filter['officer'] = officer

    if target_filter:
        today_attendance = Attendance.objects.filter(**target_filter, attendance_date=today).first()
        context['today_attendance'] = today_attendance

        context['on_time_count'] = Attendance.objects.filter(
            **target_filter,
            attendance_date__month=current_month,
            attendance_date__year=current_year,
            status='PRESENT'
        ).count()

        context['late_count'] = Attendance.objects.filter(
            **target_filter,
            attendance_date__month=current_month,
            attendance_date__year=current_year,
            status='LATE'
        ).count()

    return render(request, 'dashboards/employee_dashboard.html', context)


@csrf_exempt
def fingerprint_scan_api(request):
    """API Endpoint inayohudumia Biometric Readers / Serial Devices."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST inahitajika'}, status=400)

    try:
        user_code = request.POST.get('employee_code') or request.POST.get('user_code')
        if not user_code and request.body:
            try:
                data = json.loads(request.body)
                user_code = data.get('employee_code') or data.get('user_code')
            except json.JSONDecodeError:
                pass

        if not user_code:
            return JsonResponse({'status': 'error', 'message': 'Code inahitajika'}, status=400)

        employee = Employee.objects.filter(employee_code__iexact=user_code).first() or \
                   Employee.objects.filter(fingerprint_id=user_code).first()

        officer = None
        if not employee:
            officer = Officer.objects.filter(officer_code__iexact=user_code).first() or \
                      Officer.objects.filter(fingerprint_id=user_code).first()

        if not employee and not officer:
            return JsonResponse({'status': 'error', 'message': 'Mtumiaji hajapatikana'}, status=404)

        now_datetime = timezone.localtime(timezone.now())
        today = now_datetime.date()
        now_time = now_datetime.time()
        weekday = today.weekday()

        if weekday == 5:
            return JsonResponse({'status': 'error', 'message': 'Leo ni Sabato, mfumo wa mahudhurio umefungwa.'}, status=400)

        is_optional_day = (weekday == 4 or weekday == 6)

        filter_kwargs = {'attendance_date': today}
        if employee:
            filter_kwargs['employee'] = employee
        else:
            filter_kwargs['officer'] = officer

        cutoff_time = time(8, 5, 0)
        status = 'PRESENT' if (is_optional_day or now_time <= cutoff_time) else 'LATE'

        attendance, created = Attendance.objects.get_or_create(
            **filter_kwargs,
            defaults={'check_in_time': now_time, 'status': status}
        )

        full_name = f"{employee.first_name} {employee.last_name}" if employee else f"{officer.first_name} {officer.last_name}"

        if created:
            if employee:
                process_attendance_rules(employee, now_datetime, attendance)

            return JsonResponse({
                'status': 'success',
                'action': 'CHECK_IN',
                'employee': full_name,
                'attendance_status': status,
                'time': now_time.strftime("%H:%M:%S")
            })
        else:
            if not attendance.check_out_time:
                attendance.check_out_time = now_time
                
                dt_in = datetime.datetime.combine(today, attendance.check_in_time)
                dt_out = datetime.datetime.combine(today, now_time)
                duration = dt_out - dt_in
                
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60

                if hasattr(attendance, 'hours_worked'):
                    attendance.hours_worked = duration

                attendance.save()
                return JsonResponse({
                    'status': 'success',
                    'action': 'CHECK_OUT',
                    'employee': full_name,
                    'working_hours': f"{hours}h {minutes}m",
                    'time': now_time.strftime("%H:%M:%S")
                })
            else:
                return JsonResponse({
                    'status': 'warning',
                    'message': f'{full_name} ameshamaliza mahudhurio ya leo!'
                })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Server Error: {str(e)}'}, status=500)