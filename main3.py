#!/usr/bin/env python3
# -*- coding: utf8  -*-

r"""Utility for batch renaming of media (JPEG image and MOV/MP4 video) files to start with creation date-time string. Python3 version.

Reads EXIF tag 'DateTimeOriginal' for JPEG image files.
"""

__version__ = "0.2"
__author__ = "Marcin Wolodkiewicz"
__status__ = "Development"


import re
import sys
import optparse

## filemagic - Unix/Cygwin compatible only
# try:
#     import magic
#     has_magic = True
# except ImportError:
#     print 'Does not have (file)magic library!'
        #     with magic.Magic() as a_magic:
        #         print a_magic.id_filename(a_file),

import mimetypes

## pip install pathlib
## https://docs.python.org/3/library/pathlib.html
import pathlib

# https://docs.python.org/2/library/imghdr.html#module-imghdr
# 21.8. imghdr — Determine the type of an image
# >>> import imghdr
# >>> imghdr.what('bass.gif')
# 'gif'
import imghdr

## pip install exifread
## https://github.com/ianare/exif-py
##   EXIF tag: [Image DateTime], value: [2017:01:12 20:34:21]
##   EXIF tag: [EXIF DateTimeOriginal], value: [2017:01:12 20:34:21]
##   EXIF tag: [EXIF DateTimeDigitized], value: [2017:01:12 20:34:21]
import exifread

## pip install mp4file - does not work
# import mp4file.mp4file

## pip install hsaudiotag - does not work
## http://pythonhosted.org/hsaudiotag3k/
# import hsaudiotag.mp4
# mp4_file = hsaudiotag.mp4.File(file_path)
# print 'mp4_file=%r' % (mp4_file,)

# hachoir - appears to be incompatible with Python3
# ## pip install hachoir-core
# ## pip install hachoir-parser
# # ## pip install hachoir-metadata
# # https://web.archive.org/web/20081020052249/http://hachoir.org/wiki/hachoir-parser/code_example
# # https://bitbucket.org/haypo/hachoir/issues/33/open-file-handles-never-closed
# import hachoir_parser  # hachoir_parser.createParser
# import hachoir_core  # hachoir_core.field.field.MissingField

## raw method, without any extra libraries
## http://stackoverflow.com/questions/21355316/getting-metadata-for-mov-video/21395803#21395803
## http://stackoverflow.com/questions/21381652/python-find-record-time-of-mp4-movie
import datetime
import struct

def get_mov_timestamps(filename):
    ''' Get the creation and modification date-time from .mov metadata.

        Returns None if a value is not available.
    '''
    from datetime import datetime as DateTime
    import struct

    ATOM_HEADER_SIZE = 8
    # difference between Unix epoch and QuickTime epoch, in seconds
    EPOCH_ADJUSTER = 2082844800

    creation_time = modification_time = None

    # search for moov item
    with open(filename, "rb") as f:
        while True:
            atom_header = f.read(ATOM_HEADER_SIZE)
            #~ print('atom header:', atom_header)  # debug purposes
            if atom_header[4:8] == b'moov':
                break  # found
            else:
                atom_size = struct.unpack('>I', atom_header[0:4])[0]
                f.seek(atom_size - 8, 1)

        # found 'moov', look for 'mvhd' and timestamps
        atom_header = f.read(ATOM_HEADER_SIZE)
        if atom_header[4:8] == b'cmov':
            raise RuntimeError('moov atom is compressed')
        elif atom_header[4:8] != b'mvhd':
            raise RuntimeError('expected to find "mvhd" header.')
        else:
            f.seek(4, 1)
            creation_time = struct.unpack('>I', f.read(4))[0] - EPOCH_ADJUSTER
            creation_time = DateTime.fromtimestamp(creation_time)
            if creation_time.year < 1990:  # invalid or censored data
                creation_time = None

            modification_time = struct.unpack('>I', f.read(4))[0] - EPOCH_ADJUSTER
            modification_time = DateTime.fromtimestamp(modification_time)
            if modification_time.year < 1990:  # invalid or censored data
                modification_time = None

    # print('  DEBUG: creation_time: "%r", modification_time: "%r"' % (creation_time, modification_time))

    return creation_time, modification_time


## https://www.programiz.com/python-programming/examples/hash-file
## https://gist.github.com/aunyks/042c2798383f016939c40aa1be4f4aaf
import hashlib

# Specify how many bytes of the file you want to open at a time
BLOCKSIZE = 65536

