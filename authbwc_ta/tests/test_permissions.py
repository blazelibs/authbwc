from blazeweb.globals import ag
from werkzeug import Client, BaseResponse, BaseRequest
from compstack.auth.lib.testing import login_client_with_permissions, create_user_with_permissions
from compstack.auth.model.orm import Group, Permission

class TestNotAuthenticated(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)

    def test_unauthorized(self):
        routes = (
            '/users/add',
            '/users/edit/1',
            '/users/manage',
            '/users/delete/1',
            '/users/permissions/1',
            '/users/change-password',
            '/groups/add',
            '/groups/edit/1',
            '/groups/manage',
            '/groups/delete/1',
            '/permissions/manage',
            '/permissions/edit/1',
            '/users/profile'
        )
        for route in routes:
            yield self.check_unauthorized, route

    def check_unauthorized(self, route):
        r = self.c.get(route)
        assert r.status_code == 401, "%s -- %s" % (route, r.status)

    def test_ok(self):
        routes = (
            '/users/login',
            '/users/recover-password'
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
        cls.c = Client(ag.wsgi_test_app, BaseResponse)
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
            '/groups/delete/1',
            '/permissions/manage',
            '/permissions/edit/1'
        )
        for route in routes:
            yield self.check_forbidden, route

    def check_forbidden(self, route):
        r = self.c.get(route)
        assert r.status_code == 403, "%s -- %s" % (route, r.status)

    def test_ok(self):
        routes = (
            '/users/login',
            '/users/recover-password',
            '/users/change-password',
            '/users/profile'
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
        c = Client(ag.wsgi_test_app, BaseResponse)
        login_client_with_permissions(c)
        environ, r = c.get('/users/logout', as_tuple=True, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert BaseRequest(environ).url == 'http://localhost/users/login'

class TestAuthManage(object):

    perms = u'auth-manage'

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)
        login_client_with_permissions(cls.c, cls.perms)

    def test_ok(self):
        # add another user so that we can be sure we are not deleting the
        # user the Client is currently logged in as, which would cause a 302
        user_id = create_user_with_permissions().id
        # add a group so we get 200s when working with it instead of 302s
        group_id = Group.add(name=u'TestUsersManage.test_ok-group').id
        # get a list of permissions (there should be at least one) so we have a real id
        permission_id = Permission.pairs('id:name', Permission.name)[0][0]

        routes = (
            '/users/add',
            '/users/login',
            '/users/recover-password',
            '/users/change-password',
            '/users/edit/%s' % user_id,
            '/users/manage',
            '/users/permissions/%s' % user_id,
            '/groups/add',
            '/groups/edit/%s' % group_id,
            '/groups/manage',
            '/permissions/manage',
            '/permissions/edit/%s' % permission_id,
        )
        for route in routes:
            yield self.check_code, 200, route

        routes = (
            '/users/delete/%s' % user_id,
            '/groups/delete/%s' % group_id,
        )

        for route in routes:
            yield self.check_code, 302, route

    def check_code(self, code, route):
        r = self.c.get(route)
        assert r.status_code == code, "%s -- %s" % (route, r.status)

    def test_logout(self):
        """
            need new Client b/c using the same client can mess up other tests
            since order of tests is not guaranteed
        """
        c = Client(ag.wsgi_test_app, BaseResponse)
        login_client_with_permissions(c, self.perms)
        environ, r = c.get('/users/logout', as_tuple=True, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert BaseRequest(environ).url == 'http://localhost/users/login'
