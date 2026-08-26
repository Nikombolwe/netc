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
        ordering = ['department_name']

    def __str__(self):
        return self.department_name

    @property
    def name(self):
        """Inarudisha jina la idara kurahisisha matumizi ya template/views."""
        return self.department_name


# --------------------------------------------------------
# 2. OFFICER POSITIONS
# --------------------------------------------------------
class OfficerPosition(models.Model):
    """Vyeo vya Kiutawala: Mwenyekiti, Katibu, Mhazini, nk."""
    position_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'employees_officerposition'
        ordering = ['position_name']

    def __str__(self):
        return self.position_name

    @property
    def name(self):
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
    employee_code = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='employees'
    )
    is_director = models.BooleanField(default=False, db_index=True)
    fingerprint_id = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employees'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        role_label = "Director" if self.is_director else "Employee"
        return f"{self.full_name} ({role_label} - {self.employee_code})"

    @property
    def full_name(self):
        """
        Inachukua majina kutoka Employee profile; kama yako tupu, 
        inachukua kutoka User model au kurudisha Username.
        """
        fname = self.first_name or ""
        lname = self.last_name or ""
        name = f"{fname} {lname}".strip()

        if not name and self.user:
            fname = self.user.first_name or ""
            lname = self.user.last_name or ""
            name = f"{fname} {lname}".strip()

        return name if name else (self.user.username if self.user else f"Employee #{self.id}")


# --------------------------------------------------------
# 4. OFFICER PROFILE
# --------------------------------------------------------
class Officer(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='officer_profile'
    )
    officer_code = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    position = models.ForeignKey(
        OfficerPosition, 
        on_delete=models.RESTRICT, 
        db_column='position_id',
        related_name='officers',
        null=True,
        blank=True
    )
    fingerprint_id = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employees_officer'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        pos = self.position.position_name if self.position else 'No Position'
        return f"{self.full_name} ({pos})"

    @property
    def full_name(self):
        """
        Inachukua majina kutoka Officer profile; kama yako tupu, 
        inachukua kutoka User model au kurudisha Username.
        """
        fname = self.first_name or ""
        lname = self.last_name or ""
        name = f"{fname} {lname}".strip()

        if not name and self.user:
            fname = self.user.first_name or ""
            lname = self.user.last_name or ""
            name = f"{fname} {lname}".strip()

        return name if name else (self.user.username if self.user else f"Officer #{self.id}")