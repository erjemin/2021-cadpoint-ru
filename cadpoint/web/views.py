# -*- coding: utf-8 -*-
import math

from django.shortcuts import render, HttpResponseRedirect
from django.http import Http404, JsonResponse
from django.db.models import Count, F, Q
from django.views.decorators.http import require_GET
# from datetime import datetime
from django.utils import timezone
from taggit.models import Tag

from web.models import TbContent
from web.add_function import *
from cadpoint import settings

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


@require_GET
def tag_autocomplete(request):
    """Отдаёт теги для Select2 лениво, чтобы не грузить всю таблицу сразу."""
    term = request.GET.get("term", "").strip()
    page = max(int(request.GET.get("page", 1)), 1)
    page_size = settings.SELECT2_PAGE_SIZE
    queryset = Tag.objects.order_by("name")

    if term:
        queryset = queryset.filter(name__icontains=term)

    start = (page - 1) * page_size
    stop = start + page_size + 1
    names = list(queryset.values_list("name", flat=True)[start:stop])
    more = len(names) > page_size

    results = [
        {"id": name, "text": name}
        for name in names[:page_size]
    ]
    return JsonResponse({"results": results, "pagination": {"more": more}})


@require_GET
def alltags(request):
    """Показывает все теги сайта и число их вхождений во всех публикациях."""
    template = "alltags.jinja2"
    to_template: dict[str, object] = {"COOKIES": check_cookies(request)}

    q_tags = (
        Tag.objects.annotate(
            NumTotal=Count("taggit_taggeditem_items", distinct=True),
        )
        .filter(NumTotal__gt=0)
        .order_by("-NumTotal", "name")
    )

    to_template["TAGS_IN_PAGE"] = q_tags
    return render(request, template, to_template)


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
    empty_state_title = ""
    empty_state_message = ""
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
        to_template["SELECTED_TAGS"] = Tag.objects.filter(slug__in=selected_tags).order_by("slug")
        to_template["TAGS_S"] = "/tag_" + slug_tags
        to_template["TAGS_L"] = selected_tags

    q_content = content_qs.order_by("-tdContentPublishUp")
    total_items = q_content.count()
    total_page = max(math.ceil(total_items / settings.NUM_ITEMS_IN_PAGE) - 1, 0) if total_items else 0

    if selected_tags:
        existing_tags = set(Tag.objects.filter(slug__in=selected_tags).values_list("slug", flat=True))
        missing_tags = [tag_slug for tag_slug in selected_tags if tag_slug not in existing_tags]
        if missing_tags:
            if len(missing_tags) == 1:
                empty_state_title = "Тег не найден"
                empty_state_message = f"Тег «{missing_tags[0]}» не найден или был переименован."
            else:
                empty_state_title = "Теги не найдены"
                empty_state_message = f"Теги «{', '.join(missing_tags)}» не найдены или были переименованы."
        elif not total_items:
            if len(selected_tags) == 1:
                empty_state_message = "По этому тегу пока нет опубликованных новостей."
            else:
                empty_state_message = "По выбранным тегам пока нет опубликованных новостей."
        elif page_number > total_page:
            empty_state_message = "На этой странице больше нет новостей. Откройте первую страницу ленты."
    elif not total_items:
        empty_state_message = "Пока здесь нет новостей."

    q_content = q_content[page_number * settings.NUM_ITEMS_IN_PAGE:
                          page_number * settings.NUM_ITEMS_IN_PAGE+ settings.NUM_ITEMS_IN_PAGE]

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
        .order_by("-NumInPage", "-NumTotal", "name")[:settings.TAG_CLOUD_LIMIT]
    )

    to_template["LENTA"] = q_content
    to_template["TAGS_IN_PAGE"] = q_tags
    to_template["PAGE_OF_LIST"] = page_number
    to_template["TOTAL_PAGE"] = total_page
    to_template["EMPTY_STATE_TITLE"] = empty_state_title
    to_template["EMPTY_STATE_MESSAGE"] = empty_state_message
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
        now_value = timezone.now()
        # Фрмируем список заголовков для боковой навигации
        # Два запроса, т.к. это проще и "дешевле" чем городить один запрос и после делить его срезами.
        q_items_after = TbContent.objects.filter(
            Q(tdContentPublishDown__isnull=True) | Q(tdContentPublishDown__gt=now_value),
            Q(bContentPublish=True),
            Q(tdContentPublishUp__lte=q_item.tdContentPublishUp)
        ).only("id", "szContentHead", "szContentSlug", "tdContentPublishUp").order_by("-tdContentPublishUp", "id")[:settings.NUM_NAV_ITEMS_IN_PAGE // 2 + 1]
        q_items_before = TbContent.objects.filter(
            Q(tdContentPublishDown__isnull=True) | Q(tdContentPublishDown__gt=now_value),
            bContentPublish=True,
            tdContentPublishUp__gt=q_item.tdContentPublishUp
        ).only("id", "szContentHead", "szContentSlug", "tdContentPublishUp").order_by("tdContentPublishUp", "id")[:settings.NUM_NAV_ITEMS_IN_PAGE // 2]
        try:
            p = 0 if "p" not in request.GET else int(request.GET["p"])
            n = 0 if "n" not in request.GET else int(request.GET["n"])
            count = 0
            for i in q_items_before:
                count += 1
                if n-count < 1:
                    i.pp = p - 1
                    i.nn = n + settings.NUM_NAV_ITEMS_IN_PAGE - count
                else:
                    i.pp = p
                    i.nn = n - count
            count = 0
            for i in q_items_after:
                if i.id != q_item.id:
                    count += 1
                    if n+count <= settings.NUM_NAV_ITEMS_IN_PAGE:
                        i.pp = p
                        i.nn = n + count
                    else:
                        i.pp = p + 1
                        i.nn = n+count - settings.NUM_NAV_ITEMS_IN_PAGE
            to_template["PER_PAGE"] = settings.NUM_NAV_ITEMS_IN_PAGE
            to_template["PAGE"] = p
        except ValueError:
            to_template["PAGE"] = 0
            pass
        to_template["PAGE_OF_LIST"] = int(ppage)
        to_template["ITEMS_AFTER"] = q_items_after
        to_template["ITEMS_BEFORE"] = q_items_before
        # Счётчик просмотров обновляем отдельно от `save()`, чтобы не запускать
        # типографизацию, пересборку slug и автообновление `dtContentTimeStamp`.
        TbContent.objects.filter(pk=q_item.pk).update(iContentHits=F("iContentHits") + 1)
        q_item.iContentHits += 1
        return render(request, template, to_template)
    except (ValueError, AttributeError, TbContent.DoesNotExist, TbContent.MultipleObjectsReturned):
        raise Http404("Контента с таким id не существует")

