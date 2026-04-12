from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from taggit.models import Tag

from web.models import TbContent


class CadpointSitemap(Sitemap):
    """Одна карта сайта для публичных страниц CADpoint."""

    changefreq = 'weekly'

    def items(self):
        now_value = timezone.now()
        content_items = list(
            TbContent.objects.filter(
                bContentPublish=True,
                tdContentPublishUp__lte=now_value,
            ).filter(
                Q(tdContentPublishDown__isnull=True) | Q(tdContentPublishDown__gt=now_value)
            ).order_by('-tdContentPublishUp', 'id')
        )
        latest_content = content_items[0].dtContentTimeStamp if content_items else None

        sitemap_items = [
            {'kind': 'home', 'lastmod': latest_content},
            {'kind': 'alltags', 'lastmod': latest_content},
        ]

        tags = Tag.objects.filter(taggit_taggeditem_items__isnull=False).distinct().order_by('name')
        sitemap_items.extend({'kind': 'tag', 'tag': tag} for tag in tags)
        sitemap_items.extend({'kind': 'item', 'item': item} for item in content_items)
        return sitemap_items

    def location(self, item):
        kind = item['kind']
        if kind == 'home':
            return '/'
        if kind == 'alltags':
            return reverse('web_alltags')
        if kind == 'tag':
            return f"/tag_{item['tag'].slug}"
        return f"/item/{item['item'].id}-{item['item'].szContentSlug}"

    def lastmod(self, item):
        kind = item['kind']
        if kind in {'home', 'alltags'}:
            return item.get('lastmod')
        if kind == 'item':
            return item['item'].dtContentTimeStamp
        return None

    def priority(self, item):
        kind = item['kind']
        if kind == 'home':
            return 1.0
        if kind == 'alltags':
            return 0.6
        if kind == 'tag':
            return 0.5
        return 0.8

