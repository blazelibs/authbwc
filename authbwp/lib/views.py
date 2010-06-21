from blazeweb import user, settings
from blazeweb.exceptions import ProgrammingError
from blazeweb.hierarchy import findobj, HierarchyImportError
from blazeweb.htmltable import Table, Links, A
from blazeweb.routing import url_for
from blazeweb.utils import redirect
from blazeweb.views import SecureView
from werkzeug.exceptions import NotFound

class CommonBase(SecureView):
    def init(self):
        self._cb_action_get = None
        self._cb_action_update = None
        self._cb_action_delete = None
        self._cb_action_list = None

    def get_safe_action_prefix(self):
        return self.action_prefix.replace(' ', '_')
    safe_action_prefix = property(get_safe_action_prefix)

    def get_action(self, actname):
        localvalue = getattr(self, '_cb_action_%s' % actname)
        if localvalue:
            return localvalue
        func = '%s_%s' % (self.safe_action_prefix, actname)
        try:
            return findobj( '%s:model.actions.%s' % (self.modulename, func))
        except HierarchyImportError:
            # we assume the calling object will override action_<type>
            return None
    def test_action(self, actname):
        callable = self.get_action(actname)
        if callable is None:
            func = '%s_%s' % (self.safe_action_prefix, actname)
            raise ProgrammingError('The default "%s" function `%s` was not found.'
                                   % (actname, func))
    def get_action_get(self):
        self.test_action('get')
        return self.get_action('get')
    def get_action_update(self):
        self.test_action('update')
        return self.get_action('update')
    def get_action_delete(self):
        self.test_action('delete')
        return self.get_action('delete')
    def get_action_list(self):
        self.test_action('list')
        return self.get_action('list')
    def set_action_get(self, value):
        self._cb_action_get = value
    def set_action_update(self, value):
        self._cb_action_update = value
    def set_action_delete(self, value):
        self._cb_action_delete = value
    def set_action_list(self, value):
        self._cb_action_list = value

    action_get = property(get_action_get, set_action_get)
    action_update = property(get_action_update, set_action_update)
    action_delete = property(get_action_delete, set_action_delete)
    action_list = property(get_action_list, set_action_list)

class UpdateCommon(CommonBase):
    def init(self, modulename, objectname, classname, action_prefix=None):
        CommonBase.init(self)
        self.modulename = modulename
        self.require_all = '%s-manage' % modulename
        self.template_endpoint = 'common/update.html'
        self.objectname = objectname
        self.message_add = '%(objectname)s added successfully'
        self.message_edit = '%(objectname)s edited successfully'
        self.endpoint_manage = '%s:%sManage' % (modulename, classname)
        self.pagetitle = '%(actionname)s %(objectname)s'
        self.extend_from = settings.template.admin
        self.action_prefix = action_prefix or objectname
        try:
            self.formcls = findobj('%s:forms.%s' % (modulename, '%sForm' % classname))
        except HierarchyImportError:
            # assume the calling class will set up its own form
            pass

    def auth_post(self, oid):
        self.determine_add_edit(oid)
        self.assign_form()
        self.do_if_edit(oid)

    def determine_add_edit(self, oid):
        if oid is None:
            self.isAdd = True
            self.actionname = 'Add'
            self.message_update = self.message_add % {'objectname':self.objectname}
        else:
            self.isAdd = False
            self.actionname = 'Edit'
            self.message_update = self.message_edit % {'objectname':self.objectname}

    def assign_form(self):
        try:
            self.form = self.formcls()
        except AttributeError, e:
            if 'formcls' in str(e):
                raise ProgrammingError('%s.formcls must be set before UpdateCommon.auth_post' % type(self).__name__)

    def do_if_edit(self, oid):
        if not self.isAdd:
            dbobj = self.action_get(oid)

            if dbobj is None:
                raise NotFound

            self.form.set_defaults(self.get_form_defaults(dbobj))

    def get_form_defaults(self, dbobj):
        return dbobj.to_dict()

    def post(self, oid):
        self.form_submission(oid)
        self._call_with_expected_args(self.default)

    def form_submission(self, oid):
        if self.form.is_cancel():
            self.on_cancel()
        if self.form.is_valid():
            try:
                self.do_update(oid)
                return
            except Exception, e:
                # if the form can't handle the exception, re-raise it
                if not self.form.handle_exception(e):
                    raise
        elif not self.form.is_submitted():
            # form was not submitted, nothing left to do
            return

        # form was either invalid or caught an exception, assign error
        # messages
        self.form.assign_user_errors()

    def do_update(self, oid):
        self.update_retval = self.action_update(oid, **self.get_action_params())
        user.add_message('notice', self.message_update)
        self.on_complete()

    def get_action_params(self):
        return self.form.get_values()

    def on_complete(self):
        url = url_for(self.endpoint_manage)
        redirect(url)

    def on_cancel(self):
        redirect(url_for(self.endpoint_manage))

    def assign_vars(self):
        self.assign('actionname', self.actionname)
        self.assign('objectname', self.objectname)
        self.assign('pagetitle', self.pagetitle % {'actionname':self.actionname, 'objectname':self.objectname})
        self.assign('formobj', self.form)
        self.assign('extend_from', self.extend_from)
        
    def default(self):
        self.assign_vars()
        self.render_endpoint(self.template_endpoint)

