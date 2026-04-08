"""Утилиты для поиска и замены старых Joomla-ссылок в HTML-контенте."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class LegacyLinkMatch:
    """Результат найденной старой ссылки."""

    pattern_name: str
    content_id: int
    old_url: str
    new_url: str


def _compile_legacy_pattern(name: str, route_regex: str) -> tuple[str, re.Pattern[str]]:
    """Компилирует паттерн только для внутренних ссылок CADpoint."""
    # Важно: регулярка ловит только внутренние маршруты сайта, а не внешние
    # URL и не ссылки на картинки/медиа.
    pattern = re.compile(
        rf'(?P<url>(?:^|(?<=["\'\s>]))(?:https?://(?:www\.)?cadpoint\.ru)?/?{route_regex})',
        re.IGNORECASE,
    )
    return name, pattern


LEGACY_ROUTE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    _compile_legacy_pattern('latest-news', r'(?:news/)?1-latest-news/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('newsflash', r'(?:news/)?3-newsflash/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('publication-hardware', r'publication/32-hardware/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('publication-interview', r'publication/39-interview/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('runet-cad', r'runet-cad/37-runet-cad/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('mcad', r'section-blog/28-mcad/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('video', r'video/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('privat-blog', r'blogs/35-privat-blog/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('cad-company-feeds', r'cad-company-feeds/40-cad-company-feeds/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('component-article', r'component/content/article/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('categoryblog', r'categoryblog/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('category-table', r'category-table/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
    _compile_legacy_pattern('aboutcadpoint', r'aboutcadpoint\.html/(?P<content_id>\d+)(?:-[^"\'<>\s]*)?(?:\.html)?'),
)


def build_canonical_url(content_id: int, slug: str) -> str:
    """Строит текущий канонический URL контента."""
    safe_slug = slug.strip().strip('/')
    if safe_slug:
        return f'/item/{content_id}-{safe_slug}'
    return f'/item/{content_id}-'


def replace_legacy_links(text: str, content_by_id: dict[int, str]) -> tuple[str, list[LegacyLinkMatch]]:
    """Заменяет все старые Joomla-ссылки в тексте на текущий канонический URL.

    Возвращает обновлённый текст и список найденных замен.
    """
    # По каждому шаблону делаем отдельный проход, чтобы сохранить понятную
    # диагностику: какой именно legacy-шаблон и какой `content_id` сработал.
    matches: list[LegacyLinkMatch] = []
    result = text

    for pattern_name, pattern in LEGACY_ROUTE_PATTERNS:
        def _repl(match: re.Match[str]) -> str:
            content_id = int(match.group('content_id'))
            old_url = match.group('url')
            slug = content_by_id.get(content_id, '')
            new_url = build_canonical_url(content_id, slug)
            matches.append(LegacyLinkMatch(pattern_name, content_id, old_url, new_url))
            return new_url

        result = pattern.sub(_repl, result)

    return result, matches


def iter_legacy_link_matches(text: str) -> Iterable[LegacyLinkMatch]:
    """Находит все старые ссылки в тексте без замены."""
    # Используем тот же механизм, что и при замене, но без сохранения текста.
    _, matches = replace_legacy_links(text, {})
    return matches

