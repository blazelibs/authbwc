# -*- coding: utf-8 -*-
from pysmvt import redirect, session, ag, appimportauto, settings
from pysmvt import user as usr
from pysmvt.exceptions import ActionError
from pysmvt.routing import url_for, index_url
import actions, forms
from utils import after_login_url
appimportauto('base', ('ProtectedPageView', 'ProtectedRespondingView', 'PublicPageView', 'PublicTextSnippetView'))
                       
class Update(ProtectedPageView):
    def prep(self):
        self.require = ('users-manage')
    
    def setup(self, id):
        from forms import UserForm
        
        if id is None:
            self.isAdd = True
            self.actionName = 'Add'
            self.message = 'user added'
        else:
            self.isAdd = False
            self.actionName = 'Edit'
            self.message = 'user edited successfully'
        
        self.form = UserForm(self.isAdd)
        
        if not self.isAdd:
            user = actions.user_get(id)
            
            if user is None:
                usr.add_message('error', 'the requested user does not exist')
                url = url_for('users:Manage')
                redirect(url)

            vals = user.to_dict()
            vals['assigned_groups'] = actions.user_group_ids(user)
            vals['approved_permissions'], vals['denied_permissions'] = actions.user_assigned_perm_ids(user)
            self.form.set_defaults(vals)
    
    def post(self, id):        
        self.form_submission(id)
        self.default(id)
    
    def form_submission(self, id):
        if self.form.is_valid():
            try:
                actions.user_update(id, **self.form.get_values())
                usr.add_message('notice', self.message)
                url = url_for('users:Manage')
                redirect(url)
            except Exception, e:
                # if the form can't handle the exception, re-raise it
                if not self.form.handle_exception(e):
                    raise
        elif not self.form.is_submitted():
            return
        
        # form was submitted, but invalid
        self.form.assign_user_errors()

    def default(self, id):
        
        self.assign('actionName', self.actionName)
        self.assign('formHtml', self.form.render())

class Manage(ProtectedPageView):
    def prep(self):
        self.require = ('users-manage')
    
    def default(self):
        self.assign('users', actions.user_list())
    
class Delete(ProtectedRespondingView):
    def prep(self):
        self.require = ('users-manage')
    
    def default(self, id):
        if actions.user_delete(id):
            usr.add_message('notice', 'user deleted')
        else:
            usr.add_message('error', 'user was not found')
            
        url = url_for('users:Manage')
        redirect(url)

class ChangePassword(ProtectedPageView):
    def prep(self):
        self.authenticated_only = True
    
    def setup(self):
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
                url = index_url()
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
            user = actions.user_validate(**self.form.get_values())
            if user:
                actions.load_session_user(user)
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

class Logout(ProtectedPageView):
    
    def prep(self):
        self.authenticated_only = True
        
    def default(self):
        session['user'].clear()
            
        url = url_for('users:Login')
        redirect(url)
        
class GroupUpdate(ProtectedPageView):
    def prep(self):
        self.require = ('users-manage')
    
    def setup(self, id):
        from forms import GroupForm
        
        if id is None:
            self.isAdd = True
            self.actionName = 'Add'
            self.message = 'group added'
        else:
            self.isAdd = False
            self.actionName = 'Edit'
            self.message = 'group edited successfully'
        
        self.form = GroupForm(self.isAdd)
        
        if not self.isAdd:
            group = actions.group_get(id)
            
            if group is None:
                usr.add_message('error', 'the requested group does not exist')
                url = url_for('users:ManageGroups')
                redirect(url)
            
            # assign group form defaults
            vals = group.to_dict()
            vals['assigned_users'] = actions.group_user_ids(group)
            vals['approved_permissions'], vals['denied_permissions'] = actions.group_assigned_perm_ids(group)
            self.form.set_defaults(vals)
    
    def post(self, id):        
        if self.form.is_valid():
            try:
                actions.group_update(id, **self.form.get_values())
                usr.add_message('notice', self.message)
                url = url_for('users:GroupManage')
                redirect(url)
            except Exception, e:
                # if the form can't handle the exception, re-raise it
                if not self.form.handle_exception(e):
                    raise
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()
                    
        self.default(id)
    
    def default(self, id):
        
        self.assign('actionName', self.actionName)
        self.assign('formHtml', self.form.render())
        
class GroupManage(ProtectedPageView):
    def prep(self):
        self.require = ('users-manage')
    
    def default(self):
        self.assign('groups', actions.group_list())

class GroupDelete(ProtectedRespondingView):
    def prep(self):
        self.require = ('users-manage')
    
    def default(self, id):
        if actions.group_delete(id):
            usr.add_message('notice', 'group deleted')
        else:
            usr.add_message('error', 'groupo was not found')
            
        url = url_for('users:GroupManage')
        redirect(url)
        
class PermissionUpdate(ProtectedPageView):
    def prep(self):
        self.require = ('users-manage')
    
    def setup(self, id):
        from forms import PermissionForm
        
        if id is None:
            self.isAdd = True
            self.actionName = 'Add'
            self.message = 'permission added'
        else:
            self.isAdd = False
            self.actionName = 'Edit'
            self.message = 'permission edited successfully'
        
        self.form = PermissionForm(self.isAdd)
        
        if not self.isAdd:
            permission = actions.permission_get(id)
            
            if permission is None:
                usr.add_message('error', 'the requested permission does not exist')
                url = url_for('users:ManagePermissions')
                redirect(url)
                
            self.form.set_defaults(permission.to_dict())
    
    def post(self, id):        
        if self.form.is_valid():
            try:
                actions.permission_update(id, **self.form.get_values())
                usr.add_message('notice', self.message)
                url = url_for('users:PermissionManage')
                redirect(url)
            except Exception, e:
                # if the form can't handle the exception, re-raise it
                if self.form.handle_exception(e) == False:
                    raise
        elif self.form.is_submitted():
            # form was submitted, but invalid
            self.form.assign_user_errors()
                    
        self.default(id)
    
    def default(self, id):
        
        self.assign('actionName', self.actionName)
        self.assign('formHtml', self.form.render())
        
class PermissionManage(ProtectedPageView):
    def prep(self):
        self.require = ('users-manage')
    
    def default(self):
        self.assign('permissions', actions.permission_list())

class PermissionDelete(ProtectedRespondingView):
    def prep(self):
        self.require = ('users-manage')
    
    def default(self, id):
        if actions.permission_delete(id):
            usr.add_message('notice', 'permission deleted')
        else:
            usr.add_message('error', 'permission was not found')
            
        url = url_for('users:PermissionManage')
        redirect(url)

class NewUserEmail(PublicTextSnippetView):
    def default(self, login_id, password):
        self.assign('login_id', login_id)
        self.assign('password', password)
        
        self.assign('login_url', url_for('users:Login', _external=True))
        self.assign('index_url', index_url(True))
        
class ChangePasswordEmail(PublicTextSnippetView):
    def default(self, login_id, password):
        self.assign('login_id', login_id)
        self.assign('password', password)

        self.assign('login_url', url_for('users:Login', _external=True))
        self.assign('index_url', index_url(True))

