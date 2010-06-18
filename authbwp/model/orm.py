from sqlalchemy import Column, Integer, Unicode, DateTime, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.sql import text
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base
from plugstack.sqlalchemy import db
from hashlib import sha512
from datetime import datetime
from pysapp.lib.db import SmallIntBool, DeclarativeMixin

Base = declarative_base(metadata=db.meta)

# user <-> group table
user_groups = Table('auth_user_group_map', db.meta,
    Column('auth_user_id', Integer, ForeignKey('auth_user.id')),
    Column('auth_group_id', Integer, ForeignKey('auth_group.id'))
)

class User(Base, DeclarativeMixin):
    __tablename__ = 'auth_user'
    __table_args__ = (UniqueConstraint('login_id', name='uc_auth_users_login_id'),
                      UniqueConstraint('email_address', name='uc_auth_users_email_address'), {})

    id = Column(Integer, primary_key=True)
    login_id = Column(Unicode(150), nullable=False)
    email_address = Column(Unicode(150), nullable=False)
    pass_hash = Column(String(128), nullable=False)
    reset_required = Column(SmallIntBool, server_default=text('1'), nullable=False)
    super_user = Column(SmallIntBool, server_default=text('0'), nullable=False)
    name_first = Column(Unicode(255))
    name_last = Column(Unicode(255))
    inactive_flag = Column(SmallIntBool, nullable=False, server_default=text('0'))
    inactive_date = Column(DateTime)
    pass_reset_ts = Column(DateTime)
    pass_reset_key = Column(String(12))

    createdts = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    lastupdatets = Column(DateTime, onupdate=datetime.now)

    groups = relation('Group', secondary=user_groups, backref='users', cascade='delete')

    def __repr__(self):
        return '<User "%s" : %s>' % (self.login_id, self.email_address)

    def set_password(self, password):
        if password:
            self.pass_hash = sha512(password).hexdigest()
    password = property(None,set_password)

    @property
    def inactive(self):
        if self.inactive_flag:
            return True
        if self.inactive_date and self.inactive_date < datetime.now():
            return True
        return False

    @property
    def name(self):
        retval = '%s %s' % (self.name_first if self.name_first else '', self.name_last if self.name_last else '')
        return retval.strip()

    @property
    def name_or_login(self):
        if self.name:
            return self.name
        return self.login_id

class Group(Base, DeclarativeMixin):
    __tablename__ = 'auth_group'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(150), nullable=False, index=True, unique=True)

    createdts = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    lastupdatets = Column(DateTime, onupdate=datetime.now)

    # 'users' relation defined as backref on the groups relation in User

    def __repr__(self):
        return '<Group "%s" : %d>' % (self.name, self.id)

class Permission(Base, DeclarativeMixin):
    __tablename__ = 'auth_permission'

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(250), nullable=False, index=True, unique=True)
    description = Column(Unicode(250))

    createdts = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    lastupdatets = Column(DateTime, onupdate=datetime.now)

    def __repr__(self):
        return '<Permission: "%s">' % self.name
