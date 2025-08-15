#!/usr/bin/python
# ShowTags

import os, sys, ID3
from optparse import OptionParser

def ShowFileTags(OneFile):
  try:
      id3info = ID3.ID3(OneFile, as_tuple=1)
      for k, v in id3info.items():
        print k, ":", v
  except InvalidTagError, Message:
    print "Invalid ID3 tag in %s: %s" % (OneFile, Message)
    
# Start of main program
parser = OptionParser()
(Options, Args) = parser.parse_args()

if len(Args) > 0:
  # Process all
  for OneArg in Args:
    if os.path.isfile(OneArg):
      ShowFileTags(OneArg)
    if os.path.isdir(OneArg):
      for StartDir, Dirs, Files in os.walk(OneArg):
        for OneFile in Files:
          ShowFileTags(os.path.join(StartDir,OneFile))
else:
  sys.stderr.write("ShowTags: too few arguments!\n")
  sys.exit(2)
