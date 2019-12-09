#!/usr/bin/python
# -*- coding: utf8  -*-

r"""Utility for batch renaming media (JPEG image and MOV/MP4 video) to start with creation date-time string. Abandoned Python2 version.

Reads EXIF tag 'DateTimeOriginal' for JPEG image files.
Reads 'creation_date' from movie headers fro MOV/MP4 video files.
"""

__version__ = "0.1"
__author__ = "Marcin Wolodkiewicz"
__status__ = "Prototype"


import re
import sys

# try:
#     ## WARNING: filemagic is Unix/Cygwin compatible only
#     import magic
#     has_magic = True
# except ImportError:
#     print 'Does not have (file)magic library!'
        #     with magic.Magic() as a_magic:
        #         print a_magic.id_filename(a_file),

import mimetypes

import optparse

## pip install path.py
## https://pypi.python.org/pypi/path.py
## https://pathpy.readthedocs.io/en/latest/api.html
import path

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

## pip install hachoir-core
## pip install hachoir-parser
# ## pip install hachoir-metadata
# https://web.archive.org/web/20081020052249/http://hachoir.org/wiki/hachoir-parser/code_example
# https://bitbucket.org/haypo/hachoir/issues/33/open-file-handles-never-closed
import hachoir_parser  # hachoir_parser.createParser
import hachoir_core  # hachoir_core.field.field.MissingField

# raw method, without any extra libraries
# http://stackoverflow.com/questions/21355316/getting-metadata-for-mov-video/21395803#21395803
# http://stackoverflow.com/questions/21381652/python-find-record-time-of-mp4-movie


