#!/usr/bin/python
# encoding: utf-8
"""
ExifComment.py

Created by Ramón Barrios Lascar on 2008-02-21.
Copyright (c) 2008 iKnow. All rights reserved.
"""

import EXIFpro
from optparse import OptionParser

def ProcessOne ( filename ):
    openfile = open( filename, "rb" )
    tags = EXIFpro.process_file( openfile )
    #  close( openfile )
    return tags

parser = OptionParser()
parser.add_option( "-n", "--show-name", dest="ShowName", action="store_true", default=False, help="Show filenames" )
(options, args ) = parser.parse_args()

for OneFile in args:
    TagList = ProcessOne( OneFile )
    for OneTag in TagList.keys():
        if OneTag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            if options.ShowName:
                print "%s : %s : %s" % ( OneFile, OneTag, TagList[OneTag] )
            else:
                print "%s : %s" % (OneTag, TagList[OneTag])
