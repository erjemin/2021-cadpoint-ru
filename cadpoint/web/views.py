# -*- coding: utf-8 -*-
from django.shortcuts import render, HttpResponseRedirect
from django.http import Http404
from django.db.models import Q
# from datetime import datetime
from django.utils import timezone
from web.models import TbContent
from web.add_function import *
import pytz

# Create your views here.
def handler404(request, exception: str) -> render:
    """ Обработчик ошибки 404

        :param request:     http-запрос
        :param exception:   сообщение с причиной ошибки
        :return:  response: http-ответ
        """
    response = render(request, "404.html", {"MSG": exception})
    response.status_code = 404
    return response


def handler500(request) -> render:
    """ Обработчик ошибки 500

    :param request:
    :return:  response:
    """
    response = render(request, "500.html", {})
    response.status_code = 500
    return response


def index(request,
          ppage: int = 0) -> render:
    """ Главная страница

    :param request:
    :param ppage:      текущая страница ленты
    :return:  response:
    """
    template = "index.jinja2"  # шаблон
    to_template = {"COOKIES": check_cookies(request)}
    # query = Q(tdContentPublishDown__isnull=True)
    # query.add(Q(tdContentPublishDown__gt=timezone.now()), Q.OR)
    # query.add(Q(bContentPublish=True), Q.AND)
    # q_content = TbContent.objects.filter(query)[:5]
    query = "SELECT web_tbcontent.* FROM web_tbcontent " \
            "WHERE (web_tbcontent.tdContentPublishDown IS NULL" \
            "  OR web_tbcontent.tdContentPublishDown > NOW())" \
            "  AND web_tbcontent.bContentPublish " \
            "ORDER BY web_tbcontent.tdContentPublishUp DESC " \
            "LIMIT 7 OFFSET %d" % (int(ppage) * 7, )
    q_content = TbContent.objects.raw(query)
    q_tags = TbContent.objects.raw("SELECT DISTINCT tTotalInfo.*,"
                                  "  IF (tPageInfo.NumInPage IS UNKNOWN, 0, tPageInfo.NumInPage) AS NumInPage "
                                  "FROM (SELECT DISTINCT taggit_tag.id, COUNT(tPage.id) AS NumInPage "
                                  "  FROM taggit_taggeditem"
                                  "    INNER JOIN taggit_tag"
                                  "      ON taggit_taggeditem.tag_id = taggit_tag.id"
                                  "    INNER JOIN (%s) tPage"
                                  "       ON taggit_taggeditem.object_id = tPage.id"
                                  "  GROUP BY taggit_tag.id) tPageInfo"
                                  "  RIGHT OUTER JOIN (SELECT DISTINCT"
                                  "      taggit_tag.*,"
                                  "      COUNT(web_tbcontent.id) AS NumTotal"
                                  "   FROM taggit_taggeditem"
                                  "      INNER JOIN taggit_tag"
                                  "        ON taggit_taggeditem.tag_id = taggit_tag.id"
                                  "      INNER JOIN web_tbcontent"
                                  "        ON taggit_taggeditem.object_id = web_tbcontent.id"
                                  "    GROUP BY taggit_tag.id, taggit_tag.name, taggit_tag.slug) tTotalInfo"
                                  "    ON tPageInfo.id = tTotalInfo.id" 
                                  "    GROUP BY tPageInfo.id,    tPageInfo.NumInPage,"
                                  "         tTotalInfo.id,   tTotalInfo.NumTotal,"
                                  "         tTotalInfo.name, tTotalInfo.slug " 
                                  "ORDER BY tPageInfo.NumInPage DESC, tTotalInfo.name,"
                                  "         tTotalInfo.NumTotal DESC" % (query,))
    to_template.update({"LENTA": q_content, "TAGS_IN_PAGE": q_tags})
    to_template.update({"PAGE_OF_LIST": int(ppage)})
    return render(request, template, to_template)


def redirect_item(request,
                  content_id: int = 0) -> render:
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
              ppage: int = 0) -> render:
    """ Формирование "ленты" о предприятии

        :param request:
        :param content_id: id контента которую надо отобразить
        :return: response:
    """
    template = "item.jinja2"  # шаблон
    to_template = {"COOKIES": check_cookies(request)}
    try:
        q_item = TbContent.objects.filter(id=int(content_id)).first()
        if not q_item.bContentPublish:
            raise Http404("Контент не опубликован")
        to_template.update({"ITEM": q_item})
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
            to_template.update({"PER_PAGE": 7})
            to_template.update({"PAGE": p})
        except ValueError:
            to_template.update({"PAGE": 0})
            pass
        to_template.update({"PAGE_OF_LIST": int(ppage)})
        to_template.update({"ITEMS_AFTER": q_items_after})
        to_template.update({"ITEMS_BEFORE": q_items_before})
        q_item.iContentHits += 1
        q_item.save(update_fields=["iContentHits"])
        return render(request, template, to_template)
    except (ValueError, AttributeError, TbContent.DoesNotExist, TbContent.MultipleObjectsReturned):
        raise Http404("Контента с таким id не существует")
