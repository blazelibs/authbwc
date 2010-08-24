from blazeutils.helpers import tolist
from blazeweb.globals import settings
from savalidation import validators as val
from sqlalchemy import Column, Unicode
from sqlalchemy.sql import select, and_

from plugstack.auth.model.declarative import UserMixin
from plugstack.sqlalchemy import db
from plugstack.sqlalchemy.lib.declarative import declarative_base, DefaultMixin
from plugstack.sqlalchemy.lib.decorators import transaction
from plugstack.sqlalchemy.lib.validators import validates_unique

Base = declarative_base()

if settings.plugins.auth.model_create_user:
    class User(Base, UserMixin):
        __tablename__ = 'auth_users'

        val.validates_constraints()
        validates_unique('login_id','email_address')

class Group(Base, DefaultMixin):
    __tablename__ = 'auth_groups'

    name = Column(Unicode(150), nullable=False, index=True, unique=True)

    # 'users' relation defined as backref on the groups relation in User

    val.validates_constraints()
    validates_unique('name')

    def __repr__(self):
        return '<Group "%s">' % (self.name)

    @transaction
    def add(cls, **kwargs):
        return cls.update(**kwargs)

    @transaction
    def edit(cls, oid=None, **kwargs):
        if oid is None:
            raise ValueError('the id must be given to edit the record')
        return cls.update(oid, **kwargs)

    @classmethod
    def update(cls, oid=None, **kwargs):
        if oid is None:
            g = cls()
            db.sess.add(g)
        else:
            g = cls.get(oid)

        for k, v in kwargs.iteritems():
            try:
                # some values can not be set directly
                if k in ('assigned_users', 'approved_permissions', 'denied_permissions'):
                    pass
                else:
                    setattr(g, k, v)
            except AttributeError:
                pass

        g.users = [User.get(uid) for uid in tolist(kwargs.get('assigned_users',[]))]
        db.sess.flush()
        g.assign_permissions(kwargs.get('approved_permissions',[]), kwargs.get('denied_permissions',[]))
        return g

    def assign_permissions(self, approved_perm_ids, denied_perm_ids):
        from plugstack.auth.model.metadata import group_permission_assignments as tbl_gpa
        insval = []

        # delete existing permission assignments for this group (i.e. we start over)
        db.sess.execute(tbl_gpa.delete(tbl_gpa.c.group_id == self.id))

        # insert "approved" records
        if approved_perm_ids is not None and len(approved_perm_ids) != 0:
            insval.extend([{'group_id' : self.id, 'permission_id' : pid, 'approved' : 1} for pid in approved_perm_ids])

        # insert "denied" records
        if denied_perm_ids is not None and len(denied_perm_ids) != 0:
            insval.extend([{'group_id' : self.id, 'permission_id' : pid, 'approved' : -1} for pid in denied_perm_ids])

        # do inserts
        if insval:
            db.sess.execute(tbl_gpa.insert(), insval)

        return

    @transaction
    def assign_permissions_by_name(cls, group_name, approved_perm_list=[], denied_perm_list=[]):
        # Note: this function is a wrapper for assign_permissions and will commit db trans
        group = cls.get_by(name=unicode(group_name))
        approved_perm_ids = [item.id for item in [Permission.get_by(name=unicode(perm)) for perm in tolist(approved_perm_list)]]
        denied_perm_ids = [item.id for item in [Permission.get_by(name=unicode(perm)) for perm in tolist(denied_perm_list)]]
        group.assign_permissions(approved_perm_ids, denied_perm_ids)

    @property
    def user_ids(self):
        return [u.id for u in db.sess.query(User).filter(User.groups.any(id=self.id)).all()]

    @property
    def assigned_permission_ids(self):
        from plugstack.auth.model.metadata import group_permission_assignments as tbl_gpa
        s = select(
            [tbl_gpa.c.permission_id],
            and_(tbl_gpa.c.group_id==self.id, tbl_gpa.c.approved == 1)
            )
        approved = [r[0] for r in db.sess.execute(s)]
        s = select(
            [tbl_gpa.c.permission_id],
            and_(tbl_gpa.c.group_id==self.id, tbl_gpa.c.approved == -1)
            )
        denied = [r[0] for r in db.sess.execute(s)]

        return approved, denied

    @transaction
    def group_add_permissions_to_existing(cls, group_name, approved=[], denied=[]):
        g = cls.get_by(name=group_name)
        capproved, cdenied = g.assigned_permission_ids
        for permid in tolist(approved):
            if permid not in capproved:
                capproved.append(permid)
        for permid in tolist(denied):
            if permid not in cdenied:
                cdenied.append(permid)

        g.assign_permissions(capproved, cdenied)

class Permission(Base, DefaultMixin):
    __tablename__ = 'auth_permissions'

    name = Column(Unicode(250), nullable=False, index=True, unique=True)
    description = Column(Unicode(250))

    val.validates_constraints()
    validates_unique('name')

    def __repr__(self):
        return '<Permission: "%s">' % self.name

