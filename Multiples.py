#!/usr/bin/env python3
# encoding: utf-8
"""
Multiples.py: Shows the first multiples of few given numbers

Created by Ramón Barrios Láscar on 2021-10-22.
Copyright (c) 2021 Ínodo S.A.S. All rights reserved.
"""

import sys, os
from optparse import OptionParser, SUPPRESS_HELP

# START OF MAIN FILE
try:
  parser = OptionParser(usage="%prog [ --OPTIONS ] NUM1 ... ")
  parser.add_option("-s", "--start", dest="start", type="int", action="store", help="Start the multiples at", default=2)
  parser.add_option("-e", "--end", dest="end", type="int", action="store", help="End the multiples at", default=16)
  parser.add_option("-z","--step", dest="step", type="int", action="store", help="Step into", default=1)
  
  (Options,Args) = parser.parse_args()
  
  if len(Args)>0 :
    if Options.end < Options.start:
      Options.end+=Options.start
    for j in range(Options.start, Options.end+1, Options.step):
      if j==Options.start:
        sys.stdout.write("%3s\t"%("N"))
        for OneArg in Args:
          sys.stdout.write("%5d%s"%(int(OneArg),"\n" if (OneArg==Args[len(Args)-1]) else "\t"))
        sys.stdout.write("%3s\t"%("---"))
        for OneArg in Args:
          sys.stdout.write("%5s%s"%("-----","\n" if (OneArg==Args[len(Args)-1]) else "\t"))
      sys.stdout.write("%3d\t"%(j))
      for OneArg in Args:
        sys.stdout.write("%5d%s"%(int(OneArg)*j,"\n" if (OneArg==Args[len(Args)-1]) else "\t"))
  else:
    sys.stderr.write("Multiples: too few arguments!\n")
    sys.exit(1)
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled!\n" % (Options.PrgName))
  sys.stderr.flush()
  