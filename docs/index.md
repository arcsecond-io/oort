# Welcome to the Oort-Cloud Documentation

Oort-Cloud is the open-source super-easy-to-use tool for automatically and
continuously uploading files that are inside a folder to 
[Arcsecond.io](https://www.arcsecond.io).

[Arcsecond.io](https://www.arcsecond.io) is a comprehensive cloud platform 
for astronomical observations, for individual astronomers, collaborations and 
observatories.

## Installation & Update

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

Note that a PyPi package named `oort` (without the `-cloud`) already exists (unfortunately), 
and has nothing to do with our case. The CLI commands below nonetheless start with 
`oort` only.

## Start & Watch

Almost no-step-3 usage (the first one is to login to Arcsecond.io if not yet done):

```bash
oort login
oort restart
oort watch [OPTIONS] folder1 folder2 ...
```

The `OPTIONS` part of `oort watch is important. There is two option:
* `-o <subdomain>` (or `--organisation <subdomain>`) to specify that uploads of 
that folder will be sent to that organisation.
* `-t <telescope uuid>` (or `--telescope <telescope uuid>`) to specify to which 
telescope the Night Logs must be attached. This option is mandatory for organisation
uploads, and optional for personal uploads.

Oort will summarize the settings associated with the new watched folder, and ask for
confirmation before proceeding.   

After a `oort watch` command is issued, oort will first walk through the whole folder
tree and upload existing files. 

## Manage and Monitor

* `oort open` to open the web server in the default browser
* `oort logs` to read the latest logs in the terminal.
* `oort status` to check the status of the two processes (see below)
* `oort update` to update processes after upgrade Oort version.


## How does it work?

### An Uploader process and a Server process

Oort-Cloud works by managing 2 processes:

• An **uploader**, which takes care of creating/syncing the right Night Logs,
    Observations and Calibrations, as well as Datasets and Datafiles in
    Arcsecond.io (either in your personal account, or your Organisation).
    And then upload the files.
    
• A small **web server**, which allow you to monitor, control and setup what is
    happening in the uploader (and find what happened before too).

A subset of the `oort` subcommands is dedicated to start, stop and get status
of these two processes. 

These processes are **managed**, that is, they are automatically restarted if
they crash. Use the command `oort logs` to get the latest logs of these 
processes.

### File organisations

**Oort is using the folder structure to infer the type and organisation
of files.**

Structure is as follow: Night Logs contain multiple Observation and/or
Calibrations. To each Observation and Calibration is attached a Dataset
containing the files.

For instance, if a folder contains the word "Bias" (case-insensitive), the
files inside it will be put inside a Calibration object, associated with
a Dataset whose name is that of the folder.

Keywords directing files in Calibrations are "Bias", "Dark", "Flat" and
"Calib". All other folder names are considered as target names, and put
inside Observations.

Complete subfolder names will be used as Dataset and Observation / Calibration
names.

For instance, FITS or XISF files found in `<root>/NGC3603/mosaic/Halpha`
will be put in an Observation (not a Calibration, there is no special
keyword found), and its Dataset will be named identically
`NGC3603/mosaic/Halpha`.

### A note on dates: night are running from noon to noon

All Calibrations and Observations are automatically associated with
Night Logs whose date is inferred from the observation date of the files.
Oort takes automatically care of the right "date" whether the file is taken
before or after noon on that local place. In other words, the "night"
boundaries are running from local noon to the next local noon.


## Key principles you must be aware of

* Oort doesn't need to be run as `root`.
* If uploading for an organisation, Oort is necessarily run by a member of it.
* API keys are stored in clear in the uploading machine.
 
