#!/usr/bin/env python
# encoding: utf-8
"""
Common.py: gets common prefix for given arguments

Created by Ramón Barrios Lascar on 2017-06-02
"""
import sys, os, string
from optparse import OptionParser, SUPPRESS_HELP
  
# START OF MAIN FILE
try:
  parser = OptionParser(usage="%prog [ --OPTIONS ] NAME ... ")

  (Options, Args) = parser.parse_args()
  if len( Args ) > 0 :
    sys.stdout.write("%s\n" %(os.path.commonprefix(Args),))
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName))
  sys.stderr.flush()
