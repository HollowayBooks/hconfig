# hconfig

Tiny hierarchical config files library and cli. Currently it supports JSON and YAML.

# Installation

The package has been uploaded to pip, so install is as easy as:

```
pip install hconfig
```

# Usage

It can be used both as a library or as a CLI utility, the CLi interface is:

```
hconfig -o out.json in.json in2.json ...
```

The CLI automatically detects the output format based on the file extension. Input can be either YAML or json.

# Develop

To develop you can just commit changes, to run test locally you need a `pipenv` setup and run this command:

```
pipenv run python test_hconfig.py
```

CircleCI has been configured to run tests as well.

# Publish

To publish the package to Pypi, we've been using [twine](https://pypi.org/project/twine/) and setuptools. First step is to change version number on `setup.py` file. Then you can build and upload with these commands:

```
pip install twine
python setup.py sdist
twine upload dist/HConfig-0.5.0.tar.gz
```

_Note: use `hollowayguides` Pypi account, credentials are available in Notion_
