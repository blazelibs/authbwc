# -*- coding: utf-8 -*-
import logging

from blazeweb.content import getcontent
from blazeweb.globals import settings, user
from blazeweb.mail import EmailMessage, mail_programmers
from blazeweb.routing import current_url
from blazeweb.utils import exception_with_context

from plugstack.auth.model.actions import user_permission_map

log = logging.getLogger(__name__)

def after_login_url():
    if settings.plugins.auth.after_login_url:
        if callable(settings.plugins.auth.after_login_url):
            return settings.plugins.auth.after_login_url()
        else:
            return settings.plugins.auth.after_login_url
    return current_url(root_only=True)

def load_session_user(user_obj):
    user.id = user_obj.id
    user.login_id = user_obj.login_id
    user.is_super_user = bool(user_obj.super_user)
    user.reset_required = user_obj.reset_required
    user.is_authenticated = True

    # now permissions
    for row in user_permission_map(user_obj.id):
        if row['resulting_approval'] or user_obj.super_user:
            user.add_token(row['permission_name'])

def send_new_user_email(user_obj):
    subject = '%s - User Login Information' % (settings.name.full)
    body = getcontent('auth:new_user_email.txt', user_obj=user_obj).primary
    email = EmailMessage(subject, body, None, [user_obj.email_address])
    return send_email_or_log_error(email)

def send_change_password_email(user_obj):
    subject = '%s - User Password Reset' % (settings.name.full)
    body = getcontent('auth:change_password_email.txt', user_obj=user_obj).primary
    email = EmailMessage(subject, body, None, [user_obj.email_address])
    return send_email_or_log_error(email)

def send_password_reset_email(user_obj):
    subject = '%s - User Password Reset' % (settings.name.full)
    body = getcontent('auth:password_reset_email.txt', user_obj=user_obj).primary
    email = EmailMessage(subject, body, None, [user_obj.email_address])
    return send_email_or_log_error(email)

def send_email_or_log_error(email):
    try:
        email.send()
    except Exception, e:
        log.error('Exception while sending email in auth plugin: %s' % str(e))
        mail_programmers('%s - email send error' % settings.name.short, exception_with_context(), fail_silently=True)
        return False
    return True

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
    from plugstack.auth.model.actions import user_update

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
    user_update(
        None,
        login_id = unicode(ulogin),
        email_address = unicode(uemail),
        password = p1,
        super_user = True,
        _ignore_unique_exception=True
        )
