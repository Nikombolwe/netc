from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    # Django Admin Asili
    path('django-admin/', admin.site.urls),
    
    # Kuelekeza Root URL (/) moja kwa moja kwenye Login Page ya Authentication
    path('', lambda request: redirect('login'), name='root_redirect'),
    
    # App ya Authentication (Inajumuisha login, logout, n.k)
    path('auth/', include(('authentication.urls', 'authentication'), namespace='authentication')),
    
    # App za Mfumo zote zimewekewa Namespaces kwa usalama wa URL routing
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    
    # Hapa ndipo kwenye add_user (Employees App)
    path('employees/', include(('employees.urls', 'employees'), namespace='employees')),
    
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    
    # Njia ya Mkato (Shortcut) kuzuia 404 ukipiga /admin-overview/ pekee
    path('admin-overview/', lambda request: redirect('dashboard:admin_overview')),
]