from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

# Muhimu sana ili Django itambue njia zako kupitia namespace ya 'employees'
app_name = 'employees'

urlpatterns = [
    # Usajili wa Watumiaji
    path('add-user/', views.add_user_view, name='add_user'),
    
    # Dashboards za Aina Tatu za Watumiaji (Zinajumuisha Check-In/Out ya Mfanyakazi)
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/director/', views.director_dashboard, name='director_dashboard'),
    path('dashboard/officer/', views.officer_dashboard, name='officer_dashboard'),

    # Njia za Mkurugenzi Kukubali au Kukataa Ombi la Mfanyakazi
    path('director/process-request/<int:request_id>/<str:action>/', views.director_process_request, name='director_process_request'),

    # Njia za Maofisa Kukubali au Kukataa Ombi (Final Approval)
    path('officer/process-request/<int:request_id>/<str:action>/', views.officer_process_request, name='officer_process_request'),

    # Njia ya Kutoa Ripoti (CSV Export)
    path('export-attendance/', views.export_attendance_csv, name='export_attendance_csv'),

    # Njia ya Kutoka (Logout)
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]