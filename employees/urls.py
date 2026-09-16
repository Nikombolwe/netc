from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'employees'

urlpatterns = [
    path('add-user/', views.add_user_view, name='add_user'),
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/director/', views.director_dashboard, name='director_dashboard'),
    path('dashboard/officer/', views.officer_dashboard, name='officer_dashboard'),

    # Njia ya Mkurugenzi ya kuchakata maombi (Inahitaji parameters)
    path('director/process-request/<int:request_id>/<str:action>/', views.director_process_request, name='director_process_request'),

    # Njia ya Afisa ya kuchakata maombi
    path('officer/process-request/<int:request_id>/<str:action>/', views.officer_process_request, name='officer_process_request'),
    
    path('export-attendance/', views.export_attendance_csv, name='export_attendance_csv'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]