def main(argv=None):
    # Decode the command line arguments to unicode
    for i, a in enumerate(sys.argv):
        # >>> sys.stdin.encoding
        # 'cp852'
        # >>> locale.getpreferredencoding()
        # 'cp1250'
        # >>> sys.getfilesystemencoding()
        # 'mbcs'
        # sys.argv[i] = a.decode('ISO-8859-15')
        sys.argv[i] = a.decode(sys.getfilesystemencoding())

    if argv is None:
        argv = sys.argv

    # print 'argv=%r' % (argv,)

    parser = optparse.OptionParser()
    parser.add_option('-p', '--path', action='store', default='.', dest='path', help='working directory path containing image files to rename; default is current directory') #, metavar='')
    parser.add_option('-r', '--recursive', action='store_true', default=False, dest='recursive', help='whether to process working directory recursively')
    parser.add_option('-e', '--erase', action='store_true', default=False, dest='erase', help='whether to completely erase original file name (but keep extension); by default prepends the data-time string to the original name')
    parser.add_option('-d', '--dry-run', action='store_true', default=False, dest='dry_run', help='whether to run in dry-mode, i.e. without actually renaming image files')
    parser.add_option('-f', '--force', action='store_true', default=False, dest='force', help='whether to force renaming even in current file name contains date-time string')

    (options, args) = parser.parse_args()

    # print 'options=%r' % (options,)
    # print 'args=%r' % (args,)
    # print 'options.path=%s' % (options.path)

    # working_path = path.Path('E:\Zdjecia')
    # working_path = path.Path('C:\Projekty\Zdjeciownik\sample_imgs')
    # working_path = path.Path(u'C:\\Users\\Uparcin\\Pictures\\2017-01 biegówki Zbychowo')
    working_path = path.Path(options.path)
    print '  DEBUG: working_path=%s, .realpath()=%s' % (working_path, working_path.realpath())
    if not working_path.isdir():
        print 'ERROR! specified working directory path "%s" is not a valid directory; quitting ...' % (working_path,)
        return 1


    ## pattern used only for verifying new date-time string, not for formatting
    date_time_verify_re = re.compile(r'^\d{8}_\d{6}$')
    ## pattern used only for finding any date-time string in current file name, not for formatting
    # date_time_search_re = re.compile('^.*(\d{8}_\d{6}).*$')
    date_time_search_re = re.compile(r'^(.*)(\d{8}_\d{6}).*')


    all_file_paths = working_path.files()
    # print '  DEBUG: all_file_paths=', all_file_paths

    for file_path in all_file_paths:
        print file_path

        dir_path = file_path.dirname()
        file_name = file_path.basename()

        # if file_path.isfile() ...

        # print file_path.read_hexhash('md5')
        # print file_path.read_hexhash('sha1')
        # print file_path.getsize()

        guessed_mime_type = mimetypes.MimeTypes().guess_type(file_path)[0]
        # print '  DEBUG: guessed_mime_type=%s ' % (guessed_mime_type,)
        ## WORKAROUND: for guesses mime type being None
        guessed_mime_type = guessed_mime_type or ''

        date_time_str = None

        if guessed_mime_type.startswith('image'):
            img_type = imghdr.what(file_path)
            # print '  DEBUG: img_type=%s' % (img_type,)

            if img_type != 'jpeg':
                print '  WARNING! Failed to parse image file - not a JPEG image; skipping ... '
                continue

            with open(file_path, 'rb') as img_file:
                # exif_tags = exifread.process_file(img_file)
                # for tag_key in exif_tags.keys():
                #     if tag_key in ['JPEGThumbnail']:
                #         print '  EXIF tag: [%s], value: <binary-image-thumbnail> ' % (tag_key,)
                #     else:
                #          print '  EXIF tag: [%s], value: [%s] ' % (tag_key, exif_tags[tag_key])

                exif_tags = exifread.process_file(img_file, details=False, stop_tag='DateTimeOriginal')
                # print '  DEBUG: exif_tags=(%d)' % (len(exif_tags),)

                if 'EXIF DateTimeOriginal' in exif_tags:
                    date_time_str = str(exif_tags['EXIF DateTimeOriginal']).replace(':', '').replace(' ', '_')

        elif guessed_mime_type.startswith('video'):
            mov_parser = hachoir_parser.createParser(file_path)
            if mov_parser is None:
                print '  WARNING! Failed to parse video file - unsupported format; skipping ... '
                mov_parser.stream._input.close()
                continue

            # print '  DEBUG: mov_parser.getFieldType()=%s, .mime_type=%s ' % (mov_parser.getFieldType(), mov_parser.mime_type)
            if mov_parser.getFieldType() != 'MovFile':
                print '  WARNING! Failed to parse video file - not a MOV/MP4 file; skipping ... '
                mov_parser.stream._input.close()
                continue

            moov_atom = next((field for field in mov_parser if field.description == u'Atom: moov'), None)
            if moov_atom is None:
                print '  ERROR! Failed to parse video file - missing "moov" atom; skipping ... '
                mov_parser.stream._input.close()
                continue

            movie_atom_list = None
            try:
                movie_atom_list = moov_atom.getField('movie')
            except hachoir_core.field.field.MissingField:
                print '  ERROR! Failed to parse video file - missing "movie" atom-list; skipping ... '
                mov_parser.stream._input.close()
                continue

            mvhd_atom = next((field for field in movie_atom_list if field.description == u'Atom: mvhd'), None)
            if movie_atom_list is None:
                print '  ERROR! Failed to parse video file - missing "mvhd" atom; skipping ... '
                mov_parser.stream._input.close()
                continue

            movie_hdr = None
            try:
                movie_hdr = mvhd_atom.getField('movie_hdr')
            except hachoir_core.field.field.MissingField:
                print '  ERROR! Failed to parse video file - missing "movie_hdr"; skipping ... '
                mov_parser.stream._input.close()
                continue

            ## WARNING: it does not work without this dummy iteration
            for field in movie_hdr:
                pass

            creation_date_atom = None
            try:
                creation_date_atom = movie_hdr.getField('creation_date')
            except hachoir_core.field.field.MissingField:
                print '  ERROR! Failed to parse video file - missing "creation_date" atom; skipping ... '
                mov_parser.stream._input.close()
                continue

            # >>> creation_date = mov_parser.getField('/atom[1]/movie/atom[0]/movie_hdr/creation_date')
            # >>> creation_date.getFieldType()
            # 'TimestampUnix32'
            # >>> repr(creation_date)
            # "<TimestampUnix32 path='/atom[1]/movie/atom[0]/movie_hdr/creation_date', address=32, size=32>"
            # >>> str(creation_date)
            # '2017-03-03 14:36:52'

            date_time_str = str(creation_date_atom).replace('-', '').replace(' ', '_').replace(':', '')

            mov_parser.stream._input.close()
        else:
            print '  INFO: Unsupported file type (neither JPEG image nor MOV/MP4 video); skipping ... '
            continue


        # print '  DEBUG: date_time_str [%s] ' % (date_time_str,)
        if date_time_str is None:
            print '  ERROR! Failed to determine original/creation date-time for image or video; skipping ... '
            continue

        ## verify pattern of the date-time string
        if date_time_verify_re.match(date_time_str) is None:
            print '  ERROR! Invalid/unexpected format of date-time string for image or video [%s]; skipping ... ' % (date_time_str,)
            continue


        ## TODO: consider whether this program should not actually start with this... ;-)
        ## verify current file-name containts either the same or any other date-time string
        date_time_search = date_time_search_re.match(file_name)
        if date_time_search is not None:
            # print '  DEBUG: date_time_search.groups()=%s, .pos=%d, .string=%s' % (date_time_search.groups(), date_time_search.pos, date_time_search.string)
            current_date_time_prefix = date_time_search.groups()[0]
            current_date_time_str = date_time_search.groups()[1]
            if current_date_time_prefix == '':
                if current_date_time_str == date_time_str:
                    print '  WARNING: File name [%s] already starts with original/creation date-time string [%s];' % (file_name, current_date_time_str),
                else:
                    print '  WARNING: File name [%s] apparently starts with some other date-time string [%s];' % (file_name, current_date_time_str),
            else:
                if current_date_time_str == date_time_str:
                    print '  WARNING: File name [%s] already contains original/creation date-time string [%s];' % (file_name, current_date_time_str),
                else:
                    print '  WARNING: File name [%s] apparently contains some other date-time string [%s];' % (file_name, current_date_time_str),

            if options.force is True:
                print 'forcing rename ... '
            else:
                print 'skipping ... '
                continue


        new_file_name = ''
        if options.erase is True:
            new_file_name = date_time_str + file_name.ext
        elif file_name.startswith(date_time_str):
            new_file_name = file_name
        else:
            new_file_name = date_time_str + '_' + file_name

        if new_file_name == file_name:
            print '  INFO: Keeping original file name [%s]; skipping ... ' % (file_name)
            continue
        else:
            print '  INFO: Renaming file [%s] to [%s] ... ' % (file_name, new_file_name)

        new_file_path = dir_path.joinpath(new_file_name)
        # print 'new_file_path=%s' % (new_file_path,)
        if new_file_path.exists():
            print '  ERROR! New path [%s] already exists; skipping ... ' % (new_file_path,)
            ## TODO: compare hashes, erase duplicate?
            if file_path.read_hexhash('sha1') == new_file_path.read_hexhash('sha1'):
                print '  WARNING! New path and original path seems to be identical files; consider removing duplicate'
            continue

        if options.dry_run is True:
            print '  WARNING: Dry-run; skipping ... '
            continue

        # try:
        file_path.rename(new_file_path)
        # except

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


