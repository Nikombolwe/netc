from django.urls import path
from . import views

urlpatterns = [
    path('add-user/', views.add_user_view, name='add_user'),
]