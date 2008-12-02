from pyhtmlquickform.form import Form
from pysmvt import user, rg
from pysmvt.routing import url_for
from pysmvt.utils import toset
from formencode.validators import Email, MaxLength, MinLength
from pyhtmlquickform.validators import Select
from actions import group_list_options, user_list_options, permission_list_options, user_get, hash_pass

class UserForm(Form):
        
    def __init__(self, isAdd):
        Form.__init__(self, 'user-form', class_='generated')
        
        el = self.addElement('text', 'login_id', 'Login Id', required=True)
        el.addValidator(MaxLength(150))
        
        el = self.addElement('text', 'email_address', 'Email', required=True)
        el.addValidator(MaxLength(150))
        el.addValidator(Email(), 'email address is not formatted correctly')
        
        el = self.addElement('password', 'password', 'Password', required=isAdd)
        el.addValidator(MaxLength(25))
        el.addValidator(MinLength(6))
        el.addNote('password will change only if you enter a value above')
        
        el = self.addElement('password', 'password-confirm', 'Confirm Password', required=isAdd)
        el.addValidator(MaxLength(25))
        
        el = self.addElement('checkbox', 'reset_required', 'Password Reset Required')
        el.addNote("force the user to change their password the next time they login")
        el.addNote("is set automatically if an administrator changes a password")
        
        # if the current user is not a super user, they can't set the super user
        # field
        if user.get_attr('super_user'):
            el = self.addElement('checkbox', 'super_user', 'Super User')
            el.addNote("super users will have all permissions automatically")
        
        el = self.addElement('checkbox', 'email_notify', 'Email Notification', checked=True)
        el.addNote("send notification email on password change or new user creation")
        el.addNote("forces password reset if password is sent out in an email")
        
        el = self.addElement('header', 'group_membership_header', 'Group Membership')
        
        group_opts = group_list_options()
        el = self.addElement('select', 'assigned_groups', group_opts, 'Assign to', multiple = True)
        el.addValidator(Select(group_opts))
        
        el = self.addElement('header', 'group_permissions_header', 'User Permissions')
        
        perm_opts = permission_list_options()
        el = self.addElement('select', 'approved_permissions', perm_opts, 'Approved', multiple = True)
        el.addValidator(Select(perm_opts))
        
        el = self.addElement('select', 'denied_permissions', perm_opts, 'Denied', multiple = True)
        el.addValidator(Select(perm_opts))
        self.addElement('submit', 'submit', 'Submit')
        
        self.set_submitted(rg.request.form)
        
        self.add_validator(self.validate_perms)
    
    def validate_perms(self, values):
        errors = {}
        
        assigned = toset(values['approved_permissions'])
        denied = toset(values['denied_permissions'])
        
        if len(assigned.intersection(denied)) != 0:
            errors['denied_permissions'] = 'you can not approve and deny the same permission'
            errors['approved_permissions'] = 'you can not approve and deny the same permission'
        
        return errors

class GroupForm(Form):
        
    def __init__(self, isAdd):
        Form.__init__(self, 'group-form', class_='generated')
        
        el = self.addElement('text', 'name', 'Group Name', required=True)
        el.addValidator(MaxLength(150))
        
        el = self.addElement('header', 'group_membership_header', 'Users In Group')
        
        user_opts = user_list_options()
        el = self.addElement('select', 'assigned_users', user_opts, 'Assign', multiple = True)
        el.addValidator(Select(user_opts))

        el = self.addElement('header', 'group_permissions_header', 'Group Permissions')
        
        perm_opts = permission_list_options()
        el = self.addElement('select', 'approved_permissions', perm_opts, 'Approved', multiple = True)
        el.addValidator(Select(perm_opts))
        
        el = self.addElement('select', 'denied_permissions', perm_opts, 'Denied', multiple = True)
        el.addValidator(Select(perm_opts))

        self.addElement('submit', 'submit', 'Submit')
        
        self.set_submitted(rg.request.form)
        
        self.add_validator(self.validate_perms)
    
    def validate_perms(self, values):
        errors = {}
        
        assigned = toset(values['approved_permissions'])
        denied = toset(values['denied_permissions'])
        
        if len(assigned.intersection(denied)) != 0:
            errors['denied_permissions'] = 'you can not approve and deny the same permission'
            errors['approved_permissions'] = 'you can not approve and deny the same permission'
        
        return errors

class PermissionForm(Form):
        
    def __init__(self, isAdd):
        Form.__init__(self, 'permission-form', class_='generated')
        
        el = self.addElement('text', 'name', 'Permission Name', required=True)
        el.addValidator(MaxLength(150))

        self.addElement('submit', 'submit', 'Submit')
        
        self.set_submitted(rg.request.form)

class LoginForm(Form):
            
    def __init__(self):
        Form.__init__(self, 'login-form', class_='generated')
        
        el = self.addElement('text', 'login_id', 'Login Id', required=True)
        el.addValidator(MaxLength(150))
        
        el = self.addElement('password', 'password', 'Password', required=True)
        el.addValidator(MaxLength(25))

        self.addElement('submit', 'submit', 'Submit')
        
        self.set_submitted(rg.request.form)

class ChangePasswordForm(Form):

    def __init__(self):
        Form.__init__(self, 'login-form', class_='generated')

        el = self.addElement('password', 'old_password', 'Old Password', required=True)
        el.addValidator(MaxLength(25))

        el = self.addElement('password', 'password', 'New Password', required=True)
        el.addValidator(MaxLength(25))
        el.addValidator(MinLength(6))
        
        el = self.addElement('password', 'confirm_password', 'Confirm', required=True)
        el.addValidator(MaxLength(25))
        el.addValidator(MinLength(6))

        self.addElement('submit', 'submit', 'Submit')

        self.set_submitted(rg.request.form)

        self.add_validator(self.validate_password)
        self.add_validator(self.validate_confirm)
        self.add_validator(self.validate_validnew)
        
    def validate_password(self, values):
        errors = {}

        if not values['old_password']:
            return

        dbobj = user_get(user.get_attr('id'))
        if (dbobj.pass_hash != hash_pass(values['old_password'])):
            errors['old_password'] = 'incorrect password'

        return errors

    def validate_confirm(self, values):
        errors = {}

        if not values['old_password']:
            return
            
        if (values['password'] != values['confirm_password']):
            errors['confirm_password'] = 'passwords do not match'

        return errors

    def validate_validnew(self, values):
        errors = {}

        if not values['old_password']:
            return
            
        if (values['old_password'] == values['password']):
            errors['password'] = 'password must be different from the old password'

        return errors
        