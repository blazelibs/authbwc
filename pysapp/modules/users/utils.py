# -*- coding: utf-8 -*-
from pysmvt import settings
from pysmvt.routing import index_url

def after_login_url():
    if settings.modules.users.after_login_url:
        if callable(settings.modules.users.after_login_url):
            return settings.modules.users.after_login_url()
        else:
            return settings.modules.users.after_login_url
    return index_url()