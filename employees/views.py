from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User  # Inatumia meza ya auth_user
from django.db import transaction
from .models import Department, OfficerPosition
from .forms import UserRegistrationForm, EmployeeProfileForm, OfficerProfileForm

def add_user_view(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        emp_form = EmployeeProfileForm(request.POST)
        officer_form = OfficerProfileForm(request.POST)

        user_type = request.POST.get('user_type')
        fp_credential = request.POST.get('fingerprint_credential_id', '')

        if user_form.is_valid():
            try:
                # Inahakikisha data zinasave pamoja bila kuacha taarifa nusu
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
                            return redirect('admin_overview')
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
                            return redirect('admin_overview')
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