class ManageCommon(CommonBase):
    def init(self, modulename, objectname, objectnamepl, classname, action_prefix=None):
        CommonBase.init(self)
        self.modulename = modulename
        self.require_all = '%s-manage' % modulename
        self.delete_link_require = '%s-manage' % modulename
        self.template_endpoint = 'common/manage.html'
        self.objectname = objectname
        self.objectnamepl = objectnamepl
        self.endpoint_update = '%s:%sUpdate' % (modulename, classname)
        self.endpoint_delete = '%s:%sDelete' % (modulename, classname)
        self.table = Table(class_='dataTable manage')
        self.extend_from = settings.template.admin
        self.action_prefix = action_prefix or objectname

        # messages that will normally be ok, but could be overriden
        self.pagetitle = 'Manage %(objectnamepl)s'

    def create_table(self):
        if user.has_any_token(self.delete_link_require):
            self.table.actions = \
                Links( 'Actions',
                    A(self.endpoint_delete, 'oid:id', label='(delete)', class_='delete_link', title='delete %s' % self.objectname),
                    A(self.endpoint_update, 'oid:id', label='(edit)', class_='edit_link', title='edit %s' % self.objectname),
                    width_th='8%'
                 )
        else:
            self.table.actions = \
                Links( 'Actions',
                    A(self.endpoint_update, 'oid:id', label='(edit)', class_='edit_link', title='edit %s' % self.objectname),
                    width_th='8%'
                 )

    def render_table(self):
        data = self.action_list()
        self.assign('tablehtml', self.table.render(data))

    def assign_vars(self):
        self.create_table()
        self.render_table()
        self.assign('pagetitle', self.pagetitle % {'objectnamepl':self.objectnamepl} )
        self.assign('update_endpoint', self.endpoint_update)
        self.assign('objectname', self.objectname)
        self.assign('objectnamepl', self.objectnamepl)
        self.assign('extend_from', self.extend_from)

    def default(self):
        self.assign_vars()
        self.render_endpoint(self.template_endpoint)

class DeleteCommon(CommonBase):
    def init(self, modulename, objectname, classname, action_prefix=None):
        CommonBase.init(self)
        self.modulename = modulename
        self.require_all = '%s-manage' % modulename
        self.objectname = objectname
        self.endpoint_manage = '%s:%sManage' % (modulename, classname)
        self.action_prefix = action_prefix or objectname

        # messages that will normally be ok, but could be overriden
        self.message_ok = '%(objectname)s deleted'

    def default(self, oid):
        if self.action_delete(oid):
            user.add_message('notice', self.message_ok % {'objectname':self.objectname})
        else:
            raise NotFound
        self.on_complete()

    def on_complete(self):
        url = url_for(self.endpoint_manage)
        redirect(url)
