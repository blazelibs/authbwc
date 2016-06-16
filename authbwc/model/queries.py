from sqlalchemy.sql import select, and_, alias
from sqlalchemy.sql.functions import sum
from sqlalchemy.orm import outerjoin
from compstack.auth.model.orm import User, Group, Permission
from compstack.auth.model.metadata import group_permission_assignments as tbl_gpa
from compstack.auth.model.metadata import user_groups
from compstack.auth.model.metadata import user_permission_assignments as tbl_upa


def query_denied_group_permissions():
    return select(
        [
            Permission.id.label(u'permission_id'),
            user_groups.c.auth_user_id.label(u'user_id'),
            sum(tbl_gpa.c.approved).label(u'group_denied'),
        ],
        from_obj=outerjoin(
            Permission,
            tbl_gpa,
            and_(
                Permission.id == tbl_gpa.c.permission_id,
                tbl_gpa.c.approved == -1
            )
        ).outerjoin(
            user_groups, user_groups.c.auth_group_id == tbl_gpa.c.group_id
        )
    ).group_by(
        Permission.id,
        user_groups.c.auth_user_id
    )


def query_approved_group_permissions():
    return select(
        [
            Permission.id.label(u'permission_id'),
            user_groups.c.auth_user_id.label(u'user_id'),
            sum(tbl_gpa.c.approved).label(u'group_approved'),
        ],
        from_obj=outerjoin(
            Permission,
            tbl_gpa,
            and_(
                Permission.id == tbl_gpa.c.permission_id,
                tbl_gpa.c.approved == 1
            )
        ).outerjoin(
            user_groups, user_groups.c.auth_group_id == tbl_gpa.c.group_id
        )
    ).group_by(
        Permission.id,
        user_groups.c.auth_user_id
    )


def query_user_group_permissions():
    return select(
        [
            User.id.label(u'user_id'),
            Group.id.label(u'group_id'),
            Group.name.label(u'group_name'),
            tbl_gpa.c.permission_id,
            tbl_gpa.c.approved.label(u'group_approved'),
        ],
        from_obj=outerjoin(
            User,
            user_groups,
            User.id == user_groups.c.auth_user_id
        ).outerjoin(
            Group, Group.id == user_groups.c.auth_group_id
        ).outerjoin(
            tbl_gpa, tbl_gpa.c.group_id == Group.id
        )
    ).where(tbl_gpa.c.permission_id.isnot(None))


def query_users_permissions():
    ga = query_approved_group_permissions().alias('g_approve')
    gd = query_denied_group_permissions().alias('g_deny')
    user_perm = select([User.id.label(u'user_id'),
                        Permission.id.label(u'permission_id'),
                        Permission.name.label(u'permission_name'),
                        User.login_id]).correlate(None).alias(u'user_perm')
    return select(
        [
            user_perm.c.user_id,
            user_perm.c.permission_id,
            user_perm.c.permission_name,
            user_perm.c.login_id,
            tbl_upa.c.approved.label(u'user_approved'),
            ga.c.group_approved,
            gd.c.group_denied,
        ],
        from_obj=outerjoin(
            user_perm,
            tbl_upa,
            and_(
                tbl_upa.c.user_id == user_perm.c.user_id,
                tbl_upa.c.permission_id == user_perm.c.permission_id
            )
        ).outerjoin(
            ga,
            and_(
                ga.c.user_id == user_perm.c.user_id,
                ga.c.permission_id == user_perm.c.permission_id
            )
        ).outerjoin(
            gd,
            and_(
                gd.c.user_id == user_perm.c.user_id,
                gd.c.permission_id == user_perm.c.permission_id
            )
        )
    ).order_by(user_perm.c.user_id, user_perm.c.permission_id)
