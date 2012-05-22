# -*- coding: utf-8 -*-
import datetime
import logging
from blazeweb.globals import settings, rg, user as session_user
from blazeweb.routing import url_for, current_url
from blazeweb.utils import redirect, abort
from blazeweb.views import View, SecureView
from webhelpers.html import literal
from webhelpers.html.tags import link_to
from werkzeug.exceptions import NotFound
from compstack.auth.forms import ChangePasswordForm, NewPasswordForm, \
    LostPasswordForm, LoginForm, UserProfileForm, User as UserForm, Group as GroupForm, \
    Permission as PermissionForm
from compstack.auth.helpers import after_login_url, load_session_user, send_new_user_email, \
    send_change_password_email, send_reset_password_email
from compstack.auth.model.orm import User as orm_User, Group as orm_Group, Permission as orm_Permission
from compstack.common.lib.views import CrudBase, FormMixin
from compstack.datagrid.lib import DataGrid, Col, YesNo, Link
from compstack.sqlalchemy import db

_modname = 'auth'

log = logging.getLogger(__name__)

class UserCrud(CrudBase):
    def init(self):
        CrudBase.init(self, 'User', 'Users', UserForm, orm_User)
        self.require_all = 'auth-manage'
        self.form_auto_init = False

    def auth_calculate(self, objid=None):
        CrudBase.auth_calculate(self, objid=objid)
        # prevent non-super users from editing super users
        if objid and session_user.is_authenticated:
            sess_user_obj = orm_User.get(session_user.id)
            edited_user_obj = orm_User.get(objid)
            if edited_user_obj and edited_user_obj.super_user and not sess_user_obj.super_user:
                self.is_authorized = False

    def auth_post(self, action=None, objid=None):
        CrudBase.auth_post(self, action, objid)
        if self.action == self.DELETE:
            # prevent self-deletion
            if objid == session_user.id:
                session_user.add_message('error', 'You cannot delete your own user account')
                abort(403)

    def form_assign(self, formcls):
        CrudBase.form_assign(self, formcls)
        self.form.is_add = (self.action == self.ADD)
        self.form.init()
        self.form_assign_defaults()

    def form_assign_defaults(self):
        if self.action == self.EDIT:
            vals = self.objinst.to_dict()
            vals['assigned_groups'] = self.objinst.group_ids
            vals['approved_permissions'], vals['denied_permissions'] = self.objinst.assigned_permission_ids
            self.form.set_defaults(vals)

    def form_when_completed(self):
        if self.form.elements.email_notify.value:
            if self.action == self.ADD:
                email_sent = send_new_user_email(self.form_resulting_entity)
            elif self.form.elements.password.value:
                email_sent = send_change_password_email(self.form_resulting_entity)
            if (self.action == self.ADD or self.form.elements.password.value) and not email_sent:
                session_user.add_message('error', 'An error occurred while sending the user notification email.')

        CrudBase.form_when_completed(self)

    def _display_name(self, user):
        retval = '%s %s' % (user[self.users.c.name_first] or '', user[self.users.c.name_last] or '')
        return retval.strip()

    def manage_action_links(self, row):
        idc = self.users.c.id
        edit_link = link_to('(edit)', url_for(self.endpoint, action='edit', objid=row[idc]), class_='edit_link', title='edit %s' % self.objname)
        if self.delete_is_authorized:
            return literal('%s%s') % \
                (link_to('(delete)', url_for(self.endpoint, action='delete', objid=row[idc]), class_='delete_link', title='delete %s' % self.objname),
                edit_link)
        else:
            return literal(edit_link)

    def manage_init_grid(self):
        # use a custom query to provide the name field, which
        # combines first and last name. Allows filter to work
        # on the full name
        users = db.sess.query(
            orm_User.id,
            orm_User.inactive_flag,
            orm_User.inactive_date,
            orm_User.name_first,
            orm_User.name_last,
            (orm_User.name_first+u' '+orm_User.name_last).label('name'),
            orm_User.login_id,
            orm_User.super_user,
            orm_User.reset_required,
        ).subquery()
        self.users = users

        def determine_inactive(user):
            if user[users.c.inactive_flag] or (user[users.c.inactive_date] and user[users.c.inactive_date] < datetime.datetime.now()):
                return True
            return False

        dg = DataGrid(
            db.sess.execute,
            per_page=30,
            def_sort=lambda q: q.order_by(users.c.id.asc()),
            class_='datagrid'
            )
        dg.add_col(
            'id',
            users.c.id,
            inresult=True
        )
        dg.add_col(
            'inactive_flag',
            users.c.inactive_flag,
            inresult=True
        )
        dg.add_col(
            'inactive_date',
            users.c.inactive_date,
            inresult=True
        )
        dg.add_col(
            'name_first',
            users.c.name_first,
            inresult=True
        )
        dg.add_col(
            'name_last',
            users.c.name_last,
            inresult=True
        )
        dg.add_tablecol(
            Col('Actions',
                extractor=self.manage_action_links,
                width_th='8%'
            ),
            users.c.id,
            sort=None
        )
        dg.add_tablecol(
            Col('Login Id'),
            users.c.login_id,
            filter_on=True,
            sort='both'
        )
        dg.add_tablecol(
            Col('Name', extractor=self._display_name),
            users.c.name,
            filter_on=True,
            sort='both'
        )
        dg.add_tablecol(
            YesNo('Super User'),
            users.c.super_user,
            filter_on=False,
            sort=False
        )
        dg.add_tablecol(
            YesNo('Reset Required'),
            users.c.reset_required,
            filter_on=False,
            sort=False
        )
        dg.add_tablecol(
            YesNo('Inactive', extractor=determine_inactive),
            users.c.inactive_flag,
            filter_on=False,
            sort=False
        )
        dg.add_tablecol(
            Link( 'Permission Map',
                 validate_url=False,
                 urlfrom=lambda uobj: url_for('auth:PermissionMap', objid=uobj[users.c.id]),
                 extractor = lambda row: 'view permission map'
            ),
            users.c.id,
            filter_on=False,
            sort=False
        )
        return dg

