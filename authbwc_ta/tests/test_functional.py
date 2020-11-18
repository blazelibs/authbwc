from blazeutils import randchars
from blazeweb.globals import ag
from blazeweb.testing import Client, TestApp
import datetime
import minimock
from nose.tools import eq_
import re
import smtplib
from werkzeug.wrappers import BaseResponse

from compstack.auth.lib.testing import login_client_with_permissions, \
    login_client_as_user, create_user_with_permissions
from compstack.auth.model.orm import User, Group, Permission
from compstack.sqlalchemy import db


class TestUserViews(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)
        perms = [u'auth-manage', u'users-test1', u'users-test2']
        cls.userid = login_client_with_permissions(cls.c, perms)

    def test_users_manage_paging(self):
        User.testing_create()
        User.testing_create()

        r = self.c.get('/users/manage?onpage=2&perpage=1')
        assert b'<h2>Manage Users</h2>' in r.data

    def test_users_manage_name_filter(self):
        u = User.testing_create()
        User.edit(u.id, name_first=u'Jack', name_last=u'Frost')
        r = self.c.get('/users/manage?op(name)=contains&v1(name)=Frost')
        assert b'<td>Jack Frost</td>' in r.data

    def test_groups_manage_paging(self):
        Group.testing_create()
        Group.testing_create()

        r = self.c.get('/groups/manage?onpage=2&perpage=1')
        assert b'<h2>Manage Groups</h2>' in r.data

    def test_permissions_manage_paging(self):
        x = Permission.testing_create()
        y = Permission.testing_create()

        r = self.c.get('/permissions/manage?onpage=2&perpage=1')

        db.sess.add(x)
        db.sess.add(y)
        Permission.delete(x.id)
        Permission.delete(y.id)

        assert b'<h2>Manage Permissions</h2>' in r.data

    def test_required_fields(self):
        topost = {
            'user-submit-flag': 'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Email: field is required' in r.data
        assert b'Login Id: field is required' in r.data

    def test_loginid_unique(self):
        user = User.get(self.userid)
        topost = {
            'login_id': user.login_id,
            'password': 'testtest',
            'email_address': 'test@example.com',
            'password-confirm': 'testtest',
            'user-submit-flag': 'submitted',
            'inactive_flag': False,
            'inactive_date': '',
            'name_first': '',
            'name_last': ''
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Login Id: that user already exists' in r.data

    def test_loginid_maxlength(self):
        topost = {
            'login_id': 'r' * 151,
            'email_address': 'test@example.com',
            'user-submit-flag': 'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert b'Login Id: Enter a value not greater than 150 characters long' in r.data, r.data

    def test_email_unique(self):
        user = User.get(self.userid)
        topost = {
            'login_id': 'newuser',
            'password': 'testtest',
            'email_address': user.email_address,
            'password-confirm': 'testtest',
            'email': 'test@exacmple.com',
            'user-submit-flag': 'submitted',
            'inactive_flag': False,
            'inactive_date': '',
            'name_first': '',
            'name_last': ''
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Email: a user with that email address already exists' in r.data

    def test_email_maxlength(self):
        topost = {
            'login_id': randchars(10),
            'email_address': ('r' * 140) + '@example.com',
            'user-submit-flag': 'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Email: Enter a value not greater than 150 characters long' in r.data

    def test_email_format(self):
        topost = {
            'email_address': 'test',
            'user-submit-flag': 'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Email: An email address must contain a single @' in r.data

    def test_bad_confirm(self):
        topost = {
            'login_id': 'newuser',
            'password': 'testtest',
            'email_address': 'abc@example.com',
            'password-confirm': 'nottests',
            'email': 'test@exacmple.com',
            'user-submit-flag': 'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Confirm Password: does not match field &#34;Password&#34;' in r.data

    def test_super_user_protection(self):
        r = self.c.get('users/add')
        assert b'name="super_user"' not in r.data

    def test_perms_legit(self):
        p = Permission.get_by(name=u'users-test1')
        perm = [str(p.id)]
        topost = {
            'login_id': 'newuser',
            'password': 'testtest',
            'email_address': 'abc@example.com',
            'password-confirm': 'testtest',
            'email': 'test@exacmple.com',
            'user-submit-flag': 'submitted',
            'approved_permissions': perm,
            'denied_permissions': perm
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Denied: you can not approve and deny the same permission' in r.data
        assert b'Approved: you can not approve and deny the same permission' in r.data

    def test_fields_saved(self):
        ap = Permission.get_by(name=u'users-test1').id
        dp = Permission.get_by(name=u'users-test2').id
        gp = Group.get_by(name=u'test-group') or Group.add_iu(
            name=u'test-group', approved_permissions=[], denied_permissions=[], assigned_users=[]
        )
        gp = gp.id
        topost = {
            'login_id': 'usersaved',
            'email_address': 'usersaved@example.com',
            'user-submit-flag': 'submitted',
            'approved_permissions': ap,
            'denied_permissions': dp,
            'assigned_groups': gp,
            'super_user': 1,
            'inactive_flag': False,
            'inactive_date': '10/11/2010',
            'name_first': 'test',
            'name_last': 'user',
            'email_notify': 1
        }

        # setup the mock objects so we can test the email getting sent out
        tt = minimock.TraceTracker()
        smtplib.SMTP = minimock.Mock('smtplib.SMTP', tracker=None)
        smtplib.SMTP.mock_returns = minimock.Mock('smtp_connection', tracker=tt)

        req, r = self.c.post('users/add', data=topost, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'User added' in r.data
        assert req.url.endswith('users/manage')

        mmdump = tt.dump()
        assert 'To: usersaved@example.com' in mmdump
        assert 'You have been added to our system of registered users.' in mmdump
        assert 'user name: usersaved' in mmdump
        assert re.search(r'password: [a-zA-Z0-9]*', mmdump) is not None
        assert re.search(r'password: None', mmdump) is None
        minimock.restore()

        user = User.get_by_email(u'usersaved@example.com')
        assert user.login_id == 'usersaved'
        assert user.reset_required
        assert not user.super_user
        assert user.pass_hash
        assert user.groups[0].name == 'test-group'
        assert len(user.groups) == 1
        assert user.inactive_date == datetime.datetime(2010, 10, 11), user.inactive_date
        assert user.name_first == 'test'
        assert user.name_last == 'user'

        found = 3
        for permrow in user.permission_map:
            if permrow['permission_name'] == u'users-test1':
                assert permrow['resulting_approval']
                found -= 1
            if permrow['permission_name'] in (u'users-test2', u'auth-manage'):
                assert not permrow['resulting_approval']
                found -= 1
        assert found == 0

        # now test an edit
        topost = {
            'login_id': 'usersaved',
            'email_address': 'usersaved@example.com',
            'user-submit-flag': 'submitted',
            'approved_permissions': dp,
            'denied_permissions': ap,
            'assigned_groups': None,
            'super_user': 1,
            'inactive_flag': False,
            'inactive_date': '10/10/2010',
            'name_first': 'test2',
            'name_last': 'user2',
            'email_notify': 1,
            'password': 'test_new_password',
            'password-confirm': 'test_new_password'
        }

        # setup the mock objects so we can test the email getting sent out
        tt = minimock.TraceTracker()
        smtplib.SMTP = minimock.Mock('smtplib.SMTP', tracker=None)
        smtplib.SMTP.mock_returns = minimock.Mock('smtp_connection', tracker=tt)

        req, r = self.c.post('users/edit/%s' % user.id, data=topost, follow_redirects=True)
        assert b'User edited successfully' in r.data
        assert req.url.endswith('users/manage')

        assert tt.check(
            'Called smtp_connection.sendmail(...usersaved@example.com...Your '
            'password for this site has been reset'
            '...first successful login...'
        )
        # restore the mocked objects
        minimock.restore()

        mmdump = tt.dump()
        assert 'To: usersaved@example.com' in mmdump
        assert 'Your password for this site has been reset by an administrator.' in mmdump
        assert 'user name: usersaved' in mmdump
        assert re.search(r'password: [a-zA-Z0-9]*', mmdump) is not None
        assert re.search(r'password: None', mmdump) is None
        minimock.restore()

        db.sess.expire(user)
        assert user.login_id == 'usersaved'
        assert user.reset_required
        assert not user.super_user
        assert user.pass_hash
        assert len(user.groups) == 0
        assert user.inactive_date == datetime.datetime(2010, 10, 10), user.inactive_date
        assert user.name_first == 'test2'
        assert user.name_last == 'user2'

        found = 3
        for permrow in user.permission_map:
            if permrow['permission_name'] == u'users-test2':
                assert permrow['resulting_approval']
                found -= 1
            if permrow['permission_name'] in (u'users-test1', u'auth-manage'):
                assert not permrow['resulting_approval']
                found -= 1
        assert found == 0

        # test edit w/ reset required and email notify (no email sent)
        topost = {
            'login_id': 'usersaved',
            'email_address': 'usersaved@example.com',
            'user-submit-flag': 'submitted',
            'approved_permissions': dp,
            'denied_permissions': ap,
            'assigned_groups': None,
            'super_user': 1,
            'reset_required': 1,
            'inactive_flag': False,
            'inactive_date': '',
            'name_first': '',
            'name_last': '',
            'email_notify': 1
        }
        req, r = self.c.post('users/edit/%s' % user.id, data=topost, follow_redirects=True)
        assert b'User edited successfully' in r.data
        assert req.url.endswith('users/manage')

        db.sess.expire(user)
        assert user.login_id == 'usersaved'
        assert user.reset_required
        assert not user.super_user
        assert user.pass_hash
        assert len(user.groups) == 0

        # now test a delete
        req, r = self.c.get('users/delete/%s' % user.id, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'User deleted' in r.data
        assert req.url.endswith('users/manage')

    def test_email_fail(self):
        userlogin = randchars(12)
        topost = {
            'login_id': userlogin,
            'email_address': '%s@example.com' % userlogin,
            'user-submit-flag': 'submitted',
            'approved_permissions': [],
            'denied_permissions': [],
            'assigned_groups': [],
            'super_user': 1,
            'inactive_flag': False,
            'inactive_date': '10/11/2010',
            'name_first': 'test',
            'name_last': 'user',
            'email_notify': 1
        }

        # cause an email exception
        smtp_orig = smtplib.SMTP
        smtplib.SMTP = None

        req, r = self.c.post('users/add', data=topost, follow_redirects=True)
        assert b'User added successfully' in r.data
        assert b'An error occurred while sending the user notification email.' in r.data
        assert req.url.endswith('users/manage')

        topost['password'] = 'new_password'
        topost['password-confirm'] = 'new_password'
        user = User.get_by_email('%s@example.com' % userlogin)

        req, r = self.c.post('users/edit/%s' % user.id, data=topost, follow_redirects=True)
        assert b'User edited successfully' in r.data, r.data
        assert b'An error occurred while sending the user notification email.' in r.data
        assert req.url.endswith('users/manage')

        smtplib.SMTP = smtp_orig

    def test_password_complexity(self):
        topost = {
            'login_id': 'newuser',
            'password': 't',
            'email_address': 'abc@example.com',
            'password-confirm': 't',
            'email': 'test@exacmple.com',
            'user-submit-flag': 'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Password: Enter a value at least 6 characters long' in r.data

        topost = {
            'login_id': 'newuser',
            'password': 't' * 26,
            'email_address': 'abc@example.com',
            'password-confirm': 't' * 26,
            'email': 'test@exacmple.com',
            'user-submit-flag': 'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert b'Password: Enter a value less than 25 characters long' in r.data

    def test_same_user_delete(self):
        resp, r = self.c.get('users/delete/%s' % self.userid, follow_redirects=True)
        assert r.status_code == 403, r.status
        assert b'You cannot delete your own user account' in r.data
        assert resp.url.endswith('users/delete/%s' % self.userid)

    def test_non_existing_id(self):
        non_existing_id = 9999
        while User.get(non_existing_id):
            non_existing_id += 1000
        req, resp = self.c.get('users/edit/%s' % non_existing_id, follow_redirects=True)
        assert req.url.endswith('/users/edit/%s' % non_existing_id), req.url
        assert resp.status_code == 404, resp.status
        req, resp = self.c.get('users/delete/%s' % non_existing_id, follow_redirects=True)
        assert req.url.endswith('users/delete/%s' % non_existing_id), req.url
        assert resp.status_code == 404, resp.status

    def test_no_email_notify(self):
        topost = {
            'login_id': 'usersaved_noemailnotify',
            'email_address': 'usersaved_noemailnotify@example.com',
            'user-submit-flag': 'submitted',
            'approved_permissions': None,
            'denied_permissions': None,
            'assigned_groups': None,
            'super_user': 1,
            'inactive_flag': False,
            'inactive_date': '10/11/2010',
            'name_first': 'test',
            'name_last': 'user'
        }

        # setup the mock objects so we can test the email getting sent out
        tt = minimock.TraceTracker()
        smtplib.SMTP = minimock.Mock('smtplib.SMTP', tracker=None)
        smtplib.SMTP.mock_returns = minimock.Mock('smtp_connection', tracker=tt)

        req, r = self.c.post('users/add', data=topost, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'User added' in r.data
        assert req.url.endswith('users/manage')

        assert len(tt.dump()) == 0
        minimock.restore()

    def test_super_edit_forbidden(self):
        u = create_user_with_permissions(super_user=True)
        r = self.c.get('users/edit/%s' % u.id)
        assert r.status_code == 403, r.status


class TestUserProfileView(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)
        cls.userid = login_client_with_permissions(cls.c, u'prof-test-1', u'prof-test-2')
        cls.userid2 = create_user_with_permissions().id

    def get_to_post(self):
        user = User.get(self.userid)
        topost = {
            'name_first': 'usersfirstname',
            'name_last': 'userslastname',
            'login_id': user.login_id,
            'email_address': user.email_address,
            'user-profile-form-submit-flag': 'submitted'
        }
        return topost

    def test_fields_load(self):
        """ make sure fields load with data currently in db """
        r = self.c.get('users/profile')
        assert r.status_code == 200, r.status
        user = User.get(self.userid)
        assert user.email_address.encode() in r.data
        assert user.login_id.encode() in r.data

        r = self.c.post('users/profile', data=self.get_to_post())
        assert r.status_code == 200, r.status
        user = User.get(self.userid)
        assert user.email_address.encode() in r.data
        assert user.login_id.encode() in r.data
        assert b'usersfirstname' in r.data
        assert b'userslastname' in r.data
        assert b'profile updated succesfully' in r.data

    def test_required_fields(self):
        topost = self.get_to_post()
        topost['email_address'] = None
        r = self.c.post('users/profile', data=topost)
        assert r.status_code == 200, r.status
        assert b'Email: field is required' in r.data

        topost = self.get_to_post()
        topost['login_id'] = None
        r = self.c.post('users/profile', data=topost)
        assert r.status_code == 200, r.status
        assert b'Login Id: field is required' in r.data

    def test_password_confirm(self):
        topost = self.get_to_post()
        topost['password'] = 'newpass'
        topost['password-confirm'] = 'nomatch'
        r = self.c.post('users/profile', data=topost)
        assert r.status_code == 200, r.status
        assert b'Confirm Password: does not match field &#34;Password&#34;' in r.data, r.data

    def test_email_dups(self):
        user2 = User.get(self.userid2)
        topost = self.get_to_post()
        topost['email_address'] = user2.email_address
        r = self.c.post('users/profile', data=topost)
        assert r.status_code == 200, r.status
        assert b'Email: a user with that email address already exists' in r.data

    def test_login_id_dups(self):
        user2 = User.get(self.userid2)
        topost = self.get_to_post()
        topost['login_id'] = user2.login_id
        r = self.c.post('users/profile', data=topost)
        assert r.status_code == 200, r.status
        assert b'Login Id: that user already exists' in r.data

    def test_cancel(self):
        topost = self.get_to_post()
        topost['cancel'] = 'submitted'
        req, r = self.c.post('users/profile', data=topost, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'no changes made to your profile' in r.data
        assert req.url == 'http://localhost/'

    def test_password_changes(self):
        user = User.get(self.userid)
        pass_hash = user.pass_hash

        r = self.c.post('users/profile', data=self.get_to_post())
        assert r.status_code == 200, r.status
        user = User.get(self.userid)
        assert user.pass_hash == pass_hash

        topost = self.get_to_post()
        topost['password'] = 'newpass'
        topost['password-confirm'] = 'newpass'
        r = self.c.post('users/profile', data=topost)
        assert r.status_code == 200, r.status
        db.sess.expire(user)
        assert user.pass_hash != pass_hash

    def test_perm_changes(self):
        p1 = Permission.get_by(name=u'prof-test-1').id
        p2 = Permission.get_by(name=u'prof-test-2').id

        # add user to group
        user = User.get(self.userid)
        gp = Group.add_iu(name=u'test-group', approved_permissions=[], denied_permissions=[],
                          assigned_users=[user.id]).id

        r = self.c.post('users/profile', data=self.get_to_post())
        assert r.status_code == 200, r.status
        user = User.get(self.userid)
        approved, denied = user.assigned_permission_ids
        assert p1 in approved
        assert p2 in denied
        assert gp in [g.id for g in user.groups]

    def test_no_super_delete(self):
        su = create_user_with_permissions(super_user=True)
        r = self.c.get('users/delete/%s' % su.id)
        assert r.status_code == 403, r.status

    def test_no_super_edit(self):
        su = create_user_with_permissions(super_user=True)
        r = self.c.get('users/edit/%s' % su.id)
        assert r.status_code == 403, r.status


class TestUserViewsSuperUser(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)
        perms = [u'auth-manage', u'users-test1', u'users-test2']
        cls.userid = login_client_with_permissions(cls.c, perms, super_user=True)

    def test_super_user_protection(self):
        r = self.c.get('users/add')
        assert b'name="super_user"' in r.data

    def test_fields_saved(self):
        ap = Permission.get_by(name=u'users-test1').id
        dp = Permission.get_by(name=u'users-test2').id
        gp = Group.get_by(name=u'test-group') or Group.add_iu(
            name=u'test-group', approved_permissions=[], denied_permissions=[], assigned_users=[]
        )
        gp = gp.id
        topost = {
            'login_id': 'usersavedsu',
            'password': 'testtest',
            'email_address': 'usersavedsu@example.com',
            'password-confirm': 'testtest',
            'email': 'test@exacmple.com',
            'user-submit-flag': 'submitted',
            'approved_permissions': ap,
            'denied_permissions': dp,
            'assigned_groups': gp,
            'super_user': 1,
            'inactive_flag': False,
            'inactive_date': '',
            'name_first': '',
            'name_last': ''
        }
        req, r = self.c.post('users/add', data=topost, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'User added' in r.data
        assert req.url.endswith('users/manage')

        user = User.get_by_email(u'usersavedsu@example.com')
        assert user.login_id == 'usersavedsu'
        assert user.reset_required
        assert user.super_user
        assert user.pass_hash
        assert user.groups[0].name == 'test-group'
        assert len(user.groups) == 1

        found = 3
        for permrow in user.permission_map:
            if permrow['permission_name'] == u'users-test1':
                assert permrow['resulting_approval']
                found -= 1
            if permrow['permission_name'] in (u'users-test2', u'auth-manage'):
                assert not permrow['resulting_approval']
                found -= 1
        assert found == 0

    def test_super_edit(self):
        su = create_user_with_permissions(super_user=True)
        r = self.c.get('users/edit/%s' % su.id)
        assert r.status_code == 200, r.status
        assert b'Edit User' in r.data

    def test_super_delete(self):
        su = create_user_with_permissions(super_user=True)
        req, r = self.c.get('users/delete/%s' % su.id, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'User deleted' in r.data
        assert req.url.endswith('users/manage')


class TestUserLogins(object):

    def setUp(self):
        # create a user
        self.user = create_user_with_permissions()

    def test_failed_login(self):
        user = self.user

        client = Client(ag.wsgi_test_app, BaseResponse)
        topost = {
            'login_id': user.login_id,
            'password': 'foobar',
            'login-form-submit-flag': '1'
        }
        resp = client.post('users/login', data=topost)
        assert resp.status_code == 200, resp.status
        assert b'Login failed!' in resp.data

    def test_inactive_login(self):
        user = self.user
        # set the user's inactive flag
        user.inactive_flag = True
        db.sess.commit()

        # log user in
        client = Client(ag.wsgi_test_app, BaseResponse)
        topost = {
            'login_id': user.login_id,
            'password': user.text_password,
            'login-form-submit-flag': '1'
        }
        req, resp = client.post('users/login', data=topost, follow_redirects=True)
        assert resp.status_code == 200, resp.status
        assert b'That user is inactive.' in resp.data
        assert req.url == 'http://localhost/users/login'

    def test_cleared_login(self):
        super_user = create_user_with_permissions(super_user=True)
        ta = TestApp(ag.wsgi_test_app)
        topost = {
            'login_id': super_user.login_id,
            'password': super_user.text_password,
            'login-form-submit-flag': '1'
        }
        r = ta.post('/users/login', topost)
        assert 'auth-manage' in r.user.perms

        user = create_user_with_permissions()
        topost = {
            'login_id': user.login_id,
            'password': user.text_password,
            'login-form-submit-flag': '1'
        }
        r = ta.post('/users/login', topost)
        assert len(r.user.perms) == 0


class TestRecoverPassword(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)

    def test_invalid_user(self):

        topost = {
            'email_address': u'user@notreallythere.com',
            'lost-password-form-submit-flag': 'submitted',
        }
        r = self.c.post('users/recover-password', data=topost)
        assert r.status_code == 200, r.status
        assert b'email address is not associated with a user' in r.data

    def test_inactive_user(self):

        user = create_user_with_permissions()
        user.inactive_flag = True
        db.sess.commit()

        topost = {
            'email_address': user.email_address,
            'lost-password-form-submit-flag': 'submitted',
        }
        r = self.c.post('users/recover-password', data=topost)
        assert r.status_code == 200, r.status
        assert b'Did not find a user with email address:' in r.data

    def test_invalid_reset_link(self):

        req, resp = self.c.get('users/reset-password/nothere/invalidkey', follow_redirects=True)
        assert resp.status_code == 200, resp.status
        assert b'Recover Password' in resp.data
        assert b'invalid reset request, use the form below to resend reset link' in resp.data
        assert req.url.endswith('users/recover-password')

    def test_password_reset(self):
        """ has to be done in the same test function so that order is assured"""

        user = create_user_with_permissions()

        r = self.c.get('users/recover-password')
        assert r.status_code == 200, r.status
        assert b'Recover Password' in r.data

        # setup the mock objects so we can test the email getting sent out
        tt = minimock.TraceTracker()
        smtplib.SMTP = minimock.Mock('smtplib.SMTP', tracker=None)
        smtplib.SMTP.mock_returns = minimock.Mock('smtp_connection', tracker=tt)

        # test posting to the restore password view
        db.sess.expire(user)
        topost = {
            'email_address': user.email_address,
            'lost-password-form-submit-flag': 'submitted',
        }
        req, r = self.c.post('users/recover-password', data=topost, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'email with a link to reset your password has been sent' in r.data, r.data
        assert req.url == 'http://localhost/'

        # test the mock strings (i.e. test the email that was sent out)
        db.sess.expire(user)
        assert tt.check('Called smtp_connection.sendmail(...%s...has been issu'
                        'ed to reset the password...' % user.email_address)
        # restore the mocked objects
        minimock.restore()

        # now test resetting the password
        r = self.c.get('/users/reset-password/%s/%s' % (user.login_id, user.pass_reset_key))
        assert r.status_code == 200, r.status_code
        assert b'Reset Password' in r.data
        assert b'Please choose a new password to complete the reset request' in r.data

        # expire the date
        db.sess.expire(user)
        orig_reset_ts = user.pass_reset_ts
        user.pass_reset_ts = datetime.datetime(2000, 10, 10)
        db.sess.commit()

        # check expired message
        req, resp = self.c.get('/users/reset-password/%s/%s' % (user.login_id, user.pass_reset_key),
                               follow_redirects=True)
        assert resp.status_code == 200, resp.status
        assert b'Recover Password' in resp.data
        assert b'password reset link expired, use the form below to resend reset link' in resp.data
        assert req.url.endswith('users/recover-password')

        # unexpire the date
        db.sess.expire(user)
        user.pass_reset_ts = orig_reset_ts
        db.sess.commit()

        # check posting the new passwords
        topost = {
            'password': 'TestPassword2',
            'password-confirm': 'TestPassword2',
            'new-password-form-submit-flag': 'submitted',
        }
        req, r = self.c.post('/users/reset-password/%s/%s' % (user.login_id, user.pass_reset_key),
                             data=topost, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert b'Your password has been reset successfully' in r.data
        assert req.url == 'http://localhost/'


class TestGroupViews(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)
        perms = [u'auth-manage', u'users-test1', u'users-test2']
        cls.userid = login_client_with_permissions(cls.c, perms)

    def test_not_losing_inactives(self):
        u1 = User.testing_create()
        u2 = User.testing_create()
        u2.inactive_flag = True

        g = Group.testing_create()
        g.users = [u2]
        db.sess.commit()

        topost = {
            'approved_permissions': [],
            'assigned_users': [u1.id],
            'denied_permissions': [],
            'group-submit-flag': u'submitted',
            'name': g.name,
            'submit': u'Submit'
        }
        req, resp = self.c.post('groups/edit/{0}'.format(g.id), data=topost,
                                follow_redirects=True)
        assert resp.status_code == 200, resp.status
        assert '/groups/manage' in req.url, req.url

        db.sess.expire(g)
        eq_(len(g.users), 2)
        assert u1 in g.users
        assert u2 in g.users

    def test_required_fields(self):
        topost = {
            'group-submit-flag': 'submitted'
        }
        req, resp = self.c.post('groups/add', data=topost, follow_redirects=True)
        assert resp.status_code == 200, resp.status
        assert b'Group Name: field is required' in resp.data

    def test_group_name_unique(self):
        topost = {
            'approved_permissions': [],
            'assigned_users': [],
            'denied_permissions': [],
            'group-submit-flag': u'submitted',
            'name': u'test_group_name_unique',
            'submit': u'Submit'
        }
        req, resp = self.c.post('groups/add', data=topost, follow_redirects=True)
        assert resp.status_code == 200, resp.status
        assert '/groups/manage' in req.url, req.url
        assert b'Group added successfully' in resp.data

        topost = {
            'approved_permissions': [],
            'assigned_users': [],
            'denied_permissions': [],
            'group-submit-flag': u'submitted',
            'name': u'test_group_name_unique',
            'submit': u'Submit'
        }
        resp = self.c.post('groups/add', data=topost)
        assert resp.status_code == 200, resp.status
        assert b'Group Name: the value for this field is not unique' in resp.data


class TestPasswordResetRequired(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag.wsgi_test_app, BaseResponse)
        cls.user = create_user_with_permissions()
        cls.user.reset_required = True
        db.sess.commit()
        cls.userid = login_client_as_user(cls.c, cls.user.login_id, cls.user.text_password,
                                          validate_login_response=False)

    def test_reset_required(self):
        req, resp = self.c.get('/users/profile', follow_redirects=True)
        assert '/users/profile' in req.url
        assert b'<h1>Change Password</h1>' in resp.data

        topost = {
            'change-password-form-submit-flag': u'submitted',
            'old_password': self.user.text_password,
            'password': '%s123' % self.user.text_password,
            'password-confirm': '%s123' % self.user.text_password,
            'submit': u'Submit'
        }
        req, resp = self.c.post('/users/profile', data=topost, follow_redirects=True)
        assert '/users/profile' in req.url
        assert b'<h1>Change Password</h1>' not in resp.data, resp.data


class TestPermissionMap(object):

    @classmethod
    def setup_class(cls):
        cls.userid = User.testing_create().id
        cls.tam = TestApp(ag.wsgi_test_app)
        login_client_with_permissions(cls.tam, [u'auth-manage'])

    def test_anonymous(self):
        ta = TestApp(ag.wsgi_test_app)
        ta.get('/users/permissions/{0}'.format(self.userid), status=401)

    def test_unauthorized(self):
        ta = TestApp(ag.wsgi_test_app)
        login_client_with_permissions(ta)
        ta.get('/users/permissions/{0}'.format(self.userid), status=403)

    def test_page_load(self):
        resp = self.tam.get('/users/permissions/{0}'.format(self.userid))
        assert '<h1>Permissions for: ' in resp
        assert '/users/edit/{0}'.format(self.userid) in resp
        assert '<table class="datagrid"' in resp

    def test_no_exc_with_group_permissions(self):
        g = Group.testing_create()
        ap = Permission.testing_create()
        dp = Permission.testing_create()
        g.assign_permissions([ap.id], [dp.id])
        u = User.testing_create(groups=g)

        resp = self.tam.get('/users/permissions/{0}'.format(u.id))
        assert b'<h1>Permissions for: ' in resp

        d = resp.pyq
        db.sess.add(g)
        assert str(d('td.approved a[href="/groups/edit/{0}"]'.format(g.id)))
        assert str(d('td.denied a[href="/groups/edit/{0}"]'.format(g.id)))

    def test_no_exc_with_user_permissions(self):
        u = User.testing_create()
        ap = Permission.testing_create()
        dp = Permission.testing_create()
        u.assign_permissions([ap.id], [dp.id])
        db.sess.commit()

        resp = self.tam.get('/users/permissions/{0}'.format(u.id))
        assert b'<h1>Permissions for: ' in resp

        d = resp.pyq
        assert str(d('td.approved a[href="/users/edit/{0}"]'.format(u.id)))
        assert str(d('td.denied a[href="/users/edit/{0}"]'.format(u.id)))
