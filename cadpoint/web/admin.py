# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.urls import reverse
from django_select2.forms import Select2TagWidget
from etpgrf.config import MODE_MIXED, MODE_MNEMONIC, MODE_UNICODE, SANITIZE_ALL_HTML, SANITIZE_ETPGRF
from web.models import TbContent
from web.add_function import safe_html_special_symbols
from cadpoint import settings


TYPOGRAPH_MODE_CHOICES = [
    (MODE_MIXED, 'Смешанный (Mixed)'),
    (MODE_UNICODE, 'Юникод (Unicode)'),
    (MODE_MNEMONIC, 'Мнемоники'),
]

TYPOGRAPH_SANITIZER_CHOICES = [
    (SANITIZE_ALL_HTML, 'Очистка от HTML на входе'),
    (SANITIZE_ETPGRF, 'Очистка висячей пунктуации'),
    ('None', 'Без очистки'),
]


class AjaxCommaSeparatedSelect2TagWidget(Select2TagWidget):
    """
    Select2-виджет для `taggit`.

    Select2 в браузере работает с массивом значений, а `taggit` ждёт строку
    с тегами через запятую. Поэтому здесь есть конвертация туда и обратно.
    """

    def value_from_datadict(self, data, files, name):
        # Select2 присылает список значений, а `taggit` ожидает строку вида
        # "tag-one,tag two,tag-three".
        values = super().value_from_datadict(data, files, name)
        if isinstance(values, (list, tuple)):
            return ",".join(values)
        return values

    def optgroups(self, name, value, attrs=None):
        # При редактировании объекта нужно показать уже выбранные теги.
        # При этом не тащим ВСЕ теги из базы — только те, что уже сохранены.
        if isinstance(value, (list, tuple)):
            raw_values = []
            for item in value:
                if not item:
                    continue
                raw_values.extend(str(item).split(","))
        else:
            raw_values = str(value or "").split(",")

        values = [item for item in raw_values if item]
        selected = set(values)
        subgroup = [
            self.create_option(name, v, v, v in selected, i)
            for i, v in enumerate(values)
        ]
        return [(None, subgroup, 0)]


