from pysapp.forms import Form
from pysmvt import user
from pysmvt.routing import url_for
from pysmvt.utils import toset
from formencode.validators import MaxLength, MinLength
from pysform.exceptions import ValueInvalid
from actions import group_list_options, user_list_options, permission_list_options, user_get, hash_pass, user_get_by_email

class UserForm(Form):
        
    def __init__(self, isAdd):
        Form.__init__(self, 'user-form')
        
        el = self.add_text('login_id', 'Login Id', required=True)
        el.add_processor(MaxLength(150))
        el.add_handler('column login_id is not unique',
                 'That user already exists.')
        
        el = self.add_email('email_address', 'Email', required=True)
        el.add_processor(MaxLength(150))
        el.add_handler('column email_address is not unique',
                 'A user with that email address already exists.')
        
        el = self.add_password('password', 'Password', required=isAdd)
        el.add_processor(MaxLength(25))
        el.add_processor(MinLength(6))
        el.add_note('password will change only if you enter a value above')
        
        el = self.add_password('password-confirm', 'Confirm Password', required=isAdd)
        el.add_processor(MaxLength(25))
        
        el = self.add_checkbox('reset_required', 'Password Reset Required')
        el.add_note("force the user to change their password the next time they login")
        el.add_note("is set automatically if an administrator changes a password")
        
        # if the current user is not a super user, they can't set the super user
        # field
        if user.get_attr('super_user'):
            el = self.add_checkbox('super_user', 'Super User')
            el.add_note("super users will have all permissions automatically")
        
        el = self.add_checkbox('email_notify', 'Email Notification', checked=True)
        el.add_note("send notification email on password change or new user creation")
        el.add_note("forces password reset if password is sent out in an email")
        
        el = self.add_header('group_membership_header', 'Group Membership')
        
        group_opts = group_list_options()
        el = self.add_mselect('assigned_groups', group_opts, 'Assign to')
        
        el = self.add_header('group_permissions_header', 'User Permissions')
        
        perm_opts = permission_list_options()
        el = self.add_mselect('approved_permissions', perm_opts, 'Approved')
        el = self.add_mselect('denied_permissions', perm_opts, 'Denied')

        self.add_submit('submit')
        self.add_validator(self.validate_perms)
    
    def validate_perms(self, value):
        assigned = toset(self.approved_permissions.value)
        denied = toset(self.denied_permissions.value)

        if len(assigned.intersection(denied)) != 0:
            msg = 'you can not approve and deny the same permission'
            self.denied_permissions.add_error(msg)
            self.approved_permissions.add_error(msg)
            raise ValueInvalid()

class GroupForm(Form):
        
    def __init__(self, isAdd):
        Form.__init__(self, 'group-form')
        
        el = self.add_text('name', 'Group Name', required=True)
        el.add_processor(MaxLength(150))
        el.add_handler('column name is not unique',
                 'That group already exists.')
        
        el = self.add_header('group_membership_header', 'Users In Group')
        
        user_opts = user_list_options()
        el = self.add_mselect('assigned_users', user_opts, 'Assign')

        el = self.add_header('group_permissions_header', 'Group Permissions')
        
        perm_opts = permission_list_options()
        el = self.add_mselect('approved_permissions', perm_opts, 'Approved')
        
        el = self.add_mselect('denied_permissions', perm_opts, 'Denied')
        self.add_submit('submit')
        
        self.add_validator(self.validate_perms)
        
    def validate_perms(self, value):
        assigned = toset(self.approved_permissions.value)
        denied = toset(self.denied_permissions.value)
        
        if len(assigned.intersection(denied)) != 0:
            raise ValueInvalid('you can not approve and deny the same permission')

class PermissionForm(Form):
        
    def __init__(self, isAdd):
        Form.__init__(self, 'permission-form')
        
        el = self.add_text('name', 'Permission Name', required=True)
        el.add_processor(MaxLength(150))
        el.add_handler('column name is not unique',
                 'That permission already exists.')

        self.add_submit('submit')
        
class LoginForm(Form):
            
    def __init__(self):
        Form.__init__(self, 'login-form')
        
        el = self.add_text('login_id', 'Login Id', required=True)
        el.add_processor(MaxLength(150))
        
        el = self.add_password('password', 'Password', required=True)
        el.add_processor(MaxLength(25))

        self.add_submit('submit')

class ChangePasswordForm(Form):

    def __init__(self):
        Form.__init__(self, 'login-form')

        el = self.add_password('old_password', 'Old Password', required=True)
        el.add_processor(MaxLength(25))
        el.add_processor(self.validate_password)

        el = self.add_password('password', 'New Password', required=True)
        el.add_processor(MaxLength(25))
        el.add_processor(MinLength(6))
        
        el = self.add_password('confirm_password', 'Confirm', required=True)
        el.add_processor(MaxLength(25))
        el.add_processor(MinLength(6))

        self.add_submit('submit')
        self.add_validator(self.validate_validnew)
        self.add_validator(self.validate_confirm)
        
    def validate_password(self, value):
        dbobj = user_get(user.get_attr('id'))
        if dbobj.pass_hash != hash_pass(value):
            raise ValueInvalid('incorrect password')
            
        return value

    def validate_confirm(self, form):
        if form.confirm_password.value != form.password.value:
            err = 'did not match password'
            form.confirm_password.add_error(err)
            raise ValueInvalid()

    def validate_validnew(self, form):
        if form.password.value == form.old_password.value:
            err = 'password must be different from the old password'
            form.password.add_error(err)
            raise ValueInvalid()

class LostPasswordForm(Form):

    def __init__(self):
        Form.__init__(self, 'lost-password-form')

        el = self.add_email('email_address', 'Email', required=True)
        el.add_processor(MaxLength(150))
        el.add_processor(self.validate_email)

        self.add_submit('submit')

    def validate_email(self, value):
        dbobj = user_get_by_email(value)
        if (dbobj is None):
            raise ValueInvalid('email address is not associated with a user')

        return value
