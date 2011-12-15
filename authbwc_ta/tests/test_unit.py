import datetime
import minimock
import re
import smtplib

from blazeweb.globals import settings
from blazeweb.testing import inrequest
from blazeutils import randchars
from nose.tools import nottest, eq_

from compstack.auth.helpers import after_login_url
from compstack.auth.lib.testing import create_user_with_permissions
from compstack.auth.model.queries import query_denied_group_permissions, \
    query_approved_group_permissions, query_user_group_permissions, \
    query_users_permissions
from compstack.auth.model.orm import User, Group, Permission
from compstack.sqlalchemy import db

def test_group_unique():
    g1 = Group.add_iu(name=u'test unique group name')
    g2 = Group.add_iu(name=u'test unique group name')
    assert g1 and g2 is None

def test_group_get_by_name():
    g = Group.add_iu(name=u'group_for_testing_%s'%randchars(15))
    assert Group.get_by(name=g.name).id == g.id

def test_permission_unique():
    p1 = Permission.add_iu(name=u'test unique permission name')
    p2 = Permission.add_iu(name=u'test unique permission name')
    assert p1 and p2 is None

def test_permission_get_by_name():
    p = Permission.add_iu(name=u'permission_for_testing_%s'%randchars(15))
    assert Permission.get_by(name=p.name).id == p.id

def test_user_unique():
    u1 = create_user_with_permissions()
    u2 = User.add_iu(login_id=u1.login_id, email_address='test%s@example.com'%u1.login_id)
    assert u2 is None, '%s, %s'%(u1.id, u2.id)
    u2 = User.add_iu(login_id='test%s'%u1.login_id, email_address=u1.email_address)
    assert u2 is None

def test_user_update():
    u = create_user_with_permissions()
    current_hash = u.pass_hash
    u = User.edit(u.id, pass_hash=u'123456')
    assert u.pass_hash == current_hash

    u.reset_required = False
    db.sess.commit()
    u = User.edit(u.id, email_notify=True)
    assert not u.reset_required
    u = User.edit(u.id, password='new_password')
    assert u.reset_required

def test_password_hashing():
    u = create_user_with_permissions()
    assert u.pass_hash
    assert u.pass_salt

    # test a new random salt every time a password is set (by default)
    oldsalt = u.pass_salt
    oldhash = u.pass_hash
    u.password = 'foobar'
    assert oldsalt != u.pass_salt
    assert oldhash != u.pass_hash

    # use a custom salt
    u.set_password('foobar', 'mysalt')
    assert u.pass_salt == 'mysalt'

    # using the same password and salt should result in the same hash
    oldsalt = u.pass_salt
    oldhash = u.pass_hash
    u.set_password('foobar', 'mysalt')
    assert oldsalt == u.pass_salt
    assert oldhash == u.pass_hash

    # now make sure the application salt will be taken into account if set
    try:
        settings.components.auth.password_salt = '123456'
        u.set_password('foobar', 'mysalt')
        assert oldsalt == u.pass_salt, u.pass_salt
        # hash is different b/c of the application salt
        assert oldhash != u.pass_hash
    finally:
        settings.components.auth.password_salt = None

def test_password_validate():
    u = create_user_with_permissions()
    password = u.text_password
    assert u.validate_password(password)
    assert not u.validate_password('foobar')

def test_user_get_by_login():
    u = create_user_with_permissions()
    obj = User.get_by(login_id=u.login_id)
    assert u.id == obj.id

def test_user_get_by_email():
    u = create_user_with_permissions()
    obj = User.get_by_email(u.email_address)
    assert u.id == obj.id
    obj = User.get_by_email((u'%s'%u.email_address).upper())
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
    assert User.validate(u.login_id, u'bad_password') is None
    assert User.validate(u'bad_login', u'testpass123') is None
    assert User.validate(u.login_id, u'testpass123').id == u.id

def test_user_group_assignment():
    g1 = Group.add_iu(name=u'group_for_testing_%s'%randchars(15))
    g2 = Group.add_iu(name=u'group_for_testing_%s'%randchars(15))

    u = create_user_with_permissions()
    assert u.groups == []

    User.edit(u.id, assigned_groups=[g1.id,g2.id])
    assert len(u.groups) == 2
    assert len(g1.users) == len(g2.users) == 1

    User.edit(u.id, assigned_groups=g2.id)
    assert len(u.groups) == 1
    assert u.groups[0].id == g2.id

def test_inactive_property():
    user = create_user_with_permissions()

    user.inactive_flag = True

    assert user.inactive

    user.inactive_flag = False
    user.inactive_date = datetime.datetime(2050, 10, 10)

    assert not user.inactive

    user.inactive_date = datetime.datetime(2000, 10, 10)

    assert user.inactive

class TestPermissions(object):

    @classmethod
    def setup_class(cls):
        permissions = [
            'ugp_approved_grp', 'ugp_not_approved', 'ugp_denied_grp']

        for permission in permissions:
            Permission.add(name=unicode(permission))

        cls.user = create_user_with_permissions(u'ugp_approved', u'ugp_denied')
        cls.user2 = create_user_with_permissions(u'ugp_approved')
        cls.g1 = Group.add(name=u'ugp_g1')
        cls.g2 = Group.add(name=u'ugp_g2')
        Group.assign_permissions_by_name(u'ugp_g1', (u'ugp_approved_grp', u'ugp_denied', u'ugp_denied_grp'))
        Group.assign_permissions_by_name(u'ugp_g2', None, u'ugp_denied_grp')
        cls.user.groups.append(cls.g1)
        cls.user.groups.append(cls.g2)
        db.sess.commit()

        cls.perm_approved_grp = Permission.get_by(name=u'ugp_approved_grp')
        cls.perm_denied = Permission.get_by(name=u'ugp_denied')
        cls.perm_denied_grp = Permission.get_by(name=u'ugp_denied_grp')

    def test_user_get_by_permissions(self):

        # user directly approved
        users_approved = User.get_by_permissions(u'ugp_approved')
        assert users_approved[0] is self.user
        assert users_approved[1] is self.user2
        assert len(users_approved) == 2

        # user approved by group association
        assert User.get_by_permissions(u'ugp_approved_grp')[0] is self.user

        # user denial and group approval
        assert User.get_by_permissions(u'ugp_denied') == []

        # no approval
        assert User.get_by_permissions(u'ugp_not_approved') == []

        # approved by one group denied by another, denial takes precedence
        assert User.get_by_permissions(u'ugp_denied_grp') == []

    def test_user_permission_map_groups(self):
        # test group perms map
        perm_map = User.get(self.user.id).permission_map_groups

        assert not perm_map.has_key(Permission.get_by(name=u'ugp_approved').id)
        assert not perm_map.has_key(Permission.get_by(name=u'ugp_not_approved').id)

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
        perm_map = User.get(self.user.id).permission_map
        for rec in perm_map:
            assert rec['resulting_approval'] == (rec['permission_name'] in permissions_approved)

class TestAfterLoginUrl(object):
    def test_no_settings(self):
        settings.components.auth.after_login_url = None
        eq_('/', after_login_url())

    def test_with_function(self):
        settings.components.auth.after_login_url = lambda: '/foobar'
        eq_('/foobar', after_login_url())

    def test_with_string(self):
        settings.components.auth.after_login_url = '/foobar'
        eq_('/foobar', after_login_url())

    @inrequest('/thepage', 'http://example.com/script')
    def test_with_script_name(self):
        settings.components.auth.after_login_url = 'foobar'
        eq_('/script/foobar', after_login_url())
