from blazeweb.globals import settings
from sqlalchemy import Table, Column, ForeignKey, CheckConstraint, Index, Integer

from compstack.auth.model.orm import User, Group
from compstack.sqlalchemy import db

__all__ = ['group_permission_assignments', 'user_permission_assignments']

group_permission_assignments = Table(
    'auth_permission_assignments_groups', db.meta,
    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey("auth_groups.id", ondelete='cascade'), nullable=False),
    Column('permission_id', Integer, ForeignKey("auth_permissions.id", ondelete='cascade'),
           nullable=False),
    Column('approved', Integer, CheckConstraint('approved in (-1, 1)'), nullable=False),
    extend_existing=True
)
Index(
    'ix_auth_permission_assignments_groups_1',
    group_permission_assignments.c.group_id,
    group_permission_assignments.c.permission_id,
    unique=True
)


user_permission_assignments = Table(
    'auth_permission_assignments_users', db.meta,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey("auth_users.id", ondelete='cascade'), nullable=False),
    Column('permission_id', Integer, ForeignKey("auth_permissions.id", ondelete='cascade'),
           nullable=False),
    Column('approved', Integer, CheckConstraint('approved in (-1, 1)'), nullable=False),
    extend_existing=True
)

Index(
    'ix_auth_permission_assignments_users_1',
    user_permission_assignments.c.user_id,
    user_permission_assignments.c.permission_id,
    unique=True
)

# user <-> group table
user_groups = Table(
    'auth_user_group_map', db.meta,
    Column('auth_user_id', Integer, ForeignKey(User.id, name='fk_auth_ugmap_user_id',
                                               ondelete='cascade')),
    Column('auth_group_id', Integer, ForeignKey(Group.id, name='fk_auth_ugmap_group_id',
                                                ondelete='cascade'))
)
