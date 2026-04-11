# -*- coding: utf-8 -*-

import datetime
import logging

from django.db import models
from django.utils.timezone import now
from etpgrf import Hyphenator, Typographer
from etpgrf.config import (
    MODE_MIXED,
    MODE_MNEMONIC,
    MODE_UNICODE,
    SANITIZE_ALL_HTML,
    SANITIZE_ETPGRF,
    SANITIZE_NONE,
)
from filer.fields.image import FilerFileField
from taggit.managers import TaggableManager
from taggit.models import Tag, TaggedItem
from web.add_function import clean_text_to_slug, safe_html_special_symbols
import pytils


logger = logging.getLogger(__name__)

# Типограф настраиваем один раз на модуль: в save() он только обрабатывает строку,
# а не пересоздаётся на каждый объект контента.
_TYPOGRAPHER_LANGS = 'ru+en'
_TYPOGRAPHER_MAX_UNHYPHENATED_LEN = 14

_TYPOGRAPHER_DEFAULT_MODE = MODE_MIXED
_TYPOGRAPHER_DEFAULT_HYPHENATION = True
_TYPOGRAPHER_DEFAULT_SANITIZER = SANITIZE_NONE
_TYPOGRAPHER_DEFAULT_STRIP_SOFT_HYPHENS = True


def _normalize_typograph_mode(value: str | None) -> str:
    if value in {MODE_MIXED, MODE_UNICODE, MODE_MNEMONIC}:
        return str(value)
    return _TYPOGRAPHER_DEFAULT_MODE


def _normalize_typograph_hyphenation(value) -> bool:
    return bool(_TYPOGRAPHER_DEFAULT_HYPHENATION if value is None else value)


def _normalize_typograph_sanitizer(value):
    if value in (None, '', 'None', SANITIZE_NONE):
        return SANITIZE_NONE
    if value == SANITIZE_ALL_HTML:
        return SANITIZE_ALL_HTML
    if value == SANITIZE_ETPGRF:
        return SANITIZE_ETPGRF
    return SANITIZE_NONE


def _strip_soft_hyphens(text: str) -> str:
    """Удаляет мягкие переносы в любом виде перед передачей текста в etpgrf."""
    if not text:
        return text
    return (
        text
        .replace("&shy;", "")
        .replace("&#173;", "")
        .replace("&#xad;", "")
        .replace("\u00ad", "")
    )


def _build_typographer(mode=None, hyphenation=True, sanitizer=None, hanging_punctuation=None) -> Typographer:
    """Собирает `etpgrf` с едиными настройками для заголовка и текста."""
    normalized_mode = _normalize_typograph_mode(mode)
    normalized_hyphenation = _normalize_typograph_hyphenation(hyphenation)
    normalized_sanitizer = _normalize_typograph_sanitizer(sanitizer)
    return Typographer(
        langs=_TYPOGRAPHER_LANGS,
        mode=normalized_mode,
        process_html=True,
        hyphenation=(
            Hyphenator(
                langs=_TYPOGRAPHER_LANGS,
                max_unhyphenated_len=_TYPOGRAPHER_MAX_UNHYPHENATED_LEN,
            ) if normalized_hyphenation else False
        ),
        sanitizer=normalized_sanitizer,
        hanging_punctuation=hanging_punctuation,
    )

_TYPOGRAPHER_HEAD = _build_typographer(hanging_punctuation='left')
_TYPOGRAPHER_TEXT = _build_typographer()

def _typograph_text(text: str, typographer: Typographer) -> str:
    """Применяет `etpgrf` к HTML-фрагменту и не валит save при сбое библиотеки."""
    if not text:
        return text
    try:
        return typographer.process(text)
    except Exception:
        logger.exception("etpgrf не смог обработать текст, сохраняем исходный вариант")
        return text


# класс для транслитерации русскоязычных slug
# рецепт взят отсюда: https://timonweb.com/django/russian-slugs-for-django-taggit/
class RuTag(Tag):
    class Meta:
        proxy = True

    def slugify(self, tag, i=None):
        return pytils.translit.slugify(self.name.lower())[:128]


class RuTaggedItem(TaggedItem):
    class Meta:
        proxy = True

    @classmethod
    def tag_model(cls):
        return RuTag


