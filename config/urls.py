from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  # Kwa ajili ya Logout ya Django

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Hapa tunaongeza app ya employees (kwa ajili ya add_user, dashboards, n.k.)
    path('employees/', include('employees.urls')), 
    
    # 2. App ya mahudhurio
    path('attendance/', include('attendance.urls')), 
    
    # 3. Built-in Login & Logout ya Django (Inazuia NoReverseMatch ya 'logout')
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
]