class ChangePassword(SecureView):
    def auth_pre(self):
        self.check_authorization = False

    def auth_post(self):
        self.form = ChangePasswordForm()

    def post(self):
        if self.form.is_valid():
            orm_User.get(session_user.id).update_password(self.form.elements.password.value)
            session_user.reset_required = False
            session_user.add_message('notice', 'Your password has been changed successfully.')
            url = after_login_url() if rg.request.url == url_for('auth:ChangePassword') else rg.request.url
            redirect(url)
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()

        self.default()

    def default(self):
        self.assign('form', self.form)
        self.render_template()

class ResetPassword(View):

    def setup_view(self, login_id, key):
        # this probably should never happen, but doesn't hurt to check
        if not key or not login_id:
            self.abort()
        user = orm_User.get_by(login_id=login_id)
        if not user:
            self.abort()
        if key != user.pass_reset_key:
            self.abort()
        expires_on = user.pass_reset_ts + datetime.timedelta(hours=settings.components.auth.password_rest_expires_after)
        if datetime.datetime.utcnow() > expires_on:
            self.abort('password reset link expired')

        self.user = user
        self.form = NewPasswordForm()

    def post(self, login_id, key):
        if self.form.is_valid():
            self.user.update_password(self.form.elements.password.value)
            session_user.add_message('notice', 'Your password has been reset successfully.')

            # at this point, the user has been verified, and we can setup the user
            # session and kill the reset
            load_session_user(self.user)
            self.user.kill_reset_key()

            # redirect as if this was a login
            url = after_login_url()
            redirect(url)
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()
        self.assign_form()
        self.render_template()

    def get(self, login_id, key):
        session_user.add_message('notice', "Please choose a new password to complete the reset request.")
        self.assign_form()
        self.render_template()

    def assign_form(self):
        self.assign('form', self.form)

    def abort(self, msg='invalid reset request'):
        session_user.add_message('error', '%s, use the form below to resend reset link' % msg)
        url = url_for('auth:LostPassword')
        redirect(url)

class LostPassword(View):
    def init(self):
        self.form = LostPasswordForm()

    def post(self):
        if self.form.is_valid():
            em_address = self.form.elements.email_address.value
            user_obj = orm_User.reset_password(em_address)
            if user_obj:
                if send_reset_password_email(user_obj):
                    session_user.add_message('notice', 'An email with a link to reset your password has been sent.')
                else:
                    session_user.add_message('error', 'An error occurred while sending the notification email. Your password has not been reset.')
                url = current_url(root_only=True)
                redirect(url)
            else:
                session_user.add_message('error', 'Did not find a user with email address: %s' % em_address)
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()

        self.default()

    def default(self):
        self.assign('form', self.form)
        self.render_template()

