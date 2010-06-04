import datetime
from pysmvt import modimportauto, db, modimport
from pysutils import randchars

modimportauto('users.testing', ['create_user_with_permissions'])
modimportauto('users.actions', ['user_get', 'user_get_by_permissions',
    'group_add', 'permission_add', 'user_get_by_permissions_query',
    'user_add', 'user_get_by_login', 'user_get_by_email', 'user_validate',
    'group_get_by_name', 'permission_get_by_name', 'user_update',
    'group_delete'])
group_perm_init = modimport('users.actions', 'permission_assignments_group_by_name')

def test_group_unique():
    g1 = group_add(safe='unique', name=u'test unique group name')
    g2 = group_add(safe='unique', name=u'test unique group name')
    assert g1.id == g2.id and g1.id is not None

def test_group_get_by_name():
    g = group_add(safe='unique', name=u'group_for_testing_%s'%randchars(15))
    assert group_get_by_name(g.name).id == g.id
    
def test_permission_unique():
    p1 = permission_add(safe='unique', name=u'test unique permission name')
    p2 = permission_add(safe='unique', name=u'test unique permission name')
    assert p1.id == p2.id and p1.id is not None

def test_permission_get_by_name():
    p = permission_add(safe='unique', name=u'permission_for_testing_%s'%randchars(15))
    assert permission_get_by_name(p.name).id == p.id

def test_user_unique():
    u1 = create_user_with_permissions()
    u2 = user_add(safe='unique', login_id=u1.login_id, email_address='test%s@example.com'%u1.login_id)
    assert u2 is None, '%s, %s'%(u1.id, u2.id)
    u2 = user_add(safe='unique', login_id='test%s'%u1.login_id, email_address=u1.email_address)
    assert u2 is None

def test_user_get_by_login():
    u = create_user_with_permissions()
    obj = user_get_by_login(u.login_id)
    assert u.id == obj.id

def test_user_get_by_email():
    u = create_user_with_permissions()
    obj = user_get_by_email(u.email_address)
    assert u.id == obj.id

def test_user_name_or_login():
    u = create_user_with_permissions()
    assert u.name_or_login == u.login_id
    u.name_first = u'testname'
    assert u.name != ''
    assert u.name_or_login == u.name

def test_user_validate():
    u = create_user_with_permissions()
    u.password = u'testpass123'
    db.sess.commit()
    assert user_validate(login_id=u.login_id, password=u'bad_password') is None
    assert user_validate(login_id=u'bad_login', password=u'testpass123') is None
    assert user_validate(login_id=u.login_id, password=u'testpass123').id == u.id

def test_user_group_assignment():
    g1 = group_add(safe='unique', name=u'group_for_testing_%s'%randchars(15))
    g2 = group_add(safe='unique', name=u'group_for_testing_%s'%randchars(15))

    u = create_user_with_permissions()
    assert u.groups == []

    user_update(u.id, assigned_groups=[g1.id,g2.id])
    assert len(u.groups) == 2
    assert len(g1.users) == len(g2.users) == 1
    
    user_update(u.id, assigned_groups=g2.id)
    assert len(u.groups) == 1
    assert u.groups[0].id == g2.id

def test_group_delete():
    g1 = group_add(safe='unique', name=u'group_for_testing_%s'%randchars(15))
    g2 = group_add(safe='unique', name=u'group_for_testing_%s'%randchars(15))

    u = create_user_with_permissions()
    user_update(u.id, assigned_groups=[g1.id,g2.id])

    ret = group_delete(g1.id)
    assert ret == True
    assert len(g2.users) == 1
    assert len(u.groups) == 1
    assert u.groups[0].id == g2.id
    
def test_inactive_property():
    user = create_user_with_permissions()
    
    user.inactive_flag = True
    
    assert user.inactive
    
    user.inactive_flag = False
    user.inactive_date = datetime.datetime(2010, 10, 10)
    
    assert not user.inactive
    
    user.inactive_date = datetime.datetime(2000, 10, 10)
    
    assert user.inactive

def test_user_get_by_permissions():
    permissions = [
        'ugp_approved_grp', 'ugp_not_approved', 'ugp_denied_grp']
    
    for permission in permissions:
        permission_add(name=unicode(permission))
        
    user = create_user_with_permissions(u'ugp_approved', u'ugp_denied')
    user2 = create_user_with_permissions(u'ugp_approved')
    g1 = group_add(name=u'ugp_g1')
    g2 = group_add(name=u'ugp_g2')
    group_perm_init(u'ugp_g1', (u'ugp_approved_grp', u'ugp_denied', u'ugp_denied_grp'))
    group_perm_init(u'ugp_g2', None, u'ugp_denied_grp')
    user.groups.append(g1)
    user.groups.append(g2)
    db.sess.commit()
    
    # user directly approved
    users_approved = user_get_by_permissions(u'ugp_approved')
    assert users_approved[0] is user
    assert users_approved[1] is user2
    assert len(users_approved) == 2
    
    # user approved by group association
    assert user_get_by_permissions(u'ugp_approved_grp')[0] is user
    
    # user denial and group approval
    assert user_get_by_permissions(u'ugp_denied') == []
    
    # no approval
    assert user_get_by_permissions(u'ugp_not_approved') == []
    
    # approved by one group denied by another, denial takes precedence
    assert user_get_by_permissions(u'ugp_denied_grp') == []
    