#!/usr/bin/env python

from setuptools import setup

setup(name='roots',
      version='1.0.0',
      description='roots e-book library manager',
      author='Tom Regan',
      author_email='code.tom.regan@gmail.com',
      url='https://github.com/TomRegan/roots',
      license="http://www.apache.org/licenses/LICENSE-2.0",
      packages=['roots', 'roots.tests'],
      entry_points={
          'console_scripts': [
              'root = roots.roots:main',
          ]}
     )
