# -*- coding: utf-8 -*-
from os import path
from pysmvt import settings, modimport
from pysmvt.script import console_broadcast, console_dispatch

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
    
    # this module's permissions
    from actions import permission_add
    permission_add(name=u'users-manage', safe='unique')

@console_broadcast
def action_users_testdata():
    from actions import permission_add
    permission_add(name=u'ugp_approved')
    permission_add(name=u'ugp_denied')
    permission_add(name=u'users-test1')
    permission_add(name=u'users-test2')
    permission_add(name=u'prof-test-1')
    permission_add(name=u'prof-test-2')

@console_broadcast
def action_users_initdata():
    ''' sets up the module after the database is setup'''
    addadmin_init()
    addadmingroup_init()

def addadmin_init():
    from getpass import getpass
    user_add = modimport('users.actions', 'user_add')
    
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

@console_dispatch
def action_users_addadmin():
    """ used to add an admin user to the database """
    # ovverride settings so that we can force the prompts
    username = settings.modules.users.admin.username
    settings.modules.users.admin.username = None
    addadmin_init()
    settings.modules.users.admin.username = username