class AdminContentForm(forms.ModelForm):
    typograph_enabled = forms.BooleanField(
        label='Типограф etpgrf вкл.',
        required=False,
        initial=True,
        help_text="Обработать через <a href=\"https://typograph.cube2.ru/\""
                  " target=\"_blank\">Типограф ETPRGF</a><br />"
                  "<small><u>СТАБИЛЬНЫЙ И СОВРЕМЕННЫЙ ТИПОГРАФ, РЕКОМЕНДУЕМ</u><br />"
                  "&laquo;приклеивает&raquo; союзы и предлоги, поддерживает неразрывные конструкции, "
                  "замена тире, кавычек и дефисов, расстановка &laquo;мягких переносов&raquo; "
                  "в словах длиннее 14 символов, <!-- убирает &laquo;вдовы&raquo; &laquo;сироты&raquo; (кроме "
                  "заголовков), расставляет абзацы (кроме заголовков), расшифровывает "
                  "аббревиатуры (те, что знает и кроме заголовков), --> висячая "
                  "пунктуация (только в заголовках) и т.п.</small>"
    )
    typograph_strip_soft_hyphens = forms.BooleanField(
        label='Удалять переносы',
        required=False,
        initial=True,
        help_text='Убирает `&amp;shy;`, `&amp;#173;` и Unicode-символ мягкого переноса<br />'
                  'перед типографом.',
    )
    typograph_mode = forms.ChoiceField(
        label='Режим вывода',
        choices=TYPOGRAPH_MODE_CHOICES,
        initial=MODE_MIXED,
    )
    typograph_hyphenation = forms.BooleanField(
        label='Расстановка переносов',
        required=False,
        initial=True,
    )
    typograph_sanitizer = forms.ChoiceField(
        label='Санитайзинг',
        choices=TYPOGRAPH_SANITIZER_CHOICES,
        initial='None',
    )

    class Meta:
        model = TbContent
        fields = '__all__'

    class Media:
        js = ('codemirror/editor.js',)
        css = {
            'all': ('css/admin-select2-theme.css',),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # AJAX-виджет подгружает список тегов лениво, а здесь мы оставляем
        # только уже выбранные значения, чтобы не тащить все теги из базы при
        # открытии формы и не провоцировать лишние запросы к SQLite.
        if self.is_bound:
            if hasattr(self.data, 'getlist'):
                tag_values = self.data.getlist('tags')
            else:
                raw_values = self.data.get('tags', [])
                tag_values = raw_values if isinstance(raw_values, list) else [raw_values]
            tag_choices = [(value, value) for value in tag_values if value]
        elif self.instance.pk:
            tag_choices = [
                (name, name)
                for name in self.instance.tags.order_by('name').values_list('name', flat=True)
            ]
        else:
            tag_choices = []

        codemirror_attrs = {
            'data-codemirror-editor': '1',
            'data-language': 'html',
        }

        self.fields['szContentHead'].widget = Textarea(attrs={
            'rows': 4,
            'cols': 120,
            **codemirror_attrs,
        })

        for field_name in ('szContentHead', 'szContentIntro', 'szContentBody'):
            self.fields[field_name].widget.attrs.update(codemirror_attrs)

        self.fields['tags'].widget = AjaxCommaSeparatedSelect2TagWidget(
            attrs={
                'data-ajax--url': reverse('web_tag_autocomplete'),
                'data-ajax--cache': 'true',
                'data-ajax--data-type': 'json',
                'data-ajax--delay': settings.SELECT2_AJAX_DELAY_MS,
                'data-token-separators': settings.SELECT2_TOKEN_SEPARATORS,
                'data-minimum-input-length': settings.SELECT2_MINIMUM_INPUT_LENGTH,
            },
            choices=tag_choices,
        )


# Register your models here.
class AdminContent(admin.ModelAdmin):
    form = AdminContentForm
    search_fields = ['szContentHead', 'szContentIntro', 'szContentBody',
                     'szContentKeywords', 'szContentDescription']
    list_display = ('id', 'ContentHeadSafe', 'tag_list', 'bContentPublish', 'tdContentPublishUp')
    list_display_links = ('id', 'ContentHeadSafe')
    list_filter = ('bContentPublish', )
    list_editable = ('bContentPublish', )
    # настройка длины поля TextInput в админке
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '100%'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 14, 'cols': 120})},
    }
    # Настройка страницы редактирования
    fieldsets = [
        (None, {
            'fields': ('bContentPublish', 'tdContentPublishUp')
        }),
        ('Окончание публикации', {
            'fields': ('tdContentPublishDown',),
            'classes': ('collapse',),
        }),
        (None, {
            'fields': ('tags', 'szContentHead', 'imgContentPreview', 'szContentIntro', 'szContentBody')
        }),
        ('Типограф', {
            'fields': (
                ('typograph_enabled', ),
                ('typograph_mode', 'typograph_sanitizer', ),
                ('typograph_strip_soft_hyphens', 'typograph_hyphenation', ),
            ),
            'classes': ('collapse',),
        }),
        ('Поля для SEO', {
            'fields': ('szContentSlug', 'szContentKeywords', 'szContentDescription', 'iContentHits'),
            'classes': ('collapse', ),
        }),
    ]
    # exclude = ('', '', )
    empty_value_display = u"<b style='color:red;'>—//—</b>"
    actions_on_top = False
    actions_on_bottom = False

    def save_model(self, request, obj, form, change):
        obj._typograph_enabled = form.cleaned_data.get('typograph_enabled', False)
        obj._typograph_strip_soft_hyphens = form.cleaned_data.get('typograph_strip_soft_hyphens', True)
        obj._typograph_mode = form.cleaned_data.get('typograph_mode', MODE_MIXED)
        obj._typograph_hyphenation = form.cleaned_data.get('typograph_hyphenation', True)
        obj._typograph_sanitizer = form.cleaned_data.get('typograph_sanitizer', 'None')
        super().save_model(request, obj, form, change)

    def ContentHeadSafe(self, obj) -> str:
        return safe_html_special_symbols(obj.szContentHead)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.resolver_match and request.resolver_match.url_name == 'web_tbcontent_changelist':
            return queryset.prefetch_related('tags')
        return queryset

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


admin.site.register(TbContent, AdminContent)
