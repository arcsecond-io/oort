[![Run Tests and Linting](https://github.com/arcsecond-io/oort/actions/workflows/pythonpackage.yml/badge.svg)](https://github.com/arcsecond-io/oort/actions/workflows/pythonpackage.yml) [![Deploy Docs](https://github.com/arcsecond-io/oort/actions/workflows/docsdeploy.yml/badge.svg)](https://github.com/arcsecond-io/oort/actions/workflows/docsdeploy.yml) [![Downloads](http://pepy.tech/badge/oort-cloud)](http://pepy.tech/project/oort-cloud)

# Oort-Cloud for Arcsecond

Oort-Cloud is the open-source super-easy-to-use tool for automatically and
continuously uploading to [Arcsecond.io](https://www.arcsecond.io) files
that are inside a folder.

[Arcsecond.io](https://www.arcsecond.io) is a comprehensive cloud platform
for astronomical observations, for individual astronomers, collaborations and
observatories.

## Usage

Use pip (see [this page](https://pip.pypa.io/en/stable/installing/) on how to install pip, if you haven't done so):

```bash
$ pip install oort-cloud
```

Install for the user only (non-root):

```bash
$ pip install oort-cloud --user
```

Upgrade oort-cloud:

```bash
$ pip install oort-cloud --upgrade
```

Simple usage:

```bash
oort login
oort upload [OPTIONS] folder1 folder2 ...
```

See [detailed documentation](https://arcsecond-io.github.io/oort/) for a complete
description of all options and capabilities, with screenshots.
