from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('dashboard.urls')),  # Inaelekeza kwenda kwenye dashboard app
    path('employees/', include('employees.urls')),
]