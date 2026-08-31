from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Inafanya kazi ukienda /dashboard/ au /dashboard/admin-overview/
    path('', views.admin_overview, name='admin_overview'),
    path('admin-overview/', views.admin_overview, name='admin_overview_alt'),
    
]