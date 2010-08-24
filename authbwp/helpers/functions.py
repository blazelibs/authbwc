from blazeweb.globals import settings

from plugstack.auth.model.orm import User

def add_administrative_user(allow_profile_defaults=True):
    from getpass import getpass

    defaults = settings.plugins.auth.admin
    # add a default administrative user
    if allow_profile_defaults and defaults.username and defaults.password and defaults.email:
        ulogin = defaults.username
        uemail = defaults.email
        p1 = defaults.password
    else:
        ulogin = raw_input("User's Login id:\n> ")
        uemail = raw_input("User's email:\n> ")
        while True:
            p1 = getpass("User's password:\n> ")
            p2 = getpass("confirm password:\n> ")
            if p1 == p2:
                break
    User.add_iu(
        login_id = unicode(ulogin),
        email_address = unicode(uemail),
        password = p1,
        super_user = True
        )
