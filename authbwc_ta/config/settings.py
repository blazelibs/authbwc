from os import path

from blazeweb.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
app_package = path.basename(basedir)


class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.app_package = app_package
        DefaultSettings.init(self)

        self.supporting_apps.append('basebwa')

        self.name.full = 'authbwc Test App'
        self.name.short = 'authbwc_ta'

        self.init_routing()

        self.add_component(app_package, 'sqlalchemy', 'sqlalchemybwc')
        self.add_component(app_package, 'datagrid', 'datagridbwc')
        self.add_component(app_package, 'auth', 'authbwc')
        self.add_component(app_package, 'common', 'commonbwc')

    def init_routing(self):
        self.add_route('/', 'index.html')


class Dev(Default):
    def init(self):
        Default.init(self)
        self.apply_dev_settings()

        self.db.url = 'sqlite://'


class Test(Default):
    def init(self):
        Default.init(self)
        self.apply_test_settings()

        self.components.sqlalchemy.use_split_sessions = True
        self.template.default = 'common:layout_testing.html'
        self.template.admin = 'common:layout_testing.html'
        self.emails.from_default = 'admin@example.com'

        self.db.url = 'sqlite://'

        # uncomment this if you want to use a database you can inspect
        #from os import path
        #self.db.url = 'sqlite:///%s' % path.join(self.dirs.data, 'test_application.db')

try:
    from site_settings import *
except ImportError, e:
    if 'No module named site_settings' not in str(e):
        raise
