import datetime
from model.orm import User, Group, Permission
from model.metadata import group_permission_assignments as tbl_gpa
from model.metadata import user_permission_assignments as tbl_upa
from hashlib import sha512
from sqlalchemy import Column, literal
from sqlalchemy.exc import DatabaseError
from sqlalchemy.sql import select, and_, text, alias, join, case, or_
from pysmvt.exceptions import ActionError
from pysmvt import user as usr
from pysmvt import db, modimportauto
from pysmvt.utils import randchars, tolist
modimportauto('users.utils', ('send_new_user_email', 'send_change_password_email',
    'send_password_reset_email'))
modimportauto('users.model.autoloads', ('vuserperms'))

def user_update(id, **kwargs):
    
    if id is None:
        u = User()
        # when creating a new user, if the password is not set, assign it as
        # a random string assuming the email will get sent out to the user
        # and they will change it when they login
        if not kwargs.get('password', None):
            kwargs['password'] = randchars(8)
    else:
        u = User.get_by(id=id)
    
    # automatically turn on reset_password when the password get set manually
    # (i.e. when an admin does it), unless told not to (when a user does it
    # for their own account)
    if kwargs.get('password') and kwargs.get('pass_reset_ok', True):
        kwargs['reset_required'] = True
        
    # some values can not be set directly
    if kwargs.has_key('hash_pass'):
        del(kwargs['hash_pass'])   
    try: 
        u.from_dict(kwargs)
        u.groups = create_groups(kwargs.get('assigned_groups', []))
        db.sess.flush()
        permission_assignments_user(u, kwargs.get('approved_permissions', []), kwargs.get('denied_permissions', []))

        # if email fails, db trans will roll back
        #  initmod call will not have this flag
        if kwargs.get('email_notify'):
            if id is None:
                send_new_user_email(u, kwargs['password'])
            elif kwargs['password']:
                send_change_password_email(kwargs['login_id'], kwargs['password'], kwargs['email_address'])

        db.sess.commit()
    except:
        db.sess.rollback()
        raise

    return u

def user_add(safe=False, **kwargs):
    u = None
    try:
        u = user_update(None, **kwargs)
    except Exception, e:
        if safe == False or safe.lower() not in str(e).lower():
            raise

    return u

def create_groups(group_ids):
    groups = []
    if not isinstance(group_ids, list):
        group_ids = [group_ids]
    for gid in group_ids:
        groups.append(group_get(gid))
    return groups

def hash_pass(password):
    return sha512(password).hexdigest()
    
def user_update_password(id, **kwargs):
    dbsession = db.sess
    u = User.get_by(id=id)
    u.password = kwargs['password']
    u.reset_required = False
    dbsession.commit()

def user_lost_password(email_address):
    #email_address is validated in LostPasswordForm
    u = User.get_by(email_address=email_address)
    if not u:
        return False
    
    u.pass_reset_key = randchars(12)
    u.pass_reset_ts = datetime.datetime.utcnow()
    try:
        db.sess.flush()
        send_password_reset_email(u)
        db.sess.commit()
    except:
        db.sess.rollback()
        raise
    return True

def user_kill_reset_key(user):
    user.pass_reset_key = None
    user.pass_reset_ts = None
    try:
        db.sess.commit()
    except:
        db.sess.rollback()
        raise

def user_list():
    return User.query.all()

def user_get(id):
    return User.get_by(id=id)

def user_get_by_email(email_address):
    return User.get_by(email_address=email_address)

def user_get_by_login(login_id):
    return User.get_by(login_id=login_id)
    
def user_delete(id):
    dbsession = db.sess
    user = User.get_by(id=id)
    if user is not None:
        user.delete()
        dbsession.commit()
        return True
    return False

def user_group_ids(user):
    groups = Group.query.filter(Group.users.any(id=user.id)).all()
    return [g.id for g in groups]

def user_list_options():
    return [(u.id, u.login_id) for u in User.query.order_by('login_id')]

def user_assigned_perm_ids(user):
    dbsession = db.sess
    execute = dbsession.execute
    s = select(
        [tbl_upa.c.permission_id],
        and_(tbl_upa.c.user_id==user.id, tbl_upa.c.approved == 1)
        )
    approved = [r[0] for r in execute(s)]
    s = select(
        [tbl_upa.c.permission_id],
        and_(tbl_upa.c.user_id==user.id, tbl_upa.c.approved == -1)
        )
    denied = [r[0] for r in execute(s)]

    return approved, denied

