import paste.fixture
from blazeutils import tolist, randchars
from blazeweb.testing import Client
from werkzeug.test import Client as WerkzeugClient
from werkzeug.wrappers import BaseRequest

from compstack.auth.helpers import after_login_url
from compstack.sqlalchemy import db

try:
    from webtest import TestApp
except ImportError:
    TestApp = None


def login_client_with_permissions(client, approved_perms=None, denied_perms=None, super_user=False):
    """
        Creates a user with the given permissions and then logs in with said
        user.
    """
    from compstack.auth.lib.testing import create_user_with_permissions, login_client_as_user

    # create user
    user = create_user_with_permissions(approved_perms, denied_perms, super_user)

    # save id for later since the request to the app will kill the session
    user_id = user.id

    # login with the user
    login_client_as_user(client, user.login_id, user.text_password)

    return user_id


def login_client_as_user(client, username, password, validate_login_response=True):
    topost = {
        'login_id': username,
        'password': password,
        'login-form-submit-flag': '1'
    }
    if isinstance(client, (Client, WerkzeugClient)):
        if isinstance(client, Client):
            # blazeweb client handles follow_redirects differently
            req, resp = client.post('users/login', data=topost, follow_redirects=True)
        else:
            # werkzeug Client
            environ, resp = client.post('users/login', data=topost, as_tuple=True,
                                        follow_redirects=True)
            req = BaseRequest(environ)
        if validate_login_response:
            assert resp.status_code == 200, resp.status
            assert b'You logged in successfully!' in resp.data, resp.data[0:500]
            assert req.url.endswith(after_login_url()), '%s != %s' % (req.url, after_login_url())
        return req, resp
    elif isinstance(client, (paste.fixture.TestApp, TestApp)):
        res = client.post('/users/login', params=topost)
        res = res.follow()
        if validate_login_response:
            assert res.request.url.endswith(after_login_url()), \
                '%s != %s' % (res.request.url, after_login_url())
            res.mustcontain('You logged in successfully!')
        return res
    else:
        raise TypeError('client is of an unexpected type: %s' % client.__class__)


def create_user_with_permissions(approved_perms=None, denied_perms=None, super_user=False):
    from compstack.auth.model.orm import User, Permission

    appr_perm_ids = []
    denied_perm_ids = []
    # create the permissions
    for perm in tolist(approved_perms):
        p = Permission.get_by(name=perm)
        if p is None:
            raise ValueError('permission %s does not exist' % perm)
        appr_perm_ids.append(p.id)
    for perm in tolist(denied_perms):
        p = Permission.get_by(name=perm)
        if p is None:
            raise ValueError('permission %s does not exist' % perm)
        denied_perm_ids.append(p.id)

    # create the user
    username = u'user_for_testing_%s' % randchars(15)
    password = randchars(15)
    user = User.add(
        login_id=username,
        email_address=u'%s@example.com' % username,
        password=password,
        super_user=super_user,
        assigned_groups=[],
        approved_permissions=appr_perm_ids,
        denied_permissions=denied_perm_ids
    )

    # turn login flag off
    user.reset_required = False
    db.sess.commit()

    # make text password available
    user.text_password = password

    return user
