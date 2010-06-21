# -*- coding: utf-8 -*-
import datetime
import logging
from blazeweb import settings, rg, user as usr
from blazeweb.htmltable import Col, YesNo, Link, Table
from blazeweb.routing import url_for, current_url
from blazeweb.utils import redirect
from blazeweb.views import View, SecureView
from werkzeug.exceptions import NotFound
from plugstack.auth.forms import ChangePasswordForm, NewPasswordForm, \
    LostPasswordForm, LoginForm
from plugstack.auth.helpers import after_login_url, load_session_user, send_new_user_email, \
    send_change_password_email, send_password_reset_email
from plugstack.auth.lib.views import ManageCommon, UpdateCommon, DeleteCommon
from plugstack.auth.model.actions import user_validate, \
    user_assigned_perm_ids, user_group_ids, user_get, \
    user_update_password, user_get_by_login, \
    user_kill_reset_key, user_lost_password, user_permission_map, \
    user_permission_map_groups, group_user_ids, group_assigned_perm_ids, \
    user_update

_modname = 'auth'

log = logging.getLogger(__name__)

class UserUpdate(UpdateCommon):
    def init(self):
        UpdateCommon.init(self, _modname, 'user', 'User')

    def auth_pre(self, oid):
        # prevent non-super users from editing super users
        if oid and usr.is_authenticated:
            sess_user_obj = user_get(usr.id)
            edited_user_obj = user_get(oid)
            if edited_user_obj and edited_user_obj.super_user and not sess_user_obj.super_user:
                self.is_authorized = False

    def auth_post(self, oid):
        self.determine_add_edit(oid)
        self.form = self.formcls(self.isAdd)
        if not self.isAdd:
            self.dbobj = self.action_get(oid)
            if not self.dbobj:
                raise NotFound
            vals = self.dbobj.to_dict()
            vals['assigned_groups'] = user_group_ids(self.dbobj)
            vals['approved_permissions'], vals['denied_permissions'] = user_assigned_perm_ids(self.dbobj)
            self.form.set_defaults(vals)

    def do_update(self, oid):
        self.update_retval = self.action_update(oid, **self.get_action_params())
        usr.add_message('notice', self.message_update)
        if self.form.elements.email_notify.value:
            if self.isAdd:
                email_sent = send_new_user_email(self.update_retval)
            elif self.form.elements.password.value:
                email_sent = send_change_password_email(self.update_retval)
            if not email_sent:
                usr.add_message('error', 'An error occurred while sending the user notification email.')
        self.on_complete()

class UserManage(ManageCommon):
    def init(self):
        ManageCommon.init(self, _modname, 'user', 'users', 'User')

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
    def init(self):
        DeleteCommon.init(self, _modname, 'user', 'User')

    def auth_pre(self, oid):
        if oid and usr.is_authenticated:
            # prevent self-deletion
            if oid == usr.id:
                usr.add_message('error', 'You cannot delete your own user account')
                self.on_complete()
            # prevent non-super users from deleting super users
            sess_user_obj = user_get(usr.id)
            edited_user_obj = user_get(oid)
            if edited_user_obj and edited_user_obj.super_user and not sess_user_obj.super_user:
                self.is_authorized = False

class ChangePassword(SecureView):
    def auth_pre(self):
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
    def init(self):
        self.form = LostPasswordForm()

    def post(self):
        if self.form.is_valid():
            em_address = self.form.elements.email_address.value
            user_obj = user_lost_password(em_address)
            if user_obj:
                if send_password_reset_email(user_obj):
                    usr.add_message('notice', 'An email with a link to reset your password has been sent.')
                else:
                    usr.add_message('error', 'An error occurred while sending the notification email. Your password has not been reset.')
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
    def init(self):
        UpdateCommon.init(self, _modname, 'user', 'UserProfile')
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

    def do_update(self, oid):
        formvals = self.form.get_values()
        # assigned groups and permissions stay the same for profile submissions
        formvals['assigned_groups'] = user_group_ids(self.dbobj)
        formvals['approved_permissions'], formvals['denied_permissions'] = \
                user_assigned_perm_ids(self.dbobj)
        formvals['pass_reset_ok'] = False
        user_update(oid, **formvals)
        usr.add_message('notice', 'profile updated succesfully')
        self.default()

    def post(self):
        UpdateCommon.post(self, self.user_id)

class PermissionMap(SecureView):
    def auth_pre(self):
        self.require_all = 'auth-manage'

    def default(self, uid):
        self.assign('user', user_get(uid))
        self.assign('result', user_permission_map(uid))
        self.assign('permgroups', user_permission_map_groups(uid))
        self.render_template()

class Login(View):
    def init(self):
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
    def init(self):
        UpdateCommon.init(self, _modname, 'group', 'Group')

    def auth_post(self, oid):
        self.determine_add_edit(oid)
        self.form = self.formcls()
        if not self.isAdd:
            self.dbobj = self.action_get(oid)
            if not self.dbobj:
                raise NotFound
            vals = self.dbobj.to_dict()
            vals['assigned_users'] = group_user_ids(self.dbobj)
            vals['approved_permissions'], vals['denied_permissions'] = group_assigned_perm_ids(self.dbobj)
            self.form.set_defaults(vals)

class GroupManage(ManageCommon):
    def init(self):
        ManageCommon.init(self, _modname, 'group', 'groups', 'Group')
        self.table = Table(class_='dataTable manage', style="width: 60%")

    def create_table(self):
        ManageCommon.create_table(self)
        t = self.table
        t.name = Col('Name')

class GroupDelete(DeleteCommon):
    def init(self):
        DeleteCommon.init(self, _modname, 'group', 'Group')

class PermissionUpdate(UpdateCommon):
    def init(self):
        UpdateCommon.init(self, _modname, 'permission', 'Permission')

class PermissionManage(ManageCommon):
    def init(self):
        ManageCommon.init(self, _modname, 'permission', 'permissions', 'Permission')
        self.delete_link_require = None

    def create_table(self):
        ManageCommon.create_table(self)
        t = self.table
        t.name = Col('Permission', width_td="35%")
        t.description = Col('Description')

    def default(self):
        self.assign_vars()
        self.render_template()
        
