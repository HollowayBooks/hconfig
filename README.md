# hconfig

Tiny hierarchical config files library and CLI for YAML and JSON.

# Why?

Every system needs configs, and typically you end up setting them by a mix of file
configs, environment variables, and so on.
Configuration invariably is complex because you often have groups of settings (i.e.
the configuration is hierarchical), and then you want to selectively override certain
settings as needed (build time, config time, deploy time, etc.). Lots of complex config
management solutions exist already that do some of this.
But sometimes you just want a minimal option.

hconfig is the most minimal Python lib you can find that reads and writes files, handles
hierarchical configs (YAML or JSON), and also supports a sequence of overrides across the
hierarchy. It also:

- Supports injecting environment variables and a few data type conversions (like string to
  int) to support that.
- Can be run as a lib or command line.

Examples:

- Build your app with a base_config.yml, app_config.yml, and deploy_config.yml files, where
  each only overrides changes to the previous one.
- Build a template for a Docker configuration and then override specific pieces with another
  file or an environment varaible.

# Installation

The package has been uploaded to pip, so install is as easy as:

    pip install hconfig

# Usage

It can be used both as a library or as a CLI utility.

The CLI interface is:

    hconfig -o out.json in.json in2.json ...

The CLI automatically detects the output format based on the file extension.
Input can be either JSON or YAML.

# Develop

To develop you can just commit changes, to run test locally you need a `pipenv` setup and run
this command:

    pipenv run python test_hconfig.py

CircleCI has been configured to run tests.
