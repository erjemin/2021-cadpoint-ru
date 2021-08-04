# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from web.models import TbContent
from web.add_function import safe_html_special_symbols


# Register your models here.
class AdminContent(admin.ModelAdmin):
    search_fields = ['szContentHead', 'szContentIntro', 'szContentBody',
                     'szContentKeywords', 'szContentDescription']
    list_display = ('id', 'ContentHeadSafe', 'tag_list', 'bContentPublish', 'tdContentPublishUp')
    list_display_links = ('id', 'ContentHeadSafe')
    list_filter = ('bContentPublish', )
    list_editable = ('bContentPublish', )
    # настройка длины поля TextInput в админке
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '100%'})},
        # models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }
    # Настройка страницы редактирования
    fieldsets = [
        (None, {
            'fields': ('bContentPublish', 'tdContentPublishUp', 'tdContentPublishDown', 'tags',
                       'szContentHead', 'imgContentPreview', 'szContentIntro',
                       'szContentBody')
        }),
        ('Типограф', {
            'fields': ('bTypograf', ),
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

    def ContentHeadSafe(self, obj) -> str:
        return safe_html_special_symbols(obj.szContentHead)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())


admin.site.register(TbContent, AdminContent)
