# -*- coding: utf-8 -*-

from pysmvt.config import PluginSettings
from pysapp.utils import ControlPanelSection, ControlPanelGroup, ControlPanelLink

class Settings(PluginSettings):

    def __init__(self):
        PluginSettings.__init__(self)

        self.add_route('/users/add', 'authbwp:UserUpdate', id=None)
        self.add_route('/users/edit/<int:id>', 'authbwp:UserUpdate')
        self.add_route('/users/manage', 'authbwp:UserManage')
        self.add_route('/users/delete/<int:id>', 'authbwp:UserDelete')
        self.add_route('/users/permissions/<int:uid>', 'authbwp:PermissionMap')
        self.add_route('/users/login', 'authbwp:Login')
        self.add_route('/users/logout', 'authbwp:Logout')
        self.add_route('/users/change_password', 'authbwp:ChangePassword')
        self.add_route('/users/recover_password', 'authbwp:LostPassword')
        self.add_route('/users/password-reset/<login_id>/<key>', 'authbwp:ResetPassword')
        self.add_route('/groups/add', 'authbwp:GroupUpdate', id=None)
        self.add_route('/groups/edit/<int:id>', 'authbwp:GroupUpdate')
        self.add_route('/groups/manage', 'authbwp:GroupManage')
        self.add_route('/groups/delete/<int:id>', 'authbwp:GroupDelete')
        self.add_route('/permissions/edit/<int:id>', 'authbwp:PermissionUpdate')
        self.add_route('/permissions/manage', 'authbwp:PermissionManage')
        self.add_route('/users/profile', 'authbwp:UserProfile')
        
        self.cp_nav.enabled=True
        self.cp_nav.section = ControlPanelSection(
            "Users",
            'users-manage',
            ControlPanelGroup(
                ControlPanelLink('User Add', 'authbwp:UserUpdate'),
                ControlPanelLink('Users Manage', 'authbwp:UserManage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Group Add', 'authbwp:GroupUpdate'),
                ControlPanelLink('Groups Manage', 'authbwp:GroupManage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Permissions Manage', 'authbwp:PermissionManage'),
            )
        )
        
        # where should we go after a user logins in?  If nothing is set,
        # default to current_url(root_only=True)
        self.after_login_url = None
        
        # default values can be set when doing initmod() to avoid the command
        # prompt
        self.admin.username = None
        self.admin.password = None
        self.admin.email = None

        # how long should a password reset link be good for? (in hours)
        self.password_rest_expires_after = 24
