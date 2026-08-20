import json
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from employees.models import Employee, Officer
from .models import Attendance

@csrf_exempt
def fingerprint_scan_api(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Ombi si sahihi (POST inahitajika)'}, status=400)

    try:
        # Support kwa POST ya Form-Data na JSON payload
        user_code = request.POST.get('employee_code') or request.POST.get('user_code')
        if not user_code and request.body:
            try:
                data = json.loads(request.body)
                user_code = data.get('employee_code') or data.get('user_code')
            except json.JSONDecodeError:
                pass

        if not user_code:
            return JsonResponse({'status': 'error', 'message': 'Code au Fingerprint ID inahitajika'}, status=400)

        # 1. Tafuta Employee (kwa employee_code au fingerprint_id)
        employee = Employee.objects.filter(employee_code=user_code).first() or \
                   Employee.objects.filter(fingerprint_id=user_code).first()

        officer = None
        # 2. Kama si Employee, tafuta Officer
        if not employee:
            officer = Officer.objects.filter(officer_code=user_code).first() or \
                      Officer.objects.filter(fingerprint_id=user_code).first()

        if not employee and not officer:
            return JsonResponse({'status': 'error', 'message': f'Mtumiaji mwenye code ({user_code}) hajapatikana'}, status=404)

        today = timezone.now().date()
        now_time = timezone.now().time()

        # Vigezo vya kutafuta kulingana na aina ya mtumiaji
        filter_kwargs = {'attendance_date': today}
        if employee:
            filter_kwargs['employee'] = employee
        elif officer:
            filter_kwargs['officer'] = officer

        # Angalia au tengeneza kumbukumbu ya leo
        attendance, created = Attendance.objects.get_or_create(
            **filter_kwargs,
            defaults={'check_in_time': now_time, 'status': 'PRESENT'}
        )

        full_name = f"{employee.first_name} {employee.last_name}" if employee else f"{officer.first_name} {officer.last_name}"

        if created:
            return JsonResponse({
                'status': 'success',
                'action': 'CHECK_IN',
                'employee': full_name,
                'time': now_time.strftime("%H:%M:%S")
            })
        else:
            if not attendance.check_out_time:
                attendance.check_out_time = now_time
                attendance.save()
                return JsonResponse({
                    'status': 'success',
                    'action': 'CHECK_OUT',
                    'employee': full_name,
                    'time': now_time.strftime("%H:%M:%S")
                })
            else:
                return JsonResponse({
                    'status': 'warning',
                    'message': f'{full_name} ameshamaliza Check-In na Check-Out za leo!'
                })

    except Exception as e:
        # Kukamata kosa lolote la Database au Code ili simulator ionyeshe ujumbe badala ya Status 500 kavu
        return JsonResponse({'status': 'error', 'message': f'Server Error: {str(e)}'}, status=500)