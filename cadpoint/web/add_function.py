# -*- coding: utf-8 -*-

from cadpoint.settings import *


def check_cookies(request) -> bool:
    # проверка, что посетитель согласился со сбором данных через cookies
    if request.COOKIES.get('cookie_accept'):
        return False
    return True
