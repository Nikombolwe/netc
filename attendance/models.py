from django.db import models
from employees.models import Employee, Officer

class AttendanceLog(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('LATE', 'Late'),
        ('ABSENT', 'Absent'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    officer = models.ForeignKey(Officer, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')

    class Meta:
        db_table = 'attendance_logs'

    def __str__(self):
        user_name = self.employee or self.officer
        return f"{user_name} - {self.date}"