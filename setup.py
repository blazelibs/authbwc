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

cdir = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(cdir, 'readme.rst')).read()
CHANGELOG = open(os.path.join(cdir, 'changelog.rst')).read()
VERSION = open(os.path.join(cdir, 'authbwc', 'version.txt')).read().strip()

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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP'
    ],
    author='Randy Syring',
    author_email='randy.syring@level12.io',
    url='https://github.com/blazelibs/authbwc/',
    license='BSD',
    packages=find_packages(exclude=['authbwc_*']),
    include_package_data=True,
    zip_safe=False,
    cmdclass={'develop': DevelopCmd},
    install_requires=[
        'CommonBWC>=0.1.0',
        'WebGrid>=0.1.6',
        'BlazeWeb>=0.3.1',
        'SQLAlchemyBWC',
        'TemplatingBWC>=0.3.0',  # for Select2
        'six',
    ],
    extras_require={
        'dev': [
            'codecov',
            'coverage',
            'flake8',
            'minimock',
            'nose',
            'pyquery',
            'tox',
            'webtest',
            'wheel',
        ]
    },
    entry_points="""
        [blazeweb.app_command]
        add-admin-user = authbwc.commands:AddAdministrator
    """,
)
