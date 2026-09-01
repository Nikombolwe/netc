"""
Django settings for Smart Employee Attendance & Workforce Management System.
Generated for project 'smart_attendance' / 'netc'.
"""
from pathlib import Path
import os
from decouple import config

# ----------------------------------------------------------------------
# 1. PYMYSQL INITIALIZATION (Required for macOS / MySQL compatibility)
# ----------------------------------------------------------------------
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Bypassing MySQL 8.4 restriction for cPanel (MySQL 8.0.x)
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

# ----------------------------------------------------------------------
# 2. BASE DIRECTORY
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# 3. SECURITY SETTINGS
# ----------------------------------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-smart-attendance-system-key-change-this-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

# ----------------------------------------------------------------------
# 4. INSTALLED APPS (System Modules)
# ----------------------------------------------------------------------
INSTALLED_APPS = [
    # Default Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Packages
    'rest_framework',  # Django REST Framework for APIs

    # System Custom Apps (Modules)
    'employees',
    'attendance',
    'leaves',
    # 'emergencies',
    # 'permissions',
    # 'business_trips',
    # 'notifications',
    'warnings',
    # 'reports',
    'dashboard',
    'communications',
]

# ----------------------------------------------------------------------
# 5. MIDDLEWARE
# ----------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ----------------------------------------------------------------------
# 6. TEMPLATES
# ----------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ----------------------------------------------------------------------
# 7. DATABASE CONFIGURATION (Direct MySQL phpMyAdmin Connection)
# ----------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'netcadvent_smart_attendance_db',
        'USER': 'netcadvent_agape',
        'PASSWORD': 'Attendence.smart.2026!',
        'HOST': '167.86.86.227',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET time_zone = '+03:00', sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# ----------------------------------------------------------------------
# 8. PASSWORD VALIDATION
# ----------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ----------------------------------------------------------------------
# 9. INTERNATIONALIZATION
# ----------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Dar_es_Salaam'  # East Africa Time Zone (EAT)

USE_I18N = True

USE_TZ = True

# ----------------------------------------------------------------------
# 10. STATIC AND MEDIA FILES (CSS, JS, Uploaded Attachments)
# ----------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ----------------------------------------------------------------------
# 11. DEFAULT PRIMARY KEY FIELD TYPE
# ----------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------------------------------------------------------------
# 12. REST FRAMEWORK SETTINGS (APIs for Biometric Device / Mobile)
# ----------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ----------------------------------------------------------------------
# 13. EMAIL CONFIGURATION (Google Workspace / NETC HQ)
# ----------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='info@netcadventist.org')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='qwojyagougqzusus')

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='NETC Attendance System <info@netcadventist.org>')
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/admin-overview/'
LOGOUT_REDIRECT_URL = '/auth/login/'