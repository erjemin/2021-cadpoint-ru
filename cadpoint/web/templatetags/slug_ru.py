# -*- coding: utf-8 -*-
from django import template
from web.add_function import safe_html_special_symbols
import pytils

register = template.Library()


@register.filter
def slug_ru(value: str, arg: int) -> str:
    try:
        arg = int(arg)
        return pytils.translit.slugify(str(value).lower())[:int(arg)]
    except ValueError:
        return pytils.translit.slugify(str(value).lower())


@register.filter
def safe_html_ss(value: str) -> str:
    return safe_html_special_symbols(value)
