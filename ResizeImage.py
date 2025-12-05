#!/usr/bin/python
# encoding: utf-8
"""
ResizeImage.py

Created by Ramón Barrios Lascar on 2007-02-20.
Copyright (c) 2007 iKnow. All rights reserved.
"""

import sys
import os
import string
import re
import types
from optparse import OptionParser

parser = OptionParser()
parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
parser.add_option( "-W", "--width", dest="Width", action="store", help="Width to resize image", default=1440)
parser.add_option( "-H", "--height", dest="Height", action="store", help="Width to resize image", default=900)
(Options, Args) = parser.parse_args()
Options.PrgName = "ResizeImage"
# Search for mogrify
for CmdPath in ["/opt/local/bin/mogrify","/sw/local/bi/mogrify","/sw/bin/mogrify","/usr/local/bin/mogrify","/usr/bin/mogrify"]:
  if os.path.isfile(CmdPath):
    Options.Mogrify = CmdPath
    # sys.stderr.write("%s: Mogrify is %s\n" % (Options.PrgName,Options.Mogrify))
    break

try:
  if isinstance(Args[0],int) and isinstance(Args[1],int):
    Options.Width = Args[0] * 1
    Options.Height = Args[1] * 1
    Files = Args[2:]
    sys.stderr.write("%d %d %s\n" % (Options.Width,Options.Height,Files))
except:
  sys.stderr.write("%s: First and second arguments must be numbers!\n" % (Options.PrgName,))
  sys.stderr.write("Usage: %s WIDTH HEIGHT FILE ...\n" % (Options.PrgName,))
  sys.exit(2)

MogrifyCommand = Options.Mogrify + " -identify "
for aFile in Files:
  p = os.popen(MogrifyCommand + aFile, "r")
  mLines = p.readlines()
  p.close
  mWords = mLines.split()
  fileRes = mWords[2]
  print fileRes