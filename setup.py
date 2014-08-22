import os
from setuptools import setup, find_packages
from setuptools.command.develop import develop as STDevelopCmd


class DevelopCmd(STDevelopCmd):
    def run(self):
        # add in requirements for testing only when using the develop command
        self.distribution.install_requires.extend([
            'WebTest',
            'PyQuery',
        ])
        STDevelopCmd.run(self)

from authbwc import VERSION

cdir = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(cdir, 'readme.rst')).read()
CHANGELOG = open(os.path.join(cdir, 'changelog.rst')).read()

setup(
    name='AuthBWC',
    version=VERSION,
    description="A user authentication and authorization component for the BlazeWeb framework",
    long_description='\n\n'.join((README, CHANGELOG)),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP'
    ],
    author='Randy Syring',
    author_email='rsyring@gmail.com',
    url='http://bitbucket.org/blazelibs/authbwc/',
    license='BSD',
    packages=find_packages(exclude=['authbwc_*']),
    include_package_data=True,
    zip_safe=False,
    cmdclass={'develop': DevelopCmd},
    install_requires=[
        'CommonBWC>=0.1.0',
        'WebGrid>=0.1.6',
        'BlazeWeb>=0.3.1',
        'TemplatingBWC>=0.3.0',  # for Select2
        # need for control panel code.  This should go away eventually, see
        # #5607.
        'BaseBWA'
    ],
    entry_points="""
        [blazeweb.app_command]
        add-admin-user = authbwc.commands:AddAdministrator
    """,
)