def read_sha1_hexhash(filename):
   """"This function returns the SHA-1 hash of the file passed into it"""

   # make a hash object
   h = hashlib.sha1()

   # open file for reading in binary mode
   with open(filename,'rb') as file:

       # loop till the end of the file
       chunk = 0
       while chunk != b'':
           chunk = file.read(BLOCKSIZE)
           h.update(chunk)

   # return the hex representation of digest
   return h.hexdigest()


files_count = 0
processed_files_count = 0
renamed_files_count = 0

## pattern used only for verifying new date-time string, not for formatting
date_time_verify_re = re.compile(r'^\d{8}_\d{6}$')
## pattern used only for finding any date-time string in current file name, not for formatting
# date_time_search_re = re.compile('^.*(\d{8}_\d{6}).*$')
date_time_search_re = re.compile(r'^(.*)(\d{8}_\d{6}).*')

def process_directory(dir_path, dir_depth, options):
    global files_count, processed_files_count, renamed_files_count

    if options.max_depth > 0:
        print('Processing directory path "%s" recursively at depth %d ... ' % (dir_path.resolve(), dir_depth))
    else:
        print('Processing directory path "%s" non-recursively ... ' % dir_path.resolve())

    for tmp_path in dir_path.iterdir():
        # print('  DEBUG: tmp_path=%r' % tmp_path)

        if tmp_path.is_dir():
            if options.max_depth > dir_depth:
                process_directory(tmp_path, dir_depth +1, options)
                continue
            else:
                print('  WARNING: Not processing sub-directory path "%s", because of reached maximum depth of %d ... ' % (tmp_path, options.max_depth))
        elif not tmp_path.is_file():
            print('  INFO: Path "%s" is not a file => skipping ... ' % tmp_path)
            continue

        file_path = tmp_path

        files_count += 1
        # print('Processing file %d: "%s" ... ' % (files_count, file_path))

        file_name = file_path.name
        # parent_dir_path = file_path.parent
        # print('file_name="%s", parent_dir_path: "%s"' % (file_name, parent_dir_path))

        # print file_path.read_hexhash('md5')
        # print file_path.read_hexhash('sha1')
        # print file_path.getsize()

        guessed_mime_type = mimetypes.MimeTypes().guess_type(file_path.as_uri())[0]
        # print('  DEBUG: guessed_mime_type="%r" ' % (guessed_mime_type,))
        if guessed_mime_type is None:
            print('  WARNING: File path "%s" cannot be quessed its mime-type => skipping ... ' % file_path)
            continue

        date_time_search = date_time_search_re.match(file_name)
        # if date_time_search is not None:
        #     print(  DEBUG: date_time_search.groups()=%s, .pos=%d, .string=%s' % (date_time_search.groups(), date_time_search.pos, date_time_search.string))
        date_time_str = None

        if guessed_mime_type.startswith('image'):
            if options.skip_image is True:
                print ('  INFO: File name "%s" guessed mime-type is image, which is not to be processed => skipping ...' % file_name)
                continue

            img_type = imghdr.what(file_path)
            # print('  DEBUG: img_type=%s' % (img_type,))

            if img_type != 'jpeg':
                print('  WARNING: File path "%s" (image) does not contain JPEG image header => skipping ... ' % file_path)
                continue

            processed_files_count += 1

            ## optimization(?) for fast mode - skip file already containing some data/time string
            if options.fast is True:
                if date_time_search is not None:
                    current_date_time_prefix = date_time_search.groups()[0]
                    current_date_time_str = date_time_search.groups()[1]
                    if current_date_time_prefix == '':
                        print('  WARNING: File name "%s" (image) starts with some other date-time string "%s"' % (file_name, current_date_time_str), end='')
                    else:
                        print('  WARNING: File name "%s" (image) contains some other date-time string "%s"' % (file_name, current_date_time_str), end='')
                    print(' => fast mode - skipping ... ')
                    continue

            with open(file_path, 'rb') as img_file:
                # exif_tags = exifread.process_file(img_file)
                # for tag_key in exif_tags.keys():
                #     if tag_key in ['JPEGThumbnail']:
                #         print('  EXIF tag: [%s], value: <binary-image-thumbnail> ' % (tag_key,))
                #     else:
                #         print('  EXIF tag: [%s], value: [%s] ' % (tag_key, exif_tags[tag_key]))

                exif_tags = exifread.process_file(img_file, details=False, stop_tag='DateTimeOriginal')
                # print '  DEBUG: exif_tags=(%d)' % (len(exif_tags),)

                if 'EXIF DateTimeOriginal' in exif_tags:
                    date_time_str = str(exif_tags['EXIF DateTimeOriginal']).replace(':', '').replace(' ', '_')
                else:
                    print('  WARNING: File path "%s" (image) is missing an EXIF tag for original/creation date-time => skipping ... ' % file_path)
                    continue

        elif guessed_mime_type.startswith('video'):
            if options.skip_video is True:
                print ('  INFO: File name "%s" guessed mime-type is video, which is not ot be processed => skipping ...' % file_name)
                continue

            processed_files_count += 1

            ## optimization(?) for fast mode - skip file already containing some data/time string
            if options.fast is True:
                if date_time_search is not None:
                    current_date_time_prefix = date_time_search.groups()[0]
                    current_date_time_str = date_time_search.groups()[1]
                    if current_date_time_prefix == '':
                        print('  WARNING: File name "%s" (video) starts with some other date-time string "%s"' % (file_name, current_date_time_str), end='')
                    else:
                        print('  WARNING: File name "%s" (video) contains some other date-time string "%s"' % (file_name, current_date_time_str), end='')
                    print(' => fast mode - skipping ... ')
                    continue

            ## TODO: solve issue with this exception
            # File "main3.py", line 99, in get_mov_timestamps
            #     atom_size = struct.unpack('>I', atom_header[0:4])[0]
            # struct.error: unpack requires a buffer of 4 bytes
           
            try:
                (date_time, _) = get_mov_timestamps(file_path)
            except struct.error:
                print('  ERROR! File path "%s" (video) cannot be extracted original/creation date-time => skipping ... ' % file_path)
                continue

            if date_time is None:
                print('  WARNING: File path "%s" (video) is missing original/creation date-time => skipping ... ' % file_path)
                continue

            date_time_str = date_time.strftime("%Y%m%d_%H%M%S")

        #     mov_parser = hachoir_parser.createParser(file_path)
        #     if mov_parser is None:
        #         print('  WARNING! Failed to parse video file - unsupported format => skipping ... ')
        #         mov_parser.stream._input.close()
        #         continue

        #     # print '  DEBUG: mov_parser.getFieldType()=%s, .mime_type=%s ' % (mov_parser.getFieldType(), mov_parser.mime_type)
        #     if mov_parser.getFieldType() != 'MovFile':
        #         print('  WARNING! Failed to parse video file - not a MOV/MP4 file => skipping ... ')
        #         mov_parser.stream._input.close()
        #         continue

        #     processed_files_count += 1

        #     moov_atom = next((field for field in mov_parser if field.description == u'Atom: moov'), None)
        #     if moov_atom is None:
        #         print('  ERROR! Failed to parse video file - missing "moov" atom; skipping ... ')
        #         mov_parser.stream._input.close()
        #         continue

        #     movie_atom_list = None
        #     try:
        #         movie_atom_list = moov_atom.getField('movie')
        #     except hachoir_core.field.field.MissingField:
        #         print('  ERROR! Failed to parse video file - missing "movie" atom-list; skipping ... ')
        #         mov_parser.stream._input.close()
        #         continue

        #     mvhd_atom = next((field for field in movie_atom_list if field.description == u'Atom: mvhd'), None)
        #     if movie_atom_list is None:
        #         print('  ERROR! Failed to parse video file - missing "mvhd" atom; skipping ... ')
        #         mov_parser.stream._input.close()
        #         continue

        #     movie_hdr = None
        #     try:
        #         movie_hdr = mvhd_atom.getField('movie_hdr')
        #     except hachoir_core.field.field.MissingField:
        #         print('  ERROR! Failed to parse video file - missing "movie_hdr"; skipping ... ')
        #         mov_parser.stream._input.close()
        #         continue

        #     ## WARNING: it does not work without this dummy iteration
        #     for field in movie_hdr:
        #         pass

        #     creation_date_atom = None
        #     try:
        #         creation_date_atom = movie_hdr.getField('creation_date')
        #     except hachoir_core.field.field.MissingField:
        #         print('  ERROR! Failed to parse video file - missing "creation_date" atom; skipping ... ')
        #         mov_parser.stream._input.close()
        #         continue

        #     # >>> creation_date = mov_parser.getField('/atom[1]/movie/atom[0]/movie_hdr/creation_date')
        #     # >>> creation_date.getFieldType()
        #     # 'TimestampUnix32'
        #     # >>> repr(creation_date)
        #     # "<TimestampUnix32 path='/atom[1]/movie/atom[0]/movie_hdr/creation_date', address=32, size=32>"
        #     # >>> str(creation_date)
        #     # '2017-03-03 14:36:52'

        #     date_time_str = str(creation_date_atom).replace('-', '').replace(' ', '_').replace(':', '')

        #     mov_parser.stream._input.close()
        else:
            print('  INFO: File name "$s" guessed mime-type is neither image nor video => skipping ... ' % file_name)
            continue


        # print('  DEBUG: date_time_str [%s] ' % (date_time_str,))
        if date_time_str is None:
            print('  ERROR! Failed to determine original/creation date-time for image or video => skipping ... ')
            continue

        ## verify pattern of the date-time string
        if date_time_verify_re.match(date_time_str) is None:
            print('  ERROR! Invalid/unexpected format of determined date-time string "%s" => skipping ... ' % (date_time_str,))
            continue


        ## verify current file-name containts either the same or any other date-time string
        if date_time_search is not None:
            current_date_time_prefix = date_time_search.groups()[0]
            current_date_time_str = date_time_search.groups()[1]
            if current_date_time_prefix == '':
                if current_date_time_str == date_time_str:
                    print('  INFO: File name "%s" already starts with original/creation date-time string "%s"' % (file_name, current_date_time_str), end='')
                else:
                    print('  WARNING: File name "%s" apparently starts with some other date-time string "%s"' % (file_name, current_date_time_str), end='')
            else:
                if current_date_time_str == date_time_str:
                    print('  INFO: File name "%s" already contains original/creation date-time string "%s"' % (file_name, current_date_time_str), end='')
                else:
                    print('  WARNING: File name "%s" apparently contains some other date-time string "%s"' % (file_name, current_date_time_str), end='')

            if options.force is True:
                print(' => forcing rename ... ')
            else:
                print(' => skipping ... ')
                continue

        renamed_files_count += 1

        new_file_name = ''
        if options.erase is True:
            new_file_name = date_time_str + file_path.suffix
        elif file_name.startswith(date_time_str):
            new_file_name = file_name
        else:
            new_file_name = date_time_str + '_' + file_name

        if new_file_name == file_name:
            print('  INFO: Keeping original file name "%s" => skipping ... ' % (file_name))
            continue

        # new_file_path = dir_path.joinpath(new_file_name)
        new_file_path = file_path.with_name(new_file_name)
        # print('new_file_path=%s' % (new_file_path,))
        if new_file_path.exists():
            ## TODO: consider using the '--force' option to erase duplicate?
            if read_sha1_hexhash(file_path) == read_sha1_hexhash(new_file_path):
                print('  WARNING: New file name "%s" already exists and is identical file to the original file name "%s"; consider removing duplicate => skipping ... ' % (new_file_name, file_name))
            else:
                print('  ERROR: New file name "%s" already exists and is different file than the original file name "%s"; consider manual renaming => skipping ... ' % (new_file_name, file_name))
            continue

        if options.dry_run is not True:
            print('  INFO: Renaming file name "%s" to "%s" ... ' % (file_name, new_file_name))
            # try:
            file_path.rename(new_file_path)
            # except
        else:
            print('  INFO: Dry-run - would be renaming file name "%s" to "%s" ... ' % (file_name, new_file_name))


