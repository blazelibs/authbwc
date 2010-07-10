import datetime
import minimock
import re
import smtplib

from blazeweb.testing import inrequest
from blazeutils import randchars
from datagridbwp_ta.tests._supporting import assertEqualSQL
from nose.tools import nottest

from plugstack.auth.lib.testing import create_user_with_permissions
from plugstack.auth.model.actions import user_get, user_get_by_permissions, \
    group_update, permission_update, user_get_by_permissions_query, \
    user_update, user_get_by_login, user_get_by_email, user_validate, \
    group_get_by_name, permission_get_by_name, user_update, \
    group_delete, user_permission_map_groups, user_permission_map, \
    permission_assignments_group_by_name as group_perm_init
from plugstack.auth.model.queries import query_denied_group_permissions, \
    query_approved_group_permissions, query_user_group_permissions, \
    query_users_permissions
from plugstack.sqlalchemy import db

def test_group_unique():
    g1 = group_update(None, name=u'test unique group name', _ignore_unique_exception=True)
    g2 = group_update(None, name=u'test unique group name', _ignore_unique_exception=True)
    assert g1.id == g2.id and g1.id is not None

def test_group_get_by_name():
    g = group_update(None, name=u'group_for_testing_%s'%randchars(15), _ignore_unique_exception=True)
    assert group_get_by_name(g.name).id == g.id

def test_permission_unique():
    p1 = permission_update(None, name=u'test unique permission name', _ignore_unique_exception=True)
    p2 = permission_update(None, name=u'test unique permission name', _ignore_unique_exception=True)
    assert p1.id == p2.id and p1.id is not None

def test_permission_get_by_name():
    p = permission_update(None, name=u'permission_for_testing_%s'%randchars(15), _ignore_unique_exception=True)
    assert permission_get_by_name(p.name).id == p.id

def test_user_unique():
    u1 = create_user_with_permissions()
    u2 = user_update(None, login_id=u1.login_id, email_address='test%s@example.com'%u1.login_id, _ignore_unique_exception=True)
    assert u2 is None, '%s, %s'%(u1.id, u2.id)
    u2 = user_update(None, login_id='test%s'%u1.login_id, email_address=u1.email_address, _ignore_unique_exception=True)
    assert u2 is None

def test_user_update():
    u = create_user_with_permissions()
    current_hash = u.pass_hash
    u = user_update(u.id, pass_hash=u'123456')
    assert u.pass_hash == current_hash

    u.reset_required = False
    db.sess.commit()
    u = user_update(u.id, email_notify=True)
    assert not u.reset_required
    u = user_update(u.id, password='new_password')
    assert u.reset_required

def test_user_get_by_login():
    u = create_user_with_permissions()
    obj = user_get_by_login(u.login_id)
    assert u.id == obj.id

def test_user_get_by_email():
    u = create_user_with_permissions()
    obj = user_get_by_email(u.email_address)
    assert u.id == obj.id
    obj = user_get_by_email((u'%s'%u.email_address).upper())
    assert u.id == obj.id

def test_user_name_or_login():
    u = create_user_with_permissions()
    assert u.name_or_login == u.login_id
    u.name_first = u'testname'
    assert u.name != ''
    assert u.name_or_login == u.name

def test_user_validate():
    u = create_user_with_permissions()
    u.password = u'testpass123'
    db.sess.commit()
    assert user_validate(login_id=u.login_id, password=u'bad_password') is None
    assert user_validate(login_id=u'bad_login', password=u'testpass123') is None
    assert user_validate(login_id=u.login_id, password=u'testpass123').id == u.id

def test_user_group_assignment():
    g1 = group_update(None, name=u'group_for_testing_%s'%randchars(15), _ignore_unique_exception=True)
    g2 = group_update(None, name=u'group_for_testing_%s'%randchars(15), _ignore_unique_exception=True)

    u = create_user_with_permissions()
    assert u.groups == []

    user_update(u.id, assigned_groups=[g1.id,g2.id])
    assert len(u.groups) == 2
    assert len(g1.users) == len(g2.users) == 1

    user_update(u.id, assigned_groups=g2.id)
    assert len(u.groups) == 1
    assert u.groups[0].id == g2.id

