# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from html import unescape
import pytils
import re


def check_cookies(request) -> bool:
    # проверка, что посетитель согласился со сбором данных через cookies
    if request.COOKIES.get('cookie_accept'):
        return False
    return True


def safe_html_special_symbols(s: str) -> str:
    """Преобразует HTML-фрагмент в чистый текст.

        Удаляет все HTML-теги и декодирует HTML-сущности в Unicode.

        :param s:   строка, которую надо очистить
        :return: str: чистый текст без HTML-разметки
    """
    if not s:
        return ""

    soup = BeautifulSoup(s, "html.parser")

    # Скрипты и стили в чистый текст не нужны — выкидываем их целиком.
    for tag in soup(["script", "style", "noscript", "code", "kbd", "pre"]):
        tag.decompose()

    result = soup.get_text()
    result = unescape(result).replace("\xa0", " ")
    # Убираем мягкие переносы и другие невидимые символы, которые не нужны
    # ни для slug, ни для человекочитаемого текста.
    result = result.translate({
        ord("\xad"): None,     # символ мягкого переноса
        ord("\u200b"): None,   # символ нулевой ширины (zero-width space)
        ord("\u200c"): None,   # символ нулевой ширины (zero-width non-joiner)
        ord("\u200d"): None,   # символ Zero Width Joiner (ZWJ)
        ord("\u2060"): None,   # символ Word Joiner (WJ)
        ord("\ufeff"): None,   # символ Zero Width No-Break Space (BOM)
    })
    return " ".join(result.split())


def clean_text_to_slug(s: str, default: str = "content") -> str:
    """Готовит чистый slug из HTML/Unicode текста."""
    slug = pytils.translit.slugify(safe_html_special_symbols(s).lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or default


# Удалить: HTML-постобработка была нужна только для старого типографа Муравьёва.
# После перехода на `etpgrf` можно будет убрать и этот закомментированный блок,
# и сам импорт `re`, если он больше нигде не понадобится.
#
# def post_processing_html(s: str) -> str:
#     s = re.sub(r"\s+", " ", s, flags=re.IGNORECASE)
#     s = re.sub(r">\s+|>&nbsp;", "> ", s, flags=re.IGNORECASE)
#     s = re.sub(r"\n|\r|<p[^>]*>\s*</p>|<p>&nbsp;</p>", "", s, flags=re.IGNORECASE)
#     s = re.sub(r"</p>\s*<br[^>]*>", "</p>", s, flags=re.IGNORECASE)
#     s = re.sub(r"<br[^>]*>\s*<p>|<p[^>]*>\s*<p[^>]*>", "<p>", s, flags=re.IGNORECASE)
#     s = re.sub(r"</p>\s*</p>", "</p>", s, flags=re.IGNORECASE)
#     s = re.sub(r"<br[^>]*>\s*<br[^>]*>", "<br />", s, flags=re.IGNORECASE)
#     s = re.sub(r"<p><blockquote>", "<blockquote>", s, flags=re.IGNORECASE)
#     s = re.sub(r"</blockquote></p>", "</blockquote>", s, flags=re.IGNORECASE)
#     return s
