#!/usr/bin/python
# encoding: utf-8
"""
ImageAdjuster.py: Convert 4:3 (or other proportion) images to 16:9

Created by Ramón Barrios Lascar on 2007-03-20.
Copyright (c) 2007 iKnow. All rights reserved.
"""

# Adjust Python Module Path
import sys, os, shutil
from optparse import OptionParser
sys.path.append('/opt/local/lib/python2.6/site-packages/PIL')
import Image

parser = OptionParser()
parser.add_option("-D", "--DEBUG", dest="DEBUG", action="store_true", help="DEBUG mode", default=False)
parser.add_option("-x", "--width", dest="width", action="store", type="int", help="Target width", default=1440)
parser.add_option("-y", "--height", dest="height", action="store", type="int", help="Target height", default=900)
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose", default=False)
parser.add_option("-s", "--sufix", dest="ImageSuffix", action="store", help="Adjusted image suffix")
parser.add_option("-e", "--ext", dest="ImageExt", action="store", help="Image extension", default="jpg")
(Opts, Args) = parser.parse_args()
Opts.PrgName = "ImageAdjuster"
if not Opts.ImageSuffix:
  Opts.ImageSuffix = "_" + str(Opts.width) + "x" + str(Opts.height)

Opts.ImageBackground = Image.new( "RGB", (Opts.width,Opts.height), "black" )
if Opts.DEBUG:
  print "Opts.ImageBackground ", Opts.ImageBackground

def ProcessImage( iFile, iImage, Opts ):
  # Adjust image
  if Opts.DEBUG:
    print Opts
    sys.stderr.write( " adjusting ...")
  if Opts.verbose:
    sys.stderr.write(".")
  ( FileFullName, FileExtension ) = os.path.splitext( iFile )
  if Opts.DEBUG:
    print "FileFullName=", FileFullName
    print "FileExtension=", FileExtension
  NewFileName = FileFullName + Opts.ImageSuffix + "." + Opts.ImageExt
  if Opts.DEBUG:
    sys.stderr.write( " new is %s ..." % (NewFileName,))
  if not os.path.isfile( NewFileName ):
    iw, ih = iImage.size
    iwf = iw * 1.0
    ihf = ih * 1.0
    
    if (iwf/ihf) > (Opts.width/Opts.height):
      newHeight = Opts.height * 1.0
      newWidth = newHeight * ( iwf/ihf )
    else:
      newWidth = Opts.width * 1.0
      newHeight = newWidth / (iwf/ihf)
      
    newWidth = int( newWidth )
    newHeight = int( newHeight )
    
    if Opts.DEBUG:
      sys.stderr.write( " resizing ..." )
    resizedImage = iImage.resize((newWidth, newHeight), Image.ANTIALIAS)
    if Opts.DEBUG:
      sys.stderr.write( " pasting ..." )
    finalImage = Opts.ImageBackground.copy()
    if newWidth < Opts.width:
      finalImage.paste( resizedImage, (0,0))
    else:
      finalImage.paste( resizedImage, (0,(Opts.height-newHeight)/2))
    # Save the produced image
    try:
      if Opts.DEBUG:
        sys.stderr.write( " saving ..." )
      finalImage.save(NewFileName,"JPEG")
      FileDir = os.path.dirname( NewFileName )
      if FileDir == "":
        FileDir = "."
      JoinedPath = os.path.join( FileDir, ".adjusted" )
      if Opts.DEBUG:
        sys.stderr.write( "%s: saved %s ...\n" % (Opts.PrgName, NewFileName ) )
        print "FileDir=", FileDir
        print "JoinedPath=", JoinedPath
      try:
        if not os.path.isdir( JoinedPath ):
          os.mkdir( JoinedPath )
      except:
        sys.stderr.write( "%s: could not create \"%s\" directory!\n" % (Opts.PrgName, JoinedPath))
      try:
        shutil.move(iFile, JoinedPath )
        if Opts.DEBUG:
          sys.stderr.write("%s: moved \"%s\" to directory \"%s\".\n" % (Opts.PrgName,iFile,JoinedPath))
      except:
        sys.stderr.write( "%s: could not move \"%s\" to directory \"%s\"!\n" % (Opts.PrgName, iFile, JoinedPath))
    except:
      sys.stderr.write( "%s: could not save %s!\n" % ( Opts.PrgName, NewFileName))
  else:
    sys.stderr.write( "%s: %s exists!\n" % (Opts.PrgName, NewFileName ) )
  if Opts.DEBUG:
    sys.stderr.write( " ending ..." )

if len( Args ) > 0:
  for ImageFile in Args:
    try:
      if Opts.DEBUG:
        sys.stderr.write( "%s: trying %s ..." % (Opts.PrgName, ImageFile))
      OneImage = Image.open( ImageFile )
      if Opts.DEBUG:
        sys.stderr.write( " done ... getting size ..." )
      (iWidth, iHeight) = OneImage.size
      if Opts.DEBUG:
        sys.stderr.write( " done (%dx%d)... processing ..." % (iWidth, iHeight))
      ImageWidth = iWidth*1.0
      ImageHeight = iHeight*1.0
      if (((ImageWidth/ImageHeight) != 1.6) or (iWidth != Opts.width or iHeight != Opts.height)):
        ProcessImage( ImageFile, OneImage, Opts )
        if Opts.DEBUG:
          sys.stderr.write( " adjusted!\n")
    except:
      sys.stderr.write("%s: Could not open \"%s\"!\n" % (Opts.PrgName, ImageFile) )

  if Opts.verbose:
    sys.stderr.write("\n")
else:
  parser.error("one or more arguments are needed!")
  