from pysutils import tolist
from pysmvt import user, modimportauto, appimportauto
from pysmvt.routing import url_for
from pysmvt.utils import toset
from formencode.validators import MaxLength, MinLength
from pysform.exceptions import ValueInvalid
appimportauto('forms', ('Form', 'UniqueValidator'))

modimportauto('users.actions', ('group_list_options','user_list_options',
    'permission_list_options','user_get','hash_pass',
    'user_get_by_email', 'user_get_by_login', 'group_get_by_name'))
modimportauto('users.utils', ('validate_password_complexity', 'note_password_complexity'))

class UserFormBase(Form):
    def add_name_fields(self):
        fnel = self.add_text('name_first', 'First Name')
        fnel.add_processor(MaxLength(255))
        flel = self.add_text('name_last', 'Last Name')
        flel.add_processor(MaxLength(255))
        return fnel, flel
    
    def add_login_id_field(self):
        el = self.add_text('login_id', 'Login Id', required=True)
        el.add_processor(MaxLength(150))
        el.add_processor(UniqueValidator(fn=user_get_by_login), 'That user already exists.')
        return el
    
    def add_email_field(self):
        el = self.add_email('email_address', 'Email', required=True)
        el.add_processor(MaxLength(150))
        el.add_processor(UniqueValidator(fn=user_get_by_email),
                 'A user with that email address already exists.')
        return el
    
    def add_password_field(self, required, label='Password', add_note=True):
        el = self.add_password('password', label, required=required)
        el.add_processor(self.validate_password_complexity)
        if add_note:
            for note in tolist(note_password_complexity()):
                el.add_note(note)
        return el
    
    def add_password_fields(self, required, label='Password', add_note=True):
        el = self.add_password_field(required, label, add_note)
        cel = self.add_confirm('password-confirm', 'Confirm %s'%label, required=required, match=el)
        return el, cel
    
    def add_password_notes(self, isAdd, pasel, cel):
        if isAdd:
            pasel.add_note('leave blank to assign random password')
        else:
            pasel.add_note('leave blank and password will not change')
        pasel.add_note('if set, user will be forced to reset password the next time they login')

    def add_password_reset_field(self):
        el = self.add_checkbox('reset_required', 'Password Reset Required')
        el.add_note("force the user to change their password the next time they login")
        el.add_note("is set automatically if an administrator changes a password")
        return el
    
    def add_super_user_field(self):
        # if the current user is not a super user, they can't set the super user
        # field
        if user.get_attr('super_user'):
            el = self.add_checkbox('super_user', 'Super User')
            el.add_note("super users will have all permissions automatically")
            return el

    def add_email_notify(self):
        el = self.add_checkbox('email_notify', 'Email Notification', checked=True)
        el.add_note("send notification email on password change or new user creation")
        el.add_note("forces password reset if password is sent out in an email")
        return el

    def add_inactive_fields(self):
        iflag = self.add_checkbox('inactive_flag', 'Inactive', checked=False)
        iflag.add_note("setting this will prevent this user from logging in")
        
        idate = self.add_date('inactive_date', 'Inactive Date')
        idate.add_note("setting this will prevent this user from logging in after"
                    " the date given (regardless of the checkbox setting above)")
        idate.add_note('date format: mm/dd/yyyy')
        return iflag, idate
    
    def get_group_options(self):
        return group_list_options()
        
    def add_group_membership_section(self, multi=True, required=False):
        hel = self.add_header('group_membership_header', 'Group Membership')
        group_opts = self.get_group_options()
        if multi:
            gel = self.add_mselect('assigned_groups', group_opts, 'Assign to', required=required)
        else:
            gel = self.add_select('assigned_groups', group_opts, 'Assign to', required=required)
        return hel, gel
    
    def add_user_permissions_section(self):
        hel = self.add_header('user_permissions_header', 'User Permissions')
        perm_opts = permission_list_options()
        gel = self.add_mselect('approved_permissions', perm_opts, 'Approved')
        gel = self.add_mselect('denied_permissions', perm_opts, 'Denied')
        return hel, gel
    
    def add_submit_buttons(self):
        hel = self.add_header('submit-fields-header', '')
        sg = self.add_elgroup('submit-group', class_='submit-only')
        sel = sg.add_submit('submit')
        cel = sg.add_cancel('cancel')
        return hel, sg, sel, cel
    
    def validate_perms(self, value):
        assigned = toset(self.approved_permissions.value)
        denied = toset(self.denied_permissions.value)

        if len(assigned.intersection(denied)) != 0:
            msg = 'you can not approve and deny the same permission'
            self.denied_permissions.add_error(msg)
            self.approved_permissions.add_error(msg)
            raise ValueInvalid()

    def validate_password_complexity(self, value):
        ret = validate_password_complexity(value)
        if not ret == True:
            raise ValueInvalid(ret)
        return value

