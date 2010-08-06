from plugstack.sqlalchemy import db

def action_050_user_data():    
    from plugstack.auth.model.orm import User, Group, Permission
    db.sess.execute(User.__table__.delete())
    db.sess.execute(Group.__table__.delete())
    db.sess.execute(Permission.__table__.delete())
