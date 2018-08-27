from setuptools import setup
#from pipenv.project import Project
#from pipenv.utils import convert_deps_to_pip

#pfile = Project(chdir=False).parsed_pipfile
#requirements = convert_deps_to_pip(pfile['packages'], r=False)
#test_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)

setup(
  name='HConfig',
  version='0.3',
  packages=[
    'hconfig',
  ],
  license='Apache',
  long_description=open('README.md').read(),
  install_requires=["strif", "ruamel.yaml==0.15.60"],
  url="https://github.com/feynmanlabs/hconfig",
  maintainer="Holloway Inc",
  maintainer_email="info@holloway.com",
  scripts=['scripts/hconfig'])
