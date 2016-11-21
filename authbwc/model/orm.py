from blazeutils.strings import randchars
from blazeweb.globals import settings
from savalidation import validators as val
from sqlalchemy import Column, Unicode

from compstack.auth.model.declarative import UserMixin, GroupMixin
from compstack.sqlalchemy.lib.declarative import declarative_base, DefaultMixin
from compstack.sqlalchemy.lib.validators import validates_unique

Base = declarative_base()

if settings.components.auth.model_create_user:
    class User(Base, UserMixin):
        __tablename__ = 'auth_users'

        val.validates_constraints()
        validates_unique('login_id', 'email_address')

if settings.components.auth.model_create_group:
    class Group(Base, GroupMixin):
        __tablename__ = 'auth_groups'

        val.validates_constraints()
        validates_unique('name')


class Permission(Base, DefaultMixin):
    __tablename__ = 'auth_permissions'

    name = Column(Unicode(250), nullable=False, index=True, unique=True)
    description = Column(Unicode(250))

    val.validates_constraints()
    validates_unique('name')

    def __repr__(self):
        return '<Permission: "%s">' % self.name

    @classmethod
    def testing_create(cls):
        return cls.add(name=randchars())
