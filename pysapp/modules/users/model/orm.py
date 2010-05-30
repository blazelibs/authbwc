from pysmvt import db
from elixir import Entity, Field, Integer, String, Unicode, \
                   setup_all, create_all, using_options, \
                   ManyToMany, Boolean, SmallInteger, DateTime
from hashlib import sha512
from datetime import datetime
from pysapp.lib.db import SmallIntBool

__all__ = ['User', 'Group', 'Permission']

class User(Entity):

    login_id = Field(Unicode(150), required=True, index=True, unique=True)
    email_address = Field(Unicode(150), required=True, unique=True)
    pass_hash = Field(String(128), required=True)
    reset_required = Field(SmallIntBool, default=True, required=True)
    super_user = Field(SmallIntBool, default=False, required=True)
    name_first = Field(Unicode(255))
    name_last = Field(Unicode(255))
    inactive_flag = Field(SmallIntBool, required=True, default=False)
    inactive_date = Field(DateTime)
    pass_reset_ts = Field(DateTime)
    pass_reset_key = Field(String(12))
    
    groups = ManyToMany('Group', tablename='users_user_group_map', ondelete='cascade')
    
    using_options(tablename="users_user", inheritance='multi', metadata=db.meta, session=db.Session)
    
    def __repr__(self):
        return '<User "%s" : %s>' % (self.login_id, self.email_address)

    def set_password(self, password):
        if password:
            self.pass_hash = sha512(password).hexdigest()

    password = property(None,set_password)

    def _get_inactive(self):
        if self.inactive_flag:
            return True
        if self.inactive_date and self.inactive_date < datetime.now():
            return True
        return False
    inactive = property(_get_inactive)

    def _get_name(self):
        retval = '%s %s' % (self.name_first if self.name_first else '', self.name_last if self.name_last else '')
        return retval.strip()
    name = property(_get_name)

    def _get_name_or_login(self):
        if self.name:
            return self.name
        return self.login_id
    name_or_login = property(_get_name_or_login)

class Group(Entity):

    name = Field(Unicode(150), required=True, index=True, unique=True)
    
    users = ManyToMany('User', tablename='users_user_group_map', ondelete='cascade')
    
    using_options(tablename="users_group", metadata=db.meta, session=db.Session)
    
    def __repr__(self):
        return '<Group "%s" : %d>' % (self.name, self.id)

class Permission(Entity):

    name = Field(Unicode(250), required=True, index=True, unique=True)
    description = Field(Unicode(250))
    using_options(tablename="users_permission", metadata=db.meta, session=db.Session)
    
    def __repr__(self):
        return '<Permission: "%s">' % self.name

