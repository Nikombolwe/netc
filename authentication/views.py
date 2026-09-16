from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

def redirect_user_by_role(user):
    """Helper function ya kuelekeza mtumiaji kwenye dashboard husika"""
    # Admin anaingia moja kwa moja kupitia is_staff au is_superuser
    if user.is_staff or user.is_superuser:
        return redirect('dashboard:admin_dashboard')  # Rekebisha namespace ya dashboard kama ipo tofauti
    elif hasattr(user, 'officer_profile'):
        return redirect('employees:officer_dashboard')
    elif hasattr(user, 'employee_profile'):
        if user.employee_profile.is_director:
            return redirect('employees:director_dashboard')
        return redirect('employees:employee_dashboard')
    return redirect('authentication:login')


@csrf_exempt
def custom_login_view(request):
    # Kama mtumiaji tayari ameingia, mwelekeze kwenye dashboard yake au Admin moja kwa moja
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        return redirect_user_by_role(request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 0. ADMIN / SUPERUSER BYPASS (Anaingia moja kwa moja bila kukwama)
            if user.is_staff or user.is_superuser or role == 'admin':
                login(request, user)
                return redirect('dashboard:admin_dashboard')

            # 1. OFFICER
            elif role == 'officer':
                if hasattr(user, 'officer_profile'):
                    login(request, user)
                    return redirect('employees:officer_dashboard')
                messages.error(request, "Akaunti hii haijasajiliwa kama Officer.")

            # 2. DIRECTOR
            elif role == 'director':
                if hasattr(user, 'employee_profile') and user.employee_profile.is_director:
                    login(request, user)
                    return redirect('employees:director_dashboard')
                messages.error(request, "Akaunti hii haijasajiliwa kama Mkurugenzi (Director).")

            # 3. EMPLOYEE
            elif role == 'employee':
                if hasattr(user, 'employee_profile') and not user.employee_profile.is_director:
                    login(request, user)
                    return redirect('employees:employee_dashboard')
                messages.error(request, "Akaunti hii haijasajiliwa kama Mfanyakazi wa kawaida.")
            else:
                messages.error(request, "Tafadhali chagua aina halisi ya akaunti yako.")

        else:
            messages.error(request, "Jina la mtumiaji au neno la siri si sahihi.")

    return render(request, 'registration/login.html')


def custom_logout_view(request):
    """Inamtoa mtumiaji kwenye mfumo na kumrejesha ukurasa wa login"""
    logout(request)
    messages.success(request, "Umetoka kwenye mfumo kikamilifu.")
    return redirect('authentication:login')