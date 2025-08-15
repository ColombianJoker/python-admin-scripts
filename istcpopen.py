#!/usr/bin/env python
# encoding: utf-8
"""
istcpopen: script to test TCP port listening
last modified: Ramon Barrios Lascar, 2015/02/27
"""

import sys, os, inspect, time, string, socket, errno, subprocess
from optparse import OptionParser, SUPPRESS_HELP
from time import time as now

def WaitNetService(Server, Port, Timeout=None):
  """ Wait for network service to appear @param timeout: in seconds, if None or 0 wait forever
      @return: True of False, if timeout is None may return only True or throw unhandled network exception
  """

  Sck = socket.socket()
  # time module is needed to calc timeout shared between two exceptions
  EndTime = Timeout and now()+Timeout

  while True:
    try:
      if Timeout:
        NextTimeout = EndTime - now()
        if NextTimeout < 0:
          return False
        else:
          Sck.settimeout(NextTimeout)
      Sck.connect((Server, Port))
    except socket.timeout, err:
      # this exception occurs only if timeout is set
      if Timeout:
        return False
    except socket.error, err:
      # catch timeout exception from underlying network library
      # this one is different from socket.timeout
      if type(err.args) != tuple or err[0] not in (errno.ETIMEDOUT, errno.ECONNREFUSED):
        raise
    else:
      Sck.close()
      return True

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
  
  # if Options.Verbose:
  #   sys.stderr.write("%s\n"%(Args,))
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
    sys.stderr.write("%s: Server=%s Port=TCP/%d Timeout=%ss\n"%(PrgName,Server,Port,Timeout,))
  if WaitNetService(Server,Port,Timeout):
    if Options.Verbose:
      sys.stdout.write("%s: service on %s:%d is up.\n"%(PrgName,Server,Port,))
    sys.exit(0)
  else:
    if Options.Verbose:
      sys.stdout.write("%s: service on %s:%d doesn't answer!\n"%(PrgName,Server,Port,))
    sys.exit(1)
except KeyboardInterrupt:
  sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n" % (Options.PrgName,))
  sys.stderr.flush()
except IOError as (e):
  if Options.Verbose: 
    if e.errno==22:
      sys.stderr.write("%s: service on %s:%d is down.\n"%(PrgName,Server,Port,))
    else:
      sys.stderr.write("\n%s: IO Error (%s)!\n" % (PrgName,dir(e)))
    sys.stderr.flush()
  sys.exit(1)
except SyntaxError:
  sys.stderr.write("\n%s: Syntax error compiling/running!\n" % (Options.PrgName,))
  sys.stderr.flush()
except SystemExit as (e):
  if int(str(0))!=0:
    sys.stderr.write("%s: exit.\n" % (PrgName,))
  sys.exit(e)
  