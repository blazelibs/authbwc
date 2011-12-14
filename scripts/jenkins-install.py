import os
from jenkinsutils import BuildHelper

package = 'AuthBWC'
type = 'install'

bh = BuildHelper(package, type)

# delete & re-create the venv
bh.venv_create()

# install package
bh.vecall('pip', 'install', package)

# make sure we can import the module as our "test"
bh.vecall('python', '-c', 'import authbwc')
