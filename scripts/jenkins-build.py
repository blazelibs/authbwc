import os
from jenkinsutils import BuildHelper

package = 'AuthBWC'
type = 'build'

bh = BuildHelper(package, type)

# delete & re-create the venv
bh.venv_create()

## install package w/ setuptools develop
bh.setuppy_develop()

## run tests
bh.vepycall('nosetests', 'authbwc_ta', '--with-xunit', '--blazeweb-package=authbwc_ta')
