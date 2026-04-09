"""Настройки Django для проекта cadpoint."""

import os
from pathlib import Path

import environ


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))


def _normalize_admin_url(value: str) -> str:
    """Приводит URL админки к виду `segment/` без ведущего слэша."""
    normalized = value.strip().lstrip('/')
    if not normalized:
        return 'admin/'
    if not normalized.endswith('/'):
        normalized += '/'
    return normalized


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY', default='django-insecure-change-me')
ADMIN_URL = _normalize_admin_url(env('ADMIN_URL', default='admin/'))

DEBUG = env.bool('DJANGO_DEBUG', default=False)


ALLOWED_HOSTS = env.list(
    'DJANGO_ALLOWED_HOSTS',
    default=['127.0.0.1', 'localhost', 'cadpoint.ru'],
)

#########################################
# Настройки сообщений об ошибках когда все упало и т.п.
ADMINS = tuple(
    tuple(item.split(':', 1))
    for item in env.list('DJANGO_ADMINS', default=['S.Erjemin:erjemin@gmail.com'])
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Панель отладки показываем только в dev-окружении при `DEBUG=True`.
    'debug_toolbar',
    'easy_thumbnails',
    'filer.apps.FilerConfig',
    'mptt.apps.MpttConfig',
    # # 'ckeditor_uploader',
    'ckeditor',
    'taggit.apps.TaggitAppConfig',
    # 'fontawesome-free'
    'web.apps.WebConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Middleware нужен, иначе панель debug toolbar просто не влезет в response.
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cadpoint.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'cadpoint.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
LANGUAGE_CODE = 'ru-RU'         # <--------- RUSSIAN
# TIME_ZONE = 'Etc/GMT+3'       #
TIME_ZONE = 'Europe/Moscow'     #
USE_I18N = True
USE_L10N = True
USE_TZ = True                   # учитывать часовой пояс
FIRST_DAY_OF_WEEK = 1           # неделя начинается с понедельника
DEFAULT_CHARSET = 'utf-8'


# настройки THUMBNAIL (батарейка по созданию превьюшек)
THUMBNAIL_HIGH_RESOLUTION = True  # Для easy_thumbnails поддержки retina-дисплеев (MacBooks, iOS и т.п.)
THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    #'easy_thumbnails.processors.scale_and_crop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters',
)
THUMBNAIL_ALIASES = {
    '': {
        'x64': {'size': (64, 64), 'crop': True},
        'x680': {'size': (680, 680), 'crop': True},
        'x1140': {'size': (1140, 1140), 'crop': True},
    },
}
THUMBNAIL_QUALITY = 85
THUMBNAIL_TRANSPARENCY_EXTENSION = 'png'
THUMBNAIL_WIDGET_OPTIONS = {'size': (64, 64)}


CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"
CKEDITOR_FILENAME_GENERATOR = 'utils.get_filename'
# конфигуратор ckeditor https://ckeditor.com/latest/samples/toolbarconfigurator/index.html#basic
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar_mini': [
            {'name': 'document', 'items': ['Source', '-', ]},
            {'name': 'basicstyles', 'items': ['Bold', 'Italic', 'Underline', 'NumberedList', 'BulletedList',
                                              'Format', '-', 'RemoveFormat']},
            {'name': 'my_custom_tools', 'items': ['Preview', 'Maximize']},
        ],
        'toolbar': 'mini',  # put selected toolbar config here
        'height': '110',
        'toolbarCanCollapse': True,
    },
    'fine': {
        'toolbar_fine': [
            {'name': 'document', 'items': ['Source', '-' ]},
            {'name': 'clipboard', 'items': ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo']},
            {'name': 'basicstyles',
             'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat']},
            {'name': 'my_custom_tools', 'items': ['Preview', 'Maximize']},
            '/',
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv', '-',
                       'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock', 'Styles', 'Format', 'Iframe']},
            {'name': 'links', 'items': ['Link', 'Unlink', 'Anchor']},
            {'name': 'insert', 'items': ['Image', 'Table', 'HorizontalRule', 'SpecialChar']},
        ],
        'toolbar': 'fine',
        # 'removeButtons': 'Save,NewPage,ExportPdf,Preview,Print,Templates,Find,Replace,SelectAll,Scayt,Form,'
        #                  'Checkbox,Radio,TextField,Textarea,Select,Button,ImageButton,HiddenField,Format,'
        #                  'Font,FontSize,Maximize,ShowBlocks,About,Styles,Flash,Smiley,PageBreak,Iframe,BidiLtr,'
        #                  'BidiRtl,Language,JustifyBlock,JustifyRight,JustifyCenter,JustifyLeft,Indent,Outdent,'
        #                  'Strike,TextColor,BGColor,
        'toolbarCanCollapse': True,
        # 'extraPlugins': 'filer',
        # 'editor': [
        #     {'name': 'filebrowserBrowseUrl', 'items': ''},
        #     {'name': 'filebrowserUploadUrl', 'items': ''},
        # ],
    },
}

FILER_SUBJECT_LOCATION_IMAGE_DEBUG = True
FILER_CANONICAL_URL = 'sharing/'


STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Локальные каталоги проекта: медиа и статика лежат рядом в `public`.
PUBLIC_DIR = BASE_DIR.parent.joinpath('public')
MEDIA_ROOT = PUBLIC_DIR.joinpath('media')
STATICFILES_DIRS = [PUBLIC_DIR.joinpath('static')]
STATIC_ROOT = PUBLIC_DIR.joinpath('staticfiles')
CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])
# Внутренние адреса для debug toolbar: локальный браузер и loopback.
INTERNAL_IPS = env.list('DJANGO_INTERNAL_IPS', default=['127.0.0.1', '::1'])

# Настройки почтового сервера и базы данных читаются одинаково для всех окружений.
EMAIL_HOST = env('DJANGO_EMAIL_HOST', default='smtp.mail.ru')  # SMTP server
EMAIL_PORT = env.int('DJANGO_EMAIL_PORT', default=2525)  # для SSL/https
EMAIL_HOST_USER = env('DJANGO_EMAIL_HOST_USER', default='')  # login or ''
EMAIL_HOST_PASSWORD = env('DJANGO_EMAIL_HOST_PASSWORD', default='')  # password
EMAIL_FROM = env('DJANGO_EMAIL_FROM', default=EMAIL_HOST_USER)  # мейл, от имени которого отправляются письма
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent.joinpath('database', env('DJANGO_SQLITE_NAME', default='cadpoint-db.sqlite3')),
    }
}

SERVER_EMAIL = DEFAULT_FROM_EMAIL = EMAIL_FROM
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = '[CADPOINT.RU]: '  # префикс для оповещений об ошибках и необработанных исключениях

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
