from blazeweb.tasks import attributes

from compstack.auth.helpers import add_administrative_user
from compstack.auth.model.orm import Permission


@attributes('base-data')
def action_30_base_data():
    Permission.add_iu(name=u'auth-manage')


@attributes('+dev')
def action_40_admin_user():
    add_administrative_user()


@attributes('+test')
def action_40_test_data():
    Permission.add_iu(name=u'ugp_approved')
    Permission.add_iu(name=u'ugp_denied')
    Permission.add_iu(name=u'users-test1')
    Permission.add_iu(name=u'users-test2')
    Permission.add_iu(name=u'prof-test-1')
    Permission.add_iu(name=u'prof-test-2')
