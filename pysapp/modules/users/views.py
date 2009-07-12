# -*- coding: utf-8 -*-
from pysmvt import redirect, session, ag, appimportauto, settings, modimportauto
from pysmvt import user as usr
from pysmvt.exceptions import ActionError
from pysmvt.routing import url_for, current_url
from pysmvt.htmltable import Col, YesNo, Link, Table
import actions, forms
from utils import after_login_url
appimportauto('base', ('ProtectedPageView', 'ProtectedRespondingView',
    'PublicPageView', 'PublicTextSnippetView', 'ManageCommon', 'UpdateCommon',
    'DeleteCommon'))
modimportauto('users.actions', ('user_validate','load_session_user',
    'user_assigned_perm_ids', 'user_group_ids'))

_modname = 'users'

class UserUpdate(UpdateCommon):
    def prep(self):
        UpdateCommon.prep(self, _modname, 'user', 'User')

    def post_auth_setup(self, id):
        self.determine_add_edit(id)
        self.form = self.formcls(self.isAdd)
        if not self.isAdd:
            self.dbobj = self.action_get(id)
            if self.dbobj is None:
                user.add_message('error', self.message_exists_not % {'objectname':self.objectname})
                self.on_edit_error()
            vals = self.dbobj.to_dict()
            vals['assigned_groups'] = user_group_ids(self.dbobj)
            vals['approved_permissions'], vals['denied_permissions'] = user_assigned_perm_ids(self.dbobj)
            self.form.set_defaults(vals)

class UserManage(ManageCommon):
    def prep(self):
        ManageCommon.prep(self, _modname, 'user', 'users', 'User')
        
    def create_table(self):
        ManageCommon.create_table(self)
        t = self.table
        t.login_id = Col('Login')
        t.email_address = Col('Email')
        t.super_user = YesNo('Super User')
        t.reset_required = YesNo('Reset Required')
        t.permission_map = Link( 'Permission Map',
                 validate_url=False,
                 urlfrom=lambda uobj: url_for('users:PermissionMap', uid=uobj.id),
                 extractor = lambda row: 'view permission map'
            )

class UserDelete(DeleteCommon):
    def prep(self):
        DeleteCommon.prep(self, _modname, 'user', 'User')

    def default(self, id):
        if id == usr.get_attr('id'):
            usr.add_message('error', 'You cannot delete your own user account')
            redirect(url_for(self.endpoint_manage))
        DeleteCommon.default(self, id)

class ChangePassword(ProtectedPageView):
    def prep(self):
        self.authenticated_only = True
    
    def post_auth_setup(self):
        from forms import ChangePasswordForm
        self.form = ChangePasswordForm()

    def post(self):
        if self.form.is_valid():
            actions.user_update_password(usr.get_attr('id'), **self.form.get_values())
            usr.add_message('notice', 'Your password has been changed successfully.')
            url = after_login_url()
            redirect(url)
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()
            
        self.default()

    def default(self):

        self.assign('formHtml', self.form.render())

class LostPassword(PublicPageView):
    def setup(self):
        from forms import LostPasswordForm
        self.form = LostPasswordForm()

    def post(self):
        if self.form.is_valid():
            em_address = self.form.email_address.value
            if actions.user_lost_password(em_address):
                usr.add_message('notice', 'Your password has been reset. An email with a temporary password will be sent shortly.')
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

class PermissionMap(ProtectedPageView):
    def prep(self):
        self.require = ('users-manage')
    
    def default(self, uid):
        self.assign('user', actions.user_get(uid))
        self.assign('result', actions.user_permission_map(uid))
        self.assign('permgroups', actions.user_permission_map_groups(uid))

class Login(PublicPageView):
    
    def setup(self):
        from forms import LoginForm
        self.form = LoginForm()
    
    def post(self):        
        if self.form.is_valid():
            user = user_validate(**self.form.get_values())
            if user:
                load_session_user(user)
                usr.add_message('notice', 'You logged in successfully!')
                if user.reset_required:
                    url = url_for('users:ChangePassword')
                else:
                    url = after_login_url()
                redirect(url)
            else:
                usr.add_message('error', 'Login failed!  Please try again.')
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()
            
        self.default()
    
    def default(self):
        
        self.assign('formHtml', self.form.render())

class Logout(PublicPageView):
        
    def default(self):
        session['user'].clear()
            
        url = url_for('users:Login')
        redirect(url)
        
class GroupUpdate(UpdateCommon):
    def prep(self):
        UpdateCommon.prep(self, _modname, 'group', 'Group')

    def post_auth_setup(self, id):
        self.determine_add_edit(id)
        self.form = self.formcls()
        if not self.isAdd:
            self.dbobj = self.action_get(id)
            if self.dbobj is None:
                user.add_message('error', self.message_exists_not % {'objectname':self.objectname})
                self.on_edit_error()
            vals = self.dbobj.to_dict()
            vals['assigned_users'] = actions.group_user_ids(self.dbobj)
            vals['approved_permissions'], vals['denied_permissions'] = actions.group_assigned_perm_ids(self.dbobj)
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
        self.template_name = 'permission_manage'
        
    def create_table(self):
        ManageCommon.create_table(self)
        t = self.table
        t.name = Col('Permission', width_td="35%")
        t.description = Col('Description')

class NewUserEmail(PublicTextSnippetView):
    def default(self, login_id, password):
        self.assign('login_id', login_id)
        self.assign('password', password)
        
        self.assign('login_url', url_for('users:Login', _external=True))
        self.assign('index_url', current_url(root_only=True))
        
class ChangePasswordEmail(PublicTextSnippetView):
    def default(self, login_id, password):
        self.assign('login_id', login_id)
        self.assign('password', password)

        self.assign('login_url', url_for('users:Login', _external=True))
        self.assign('index_url', current_url(root_only=True))

