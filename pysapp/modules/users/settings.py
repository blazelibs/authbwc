# -*- coding: utf-8 -*-

from werkzeug.routing import Rule
from pysmvt.config import QuickSettings
from pysapp.utils import ControlPanelSection, ControlPanelGroup, ControlPanelLink

class Settings(QuickSettings):

    def __init__(self):
        QuickSettings.__init__(self)

        
        self.routes = [
            Rule('/users/add', defaults={'id': None}, endpoint='users:Update'),
            Rule('/users/edit/<int:id>', endpoint='users:Update'),
            Rule('/users/manage', endpoint='users:Manage'),
            Rule('/users/delete/<int:id>', endpoint='users:Delete'),
            Rule('/users/permissions/<int:uid>', endpoint='users:PermissionMap'),
            Rule('/users/login', endpoint='users:Login'),
            Rule('/users/logout', endpoint='users:Logout'),
            Rule('/users/change_password', endpoint='users:ChangePassword'),
            Rule('/users/recover_password', endpoint='users:LostPassword'),
            Rule('/groups/add', defaults={'id': None}, endpoint='users:GroupUpdate'),
            Rule('/groups/edit/<int:id>', endpoint='users:GroupUpdate'),
            Rule('/groups/manage', endpoint='users:GroupManage'),
            Rule('/groups/delete/<int:id>', endpoint='users:GroupDelete'),
            Rule('/permissions/add', defaults={'id': None}, endpoint='users:PermissionUpdate'),
            Rule('/permissions/edit/<int:id>', endpoint='users:PermissionUpdate'),
            Rule('/permissions/manage', endpoint='users:PermissionManage'),
            Rule('/permissions/delete/<int:id>', endpoint='users:PermissionDelete'),
        ]
        self.cp_nav.enabled=True
        self.cp_nav.section = ControlPanelSection(
            "Users",
            'users-manage',
            ControlPanelGroup(
                ControlPanelLink('User Add', 'users:Update'),
                ControlPanelLink('Users Manage', 'users:Manage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Group Add', 'users:GroupUpdate'),
                ControlPanelLink('Groups Manage', 'users:GroupManage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Permission Add', 'users:PermissionUpdate'),
                ControlPanelLink('Permissions Manage', 'users:PermissionManage'),
            )
        )
        
        # where should we go after a user logins in?  If nothing is set,
        # default to index_url()
        self.after_login_url = None
        
        # default values can be set when doing initmod() to avoid the command
        # prompt
        self.admin.username = None
        self.admin.password = None
        self.admin.email = None

