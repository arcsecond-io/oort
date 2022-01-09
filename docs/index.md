---
home: true
heroImage: https://statics.arcsecond.io/img/logo-circle.png
heroAlt: Arcsecond Logo
heroText: Arcsecond Oort Uploader
tagline: The open-source easy-to-use tool for uploading data to Arcsecond.io.
footer: MIT Licensed | Copyright © 2018-present Arcsecond.io (F52 Tech).
---

[[toc]]

## Introduction

[Arcsecond.io](https://www.arcsecond.io) is a comprehensive cloud platform 
for astronomical observations, for individual astronomers, collaborations
and observatories. Arcsecond's cloud storage backend is 
[Amazon's S3](https://aws.amazon.com/s3/), and Oort has been thoroughly 
tested on recent Linux and macOS operating systems (it may need some tweaks 
on Windows).

**Oort is a pure uploading tool, not a two-ways syncing tool.** A file that 
is deleted locally will remain in the cloud if already uploaded. Change of
files in the cloud have no effect locally either.

Oort can be used by an observatory, when data is acquired during the night 
and are saved on disk. Upon save, files will be immediately sent to the 
cloud in an orderly manner, organised inside datasets, in the background. Or 
it can be used by individual astronomers or science groups who want to 
easily upload their data archive.

::: tip
If you are an observatory, or an astronomical consortium, or any institute 
interested in storing astronomical data in the cloud, 
[contact us](mailto:team@arcsecond.io). We would be happy to open a portal 
for you to see and try to upload data.
:::

In batch mode, Oort comes with a small local web server to monitor the 
uploader, and this is what it looks like when running:
![](./img/oort-screenshot-uploading.png)
(<a href="https://raw.githubusercontent.com/arcsecond-io/oort/master/docs/img/oort-screenshot-uploading.png">enlarge</a>)

## Installation & Update

Use pip (see [this page](https://pip.pypa.io/en/stable/installing/) on how 
to install pip, if you haven't done so):

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

::: warning
Yes, another package available through pip is called `oort` and has nothing 
to do with our case. Hence the name `oort-cloud` of our package. However, 
all commands start with the simple `oort` executable.
:::

Then, make sure to login first with oort before uploading:

```bash
$ oort login
```

Logging in through oort will retrieve a upload key that will be placed 
inside `~/.oort/config.ini`. Do not share this personal key. Note however 
that this key is not your personal API Key. The Upload Key has just enough 
permission to upload data on your behalf.  

## Datasets & DataFiles

Oort is using the folder structure to put files inside datasets. And there 
is one simple rule to know: 
::: info
* **One folder (or subfolder) = One Dataset**. 
* **For each (valid) folder content file, there will be one DataFile put 
  inside the Dataset**
:::
The rule is voluntarily simple to make Oort focused and reliable. Subsequent 
re-organisation, renaming etc will occur on the online platform.

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

## Usage

Oort has two modes, which can be used simultaneously.

::: warning
As of now, the two modes are mutually exclusive (because of the access to the 
small local SQLite database). You must **not** have oort batch mode running 
if you want to use the direct mode. If you need to use the direct mode, stop 
the batch mode first.
:::

### Direct mode

Oort can be used in a pure "upload this folder right now, please" manner, 
also called the "direct" mode. It is suited for cases where a folder contains 
existing files of data, and the content of the folder won't change over time.
Note that if it does, the command can be safely re-run.

**All non-hidden files will be uploaded.** Be careful to choose folders that 
contain only data you want to send to the cloud. Of course, in case of a
mistake, the data can later on be deleted from the various Data pages 
available on [https://www.arcsecond.io](https://www.arcsecond.io).

Here are the command for basic direct upload:

```bash
$ oort upload [OPTIONS] <folder>
```

There are three `OPTIONS`:

* `-o <subdomain>` (or `--organisation <subdomain>`) to tell Oort to send 
  files to an organisation account.
* `-t <telescope uuid>` (or `--telescope <telescope uuid>`) to specify the 
  telescope with which that data must be associated. This option is mandatory
  for uploads to an organisation account, and optional for uploads to a 
  personal account.
* `-f` (or `--force`) to force the re-upload of the folder's content. As 
  always, existing files in the cloud will never be modified or overwritten.
  Simply, Oort will reset the local metadata it keeps for every upload, and 
  start over.

The `upload` command will summarise its settings and ask for confirmation 
before proceeding.

### Batch / background mode

Oort batch mode works by watching for files in a folder, and automatically 
upload them to the cloud in the background. This mode is designed for "live
mode" where data files are being sent to a folder, during the night. Hence 
the content of the folder changes over time.

**All non-hidden files will be uploaded.** Be careful to choose folders that 
contain only data you want to send to the cloud. Of course, in case of a
mistake, the data can later on be deleted from the various Data pages 
available on [https://www.arcsecond.io](https://www.arcsecond.io).

To start, or restart the Oort batch mode, including the uploader and the 
server (see below), simply issue the command once:

```bash
oort restart
```

Then, to tell Oort which folder(s) to watch for existing and future files, 
the command is:

```bash
oort watch [OPTIONS] <folder1> <folder2> ...
```

The `OPTIONS` part of `oort watch` is important. There are three options:

* `-o <subdomain>` (or `--organisation <subdomain>`) to tell Oort to send 
  files to an organisation account.
* `-t <telescope uuid>` (or `--telescope <telescope uuid>`) to specify the 
  telescope with which that data must be associated. This option is mandatory
  for uploads to an organisation account, and optional for uploads to a 
  personal account.
* `-z` (or `--zip`) to automatically gzip data files (FITS and XISF, other 
  diles aren't touched) before upload. Default is False. Note that switching
  zip on will modify the content of the folder (replacing files with zipped 
  ooes), hence impacting a possible backup system. Moreover, zipping will
  require some CPU resource. On the other hand, it will reduce the bandwidth 
  usage and storage footprint.

The `watch` command will summarise its settings and ask for 
confirmation before proceeding.

### How does the batch mode work?

Oort-Cloud works by managing 2 processes:

• A **batch-uploader**, which takes care of creating/syncing the Datasets 
and Datafiles objects in Arcsecond.io (either in your personal account, or
your Organisation). And then upload the files.

• A **monitor-server** (small local web server), which allow you to observe, 
control and setup what is happening in the uploader (and find what
happened before too).

These processes are **managed** (by a small `supervisord` daemon), that is, 
they are automatically restarted if they crash.

### Why 0.0.0.0:5000 ?

The little web server that Oort starts locally has the address 
<code>http://0.0.0.0:5000 </code>. With such IP address, the oort processes 
can run in the PC where data is sent to, and still being monitored from a 
remote PC without login.

It is particularly useful for observatories managing various PCs with 
different roles.

Say for instance the PC that receives all the data is PC42 and you work on 
PC17. Oort watch command has been issued on PC42. From PC17 you can monitor
what happens on PC42 by simply visiting <code>http://&lt;ip address of 
pc42&gt;:5000 </code>.

## All batch mode commands

Use:

* `oort start`, to start the batch-uploader and the monitor-server.
* `oort stop` to stop the batch-uploader and the monitor-server
* `oort restart`, in case you need a full reconfiguration and restart.
* `oort status` to check the status of the two processes.
* `oort logs` to display the latest batch-uploader logs in the terminal.
* `oort open` to open the monitor web server in the default browser
* `oort folders` to display a list of the folders watched abd their settings.

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
* If uploading for an organisation, Oort must necessarily be run by a member 
  of it (quite obviously).
* This tool is open-source obviously to let anyone sees it doesn't send or 
  use data that has not explicitly marked for uploading. It is also open for
  modification, or improvement. Please, use the standard GitHub pull-request 
  mechanism.
* The only auxiliary data that is collected and attached as tag of the files 
  and datasets is the machine hostname (the output of the `uname -n`
  command). See inside `oort/uploader/engine/preparator.py` and `uploader.
  py` for the line `socket.gethostname()`.
* Oort keeps all its metadata inside a hidden folder in `~/.oort/`. Be 
  careful not modifying the content of it without knowing what you do.
