# media-auto-renamer
Automatic renamer of media files (JPEG image and MOV/MP4 video) to include the media creation date and time string, extracted from the metadata.

Originally written in Python2, currently written in Python3.

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

## Dependencies

The following Python packages are used and needs to be installed, presumable with ''pip install'':
* exifread
* pathlib
* imghdr
* hachoir - removed

## Credits

Used some ideas from:
* https://github.com/ianare/exif-py
* http://stackoverflow.com/questions/21381652/python-find-record-time-of-mp4-movie
* http://stackoverflow.com/questions/21355316/getting-metadata-for-mov-video/21395803#21395803
