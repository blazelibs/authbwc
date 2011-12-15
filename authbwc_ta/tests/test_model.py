from nose.tools import eq_

from authbwc.model.orm import User, Permission, Group
from authbwc.model.metadata import user_permission_assignments as upa, \
    user_groups as tbl_ugm
from compstack.sqlalchemy import db

class TestUser(object):
    @classmethod
    def setup_class(self):
        Permission.delete_all()
        Permission.add(name=u'ugp_approved')
        Permission.add(name=u'ugp_denied')
        Permission.add(name=u'users-test1')
        Permission.add(name=u'users-test2')
        Permission.add(name=u'prof-test-1')
        Permission.add(name=u'prof-test-2')
        Permission.add(name=u'auth-manage')

    def setUp(self):
        User.delete_all()
        Group.delete_all()

    def test_permission_dict(self):
        u = User.testing_create()
        expect = {u'auth-manage': False, u'prof-test-2': False,
            u'ugp_approved': False, u'ugp_denied': False, u'users-test1': False,
            u'users-test2': False, u'prof-test-1': False}
        eq_(u.permission_dict(), expect)

        # with SU
        u.super_user = True
        expect = {u'auth-manage': True, u'prof-test-2': True,
            u'ugp_approved': True, u'ugp_denied': True, u'users-test1': True,
            u'users-test2': True, u'prof-test-1': True}
        eq_(u.permission_dict(), expect)

        # with SU but override off
        expect = {u'auth-manage': False, u'prof-test-2': False,
            u'ugp_approved': False, u'ugp_denied': False, u'users-test1': False,
            u'users-test2': False, u'prof-test-1': False}
        eq_(u.permission_dict(su_override=False), expect)

    def test_has_perm(self):
        u = User.testing_create()
        p = Permission.get_by(name=u'auth-manage')
        p2 = Permission.get_by(name=u'prof-test-1')
        eq_(u.has_permission(u'auth-manage'), False)

        # approve it
        u.assign_permissions([p.id, p2.id], [])

        # single permission approved
        eq_(u.has_permission(u'auth-manage'), True)

        # double permission approved
        eq_(u.has_permission(u'auth-manage', u'prof-test-1'), True)

        # one approved, one absent
        eq_(u.has_permission(u'auth-manage', u'foobar'), False)

        # one approved, one denied
        eq_(u.has_permission(u'auth-manage', u'ugp_denied'), False)

        # one approved with super user
        u.super_user = True
        eq_(u.has_permission(u'ugp_denied'), True)

        # discount super user
        eq_(u.has_permission(u'ugp_denied', su_override=False), False)

    def test_testing_create_args(self):
        u = User.testing_create(loginid = u'foobar')
        eq_(u.login_id, u'foobar')
        eq_(u.email_address, u'foobar@example.com')
        eq_(u.reset_required, False)

    def test_testing_create_perms(self):
        # approved perms
        u = User.testing_create(approved_perms=[u'auth-manage', u'prof-test-1'])
        eq_(u.has_permission(u'auth-manage', u'prof-test-1'), True)

        # non-list usage
        u = User.testing_create(approved_perms=u'auth-manage', denied_perms=u'prof-test-1')
        eq_(u.has_permission(u'auth-manage'), True)
        eq_(u.has_permission(u'prof-test-1'), False)

        # make sure deny permission is there, not False above b/c its not mapped
        perm_count = db.sess.query(upa.c.id).filter(upa.c.user_id == u.id).count()
        eq_(perm_count, 2)

    def test_user_delete_doesnt_delete_group(self):
        # create group and make sure count logic works
        g1 = Group.testing_create()
        g1_id = g1.id
        eq_(Group.count_by(id=g1_id), 1)

        # create user assigned to group
        u = User.testing_create(groups=g1)

        # delete user
        User.delete(u.id)

        # group should still be there
        eq_(Group.count_by(id=g1_id), 1)

    def test_ugmap_fk(self):
        g = Group.testing_create()
        u = User.testing_create(groups=g)
        uid = u.id

        eq_(db.sess.query(tbl_ugm).count(), 1)

        # delete the user with delete_where() because .delete() loads the ORM
        # object and then calls <session>.delete().  That method will trigger SA
        # to issue a DELETE statement on the map table. Therefore, using
        # .delete() would allow this test to pass even if our FK was not
        # configured correctly.
        User.delete_where(User.id==uid)

        # shouldn't be any mappings left
        eq_(db.sess.query(tbl_ugm).count(), 0)

class TestGroups(object):

    def setUp(self):
        User.delete_all()
        Group.delete_all()

    def test_group_delete(self):
        g1 = Group.testing_create()
        g2 = Group.testing_create()

        u = User.testing_create(groups=[g1,g2])
        eq_(len(u.groups), 2)

        assert Group.delete(g1.id)
        eq_(len(g2.users), 1)
        eq_(len(u.groups), 1)
        eq_(u.groups[0].id, g2.id)
        eq_(Group.count(), 1)

    def test_group_delete_doesnt_affect_user(self):
        # create group
        g1 = Group.testing_create()

        # create user assigned to group and make sure count logic works
        u = User.testing_create(groups=g1)
        u1_id = u.id
        eq_(User.count_by(id=u1_id), 1)

        # delete group
        Group.delete(g1.id)

        # user should still be there
        eq_(User.count_by(id=u1_id), 1)

    def test_ugmap_fk(self):
        g = Group.testing_create()
        gid = g.id
        u = User.testing_create(groups=g)

        eq_(db.sess.query(tbl_ugm).count(), 1)

        # delete the group with delete_where() because .delete() loads the ORM
        # object and then calls <session>.delete().  That method will trigger SA
        # to issue a DELETE statement on the map table. Therefore, using
        # .delete() would allow this test to pass even if our FK was not
        # configured correctly.
        Group.delete_where(Group.id==gid)

        # shouldn't be any mappings left
        eq_(db.sess.query(tbl_ugm).count(), 0)
