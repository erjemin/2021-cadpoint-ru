# Сайт CADpoint.ru

Сайт с новостями (блог о 3D-печать и Систем Автоматизированного Проектирования) на Django со 
встроенными свистелками-перделками:
* медиа-библиотека (filer);
* WYSIWYG-редактор (ckeditor) в админке;
* типограф (по API или встроенный «типограф Муравьева», с костылями под ckeditor);
* теги новостей (taggit).

[Инструкция по развертыванию на хостинге DreamHost.com](deploy_to_dreamhost.md)

Для локальной настройки секретов используй `cadpoint/cadpoint/my_secret_example.py` как шаблон и
создавай рядом незакоммиченный `cadpoint/cadpoint/my_secret.py`.

Для логического бэкапа базы через Django используй команду:

```bash
cd cadpoint
python manage.py backup_db
```

По умолчанию файл дампа сохраняется в `database/backups/`. Восстановление делается обычной командой
`python manage.py loaddata <fixture>.json` в пустую базу после `python manage.py migrate`.

Для нового окружения на Poetry:

```bash
poetry install --with dev
poetry run python cadpoint/manage.py migrate
poetry run python cadpoint/manage.py runserver
```

