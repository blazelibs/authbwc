# -*- coding: utf-8 -*-
from pysmvt import settings, getview, modimport
from pysmvt.routing import current_url
from pysmvt.mail import EmailMessage

def after_login_url():
    if settings.modules.users.after_login_url:
        if callable(settings.modules.users.after_login_url):
            return settings.modules.users.after_login_url()
        else:
            return settings.modules.users.after_login_url
    return current_url(root_only=True)

def send_new_user_email(user_obj, password):
    subject = '%s - User Login Information' % (settings.name.full)
    body = getview('users:NewUserEmail', user_obj=user_obj, password=password)
    email = EmailMessage(subject, body, None, [user_obj.email_address])
    email.send()

def send_change_password_email(login_id, password, email_address):
    subject = '%s - User Password Reset' % (settings.name.full)
    body = getview('users:ChangePasswordEmail', login_id=login_id, password=password)
    email = EmailMessage(subject, body, None, [email_address])
    email.send()

def send_password_reset_email(user):
    subject = '%s - User Password Reset' % (settings.name.full)
    body = getview('users:PasswordResetEmail', user=user)
    email = EmailMessage(subject, body, None, [user.email_address])
    email.send()

def validate_password_complexity(password):
    if len(password) < 6:
        return 'Enter a value at least 6 characters long'
    if len(password) > 25:
        return 'Enter a value less than 25 characters long'
    return True

def note_password_complexity():
    return 'min 6 chars, max 25 chars'

def add_administrative_user(allow_profile_defaults=True):
    from getpass import getpass
    user_add = modimport('users.actions', 'user_add')
    
    defaults = settings.modules.users.admin
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
    user_add(login_id = unicode(ulogin), email_address = unicode(uemail), password = p1,
             super_user = True, assigned_groups = None,
             approved_permissions = None, denied_permissions = None, safe='unique' )