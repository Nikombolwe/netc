from django.db import models
from django.contrib.auth.models import User

class SMSLog(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=50)
    message = models.TextField()
    status = models.CharField(max_length=50, default='PENDING')
    target_group = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.status}"