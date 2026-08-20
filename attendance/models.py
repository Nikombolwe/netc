from django.db import models
from employees.models import Employee, Officer

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('LATE', 'Late'),
        ('ABSENT', 'Absent'),
    ]

    # Mahusiano ya Mfanyakazi (Employee)
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        db_column='employee_id',
        related_name='attendances'
    )
    
    # Mahusiano ya Afisa (Officer)
    officer = models.ForeignKey(
        Officer, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        db_column='officer_id',
        related_name='officer_attendances'
    )
    
    # Taarifa za Mahudhurio
    attendance_date = models.DateField(auto_now_add=True, db_index=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    is_late = models.BooleanField(default=False)
    lateness_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        # Huongeza kasi ya search kwenye database wakati wa kuangalia mahudhurio ya leo
        indexes = [
            models.Index(fields=['attendance_date', 'employee']),
            models.Index(fields=['attendance_date', 'officer']),
        ]

    def __str__(self):
        user_name = self.employee or self.officer or "Unknown User"
        return f"{user_name} - {self.attendance_date}"