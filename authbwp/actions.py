import datetime
from plugstack.auth.model.orm import User, Group, Permission
from plugstack.auth.model.metadata import group_permission_assignments as tbl_gpa
from plugstack.auth.model.metadata import user_permission_assignments as tbl_upa
from hashlib import sha512
from sqlalchemy.sql import select, and_, alias, or_, func
from sqlalchemy.sql.functions import sum
from sqlalchemy.orm import join
from pysmvt import user as usr
from plugstack.sqlalchemybwp import db
from pysmvt.utils import randchars, tolist
from plugstack.auth.lib.utils import send_new_user_email, send_change_password_email, send_password_reset_email
from plugstack.auth.lib.db import query_user_group_permissions, query_users_permissions
    
def user_update(id, **kwargs):

    if id is None:
        u = User()
        db.sess.add(u)
        # when creating a new user, if the password is not set, assign it as
        # a random string assuming the email will get sent out to the user
        # and they will change it when they login
        if not kwargs.get('password', None):
            kwargs['password'] = randchars(8)
    else:
        u = user_get(id)
    
    # automatically turn on reset_password when the password get set manually
    # (i.e. when an admin does it), unless told not to (when a user does it
    # for their own account)
    if kwargs.get('password') and kwargs.get('pass_reset_ok', True):
        kwargs['reset_required'] = True

    for k, v in kwargs.iteritems():
        try:
            # some values can not be set directly
            if k in ('pass_hash', 'assigned_groups', 'approved_permissions', 'denied_permissions'):
                pass
            else:
                setattr(u, k, v)
        except AttributeError:
            pass

    try:
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
    u = user_get(id)
    u.password = kwargs['password']
    u.reset_required = False
    dbsession.commit()

def user_lost_password(email_address):
    #email_address is validated in LostPasswordForm
    u = user_get_by_email(email_address)
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
    return db.sess.query(User).all()

def user_get(id):
    return db.sess.query(User).get(id)

def user_get_by_email(email_address):
    return db.sess.query(User).filter(func.lower(User.email_address)==func.lower(email_address)).first()

def user_get_by_login(login_id):
    return db.sess.query(User).filter(User.login_id==login_id).first()
    
def user_delete(id):
    dbsession = db.sess
    user = user_get(id)
    if user is not None:
        db.sess.delete(user)
        try:
            dbsession.commit()
        except:
            dbsession.rollback()
            raise
        return True
    return False

def user_group_ids(user):
    groups = db.sess.query(Group).filter(Group.users.any(id=user.id)).all()
    return [g.id for g in groups]

def user_list_options():
    return [(u.id, u.login_id) for u in db.sess.query(User).order_by('login_id')]

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
    vuserperms = query_users_permissions().alias()
    q = db.sess.query(User).select_from(
        join(User, vuserperms, User.id == vuserperms.c.user_id)
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
    user_perm = query_users_permissions()
    s = select([user_perm.c.user_id,
                 user_perm.c.permission_id,
                 user_perm.c.permission_name,
                 user_perm.c.login_id,
                 user_perm.c.user_approved,
                 user_perm.c.group_approved,
                 user_perm.c.group_denied,],
               from_obj=user_perm).where(user_perm.c.user_id==uid)
    results = dbsession.execute(s)
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
        elif nrow['user_approved'] == 1:
            approved = True
        elif nrow['group_denied'] <= -1:
            approved = False
        elif nrow['group_approved'] >= 1:
            approved = True
        else:
            approved = False
        
        nrow[u'resulting_approval'] = approved
        retval.append(nrow)
    return retval

def user_permission_map_groups(uid):
    dbsession = db.sess
    user_group_perm = query_user_group_permissions()
    s = select([user_group_perm.c.permission_id,
                user_group_perm.c.group_name,
                user_group_perm.c.group_id,
                user_group_perm.c.group_approved],
               from_obj=user_group_perm).where(user_group_perm.c.user_id==uid)
    results = dbsession.execute(s)
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
    return db.sess.query(User).filter_by(login_id=kwargs['login_id'], pass_hash=hash_pass(kwargs['password'])).first()

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
    dbsession = db.sess
    if id is None:
        g = Group()
        db.sess.add(g)
    else:
        g = group_get(id)

    for k, v in kwargs.iteritems():
        try:
            # some values can not be set directly
            if k in ('assigned_users', 'approved_permissions', 'denied_permissions'):
                pass
            else:
                setattr(g, k, v)
        except AttributeError:
            pass

    try:
        g.users = create_users(kwargs.get('assigned_users',[]))
        permission_assignments_group(g, kwargs.get('approved_permissions',[]), kwargs.get('denied_permissions',[]))
        dbsession.commit()
    except:
        dbsession.rollback()
        raise
    return g

def group_add(safe=False, **kwargs):
    try:
        return group_update(None, **kwargs)
    except Exception, e:
        if safe == False or safe not in str(e):
            raise
        return group_get_by_name(kwargs['name'])

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
    return db.sess.query(Group).order_by(Group.name).all()

def group_list_options():
    return [(g.id, g.name) for g in db.sess.query(Group).order_by(Group.name)]

def group_get(id):
    return db.sess.query(Group).get(id)

def group_get_by_name(name):
    return db.sess.query(Group).filter(Group.name==name).first()
    
def group_delete(id):
    dbsession = db.sess
    group = group_get(id)
    
    if group is not None:
        db.sess.delete(group)
        try:
            dbsession.commit()
        except:
            dbsession.rollback()
            raise
        return True
    return False

def group_delete_by_name(name):
    group = group_get_by_name(name)
    if group:
        return group_delete(group.id)
    return False

def group_user_ids(group):
    users = db.sess.query(User).filter(User.groups.any(id=group.id)).all()
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
    dbsession = db.sess
    if id is None:
        p = Permission()
        db.sess.add(p)
    else:
        p = permission_get(id)

    for k, v in kwargs.iteritems():
        try:
            setattr(p, k, v)
        except AttributeError:
            pass

    try:
        dbsession.commit()
        return p
    except Exception, e:
        dbsession.rollback()
        raise
        
def permission_add(safe=False, **kwargs):
    try:
        return permission_update(None, **kwargs)
    except Exception, e:
        if safe == False or safe not in str(e):
            raise
        return permission_get_by_name(kwargs['name'])

def permission_list():
    return db.sess.query(Permission).order_by(Permission.name).all()

def permission_list_options():
    return [(p.id, p.name) for p in db.sess.query(Permission).order_by(Permission.name)]

def permission_get(id):
    return db.sess.query(Permission).get(id)
    
def permission_get_by_name(name):
    return db.sess.query(Permission).filter_by(name=name).first()

def permission_delete(id):
    permission = permission_get(id)
    if permission is not None:
        db.sess.delete(permission)
        try:
            db.sess.commit()
        except:
            db.sess.rollback()
            raise
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