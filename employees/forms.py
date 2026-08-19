from django import forms
from django.contrib.auth.models import User
from .models import Employee, Officer, Department, OfficerPosition

# --------------------------------------------------------
# 1. USER CREATION FORM (Basic User Account)
# --------------------------------------------------------
class UserRegistrationForm(forms.ModelForm):
    USER_TYPE_CHOICES = [
        ('employee', 'Employee Wa Kawaida'),
        ('director', 'Director (Mkuu wa Idara)'),
        ('officer', 'Officer (Mwenyekiti / Katibu / Mhazini)'),
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES, 
        widget=forms.Select(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
        }

# --------------------------------------------------------
# 2. EMPLOYEE / DIRECTOR PROFILE FORM
# --------------------------------------------------------
class EmployeeProfileForm(forms.ModelForm):
    # Field ya department inavuta idara zote kutoka database moja kwa moja
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label="- Chagua Idara -",
        required=False,
        widget=forms.Select(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'})
    )

    class Meta:
        model = Employee
        fields = ['employee_code', 'first_name', 'last_name', 'phone_number', 'job_title', 'department']
        widgets = {
            'employee_code': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'job_title': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
        }

# --------------------------------------------------------
# 3. OFFICER PROFILE FORM
# --------------------------------------------------------
class OfficerProfileForm(forms.ModelForm):
    # Field ya position inavuta vyeo vyote kutoka database
    position = forms.ModelChoiceField(
        queryset=OfficerPosition.objects.all(),
        empty_label="- Chagua Cheo -",
        required=False,
        widget=forms.Select(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'})
    )

    class Meta:
        model = Officer
        fields = ['officer_code', 'first_name', 'last_name', 'phone_number', 'position']
        widgets = {
            'officer_code': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full p-2.5 bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block'}),
        }