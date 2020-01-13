# Arcsecond's Oort Cloud

Oort Cloud is a small utility that starts a little server allowing to:

* Automatically upload all the files of a folder (see below), as they appear
* Upload to your personal or organisation account.
* Make available a local webpage allowing to follow the upload operations live.
* Keep track of past uploads  

In one word, Oort Cloud send your files to Arcsecond's cloud for storage.

Installation
===

```sh
$ pip install oort-cloud
``` 

This will also install the `arcsecond` [CLI](https://github.com/arcsecond-io/cli).

Usage
===

```sh
$ arcsecond login 
$ cd <parent folder where files are located>
// for uploading to a personal account:
$ oort
// for uploading to an organisation account whose subdomain is 'saao':
$ oort -o saao
``` 

That's it! Now, you can open a browser in `http://localhost:5000` and follow the operations.

![Oort in action](/assets/oort-cloud-basic.png)