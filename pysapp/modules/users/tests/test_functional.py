from pysmvt import modimport, appimportauto
from werkzeug import Client, BaseResponse

from pysappexample.testing import testapp

#class TestPublic(object):
#
#    @classmethod
#    def setup_class(cls):
#        cls.c = Client(testapp, BaseResponse)
#
#    def test_unauthorized(self):
#        r = self.c.get('/users/manage')
#        assert r.status == '401 UNAUTHORIZED', r.status
#        assert 'Authorization Error Encountered' in r.data
#
#        r = self.c.get('/users/add')
#        assert r.status == '401 UNAUTHORIZED', r.status
#        assert 'Authorization Error Encountered' in r.data
#
#    def test_login(self):
#        r = self.c.get('/users/login')
#        assert r.status == '200 OK', r.status
#        assert 'Login' in r.data