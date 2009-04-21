# -*- coding: utf-8 -*-
from os import path
from pysmvt import settings
from pysmvt.script import console_broadcast

@console_broadcast
def action_users_initdb():
    ''' sets up the database after the model objects have been created '''
    from pysmvt import db
    # add the sql views
    dbsession = db.sess
    am_dir = path.dirname(path.abspath(__file__))
    filename = '%s.sql' % db.engine.dialect.name
    sql = file(path.join(am_dir, 'sql', filename)).read()
    for statement in sql.split('--statement-break'):
        statement.strip()
        if statement:
            dbsession.execute(statement)
    dbsession.commit()

@console_broadcast
def action_users_initmod():
    ''' sets up the module after the database is setup'''
    addperms_init()
    addadmin_init()
    addadmingroup_init()

def addperms_init():
    # this module's permissions
    from actions import permission_add
    permission_add(name=u'users-manage', safe='unique')

def addadmin_init():
    from getpass import getpass
    from actions import user_add
    
    defaults = settings.modules.users.admin
    # add a default administrative user
    if defaults.username and defaults.password and defaults.email:
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

def addadmingroup_init():
    from actions import group_add
    group_add(name=u'admin', assigned_users=[], approved_permissions=[], denied_permissions=[], safe='unique')
