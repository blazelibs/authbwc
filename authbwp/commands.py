from pysmvt.script import console_broadcast, console_dispatch

@console_dispatch
def action_users_addadmin():
    """ used to add an admin user to the database """
    from plugstack.auth.lib.utils import add_administrative_user
    add_administrative_user(allow_profile_defaults=False)