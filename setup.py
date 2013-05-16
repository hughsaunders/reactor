#!/usr/bin/env python
##############################################################################

from setuptools import setup, find_packages

requirements = ['pykka']
excludes = ['test_runner.py', 'tests', 'tests.*']


setup(name='reactor',
      version='1.0.0',
      description='Event Reactor',
      author='rcbops',
      author_email='rcb-deploy@lists.rackspace.com',
      url='https://github.com/rpedde/reactor',
      license='Apache',
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'Intented Audience :: Information Technology',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: OS Independant',
                   'Programming Language :: Python',
                   ],
      include_package_data=True,
      packages=find_packages(exclude=excludes),
      install_requires=requirements,
      )
