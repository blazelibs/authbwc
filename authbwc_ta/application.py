from blazeweb.application import WSGIApp
from blazeweb.hierarchy import visitmods
from blazeweb.middleware import full_wsgi_stack
from blazeweb.scripting import application_entry
from sqlalchemybwc.lib.middleware import SQLAlchemyApp

import authbwc_ta.config.settings as settingsmod


def make_wsgi(profile='Dev'):
    app = WSGIApp(settingsmod, profile)

    app = SQLAlchemyApp(app)

    # has to happen after the db global gets setup and is needed b/c of our
    # use of @asview
    visitmods('views')

    return full_wsgi_stack(app)


def script_entry():
    application_entry(make_wsgi)

if __name__ == '__main__':
    script_entry()
