from pysmvt import db
from elixir import Entity, Field, Integer, String, Unicode, \
                   setup_all, create_all, using_options, \
                   ManyToMany, Boolean
from hashlib import sha512

__all__ = ['User', 'Group', 'Permission']

class User(Entity):

    login_id = Field(Unicode(150), required=True, index=True, unique=True)
    email_address = Field(Unicode(150), required=True, unique=True)
    pass_hash = Field(String(128), required=True)
    reset_required = Field(Boolean, default=True, required=True)
    super_user = Field(Boolean, default=True, required=True)
    
    groups = ManyToMany('Group', tablename='users_user_group_map', ondelete='cascade')
    
    using_options(tablename="users_user", inheritance='multi', metadata=db.meta, session=db.Session)
    
    def __repr__(self):
        return '<User "%s" : %s>' % (self.login_id, self.email_address)

    def set_password(self, password):
        if password:
            self.pass_hash = sha512(password).hexdigest()

    password = property(None,set_password)

class Group(Entity):

    name = Field(Unicode(150), required=True, index=True, unique=True)
    
    users = ManyToMany('User', tablename='users_user_group_map', ondelete='cascade')
    
    using_options(tablename="users_group", metadata=db.meta, session=db.Session)
    
    def __repr__(self):
        return '<Group "%s" : %d>' % (self.name, self.id)

class Permission(Entity):

    name = Field(Unicode(250), required=True, index=True, unique=True)
    
    using_options(tablename="users_permission", metadata=db.meta, session=db.Session)
    
    def __repr__(self):
        return '<Permission "%s" : %d>' % self.name

