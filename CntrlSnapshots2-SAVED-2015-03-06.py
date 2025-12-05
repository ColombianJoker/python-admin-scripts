#!/usr/bin/env python
# encoding: utf-8
"""
CntrlSnapshots.py: Control SVC/Storwize volume (mdisk) snapshots in consistency groups
Created by Ramón Barrios Láscar on 2015/02/17
Last mod by Ramón Barrios Láscar on 2014/03/26
Copyright (c) 2015 Ínodo. All rights reserved
"""

import sys, os, inspect, subprocess, time, random, re, logging, logging.handlers
from optparse import OptionParser, SUPPRESS_HELP

def DebugFn():
  if Opts.DEBUG:
    Opts.Log.debug(" • %s\n"%(inspect.stack()[1][3]),)

def SetLogging():
  if Opts.DoLog:
    Opts.Log=logging.getLogger('INODO')
    if Opts.DEBUG:
      Opts.Log.setLevel(logging.DEBUG)
    elif Opts.Verbose:
      Opts.Log.setLevel(logging.INFO)
    else:
      Opts.Log.setLevel(logging.WARNING)
    LogHandler=logging.handlers.TimedRotatingFileHandler(Opts.LogFile,'Midnight',1,backupCount=30)
    ScreenHandler=logging.StreamHandler()
    LogFormatter=logging.Formatter('%(asctime)s %(levelname)s %(message)s',datefmt='%Y/%m/%d %H:%M:%S')
    ScreenFormatter=logging.Formatter('%(levelname)s %(message)s')
    LogHandler.setFormatter(LogFormatter)
    ScreenHandler.setFormatter(ScreenFormatter)
    Opts.Log.addHandler(LogHandler)
    Opts.Log.addHandler(ScreenHandler)
    return Opts.Log

def UNIXconnect(UserName, ServerName, CommandString):
  DebugFn()
  FnName=inspect.stack()[1][2]
  CxUserServer="%s@%s" % (UserName,ServerName)
  CxCommand=[Opts.RemoteUnixCommand, CxUserServer, CommandString]
  Opts.Log.debug(" •• %s=%s\n" % ("CxCommand", CxCommand))
  try:
    CxLines=""
    CxLines = subprocess.check_output(CxCommand,shell=False)
    CxLines = CxLines.decode('utf-8')
    Opts.Log.debug(" ••• %s ------------------------\n" % (FnName,))
    Opts.Log.debug(str(CxLines))
    Opts.Log.debug(" ••• %s ------------------------\n" % (FnName,))
  except subprocess.CalledProcessError as e:
    if Opts.Raise and e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  except:
    Opts.Log.error("\n%s() could not connect!\n%s=[%s]\n" % (FnName, "CxCommand", CxCommand))
    if not Opts.DEBUG:
      Opts.ExitCode=8
      sys.exit(Opts.ExitCode) # Exit code 8 now defined as ERROR in SSH CONNECTION
  return CxLines

def WaitSeconds():
  if Opts.DEBUG and Opts.NoWaitOnDebug:
    Opts.Log.info("• WaitSeconds(NoWaitOnDebug)")
  else:
    Opts.Log.info(".")
    time.sleep(Opts.SmallWait)
  return

def MiniWait():
  if not Opts.DEBUG:
    time.sleep(Opts.MiniWait)
  return