def user_get_by_permissions_query(permissions):
    q = db.sess.query(User).select_from(
        User.table.join(vuserperms, User.id == vuserperms.c.user_id)
    ).filter(
        or_(
            vuserperms.c.user_approved == 1,
            and_(
                vuserperms.c.user_approved == None,
                or_(
                    vuserperms.c.group_denied == None,
                    vuserperms.c.group_denied >= 0,
                ),
                vuserperms.c.group_approved >= 1
            )
        )
    ).filter(
        vuserperms.c.permission_name.in_(tolist(permissions))
    )
    return q

def user_get_by_permissions(permissions):
    return user_get_by_permissions_query(permissions).all()

def user_permission_map(uid):
    dbsession = db.sess
    s = select([text('*')], 'user_id = :x', from_obj='v_users_permissions')
    results = dbsession.execute(s, {'x':uid})
    retval = []
    for row in results:
        nrow = {}
        for key, value in row.items():
            if value is None:
                nrow[key] = 0
            else:
                nrow[key] = value
        
        if nrow['user_approved'] == -1:
            approved = False
            #print 1
        elif nrow['user_approved'] == 1:
            approved = True
            #print 2
        elif nrow['group_denied'] <= -1:
            approved = False
            #print 3
        elif nrow['group_approved'] >= 1:
            approved = True
            #print 4
        else:
            approved = False
            #print 5
        
        nrow['resulting_approval'] = approved
        retval.append(nrow)
    return retval

def user_permission_map_groups(uid):
    dbsession = db.sess
    s = select([text('*')], 'user_id = :x', from_obj='v_users_user_group_permissions')
    results = dbsession.execute(s, {'x':uid})
    retval = {}
    for row in results:
        if not retval.has_key(row['permission_id']):
            retval[row['permission_id']] = {'approved' : [], 'denied' : []}
        if row['group_approved'] <= -1:
            retval[row['permission_id']]['denied'].append({'name':row['group_name'], 'id':row['group_id']})
        elif row['group_approved'] >= 1:
            retval[row['permission_id']]['approved'].append({'name':row['group_name'], 'id':row['group_id']})
    return retval

def user_validate(**kwargs):
    return User.get_by(login_id = kwargs['login_id'], pass_hash=hash_pass(kwargs['password']))

def load_session_user(user):
    usr.set_attr('id', user.id)
    usr.set_attr('login_id', user.login_id)
    usr.set_attr('super_user', user.super_user)
    usr.set_attr('reset_required', user.reset_required)
    usr.authenticated()
    
    # now permissions
    for row in user_permission_map(user.id):
        if row['resulting_approval'] or user.super_user:
            usr.add_perm(row['permission_name'])

## Group Actions

def group_update(id, **kwargs):
    try: 
        if id is not None:
           return group_edit(id, **kwargs)
        else:
           return group_add(**kwargs)
            
    except DatabaseError, e:
        db.sess.rollback()
        raise
    
def group_add(safe=False, name=None, assigned_users=None, approved_permissions=None,
            denied_permissions=None, **kwargs):
    dbsession = db.sess
    try:
        g = Group()
        g.name = name
        g.users = create_users(assigned_users)
        dbsession.flush()
        permission_assignments_group(g, approved_permissions, denied_permissions)
        dbsession.commit()
        return g
    except Exception, e:
        dbsession.rollback()
        if safe == False or safe not in str(e):
            raise
        return group_get_by_name(name)

def group_edit(id, **kwargs):
    dbsession = db.sess
    g = Group.get_by(id=id)
    g.from_dict(kwargs)
    g.users = create_users(kwargs['assigned_users'])
    permission_assignments_group(g, kwargs['approved_permissions'], kwargs['denied_permissions'])
    dbsession.commit()
    return g

def create_users(user_ids):
    users = []
    if user_ids is None:
        return users
    if not isinstance(users, list):
        user_ids = [user_ids]
    for uid in user_ids:
        users.append(user_get(uid))
    return users

def group_list():
    return Group.query.order_by('name').all()

def group_list_options():
    return [(g.id, g.name) for g in Group.query.order_by('name')]

def group_get(id):
    return Group.get_by(id=id)

def group_get_by_name(name):
    return Group.get_by(name=name)
    
def group_delete(id):
    dbsession = db.sess
    # @todo: the user/group relationship needs to be deleted too
    group = Group.get_by(id=id)
    
    if group is not None:
        group.delete()
        dbsession.commit()
        return True
    return False

def group_delete_by_name(name):
    group = group_get_by_name(name)
    if group:
        return group_delete(group.id)
    return False

def group_user_ids(group):
    users = User.query.filter(User.groups.any(id=group.id)).all()
    return [u.id for u in users]

