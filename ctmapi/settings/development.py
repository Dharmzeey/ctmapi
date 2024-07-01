from .base import *
DEBUG = True

ALLOWED_HOSTS = ['*']

SECRET_KEY = "django-insecure-gi5bknhnt_k4=-b-it8qq0x9ug&a+8zja96)=*cu=8q92$k0ic"

DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': "ctmapi",
    'USER': "postgres",
    'PASSWORD': "Azeezat1@",
    'HOST': "127.0.0.1",
    'PORT': '',
  }
}


# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'campustrademart@gmail.com'
EMAIL_HOST_PASSWORD = 'ciac ljwi qlgb itar'


# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'rest_framework_simplejwt.authentication.JWTAuthentication',
#         # 'rest_framework.authentication.SessionAuthentication',
#         # 'rest_framework.authentication.BasicAuthentication',
#         # 'rest_framework.authentication.TokenAuthentication',
#     ),
# }

MEDIA_ROOT = "C://pycharm/django_project/storage/ctm/media"