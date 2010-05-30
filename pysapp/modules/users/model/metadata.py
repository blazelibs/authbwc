from pysmvt import db
from sqlalchemy import Table, Column, ForeignKey, CheckConstraint, Index, Integer

__all__ = ['group_permission_assignments', 'user_permission_assignments']

group_permission_assignments = Table('users_permission_assignments_groups', db.meta, 
    Column('id', Integer, primary_key = True),
    Column('group_id', Integer, ForeignKey("users_group.id", ondelete='cascade'), nullable = False),
    Column('permission_id', Integer, ForeignKey("users_permission.id", ondelete='cascade'), nullable = False),
    Column('approved', Integer, CheckConstraint('approved in (-1, 1)'), nullable = False),
    useexisting=True
)
Index('ix_users_permission_assignments_groups_1',
    group_permission_assignments.c.group_id,
    group_permission_assignments.c.permission_id,
    unique=True)

user_permission_assignments = Table('users_permission_assignments_users', db.meta, 
    Column('id', Integer, primary_key = True),
    Column('user_id', Integer, ForeignKey("users_user.id", ondelete='cascade'), nullable = False),
    Column('permission_id', Integer, ForeignKey("users_permission.id", ondelete='cascade'), nullable = False),
    Column('approved', Integer, CheckConstraint('approved in (-1, 1)'), nullable = False),
    useexisting=True
)
Index('ix_users_permission_assignments_users_1',
    user_permission_assignments.c.user_id,
    user_permission_assignments.c.permission_id,
    unique=True)
