"""cadpoint URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.conf.urls.static import static
from django.urls import path, include, re_path
from cadpoint import settings
from web import views
from web.sitemaps import CadpointSitemap

urlpatterns = [
    path(
        settings.ADMIN_URL + 'tags/autocomplete/',
        admin.site.admin_view(views.tag_autocomplete),
        name='web_tag_autocomplete',
    ),
    path(settings.ADMIN_URL, admin.site.urls),
    re_path(r'^$', views.index),
    re_path(r'^p(?P<ppage>\d*)$', views.index),
    re_path(r'^tag_(?P<slug_tags>[^/]*)$', views.index),
    re_path(r'^tag_(?P<slug_tags>[^/]*)[^/]*/p(?P<ppage>\d*)$', views.index),
    re_path(r'^alltags$', views.alltags, name='web_alltags'),
    # Статья
    re_path(r'^item/(?P<content_id>\d*)-\S*$', views.show_item),
    # После чистки кросс-ссылок в контенте legacy Joomla-редиректы временно
    # отключаем, но код оставляем в файле как быстрый архивный reference.
    # Если понадобится откат, достаточно раскомментировать блок ниже.
    # re_path(r'^publication/32-hardware/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^publication/39-interview/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^news/3-newsflash/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^news/1-latest-news/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^runet-cad/37-runet-cad/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^section-blog/28-mcad/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^video/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^blogs/35-privat-blog/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^cad-company-feeds/40-cad-company-feeds/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^component/content/article/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^categoryblog/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^category-table/(?P<content_id>\d*)-\S*$', views.redirect_item),
    # re_path(r'^aboutcadpoint.html/(?P<content_id>\d*)-\S*$', views.redirect_item),

    path('sitemap.xml', sitemap_view, {'sitemaps': {'cadpoint': CadpointSitemap}}, name='web_sitemap'),

]

handler404 = 'web.views.handler404'
handler400 = 'web.views.handler400'
handler403 = 'web.views.handler403'
handler500 = 'web.views.handler500'

if settings.DEBUG:
    import mimetypes
    import debug_toolbar
    from django.views.static import serve

    def _serve_public_root_file(request, path):
        """Отдаёт файлы из корня `public` в dev-режиме в utf-8."""
        response = serve(request, path, document_root=settings.PUBLIC_DIR)
        content_type, _ = mimetypes.guess_type(path)
        if content_type:
            if content_type.startswith('text/'):
                response['Content-Type'] = f'{content_type}; charset=utf-8'
            else:
                response['Content-Type'] = content_type
        elif path.endswith('.txt'):
            response['Content-Type'] = 'text/plain; charset=utf-8'
        elif path.endswith('.html'):
            response['Content-Type'] = 'text/html; charset=utf-8'
        return response

    def _iter_public_root_files():
        """Находит все обычные файлы в корне `public`, кроме служебных артефактов."""
        for file_path in sorted(settings.PUBLIC_DIR.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.name.startswith('.'):
                continue
            if file_path.name == 'README.md':
                continue
            yield file_path.name

    PUBLIC_ROOT_URLPATTERNS = [
        path(filename, _serve_public_root_file, {'path': filename})
        for filename in _iter_public_root_files()
    ]

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), ] + urlpatterns
    urlpatterns = [*PUBLIC_ROOT_URLPATTERNS, *urlpatterns]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.PUBLIC_DIR.joinpath('static'))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
