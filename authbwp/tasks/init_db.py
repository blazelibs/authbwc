from pysmvt.tasks import attributes

from plugstack.auth.helpers import add_administrative_user
from plugstack.auth.model.actions import permission_update

@attributes('base-data')
def action_30_base_data():
    permission_update(None, name=u'auth-manage', _ignore_unique_exception=True)

@attributes('+dev')
def action_40_admin_user():
    add_administrative_user()

@attributes('+test')
def action_40_test_data():
    permission_update(None, name=u'ugp_approved')
    permission_update(None, name=u'ugp_denied')
    permission_update(None, name=u'users-test1')
    permission_update(None, name=u'users-test2')
    permission_update(None, name=u'prof-test-1')
    permission_update(None, name=u'prof-test-2')