def main(argv=None):
    # # Decode the command line arguments to unicode
    # for i, a in enumerate(sys.argv):
    #     # >>> sys.stdin.encoding
    #     # 'cp852'
    #     # >>> locale.getpreferredencoding()
    #     # 'cp1250'
    #     # >>> sys.getfilesystemencoding()
    #     # 'mbcs'
    #     # sys.argv[i] = a.decode('ISO-8859-15')
    #     sys.argv[i] = a.decode(sys.getfilesystemencoding())

    if argv is None:
        argv = sys.argv

    # print '  DEBUG: argv=%r' % (argv,)

    parser = optparse.OptionParser()
    parser.add_option('-p', '--path', action='store', default='.', dest='path', help='directory path to start processing from; default is the current directory') #, metavar='')
    parser.add_option('-r', '--recursive', action='store_true', default=False, dest='recursive', help='whether to process directories recursively; obsoleted by option --max-depth')
    parser.add_option('-e', '--erase', action='store_true', default=False, dest='erase', help='whether to completely erase original file name (but keep extendsion); by default prepends the data-time string to the original name')
    parser.add_option('-s', '--fast', action='store_true', default=False, dest='fast', help='whether to enable fast mode skipping of file names containing any date-time string')
    parser.add_option('-d', '--dry-run', action='store_true', default=False, dest='dry_run', help='whether to run in dry-mode, i.e. without actually renaming image files')
    parser.add_option('-f', '--force', action='store_true', default=False, dest='force', help='whether to force renaming even in current file name contains date-time string')
    parser.add_option('-m', '--max-depth', action='store', type='int', default=1, dest='max_depth', help='determines maximum depth for processing directories recursively; default is 1; implies option --recursive')
    parser.add_option('', '--skip-video', action='store_true', default=False, dest='skip_video', help='whether to process image files only, i.e. skip video files')
    parser.add_option('', '--skip-image', action='store_true', default=False, dest='skip_image', help='whether to process video files only, i.e. skip image files')

    (options, _) = parser.parse_args()

    # print 'options=%r' % (options,)
    # # print 'args=%r' % (args,)
    # print 'options.path=%s' % (options.path)

    # working_path = path.Path('E:\Pictures')
    # working_path = path.Path('C:\Projects\Code\sample_imgs')
    # working_path = path.Path(u'C:\\Users\\Marcin\\Pictures\\2019-06 Vacation')
    working_path = pathlib.Path(options.path)
    # print('  DEBUG: working_path="%s", .resolve()="%s"' % (working_path, working_path.resolve()))
    if not working_path.is_dir():
        print('ERROR! Specified working path "%s" is not a valid directory => quitting ...' % (working_path,))
        return 1


    dir_path = working_path.resolve()
    dir_depth = 0

    # all_file_paths = working_path.files()
    # # print '  DEBUG: all_file_paths=', all_file_paths

    global files_count, processed_files_count, renamed_files_count

    process_directory(dir_path, dir_depth, options)

    if options.dry_run is True:
        print('Files total: %d, image/video: %d, dry-run - would be renamed: %d' % (files_count, processed_files_count, renamed_files_count))
    else:
        print('Files total: %d, image/video: %d, renamed: %d' % (files_count, processed_files_count, renamed_files_count))

    return 0

