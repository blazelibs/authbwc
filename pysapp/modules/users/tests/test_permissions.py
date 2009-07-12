from pysmvt import modimportauto, appimportauto, ag
from werkzeug import Client, BaseResponse, BaseRequest

modimportauto('users.testing', ['login_client_with_permissions'])
            
class TestNotAuthenticated(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag._wsgi_test_app, BaseResponse)
        
    def test_unauthorized(self):
        routes = (
            '/users/add',
            '/users/edit/1',
            '/users/manage',
            '/users/delete/1',
            '/users/permissions/1',
            '/users/change_password',
            '/groups/add',
            '/groups/edit/1',
            '/groups/manage',
            '/groups/delete/1'
        )
        for route in routes:
            yield self.check_unauthorized, route
    
    def check_unauthorized(self, route):
        r = self.c.get(route)
        assert r.status_code == 401, "%s -- %s" % (route, r.status)

    def test_ok(self):
        routes = (
            '/users/login',
            '/users/recover_password'
        )
        for route in routes:
            yield self.check_ok, route
    
    def check_ok(self, route):
        r = self.c.get(route)
        assert r.status_code == 200, "%s -- %s" % (route, r.status)
    
    def test_logout(self):
        r = self.c.get('/users/logout')
        assert r.status_code == 302, r.status
        assert '/users/login' in r.data

class TestNoPerms(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag._wsgi_test_app, BaseResponse)
        login_client_with_permissions(cls.c)

    def test_forbidden(self):
        routes = (
            '/users/add',
            '/users/edit/1',
            '/users/manage',
            '/users/delete/1',
            '/users/permissions/1',
            '/groups/add',
            '/groups/edit/1',
            '/groups/manage',
            '/groups/delete/1'
        )
        for route in routes:
            yield self.check_forbidden, route
    
    def check_forbidden(self, route):
        r = self.c.get(route)
        assert r.status_code == 403, "%s -- %s" % (route, r.status)

    def test_ok(self):
        routes = (
            '/users/login',
            '/users/recover_password',
            '/users/change_password',
        )
        for route in routes:
            yield self.check_ok, route
    
    def check_ok(self, route):
        r = self.c.get(route)
        assert r.status_code == 200, "%s -- %s" % (route, r.status)
    
    def test_logout(self):
        """
            need new Client b/c using the same client can mess up other tests
            since order of tests is not guaranteed
        """
        c = Client(ag._wsgi_test_app, BaseResponse)
        login_client_with_permissions(c)
        environ, r = c.get('/users/logout', as_tuple=True, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert BaseRequest(environ).url == 'http://localhost/users/login'

class TestUsersManage(object):
    
    perms = u'users-manage'
    
    @classmethod
    def setup_class(cls):
        cls.c = Client(ag._wsgi_test_app, BaseResponse)
        login_client_with_permissions(cls.c, cls.perms)

    def test_ok(self):
        routes = (
            '/users/add',
            '/users/login',
            '/users/recover_password',
            '/users/change_password',
            '/users/edit/1',
            '/users/manage',
            '/users/delete/1',
            '/users/permissions/1',
            '/groups/add',
            '/groups/edit/1',
            '/groups/manage',
            '/groups/delete/1'
        )
        for route in routes:
            yield self.check_ok, route
            break
    
    def check_ok(self, route):
        r = self.c.get(route)
        assert r.status_code == 200, "%s -- %s" % (route, r.status)
    
    def test_logout(self):
        """
            need new Client b/c using the same client can mess up other tests
            since order of tests is not guaranteed
        """
        c = Client(ag._wsgi_test_app, BaseResponse)
        login_client_with_permissions(c, self.perms)
        environ, r = c.get('/users/logout', as_tuple=True, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert BaseRequest(environ).url == 'http://localhost/users/login'
    