def GetVolumeSize(VolumeName):
  """Return the size of VolumeName or 0 (zero)"""
  DebugFn()
  Opts.Log.info("trying to get size of %s..."%(VolumeName,) )
  ReturnedSize=0
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="lsvdisk -bytes -delim : %s"%(VolumeName,)
      OutputText=UNIXconnect(Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        # Filter lines
        for TextLine in OutputText.splitlines():
          if TextLine.startswith("capacity"):
            CapacityLine=TextLine
            break # of for
        CapacityInBytes=CapacityLine.split(":")[1]
        ReturnedSize=int(CapacityInBytes)
        Opts.Log.info("found size (%dB) for \"%s\""%(ReturnedSize,VolumeName))
    finally:
      return ReturnedSize
  else:
    return ReturnedSize # 0

def GetTimedSuffix():
  """Return a timed suffix like _20140208_183716 for 2014/feb/08 6:37:16PM"""
  DebugFn()
  TimeStr="_%04d%02d%02d_%02d%02d%02d" % (time.localtime(time.time())[0:6])
  return TimeStr

def CreateNowNamedVolume(VolumeName):
  """Create a now named volume based on VolumeName, and return the name"""
  DebugFn()
  Opts.Log.info("trying to create new volume to snap \"%s\"..."%(VolumeName,))
  NewVolumeName="" #WTF?
  if Opts.Storage1Type=="storwize":
    try:
      TimeSuffix=GetTimedSuffix()
      NowVolumeName="%s%s"%(VolumeName,TimeSuffix)
      NewSnapSize=GetVolumeSize(VolumeName)
      CxCommand="mkvdisk -mdiskgrp %s -iogrp %d -size %d -unit b -rsize %d%% -warning %d%% -autoexpand -easytier %s -name %s" % (Opts.Pool,Opts.IOgroup,NewSnapSize,Opts.PercentThin,Opts.SnapWarning,Opts.SnapEasy,NowVolumeName)
      OutputText=UNIXconnect(Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        Opts.Log.info("volume \"%s\" created" % (NowVolumeName,))
        return NowVolumeName
      else:
        Opts.Log.info("could not create volume \"%s\"!" % (NowVolumeName,))
        return COULD_NOT_CREATE
    except:
      Opts.Log.warning("could not create volume \"%s\"!" % (NowVolumeName,))
      return COULD_NOT_CREATE
  else:
    return COULD_NOT_CREATE

def CreateNowNamedCG():
  """Create a now named consistency group based on ConsistencyGroupPrefix, and return the name"""
  DebugFn()
  Opts.Log.info("trying to create new consistency group to snap \"%s\"..."%(Opts.ConsistencyGroupPrefix,))
  if Opts.Storage1Type=="storwize":
    try:
      TimeSuffix=GetTimedSuffix()
      NowCGName="%s%s" % (Opts.ConsistencyGroupPrefix,TimeSuffix)
      CxCommand="mkfcconsistgrp -name %s -autodelete"%(NowCGName,)
      OutputText=UNIXconnect(Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        Opts.Log.info("consistency group \"%s\" created" % (NowCGName,))
        return NowCGName
      else:
        Opts.Log.info("could not create consistency group \"%s\"!" % (NowCGName,))
        return COULD_NOT_CREATE
    except:
      Opts.Log.warning("could not create consistency group \"%s\"!" % (NowCGName,))
      return COULD_NOT_CREATE
  else:
    return COULD_NOT_CREATE

def GetListOfNamedSnaps(VolumeName):
  """Get the list of volumes (snapshots) with VolumeName like base name"""
  DebugFn()
  Opts.Log.info("trying to get the list of snapshots of \"%s\"..."%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      VolumeList=[]
      CxCommand="lsvdisk -bytes"
      OutputText=UNIXconnect(Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        # Filter lines
        for TextLine in OutputText.splitlines():
          SecondWord=TextLine.split()[1]
          if SecondWord.startswith("%s_" % (VolumeName,)):
            # Append to result list
            # Msg(Opts,"%s volume found" % (SecondWord,))
            VolumeList.append(SecondWord)
        Opts.Log.debug("done listing snapshots for \"%s\""%(VolumeName,))
        Opts.Log.debug("snapshots of \"%s\": %s"%(VolumeName,str(VolumeList),))
        return VolumeList
      else:
        return []
    except:
      return []
  else:
    return []

def CountNamedSnaps(VolumeName):
  """Count how many snapshots a VolumeName has"""
  DebugFn()
  Opts.Log.debug("trying to count snapshots for volume \"%s\""%(VolumeName,))
  if Opts.DEBUG:
    Opts.Log.debug("%d snapshots found for %s"%(len(GetListOfNamedSnaps(VolumeName)),VolumeName))
  return len(GetListOfNamedSnaps(VolumeName))

def GetNameOfFirstNamedSnap(VolumeName):
  """Get name of first volume (snapshot) with VolumeName like base name"""
  DebugFn()
  Opts.Log.debug("trying to get first snapshot for \"%s\""%(VolumeName,))
  if Opts.DEBUG:
    Opts.Log.debug("first snapshot of \"%s\" is \"%s\""%(VolumeName,sorted(GetListOfNamedSnaps(VolumeName))[0]))
  return sorted(GetListOfNamedSnaps(VolumeName))[0]

def RemoveVolume(VolumeName):
  """Remove named volume from storage"""
  DebugFn()
  Opts.Log.info("trying to force remove volume %s"%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="rmvdisk -force %s" % (VolumeName,)
      OutputText=UNIXconnect(Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Opts.Log.info("volume \"%s\" removed." % (VolumeName))
    except:
      Opts.Log.error("volume \"%s\" could not be removed.\n"%(VolumeName,))
  else:
    Opts.Log.error("volume \"%s\" could not be removed.\n"%(VolumeName,))
  return

def SnapVolumeToVolume(SourceVolume,TargetVolume,ConsistencyGroupName):
  """Create snapshot mapping between source volume and target volume, synched using a consistency group"""
  DebugFn()
  Opts.Log.info("trying to snap \"%s\" into \"%s\""%(SourceVolume,TargetVolume))
  if Opts.Storage1Type=="storwize":
    try:
      MatchOb = re.match( '%s_([0-9]{8}_[0-9]{6})'%(SourceVolume), TargetVolume)
      if MatchOb:
        TimeSuffix=MatchOb.group(1)
      else:
        TimeSuffix="__NOTSEQ__%d" % (random.randint(1000,10000),)
      SnapshotNow="%s%s%s" % (SourceVolume,"_snapshot_",TimeSuffix)
      CxCommand="mkfcmap -source %s -target %s -name %s -copyrate %d -consistgrp %s -autodelete" % (SourceVolume,TargetVolume,SnapshotNow,Opts.SnapSpace,ConsistencyGroupName)
      OutputText=UNIXconnect(Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Opts.Log.info("snapshot of volume \"%s\" created into \"%s\" (pair named \"%s\")" % (SourceVolume,TargetVolume,SnapshotNow))
    except:
      Opts.Log.error("snapshot of volume \"%s\" could not created into \"%s\"!\n" % (SourceVolume,TargetVolume))
  return

def StartSyncSnaps(ConsistencyGroupName):
  """Start all flashcopies by starting the whole consistency group"""
  DebugFn
  Opts.Log.info("trying to start consistency group \"%s\""%(ConsistencyGroupName,))
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="startfcconsistgrp -prep -restore %s" % (ConsistencyGroupName,)
      OutputText=UNIXconnect(Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Opts.Log.info("snapshots of consistency group \"%s\" started"%(ConsistencyGroupName,))
    except:
      Opts.Log.error("snapshots of consistency group \"%s\" failed"%(ConsistencyGroupName,))
  return

def ExitIfKillFile():
  """Terminates script if kill file is found"""
  Opts.Log.debug(" • %s"%(inspect.stack()[1][2],))
  if os.path.exists(Opts.KillFile):
    # Exit now
    try:
      os.unlink(Opts.KillFile)
      Opts.Log.info("%s: kill file found and removed, exiting...\n" % (Opts.PrgName,))
    except IOError:
      Opts.Log.info("%s: error trying to remove killfile (%s)"%(Opts.PrgName,Opts.KillFile,))
    sys.exit(5)
  return

def TryOneScript(CommandString):
  DebugFn()
  FnName=inspect.stack()[1][2]
  CxCommand=[CommandString]
  Opts.Log.debug(" •• %s=%s\n" % ("CommandString", CommandString))
  try:
    CmLines=""
    CmLines = subprocess.check_output(CommandString,shell=False)
    CmLines = CmLines.decode('utf-8')
    Opts.Log.debug(" ••• %s ------------------------\n" % (FnName,))
    Opts.Log.debug(str(CmLines))
    Opts.Log.debug(" ••• %s ------------------------\n" % (FnName,))
  except subprocess.CalledProcessError as e:
    if Opts.Raise and e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  except:
    Opts.Log.error("\n%s() could not connect!\n%s=[%s]\n" % (FnName, "CommandString", CommandString))
    if not Opts.DEBUG:
      Opts.ExitCode=8
      sys.exit(Opts.ExitCode) # Exit code 8 now defined as ERROR in SSH CONNECTION
  return CmLines

def ExecuteScript(Pre,Mandatory):
  """Executes snapshot world preparing scripts"""
  """
              Pre==True && Mandatory==True -> PreScript
              Pre==True && Mandatory==False -> PreScript2
              Pre==False && Mandatory==True -> PosScript
              Pre==False && Mandatory==False -> PosScript
  """
  if Pre and Mandatory:
    Opts.Log.debug("PreScript")
    if Opts.PreScript=="/usr/bin/true" or Opts.PreScript=="CMD":
      Opts.Log.debug("skipped NOOP command")
      return True
    else:
      TryOneScript(Opts.PreScript)
  elif Pre and not Mandatory:
    Opts.Log.debug("PreScript2")
    if Opts.PreScript2=="/usr/bin/true" or Opts.PreScript2=="CMD":
      Opts.Log.debug("skipped NOOP command")
    else:
      TryOneScript(Opts.PreScript2)
  elif not Pre and Mandatory:
    Opts.Log.debug("PosScript")
    if Opts.PosScript=="/usr/bin/true" or Opts.PosScript=="CMD":
      Opts.Log.debug("skipped NOOP command")
    else:
      TryOneScript(Opts.PosScript)
  else:
    Opts.Log.debug("PosScript2")
    if Opts.PosScript2=="/usr/bin/true" or Opts.PosScript2=="CMD":
      Opts.Log.debug("skipped NOOP command")
    else:
      TryOneScript(Opts.PosScript2)
  return

def WaitNextIteration():
  """Wait for next iteration"""
  # This function waits ONE HOUR if RunOClock==FALSE
  # This function waits for HOUR OCLOCK if RunOClock==TRUE
  DebugFn()
  StartingMinute=Opts.StartingSecond//60
  FullWait=Opts.FullWait//60
  Opts.Log.debug("waiting for next iteration, now is %s seq minutes"%(StartingMinute,))
  while True:
    # Run forever until break
    ExitIfKillFile()
    WaitSeconds()
    if Opts.DEBUG:
      # Only waits ONE MINUTE on DEBUG
      break
    if Opts.RunOClock:
      # Run on o'clock hours only
      if (time.localtime(time.time())[4])==Opts.OClock:
        break # of while
    else:
      NowMinutes=(int(time.time())//60)
      if ((NowMinutes-StartingMinute)%FullWait)==0:
        break # of while
  return

def CreateKillFile(FileName):
  open(FileName, "w").close()
  sys.exit(0)

# ------------------------------------------------------------------------------------------------------
# Start of main()
ScriptFile=os.path.realpath(__file__)
PrgName=os.path.basename(os.path.splitext(ScriptFile)[0])
KillFile=ScriptFile+".kill"
COULD_NOT_CREATE=-1
COULD_NOT_REMOVE=-2

try:
  parser=OptionParser(usage="%prog [ --OPTIONS ]")
  parser.add_option("-q", dest="Verbose", action="store_false", default=True, help="Quiet mode. Don't show messages")
  parser.add_option("-o", "--output", dest="LogFile", action="store", type="string", help="Log execution into file name", default="%s.log" % (PrgName,))
  parser.add_option("-D", "--max-log-days", dest="MaxLogDays", action="store", type="int", help="Max log duration in days", default=1)
  parser.add_option("--no-log", dest="DoLog", action="store_false", help="No log to a file", default=True)
  parser.add_option("-d", "--workdir", dest="WorkDir", action="store", type="string", help="Working directory", default="/opt/snapshots")
  parser.add_option("-r", "--ur", "--remote-unix-command", dest="RemoteUnixCommand", action="store", type="string", help="Remote execution command for Unix connections", default="ssh")
  parser.add_option("--t1n", "--storage1name", dest="Storage1Name", action="store", type="string", help="Storage server #1 hostname", default="V7000")
  parser.add_option("--t1u", "--storage1user", dest="Storage1User", action="store", type="string", help="Storage server #1 username to connect to", default="soporte")
  parser.add_option("--t1t", "--storage1type", dest="Storage1Type", action="store", type="string", help="Storage server #1 type of OS", default="storwize")
  parser.add_option("--cg", "--consistency-group", dest="ConsistencyGroupPrefix", action="store", type="string", help="Consistency group name prefix", default="SAP_Replica_")
  parser.add_option("--ps", "--pre-script", dest="PreScript", action="store", type="string", help="Pre- script to execute to", default="/usr/bin/true")
  parser.add_option("--ps2", "--pre-script2", dest="PreScript2", action="store", type="string", help=SUPPRESS_HELP, default="/usr/bin/true")
  parser.add_option("--Ps", "--post-script", dest="PosScript", action="store", type="string", help="Post- script to execute to", default="/usr/bin/true")
  parser.add_option("--Ps2", "--post-script2", dest="PosScript2", action="store", type="string", help=SUPPRESS_HELP, default="/usr/bin/true")
  parser.add_option("--sb","--script-before-cloning", dest="ScriptBeforeCloning", action="store_true", help="Run script before cloning", default=False)
  parser.add_option("-n", "--snapshots", dest="Snapshots", action="store", type="int", help="How many snapshots to maintain", default=6)
  parser.add_option("-p", "--percent-thin", dest="PercentThin", action="store", type="int", help="How thin make snapshots, percent integer", default=5)
  parser.add_option("-P", "--storage-pool", dest="Pool", action="store", type="string", help="Storage pool name", default="Eliot_2013_Pool1")
  parser.add_option("-c", "--clock-minute", dest="OClock", action="store", type="int", help="Minutes to replicate on", default=5)
  parser.add_option("-w", "--small-wait", dest="SmallWait", action="store", type="int", help=SUPPRESS_HELP, default=60)
  parser.add_option("-W", "--full-wait", dest="FullWait",action="store", type="int", help="Time between snapshots (seconds)", default=60*60)
  parser.add_option("-C", "--only-clean", "--clean-only", dest="OnlyClean", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("-K", "--kill", dest="Kill", action="store_true", default=False, help="Kill another instance of script")
  parser.add_option("--run-each",dest="RunOClock",action="store_false",default=True,help=SUPPRESS_HELP)
  parser.add_option("--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DEBUGUNIX", dest="DEBUGUNIX", action="store_true", default=False, help=SUPPRESS_HELP)

  (Opts, Args)=parser.parse_args()
  Opts.PrgName=PrgName
  Opts.KillFile=KillFile
  Opts.ExitCode=0
  # Internal variables
  Opts.NoWaitOnDebug=True
  Opts.MiniWait=3
  Opts.Raise=True
  Opts.IOgroup=0
  Opts.SnapWarning=95
  Opts.SnapTier="generic_hdd"
  Opts.SnapEasy="on"
  Opts.SnapSpace=0
  Options=Opts

  if Options.Kill:
    CreateKillFile(KillFile)
  
  Log=SetLogging()

  TimeStr="%04d/%02d/%02d %02d:%02d:%02d" % (time.localtime(time.time())[0:6])
  Opts.StartingSecond=int(time.time())
  Log.info("\n------------------------------------------------------------------------")
  if Opts.OnlyClean:
    Log.info("starting to clean")
  else:
    Log.info("starting out")
  # ----------------------------------------------------------- Only for connectivity tests

  # ----------------------------------------------------------- Only for connectivity tests
  if Opts.DEBUGUNIX:
    Opts.DEBUG=True
    if len(Args)>0:
      for OneName in Args:
        UNIXconnect("root",OneName,"ping %s"%(OneName,))
    else:
      UNIXconnect("root","ESX11CO","ping 192.168.20.1")
    sys.exit(0)
  # ----------------------------------------------------------- Only for connectivity tests
  
  # Change to working directory
  if not Opts.DEBUG:
    os.chdir(Options.WorkDir)
  
  while len(Args)>0:
    # Do forever
    # Create snapshots
    TimeStr="%04d/%02d/%02d %02d:%02d:%02d" % (time.localtime(time.time())[0:6])
    Log.info("waking")
    Opts.TryToSnap=True
    if Opts.ScriptBeforeCloning:
      try:
        ExecuteScript(Pre=True,Mandatory=True)
        ExecuteScript(Pre=True,Mandatory=False)
      except subprocess.CalledProcessError:
        Opts.TryToSnap=False
    if Opts.TryToSnap:
      NewConsistencyGroup=CreateNowNamedCG()
      for OneVolume in Args:
        NewVolumeName=CreateNowNamedVolume(OneVolume)
        SnapVolumeToVolume(OneVolume,NewVolumeName,NewConsistencyGroup)
        while CountNamedSnaps(OneVolume)>Opts.Snapshots:
          # Remove excess of snapshots
          try:
            FirstSnapshot=GetNameOfFirstNamedSnap(OneVolume)
            RemoveVolume(FirstSnapshot)
          except:
            continue # with while
      StartSyncSnaps(NewConsistencyGroup)
    else:
      Log.info("snapshot phase skipped")
    if Opts.TryToSnap:
      try:
        ExecuteScript(Pre=False,Mandatory=True)
        ExecuteScript(Pre=False,Mandatory=False)
      except subprocess.CalledProcessError:
        Opts.TryToSnap=False
    WaitNextIteration()
  else:
    Log.critical("No arguments!")
  #The End
  sys.exit(0)

except KeyboardInterrupt:
  logging.info("%s: Process cancelled (keyboard interrupt)!\n" % (Opts.PrgName,))
  sys.stderr.write("\n%s: Process cancelled (keyboard interrupt)!\n" % (Opts.PrgName,))
  sys.stderr.flush()
except IOError:
  logging.error("%s: IO Error changing directory to %s!\n" % (Opts.PrgName,Opts.WorkDir))
  sys.stderr.write("\n%s: IO Error changing directory to %s!\n" % (Opts.PrgName,Opts.WorkDir))
  sys.stderr.flush()
except SyntaxError:
  logging.error("%s: Syntax error compiling/running!\n" % (Opts.PrgName,))
  sys.stderr.write("\n%s: Syntax error compiling/running!\n" % (Opts.PrgName,))
  sys.stderr.flush()
except SystemExit as e:
  sys.stderr.write("%s: exit.\n" % (PrgName,))
  sys.exit(e)
  
# --------------------------------------------------------------------------------
# ASSERTS:
# PythonWin or ActivePython installed on machine running script
# On Windows servers:
#   Directory /opt/snapshots or option -d WORKINGDIR
# Must be a V7000 host definition on SSH saved, with priv/pub DSA keys defined or
#   a named configuration named with option --t1n STORAGESERVER or with option
#   --storage1name STORAGESERVER
# On Storwize Storage servers:
#   windowspubdsa installed
#   ### This is user PUBLIC DSA KEY  ###
#
# --------------------------------------------------------------------------------
# Ramon Barrios Lascar, 2014, Ínodo S.A.S.
# --------------------------------------------------------------------------------
