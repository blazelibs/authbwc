from pysmvt import modimportauto, ag
from werkzeug import Client, BaseResponse, BaseRequest

modimportauto('users.testing', ['login_client_with_permissions'])
modimportauto('users.actions', ['user_get', 'permission_get_by_name',
    'user_get_by_email', 'group_add', 'user_permission_map'])
            
class TestUserViews(object):

    @classmethod
    def setup_class(cls):
        cls.c = Client(ag._wsgi_test_app, BaseResponse)
        perms = [u'users-manage', u'users-test1', u'users-test2']
        cls.userid = login_client_with_permissions(cls.c, perms)
        
    def test_required_fields(self):
        topost = {
          'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Email: field is required' in r.data
        assert 'Confirm Password: field is required' in r.data
        assert 'Password: field is required' in r.data
        assert 'Login Id: field is required' in r.data
        
    def test_loginid_unique(self):
        user = user_get(self.userid)
        topost = {
            'login_id': user.login_id,
            'password': 'testtest',
            'email_address': 'test@example.com',
            'password-confirm': 'testtest',
            'email': 'test@exacmple.com',
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Login Id: That user already exists' in r.data
        
    def test_loginid_maxlength(self):
        topost = {
            'login_id': 'r'*151,
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert 'Login Id: Enter a value less than 150 characters long' in r.data
    
    def test_email_unique(self):
        user = user_get(self.userid)
        topost = {
            'login_id': 'newuser',
            'password': 'testtest',
            'email_address': user.email_address,
            'password-confirm': 'testtest',
            'email': 'test@exacmple.com',
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Email: A user with that email address already exists' in r.data
    
    def test_email_maxlength(self):
        topost = {
            'email_address': 'r'*151,
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Email: Enter a value less than 150 characters long' in r.data
    
    def test_email_format(self):
        topost = {
            'email_address': 'test',
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Email: An email address must contain a single @' in r.data
        
    def test_bad_confirm(self):
        topost = {
            'login_id': 'newuser',
            'password': 'testtest',
            'email_address': 'abc@example.com',
            'password-confirm': 'nottests',
            'email': 'test@exacmple.com',
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Confirm Password: does not match field "Password"' in r.data
    
    def test_super_user_protection(self):
        r = self.c.get('users/add')
        assert 'name="super_user"' not in r.data
    
    def test_perms_legit(self):
        p = permission_get_by_name(u'users-test1')
        perm = [str(p.id)]
        topost = {
            'login_id': 'newuser',
            'password': 'testtest',
            'email_address': 'abc@example.com',
            'password-confirm': 'testtest',
            'email': 'test@exacmple.com',
            'user-form-submit-flag':'submitted',
            'approved_permissions': perm,
            'denied_permissions': perm
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Denied: you can not approve and deny the same permission' in r.data
        assert 'Approved: you can not approve and deny the same permission' in r.data
    
    def test_fields_saved(self):
        ap = permission_get_by_name(u'users-test1').id
        dp = permission_get_by_name(u'users-test2').id
        gp = group_add(name=u'test-group', approved_permissions=[],
                      denied_permissions=[], assigned_users=[], safe='unique').id
        topost = {
            'login_id': 'usersaved',
            'password': 'testtest',
            'email_address': 'usersaved@example.com',
            'password-confirm': 'testtest',
            'email': 'test@exacmple.com',
            'user-form-submit-flag':'submitted',
            'approved_permissions': ap,
            'denied_permissions': dp,
            'assigned_groups': gp
        }
        r = self.c.post('users/add', data=topost, follow_redirects=True)
        assert r.status_code == 200, r.status
        assert 'user added' in r.data
        
        user = user_get_by_email(u'usersaved@example.com')
        assert user.login_id == 'usersaved'
        assert user.reset_required
        assert not user.super_user
        assert user.pass_hash
        assert user.groups[0].name == 'test-group'
        assert len(user.groups) == 1
        
        found = 3
        for permrow in user_permission_map(user.id):
            if permrow['permission_name'] == u'users-test1':
                assert permrow['resulting_approval']
                found -= 1
            if permrow['permission_name'] in (u'users-test2', u'users-manage'):
                assert not permrow['resulting_approval']
                found -= 1
        assert found == 0
    
    def test_password_complexity(self):
        topost = {
            'login_id': 'newuser',
            'password': 't',
            'email_address': 'abc@example.com',
            'password-confirm': 't',
            'email': 'test@exacmple.com',
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Password: Enter a value at least 6 characters long' in r.data
        
        topost = {
            'login_id': 'newuser',
            'password': 't'*26,
            'email_address': 'abc@example.com',
            'password-confirm': 't'*26,
            'email': 'test@exacmple.com',
            'user-form-submit-flag':'submitted'
        }
        r = self.c.post('users/add', data=topost)
        assert r.status_code == 200, r.status
        assert 'Password: Enter a value less than 25 characters long' in r.data