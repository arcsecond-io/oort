# Welcome to the Oort Documentation

Oort is the open-source super-easy-to-use tool for automatically and
continuously uploading to [Arcsecond.io](https://www.arcsecond.io)
files that are inside a folder.

[Arcsecond.io](https://www.arcsecond.io) is a comprehensive cloud platform 
for astronomical observations, for individual astronomers, collaborations and 
observatories.

Cloud storage backend is [Amazon's S3](https://aws.amazon.com/s3/), 
and Oort has been thoroughly tested on recent Linux and macOS operating systems 
(it may need some tweaks on Windows).

Oort is a pure push up tool, not a two-way syncing tool. A file that
is deleted locally will remain in the cloud if already uploaded. Change
of files in the cloud have no effect locally either.

Oort can be used by individual astronomers who want to store data in
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
tree and upload existing files. Then it will detect and upload any new file being added
inside the watch folder (or in one of its subfolder).

**All non-hidden files will be uploaded.** 
<span style='color: red;'>And data files will be compressed automatically before upload.</span> 
See below for details.

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

### File extensions

All non-hidden files found in the watch folder or one of its subfolder will be uploaded.
Files can have an extension or not (for instance `README` files will also be uploaded).

As for the data, **Oort support XISF and FITS files, zipped or not.** 
Oort will accept files with the following FITS filename extensions:

`.fits`, `.fit`, `.fts`, `.ft`, `.mt`, `.imfits`, `.imfit`, `.uvfits`, 
`.uvfit`, `.pha`, `.rmf`, `.arf`, `.rsp`, `.pi`

as well as `.xisf` ones.

Moreover, these extensions can be augmented with the following zipped file
extensions: `.zip`, `.gz`, `.bz2`

### File compression

Files to be uploaded can be already compressed or not, oort is able to deal with
any of them transparently.

However, if a XISF or FITS file is being detected, it will be zipped (with standard)
`gzip` compression before being uploaded. The compression is made locally just beside the
original file, which will be deleting once zip is done (as would a normal `gzip` command
do in the terminal).

**Oort includes an interruption handler that will stop any zip process running**, would
any problem occurs preventing the process to complete. More precisely it will stop
zip processes on `SIGINT`, `SIGQUIT` and `SIGTERM`.

<span style='color: red;'>Oort is a compressor tool for data files too.</span>

Oort has a limitation nonetheless: if the folder is read-only, no zipping will be
permitted and file will not be uploaded. We are working on solving this problem.

### Folder structure and Data organisation

**Oort is using the folder structure to infer the type and organisation of files.**

Structure is as follow: Night Logs contain multiple Observation and/or
Calibrations taken the same night. To each Observation and Calibration is 
attached one (and only one) Dataset containing one or more files.

For instance, if the folder on disk contains the word "Bias" (case-insensitive), 
the files inside it will be put inside a Calibration object, associated with
a Dataset whose name is that of the folder. Complete subfolder names will be 
used as Dataset and Observation / Calibration names. See below for a table of 
examples.

Keywords directing files to Calibrations containers are <code>bias</code>, 
<code>dark</code>, <code>flat</code> and <code>calib</code> (all case-insensitive). All other folder names are considered as target names, and put
inside Observations containers.

For instance, FITS or XISF files found in `<root>/NGC3603/mosaic/Halpha`
will be put in an Observation (not a Calibration, since there is no special
keyword found), and its Dataset will be named identically
`NGC3603/mosaic/Halpha`.

To determine the Night Log date, Oort reads the FITS or XISF header and look for
any of the following keywords: `DATE`, `DATE-OBS` and `DATE_OBS`. Dates are 
assumed to be local ones.

**"Nights" run from local noon to local noon.** That is, all data files whose
date is in the morning, until 12am, is considered as part of the night that
just finished. The Night Log date is that of the starting noon.

### Folder structure examples

#### `<root>/NGC3603/Halpha/Mosaic1.fits` 
with Local time `Sep. 9, 2020, 2pm` will give:
    
| NL Date | Type | Dataset | Filename | Format |
 ---- | ---- | ------------ | --- | --- |
| `2020-09-09` | Obs | `NGC3603/Halpha` | `Mosaic1.fits.gz` | FITS |

<br/>

#### `<root>/Calibration/MasterBias.xisf` 
with Local time `Sep. 21, 2020, 9am` will give:
    
| NL Date | Type | Dataset | Filename | Format |
 ---- | ---- | ------------ | --- | --- |
| `2020-09-20` | Calib | `Calibration` | `MasterBias.xisf` | XISF |

<br/>

#### `<root>/Tests/Flats/U/U1.fit.gz` 
with Local time `Sep. 30, 2020, 01am` will give:
    
| NL Date | Type | Dataset | Filename | Format |
 ---- | ---- | ------------ | --- | --- |
| `2020-09-30` | Calib | `Tests/Flats/U` | `U1.fit.gz` | FITS |

<br/>

#### `<root>/NGC3603_V_2x2.fit` 
with Local time `Oct. 15, 2020, 04am` will give:
    
| NL Date | Type | Dataset | Filename | Format |
 ---- | ---- | ------------ | --- | --- |
| `2020-10-15` | Obs | `(folder <root>)` | `NGC3603_V_2x2.fit` | FITS |

<br/>

#### `<root>/GRO_J1655-40.FITS` but no `DATE`, not `DATE-OBS` nor `DATE_OBS` found

| NL Date | Type | Dataset | Filename | Format |
 ---- | ---- | ------------ | --- | --- |
| (none) | (None) | `(folder <root>)` | `GRO_J1655-40.FITS` | FITS |

There will be no Observation or Calibration created when there is 
no Night Log present, for which the date is mandatory. 

<br/>

#### `<root>/folder1/passwords.csv`

| NL Date | Type | Dataset | Filename | Format |
 ---- | ---- | ------------ | --- | --- |
| (none) | (None) | `folder1` | `passwords.csv` | csv |

<br/>

#### `<root>/folder1/folder2/folder3/README`

| NL Date | Type | Dataset | Filename | Format |
 ---- | ---- | ------------ | --- | --- |
| (none) | (None) | `folder1/folder2/folder3` | `README` | (None) |

<br/>

#### `<root>/subfolder/.svn/revision.log`

Will not be uploaded because it is inside a hidden folder (starting with a `.`).

<br/>

#### `<root>/folder2/subfolder/.config`

Will not be uploaded because it is an hidden file (starting with a `.`).

## Key things you must be aware of

* There is no need to install or run Oort as `root`.
* One must login first before uploading, with the command `oort login`. It will 
locally store the necessary credentials used for uploading. **Keep these credentials safe**.
* Note that `oort login` fetches a limited-scope upload key, just enough to perform its task. 
  To the contrary of `arcsecond login` which fetches your full API key.  
* If uploading for an organisation, Oort must necessarily be run someone who is a 
  member of it (quite obviously).