if __name__ == "__main__":
    sys.exit(main())



# >>> import hachoir_parser
# >>> vf = hachoir_parser.createParser(u'./sample_imgs/MOV_1085.MP4')

# >>> [(f.path, f.getFieldType(), f.description) for f in vf]
# [('/atom[0]', 'Atom', u'Atom: ftyp'), ('/atom[1]', 'Atom', u'Atom: moov'), ('/atom[2]', 'Atom', u'Atom: free'), ('/atom[3]', 'Atom', u'Atom:
#  mdat')]

# >>> moov=vf.getField('/atom[1]')
# >>> [(f.path, f.getFieldType(), f.description) for f in moov]
# [('/atom[1]/size', 'UInt32', u''), ('/atom[1]/tag', 'FixedString<ASCII>', u''), ('/atom[1]/movie', 'AtomList', 'Movie')]

# >>> movie = vf.getField('/atom[1]/movie')
# >>> [(f.path, f.getFieldType(), f.description) for f in movie]
# [('/atom[1]/movie/atom[0]', 'Atom', u'Atom: mvhd'), ('/atom[1]/movie/atom[1]', 'Atom', u'Atom: meta'), ('/atom[1]/movie/atom[2]', 'Atom', u'
# Atom: trak'), ('/atom[1]/movie/atom[3]', 'Atom', u'Atom: trak')]

