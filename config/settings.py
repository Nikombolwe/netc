"""
Django settings for Smart Employee Attendance & Workforce Management System.
Generated for project 'smart_attendance' / 'netc'.
"""
import pymysql
pymysql.install_as_MySQLdb()

# Bypassing MySQL 8.4 restriction for cPanel (MySQL 8.0.x)
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

import pymysql
pymysql.install_as_MySQLdb()

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
    # 'attendance',
    # 'leaves',
    # 'emergencies',
    # 'permissions',
    # 'business_trips',
    # 'notifications',
    # 'warnings',
    # 'reports',
    'dashboard',
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

ROOT_URLCONF = 'core.urls'  # Badilisha 'config' ikiwa jina la folder lako la settings ni tofauti (mfano 'netc.urls')

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
# 7. DATABASE CONFIGURATION (MySQL)
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# 7. DATABASE CONFIGURATION (Direct MySQL phpMyAdmin Connection)
# ----------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'netcadvent_smart_attendance_db', # Jina kamili la DB kutoka cPanel
        'USER': 'netcadvent_agape',                     # User uliyemtengeneza cPanel
        'PASSWORD': 'foddyn-teprar-zeRri4',           # Password uliyotengeneza cPanel
        'HOST': '167.86.86.227',  # au 'ran-002.routeafrica.net'           # Mfano '192.168.1.1' au 'yourdomain.com'
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
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

TIME_ZONE = 'Africa/Dar_es_Salaam'  # Imewekwa Swahili/East Africa Time Zone

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