def test_group_delete():
    g1 = group_update(None, name=u'group_for_testing_%s'%randchars(15), _ignore_unique_exception=True)
    g2 = group_update(None, name=u'group_for_testing_%s'%randchars(15), _ignore_unique_exception=True)

    u = create_user_with_permissions()
    user_update(u.id, assigned_groups=[g1.id,g2.id])

    ret = group_delete(g1.id)
    assert ret == True
    assert len(g2.users) == 1
    assert len(u.groups) == 1
    assert u.groups[0].id == g2.id

def test_inactive_property():
    user = create_user_with_permissions()

    user.inactive_flag = True

    assert user.inactive

    user.inactive_flag = False
    user.inactive_date = datetime.datetime(2010, 10, 10)

    assert not user.inactive

    user.inactive_date = datetime.datetime(2000, 10, 10)

    assert user.inactive

class TestPermissions(object):

    @classmethod
    def setup_class(cls):
        permissions = [
            'ugp_approved_grp', 'ugp_not_approved', 'ugp_denied_grp']

        for permission in permissions:
            permission_update(None, name=unicode(permission))

        cls.user = create_user_with_permissions(u'ugp_approved', u'ugp_denied')
        cls.user2 = create_user_with_permissions(u'ugp_approved')
        cls.g1 = group_update(None, name=u'ugp_g1')
        cls.g2 = group_update(None, name=u'ugp_g2')
        group_perm_init(u'ugp_g1', (u'ugp_approved_grp', u'ugp_denied', u'ugp_denied_grp'))
        group_perm_init(u'ugp_g2', None, u'ugp_denied_grp')
        cls.user.groups.append(cls.g1)
        cls.user.groups.append(cls.g2)
        db.sess.commit()

        cls.perm_approved_grp = permission_get_by_name(u'ugp_approved_grp')
        cls.perm_denied = permission_get_by_name(u'ugp_denied')
        cls.perm_denied_grp = permission_get_by_name(u'ugp_denied_grp')

    def test_user_get_by_permissions(self):

        # user directly approved
        users_approved = user_get_by_permissions(u'ugp_approved')
        assert users_approved[0] is self.user
        assert users_approved[1] is self.user2
        assert len(users_approved) == 2

        # user approved by group association
        assert user_get_by_permissions(u'ugp_approved_grp')[0] is self.user

        # user denial and group approval
        assert user_get_by_permissions(u'ugp_denied') == []

        # no approval
        assert user_get_by_permissions(u'ugp_not_approved') == []

        # approved by one group denied by another, denial takes precedence
        assert user_get_by_permissions(u'ugp_denied_grp') == []

    def test_user_permission_map_groups(self):
        # test group perms map
        perm_map = user_permission_map_groups(self.user.id)

        assert not perm_map.has_key(permission_get_by_name(u'ugp_approved').id)
        assert not perm_map.has_key(permission_get_by_name(u'ugp_not_approved').id)

        assert len(perm_map[self.perm_approved_grp.id]['approved']) == 1
        assert perm_map[self.perm_approved_grp.id]['approved'][0]['id'] == self.g1.id
        assert len(perm_map[self.perm_approved_grp.id]['denied']) == 0

        assert len(perm_map[self.perm_denied.id]['approved']) == 1
        assert perm_map[self.perm_denied.id]['approved'][0]['id'] == self.g1.id
        assert len(perm_map[self.perm_denied.id]['denied']) == 0

        assert len(perm_map[self.perm_denied_grp.id]['approved']) == 1
        assert perm_map[self.perm_denied_grp.id]['approved'][0]['id'] == self.g1.id
        assert len(perm_map[self.perm_denied_grp.id]['denied']) == 1
        assert perm_map[self.perm_denied_grp.id]['denied'][0]['id'] == self.g2.id

    def test_user_permission_map(self):
        permissions_approved = [
            'ugp_approved', 'ugp_approved_grp']
        # test user perms map
        perm_map = user_permission_map(self.user.id)
        for rec in perm_map:
            assert rec['resulting_approval'] == (rec['permission_name'] in permissions_approved)

@nottest
def cleanup_query_for_test(query):
    return unicode(query).replace('\r','').replace('\n',' ').replace('  ',' ')