# >>> mvhd = vf.getField('/atom[1]/movie/atom[0]')
# >>> [(f.path, f.getFieldType(), f.description) for f in mvhd]
# [('/atom[1]/movie/atom[0]/size', 'UInt32', u''), ('/atom[1]/movie/atom[0]/tag', 'FixedString<ASCII>', u''), ('/atom[1]/movie/atom[0]/movie_h
# dr', 'MovieHeader', 'Movie header')]

# >>> trak_a = vf.getField('/atom[1]/movie/atom[1]')
# >>> trak_b = vf.getField('/atom[1]/movie/atom[2]')
# >>> [(f.path, f.getFieldType(), f.description) for f in trak_a]
# [('/atom[1]/movie/atom[1]/size', 'UInt32', u''), ('/atom[1]/movie/atom[1]/tag', 'FixedString<ASCII>', u''), ('/atom[1]/movie/atom[1]/data',
# 'RawBytes', 'Raw data')]
# >>> [(f.path, f.getFieldType(), f.description) for f in trak_b]
# [('/atom[1]/movie/atom[2]/size', 'UInt32', u''), ('/atom[1]/movie/atom[2]/tag', 'FixedString<ASCII>', u''), ('/atom[1]/movie/atom[2]/track',
#  'AtomList', 'Track')]

