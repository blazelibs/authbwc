import os
import sys

from jenkinsutils import BuildHelper

package = 'AuthBWC'
type = 'build'

bh = BuildHelper(package, type)

# delete & re-create the venv
bh.venv_create()

if sys.platform == 'win32':
    # have to install a specific version of lxml that has an egg available
    # pyquery uses lxml and will install the latest if we don't specify
    bh.vepycall('easy_install', 'lxml==2.3')

## install package w/ setuptools develop
bh.setuppy_develop()

## run tests
bh.vepycall('nosetests', 'authbwc_ta', '--with-xunit', '--blazeweb-package=authbwc_ta')
