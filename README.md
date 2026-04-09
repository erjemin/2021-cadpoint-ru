# Сайт CADpoint.ru

Сайт с новостями (блог о 3D-печать и Систем Автоматизированного Проектирования) на Django со 
встроенными свистелками-перделками:
* медиа-библиотека (filer);
* HTML-редактор на обычной textarea в админке;
* типограф (по API или встроенный «типограф Муравьева»);
* теги новостей (taggit).

[Инструкция по развертыванию на хостинге DreamHost.com](deploy_to_dreamhost.md)

Для локальной и продовой настройки используй файл `.env` в корне проекта.
Шаблон для него лежит в `.env.sample`.

Набор базовых переменных:

* `DJANGO_SECRET_KEY`
* `DJANGO_DEBUG`
* `DJANGO_ALLOWED_HOSTS`
* `DJANGO_ADMINS`
* `DJANGO_CSRF_TRUSTED_ORIGINS`
* `DJANGO_INTERNAL_IPS`
* `DJANGO_SQLITE_NAME`
* `ADMIN_URL`
* `DJANGO_EMAIL_HOST`
* `DJANGO_EMAIL_PORT`
* `DJANGO_EMAIL_HOST_USER`
* `DJANGO_EMAIL_HOST_PASSWORD`
* `DJANGO_EMAIL_FROM`

Для логического бэкапа базы через Django используй команду:

```bash
cd cadpoint
python manage.py backup_db
```

По умолчанию файл дампа сохраняется в `database/backups/`. Восстановление делается обычной командой
`python manage.py loaddata <fixture>.json` в пустую базу после `python manage.py migrate`.

## Замена старых Joomla-ссылок в контенте

Для массовой замены старых внутренних ссылок в HTML-контенте используй management command:

```bash
cd cadpoint
python manage.py replace_legacy_links
```

По умолчанию команда работает в режиме `dry-run`: она только показывает, какие поля и записи
будут изменены. Чтобы записать изменения в базу, добавь флаг:

```bash
cd cadpoint
python manage.py replace_legacy_links --apply
```

Сейчас команда чинит только кросс-ссылки на статьи. Ссылки на картинки и прочие медиа пока
оставлены как есть.

Для нового окружения на Poetry:

```bash
poetry install --with dev
cp .env.sample .env
poetry run python cadpoint/manage.py migrate
poetry run python cadpoint/manage.py runserver
```

Для разработки медиа-файлы и статика лежат в `public/media` и `public/static`.
`django-debug-toolbar` показывается только при `DJANGO_DEBUG=true` и заходе с локального
адреса (`127.0.0.1` / `localhost`); если нужно, свои IP можно добавить в `DJANGO_INTERNAL_IPS`.

