from os import path

from blazeweb.config import DefaultSettings

basedir = path.dirname(path.dirname(__file__))
app_package = path.basename(basedir)

class Default(DefaultSettings):
    def init(self):
        self.dirs.base = basedir
        self.app_package = app_package
        DefaultSettings.init(self)

        self.name.full = 'AuthBWP Test App'
        self.name.short = 'authbwp_ta'

        self.init_routing()

        self.add_plugin(app_package, 'sqlalchemy', 'sqlalchemybwp')
        self.add_plugin(app_package, 'datagrid', 'datagridbwp')
        self.add_plugin(app_package, 'auth', 'authbwp')
        self.add_plugin(app_package, 'common', 'commonbwp')

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