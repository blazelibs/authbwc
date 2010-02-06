from pysmvt.tasks import attributes
from pysapp.lib.db import run_module_sql

def action_20_custom_sql():
    run_module_sql('users', 'create_views', use_dialect=True)

@attributes('base-data')
def action_30_base_data():    
    # this module's permissions
    from ..actions import permission_add
    permission_add(name=u'users-manage', safe='unique')

@attributes('+dev')
def action_40_admin_user():
    from ..utils import add_administrative_user
    add_administrative_user()

@attributes('+test')
def action_40_test_data():
    from ..actions import permission_add
    permission_add(name=u'ugp_approved')
    permission_add(name=u'ugp_denied')
    permission_add(name=u'users-test1')
    permission_add(name=u'users-test2')
    permission_add(name=u'prof-test-1')
    permission_add(name=u'prof-test-2')