# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
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


def index(request) -> render:
    """ Главная страница

    :param request:
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
            "LIMIT 5 OFFSET 0"
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
    return render(request, template, to_template)
