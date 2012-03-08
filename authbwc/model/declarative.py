from datetime import datetime
from hashlib import sha512

from blazeutils.helpers import tolist
from blazeutils.strings import randchars
from blazeweb.globals import settings
from sqlalchemy import Column, Unicode, DateTime, String
from sqlalchemy.orm import join, relation
from sqlalchemy.sql import select, and_, alias, or_, func, text
from sqlalchemy.sql.functions import sum
from sqlalchemy.util import classproperty

from compstack.sqlalchemy import db
from compstack.sqlalchemy.lib.columns import SmallIntBool
from compstack.sqlalchemy.lib.declarative import DefaultMixin
from compstack.sqlalchemy.lib.decorators import transaction, transaction_ncm

class AuthRelationsMixin(object):
    """
        This mixin provides methods and properties for a user-like entity
        to be related to groups and permissions.
    """
    @classproperty
    def groups(cls):
        return relation('Group', secondary='auth_user_group_map')

    def assign_permissions(self, approved_perm_ids, denied_perm_ids):
        from compstack.auth.model.metadata import user_permission_assignments as tbl_upa
        insval = []

        # delete existing permission assignments for this user (i.e. we start over)
        db.sess.execute(tbl_upa.delete(tbl_upa.c.user_id == self.id))

        # insert "approved" records
        if approved_perm_ids is not None and len(approved_perm_ids) != 0:
            insval.extend([{'user_id' : self.id, 'permission_id' : pid, 'approved' : 1} for pid in approved_perm_ids])

        # insert "denied" records
        if denied_perm_ids is not None and len(denied_perm_ids) != 0:
            insval.extend([{'user_id' : self.id, 'permission_id' : pid, 'approved' : -1} for pid in denied_perm_ids])

        # do inserts
        if insval:
            db.sess.execute(tbl_upa.insert(), insval)

    @property
    def group_ids(self):
        from compstack.auth.model.orm import Group
        return [g.id for g in db.sess.query(Group).filter(Group.users.any(id=self.id)).all()]

    @property
    def assigned_permission_ids(self):
        from compstack.auth.model.metadata import user_permission_assignments as tbl_upa
        s = select(
            [tbl_upa.c.permission_id],
            and_(tbl_upa.c.user_id==self.id, tbl_upa.c.approved == 1)
            )
        approved = [r[0] for r in db.sess.execute(s)]
        s = select(
            [tbl_upa.c.permission_id],
            and_(tbl_upa.c.user_id==self.id, tbl_upa.c.approved == -1)
            )
        denied = [r[0] for r in db.sess.execute(s)]

        return approved, denied

    @classmethod
    def get_by_permissions(cls, permissions):
        from compstack.auth.model.queries import query_users_permissions
        vuserperms = query_users_permissions().alias()
        return db.sess.query(cls).select_from(
            join(cls, vuserperms, cls.id == vuserperms.c.user_id)
        ).filter(
            or_(
                vuserperms.c.user_approved == 1,
                and_(
                    vuserperms.c.user_approved == None,
                    or_(
                        vuserperms.c.group_denied == None,
                        vuserperms.c.group_denied >= 0,
                    ),
                    vuserperms.c.group_approved >= 1
                )
            )
        ).filter(
            vuserperms.c.permission_name.in_(tolist(permissions))
        ).all()

    @classmethod
    def cm_permission_map(cls, uid):
        from compstack.auth.model.queries import query_users_permissions
        user_perm = query_users_permissions().alias()
        s = select([user_perm.c.user_id.label('user_id'),
                    user_perm.c.permission_id.label('permission_id'),
                    user_perm.c.permission_name.label('permission_name'),
                    user_perm.c.login_id.label('login_id'),
                    user_perm.c.user_approved.label('user_approved'),
                    user_perm.c.group_approved.label('group_approved'),
                    user_perm.c.group_denied.label('group_denied'),
                ],
                from_obj=user_perm).where(user_perm.c.user_id==uid)
        results = db.sess.execute(s)
        retval = []
        for row in results:
            nrow = {}
            for key, value in row.items():
                if value is None:
                    nrow[key] = 0
                else:
                    nrow[key] = value

            if nrow['user_approved'] == -1:
                approved = False
            elif nrow['user_approved'] == 1:
                approved = True
            elif nrow['group_denied'] <= -1:
                approved = False
            elif nrow['group_approved'] >= 1:
                approved = True
            else:
                approved = False

            nrow[u'resulting_approval'] = approved
            retval.append(nrow)
        return retval

    @property
    def permission_map(self):
        return self.__class__.cm_permission_map(self.id)

    @property
    def permission_map_groups(self):
        from compstack.auth.model.queries import query_user_group_permissions
        user_group_perm = query_user_group_permissions().alias()
        s = select([user_group_perm.c.permission_id,
                    user_group_perm.c.group_name,
                    user_group_perm.c.group_id,
                    user_group_perm.c.group_approved],
                from_obj=user_group_perm).where(user_group_perm.c.user_id==self.id)
        results = db.sess.execute(s)
        retval = {}
        for row in results:
            if not retval.has_key(row['permission_id']):
                retval[row['permission_id']] = {'approved' : [], 'denied' : []}
            if row['group_approved'] <= -1:
                retval[row['permission_id']]['denied'].append({'name':row['group_name'], 'id':row['group_id']})
            elif row['group_approved'] >= 1:
                retval[row['permission_id']]['approved'].append({'name':row['group_name'], 'id':row['group_id']})
        return retval

