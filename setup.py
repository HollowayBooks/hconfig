# Copyright 2019 Holloway Inc

from setuptools import setup

setup(
  name='HConfig',
  version='0.5.1',
  packages=[
    'hconfig',
  ],
  license='Apache',
  long_description=open('README.md').read(),
  install_requires=["strif", "ruamel.yaml==0.15.60"],
  url="https://github.com/hollowayguides/hconfig",
  maintainer="Holloway Inc",
  maintainer_email="hello@holloway.com",
  scripts=['scripts/hconfig'])
