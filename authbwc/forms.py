from blazeform.exceptions import ValueInvalid
from blazeutils.helpers import tolist, toset
from blazeweb.globals import user
from blazeweb.routing import url_for
from formencode import Invalid
from formencode.validators import FancyValidator, MaxLength, MinLength

from compstack.auth.helpers import validate_password_complexity, note_password_complexity
from compstack.auth.model.orm import User as orm_User, Group as orm_Group, \
    Permission as orm_Permission
from compstack.common.lib.forms import Form


class UserFormBase(Form):
    def add_name_fields(self):
        fnel = self.add_text('name_first', 'First Name')
        flel = self.add_text('name_last', 'Last Name')
        return fnel, flel

    def add_login_id_field(self):
        el = self.add_text('login_id', 'Login Id', required=True)
        return el

    def add_email_field(self):
        el = self.add_email('email_address', 'Email', required=True)
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
        cel = self.add_confirm(
            'password-confirm',
            'Confirm %s' % label,
            required=required,
            match=el
        )
        return el, cel

    def add_password_notes(self, is_add, pasel, cel):
        if is_add:
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
        if user.is_super_user:
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
        idate.add_note(
            "setting this will prevent this user from logging in after"
            " the date given (regardless of the checkbox setting above)"
        )
        idate.add_note('date format: mm/dd/yyyy')
        return iflag, idate

    def get_group_options(self):
        return orm_Group.pairs('id:name', orm_Group.name)

    def add_group_membership_section(self, multi=True, required=False):
        hel = self.add_header('group_membership_header', 'Group Membership')
        group_opts = self.get_group_options()
        if multi:
            gel = self.add_mselect('assigned_groups', group_opts, 'Assign to',
                                   required=required, choose=None)
        else:
            gel = self.add_select('assigned_groups', group_opts, 'Assign to', required=required)
        return hel, gel

    def add_user_permissions_section(self):
        hel = self.add_header('user_permissions_header', 'User Permissions')
        perm_opts = orm_Permission.pairs('id:name', orm_Permission.name)
        gel = self.add_mselect('approved_permissions', perm_opts, 'Approved', choose=None)
        gel = self.add_mselect('denied_permissions', perm_opts, 'Denied', choose=None)
        return hel, gel

    def add_submit_buttons(self):
        hel = self.add_header('submit-fields-header', '')
        sg = self.add_elgroup('submit-group', class_='submit-only')
        sel = sg.add_submit('submit')
        cel = sg.add_cancel('cancel')
        return hel, sg, sel, cel

    def validate_perms(self, value):
        assigned = toset(self.elements.approved_permissions.value)
        denied = toset(self.elements.denied_permissions.value)

        if len(assigned.intersection(denied)) != 0:
            msg = 'you can not approve and deny the same permission'
            self.elements.denied_permissions.add_error(msg)
            self.elements.approved_permissions.add_error(msg)
            raise ValueInvalid()

    def validate_password_complexity(self, value):
        ret = validate_password_complexity(value)
        if isinstance(ret, basestring):
            raise ValueInvalid(ret)
        return value

    def add_field_errors(self, errors):
        for err in errors.get('login_id', []):
            if 'not unique' in err:
                self.elements.login_id.add_error('that user already exists')
                errors['login_id'].remove(err)
                break

        for err in errors.get('email_address', []):
            if 'not unique' in err:
                self.elements.email_address.add_error(
                    'a user with that email address already exists'
                )
                errors['email_address'].remove(err)
                break

        return Form.add_field_errors(self, errors)


class User(UserFormBase):
    def init(self):
        self.req_note_level = 'form'
        self.add_name_fields()
        self.add_login_id_field()
        self.add_email_field()
        pasel, confel = self.add_password_fields(False)
        self.add_password_notes(self.is_add, pasel, confel)
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
    def init(self):
        self.req_note_level = 'form'
        self.add_name_fields()
        self.add_email_field()
        self.add_login_id_field()
        pasel, confel = self.add_password_fields(False)
        pasel.add_note('password will change only if you enter a value above')
        self.add_submit_buttons()


class Group(Form):
    def add_name_field(self):
        self.add_text('name', 'Group Name', required=True)

    def add_user_membership_section(self):
        el = self.add_header('group_membership_header', 'Users In Group')

        # list only active users, using the "inactive" hybrid property to account
        #   for all cases
        users = orm_User.list_where(
            orm_User.inactive == False,
            order_by=[orm_User.name, orm_User.login_id]
        )
        user_opts = [
            (
                u.id,
                '{0} ({1})'.format(u.name, u.login_id) if u.name else u.login_id
            ) for u in users
        ]
        el = self.add_mselect('assigned_users', user_opts, 'Assign', choose=None)

    def add_group_permissions_section(self):
        el = self.add_header('group_permissions_header', 'Group Permissions')

        perm_opts = orm_Permission.pairs('id:name', orm_Permission.name)
        el = self.add_mselect('approved_permissions', perm_opts, 'Approved', choose=None)

        el = self.add_mselect('denied_permissions', perm_opts, 'Denied', choose=None)

    def add_submit_buttons(self):
        self.add_header('submit-fields-header', '')
        sg = self.add_elgroup('submit-group', class_='submit-only')
        el = sg.add_submit('submit')
        el = sg.add_cancel('cancel')

    def init(self):
        self.req_note_level = 'form'
        self.add_name_field()
        self.add_user_membership_section()
        self.add_group_permissions_section()
        self.add_submit_buttons()

        self.add_validator(self.validate_perms)

    def validate_perms(self, value):
        assigned = toset(self.elements.approved_permissions.value)
        denied = toset(self.elements.denied_permissions.value)

        if len(assigned.intersection(denied)) != 0:
            raise ValueInvalid('you can not approve and deny the same permission')


class Permission(Form):

    def init(self):
        self.req_note_level = 'form'
        el = self.add_static('name', 'Permission Name', required=True)

        el = self.add_text('description', 'Description')

        self.add_header('submit-fields-header', '')
        sg = self.add_elgroup('submit-group', class_='submit-only')
        el = sg.add_submit('submit')
        el = sg.add_cancel('cancel')


class LoginForm(Form):

    def init(self):
        el = self.add_text('login_id', 'Login Id', required=True)
        el.add_processor(MaxLength(150))

        el = self.add_password('password', 'Password', required=True)
        el.add_processor(MaxLength(25))

        self.add_submit('submit')


class ChangePasswordForm(UserFormBase):

    def init(self):
        el = self.add_password('old_password', 'Current Password', required=True)
        el.add_processor(MaxLength(25))
        el.add_processor(self.validate_password)

        self.add_password_fields(True, 'New Password')

        self.add_submit('submit')
        self.add_validator(self.validate_validnew)

    def validate_password(self, value):
        dbobj = orm_User.get(user.id)
        if not dbobj.validate_password(value):
            raise ValueInvalid('incorrect password')

        return value

    def validate_validnew(self, form):
        if form.password.value == form.old_password.value:
            err = 'password must be different from the old password'
            form.password.add_error(err)
            raise ValueInvalid()


class NewPasswordForm(UserFormBase):

    def init(self):
        self.add_password_fields(True)

        self.add_submit('submit')


class LostPasswordForm(Form):

    def init(self):
        el = self.add_email('email_address', 'Email', required=True)
        el.add_processor(MaxLength(150))
        el.add_processor(self.validate_email)

        self.add_submit('submit')

    def validate_email(self, value):
        dbobj = orm_User.get_by_email(value)
        if (dbobj is None):
            raise ValueInvalid('email address is not associated with a user')

        return value
