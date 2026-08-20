from django.urls import path
from .views import employee_checkin_view, fingerprint_scan_api

urlpatterns = [
    path('check-in/', employee_checkin_view, name='employee_checkin'),
    path('api/scan/', fingerprint_scan_api, name='fingerprint_scan_api'),
]