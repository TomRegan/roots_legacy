#!/usr/bin/env python

from setuptools import setup

setup(name='roots',
      version='1.0.0',
      description='roots e-book library manager',
      author='Tom Regan',
      author_email='code.tom.regan@gmail.com',
      url='https://github.com/TomRegan/roots',
      license="http://www.apache.org/licenses/LICENSE-2.0",
      packages=['roots'],
      install_requires=[
          'pyyaml==4.2b4',
          'click==4.1',
          'mkdocs==0.11.1',
          'requests==2.21.0',
          'texttable==0.8.1',
          # Tests
          'nose==1.3.4',
          'responses==0.3.0'
      ],
      entry_points={
          'console_scripts': [
              'root = roots.roots:main',
          ]}
)
