#!/usr/bin/env python

from setuptools import setup

setup(name='obeliks',
      version='1.0',
      description='Sentence splitting & tokenization',
      author='CLARIN.SI',
      url='https://www.github.com/clarinsi/obeliks',
      packages=['obeliks'],
      scripts=['obeliks/obeliks'],
      install_requires=['lxml', 'regex'],
      package_data={'obeliks': ['res/*.txt']}
     )
