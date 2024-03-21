---
layout: doc
---

![img](https://statics.arcsecond.io/img/logo-circle-sm.png)

# Arcsecond Oort Uploader

The open-source easy-to-use tool for uploading data to Arcsecond.io.

## Quick start for Observatory Portals

```bash
$ pip install oort-cloud 
$ oort login
$ oort upload <path to a folder>
```

## Introduction

Oort is Arcsecond's uploader tool. [Arcsecond.io](https://www.arcsecond.io) is a
comprehensive cloud platform for astronomical observations, for individual
astronomers and observatories. Hence, Oort can be used by individuals to upload
their data to their Arcsecond account, or observatories to their portal.

::: tip
To open an Observatory Portal, simply visit your Arcsecond settings
[here](https://www.arcsecond.io/profile#memberships) and click "Create Portal".
:::

**Oort is a pure uploading tool, not a two-ways syncing tool.** A file that
is deleted locally will remain in the cloud if already uploaded. Change of
files in the cloud have no effect locally either.

Oort has been thoroughly tested on recent Linux and macOS operating systems
(it may need some tweaks on Windows).

## Installation & Update

Use pip (see [this page](https://pip.pypa.io/en/stable/installing/) on how
to install pip, if you haven't done so):

```bash
$ pip install oort-cloud
```

::: warning
The Pypi database already contains an `oort` package (without the `-cloud`
suffix) and it has nothing to do with ours.
:::

Install for the user only (non-root):

```bash
$ pip install oort-cloud --user
```

Upgrade oort-cloud:

```bash
$ pip install oort-cloud --upgrade
```

::: info
Even if our package is named `oort-cloud`,
all commands start with the simple `oort` string.
:::

Then, make sure to login first with oort before uploading:

```bash
$ oort login
```

Logging in through oort will retrieve your personal Upload Key that will be
placed inside `~/.oort/config.ini`. **Do not share this key.**

::: info
This key is not your personal API Key. The Upload Key has just enough
permission to upload data on your behalf, and it cannot give access to your
account. It can also be reset from your Arcsecond
[account settings](https://www.arcsecond.io/profile#keys).
:::

## Usage

**All non-hidden files will be uploaded.** Be careful to choose folders that
contain only data you want to send to the cloud. Of course, in case of a
mistake, the data can later on be deleted from the various Data pages
available on the web.

Here are the command for basic direct upload:

```bash
$ oort upload [OPTIONS] <folder>
```

There are five `OPTIONS`:

* `-o <subdomain>` (or `--organisation <subdomain>`) to tell Oort to send
  files to an organisation account.
* `-t <telescope uuid>` (or `--telescope <telescope uuid>`) to specify the
  telescope with which that data must be associated. This option is mandatory
  for uploads to an organisation account, and optional for uploads to a
  personal account.
* `-f` (or `--force`) to reset the local metadata and force the re-upload of
  the folder's content. As always, existing files in the cloud will never be  
  modified or overwritten.
* `-z` (or `--zip`) to tell Oort to zip FITS and XISF files before uploading 
  them. If they are already zipped, they won't be changed.
* `-d <name or uuuid>` (or `--dataset <name or uuuid>`) to tell Oort to what
  dataset all files of the folder (and its subfolders). must be put. The 
  argument can either be a name or a UUID. If it is a name, Oort will try to 
  find it. If none is found, Oort will create it. If it is a UUID, Oort will 
  look for it. If none is found, Oort will raise an error.

The `upload` command will summarise its settings and ask for confirmation
before proceeding. It is a small step to ensure that no mistake have been
made before starting upload.

## Other Oort commands

Use:

* `oort telescopes` to get a list of telescopes available (filtered to an
  organisation with the `-o <subdomain>` option).
* `oort login` to login to your personal Arcsecond.io account and fetch your
  personal upload key.
* `oort --version` to display Oort version
* `oort` or `oort --help` for a complete help.

All commands have a dedicated help accessible with `oort <command> --help`

There is no need of using `sudo` in any case with oort.

## Datasets & DataFiles

Oort is using the folder structure to put files inside datasets. And there
is one simple rule to know:
::: info

* **One folder (or subfolder) = One Dataset**.
* **For each (valid) folder content file, there will be one DataFile put
  inside the Dataset**
  :::
  The rule is voluntarily simple to make Oort focused and reliable. Subsequent
  re-organisation, renaming etc. will occur on the web.

For instance, for a folder structure on disk, where Oort has been instructed
to upload the content of the folder `data/`:

```
data/
│   README.md
│   file001.txt    
│
└───folder1/
│   │   file011.fits
│   │   file012.xisf
│   │
│   └───subfolder1/
│       │   .hidden_file111.txt
│       │   file112.asf
│       │   ...
│   
└───folder2/
    │   file021.jpeg
    │   file022.fts
```

There will be 4 Datasets, with the following names:

* `data` containing the DataFiles for `README.md` and `file001.txt`
* `data/folder1` containing the DataFiles for `file011.fits` and `file012.xisf`
* `data/folder1/subfolder1` containing the DataFiles for `file112.asf` only
* `data/folder2` containing the DataFiles for `file021.jpeg` and `file022.fts`

Datasets and DataFiles will be tagged with various information (folder name,
telescope UUID etc) to help Arcsecond's backend post-process the files.

## How files are treated

### File extensions

All non-hidden files found in the watch folder or one of its subfolder will
be uploaded. Files can have an extension or not (for instance `README` files
will also be uploaded). Hidden files starting with a dot will not be uploaded.

As for the data, **Oort support XISF and FITS files, zipped or not.** Oort
will accept files with the following FITS filename extensions:
`.fits`, `.fit`, `.fts`, `.ft`, `.mt`, `.imfits`, `.imfit`, `.uvfits`,
`.uvfit`, `.pha`, `.rmf`, `.arf`, `.rsp`, `.pi`
as well as `.xisf` ones.

Moreover, these extensions can be augmented with the following zipped file
extensions: `.zip`, `.gz`, `.bz2`

### File compression

Files to be uploaded can be already compressed or not. Oort is able to deal
with any of them transparently.

If a XISF or FITS file is being detected and the zip option is set (in the
`watch` command), it will be zipped (with standard) `gzip` compression
before being uploaded. The compression is made locally just beside the
original file. That latter file will be deleted once the zip is done (as
would a normal `gzip` command do in the terminal).

**Oort includes an interruption handler that will stop any zip process
running**, would any problem occurs preventing the process to complete. More
precisely it will stop zip processes on `SIGINT`, `SIGQUIT` and `SIGTERM`.

Of course, if the folder is read-only for its user, no zipping will be made.

## Additional things you must be aware of

* There is no need to install or run Oort as `root`.
* One must login first before uploading, with the command `oort login`. It
  will locally store the necessary credentials used for uploading. **Keep
  these credentials safe**.
* Note that `oort login` fetches a limited-scope upload key, just enough to
  perform its task.
* If uploading for an Observatory Portal, Oort must necessarily be run by a member
  of it (quite obviously), with role `member` or above. See
  [permissions](https://docs.arcsecond.io/portals/permissions) for more details.
* This tool is open-source obviously to let anyone sees it doesn't send or
  use data that has not explicitly marked for uploading. It is also open for
  modification, or improvement. Please, use the standard GitHub pull-request
  mechanism.
* The only auxiliary data that is collected and attached as tag of the files
  and datasets is the machine hostname (the output of the `uname -n`
  command). See inside `oort/preparator.py` and `uploader.py` for the 
  line `socket.gethostname()`.
* Oort keeps all its metadata inside a hidden folder in `~/.oort/`. Be
  careful not modifying the content of it without knowing what you do.
