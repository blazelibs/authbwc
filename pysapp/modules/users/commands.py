# -*- coding: utf-8 -*-
from os import path
from actions import user_add, permission_add, group_add, permission_get_by_name
from pysmvt import db, settings

def action_users_initdb():
    ''' sets up the database after the model objects have been created '''
    
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
broadcast_initdb = action_users_initdb
    
def action_users_initmod():
    ''' sets up the module after the database is setup'''
    addperms_init()
    addadmin_init()
    addadmingroup_init()
broadcast_initmod = action_users_initmod

def addperms_init():
    # this module's permissions
    permission_add(name=u'users-manage', safe='unique')

def addadmin_init():
    from getpass import getpass

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
             approved_permissions = None, denied_permissions = None )

def addadmingroup_init():
    perms = [permission_get_by_name(u'users-manage').id]
    group_add(name=u'admin', assigned_users=[], approved_permissions=perms, denied_permissions=[])
