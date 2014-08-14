from blazeweb.views import asview


@asview('/')
def index():
    return 'index'
