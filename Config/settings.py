from dotenv import load_dotenv
import os 
from pathlib import Path
import cloudinary 
import cloudinary.uploader
import cloudinary.api

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-8m$=11%5!af2-ya((l_d)k$i=#07evr*vdkhh207sj#crui+la')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'usuarios.apps.UsuariosConfig',
    'productos',
    'pagos',
    'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "productos.context_processors.carrito_y_categorias",
            ],
        },
    },
]

WSGI_APPLICATION = 'Config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'softFinal'),
        'USER': os.getenv('DB_USER', 'eduardo'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'eduardo123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
AUTH_USER_MODEL = 'usuarios.Usuario'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"), api_secret = os.getenv("CLOUDINARY_API_SECRET"), secure=True
)

MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

LOGIN_URL = 'usuarios:login'

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'naturistasoftnatur@gmail.com')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'jsaovucsgwdhtdro')
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

RESEND_API_KEY = os.getenv('RESEND_API_KEY', default='')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', default='noreply@softnatur.sebacry.me')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Configuración adicional
EMAIL_SUBJECT_PREFIX = '[softnatur]'
EMAIL_USE_LOCALTIME = False
EMAIL_TIMEOUT = 30

# Resend API Configuration (no SMTP ports, works with Render free tier)
if RESEND_API_KEY:
    EMAIL_BACKEND = 'Config.emailsbackends.ResendEmailBackend'
else:
    # Fallback para desarrollo sin API key
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



BOLD_API_KEY = os.getenv("BOLD_API_KEY")
BOLD_SECRET_KEY = os.getenv("BOLD_SECRET_KEY")

CSRF_TRUSTED_ORIGINS = [
    'https://kamala-isotheral-charlyn.ngrok-free.dev'
]

import dj_database_url

# Obtener DATABASE_URL
database_url = os.getenv('DATABASE_URL')

# Si existe DATABASE_URL, estamos en Railway (producción)
if database_url:
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # ALLOWED_HOSTS para Railway
    ALLOWED_HOSTS = [
        os.getenv('RAILWAY_PUBLIC_DOMAIN', ''),
        '.up.railway.app',
        '*'
    ]
    
    # Base de datos de Railway
    DATABASES = {
        'default': dj_database_url.parse(database_url)
    }
    
    # Archivos estáticos para producción
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # CSRF trusted origins
    CSRF_TRUSTED_ORIGINS = [
        'https://*.up.railway.app',
        'https://web-production-1e907.up.railway.app',
        'https://softnatur.sebacry.me',
        'https://kamala-isotheral-charlyn.ngrok-free.dev'
    ]
else:
    # Configuración local (desarrollo)
    DEBUG = True
    ALLOWED_HOSTS = ["*"]
    # La configuración de DATABASES local ya está definida arriba


