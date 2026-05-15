import environ
import os
from pathlib import Path

env = environ.Env(
    DEBUG=(bool, False),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ============================================================================
# 1. CORE DJANGO SETTINGS
# ============================================================================


SECRET_KEY = env.str('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = ["*"]
APPEND_SLASH = True
WSGI_APPLICATION = 'project.wsgi.application'
ASGI_APPLICATION = "project.asgi.application"
ROOT_URLCONF = 'project.urls'


# ============================================================================
# 2. INSTALLED APPS & MIDDLEWARE
# ============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-Party Apps
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',

    # Project apps
    'apps.authentication.apps.AuthenticationConfig',
    'apps.document.apps.DocumentConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================================
# 3.  AUTHENTICATION & AUTHORIZATION
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

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

# ============================================================================
# 4. SWAGGER CONFIGURATION
# ============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Sanaap API Challenge',
    'DESCRIPTION': ':)',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    # Other optional settings
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,

    # Force using local files instead of CDN
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

# ============================================================================
# 5. TEMPLATES & INTERNATIONALIZATION
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ============================================================================
# 6. DATABASE CONFIGURATION
# ============================================================================

DATABASES = {
    'default': env.db('DATABASE_URL')
}

# ============================================================================
# 7. CACHE CONFIGURATION
# ============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env('DEFAULT_REDIS_URL'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        'KEY_PREFIX': 'docs',
    }
}
DOCUMENT_CACHE_TTL = env.int('DOCUMENT_CACHE_TTL')

# ============================================================================
# 8. STORAGE (MINIO) CONFIGURATION
# ============================================================================

STORAGES = {
    "default": {
        "BACKEND": "apps.document.storage.MinIOStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


AWS_ACCESS_KEY_ID = env('MINIO_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = env('MINIO_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = env('MINIO_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = env('MINIO_ENDPOINT')
MINIO_PUBLIC_ENDPOINT_URL = env('MINIO_PUBLIC_ENDPOINT_URL')
AWS_S3_REGION_NAME = 'us-east-1'


AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 60 * 60
AWS_S3_FILE_OVERWRITE = False
AWS_S3_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ============================================================================
# 9. CELERY CONFIGURATION
# ============================================================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL')          # same Redis instance, different DB fine
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_RESULT_EXPIRES = 60 * 60 * 24
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ACKS_LATE = True       # task re-queued if worker dies mid-flight
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # fair dispatch under heavy load

# ============================================================================
# 10. SESSION & STATIC & MEDIA
# ============================================================================

SESSION_COOKIE_AGE = 60 * 60 * 24

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
