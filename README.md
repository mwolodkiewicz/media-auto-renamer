# media-auto-renamer
Batch auto-renamer of media files (JPEG image and MOV/MP4 video), to include the media creation date and time string, extracted from the metadata.

Initially written in Python2, currently written in Python3.

Tested on Windows platform, but should work also on Linux platforms and also within Cygwin environment.

## Introduction

Various cameras implement different algorithms for generating file names for newly created media. 
Sometimes date and time is used in file name, sometimes kind of internal camera device index is used.
When collecting media files from different sources, especially when not using a dedicated media
library manager, organizing them becomes somewhat troublesome. Either file name clashes happen.
Or just the files get randomly arranged when using regular file explorers and or simple media browsers. 

A solution with batch renaming of media files, so as to make all file names start with a string
containing creation date and time (with seconds precision), appears to solve the above-mentioned issues. 
Firstly, the risk of name clash is minimized. Secondly, it makes media files
to self-arrange (by file names) chronorogically.

## Implementation details

Description will be extended for the following features, which have been implemented:
* format of date and time string
* using recursive mode
* using dry-run mode
* informing about duplicates during rename (and error/warning reporting in general)
* skipping rename

## Dependencies

The following Python packages are used and needs to be installed, presumably with *pip install*:
* pathlib
* imghdr
* exifread
* hachoir - removed

## Usage

Getting help for supported options:

`python.exe main3.py --help`

Renaming media files in single specific directory (non-recursively):

`python.exe main3.py --path "\\NAS\Media\Photo\Vacations 2019-06"`

Like above, but in dry-run mode, i.e. without actually renaming any files:

`python.exe main3.py --path "\\NAS\Media\Photo\Vacations 2019-06" --dry-run`

Renaming media files in sub-directories (recursively):

`python.exe main3.py --path "\\NAS\Media\Photo" --recursive --max-depth=2`

## Future considerations

Things to do:
1. Check on a Linux platform, paths processing specifically.
1. Check within Cygwin environment; ditto.
1. Remove redundant option `--recursive`, use just option `--max-depth` instead.
1. Add option to define custom format for date and time string

## Credits

Used some ideas from:
* https://github.com/ianare/exif-py
* http://stackoverflow.com/questions/21381652/python-find-record-time-of-mp4-movie
* http://stackoverflow.com/questions/21355316/getting-metadata-for-mov-video/21395803#21395803
