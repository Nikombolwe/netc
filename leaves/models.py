from django.db import models
from django.contrib.auth.models import User

class LeaveBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leave_balance')
    annual_leave_days = models.IntegerField(default=28)  # Siku za likizo kwa mwaka
    emergency_leave_count = models.IntegerField(default=5)  # Mara za ruhusa ya dharura kwa mwaka

    def __str__(self):
        return f"Balance for {self.user.username}"

class RequestApplication(models.Model):
    REQUEST_TYPES = (
        ('LATE_ARRIVAL', 'Kuchelewa Kuingia Kazini'),
        ('ABSENCE', 'Kutohudhuria Kazini (Siku 1/chache)'),
        ('EMERGENCY', 'Ruhusa ya Dharura'),
        ('ANNUAL_LEAVE', 'Likizo ya Mwaka'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Inasubiri'),
        ('APPROVED', 'Imekubaliwa'),
        ('REJECTED', 'Imekataliwa'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)