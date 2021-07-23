# -*- coding: utf-8 -*-
from django.shortcuts import render
from web.add_function import *

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
    template = "under_reconstruction.jinja2"  # шаблон
    to_template = {"COOKIES": check_cookies(request)}
    return render(request, template, to_template)
