"""Mass-замена старых Joomla-кросс-ссылок в HTML-контенте.

Пока команда чинит только внутренние ссылки на статьи. Ссылки на картинки и
прочие медиа остаются без изменений.
"""

from __future__ import annotations

from collections import Counter
from django.core.management.base import BaseCommand
from django.db import transaction

from web.legacy_links import iter_legacy_link_matches, replace_legacy_links
from web.models import TbContent


class Command(BaseCommand):
    help = (
        'Находит и заменяет старые Joomla-кросс-ссылки в HTML-контенте на '
        'текущие Django-URL. Ссылки на медиа пока не трогает.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Сохранить изменения в базе. Без флага команда работает в режиме dry-run.',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        # Сначала один раз собираем карту `id -> slug`, чтобы не делать лишние
        # запросы к базе в цикле по каждому контенту.
        content_by_id = dict(
            TbContent.objects.values_list('id', 'szContentSlug')
        )
        # Обрабатываем только HTML-поля, где реально встречаются старые ссылки.
        fields = ('szContentIntro', 'szContentBody', 'szContentHead')
        pattern_counter = Counter()
        updated_objects = 0
        updated_fields = 0

        for content in TbContent.objects.all().iterator():
            field_updates: dict[str, str] = {}
            object_matches = []

            for field_name in fields:
                text = getattr(content, field_name) or ''
                if not text:
                    continue
                # Быстрая проверка: если в тексте нет legacy-ссылок, не тратим
                # время на полноценную замену.
                if not any(match for match in iter_legacy_link_matches(text)):
                    continue

                new_text, matches = replace_legacy_links(text, content_by_id)
                if matches and new_text != text:
                    field_updates[field_name] = new_text
                    object_matches.extend(matches)
                    pattern_counter.update(match.pattern_name for match in matches)

            if not field_updates:
                continue

            updated_objects += 1
            updated_fields += len(field_updates)
            self.stdout.write(
                f'#{content.pk}: {len(object_matches)} замен(ы) в полях {", ".join(field_updates)}'
            )
            for match in object_matches[:5]:
                self.stdout.write(f'  - {match.pattern_name}: {match.old_url} -> {match.new_url}')
            if len(object_matches) > 5:
                self.stdout.write(f'  ... ещё {len(object_matches) - 5} замен(ы)')

            if apply_changes:
                # Записываем только те поля, которые действительно изменились.
                with transaction.atomic():
                    TbContent.objects.filter(pk=content.pk).update(**field_updates)

        self.stdout.write(self.style.SUCCESS(f'Затронуто объектов: {updated_objects}'))
        self.stdout.write(self.style.SUCCESS(f'Затронуто полей: {updated_fields}'))
        self.stdout.write(self.style.SUCCESS(f'Сводка по шаблонам: {dict(pattern_counter)}'))
        if not apply_changes:
            self.stdout.write(self.style.WARNING('Это dry-run. Для записи в БД добавь флаг --apply.'))

