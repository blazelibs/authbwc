from pysmvt import db

def action_050_user_data():    
    from ..model.orm import User, Group, Permission
    db.sess.execute(User.table.delete())
    db.sess.execute(Group.table.delete())
    db.sess.execute(Permission.table.delete())