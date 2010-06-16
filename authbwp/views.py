# -*- coding: utf-8 -*-
import datetime
import logging
from pysmvt import redirect, settings, rg, user as usr
from pysmvt.routing import url_for, current_url
from pysmvt.htmltable import Col, YesNo, Link, Table
from pysmvt.views import View, SecureView
from plugstack.auth.lib.views import ManageCommon, UpdateCommon, DeleteCommon
from plugstack.auth.actions import user_validate,load_session_user, \
    user_assigned_perm_ids, user_group_ids, user_get, \
    user_update_password, user_get_by_login, load_session_user, \
    user_kill_reset_key, user_lost_password, user_permission_map, \
    user_permission_map_groups, group_user_ids, group_assigned_perm_ids, \
    user_update
from plugstack.auth.lib.utils import after_login_url
from plugstack.auth.forms import ChangePasswordForm, NewPasswordForm, \
    LostPasswordForm, LoginForm

_modname = 'auth'

log = logging.getLogger(__name__)

class UserUpdate(UpdateCommon):
    def prep(self):
        UpdateCommon.prep(self, _modname, 'user', 'User')

    def auth_pre(self, id):
        # prevent non-super users from editing super users
        if id and usr.is_authenticated:
            sess_user_obj = user_get(usr.id)
            edited_user_obj = user_get(id)
            if edited_user_obj and edited_user_obj.super_user and not sess_user_obj.super_user:
                self.is_authorized = False

    def auth_post(self, id):
        self.determine_add_edit(id)
        self.form = self.formcls(self.isAdd)
        if not self.isAdd:
            self.dbobj = self.action_get(id)
            vals = self.dbobj.to_dict()
            vals['assigned_groups'] = user_group_ids(self.dbobj)
            vals['approved_permissions'], vals['denied_permissions'] = user_assigned_perm_ids(self.dbobj)
            self.form.set_defaults(vals)

class UserManage(ManageCommon):
    def prep(self):
        ManageCommon.prep(self, _modname, 'user', 'users', 'User')

    def create_table(self):
        def determine_inactive(user):
            return user.inactive

        ManageCommon.create_table(self)
        t = self.table
        t.login_id = Col('Login Id')
        t.name = Col('Name')
        t.super_user = YesNo('Super User')
        t.reset_required = YesNo('Reset Required')
        t.inactive = YesNo('Inactive', extractor=determine_inactive)
        t.permission_map = Link( 'Permission Map',
                 validate_url=False,
                 urlfrom=lambda uobj: url_for('auth:PermissionMap', uid=uobj.id),
                 extractor = lambda row: 'view permission map'
            )

class UserDelete(DeleteCommon):
    def prep(self):
        DeleteCommon.prep(self, _modname, 'user', 'User')

    def auth_pre(self, id):
        if id and usr.is_authenticated:
            # prevent self-deletion
            if id == usr.id:
                usr.add_message('error', 'You cannot delete your own user account')
                self.on_complete()
            # prevent non-super users from deleting super users
            sess_user_obj = user_get(usr.id)
            edited_user_obj = user_get(id)
            if edited_user_obj and edited_user_obj.super_user and not sess_user_obj.super_user:
                self.is_authorized = False

class ChangePassword(SecureView):
    def auth_pre(self):
        self.is_authenticated = True
        self.check_authorization = False

    def auth_post(self):
        self.form = ChangePasswordForm()

    def post(self):
        if self.form.is_valid():
            user_update_password(usr.id, **self.form.get_values())
            usr.add_message('notice', 'Your password has been changed successfully.')
            url = after_login_url()
            redirect(url)
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()

        self.default()

    def default(self):
        self.assign('formHtml', self.form.render())
        self.render_template()

class ResetPassword(View):

    def setup_view(self, login_id, key):
        # this probably should never happen, but doesn't hurt to check
        if not key or not login_id:
            self.abort()
        user = user_get_by_login(login_id)
        if not user:
            self.abort()
        if key != user.pass_reset_key:
            self.abort()
        expires_on = user.pass_reset_ts + datetime.timedelta(hours=settings.plugins.auth.password_rest_expires_after)
        if datetime.datetime.utcnow() > expires_on:
            self.abort('password reset link expired')

        self.user = user
        self.form = NewPasswordForm()

    def post(self, login_id, key):
        if self.form.is_valid():
            user_update_password(self.user.id, **self.form.get_values())
            usr.add_message('notice', 'Your password has been reset successfully.')

            # at this point, the user has been verified, and we can setup the user
            # session and kill the reset
            load_session_user(self.user)
            user_kill_reset_key(self.user)

            # redirect as if this was a login
            url = after_login_url()
            redirect(url)
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()
        self.assign_form()
        self.render_template()

    def get(self, login_id, key):
        usr.add_message('Notice', "Please choose a new password to complete the reset request.")
        self.assign_form()
        self.render_template()

    def assign_form(self):
        self.assign('form', self.form)

    def abort(self, msg='invalid reset request'):
        usr.add_message('error', '%s, use the form below to resend reset link' % msg)
        url = url_for('auth:LostPassword')
        redirect(url)

