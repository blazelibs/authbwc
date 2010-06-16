from pysmvt.config import PluginSettings
from pysapp.utils import ControlPanelSection, ControlPanelGroup, ControlPanelLink

class Settings(PluginSettings):

    def __init__(self):
        PluginSettings.__init__(self)

        self.add_route('/users/add', 'auth:UserUpdate', defaults={'oid':None})
        self.add_route('/users/edit/<int:oid>', 'auth:UserUpdate')
        self.add_route('/users/manage', 'auth:UserManage')
        self.add_route('/users/delete/<int:oid>', 'auth:UserDelete')
        self.add_route('/users/permissions/<int:uid>', 'auth:PermissionMap')
        self.add_route('/users/login', 'auth:Login')
        self.add_route('/users/logout', 'auth:Logout')
        self.add_route('/users/change_password', 'auth:ChangePassword')
        self.add_route('/users/recover_password', 'auth:LostPassword')
        self.add_route('/users/password-reset/<login_id>/<key>', 'auth:ResetPassword')
        self.add_route('/groups/add', 'auth:GroupUpdate', defaults={'oid':None})
        self.add_route('/groups/edit/<int:oid>', 'auth:GroupUpdate')
        self.add_route('/groups/manage', 'auth:GroupManage')
        self.add_route('/groups/delete/<int:oid>', 'auth:GroupDelete')
        self.add_route('/permissions/edit/<int:oid>', 'auth:PermissionUpdate')
        self.add_route('/permissions/manage', 'auth:PermissionManage')
        self.add_route('/users/profile', 'auth:UserProfile')

        self.cp_nav.enabled=True
        self.cp_nav.section = ControlPanelSection(
            "Users",
            'auth-manage',
            ControlPanelGroup(
                ControlPanelLink('User Add', 'auth:UserUpdate'),
                ControlPanelLink('Users Manage', 'auth:UserManage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Group Add', 'auth:GroupUpdate'),
                ControlPanelLink('Groups Manage', 'auth:GroupManage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Permissions Manage', 'auth:PermissionManage'),
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