# > python main.py -p ./sample_imgs -d
# ./sample_imgs\20161029_202116.mp4
#   DEBUG: date_time_str [20161029_182754]
#   INFO: renaming [20161029_202116.mp4] to [20161029_182754_20161029_202116.mp4]; dry-run skipping ...
# ./sample_imgs\20170112_203419_DSC_0118.JPG
#   DEBUG: date_time_str [20170112_203419]
#   INFO: File name [20170112_203419_DSC_0118.JPG] already contains date-time string [20170112_203419]; skipping ...
# ./sample_imgs\20170112_203421_DSC_0119.JPG
#   DEBUG: date_time_str [20170112_203421]
#   INFO: File name [20170112_203421_DSC_0119.JPG] already contains date-time string [20170112_203421]; skipping ...
# ./sample_imgs\MOV_1085.mp4
#   DEBUG: date_time_str [20170303_143652]
#   INFO: renaming [MOV_1085.mp4] to [20170303_143652_MOV_1085.mp4]; dry-run skipping ...

# > python main.py -f -d -e -p "C:\Users\Uparcin\Pictures\2017-01 biegówki Zbychowo"
# C:\Users\Uparcin\Pictures\2017-01 biegówki Zbychowo\20170106_143856_IMG_20170106_143855.jpg
#   INFO: File name [20170106_143856_IMG_20170106_143855.jpg] already contains date-time string [20170106_143856]; forcing rename ...
#   INFO: erasing original file name ...
#   INFO: renaming [20170106_143856_IMG_20170106_143855.jpg] to [20170106_143856.jpg]; dry-run skipping ...
# C:\Users\Uparcin\Pictures\2017-01 biegówki Zbychowo\20170106_145231_IMG_20170107_194711.jpg
#   INFO: File name [20170106_145231_IMG_20170107_194711.jpg] already contains date-time string [20170106_145231]; forcing rename ...
#   INFO: erasing original file name ...
#   INFO: renaming [20170106_145231_IMG_20170107_194711.jpg] to [20170106_145231.jpg]; dry-run skipping ...
# C:\Users\Uparcin\Pictures\2017-01 biegówki Zbychowo\20170106_145238_IMG_20170106_145237.jpg
#   INFO: File name [20170106_145238_IMG_20170106_145237.jpg] already contains date-time string [20170106_145238]; forcing rename ...
#   INFO: erasing original file name ...
#   INFO: renaming [20170106_145238_IMG_20170106_145237.jpg] to [20170106_145238.jpg]; dry-run skipping ...
# C:\Users\Uparcin\Pictures\2017-01 biegówki Zbychowo\20170106_145240_IMG_20170106_145239.jpg
#   INFO: File name [20170106_145240_IMG_20170106_145239.jpg] already contains date-time string [20170106_145240]; forcing rename ...
#   INFO: erasing original file name ...
#   INFO: renaming [20170106_145240_IMG_20170106_145239.jpg] to [20170106_145240.jpg]; dry-run skipping ...
# C:\Users\Uparcin\Pictures\2017-01 biegówki Zbychowo\20170106_150214_IMG_20170106_150213.jpg
#   INFO: File name [20170106_150214_IMG_20170106_150213.jpg] already contains date-time string [20170106_150214]; forcing rename ...
#   INFO: erasing original file name ...
#   INFO: renaming [20170106_150214_IMG_20170106_150213.jpg] to [20170106_150214.jpg]; dry-run skipping ...
# C:\Users\Uparcin\Pictures\2017-01 biegówki Zbychowo\Thumbs.db
#   INFO: file [Thumbs.db] is apparently not a JPEG image; skipping ...


