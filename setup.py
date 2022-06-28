#!/usr/bin/env python

from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(long_description=long_description,
      long_description_content_type="text/markdown",
      name='obeliks',
      version='1.1.5',
      description='Sentence splitting & tokenization',
      author='CLARIN.SI',
      url='https://www.github.com/clarinsi/obeliks',
      packages=['obeliks'],
      scripts=['obeliks/obeliks'],
      install_requires=['lxml', 'regex'],
      package_data={'obeliks': ['res/*.txt']}
     )
