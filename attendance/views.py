import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from employees.models import Employee, Officer
from .models import AttendanceLog

@csrf_exempt
def fingerprint_scan_api(request):
    if request.method == 'POST':
        # Tunapokea code (inaweza kuwa employee_code, officer_code au fingerprint_id)
        user_code = request.POST.get('employee_code') or request.POST.get('user_code')
        
        if not user_code:
            return JsonResponse({'status': 'error', 'message': 'Code au Fingerprint ID inahitajika'}, status=400)
        
        # 1. Tafuta kama ni Employee (kwa employee_code au fingerprint_id)
        employee = Employee.objects.filter(employee_code=user_code).first() or \
                   Employee.objects.filter(fingerprint_id=user_code).first()
        
        officer = None
        # 2. Kama si Employee, tafuta kama ni Officer
        if not employee:
            officer = Officer.objects.filter(officer_code=user_code).first() or \
                      Officer.objects.filter(fingerprint_id=user_code).first()
            
        if not employee and not officer:
            return JsonResponse({'status': 'error', 'message': 'Mtumiaji hajapatikana kwenye mfumo'}, status=404)
        
        today = timezone.now().date()
        now = timezone.now()
        
        # Vigezo vya kutafuta kulingana na aina ya mtumiaji
        filter_kwargs = {'date': today}
        if employee:
            filter_kwargs['employee'] = employee
        else:
            filter_kwargs['officer'] = officer

        # Angalia au tengeneza kumbukumbu ya leo
        attendance, created = AttendanceLog.objects.get_or_create(
            **filter_kwargs,
            defaults={'check_in': now.time(), 'status': 'PRESENT'}
        )
        
        full_name = f"{employee.first_name} {employee.last_name}" if employee else f"{officer.first_name} {officer.last_name}"
        
        if created:
            # Mara ya kwanza kuscan kwa siku - CHECK-IN
            return JsonResponse({
                'status': 'success',
                'action': 'CHECK_IN',
                'employee': full_name,
                'time': now.strftime("%H:%M:%S")
            })
        else:
            # Mara ya pili kuscan - CHECK-OUT
            if not attendance.check_out:
                attendance.check_out = now.time()
                attendance.save()
                return JsonResponse({
                    'status': 'success',
                    'action': 'CHECK_OUT',
                    'employee': full_name,
                    'time': now.strftime("%H:%M:%S")
                })
            else:
                # Mara ya tatu au zaidi
                return JsonResponse({
                    'status': 'warning',
                    'message': f'{full_name} ameshamaliza Check-In na Check-Out za leo!'
                })
                
    return JsonResponse({'status': 'error', 'message': 'Ombi si sahihi (POST inahitajika)'}, status=400)