class UserProfile(SecureView, FormMixin):
    def init(self):
        self.check_authorization = False
        self.form = UserProfileForm()

    def auth_post(self):
        self.objid = session_user.id
        self.objinst = orm_User.get(self.objid)
        self.form.set_defaults(self.objinst.to_dict())

    def form_on_cancel(self):
        session_user.add_message('notice', 'no changes made to your profile')
        redirect(current_url(root_only=True))

    def form_on_valid(self):
        formvals = self.form.get_values()
        # assigned groups and permissions stay the same for profile submissions
        formvals['assigned_groups'] = self.objinst.group_ids
        formvals['approved_permissions'], formvals['denied_permissions'] = \
                self.objinst.assigned_permission_ids
        formvals['pass_reset_ok'] = False
        orm_User.edit(self.objid, **formvals)
        session_user.add_message('notice', 'profile updated succesfully')

class PermissionMap(SecureView):
    def auth_pre(self):
        self.require_all = 'auth-manage'

    def default(self, objid):
        dbuser = orm_User.get(objid)
        self.assign('dbuser', dbuser)
        self.assign('result', dbuser.permission_map)
        self.assign('permgroups', dbuser.permission_map_groups)
        self.render_template()

class Login(View):
    def init(self):
        self.form = LoginForm()

    def post(self):
        if self.form.is_valid():
            user = orm_User.validate(
                self.form.els.login_id.value,
                self.form.els.password.value
                )
            if user:
                if user.inactive:
                    session_user.add_message('error', 'That user is inactive.')
                else:
                    load_session_user(user)
                    log.application('user %s logged in; session id: %s; remote_ip: %s', user.login_id, rg.session.id, rg.request.remote_addr)
                    session_user.add_message('notice', 'You logged in successfully!')
                    if user.reset_required:
                        url = url_for('auth:ChangePassword')
                    else:
                        url = after_login_url()
                    redirect(url)
            else:
                log.application('user login failed; user login: %s; session id: %s; remote_ip: %s', self.form.elements.login_id.value, rg.session.id, rg.request.remote_addr)
                session_user.add_message('error', 'Login failed!  Please try again.')
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()

        self.default()

    def default(self):
        self.assign('form', self.form)
        self.render_template()

class Logout(View):

    def default(self):
        rg.session.invalidate()

        url = url_for('auth:Login')
        redirect(url)

class GroupCrud(CrudBase):
    def init(self):
        CrudBase.init(self, 'Group', 'Groups', GroupForm, orm_Group)
        self.require_all = 'auth-manage'

    def form_assign_defaults(self):
        if self.action == self.EDIT:
            vals = self.objinst.to_dict()
            vals['assigned_users'] = self.objinst.user_ids
            vals['approved_permissions'], vals['denied_permissions'] = self.objinst.assigned_permission_ids
            self.form.set_defaults(vals)

    def manage_init_grid(self):
        dg = DataGrid(
            db.sess.execute,
            per_page=30,
            def_sort=lambda q: q.order_by(orm_Group.id.asc()),
            class_='datagrid'
            )
        dg.add_col(
            'id',
            orm_Group.id,
            inresult=True
        )
        dg.add_tablecol(
            Col('Actions',
                extractor=self.manage_action_links,
                width_th='8%'
            ),
            orm_Group.id,
            sort=None
        )
        dg.add_tablecol(
            Col('Name'),
            orm_Group.name,
            filter_on=True,
            sort='both'
        )
        return dg

class PermissionCrud(CrudBase):
    def init(self):
        CrudBase.init(self, 'Permission', 'Permissions', PermissionForm, orm_Permission)
        self.require_all = 'auth-manage'
        self.manage_template_endpoint = 'auth:permission_manage.html'

    def auth_post(self, action=None, objid=None):
        CrudBase.auth_post(self, action, objid)
        if self.action in [self.ADD, self.DELETE]:
            abort(400)

    def manage_init_grid(self):
        dg = DataGrid(
            db.sess.execute,
            per_page=30,
            def_sort=lambda q: q.order_by(orm_Permission.id.asc()),
            class_='datagrid'
            )
        dg.add_col(
            'id',
            orm_Permission.id,
            inresult=True
        )
        dg.add_tablecol(
            Col('Actions',
                extractor=self.manage_action_links,
                width_th='8%'
            ),
            orm_Permission.id,
            sort=None
        )
        dg.add_tablecol(
            Col('Permission', width_td="35%"),
            orm_Permission.name,
            filter_on=True,
            sort='both'
        )
        dg.add_tablecol(
            Col('Description'),
            orm_Permission.description,
            filter_on=False,
            sort=False
        )
        return dg
