"""Настройки Django для проекта cadpoint."""

from pathlib import Path
from django.db.backends.signals import connection_created
from django.dispatch import receiver
import environ
import os


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
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

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
    'django.contrib.sitemaps',
    'django_select2',
    'easy_thumbnails',
    'filer.apps.FilerConfig',
    'mptt.apps.MpttConfig',
    'taggit.apps.TaggitAppConfig',
    # 'fontawesome-free'
    'web.apps.WebConfig',
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
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'ru-RU'         # <--------- RUSSIAN
# TIME_ZONE = 'Etc/GMT+3'       #
TIME_ZONE = 'Europe/Moscow'     #
USE_I18N = True
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

# Django 5 требует явное описание хранилищ.
# `default` нужен для загружаемых файлов (filer, FileField, ImageField) и смотрит в `MEDIA_ROOT`.
# `staticfiles` остаётся отдельно: в dev используется обычная статика Django, в prod — WhiteNoise.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': MEDIA_ROOT,
        },
    },
}

# Параметры Select2 в админке.
# Держим их здесь, чтобы не размазывать магические числа по `admin.py`.
SELECT2_AJAX_DELAY_MS = 250
SELECT2_MINIMUM_INPUT_LENGTH = 0
SELECT2_TOKEN_SEPARATORS = '[","]'
SELECT2_PAGE_SIZE = 25

# Параметры SQLite, чтобы дев-окружение не падало на `database is locked`.
# WAL и busy_timeout уменьшают конфликты при чтении/записи, а synchronous=NORMAL
# делает SQLite чуть менее параноидальной, но более живой для локальной разработки.
SQLITE_BUSY_TIMEOUT_MS = 20_000
SQLITE_JOURNAL_MODE = 'WAL'
SQLITE_SYNCHRONOUS = 'NORMAL'


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
        'OPTIONS': {
            'timeout': 20,
        },
    }
}


@receiver(connection_created)
def _configure_sqlite_connection(sender, connection, **kwargs):
    """
    Настраиваем SQLite сразу после открытия соединения.

    Это нужно, чтобы:
    - уменьшить число ошибок `database is locked`;
    - позволить чтению и записи меньше мешать друг другу;
    - сделать dev-среду более терпимой к админке и Select2-поиску.
    """
    if connection.vendor != 'sqlite':
        return
    with connection.cursor() as cursor:
        cursor.execute(f'PRAGMA journal_mode={SQLITE_JOURNAL_MODE};')
        cursor.execute(f'PRAGMA synchronous={SQLITE_SYNCHRONOUS};')
        cursor.execute(f'PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS};')


SERVER_EMAIL = DEFAULT_FROM_EMAIL = EMAIL_FROM
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = 'CADPOINT.RU => '  # префикс для оповещений об ошибках и необработанных исключениях

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================
# ПЕРЕМЕННЫЕ НАСТРОЙКИ ПРОЕКТА
# Число тегов в облаке на главной странице. Выбирается эмпирически, чтобы не
# перегружать интерфейс и не провоцировать лишние запросы к SQLite при
# открытии страницы.
TAG_CLOUD_LIMIT = 20

# Число заголовков статей в боковой панели (лучше чтобы было нечетным, чтобы над текущей статьей было
# равное число заголовков "более ранние" и "более поздние").
NUM_NAV_ITEMS_IN_PAGE = 7

# Число статей (заголовок + тизер) на странице
NUM_ITEMS_IN_PAGE = NUM_NAV_ITEMS_IN_PAGE


if DEBUG:
    # В деве оставляем стандартную отдачу статики Django без WhiteNoise.
    STORAGES['staticfiles'] = {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    }
    # Django Debug Toolbar нужен только в dev
    def _show_debug_toolbar(request):
        """Скрывает debug toolbar внутри админки Django"""
        return not request.path.startswith(f'/{ADMIN_URL}')

    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': _show_debug_toolbar,
    }

else:
    # В проде WhiteNoise обслуживает собранную статику и файлы из `public`.
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STORAGES['staticfiles'] = {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    }
    # Конфигурация WhiteNoise для обслуживания статических файлов и файлов из /public (например,
    # robots.txt, favicon.ico и т.п.)
    WHITENOISE_ROOT = PUBLIC_DIR
