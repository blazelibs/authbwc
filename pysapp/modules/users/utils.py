# -*- coding: utf-8 -*-
from pysmvt import settings, getview
from pysmvt.routing import current_url
from pysmvt.mail import EmailMessage

def after_login_url():
    if settings.modules.users.after_login_url:
        if callable(settings.modules.users.after_login_url):
            return settings.modules.users.after_login_url()
        else:
            return settings.modules.users.after_login_url
    return current_url(root_only=True)

def send_new_user_email(login_id, password, email_address):
    subject = '%s - User Login Information' % (settings.name.full)
    body = getview('users:NewUserEmail', login_id=login_id, password=password)
    email = EmailMessage(subject, body, None, [email_address])
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