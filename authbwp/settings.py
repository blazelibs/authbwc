# -*- coding: utf-8 -*-

from werkzeug.routing import Rule
from pysmvt.config import QuickSettings
from pysapp.utils import ControlPanelSection, ControlPanelGroup, ControlPanelLink

class Settings(QuickSettings):

    def __init__(self):
        QuickSettings.__init__(self)

        
        self.routes = [
            Rule('/users/add', defaults={'id': None}, endpoint='authbwp:UserUpdate'),
            Rule('/users/edit/<int:id>', endpoint='authbwp:UserUpdate'),
            Rule('/users/manage', endpoint='authbwp:UserManage'),
            Rule('/users/delete/<int:id>', endpoint='authbwp:UserDelete'),
            Rule('/users/permissions/<int:uid>', endpoint='authbwp:PermissionMap'),
            Rule('/users/login', endpoint='authbwp:Login'),
            Rule('/users/logout', endpoint='authbwp:Logout'),
            Rule('/users/change_password', endpoint='authbwp:ChangePassword'),
            Rule('/users/recover_password', endpoint='authbwp:LostPassword'),
            Rule('/users/password-reset/<login_id>/<key>', endpoint='authbwp:ResetPassword'),
            Rule('/groups/add', defaults={'id': None}, endpoint='authbwp:GroupUpdate'),
            Rule('/groups/edit/<int:id>', endpoint='authbwp:GroupUpdate'),
            Rule('/groups/manage', endpoint='authbwp:GroupManage'),
            Rule('/groups/delete/<int:id>', endpoint='authbwp:GroupDelete'),
            Rule('/permissions/edit/<int:id>', endpoint='authbwp:PermissionUpdate'),
            Rule('/permissions/manage', endpoint='authbwp:PermissionManage'),
            Rule('/users/profile', endpoint='authbwp:UserProfile'),
        ]
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
