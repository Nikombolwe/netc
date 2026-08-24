from django.db import models
from django.contrib.auth.models import User

# --------------------------------------------------------
# 1. DEPARTMENTS
# --------------------------------------------------------
class Department(models.Model):
    department_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    head_of_department = models.ForeignKey(
        'Employee', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='head_of_employee_id',
        related_name='managed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return self.department_name


# --------------------------------------------------------
# 2. OFFICER POSITIONS
# --------------------------------------------------------
class OfficerPosition(models.Model):
    """Vyeo vya Kiutawala: Mwenyekiti, Katibu, Mhazini, nk."""
    position_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        # IMEBADILISHWA: Lazima isome 'employees_officerposition' ili Foreign Key ya MySQL isikatae
        db_table = 'employees_officerposition'

    def __str__(self):
        return self.position_name


# --------------------------------------------------------
# 3. EMPLOYEES
# --------------------------------------------------------
class Employee(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='employee_profile'
    )
    employee_code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='employees'
    )
    is_director = models.BooleanField(default=False)
    fingerprint_id = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employees'

    def __str__(self):
        role_label = "Director" if self.is_director else "Employee"
        return f"{self.first_name} {self.last_name} ({role_label} - {self.employee_code})"


# --------------------------------------------------------
# 4. OFFICER PROFILE
# --------------------------------------------------------
class Officer(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='officer_profile'
    )
    officer_code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    position = models.ForeignKey(
        OfficerPosition, 
        on_delete=models.RESTRICT, 
        db_column='position_id',
        related_name='officers'
    )
    fingerprint_id = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employees_officer'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position.position_name})"