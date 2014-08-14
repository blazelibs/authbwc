
from sqlalchemy.exc import OperationalError

from compstack.auth.model.orm import User, Group
from compstack.auth.model.metadata import user_groups as tbl_ugm
from compstack.sqlalchemy import db
from compstack.sqlalchemy.lib.sql import run_component_sql


def is_group_fk_present():
    g = Group.testing_create()
    u = User.testing_create(groups=g)
    gid = g.id

    # delete the group with delete_where() because .delete() loads the ORM
    # object and then calls <session>.delete().  That method will trigger SA
    # to issue a DELETE statement on the map table. Therefore, using
    # .delete() would allow this test to pass even if our FK was not
    # configured correctly.
    Group.delete_where(Group.id == gid)

    # if there are no records left, then the FK is present
    try:
        return db.sess.query(tbl_ugm).filter(tbl_ugm.c.auth_group_id == gid).count() == 0
    finally:
        db.sess.execute(tbl_ugm.delete().where(tbl_ugm.c.auth_group_id == gid))
        User.delete(u.id)


def fix_sqlite():
    from compstack.sqlalchemy.tasks.init_db import action_10_create_db_objects
    db.engine.execute('alter table auth_user_group_map rename to auth_user_group_map_old')
    # its ok if the trigger isn't dropped
    try:
        db.engine.execute(
            'drop trigger auth_user_group_map__auth_group_id__fkd__auth_groups__id__auto'
        )
    except OperationalError:
        pass
    db.engine.execute('drop trigger auth_user_group_map__auth_group_id__fki__auth_groups__id__auto')
    db.engine.execute('drop trigger auth_user_group_map__auth_group_id__fku__auth_groups__id__auto')
    db.engine.execute('drop trigger auth_user_group_map__auth_user_id__fkdc__auth_users__id__auto')
    db.engine.execute('drop trigger auth_user_group_map__auth_user_id__fki__auth_users__id__auto')
    db.engine.execute('drop trigger auth_user_group_map__auth_user_id__fku__auth_users__id__auto')
    action_10_create_db_objects()
    db.engine.execute("""
        insert into auth_user_group_map (auth_user_id, auth_group_id)
        select auth_user_id, auth_group_id from auth_user_group_map_old
    """)
    db.engine.execute('drop table auth_user_group_map_old')


def action_020_run_sql_files():
    if is_group_fk_present():
        print 'fix not needed'
    else:
        if db.engine.dialect.name == 'sqlite':
            fix_sqlite()
        else:
            run_component_sql('auth', 'fix_group_fk')
        db.sess.commit()
        print 'fixed the FK'
