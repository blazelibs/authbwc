from pysmvt import modimport, db, appimportauto
from pysutils import tolist, randchars
from werkzeug import BaseRequest
from pysmvt.test import Client

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
    req, resp = login_client_as_user(client, user.login_id, user.text_password)
    assert resp.status_code == 200, resp.status
    assert 'You logged in successfully!' in resp.data
    assert req.url == 'http://localhost/'
    
    return user_id

def login_client_as_user(client, username, password):
    topost = {'login_id': username,
          'password': password,
          'login-form-submit-flag':'1'}
    if isinstance(client, Client):
        # pysmvt client handles follow_redirects differently
        return client.post('users/login', data=topost, follow_redirects=True)
    else:
        # werkzeug Client
        environ, r = client.post('users/login', data=topost, as_tuple=True, follow_redirects=True)
        return BaseRequest(environ), r

def create_user_with_permissions(approved_perms=None, denied_perms=None, super_user=False):
    user_update = modimport('users.actions', 'user_update')
    permission_add = modimport('users.actions', 'permission_add')
    
    appr_perm_ids = []
    denied_perm_ids = []
    # create the permissions
    for perm in tolist(approved_perms):
        p = permission_add(name=perm, safe='unique')
        appr_perm_ids.append(p.id)
    for perm in tolist(denied_perms):
        p = permission_add(name=perm, safe='unique')
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