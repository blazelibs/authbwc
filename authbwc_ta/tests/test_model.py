from nose.tools import eq_

from authbwc.model.orm import User, Permission

class TestUser(object):

    def test_permission_dict(self):
        u = User.test_create()
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
        u = User.test_create()
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
