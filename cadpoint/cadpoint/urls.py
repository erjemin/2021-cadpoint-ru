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
from django.conf.urls.static import static
from django.urls import path, include, re_path
from cadpoint import settings
from web import views

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

    re_path(r'^sitemap.xml$', views.sitemap),

]

handler404 = 'web.views.handler404'
handler500 = 'web.views.handler500'

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
