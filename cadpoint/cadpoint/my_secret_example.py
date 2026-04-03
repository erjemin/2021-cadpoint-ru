# -*- coding: utf-8 -*-
"""Шаблон локальных секретов для CADpoint.

Скопируй этот файл в `my_secret.py` и заполни реальными значениями вне Git.
"""

# Секретный ключ Django.
MY_SECRET_KEY = "CHANGE_ME"

# Имена хостов, на которых включается DEBUG.
MY_HOST_HOME = "CHANGE_ME"
MY_HOST_WORK = "CHANGE_ME"

# Локальные пути для разработки.
MY_MEDIA_ROOT_DEV = "/path/to/media/dev"
MY_STATIC_ROOT_DEV = "/path/to/static/dev"

# Почта для разработки.
MY_EMAIL_HOST_DEV = "smtp.example.com"
MY_EMAIL_PORT_DEV = 587
MY_EMAIL_HOST_USER_DEV = "user@example.com"
MY_EMAIL_HOST_PASSWORD_DEV = "CHANGE_ME"
MY_EMAIL_FROM_DEV = "user@example.com"

# База данных для разработки.
MY_DATABASE_HOST_DEV = "127.0.0.1"
MY_DATABASE_PORT_DEV = 3306
MY_DATABASE_NAME_DEV = "cadpoint_dev"
MY_DATABASE_USER_DEV = "cadpoint_dev"
MY_DATABASE_PASSWORD_DEV = "CHANGE_ME"

# Пути для production.
MY_MEDIA_ROOT_PROD = "/path/to/media/prod"
MY_STATIC_ROOT_PROD = "/path/to/static/prod"

# Почта для production.
MY_EMAIL_HOST_PROD = "smtp.example.com"
MY_EMAIL_PORT_PROD = 587
MY_EMAIL_HOST_USER_PROD = "user@example.com"
MY_EMAIL_HOST_PASSWORD_PROD = "CHANGE_ME"
MY_EMAIL_FROM_PROD = "user@example.com"

# База данных для production.
MY_DATABASE_HOST_PROD = "127.0.0.1"
MY_DATABASE_PORT_PROD = 3306
MY_DATABASE_NAME_PROD = "cadpoint_prod"
MY_DATABASE_USER_PROD = "cadpoint_prod"
MY_DATABASE_PASSWORD_PROD = "CHANGE_ME"

