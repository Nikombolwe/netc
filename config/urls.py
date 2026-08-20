from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('attendance/', include('attendance.urls')), # Au jina la app yako
]