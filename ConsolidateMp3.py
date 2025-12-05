#!/usr/bin/python
# ConsolidateMp3

import os, sys, id3
from optparse import OptionParser

def GetBasicTags(Opts, OneFile):
  OneSongArtist = Opts.UnknownArtist
  OneSongAlbum = Opts.UnknownAlbum
  OneSongTitle = Opts.UnknownTitle
  try:
      id3info = ID3.ID3(OneFile, as_tuple=1)
      if Opts.DEBUG:
        for k, v in id3info.items():
          if k == "ALBUM":
            OneSongAlbum = v
          if k == "ARTIST":
            OneSongArtist = v
          if k == "TITLE":
            OneSongTitle = v
        sys.stderr.write("%s: %s=%s, %s=%s, %s=%s\n" % (OneFile, "Artist", OneSongArtist, "Album", OneSongAlbum, "Title", OneSongTitle))
  except InvalidTagError, Message:
    print "Invalid ID3 tag in %s: %s" % (OneFile, Message)
  return OneSongArtist, OneSongAlbum, OneSongTitle
  
# Start of main program
parser = OptionParser()
parser.add_option( "-D", "--debug", dest="DEBUG", action="store_true", help="Debug mode", default=False)
parser.add_option( "--unknown-artist", dest="UnknownArtist", action="store", help="Default artist name", default="UnknownArtist")
parser.add_option( "--unknown-album", dest="UnknownAlbum", action="store", help="Default album name", default="UnknownAlbum")
parser.add_option( "--unknown-title", dest="UnknownTitle", action="store", help="Default song name", default="UnknownTitle")

(Options, Args) = parser.parse_args()

# Initialize some basic things
Options

if len(Args) > 0:
  # Process all
  for OneArg in Args:
    if os.path.isfile(OneArg):
      TheArtist, TheAlbum, TheTitle = GetBasicTags(Options, OneArg)
      sys.stdout.write("  %s\\%s\\%s\n" % (TheArtist, TheAlbum, TheTitle))
    if os.path.isdir(OneArg):
      for StartDir, Dirs, Files in os.walk(OneArg):
        for OneFile in Files:
          TheArtist, TheAlbum, TheTitle = GetBasicTags(Options, os.path.join(StartDir,OneFile))
          sys.stdout.write("  %s\\%s\\%s\n" % (TheArtist, TheAlbum, TheTitle))
else:
  sys.stderr.write("ShowTags: too few arguments!\n")
  sys.exit(2)
