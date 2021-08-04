# -*- coding: utf-8 -*-

from django.db import models
from django.utils.timezone import now
from filer.fields.image import FilerFileField
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager
from taggit.models import Tag, TaggedItem

import web.models
from web.add_function import safe_html_special_symbols
import urllib3
import pytils
import random
import datetime


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


# Create your models here.
class TbContent(models.Model):
    # ============================================================
    # ТАБЛИЦА TbContent (контент для всего-всего-всего)
    # ------------------------------------------------------------
    # | id                    -- id | primarykey bigint NOT NULL AUTO_INCREMENT |
    # | kCategory_id          -- категория (ссылка на таблицу TbCategory) | bigint DEFAULT NULL,
    # | bContentPublish       -- имя файла | TINYINT(1) NOT NULL ADD INDEX |
    # | tdContentPublishStart -- начало публикации | date NOT NULL ADD INDEX |
    # | szContentHead         -- заголовок | varchar(512) NOT NULL |
    # | imgContentPreview_id  -- картинка превью (ссылка на таблицу filer_image) | bigint DEFAULT NULL ADD INDEX
    # | szContentAnno         -- анонс | longtext NOT NULL,
    # | szContentBody         -- содержание | longtext NOT NULL,
    # | bTypografS            -- включить типограф Typograf 2.0  | tinyint(1) NOT NULL,
    # | szContentTitle        -- title для SEO | longtext NOT NULL,
    # | szContentKeywords     -- keywords для SEO  | longtext NOT NULL,
    # | szContentDescription  -- Description для SEO | longtext NOT NULL,
    # | dtContentCreate       --  дата и время создания | datetime(6) NOT NULL,
    # | dtContentTimeStamp    -- штамп времени (время последнего обновления в базе) | datetime(6) NOT NULL
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
        db_index=True, null=True, blank=True, # default=datetime.datetime(2035, 12, 31, 23, 59, 59, 0), # default=0,
        verbose_name="Окончания публикации",
        help_text=u"Дата окончания публикации, с её момента новость исчезнет с сайта."
    )
    tags = TaggableManager(
        blank=True,
        through=RuTaggedItem,   # uTaggedItem,
        verbose_name=u"Теги",
        help_text=u"Теги через запятую… Регистр не чувствителен… Длинные теги, содержащие пробел, заключайте"
                  u"'в кавычки'… <b>Теги нужны для присвоения категорий объектам контента<b>."
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
    szContentIntro = RichTextField(
        config_name='fine',
        default="",
        verbose_name="Анонс",
        help_text="Анонс <small>(допустим HTML-код, будет обработан типографом,"
                  " если его включить)</small>"
    )
    szContentBody = RichTextField(
        config_name='fine',
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
    bTypograf = models.BooleanField(
        default=False,
        verbose_name="Типограф Стандарт",
        help_text="Обработать через <a href=\"https://www.typograf.ru\""
                  " target=\"_blank\">Типограф 2.0</a><br />"
                  "<small><b>НОРМАЛЬНЫЙ ТИПОГРАФ, ХОРОШИЙ HTML, РЕКОМЕНДУЕМ</b> "
                  "&laquo;приклеивает&raquo; союзы, поддерживает неразрывные конструкции, "
                  "замена тире, кавычек и дефисов, расстановка &laquo;мягких переносов&raquo; "
                  "в словах длиннее 12 символов, убирает &laquo;вдовы&raquo; &laquo;сироты&raquo; (кроме "
                  "заголовков), расставляет абзацы (кроме заголовков), расшифровывает "
                  "аббревиатуры (те, что знает и кроме заголовков), висячая "
                  "пунктуация (только в заголовках) и т.п.</small>"
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
        # переопределяем метод save() чтобы "проверуть" тексты через типографы...
        if self.szContentSlug is None or self.szContentSlug == "" or " " in self.szContentSlug:
            print("ку-ку", self.szContentHead)
            result_slug = pytils.translit.slugify(
                safe_html_special_symbols(self.szContentHead)).lower()
            while TbContent.objects.filter(szContentSlug=result_slug).count() != 0:
                result_slug = "%s-%x" % (result_slug[0: -3], int(random.uniform(0, 255)))
            self.szContentSlug = result_slug
        if self.bTypograf:
            # Используем типограф Eugene Spearance (https://www.typograf.ru) через API
            # Настройки стиля типографики см. тут: https://www.typograf.ru/webservice/about/
            try:
                http = urllib3.PoolManager()
                resp = http.request("POST", "https://www.typograf.ru/webservice/",
                                    fields={"text": self.szContentHead.encode('cp1251'),
                                            'xml': '<?xml version="1.0" encoding="windows-1251" ?>'
                                                   '<preferences>'
                                                   '	<!-- Абзацы НЕ СТАВИМ-->'
                                                   '	<paragraph insert="0" />'
                                                   '    <!-- Переводы строк НЕ СТАВИМ -->'
                                                   '	<newline insert="0" />'
                                                   '	<!-- Неразрывные конструкции ДА -->'
                                                   '	<hanging-punct insert="1" />'
                                                   '	<!-- Переносы слов длиннее 12 знаков -->'
                                                   '	<hyphen insert="1" length="12" />'
                                                   '</preferences>'.encode('cp1251')})
                result = resp.data.decode('cp1251')
                if len(result) <= 512:
                    self.szContentHead = result
                resp = http.request("POST", "https://www.typograf.ru/webservice/",
                                    fields={"text": self.szContentIntro.encode('cp1251'),
                                            'xml': '<?xml version="1.0" encoding="windows-1251" ?>'
                                                   '<preferences>'
                                                   '    <!-- Висячая пунктуация УДАЛЯЕТСЯ -->'
                                                   '	<hanging-punct insert="1" />'
                                                   '	<!-- Висячие слова УДАЛЯЕМ -->'
                                                   '	<hanging-line delete="1" />'
                                                   '	<!-- Переносы  слов длиннее 12 знаков -->'
                                                   '	<hyphen insert="1" length="12" />'
                                                   '    <!-- Параметры ссылок -->'
                                                   '	<link target="_blank" />'
                                                   '</preferences>'.encode('cp1251')})
                self.szContentIntro = resp.data.decode('cp1251')
                resp = http.request("POST", "https://www.typograf.ru/webservice/",
                                    fields={"text": self.szContentBody.encode('cp1251'),
                                            'xml': '<?xml version="1.0" encoding="windows-1251" ?>'
                                                   '<preferences>'
                                                   '    <!-- Висячая пунктуация УДАЛЯЕТСЯ -->'
                                                   '	<hanging-punct insert="1" />'
                                                   '	<!-- Висячие слова УДАЛЯЕМ -->'
                                                   '	<hanging-line delete="1" />'
                                                   '	<!-- Переносы  слов длиннее 10 знаков -->'
                                                   '	<hyphen insert="1" length="12" />'
                                                   '    <!-- Параметры ссылок -->'
                                                   '	<link target="_blank" />'
                                                   '</preferences>'.encode('cp1251')})
                self.szContentBody = resp.data.decode('cp1251')
                self.bTypograf = False
            except:
                self.bTypograf = False

        super(TbContent, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Контент"
        verbose_name_plural = u"Контент"
        ordering = ['-tdContentPublishUp', ]
