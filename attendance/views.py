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

    # SDASMS API Token
    API_TOKEN = "165|f2IywyWAhT8qG7TxcGXZKn9cO1jsNq7X4Kg1gcu66db2f0fc"
    URL = "https://my.sdasms.com/api/v3/sms/send"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "recipient": phone_number,
        "message": message_text,
        "sender_id": "NETC HQ"  # Sender ID iliyoidhinishwa
    }

    try:
        # verify=False imeongezwa kuzuia SSL Certificate verification error
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

    # 1. Kutafuta direct field za phone na email
    for p_attr in ['phone_number', 'phone', 'mobile', 'telephone']:
        if hasattr(obj, p_attr) and getattr(obj, p_attr):
            phone = getattr(obj, p_attr)
            break

    for e_attr in ['email', 'email_address']:
        if hasattr(obj, e_attr) and getattr(obj, e_attr):
            email = getattr(obj, e_attr)
            break

    # 2. Kama zipo ndani ya relationship ya Django User
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

    # Extract taarifa za mfanyakazi mwenyewe
    emp_phone, emp_email = extract_phone_and_email(employee)

    # 1. MFANYAKAZI AMECHELEWA (LATE)
    if attendance_record.status == 'LATE':
        
        # Hesabu idadi ya siku alizochelewa mwezi huu
        late_count = Attendance.objects.filter(
            employee=employee,
            attendance_date__month=current_month,
            attendance_date__year=current_year,
            status='LATE'
        ).count()

        # A. SMS na Email kwa Mfanyakazi Mwenyewe (Iwe ni Director au Mfanyakazi wa kawaida)
        emp_msg = f"Habari {full_name}, tunatumaini unaendelea vizuri. Leo umeingia kazini saa {time_str}, baada ya muda rasmi wa kufika ambao ni 08:00 AM. Tunakukumbusha kwa upendo umuhimu wa kuwahi kazini na kutunza muda. Tunaamini utaendelea kujitahidi kufanya vizuri katika utekelezaji wa majukumu yako. Bwana akubariki katika kazi zako. Maranatha!"

        send_sms_notification(emp_phone, emp_msg)

        emp_email_subject = f"TAARIFA YA KUCHELEWA KAZINI - {today.strftime('%d/%m/%Y')}"

        emp_email_body = (
    f"Habari {full_name},\n\n"

    f"Unataarifiwa kuwa leo tarehe {today.strftime('%d-%m-%Y')} "
    f"umeingia kazini saa {time_str}, baada ya muda rasmi wa kuanza kazi "
    f"ambao ni saa 08:00 AM.\n\n"

    f"Kumbukumbu za mfumo wa mahudhurio zinaonyesha kuwa hii ni mara yako "
    f"ya ({late_count}) kuchelewa katika mwezi wa {today.strftime('%B %Y')}.\n\n"

    f"Unakumbushwa kuzingatia muda wa kazi na kuhakikisha unafika kazini "
    f"kwa wakati. Kuchelewa mara kwa mara kunaathiri utekelezaji wa majukumu "
    f"na ufanisi wa kazi za taasisi.\n\n"

    f"Tafadhali chukua hatua stahiki kuhakikisha hali hii haijirudii.\n\n"

    f"Wako katika utumishi,\n"
    f"Katibu wa Conference\n"
    f"NETC HQ"
)
        send_email_notification(emp_email_subject, emp_email_body, [emp_email])

        # B. SMS na Email kwa Director / Mkuu wa Idara
        director_obj = None

        if hasattr(employee, 'department') and employee.department:
            dept = employee.department
            
            # 1. Jaribu kupata Director kutoka kwenye Idara
            for attr in ['director', 'head_of_department', 'manager', 'head', 'leader']:
                if hasattr(dept, attr) and getattr(dept, attr):
                    director_obj = getattr(dept, attr)
                    break
            
            # 2. Kama idara haina director, tumia `job_title` au `is_director` badala ya `role`
            if not director_obj:
                director_obj = Employee.objects.filter(
                    department=dept,
                    job_title__icontains='Mkurugenzi'
                ).first() or Employee.objects.filter(
                    department=dept,
                    job_title__icontains='Director'
                ).first() or Employee.objects.filter(
                    department=dept,
                    is_director=True
                ).first()

        director_phone, director_email = extract_phone_and_email(director_obj)

        # HAKIKISHA: Director yupo NA Mfanyakazi anayechelewa SIO huyo Director mwenyewe!
        if director_obj and director_obj.pk != employee.pk:
            dir_msg = f"Taarifa ya Mahudhurio: Mfanyakazi {full_name} wa idara yako amechelewa kufika kazini leo na aliingia saa {time_str}. Hii ni mara yake ya {late_count} kuchelewa katika mwezi huu. Tafadhali pokea taarifa hii kwa ufuatiliaji. - NETC Attendance System"
            
            if director_phone:
                send_sms_notification(director_phone, dir_msg)

            if director_email:
                dir_email_subject = f"TAARIFA YA IDARA: Kuchelewa kwa {full_name}"
                dir_email_body = (
    f"Habari Mkuu wa Idara,\n\n"

    f"Taarifa za mahudhurio zinaonyesha kuwa mfanyakazi {full_name} wa idara yako "
    f"amechelewa kufika kazini leo, tarehe {today.strftime('%d-%m-%Y')}, "
    f"na aliingia saa {time_str}.\n\n"

    f"Hii ni mara yake ya {late_count} kuchelewa katika mwezi wa "
    f"{today.strftime('%B %Y')}.\n\n"

    f"Taarifa hii imetumwa kwa ajili ya taarifa na ufuatiliaji wa mahudhurio "
    f"katika idara yako.\n\n"

    f"---\n"
    f"NETC Attendance System\n"
)
                send_email_notification(dir_email_subject, dir_email_body, [director_email])
        elif not director_obj:
            print(f"[Alert System]: Mfanyakazi {full_name} idara yake haina Director au namba/email yake haijajazwa vizuri kwenye mfumo!")

        # C. MARA YA 2 AU ZAIDI: Taarifa kwa Officers wote (SMS na Email)
        if late_count >= 2:
            officers = Officer.objects.all()
            officer_emails = []
            officer_msg = f"ALERT: Mfanyakazi {full_name} amechelewa mara {late_count} mwezi huu wa {today.strftime('%B %Y')} (Leo: {time_str})."

            for officer in officers:
                off_phone, off_email = extract_phone_and_email(officer)
                if off_phone:
                    send_sms_notification(off_phone, officer_msg)
                if off_email:
                    officer_emails.append(off_email)

            send_email_notification(
                subject=f"Taarifa ya Kuchelewa Mara kwa Mara: {full_name}",
                message=officer_msg,
                recipient_list=officer_emails
            )

        # D. MARA YA 3 AU ZAIDI: Barua ya Onyo (Email kwa Mfanyakazi)
        if late_count >= 3:
            warning_email_body = (
    f"Ndugu {full_name},\n\n"

    f"TAARIFA YA ONYO KUHUSU KUCHELEWA KAZINI\n\n"

    f"Rekodi za mfumo wa mahudhurio zinaonyesha kuwa umechelewa kufika kazini "
    f"mara {late_count} katika mwezi wa {today.strftime('%B %Y')}.\n\n"

    f"Tunapenda kukukumbusha umuhimu wa kutunza muda na kufika kazini kwa wakati, "
    f"ili kuhakikisha utekelezaji wa majukumu unaendelea vizuri.\n\n"

    f"Tafadhali zingatia zaidi muda wa kufika kazini na jitahidi kuhakikisha "
    f"hali ya kuchelewa haijirudii mara kwa mara.\n\n"

    f"Tunaamini utazingatia taarifa hii na kufanya maboresho katika utunzaji wa muda.\n\n"

    f"Bwana akubariki katika utekelezaji wa majukumu yako.\n"
    f"Maranatha!\n\n"

    f"NETC HQ\n"
    f"Ujumbe huu umetumwa kupitia Mfumo wa Mahudhurio."
)
            send_email_notification(
                subject="BARUA YA ONYO - KUCHELEWA KAZINI",
                message=warning_email_body,
                recipient_list=[emp_email]
            )

    # 2. MFANYAKAZI AMEWAHI (PRESENT)
    elif attendance_record.status == 'PRESENT':
        past_4_logs = Attendance.objects.filter(
            employee=employee,
            attendance_date__lt=today
        ).order_by('-attendance_date')[:3]

        presents_streak = 1  # Ya leo
        for log in past_4_logs:
            if log.status == 'PRESENT':
                presents_streak += 1
            else:
                break

        if presents_streak == 4:
            congrats_msg = f"Hongera sana {full_name}! Umefanikiwa kuwahi kazini siku 4 mfululizo. Hongera kwa uwajibikaji mwema!"
            send_sms_notification(emp_phone, congrats_msg)


