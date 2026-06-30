from .base import *  # noqa

DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # prints emails to terminal instead of sending
