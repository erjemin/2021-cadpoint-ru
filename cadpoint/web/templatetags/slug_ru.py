# -*- coding: utf-8 -*-
from django import template
from web.add_function import clean_text_to_slug, safe_html_special_symbols

register = template.Library()


@register.filter
def slug_ru(value: str, arg: int) -> str:
    """ ДЕЛАЕТ СЛАГ (slug) ИЗ РУССКОЯЗЫЧНОЙ СТРОКИ

            :param value:       получает русскоязычную (любую) строку
            :param arg:         сколько символов оставить (остальные обрежет)
            :return: value:     возвращает слугофицированную строку в нижнем регистре
    """
    try:
        arg = int(arg)
        return clean_text_to_slug(str(value))[:int(arg)]
    except ValueError:
        return clean_text_to_slug(str(value))


@register.filter
def safe_html_ss(value: str) -> str:
    return safe_html_special_symbols(value)


@register.filter
def rm_tag(value: str, arg: str = "") -> str:
    """ УДАЛЯТЕЛЬ ТЕГОВ

        :param value:       получает строку типа "/tag_slug-1_slug-2_slug-A_slug-NN" (разделитель "_")
        :param arg:         слаг (slug) тега, который надо удалить, например "slug-2"
        :return: value:     возвращает строку "/tag_slug-1_slug-A_slug-NN"
    """
    value = value.replace(arg, "")
    value = value.replace("__", "_")
    if value == "/tag_":
        return "/"
    if value[-1] == "_":
        return value[0:-1]
    return value
