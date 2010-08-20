from blazeweb.tasks import attributes

from plugstack.auth.helpers import add_administrative_user
from plugstack.auth.model.orm import Permission

@attributes('base-data')
def action_30_base_data():
    Permission.add_iu(name=u'auth-manage')

@attributes('+dev')
def action_40_admin_user():
    add_administrative_user()

@attributes('+test')
def action_40_test_data():
    Permission.add(name=u'ugp_approved')
    Permission.add(name=u'ugp_denied')
    Permission.add(name=u'users-test1')
    Permission.add(name=u'users-test2')
    Permission.add(name=u'prof-test-1')
    Permission.add(name=u'prof-test-2')
