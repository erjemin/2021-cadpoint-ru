# -*- coding: utf-8 -*-
import math

from django.shortcuts import render, HttpResponseRedirect
from django.http import Http404
from django.db.models import Count, Q
# from datetime import datetime
from django.utils import timezone
from taggit.models import Tag

from web.models import TbContent
from web.add_function import *

# Create your views here.
def handler404(request, exception: str):
    """ Обработчик ошибки 404

        :param request:     http-запрос
        :param exception:   сообщение с причиной ошибки
        :return:  response: http-ответ
        """
    response = render(request, "404.html", {"MSG": exception})
    response.status_code = 404
    return response


def handler500(request):
    """ Обработчик ошибки 500

    :param request:
    :return:  response:
    """
    response = render(request, "500.html", {})
    response.status_code = 500
    return response


def index(request,
          slug_tags: str = "",
          ppage: int = 0):
    """ Главная страница

    :param request:
    :param ppage:      текущая страница ленты
    :param slug_tags:      текущие slug-таги, разделитель "_" (в формате tag-1_tag-2_tag-eshe-odin
    :return:  response:
    """
    template = "index.jinja2"  # шаблон
    to_template: dict[str, object] = {"COOKIES": check_cookies(request)}
    page_number = max(int(ppage), 0)
    now_value = timezone.now()

    # Базовый набор публикаций, который одинаково работает и в SQLite, и в MySQL/MariaDB.
    content_qs = TbContent.objects.filter(
        bContentPublish=True,
        tdContentPublishUp__lte=now_value,
    ).filter(
        Q(tdContentPublishDown__isnull=True) | Q(tdContentPublishDown__gt=now_value)
    )

    if slug_tags == "":
        selected_tags: list[str] = []
    else:
        selected_tags = slug_tags.split("_")
        if sorted(selected_tags) != selected_tags:
            # Список тегов должен быть отсортированным для канонического URL.
            return HttpResponseRedirect("tag_%s" % "_".join(sorted(selected_tags)))
        content_qs = content_qs.filter(tags__slug__in=selected_tags).distinct()
        to_template["TAGS_S"] = "/tag_" + slug_tags
        to_template["TAGS_L"] = selected_tags

    q_content = content_qs.order_by("-tdContentPublishUp")
    total_items = q_content.count()
    total_page = max(math.ceil(total_items / 7) - 1, 0) if total_items else 0

    q_content = q_content[page_number * 7: page_number * 7 + 7]

    # Готовим облако тегов: общее число публикаций по каждому тегу и число публикаций на текущей странице.
    page_ids = list(q_content.values_list("id", flat=True))
    q_tags = (
        Tag.objects.annotate(
            NumTotal=Count("taggit_taggeditem_items", distinct=True),
            NumInPage=Count(
                "taggit_taggeditem_items",
                filter=Q(taggit_taggeditem_items__object_id__in=page_ids),
                distinct=True,
            ),
        )
        .filter(NumTotal__gt=0)
        .order_by("-NumInPage", "-NumTotal", "name")[:20]
    )

    to_template["LENTA"] = q_content
    to_template["TAGS_IN_PAGE"] = q_tags
    to_template["PAGE_OF_LIST"] = page_number
    to_template["TOTAL_PAGE"] = total_page
    return render(request, template, to_template)


def redirect_item(request,
                  content_id: int = 0):
    """ Переадресация URL для обеспечения переходов из поисковиков по уже проиндексированным страницам

        :param request:
        :param point:      str_id блока, в которой находится контент
        :param item:       str_id страницы/категории, в которой находится контент
        :param content_id: id контента которую надо отобразить
        :return: response:
    """
    return HttpResponseRedirect("/item/%d-" % int(content_id))


def show_item(request,
              content_id: int = 0,
              ppage: int = 0):
    """ Формирование "ленты" о предприятии

        :param request:
        :param content_id: id контента которую надо отобразить
        :return: response:
    """
    template = "item.jinja2"  # шаблон
    to_template: dict[str, object] = {"COOKIES": check_cookies(request)}
    try:
        q_item = TbContent.objects.filter(id=int(content_id)).first()
        if q_item is None:
            raise Http404("Контента с таким id не существует")
        if not q_item.bContentPublish:
            raise Http404("Контент не опубликован")
        to_template["ITEM"] = q_item
        # query = Q(tdContentPublishDown__isnull=True)
        # query.add(Q(tdContentPublishDown__gt=timezone.now()), Q.OR)
        # query.add(Q(bContentPublish=True), Q.AND)
        # query.add(Q(tdContentPublishUp__lte=q_item.tdContentPublishUp), Q.AND)
        q_items_after = TbContent.objects.filter(
            Q(tdContentPublishDown__isnull=True)  | Q(tdContentPublishDown__gt=timezone.now()),
            Q(bContentPublish=True),
            Q(tdContentPublishUp__lte=q_item.tdContentPublishUp)
        ).order_by("-tdContentPublishUp", "id")[:4]
        q_items_before = TbContent.objects.filter(
            Q(tdContentPublishDown__isnull=True) | Q(tdContentPublishDown__gt=timezone.now()),
            bContentPublish=True,
            tdContentPublishUp__gt=q_item.tdContentPublishUp
        ).order_by("tdContentPublishUp", "id")[:3]
        try:
            p = 0 if "p" not in request.GET else int(request.GET["p"])
            n = 0 if "n" not in request.GET else int(request.GET["n"])
            count = 0
            for i in q_items_before:
                count += 1
                if n-count < 1:
                    i.pp = p - 1
                    i.nn = n + 7 - count
                else:
                    i.pp = p
                    i.nn = n - count
            count = 0
            for i in q_items_after:
                if i.id != q_item.id:
                    count += 1
                    if n+count <= 7:
                        i.pp = p
                        i.nn = n + count
                    else:
                        i.pp = p + 1
                        i.nn = n+count - 7
            to_template["PER_PAGE"] = 7
            to_template["PAGE"] = p
        except ValueError:
            to_template["PAGE"] = 0
            pass
        to_template["PAGE_OF_LIST"] = int(ppage)
        to_template["ITEMS_AFTER"] = q_items_after
        to_template["ITEMS_BEFORE"] = q_items_before
        q_item.iContentHits += 1
        q_item.save(update_fields=["iContentHits"])
        return render(request, template, to_template)
    except (ValueError, AttributeError, TbContent.DoesNotExist, TbContent.MultipleObjectsReturned):
        raise Http404("Контента с таким id не существует")


def sitemap(request):
    template = "sitemap.jinja2"  # шаблон
    q_items = TbContent.objects.filter(
        bContentPublish=True,
        tdContentPublishUp__lte=timezone.now(),
    ).filter(
        Q(tdContentPublishDown__isnull=True) | Q(tdContentPublishDown__gt=timezone.now())
    ).order_by("-tdContentPublishUp", "id").all()
    to_template: dict[str, object] = {"ITEMS": q_items}
    print(q_items)
    response = render(request, template, to_template)
    return response
