# Welcome to the Oort-Cloud Documentation

Oort-Cloud is the open-source super-easy-to-use tool for automatically and
continuously uploading files that are inside a folder to 
[Arcsecond.io](https://www.arcsecond.io).

[Arcsecond.io](https://www.arcsecond.io) is a comprehensive cloud platform 
for astronomical observations, for individual astronomers, collaborations and 
observatories.

Oort-Cloud can be used by individual astronomers who want to store data in
a cloud dedicated to astronomical data. Or by an observatory, to store data
specifically for that organisation. For that, the organisation must have been 
registered first, and subdomain defined. See also the `--organisation` option 
below.

[Contact us](mailto:team@arcsecond.io). We would be happy to open
a portal for you to see and try, even uploading some data, before you decide. 

![https://arcsecond-io.github.io/oort/assets/oort-screenshot-uploading.png](./assets/oort-screenshot-uploading.png)
(<a href="https://arcsecond-io.github.io/oort/assets/oort-screenshot-uploading.png">enlarge</a>)

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

The `OPTIONS` part of `oort watch` is important. There are two options:
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

* `oort login` to login to Arcsecond first.
* `oort status` to check the status of the two processes (see below)
* `oort update` to update processes after upgrade Oort version.
* `oort open` to open the web server in the default browser
* `oort logs` to read the latest logs in the terminal.

And:
* `oort restart`, in case you need a full restart.
* `oort` or `oort --help` for a complete help.

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
of these two processes. These processes are managed by a small `supervisord`
daemon.

These processes are **managed**, that is, they are automatically restarted if
they crash. Use the command `oort logs` to get the latest logs of these 
processes.

### File organisations

**Oort is using the folder structure to infer the type and organisation
of files.**

Structure is as follow: Night Logs contain multiple Observation and/or
Calibrations taken the same night. To each Observation and Calibration is 
attached one (and only one) Dataset containing the files (as many as they are).

For instance, if a folder contains the word "Bias" (case-insensitive), the
files inside it will be put inside a Calibration object, associated with
a Dataset whose name is that of the folder. See below for a table of 
examples.

Keywords directing files in Calibrations are "Bias", "Dark", "Flat" and
"Calib". All other folder names are considered as target names, and put
inside Observations.

Complete subfolder names will be used as Dataset and Observation / Calibration
names.

For instance, FITS or XISF files found in `<root>/NGC3603/mosaic/Halpha`
will be put in an Observation (not a Calibration, there is no special
keyword found), and its Dataset will be named identically
`NGC3603/mosaic/Halpha`.

| <sup>File Path | &nbsp; &nbsp; &nbsp;<sup>Local Time</sup>&nbsp; &nbsp; &nbsp; | &nbsp; &nbsp; &nbsp;<sup>Night Log Date</sup>&nbsp; &nbsp; &nbsp; | <sup>Type | <sup>Dataset Name |
| ---- | ---- | ---- | ---- | ------------ |
| <sup>`<root>/NGC3603/Halpha/Mosaic1.fits`</sup> | <sup>Sep. 9, 2020, 2pm | <sup>2020-09-09 | <sup>Obs. | <sup>`NGC3603/Halpha`</sup> |  
| <sup>`<root>/Calibration/MasterBias.xisf`</sup> | <sup>Sep. 21, 2020, 9am | <sup>2020-09-20 | <sup>Calib. | <sup>`Calibration`</sup> |  
| <sup>`<root>/Tests/Flats/U/U1.fit`</sup> | <sup>Sep. 30, 2020, 01am | <sup>2020-09-30 | <sup>Calib. | <sup>`Tests/Flats/U`</sup> |  
| <sup>`<root>/NGC3603_V_2x2.fit`</sup> | <sup>Oct. 15, 2020, 04am | <sup>2020-10-15 | <sup>Obs. | <sup>`(folder <root>)`</sup> |  
| <sup>`<root>/passwords.csv`</sup> | | | | <sup>not uploaded (not fits or xisf) |  
| <sup>`<root>/GRO_J1655-40.FITS`</sup> | | | | <sup>not uploaded (no date obs found) |  

etc.

### A note on dates: night are running from noon to noon

All Calibrations and Observations are automatically associated with
Night Logs whose date is inferred from the observation date of the files.
Oort takes automatically care of the right "date" whether the file is taken
before or after noon on that local place. In other words, the "night"
boundaries are running from local noon to the next local noon.


## Key things you must be aware of

* There is no need to install or run Oort as `root`.
* One must login first before uploading, with the command `oort login`. It will 
locally store the necessary credentials used for uploading. **Keep these credentials safe**.
* If uploading for an organisation, Oort must necessarily be run someone who is a member of it.
* To determine the Night Log date, Oort reads the FITS or XISF header and look for
 any of the following keywords: `DATE`, `DATE-OBS` and `DATE_OBS`. Dates are
 assumed to be local ones.
* "Nights" run from local noon to local noon. That is, all data files whose
date is in the morning, until 12am, is considered as part of the night that
just finished. The Night Log date is that of the starting noon.