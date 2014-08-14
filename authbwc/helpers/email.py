import logging

from blazeweb.content import getcontent
from blazeweb.globals import settings
from blazeweb.mail import EmailMessage, mail_programmers
from blazeweb.utils import exception_with_context

log = logging.getLogger(__name__)


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


def send_reset_password_email(user_obj):
    subject = '%s - User Password Reset' % (settings.name.full)
    body = getcontent('auth:password_reset_email.txt', user_obj=user_obj).primary
    email = EmailMessage(subject, body, None, [user_obj.email_address])
    return send_email_or_log_error(email)


def send_email_or_log_error(email):
    try:
        email.send()
    except Exception, e:
        log.error('Exception while sending email in auth component: %s' % str(e))
        mail_programmers(
            '%s - email send error' % settings.name.short,
            exception_with_context(),
            fail_silently=True
        )
        return False
    return True
