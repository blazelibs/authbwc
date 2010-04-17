from pysmvt import modimport, db, appimportauto
from pysutils import tolist, randchars
from werkzeug import BaseRequest, Client as WerkzeugClient
from pysmvt.test import Client
import paste.fixture
try:
    from webtest import TestApp
except ImportError:
    TestApp = None
    
def login_client_with_permissions(client, approved_perms=None, denied_perms=None, super_user=False):
    """
        Creates a user with the given permissions and then logs in with said
        user.
    """
    
    # create user
    user = create_user_with_permissions(approved_perms, denied_perms, super_user)
    
    # save id for later since the request to the app will kill the session
    user_id = user.id
    
    # login with the user
    login_client_as_user(client, user.login_id, user.text_password)

    return user_id

def login_client_as_user(client, username, password):
    topost = {'login_id': username,
          'password': password,
          'login-form-submit-flag':'1'}
    if isinstance(client, (Client, WerkzeugClient)):
        if isinstance(client, Client):
            # pysmvt client handles follow_redirects differently
            req, resp = client.post('users/login', data=topost, follow_redirects=True)
        else:
            # werkzeug Client
            environ, resp = client.post('users/login', data=topost, as_tuple=True, follow_redirects=True)
            req = BaseRequest(environ)
        assert resp.status_code == 200, resp.status
        assert 'You logged in successfully!' in resp.data, resp.data[0:500]
        assert req.url == 'http://localhost/'
    elif isinstance(client, (paste.fixture.TestApp, TestApp)):
        res = client.post('/users/login', params=topost)
        res = res.follow()
        assert res.request.url == '/' or res.request.url == 'http://localhost/', res.request.url
        res.mustcontain('You logged in successfully!')
    else:
        raise TypeError('client is of an unexpected type: %s' % client.__class__)

def create_user_with_permissions(approved_perms=None, denied_perms=None, super_user=False):
    user_update = modimport('users.actions', 'user_update')
    permission_get_by_name = modimport('users.actions', 'permission_get_by_name')
    
    appr_perm_ids = []
    denied_perm_ids = []
    # create the permissions
    for perm in tolist(approved_perms):
        p = permission_get_by_name(perm)
        if p is None:
            raise ValueError('permission %s does not exist' % perm)
        appr_perm_ids.append(p.id)
    for perm in tolist(denied_perms):
        p = permission_get_by_name(perm)
        if p is None:
            raise ValueError('permission %s does not exist' % perm)
        denied_perm_ids.append(p.id)

    # create the user
    username = u'user_for_testing_%s' % randchars(15)
    password = randchars(15)
    user = user_update(None, login_id=username, email_address=u'%s@example.com' % username,
         password=password, super_user = super_user, assigned_groups = [],
         approved_permissions = appr_perm_ids, denied_permissions = denied_perm_ids)
    
    # turn login flag off
    user.reset_required=False
    db.sess.commit()
    
    # make text password available
    user.text_password = password
    
    return user