from pysmvt import modimport, appimportauto, ag
from werkzeug import Client, BaseResponse

class TestPublic(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag._wsgi_test_app, BaseResponse)

    def test_unauthorized(self):
        r = self.c.get('/users/manage')
        assert r.status == '401 UNAUTHORIZED', r.status
        assert 'Authorization Error Encountered' in r.data

        r = self.c.get('/users/add')
        assert r.status == '401 UNAUTHORIZED', r.status
        assert 'Authorization Error Encountered' in r.data

    def test_login(self):
        r = self.c.get('/users/login')
        assert r.status == '200 OK', r.status
        assert 'Login' in r.data