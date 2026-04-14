# CADpoint.ru

Сайт CADpoint.ru — это Django-проект, который сейчас живёт в Docker.

Кратко о схеме:

- сам Django запускается в контейнере `cadpoint-backend`;
- локально используется `docker-compose.local.yml`;
- на проде используется `docker-compose.prod.yml`;
- внешний `nginx` стоит на хосте и проксирует запросы в контейнер;
- конфигурация и секреты лежат в `.env`;
- медиа, статика и SQLite-база живут в проектных каталогах и монтируются в контейнер.

## Что есть в проекте

- `cadpoint/` — Django-проект, приложения, шаблоны, management commands.
- `public/static/` — исходная статика проекта.
- `public/media/` — загруженные файлы и служебные error-assets.
- `database/` — SQLite-база и дампы.
- `config/nginx/` — конфиг внешнего `nginx` для прод-хоста.
- `frontend-assembly/` — сборка CodeMirror 6 для админки.
- `Dockerfile` — финальный образ приложения.
- `docker-compose.local.yml` — локальный запуск.
- `docker-compose.prod.yml` — prod-запуск.

## Быстрый старт

### 1. Подготовить `.env`

Скопируй шаблон и заполни значения:

```bash
cp .env.sample .env
```

Основные переменные:

- Общие:
  - `DJANGO_SECRET_KEY` — секрет Django для подписи сессий, CSRF-токенов, password reset и других подписанных данных. Должен быть уникальным и храниться только в `.env`.
  - `DJANGO_DEBUG` — включает режим отладки Django. Для локальной разработки обычно `True`, для прода — `False`.
  - `DJANGO_ALLOWED_HOSTS` — список доменов и IP, с которых Django принимает запросы. Значения перечисляются через запятую.
  - `DJANGO_ADMINS` — список админов для email-уведомлений о критических ошибках. Формат: `Имя:email@domain` (несколько значений через запятую).
  - `DJANGO_CSRF_TRUSTED_ORIGINS` — список доверенных origin для CSRF. Нужен для доменов, с которых разрешены POST-запросы.
  - `DJANGO_INTERNAL_IPS` — внутренние IP для `debug_toolbar` в dev-режиме. Обычно достаточно `127.0.0.1` и `::1`.
  - `DJANGO_SQLITE_NAME` — имя файла SQLite-базы внутри каталога `database/`. Полный путь собирается через `BASE_DIR.parent / 'database'`.
  - `ADMIN_URL` — относительный URL админки. По умолчанию `admin/`, можно заменить на любой другой сегмент вроде `a-d-m-i-n/`.
  - `DJANGO_EMAIL_HOST` — SMTP-хост почтового сервера.
  - `DJANGO_EMAIL_PORT` — SMTP-порт.
  - `DJANGO_EMAIL_HOST_USER` — логин для SMTP.
  - `DJANGO_EMAIL_HOST_PASSWORD` — пароль или токен для SMTP.
  - `DJANGO_EMAIL_FROM` — адрес отправителя писем. Если не задан, берётся из `DJANGO_EMAIL_HOST_USER`.
- Специфичные для продакшена:
  - `HOST_PROJECT_PATH` — полный путь к проекту на прод-хосте. Используется при генерации nginx-конфига, чтобы подставить правильный `alias` для media-файлов.
  - `REPO_USER` / `REPO_PASS` — логин и токен/пароль для доступа к приватному registry, откуда Watchtower подтягивает новый образ.

Для ориентира:

- `DJANGO_DEBUG` управляет самим Django.
- `DEBUG` в `docker-compose.local.yml` — это служебная переменная контейнера, но в проекте используется именно `DJANGO_DEBUG`.
- `DJANGO_SETTINGS_MODULE` и `PYTHONUNBUFFERED` задаются в Docker Compose и обычно не трогаются вручную.

### 2. Локальная разработка

```bash
docker compose -f docker-compose.local.yml up --build
```

После старта сайт будет доступен на:

```text
http://127.0.0.1:8055
```

### 3. Продакшен на сервере

На сервере должен быть:

- установлен Docker;
- настроен внешний `nginx` на хосте;
- подготовлен `.env`;
- доступен приватный registry с образом проекта.
- в корне проекта на хосте заранее созданы каталоги `database/`, `config/` и `media/` — они монтируются в контейнер как bind-mount'ы.

Запуск:

```bash
docker compose -f docker-compose.prod.yml up -d
```

Backend в контейнере слушает только localhost хоста:

```text
127.0.0.1:8050
```

А уже внешний `nginx` проксирует домен на этот порт.

## Где лежат данные

- `public/static/` — исходники статики.
- `public/staticfiles/` — результат `collectstatic`.
- `public/media/` — загруженные файлы и служебные error-pages.
- `database/` — SQLite-файл и бэкапы.

## Основные команды

### Миграции

Локально:

```bash
docker compose -f docker-compose.local.yml exec web python manage.py migrate
```

На проде:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Django shell

```bash
docker compose -f docker-compose.local.yml exec web python manage.py shell
```

### Логи

```bash
docker compose -f docker-compose.prod.yml logs -f web
```

### Бэкап базы

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py backup_db
```

### Восстановление fixture

После `migrate` в пустую базу:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py loaddata <fixture>.json
```

## Замена старых Joomla-ссылок

Для массовой замены старых внутренних ссылок в HTML-контенте есть management command:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py replace_legacy_links
```

По умолчанию команда работает в режиме `dry-run`.

Чтобы применить изменения:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py replace_legacy_links --apply
```

Сейчас команда чинит только кросс-ссылки на статьи. Ссылки на картинки и прочие медиа пока остаются как есть.

## CodeMirror 6 в админке

Редактор админки собирается отдельно из npm-части.

Исходники и скрипт сборки лежат в `frontend-assembly/`.

Сборка:

```bash
bash ./frontend-assembly/build-codemirror6.sh
```

Результат сборки — только готовый бандл:

```text
public/static/codemirror/editor.js
```

## Заметки по развертыванию

- Главный источник правды по запуску — `docker-compose.local.yml` и `docker-compose.prod.yml`.
- Секреты не храним в репозитории: используем `.env`.


