from django.urls import path
from . import views

urlpatterns = [
    path('api/scan/', views.fingerprint_scan_api, name='api_scan'),
]