def test_query_denied_group_permissions():
    query = cleanup_query_for_test(query_denied_group_permissions())
    assert query == 'SELECT auth_permissions.id AS permission_id, auth_user_group_map.auth_user_id AS user_id, sum(auth_permission_assignments_groups.approved) AS group_denied ' \
    'FROM auth_permissions LEFT OUTER JOIN auth_permission_assignments_groups ON auth_permissions.id = auth_permission_assignments_groups.permission_id ' \
    'AND auth_permission_assignments_groups.approved = :approved_1 LEFT OUTER JOIN auth_user_group_map ON auth_user_group_map.auth_group_id = auth_permission_assignments_groups.group_id GROUP BY auth_permissions.id, auth_user_group_map.auth_user_id'

def test_query_approved_group_permissions():
    query = cleanup_query_for_test(query_approved_group_permissions())
    assert query == 'SELECT auth_permissions.id AS permission_id, auth_user_group_map.auth_user_id AS user_id, sum(auth_permission_assignments_groups.approved) AS group_approved ' \
    'FROM auth_permissions LEFT OUTER JOIN auth_permission_assignments_groups ON auth_permissions.id = auth_permission_assignments_groups.permission_id ' \
    'AND auth_permission_assignments_groups.approved = :approved_1 LEFT OUTER JOIN auth_user_group_map ON auth_user_group_map.auth_group_id = auth_permission_assignments_groups.group_id GROUP BY auth_permissions.id, auth_user_group_map.auth_user_id'

def test_query_user_group_permissions():
    query = cleanup_query_for_test(query_user_group_permissions())
    expected = 'SELECT auth_users.id AS user_id, auth_groups.id AS group_id, auth_groups.name AS group_name, auth_permission_assignments_groups.permission_id, auth_permission_assignments_groups.approved AS group_approved ' \
    'FROM auth_users LEFT OUTER JOIN auth_user_group_map ON auth_users.id = auth_user_group_map.auth_user_id LEFT OUTER JOIN auth_groups ON auth_groups.id = auth_user_group_map.auth_group_id LEFT OUTER JOIN auth_permission_assignments_groups ON auth_permission_assignments_groups.group_id = auth_groups.id ' \
    'WHERE auth_permission_assignments_groups.permission_id IS NOT NULL'
    assertEqualSQL(query, expected)

def test_query_users_permissions():
    query = cleanup_query_for_test(query_users_permissions())
    expected = 'SELECT user_perm.user_id, user_perm.permission_id, user_perm.permission_name, user_perm.login_id, auth_permission_assignments_users.approved AS user_approved, g_approve.group_approved, g_deny.group_denied ' \
    'FROM (SELECT auth_users.id AS user_id, auth_permissions.id AS permission_id, auth_permissions.name AS permission_name, auth_users.login_id AS login_id ' \
    'FROM auth_users, auth_permissions) AS user_perm LEFT OUTER JOIN auth_permission_assignments_users ON auth_permission_assignments_users.user_id = user_perm.user_id AND auth_permission_assignments_users.permission_id = user_perm.permission_id LEFT OUTER JOIN (SELECT auth_permissions.id AS permission_id, auth_user_group_map.auth_user_id AS user_id, sum(auth_permission_assignments_groups.approved) AS group_approved ' \
    'FROM auth_permissions LEFT OUTER JOIN auth_permission_assignments_groups ON auth_permissions.id = auth_permission_assignments_groups.permission_id ' \
    'AND auth_permission_assignments_groups.approved = :approved_1 LEFT OUTER JOIN auth_user_group_map ON auth_user_group_map.auth_group_id = auth_permission_assignments_groups.group_id GROUP BY auth_permissions.id, auth_user_group_map.auth_user_id) AS g_approve ON g_approve.user_id = user_perm.user_id AND g_approve.permission_id = user_perm.permission_id LEFT OUTER JOIN (SELECT auth_permissions.id AS permission_id, auth_user_group_map.auth_user_id AS user_id, sum(auth_permission_assignments_groups.approved) AS group_denied ' \
    'FROM auth_permissions LEFT OUTER JOIN auth_permission_assignments_groups ON auth_permissions.id = auth_permission_assignments_groups.permission_id ' \
    'AND auth_permission_assignments_groups.approved = :approved_2 LEFT OUTER JOIN auth_user_group_map ON auth_user_group_map.auth_group_id = auth_permission_assignments_groups.group_id GROUP BY auth_permissions.id, auth_user_group_map.auth_user_id) AS g_deny ON g_deny.user_id = user_perm.user_id AND g_deny.permission_id = user_perm.permission_id ORDER BY user_perm.user_id, user_perm.permission_id'
    assertEqualSQL(query, expected)
