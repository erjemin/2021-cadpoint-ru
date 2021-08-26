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
          slug_tags: str = "",
          ppage: int = 0) -> render:
    """ Главная страница

    :param request:
    :param ppage:      текущая страница ленты
    :param slug_tags:      текущие slug-таги, разделитель "_" (в формате tag-1_tag-2_tag-eshe-odin
    :return:  response:
    """
    template = "index.jinja2"  # шаблон
    to_template = {"COOKIES": check_cookies(request)}
    # query = Q(tdContentPublishDown__isnull=True)
    # query.add(Q(tdContentPublishDown__gt=timezone.now()), Q.OR)
    # query.add(Q(bContentPublish=True), Q.AND)
    # q_content = TbContent.objects.filter(query)[:5]
    if slug_tags == "":
        query = "SELECT web_tbcontent.* FROM web_tbcontent " \
                "WHERE (web_tbcontent.tdContentPublishDown IS NULL" \
                "  OR web_tbcontent.tdContentPublishDown > NOW())" \
                "  AND web_tbcontent.tdContentPublishUp <= NOW() " \
                "  AND web_tbcontent.bContentPublish " \
                "ORDER BY web_tbcontent.tdContentPublishUp DESC " \
                "LIMIT 7 OFFSET %d" % (int(ppage) * 7, )
        query_count = "SELECT 1 AS id," \
                      "  COUNT(web_tbcontent.id) AS tot_item " \
                      "FROM web_tbcontent " \
                      "WHERE (web_tbcontent.tdContentPublishDown IS NULL" \
                      "  OR web_tbcontent.tdContentPublishDown > NOW())" \
                      "  AND web_tbcontent.tdContentPublishUp <= NOW()" \
                      "  AND web_tbcontent.bContentPublish"
    else:
        l_tags = slug_tags.split("_")
        s_tags = slug_tags.replace("_", "\', \'")
        query = "SELECT web_tbcontent.* FROM taggit_taggeditem" \
                "  INNER JOIN taggit_tag" \
                "    ON taggit_taggeditem.tag_id = taggit_tag.id" \
                "    AND taggit_taggeditem.content_type_id = 21" \
                "    AND taggit_tag.slug IN ('%s')" \
                "  RIGHT OUTER JOIN web_tbcontent" \
                "    ON web_tbcontent.id = taggit_taggeditem.object_id " \
                "WHERE (web_tbcontent.tdContentPublishDown IS NULL" \
                "  OR web_tbcontent.tdContentPublishDown > NOW())" \
                "  AND web_tbcontent.tdContentPublishUp <= NOW() " \
                "  AND web_tbcontent.bContentPublish " \
                "GROUP BY web_tbcontent.szContentHead " \
                "HAVING COUNT(DISTINCT taggit_tag.id) = %d "  \
                "ORDER BY web_tbcontent.tdContentPublishUp DESC " \
                "LIMIT 7 OFFSET %d" % (s_tags, len(l_tags), int(ppage) * 7)
        query_count = "SELECT 1 AS id," \
                      "  COUNT(SubQuery.id) AS tot_item " \
                      "FROM (SELECT web_tbcontent.id" \
                      "  FROM taggit_taggeditem" \
                      "    INNER JOIN taggit_tag" \
                      "      ON taggit_taggeditem.tag_id = taggit_tag.id" \
                      "      AND taggit_taggeditem.content_type_id = 21" \
                      "      AND taggit_tag.slug IN  ('%s')" \
                      "    RIGHT OUTER JOIN web_tbcontent" \
                      "      ON web_tbcontent.id = taggit_taggeditem.object_id" \
                      "  WHERE (web_tbcontent.tdContentPublishDown IS NULL" \
                      "  OR web_tbcontent.tdContentPublishDown > NOW())" \
                      "  AND web_tbcontent.tdContentPublishUp <= NOW()" \
                      "  AND web_tbcontent.bContentPublish" \
                      "  GROUP BY web_tbcontent.id" \
                      "  HAVING COUNT(DISTINCT taggit_tag.id) = %d) SubQuery" % (s_tags, len(l_tags))
        to_template.update({"TAGS_S": "/tag_" + slug_tags, "TAGS_L": l_tags})
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
                                  "ORDER BY tPageInfo.NumInPage DESC, tTotalInfo.NumTotal DESC, "
                                  "tTotalInfo.name LIMIT 20" % (query,))
    to_template.update({"LENTA": q_content, "TAGS_IN_PAGE": q_tags})
    to_template.update({"PAGE_OF_LIST": int(ppage)})
    q_count = TbContent.objects.raw(query_count)
    # print("--", (q_count[0].tot_item - 1) // 7, q_count[0].tot_item)
    to_template.update({"TOTAL_PAGE": (q_count[0].tot_item - 1) // 7})
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


def sitemap(request):
    template = "sitemap.jinja2"  # шаблон
    q_items = TbContent.objects.filter(
        Q(tdContentPublishDown__isnull=True) | Q(tdContentPublishDown__gt=timezone.now()),
        Q(bContentPublish=True)).order_by("-tdContentPublishUp", "id").all()
    to_template = {"ITEMS": q_items}
    print(q_items)
    response = render(request, template, to_template)
    return response