# Moorcin@komp-w-pieli /cygdrive/c/Proj-katalog-zdjec
# $ python main.py
# cpath= E:\Zdjecia
# cpath.realpath()= E:\Zdjecia
# cpath.files()= [Path(u'E:\\Zdjecia\\1185355_10151877957408698_515139299_n.jpg'), Path(u'E:\\Zdjecia\\1900px.rar'), Path(u'E:\\Zdjecia\\20150406_153617.jpg'), Path(u'E:\\Zdjecia\\20150409_145145.jpg'), Path(u'E:\\Zdjecia\\20150419_155344.jpg'), Path(u'E:\\Zdjecia\\25382_408532353697_1203635_n.jpg'), Path(u'E:\\Zdjecia\\Allegro 010.JPG'), Path(u'E:\\Zdjecia\\Allegro 011.JPG'), Path(u'E:\\Zdjecia\\DSCN4047.JPG'), Path(u'E:\\Zdjecia\\DSCN4209.JPG'), Path(u'E:\\Zdjecia\\DSCN4319.JPG'), Path(u'E:\\Zdjecia\\IMG_1565.JPG'), Path(u'E:\\Zdjecia\\IMG_1721.JPG'), Path(u'E:\\Zdjecia\\IMG_5707__.jpg'), Path(u'E:\\Zdjecia\\IMG_5723__.jpg'), Path(u'E:\\Zdjecia\\IMG_5736__.jpg'), Path(u'E:\\Zdjecia\\IMG_5795__.jpg'), Path(u'E:\\Zdjecia\\IMG_9868.JPG'), Path(u'E:\\Zdjecia\\urodziny13.JPG'), Path(u'E:\\Zdjecia\\urodziny16.JPG')]
# E:\Zdjecia\1185355_10151877957408698_515139299_n.jpg image/jpeg jpeg f0403a99c306d382749a5058118822db
# E:\Zdjecia\1900px.rar None None  not an JPEG image(?)
# E:\Zdjecia\20150406_153617.jpg image/jpeg jpeg 83dd04f992a503e389f4828a17c36cf3
# E:\Zdjecia\20150409_145145.jpg image/jpeg jpeg 1c9be903315fa39bfc67d906322d7194
# E:\Zdjecia\20150419_155344.jpg image/jpeg jpeg a497950942718a972e445bf30ecc94ae
# E:\Zdjecia\25382_408532353697_1203635_n.jpg image/jpeg jpeg 21f5e3cf5c5368cf4a1dcec0edea2f3b
# E:\Zdjecia\Allegro 010.JPG image/jpeg jpeg b79e2e0a78e371ecee5ced6caa97e3cb
# E:\Zdjecia\Allegro 011.JPG image/jpeg jpeg 0778d2a9965736fa53dea4fded4fd522
# E:\Zdjecia\DSCN4047.JPG image/jpeg jpeg 60087fe4b4f186174c089c4f83c9b653
# E:\Zdjecia\DSCN4209.JPG image/jpeg jpeg e73044780772e86fa3bf035a5277f887
# E:\Zdjecia\DSCN4319.JPG image/jpeg jpeg c04fd55a3d7503a28a3f3d76dec0239b
# E:\Zdjecia\IMG_1565.JPG image/jpeg jpeg d008dbf5aae8891b9f80c2bdf47dd99c
# E:\Zdjecia\IMG_1721.JPG image/jpeg jpeg baf2766f93fb25abda0142157e3d8366
# E:\Zdjecia\IMG_5707__.jpg image/jpeg None 9706d2e337e90d0377c7916fdd4d687f
# E:\Zdjecia\IMG_5723__.jpg image/jpeg None a7de59bf3de5b57aa63ccfe38d6aa4f9
# E:\Zdjecia\IMG_5736__.jpg image/jpeg None e76290fd9282291cb05b6d936a29f4b0
# E:\Zdjecia\IMG_5795__.jpg image/jpeg None 5bcd0bc3e5614ae04c15a4ba3dc70a24
# E:\Zdjecia\IMG_9868.JPG image/jpeg jpeg a03a9529a254db9b37f7aa1e74faa672
# E:\Zdjecia\urodziny13.JPG image/jpeg jpeg 1b476b5ab8723c814dea3e77ef42b2e6
# E:\Zdjecia\urodziny16.JPG image/jpeg jpeg 733f4323dda0d391a598304d3cf7e73c
