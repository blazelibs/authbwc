from blazeweb.routing import url_for
import sqlalchemy as sa
from webgrid import Column, YesNoColumn, LinkColumnBase
from webgrid.blazeweb import Grid
from webgrid.filters import FilterBase, Operator, TextFilter
from webhelpers2.html import literal
from webhelpers2.html.tags import link_to

from compstack.auth.model.orm import Permission, Group, User


class ActionColumn(Column):
    def render_html(self, rec, hah):
        data = self.extract_data(rec)
        hah.class_ = 'two_action_col'
        return data

    def extract_data(self, rec):
        edit_link = link_to(
            '(edit)',
            url_for(
                self.endpoint,
                action='edit',
                objid=rec.id,
                session_key=self.grid.session_key,
            ),
            class_='edit_link',
            title='edit record'
        )
        delete_link = link_to(
            '(delete)',
            url_for(
                self.endpoint,
                action='delete',
                objid=rec.id,
                session_key=self.grid.session_key,
            ),
            class_='delete_link',
            title='delete record'
        )
        links = [delete_link, edit_link]
        return literal(''.join(links))


class UserActionColumn(ActionColumn):
    endpoint = 'auth:UserCrud'


class GroupActionColumn(ActionColumn):
    endpoint = 'auth:GroupCrud'


class PermissionActionColumn(ActionColumn):
    endpoint = 'auth:PermissionCrud'

    def render_html(self, rec, hah):
        data = self.extract_data(rec)
        hah.class_ = 'two_action_col'
        return data

    def extract_data(self, rec):
        edit_link = link_to(
            '(edit)',
            url_for(
                self.endpoint,
                action='edit',
                objid=rec.id,
                session_key=self.grid.session_key,
            ),
            class_='edit_link',
            title='edit record'
        )
        return literal(edit_link)


class PermissionMapColumn(LinkColumnBase):
    def extract_data(self, rec):
        return 'view permission map'

    def create_url(self, record):
        return url_for(
            'auth:PermissionMap',
            objid=record.id,
        )


class YesNoFilter(FilterBase):
    operators = (
        Operator('a', 'all', None),
        Operator('y', 'yes', None),
        Operator('n', 'no', None),
    )

    def apply(self, query):
        if self.op == 'a':
            return query
        if self.op == 'y':
            return query.filter(self.sa_col == sa.true())
        if self.op == 'n':
            return query.filter(self.sa_col == sa.false())
        return FilterBase.apply(self, query)


class UserGrid(Grid):
    session_on = True

    UserActionColumn('', User.id, can_sort=False, render_in='html')
    Column('Login ID', User.login_id, TextFilter)
    Column('Name', User.name, TextFilter)
    YesNoColumn('Super User', User.super_user, YesNoFilter)
    YesNoColumn('Reset Required', User.reset_required, YesNoFilter)
    YesNoColumn('Inactive', User.inactive, YesNoFilter)
    PermissionMapColumn('Permission Map', None, can_sort=False)

    def query_prep(self, query, has_sort, has_filters):
        query = query.add_entity(
            User
        )

        # default sort
        if not has_sort:
            query = query.order_by(
                User.name,
            )

        return query


class GroupGrid(Grid):
    session_on = True

    GroupActionColumn('', Group.id, can_sort=False, render_in='html')
    Column('Group', Group.name, TextFilter)

    def query_prep(self, query, has_sort, has_filters):
        # default sort
        if not has_sort:
            query = query.order_by(
                Group.name,
            )

        return query


class PermissionGrid(Grid):
    session_on = True

    PermissionActionColumn('', Permission.id, can_sort=False, render_in='html')
    Column('Permission', Permission.name, TextFilter)
    Column('Description', Permission.description, TextFilter)

    def query_prep(self, query, has_sort, has_filters):
        # default sort
        if not has_sort:
            query = query.order_by(
                Permission.name,
            )

        return query