class LostPassword(View):
    def __init__(self, urlargs, endpoint):
        View.__init__(self, urlargs, endpoint)
        self.form = LostPasswordForm()

    def post(self):
        if self.form.is_valid():
            em_address = self.form.elements.email_address.value
            if user_lost_password(em_address):
                usr.add_message('notice', 'An email with a link to reset your password has been sent.')
                url = current_url(root_only=True)
                redirect(url)
            else:
                usr.add_message('error', 'Did not find a user with email address: %s' % em_address)
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()

        self.default()

    def default(self):
        self.assign('formHtml', self.form.render())
        self.render_template()

class UserProfile(UpdateCommon):
    def prep(self):
        UpdateCommon.prep(self, _modname, 'user', 'UserProfile')
        self.check_authorization = False
        self.actionname = 'Update'
        self.objectname = 'Profile'

    def auth_post(self):
        self.assign_form()
        self.user_id = usr.id
        self.dbobj = user_get(self.user_id)
        self.form.set_defaults(self.dbobj.to_dict())

    def on_cancel(self):
        usr.add_message('notice', 'no changes made to your profile')
        redirect(current_url(root_only=True))

    def do_update(self, id):
        formvals = self.form.get_values()
        # assigned groups and permissions stay the same for profile submissions
        formvals['assigned_groups'] = user_group_ids(self.dbobj)
        formvals['approved_permissions'], formvals['denied_permissions'] = \
                user_assigned_perm_ids(self.dbobj)
        formvals['pass_reset_ok'] = False
        user_update(id, **formvals)
        usr.add_message('notice', 'profile updated succesfully')
        self.default()

    def post(self):
        UpdateCommon.post(self, self.user_id)

    def default(self, id=None):
        UpdateCommon.default(self, self.user_id)

class PermissionMap(SecureView):
    def auth_pre(self):
        self.require_all = 'users-manage'

    def default(self, uid):
        self.assign('user', user_get(uid))
        self.assign('result', user_permission_map(uid))
        self.assign('permgroups', user_permission_map_groups(uid))
        self.render_template()

class Login(View):
    def __init__(self, urlargs, endpoint):
        View.__init__(self, urlargs, endpoint)
        self.form = LoginForm()

    def post(self):
        if self.form.is_valid():
            user = user_validate(**self.form.get_values())
            if user:
                if user.inactive:
                    usr.add_message('error', 'That user is inactive.')
                else:
                    load_session_user(user)
                    log.application('user %s logged in; session id: %s; remote_ip: %s', user.login_id, rg.session.id, rg.request.remote_addr)
                    usr.add_message('notice', 'You logged in successfully!')
                    if user.reset_required:
                        url = url_for('auth:ChangePassword')
                    else:
                        url = after_login_url()
                    redirect(url)
            else:
                log.application('user login failed; user login: %s; session id: %s; remote_ip: %s', self.form.elements.login_id.value, rg.session.id, rg.request.remote_addr)
                usr.add_message('error', 'Login failed!  Please try again.')
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()

        self.default()

    def default(self):
        self.assign('formHtml', self.form.render())
        self.render_template()

class Logout(View):

    def default(self):
        rg.session.invalidate()

        url = url_for('auth:Login')
        redirect(url)

class GroupUpdate(UpdateCommon):
    def prep(self):
        UpdateCommon.prep(self, _modname, 'group', 'Group')

    def auth_post(self, id):
        self.determine_add_edit(id)
        self.form = self.formcls()
        if not self.isAdd:
            self.dbobj = self.action_get(id)
            vals = self.dbobj.to_dict()
            vals['assigned_users'] = group_user_ids(self.dbobj)
            vals['approved_permissions'], vals['denied_permissions'] = group_assigned_perm_ids(self.dbobj)
            self.form.set_defaults(vals)

class GroupManage(ManageCommon):
    def prep(self):
        ManageCommon.prep(self, _modname, 'group', 'groups', 'Group')
        self.table = Table(class_='dataTable manage', style="width: 60%")

    def create_table(self):
        ManageCommon.create_table(self)
        t = self.table
        t.name = Col('Name')

class GroupDelete(DeleteCommon):
    def prep(self):
        DeleteCommon.prep(self, _modname, 'group', 'Group')

class PermissionUpdate(UpdateCommon):
    def prep(self):
        UpdateCommon.prep(self, _modname, 'permission', 'Permission')

class PermissionManage(ManageCommon):
    def prep(self):
        ManageCommon.prep(self, _modname, 'permission', 'permissions', 'Permission')
        self.delete_link_require = None

    def create_table(self):
        ManageCommon.create_table(self)
        t = self.table
        t.name = Col('Permission', width_td="35%")
        t.description = Col('Description')

    def default(self):
        self.assign_vars()
        self.render_template()
        