import datetime
from pysmvt import modimportauto, db, modimport

modimportauto('users.testing', ['create_user_with_permissions'])
modimportauto('users.actions', ['user_get', 'user_get_by_permissions',
    'group_add', 'permission_add', 'user_get_by_permissions_query'])
group_perm_init = modimport('users.actions', 'permission_assignments_group_by_name')

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