class TbContent(models.Model):
    # ============================================================
    # ТАБЛИЦА TbContent (контент для всего-всего-всего)
    # ------------------------------------------------------------
    # | id                    -- id | primarykey bigint NOT NULL AUTO_INCREMENT |
    # | bContentPublish       -- признак публикации | TINYINT(1) NOT NULL ADD INDEX |
    # | tdContentPublishUp    -- начало публикации | datetime(6) NOT NULL ADD INDEX |
    # | tdContentPublishDown  -- окончание публикации | datetime(6) NULL ADD INDEX |
    # | tags                  -- теги (taggit, M2M) |
    # | szContentHead         -- заголовок | varchar(512) NOT NULL |
    # | imgContentPreview_id  -- картинка-превью (ссылка на `filer_image`) | bigint DEFAULT NULL |
    # | szContentIntro        -- анонс | longtext NOT NULL |
    # | szContentBody         -- содержание | longtext NOT NULL |
    # | szContentSlug         -- slug | varchar(128) |
    # | iContentHits          -- число просмотров | bigint/unsigned int NOT NULL ADD INDEX |
    # | szContentKeywords     -- keywords для SEO | varchar(256) |
    # | szContentDescription  -- description для SEO | varchar(256) |
    # | dtContentCreate       -- дата и время создания | datetime(6) NOT NULL |
    # | dtContentTimeStamp    -- штамп времени (время последнего обновления) | datetime(6) NOT NULL |
    #
    # Типограф и его настройки теперь живут в админке как виртуальные поля,
    # и в базе отдельно не хранятся.
    # ============================================================
    bContentPublish = models.BooleanField(
        default=True, db_index=True,
        verbose_name="Опуб…",
        help_text="Опубликованный контент будет отображаться в соответствующей ленте категории и"
                  "&nbsp;при его просмотре будет отображаться навигация &laque;Предыдущий&raque;"
                  " и&nbsp;&laque;Следующий&raque; по ленте. По прямому URL (если его знать) "
                  "отображается даже не опубликованный контент (но без навигации)."
    )
    tdContentPublishUp = models.DateTimeField(
        db_index=True,  default=now,   # datetime.date.today(),
        verbose_name="Начало публикации",
        help_text=u"Дата публикации, с её момента новость появится на сайте."
    )
    tdContentPublishDown = models.DateTimeField(
        db_index=True, null=True, blank=True,  # default=datetime.datetime(2035, 12, 31, 23, 59, 59, 0), # default=0,
        verbose_name="Окончания публикации",
        help_text=u"Дата окончания публикации, с её момента новость исчезнет с сайта."
    )
    tags = TaggableManager(
        blank=True,
        through=RuTaggedItem,   # uTaggedItem,
        verbose_name=u"Теги",
        help_text=u"Теги можно выбирать из списка или вводить вручную. Многословные теги поддерживаются"
                  u" без кавычек. <b>Теги нужны для присвоения категорий объектам контента<b>."
    )
    szContentHead = models.CharField(
        max_length=512, default=u"", blank=False, null=False,
        verbose_name="Заголовок",
        help_text="Заголовок контента <small>(допустим HTML-код, будет обработан типографом,"
                  " если его включить, максимальная длинна <b>512 символов</b>)</small>"
    )
    imgContentPreview = FilerFileField(
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="Превью",
        verbose_name="Превью",
        help_text="Картинка-превью"
    )
    szContentIntro = models.TextField(
        default="",
        verbose_name="Анонс",
        help_text="Анонс <small>(допустим HTML-код, будет обработан типографом,"
                  " если его включить)</small>"
    )
    szContentBody = models.TextField(
        default="",
        verbose_name="Содержание",
        help_text="Содержание <b>БЕЗ АНОНСА</b> <small>(допустим HTML-код, будет обработан типографом,"
                  " если его включить)</small>"
    )
    szContentSlug = models.CharField(
        default="", max_length=128, blank=True, null=True,
        verbose_name="Slug",
        help_text="Слуг… 128 символов.<br /><small><b>Если оставить"
                  " пустым, то slug сформируется автоматически</b></small>"
    )
    iContentHits = models.PositiveIntegerField(
        default=0, db_index=True,
        verbose_name="◉",
        help_text="Число просмотров"
    )
    szContentKeywords = models.CharField(
        default="", max_length=256, blank=True, null=True,
        verbose_name="Keywords (SEO)",
        help_text="Ключевые слова. Через запятую. 256 символов."
    )
    szContentDescription = models.CharField(
        default="", max_length=256, blank=True, null=True,
        verbose_name="Description (SEO)",
        help_text="Описание страницы… 256 символов (включая пробелы), но поисковики обработают только 155–160"
                  " из них.<br /><small><b>Если оставить пустым, то описание сформируется автоматически"
                  " на базе заголовка и анонса</b></small>"
    )
    dtContentCreate = models.DateTimeField(
        auto_now_add=True,     # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после она не нужна
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name="Дата Создания"
    )
    dtContentTimeStamp = models.DateTimeField(
        auto_now=True,           # надо указать False при миграции, после вернуть в True
        # для выполнения миграций нужно добавлять default, а после она не нужна
        # default=datetime.datetime.now(pytz.timezone(settings.TIME_ZONE)),
        verbose_name="Штамп времени"
    )

    def __unicode__(self):
        return u"%03d: %s" % (self.id,
                              self.szContentHead[:30] + "…" if len(self.szContentHead) > 30 else self.szContentHead)

    def __str__(self):
        result = safe_html_special_symbols(self.szContentHead)
        return u"%03d: %s" % (self.id, result[:50] + "…" if len(result) > 50 else result)

    def save(self, *args, **kwargs):
        # Переопределяем save(), чтобы автоматически типографировать контент перед сохранением.
        typograph_enabled = getattr(self, '_typograph_enabled', False)
        typograph_mode = getattr(self, '_typograph_mode', _TYPOGRAPHER_DEFAULT_MODE)
        typograph_hyphenation = getattr(self, '_typograph_hyphenation', _TYPOGRAPHER_DEFAULT_HYPHENATION)
        typograph_sanitizer = getattr(self, '_typograph_sanitizer', _TYPOGRAPHER_DEFAULT_SANITIZER)
        typograph_strip_soft_hyphens = getattr(
            self,
            '_typograph_strip_soft_hyphens',
            _TYPOGRAPHER_DEFAULT_STRIP_SOFT_HYPHENS,
        )
        if self.szContentSlug is None or self.szContentSlug == "" or " " in self.szContentSlug:
            # print("ку-ку", self.szContentHead)
            base_slug = clean_text_to_slug(self.szContentHead)
            result_slug = base_slug
            suffix = 1
            while TbContent.objects.filter(szContentSlug=result_slug).exists():
                result_slug = f"{base_slug}-{suffix}"
                suffix += 1
            self.szContentSlug = result_slug
        if typograph_enabled:
            # `etpgrf` уже умеет HTML-режим и висячую пунктуацию, поэтому здесь
            # не нужен старый локальный fallback.
            # Мягкие переносы убираем заранее: `etpgrf` не очищает их сам, а они
            # потом мешают и типографу, и последующей нормализации текста.
            # Для заголовка включаем левую висячую пунктуацию, а для анонса и
            # тела текста оставляем обычную обработку без hanging punctuation.
            if typograph_strip_soft_hyphens:
                self.szContentHead = _strip_soft_hyphens(self.szContentHead)
                self.szContentIntro = _strip_soft_hyphens(self.szContentIntro)
                self.szContentBody = _strip_soft_hyphens(self.szContentBody)
            head_typographer = _build_typographer(
                mode=typograph_mode,
                hyphenation=typograph_hyphenation,
                sanitizer=typograph_sanitizer,
                hanging_punctuation='left',
            )
            text_typographer = _build_typographer(
                mode=typograph_mode,
                hyphenation=typograph_hyphenation,
                sanitizer=typograph_sanitizer,
                hanging_punctuation=False,
            )
            self.szContentHead = _typograph_text(self.szContentHead, head_typographer)
            self.szContentIntro = _typograph_text(self.szContentIntro, text_typographer)
            self.szContentBody = _typograph_text(self.szContentBody, text_typographer)
        if self.dtContentCreate is None:
            self.dtContentCreate = datetime.datetime.now()
        super(TbContent, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Контент"
        verbose_name_plural = u"Контент"
        # Чтобы боковая навигация или лента нне упиралась в SQLite и работала быстро,
        # добавляем составные индексы.
        indexes = [
            models.Index(fields=['bContentPublish', 'tdContentPublishUp']),
            models.Index(fields=['bContentPublish', 'tdContentPublishDown']),
        ]
        ordering = ['-tdContentPublishUp', ]
