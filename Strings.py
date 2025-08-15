#!/usr/bin/env python3
# encoding: utf-8
"""
Strings.py: strings python implementation

Created by Ramón Barrios Lascar on 2017-09-10.
Copyright (c) 2017 Ínodo S.A.S. All rights reserved.
"""
from mmap import mmap, PROT_READ
from optparse import OptionParser, SUPPRESS_HELP
import re
import sys

def strings(fname, n=6):
    with open(fname, 'rb') as f, mmap(f.fileno(), 0, prot=PROT_READ) as m:
        for match in re.finditer(('([\w/]{%s}[\w/]*)' % n).encode(), m):
            yield match.group(0)

# START OF MAIN FILE
if __name__ == '__main__':
  try:
    parser=OptionParser(usage="%prog [ --OPTIONS ] FILE ...")
    parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
    parser.add_option( "-n", "--chars", dest="Min", action="store", help="Minimum number of chars", default=4)
    (Options,Args)=parser.parse_args()
    PrgName="Strings"
    Min=Options.Min
  
    for OneFile in Args:
      if len(Args)>1:
        sys.stderr.write("%s: %s\n"%(PrgName,OneFile))
      for Word in strings(OneFile,Min):
        sys.stdout.write("%s\n"%(Word,))
        sys.stdout.flush()
  except KeyboardInterrupt:
    sys.stderr.write("\n%s: Process cancelled!\n"%(PrgName,))
    sys.stderr.flush()
  