# >>> movie_hdr = vf.getField('/atom[1]/movie/atom[0]/movie_hdr')
# >>> [(f.path, f.getFieldType(), f.description) for f in movie_hdr]
# [('/atom[1]/movie/atom[0]/movie_hdr/version', 'UInt8', u''), ('/atom[1]/movie/atom[0]/movie_hdr/flags', 'RawBytes', 'Raw data'), ('/atom[1]/
# movie/atom[0]/movie_hdr/creation_date', 'TimestampUnix32', u''), ('/atom[1]/movie/atom[0]/movie_hdr/lastmod_date', 'TimestampUnix32', u''),
# ('/atom[1]/movie/atom[0]/movie_hdr/time_scale', 'UInt32', u''), ('/atom[1]/movie/atom[0]/movie_hdr/duration', 'UInt32', u''), ('/atom[1]/mov
# ie/atom[0]/movie_hdr/play_speed', 'QTFloat32', u'1.0'), ('/atom[1]/movie/atom[0]/movie_hdr/volume', 'UInt16', u''), ('/atom[1]/movie/atom[0]
# /movie_hdr/reserved[0]', 'PaddingBytes', 'Padding'), ('/atom[1]/movie/atom[0]/movie_hdr/geom_a', 'QTFloat32', 'Width scale'), ('/atom[1]/mov
# ie/atom[0]/movie_hdr/geom_b', 'QTFloat32', 'Width rotate'), ('/atom[1]/movie/atom[0]/movie_hdr/geom_u', 'QTFloat32', 'Width angle'), ('/atom
# [1]/movie/atom[0]/movie_hdr/geom_c', 'QTFloat32', 'Height rotate'), ('/atom[1]/movie/atom[0]/movie_hdr/geom_d', 'QTFloat32', 'Height scale')
# , ('/atom[1]/movie/atom[0]/movie_hdr/geom_v', 'QTFloat32', 'Height angle'), ('/atom[1]/movie/atom[0]/movie_hdr/geom_x', 'QTFloat32', 'Positi
# on X'), ('/atom[1]/movie/atom[0]/movie_hdr/geom_y', 'QTFloat32', 'Position Y'), ('/atom[1]/movie/atom[0]/movie_hdr/geom_w', 'QTFloat32', 'Di
# vider scale'), ('/atom[1]/movie/atom[0]/movie_hdr/preview_start', 'UInt32', u''), ('/atom[1]/movie/atom[0]/movie_hdr/preview_length', 'UInt3
# 2', u''), ('/atom[1]/movie/atom[0]/movie_hdr/still_poster', 'UInt32', u''), ('/atom[1]/movie/atom[0]/movie_hdr/sel_start', 'UInt32', u''), (
# '/atom[1]/movie/atom[0]/movie_hdr/sel_length', 'UInt32', u''), ('/atom[1]/movie/atom[0]/movie_hdr/current_time', 'UInt32', u''), ('/atom[1]/
# movie/atom[0]/movie_hdr/next_track', 'UInt32', u'')]
# >>> movie_hdr.getField('current_time')
# <UInt32 path='/atom[1]/movie/atom[0]/movie_hdr/current_time', address=736, size=32>
# >>> movie_hdr.getField('creation_date')
# <TimestampUnix32 path='/atom[1]/movie/atom[0]/movie_hdr/creation_date', address=32, size=32>
# >>> movie_hdr.getField('creation_date').value
# datetime.datetime(2017, 3, 3, 14, 36, 52)
# >>> movie_hdr.getField('creation_date').description
# u''
# >>> movie_hdr.getField('creation_date').value
# datetime.datetime(2017, 3, 3, 14, 36, 52)
# >>> str(movie_hdr.getField('creation_date'))
# '2017-03-03 14:36:52'
# >>> creation_date = vf.getField('/atom[1]/movie/atom[0]/movie_hdr/creation_date')
# >>> creation_date.getFieldType()
# 'TimestampUnix32'
# >>> repr(creation_date)
# "<TimestampUnix32 path='/atom[1]/movie/atom[0]/movie_hdr/creation_date', address=32, size=32>"
# >>> str(creation_date)
# '2017-03-03 14:36:52'
