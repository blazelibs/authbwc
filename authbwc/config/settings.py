from basebwa.lib.cpanel import ControlPanelSection, ControlPanelGroup, ControlPanelLink
from blazeweb.config import ComponentSettings


class Settings(ComponentSettings):

    def init(self):

        self.add_route('/users/<action>', endpoint='auth:UserCrud')
        self.add_route('/users/<action>/<int:objid>', endpoint='auth:UserCrud')
        self.add_route('/users/permissions/<int:objid>', 'auth:PermissionMap')
        self.add_route('/users/login', 'auth:Login')
        self.add_route('/users/logout', 'auth:Logout')
        self.add_route('/users/change-password', 'auth:ChangePassword')
        self.add_route('/users/recover-password', 'auth:LostPassword')
        self.add_route('/users/reset-password/<login_id>/<key>', 'auth:ResetPassword')
        self.add_route('/groups/<action>', endpoint='auth:GroupCrud')
        self.add_route('/groups/<action>/<int:objid>', endpoint='auth:GroupCrud')
        self.add_route('/permissions/<action>', endpoint='auth:PermissionCrud')
        self.add_route('/permissions/<action>/<int:objid>', endpoint='auth:PermissionCrud')
        self.add_route('/users/profile', 'auth:UserProfile')

        self.for_me.cp_nav.enabled = True
        self.for_me.cp_nav.section = ControlPanelSection(
            "Users",
            'auth-manage',
            ControlPanelGroup(
                ControlPanelLink('User Add', 'auth:UserCrud', action='add'),
                ControlPanelLink('Users Manage', 'auth:UserCrud', action='manage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Group Add', 'auth:GroupCrud', action='add'),
                ControlPanelLink('Groups Manage', 'auth:GroupCrud', action='manage'),
            ),
            ControlPanelGroup(
                ControlPanelLink('Permissions Manage', 'auth:PermissionCrud', action='manage'),
            )
        )

        # where should we go after a user logins in?  If nothing is set,
        # default to current_url(root_only=True)
        self.for_me.after_login_url = None

        # default values can be set when doing init-db to avoid the command
        # prompt
        self.for_me.admin.username = None
        self.for_me.admin.password = None
        self.for_me.admin.email = None

        # how long should a password reset link be good for? (in hours)
        self.for_me.password_rest_expires_after = 24

        # should the User entity be created? Can be useful when trying to use
        # this module with a DB that is already created and for which the
        # User entity needs to be tweaked.
        self.for_me.model_create_user = True
        self.for_me.model_create_group = True

        # application level password salt that will get joined with the random
        # salt of the record when hashing the password.  Use a random string of
        # at least 16 characters.  You can get one here:
        #
        #   https://www.grc.com/passwords.htm
        #
        # BE CAREFUL!!, if you use this setting and then lose the salt for value
        # for some reason, all your users will need to reset their passwords!
        #
        #
        # If left as None, it will not be used
        self.for_me.password_salt = None
