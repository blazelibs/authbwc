from setuptools import setup, find_packages

version = '0.1dev'

setup(
    name='AuthBWP',
    version=version,
    description="An authentication and authorization component for the BlazeWeb framework",
    classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    ],
    author='Randy Syring',
    author_email='rsyring@gmail.com',
    url='',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'CommonBWP>=0.1dev',
        'DataGridBWP>=0.1dev',
    ],
)