class UserForm(UserFormBase):
        
    def __init__(self, isAdd):
        UserFormBase.__init__(self, 'user-form')
        
        self.add_name_fields()
        self.add_login_id_field()
        self.add_email_field()
        pasel, confel = self.add_password_fields(False)
        self.add_password_notes(isAdd, pasel, confel)
        pasel.add_note('if set, user will be emailed the new password')
        self.add_password_reset_field()
        self.add_super_user_field()
        self.add_email_notify()
        self.add_inactive_fields()
        
        self.add_group_membership_section()
        self.add_user_permissions_section()
        
        self.add_submit_buttons()
        
        self.add_validator(self.validate_perms)

class UserProfileForm(UserFormBase):
        
    def __init__(self):
        UserFormBase.__init__(self, 'user-profile-form')
        
        self.add_name_fields()
        self.add_email_field()
        self.add_login_id_field()
        pasel, confel = self.add_password_fields(False)
        pasel.add_note('password will change only if you enter a value above')
        self.add_submit_buttons()

class GroupForm(Form):
        
    def __init__(self):
        Form.__init__(self, 'group-form')
        
        el = self.add_text('name', 'Group Name', required=True)
        el.add_processor(MaxLength(150))
        el.add_processor(UniqueValidator(fn=group_get_by_name),
                 'a group with that name already exists')
        
        el = self.add_header('group_membership_header', 'Users In Group')
        
        user_opts = user_list_options()
        el = self.add_mselect('assigned_users', user_opts, 'Assign')

        el = self.add_header('group_permissions_header', 'Group Permissions')
        
        perm_opts = permission_list_options()
        el = self.add_mselect('approved_permissions', perm_opts, 'Approved')
        
        el = self.add_mselect('denied_permissions', perm_opts, 'Denied')

        self.add_header('submit-fields-header', '')
        sg = self.add_elgroup('submit-group', class_='submit-only')
        el = sg.add_submit('submit')
        el = sg.add_cancel('cancel')
                
        self.add_validator(self.validate_perms)
        
    def validate_perms(self, value):
        assigned = toset(self.approved_permissions.value)
        denied = toset(self.denied_permissions.value)
        
        if len(assigned.intersection(denied)) != 0:
            raise ValueInvalid('you can not approve and deny the same permission')

class PermissionForm(Form):
        
    def __init__(self):
        Form.__init__(self, 'permission-form')
        
        el = self.add_static('name', 'Permission Name', required=True)
        
        el = self.add_text('description', 'Description')
        el.add_processor(MaxLength(250))

        self.add_header('submit-fields-header', '')
        sg = self.add_elgroup('submit-group', class_='submit-only')
        el = sg.add_submit('submit')
        el = sg.add_cancel('cancel')
        
        
class LoginForm(Form):
            
    def __init__(self):
        Form.__init__(self, 'login-form')
        
        el = self.add_text('login_id', 'Login Id', required=True)
        el.add_processor(MaxLength(150))
        
        el = self.add_password('password', 'Password', required=True)
        el.add_processor(MaxLength(25))

        self.add_submit('submit')

class ChangePasswordForm(UserFormBase):

    def __init__(self):
        UserFormBase.__init__(self, 'change-pass-form')

        el = self.add_password('old_password', 'Current Password', required=True)
        el.add_processor(MaxLength(25))
        el.add_processor(self.validate_password)

        self.add_password_fields(True, 'New Password')

        self.add_submit('submit')
        self.add_validator(self.validate_validnew)
        
    def validate_password(self, value):
        dbobj = user_get(user.get_attr('id'))
        if dbobj.pass_hash != hash_pass(value):
            raise ValueInvalid('incorrect password')
            
        return value

    def validate_validnew(self, form):
        if form.password.value == form.old_password.value:
            err = 'password must be different from the old password'
            form.password.add_error(err)
            raise ValueInvalid()

class NewPasswordForm(UserFormBase):

    def __init__(self):
        Form.__init__(self, 'new-pass-form')

        self.add_password_fields(True)

        self.add_submit('submit')

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
