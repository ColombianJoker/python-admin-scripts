#!/usr/bin/env python
# encoding: utf-8
"""
isopen: script to test WaitNetService
"""

from WaitNetService import wait_net_service as WaitNetService

import sys, os, inspect, time, string, socket, subprocess
from optparse import OptionParser, SUPPRESS_HELP

def DebugFn(Opts):
  if Opts.DEBUG:
    sys.stderr.write(" • %s()\n"%(inspect.stack()[1][3]),)

# ------------------------------------------------------------------------------------------------------
# Start of main()
ScriptFile=os.path.realpath(__file__)
PrgName=os.path.basename(os.path.splitext(ScriptFile)[0])
KillFile=ScriptFile+".kill"

if os.name!="nt" and sys.platform!="darwin":
  sys.stderr.write("%s: This program only runs on Windows systems!\n"%(PrgName,))
  sys.exit(1)

try:
  parser=OptionParser(usage="%prog [ -q ] [ SERVER ] [ PORT ] [ TIMEOUT ]\n  SERVER  defaults to 127.0.0.1,\n  PORT   defaults to 22, and\n  TIMEOUT defaults to 10 (seconds).")
  parser.add_option("-q", dest="Verbose", action="store_false", default=True, help="Quiet mode. Don't show messages, returns code 0 on open")
  (Options,Args)=parser.parse_args()
  Options.PrgName=PrgName
  Options.Hostname=socket.gethostname()
  Options.KillFile=KillFile
  
  if Options.Verbose:
    sys.stderr.write("%s\n"%(Args,))
  if len(Args)>0:
    Server=Args[0]
  else:
    Server="127.0.0.1"
  if len(Args)>1:
    Port=int(Args[1])
  else:
    Port=22
  if len(Args)>2:
    Timeout=int(Args[2])
  else:
    Timeout=10
  if Options.Verbose:
    sys.stderr.write("Server:%s Port:%d Timeout:%s\n"%(Server,Port,Timeout,))
  if WaitNetService(Server,Port,Timeout):
    if Options.Verbose:
      sys.stdout.write("%s: service on %s:%d is up.\n"%(PrgName,Server,Port,))
    sys.exit(0)
  else:
    if Options.Verbose:
      sys.stdout.write("%s: service on %s:%d doesn't look up!\n"%(PrgName,Server,Port,))
    sys.exit(1)
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n" % (Options.PrgName,))
  sys.stderr.flush()
except IOError:
  sys.stderr.write("\n%s: IO Error!\n" % (Options.PrgName,))
  sys.stderr.flush()
except SyntaxError:
  sys.stderr.write("\n%s: Syntax error compiling/running!\n" % (Options.PrgName,))
  sys.stderr.flush()
except SystemExit as (e):
  sys.stderr.write("%s: exit.\n" % (PrgName,))
  sys.exit(e)
  