from pysmvt.tasks import attributes

from plugstack.auth.actions import permission_add
from plugstack.auth.lib.utils import add_administrative_user

@attributes('base-data')
def action_30_base_data():
    permission_add(name=u'auth-manage', safe='unique')

@attributes('+dev')
def action_40_admin_user():
    add_administrative_user()

@attributes('+test')
def action_40_test_data():
    permission_add(name=u'ugp_approved')
    permission_add(name=u'ugp_denied')
    permission_add(name=u'users-test1')
    permission_add(name=u'users-test2')
    permission_add(name=u'prof-test-1')
    permission_add(name=u'prof-test-2')
