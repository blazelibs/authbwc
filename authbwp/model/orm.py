from datetime import datetime
from hashlib import sha512

from blazeutils.strings import randchars
from blazeweb.globals import settings
from sqlalchemy import Column, Integer, Unicode, DateTime, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import relation
from sqlalchemy.sql import text
from sqlalchemy.util import classproperty

from plugstack.sqlalchemy import db
from plugstack.sqlalchemy.lib.columns import SmallIntBool
from plugstack.sqlalchemy.lib.declarative import declarative_base, DefaultMixin
from plugstack.sqlalchemy.lib.declarative import one_to_none

Base = declarative_base()

class UserMixin(DefaultMixin):
    __table_args__ = (UniqueConstraint('login_id', name='uc_auth_users_login_id'),
                      UniqueConstraint('email_address', name='uc_auth_users_email_address'), {})

    login_id = Column(Unicode(150), nullable=False)
    email_address = Column(Unicode(150), nullable=False)
    pass_hash = Column(String(128), nullable=False)
    pass_salt = Column(String(32), nullable=False)
    reset_required = Column(SmallIntBool, server_default=text('1'), nullable=False)
    super_user = Column(SmallIntBool, server_default=text('0'), nullable=False)
    name_first = Column(Unicode(255))
    name_last = Column(Unicode(255))
    inactive_flag = Column(SmallIntBool, nullable=False, server_default=text('0'))
    inactive_date = Column(DateTime)
    pass_reset_ts = Column(DateTime)
    pass_reset_key = Column(String(12))

    @classproperty
    def groups(cls):
        return relation('Group', secondary='auth_user_group_map', backref='users', cascade='delete')

    def __repr__(self):
        return '<User "%s" : %s>' % (self.login_id, self.email_address)

    def set_password(self, password, record_salt=None):
        if password:
            _, record_salt = self.calc_salt(record_salt)
            self.pass_salt = record_salt
            self.pass_hash = self.calc_pass_hash(password, record_salt)
            self.text_password = password
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

    @classmethod
    def calc_salt(cls, record_salt=None):
        record_salt = record_salt or randchars(32, 'all')
        if settings.plugins.auth.password_salt:
            full_salt = settings.plugins.auth.password_salt + record_salt
            return full_salt, record_salt
        return record_salt, record_salt

    @classmethod
    def calc_pass_hash(cls, password, record_salt=None):
        full_salt, record_salt = cls.calc_salt(record_salt)
        return sha512(password+full_salt).hexdigest()

    @classmethod
    def validate(cls, login_id, password):
        """
            Returns the user that matches login_id and password or None
        """
        u = cls.get_by(login_id = login_id)
        if not u:
            return
        if u.validate_password(password):
            return u

    def validate_password(self, password):
        return self.pass_hash == self.calc_pass_hash(password, self.pass_salt)

if settings.plugins.auth.model_create_user:
    class User(Base, UserMixin):
        __tablename__ = 'auth_users'

class Group(Base, DefaultMixin):
    __tablename__ = 'auth_groups'

    name = Column(Unicode(150), nullable=False, index=True, unique=True)

    # 'users' relation defined as backref on the groups relation in User

    def __repr__(self):
        return '<Group "%s" : %d>' % (self.name, self.id)

class Permission(Base, DefaultMixin):
    __tablename__ = 'auth_permissions'

    name = Column(Unicode(250), nullable=False, index=True, unique=True)
    description = Column(Unicode(250))

    def __repr__(self):
        return '<Permission: "%s">' % self.name