# =====================================================================
# MAIN VIEWS
# =====================================================================

def employee_checkin_view(request):
    """View inayohudumia ukurasa wa HTML wa Check-In / Check-Out."""
    if request.method == 'POST':
        user_code = request.POST.get('employee_code', '').strip()
        action = request.POST.get('action')

        if not user_code:
            messages.error(request, "Tafadhali ingiza Code yako!")
            return redirect('employee_checkin')

        employee = Employee.objects.filter(employee_code__iexact=user_code).first() or \
                   Employee.objects.filter(fingerprint_id=user_code).first()

        officer = None
        if not employee:
            officer = Officer.objects.filter(officer_code__iexact=user_code).first() or \
                      Officer.objects.filter(fingerprint_id=user_code).first()

        if not employee and not officer:
            messages.error(request, f"Mtumiaji mwenye code ({user_code}) hajapatikana!")
            return redirect('employee_checkin')

        full_name = f"{employee.first_name} {employee.last_name}" if employee else f"{officer.first_name} {officer.last_name}"

        now_datetime = timezone.localtime(timezone.now())
        today = now_datetime.date()
        now_time = now_datetime.time()
        weekday = today.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun

        is_friday = (weekday == 4)  # Work from Home

        filter_kwargs = {'attendance_date': today}
        if employee:
            filter_kwargs['employee'] = employee
        else:
            filter_kwargs['officer'] = officer

        attendance = Attendance.objects.filter(**filter_kwargs).first()

        if action == 'check_in':
            if attendance:
                time_str = attendance.check_in_time.strftime('%I:%M %p') if attendance.check_in_time else ""
                messages.error(request, f"Habari {full_name}, tayari umefanya Check-In leo saa {time_str}!")
            else:
                cutoff_time = time(8, 5, 0)  # Grace Period: 08:05 AM
                
                if is_friday:
                    status = 'PRESENT'
                    note = "(Work From Home)"
                else:
                    status = 'PRESENT' if now_time <= cutoff_time else 'LATE'
                    note = "Umewahi!" if status == 'PRESENT' else "Umechelewa!"

                attendance = Attendance.objects.create(
                    **filter_kwargs,
                    check_in_time=now_time,
                    status=status
                )

                if employee:
                    process_attendance_rules(employee, now_datetime, attendance)

                messages.success(
                    request,
                    f"Karibu {full_name}! Check-In yako imefanikiwa saa {now_datetime.strftime('%I:%M %p')}. {note}"
                )

        elif action == 'check_out':
            if not attendance:
                messages.error(request, f"Habari {full_name}, huwezi ku-check out kabla ya ku-check in!")
            elif attendance.check_out_time:
                time_str = attendance.check_out_time.strftime('%I:%M %p')
                messages.error(request, f"Habari {full_name}, tayari umeshafanya Check-Out leo saa {time_str}!")
            else:
                closing_time = time(17, 30, 0)  # Saa 17:30 (05:30 PM)
                
                early_out_warning = ""
                if now_time < closing_time and not is_friday:
                    early_out_warning = " (Umetoka kabla ya muda rasmi wa 05:30 PM!)"

                attendance.check_out_time = now_time

                # Kuhesabu Masaa Aliyofanya Kazi
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

        return redirect('employee_checkin')

    return render(request, 'attendance/check_in.html')


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
        is_friday = (weekday == 4)

        filter_kwargs = {'attendance_date': today}
        if employee:
            filter_kwargs['employee'] = employee
        else:
            filter_kwargs['officer'] = officer

        cutoff_time = time(8, 5, 0)
        status = 'PRESENT' if (is_friday or now_time <= cutoff_time) else 'LATE'

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