#!/usr/bin/env python3
# encoding: utf-8
"""
Process SSH config file
Created : 2017-03-17, Ramón Barrios Láscar, Ínodo SAS
Modified:
"""

import sys, os
from optparse import OptionParser

def LoadHost(F):
  "Load file sections"
  for TextLine in F:
    SSHdic = {}
    SSHlist = []
    for TextLine in F:
      if TextLine == '\n':
        SSHdic.update({SSHlist[0]:SSHlist[1:]})
        SSHlist = []
      else:
        name = TextLine.strip()        
        if ',' in TextLine:
          SSHlist.append(TextLine)
    if SSHlist:
      SSHdic.update({SSHlist[0]:SSHlist[1:]})
  return SSHdic

# ------------------------------------------------------------------------------------------------------
# Start of main()
ScriptFile=os.path.realpath(__file__)
PrgName=os.path.basename(os.path.splitext(ScriptFile)[0])
KillFile=ScriptFile+".kill"
GB=1024*1024*1024

try:
  parser = OptionParser()
  parser.add_option( "-v", "--verbose", dest="Verbose", action="store_true", help="Verbose mode", default=False)
  parser.add_option( "-c", "--config-file", dest="ConfigFile", action="store", help="Config file to load", default="~/.ssh/config")
  (Options, Args) = parser.parse_args()

  Options.ConfigFile=os.path.expanduser(Options.ConfigFile)
  PrgName=PrgName

  if Options.Verbose:
    sys.stdout.write("%s: using «%s» file.\n"%(PrgName,Options.ConfigFile))
  
  MasterDic = LoadHost(Options.ConfigFile)
  print(MasterDic)
  
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n" % (Options.PrgName,))
  sys.stderr.flush()
except IOError:
  sys.stderr.write("\n%s: IO Error changing directory to %s!\n" % (Options.PrgName,Options.WorkDir))
  sys.stderr.flush()
except SyntaxError:
  sys.stderr.write("\n%s: Syntax error compiling/running!\n" % (Options.PrgName,))
  sys.stderr.flush()
except SystemExit as e:
  sys.stderr.write("%s: exit.\n" % (PrgName,))
  sys.exit(e)
  