from pysmvt import modimportauto, db
from pysutils import tolist, randchars
from werkzeug import BaseRequest

modimportauto('users.actions', ['user_update', 'permission_add'])

def login_client_with_permissions(client, approved_perms=None, denied_perms=None, super_user=False):
    """
        Creates a user with the given permissions and then logs in with said
        user.
    """
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
         password=password, super_user = super_user,
         approved_permissions = appr_perm_ids, denied_permissions = denied_perm_ids)
    
    # turn login flag off
    user.reset_required=False
    db.sess.commit()
    
    # save id for later since the request to the app will kill the session
    user_id = user.id
    
    # login with the user
    topost = {'login_id': username,
          'password': password,
          'login-form-submit-flag':'1'}
    environ, r = client.post('users/login', data=topost, as_tuple=True, follow_redirects=True)
    assert r.status_code == 200, r.status
    assert 'You logged in successfully!' in r.data
    assert BaseRequest(environ).url == 'http://localhost/'
    
    return user_id