class UserMixin(DefaultMixin, AuthRelationsMixin):
    """
        A mixin with common
    """
    login_id = Column(Unicode(150), nullable=False, unique=True)
    email_address = Column(Unicode(150), nullable=False, unique=True)
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
        if settings.components.auth.password_salt:
            full_salt = settings.components.auth.password_salt + record_salt
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
        from compstack.auth.model.orm import Group
        if oid is None:
            u = cls()
            db.sess.add(u)
            # when creating a new user, if the password is not set, assign it as
            # a random string assuming the email will get sent out to the user
            # and they will change it when they login
            if not kwargs.get('password', None):
                kwargs['password'] = randchars(8)
        else:
            u = cls.get(oid)
        # automatically turn on reset_password when the password get set manually
        # (i.e. when an admin does it), unless told not to (when a user does it
        # for their own account)
        if kwargs.get('password') and kwargs.get('pass_reset_ok', True):
            kwargs['reset_required'] = True

        for k, v in kwargs.iteritems():
            try:
                # some values can not be set directly
                if k not in ('pass_hash', 'pass_salt', 'assigned_groups', 'approved_permissions', 'denied_permissions'):
                    setattr(u, k, v)
            except AttributeError:
                pass

        u.groups = [Group.get(gid) for gid in tolist(kwargs.get('assigned_groups', []))]
        db.sess.flush()
        u.assign_permissions(kwargs.get('approved_permissions', []), kwargs.get('denied_permissions', []))
        return u

    @transaction_ncm
    def update_password(self, password):
        self.password = password
        self.reset_required = False

    @transaction
    def reset_password(cls, email_address):
        u = cls.get_by_email(email_address)
        if not u:
            return False

        u.pass_reset_key = randchars(12)
        u.pass_reset_ts = datetime.utcnow()
        return u

    @transaction_ncm
    def kill_reset_key(self):
        self.pass_reset_key = None
        self.pass_reset_ts = None

    @classmethod
    def get_by_email(cls, email_address):
        # case-insensitive query
        return db.sess.query(cls) \
            .filter(func.lower(cls.email_address)==func.lower(email_address)) \
            .first()

    @classmethod
    def cm_permission_dict(cls, uid, su_override=True):
        """
            returns a dictionary that has the permission name as the key and
            the resulting approval, for the user with the given user_id `uid`
            as the value.

            Example return:
                { 'approved-perm-name': True, 'denied-perm-name': False }

            kwargs:
                `su_override`: if user is a super user, show all perms as approved;
                    default: True
        """
        retval = {}
        user_is_super = False
        if su_override:
            user_is_super = bool(db.sess.query(cls.super_user).filter_by(id=uid).scalar())
        for pmap in cls.cm_permission_map(uid):
            retval[pmap['permission_name']] = user_is_super or pmap['resulting_approval']
        return retval
        u = cls.get(uid)
        return u.permission_dict()

    def permission_dict(self, su_override=True):
        """
            same as cm_perm_dict() for the current instance
        """
        return self.__class__.cm_permission_dict(self.id, su_override=su_override)

    @classmethod
    def cm_has_permission(cls, uid, *perms, **kwargs):
        """
            Return True if the user has all permiss names given, False otherwise

            kwargs:
                su_override: if user is a super user, show all perms as approved;
                    default: True
        """
        su_override = kwargs.pop('su_override', True)
        pdict = cls.cm_permission_dict(uid, su_override=su_override)
        if not pdict:
            return False
        for pname in perms:
            if pname not in pdict:
                return False
            if not pdict[pname]:
                return False
        return True

    def has_permission(self, *perms, **kwargs):
        return self.__class__.cm_has_permission(self.id, *perms, **kwargs)

    @classmethod
    def testing_create(cls, loginid = None, approved_perms=[], denied_perms=[],
                reset_required=False, groups=[]):
        # use the hierarchy to find the Permission in case the app has changed
        # it
        from compstack.auth.model.orm import Permission

        login_id = loginid or randchars()
        email_address = '%s@example.com' % login_id
        password = randchars(15)

        appr_perm_ids = []
        denied_perm_ids = []
        # create the permissions
        for perm in tolist(approved_perms):
            p = Permission.get_by(name=perm)
            if p is None:
                raise ValueError('permission %s does not exist' % perm)
            appr_perm_ids.append(p.id)
        for perm in tolist(denied_perms):
            p = Permission.get_by(name=perm)
            if p is None:
                raise ValueError('permission %s does not exist' % perm)
            denied_perm_ids.append(p.id)

        u = cls.add(
            login_id=login_id,
            email_address=email_address,
            password = password,
            reset_required = reset_required,
            # don't let the update method set reset_required
            pass_reset_ok = False,
            approved_permissions = appr_perm_ids,
            denied_permissions = denied_perm_ids,
            # not quite sure why these are needed, they should default, but I
            # ran into an issue when testing that would throw SAValidation
            # errors up when I leave them out.
            inactive_flag = False,
            super_user = False,
        )
        u.groups.extend(tolist(groups))
        db.sess.commit()
        u.text_password = password
        return u

class GroupMixin(DefaultMixin):
    name = Column(Unicode(150), nullable=False, index=True, unique=True)

    @classproperty
    def users(cls):
        return relation('User', secondary='auth_user_group_map')

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
        from compstack.auth.model.orm import User
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
        from compstack.auth.model.metadata import group_permission_assignments as tbl_gpa
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
        from compstack.auth.model.orm import Permission
        group = cls.get_by(name=unicode(group_name))
        approved_perm_ids = [item.id for item in [Permission.get_by(name=unicode(perm)) for perm in tolist(approved_perm_list)]]
        denied_perm_ids = [item.id for item in [Permission.get_by(name=unicode(perm)) for perm in tolist(denied_perm_list)]]
        group.assign_permissions(approved_perm_ids, denied_perm_ids)

    @property
    def user_ids(self):
        from compstack.auth.model.orm import User
        return [u.id for u in db.sess.query(User).filter(User.groups.any(id=self.id)).all()]

    @property
    def assigned_permission_ids(self):
        from compstack.auth.model.metadata import group_permission_assignments as tbl_gpa
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

    @classmethod
    def testing_create(cls):
        return cls.add(name=randchars())