def group_assigned_perm_ids(group):
    dbsession = db.sess
    execute = dbsession.execute
    s = select(
        [tbl_gpa.c.permission_id],
        and_(tbl_gpa.c.group_id==group.id, tbl_gpa.c.approved == 1)
        )
    approved = [r[0] for r in execute(s)]
    s = select(
        [tbl_gpa.c.permission_id],
        and_(tbl_gpa.c.group_id==group.id, tbl_gpa.c.approved == -1)
        )
    denied = [r[0] for r in execute(s)]

    return approved, denied

def group_add_permissions_to_existing(gname, approved=[], denied=[]):
    g = group_get_by_name(gname)
    capproved, cdenied = group_assigned_perm_ids(g)
    for permid in tolist(approved):
        if permid not in capproved:
            capproved.append(permid)
    for permid in tolist(denied):
        if permid not in cdenied:
            cdenied.append(permid)
    try:
        permission_assignments_group(g, capproved, cdenied)
        db.sess.commit()
    except:
        db.sess.rollback()
        raise
        
## Permissions

def permission_update(id, **kwargs):
    try:
        if id is not None:
            permission_edit(id, **kwargs)
        else:
            permission_add(**kwargs)
    except:
        db.sess.rollback()
        raise
    
def permission_add(safe=False, **kwargs):
    try:
        dbsession = db.sess
        p = Permission()
        p.from_dict(kwargs)
        dbsession.commit()
        return p
    except Exception, e:
        dbsession.rollback()
        if safe == False or safe not in str(e):
            raise
        return permission_get_by_name(kwargs['name'])

def permission_edit(id, **kwargs):
    dbsession = db.sess
    p = Permission.get_by(id=id)
    p.from_dict(kwargs)
    dbsession.commit()

def permission_list():
    return Permission.query.order_by('name').all()

def permission_list_options():
    return [(p.id, p.name) for p in Permission.query.order_by('name')]

def permission_get(id):
    return Permission.get_by(id=id)
    
def permission_get_by_name(name):
    return Permission.get_by(name=name)

def permission_delete(id):
    permission = Permission.get_by(id=id)
    if permission is not None:
        permission.delete()
        db.sess.commit()
        return True
    return False

def permission_assignments_group(group, approved_perm_ids, denied_perm_ids):
    dbsession = db.sess
    # delete existing permission assignments for this group (i.e. we start over)
    dbsession.execute(tbl_gpa.delete(tbl_gpa.c.group_id == group.id))
    
    # insert "approved" records
    if approved_perm_ids is not None and len(approved_perm_ids) != 0:
        # prep insert values
        insval = []
        for pid in approved_perm_ids:
            # print 'inserting %s:%s' % (group.id, pid)
            insval.append({'group_id' : group.id, 'permission_id' : pid, 'approved' : 1})
        # do inserts
        dbsession.execute(tbl_gpa.insert(), insval)
    
    # insert "denied" records
    if denied_perm_ids is not None and len(denied_perm_ids) != 0:
        # prep insert values
        insval = []
        for pid in denied_perm_ids:
            insval.append({'group_id' : group.id, 'permission_id' : pid, 'approved' : -1})
        # do inserts
        dbsession.execute(tbl_gpa.insert(), insval)

    return

def permission_assignments_group_by_name(group_name, approved_perm_list=[], denied_perm_list=[]):
    # Note: this function is a wrapper for permission_assignments_group and will commit db trans
    group = group_get_by_name(group_name)
    approved_perm_ids = [item.id for item in [permission_get_by_name(perm) for perm in tolist(approved_perm_list)]]
    denied_perm_ids = [item.id for item in [permission_get_by_name(perm) for perm in tolist(denied_perm_list)]]
    permission_assignments_group(group, approved_perm_ids, denied_perm_ids)
    db.sess.commit()
    return

def permission_assignments_user(user, approved_perm_ids, denied_perm_ids):
    dbsession = db.sess
    # delete existing permission assignments for this user (i.e. we start over)
    dbsession.execute(tbl_upa.delete(tbl_upa.c.user_id == user.id))
    
    # insert "approved" records
    if approved_perm_ids is not None and len(approved_perm_ids) != 0:
        # prep insert values
        insval = []
        for pid in approved_perm_ids:
            insval.append({'user_id' : user.id, 'permission_id' : pid, 'approved' : 1})
        # do inserts
        dbsession.execute(tbl_upa.insert(), insval)
    
    # insert "denied" records
    if denied_perm_ids is not None and len(denied_perm_ids) != 0:
        # prep insert values
        insval = []
        for pid in denied_perm_ids:
            insval.append({'user_id' : user.id, 'permission_id' : pid, 'approved' : -1})
        # do inserts
        dbsession.execute(tbl_upa.insert(), insval)

    return
    
