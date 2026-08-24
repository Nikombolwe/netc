from django.urls import path
from . import views

urlpatterns = [
    # Njia yako ya zamani ya usajili
    path('add-user/', views.add_user_view, name='add_user'),
    
    # Dashboards za Aina Tatu za Watumiaji (Hizi ndizo zilikuwa zinatakiwa na Login system)
    path('dashboard/employee/', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/director/', views.director_dashboard, name='director_dashboard'),
    path('dashboard/officer/', views.officer_dashboard, name='officer_dashboard'),
]