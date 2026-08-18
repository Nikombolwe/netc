from django.urls import path
from . import views

urlpatterns = [
    path('admin-overview/', views.admin_overview, name='admin_overview'),
]