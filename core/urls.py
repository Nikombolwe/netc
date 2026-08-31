from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('django-admin/', admin.site.urls),
    
    # Kuelekeza Root URL (/) moja kwa moja kwenye Login Page
    path('', lambda request: redirect('login'), name='root_redirect'),
    
    # App ya Authentication
    path('auth/', include('authentication.urls')),
    
    # App za Mfumo
    path('dashboard/', include('dashboard.urls')),
    path('employees/', include('employees.urls')),
    path('attendance/', include('attendance.urls')),
    
    # Njia ya Mkato (Shortcut) kuzuia 404 ukipiga /admin-overview/ pekee
    path('admin-overview/', lambda request: redirect('dashboard:admin_overview')),
    
    
]