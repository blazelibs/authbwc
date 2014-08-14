from blazeweb.events import signal
from blazeweb.globals import user
from blazeweb.views import forward


def check_reset_required(sender, endpoint, urlargs):
    skip_endpoints = ['auth:ChangePassword', 'auth:Logout']
    if user.is_authenticated and user.reset_required and endpoint not in skip_endpoints:
        forward('auth:ChangePassword')

signal('blazeweb.response_cycle.started').connect(check_reset_required)
