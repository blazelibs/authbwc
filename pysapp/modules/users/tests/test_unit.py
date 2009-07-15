import datetime
from pysmvt import modimportauto, db

modimportauto('users.testing', ['create_user_with_permissions'])
modimportauto('users.actions', ['user_get'])

def test_inactive_property():
    user = create_user_with_permissions()
    
    user.inactive_flag = True
    
    assert user.inactive
    
    user.inactive_flag = False
    user.inactive_date = datetime.datetime(2010, 10, 10)
    
    assert not user.inactive
    
    user.inactive_date = datetime.datetime(2000, 10, 10)
    
    assert user.inactive
    