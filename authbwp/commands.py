from blazeweb.script import console_dispatch

@console_dispatch
def action_users_addadmin():
    """ used to add an admin user to the database """
    from compstack.auth.helpers import add_administrative_user
    add_administrative_user(allow_profile_defaults=False)
