from .settings import * # Import everything from the main settings

# 1. Use a fast, local database (sqlite is common, or just a separate postgres test db)
# Django handles this automatically usually, but you can be explicit.

# 2. OVERRIDE STORAGES
# We swap MinIO for standard FileSystemStorage
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# 3. Handle the "Clutter" with a temporary Media Root
import tempfile
# This creates a unique directory in your OS temp folder every time you run tests
MEDIA_ROOT = tempfile.mkdtemp() 

# 4. Use a faster Password Hasher (Speeds up tests significantly!)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# 5. Fast Cache (In-memory instead of Redis)
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#     }
# }