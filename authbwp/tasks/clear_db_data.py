from pysmvt import db

def action_050_user_data():    
    from plugstack.users.model.orm import User, Group, Permission
    db.sess.execute(User.table.delete())
    db.sess.execute(Group.table.delete())
    db.sess.execute(Permission.table.delete())