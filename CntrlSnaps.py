#!/usr/bin/python
# encoding: utf-8
"""
CntrlSnaps.py: Control SVC/Storwize volume (mdisk) snapshots
Created by Ramón Barrios Láscar on 2014/02/08
Last mod by Ramón Barrios Láscar on 2014/03/10
Copyright (c) 2014 Ínodo. All rights reserved
"""

import sys, os, inspect, subprocess, time, random, re
from optparse import OptionParser, SUPPRESS_HELP

def DebugFn(Opts):
  if Opts.DEBUG:
    sys.stderr.write(" • %s\n"%(inspect.stack()[1][3]),)

def UNIXconnect(Opts, UserName, ServerName, CommandString):
  DebugFn(Opts)
  FnName=inspect.stack()[1][3]
  CxUserServer="%s@%s" % (UserName,ServerName)
  CxCommand=[Opts.RemoteUnixCommand, CxUserServer, CommandString]
  if Opts.DEBUG:
    sys.stderr.write(" •• %s=%s\n" % ("CxCommand", CxCommand))
  try:
    CxLines=""
    CxLines = subprocess.check_output(CxCommand,shell=False)
    CxLines = CxLines.decode('utf-8')
    if Opts.DEBUG:
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.write(str(CxLines))
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.flush()
  except subprocess.CalledProcessError as e:
    if Opts.Raise and e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  except:
    sys.stderr.write("\n%s() could not connect!\n%s=[%s]\n" % (FnName, "CxCommand", CxCommand))
    if not Opts.DEBUG:
      Opts.ExitCode=8
      sys.exit(Opts.ExitCode) # Exit code 8 now defined as ERROR in SSH CONNECTION
  return CxLines

def WINconnect(Opts, ServerName, CommandString):
  DebugFn(Opts)
  FnName=inspect.stack()[1][3]
  CxServer=r"\\%s" % (ServerName,)
  CxCommand="%s %s %s" % (Opts.RemoteWindowsCommand, CxServer, CommandString)
  if Opts.DEBUG:
    sys.stderr.write(" •• %s=[%s]\n" % ("CxCommand", CxCommand))
  try:
    CxLines=""
    CxLines = subprocess.check_output(CxCommand)
    CxLines=CxLines.decode('utf-8')
    if Opts.DEBUG:
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.write(str(CxLines)+'\n')
      sys.stdout.write(" ••• %s ------------------------\n" % (FnName,))
      sys.stdout.flush()
  except subprocess.CalledProcessError as e:
    if e.returncode!=0:
      raise subprocess.CalledProcessError(e.returncode, e.cmd)
  except:
    sys.stderr.write("\n%s() could not connect!\n%s=[%s]\n" % (FnName, "CxCommand", CxCommand))
    if not Opts.DEBUG:
      Opts.ExitCode=9
      sys.exit(Opts.ExitCode) # Exit code 9 now defined as ERROR in PSEXEC CONNECTION
  return CxLines

def FileLog(Opts,Message):
  if not Opts.NoLog:
    TimeStr="%04d/%02d/%02d %02d:%02d:%02d" % (time.localtime(time.time())[0:6])
    LogF=open(Opts.LogFile, "a")
    LogF.write("%s: %s %s\n"%(Opts.PrgName,TimeStr,Message))
    LogF.close()
  return

def Msg(Opts,Message):
  if Opts.Verbose:
    sys.stdout.write("%s: %s\n"%(Opts.PrgName,Message))
  FileLog(Opts,Message)
  return
  
def ErrMsg(Opts,Message):
  sys.stderr.write("%s: ERROR %s\n"%(Opts.PrgName,Message))
  sys.stderr.flush()
  FileLog(Opts,"ERROR %s"%(Message,))
  return
      
def WaitSeconds(Opts):
  if Opts.DEBUG and Opts.NoWaitOnDebug:
    ErrMsg(Opts,"• WaitSeconds(NoWaitOnDebug)")
  else:
    sys.stdout.write(".")
    time.sleep(Opts.SmallWait)
  return

def MiniWait(Opts):
  if not Opts.DEBUG:
    time.sleep(Opts.MiniWait)
  return

def GetVolumeSize(Opts,VolumeName):
  """Return the size of VolumeName or 0 (zero)"""
  DebugFn(Opts)
  Msg(Opts,"trying to get size of %s..."%(VolumeName,) )
  ReturnedSize=0
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="lsvdisk -bytes -delim : %s"%(VolumeName,)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        # Filter lines
        for TextLine in OutputText.splitlines():
          if TextLine.startswith("capacity"):
            CapacityLine=TextLine
            break # of for
        CapacityInBytes=CapacityLine.split(":")[1]
        ReturnedSize=int(CapacityInBytes)
        Msg(Opts,"found size (%dB) for %s"%(ReturnedSize,VolumeName))
    finally:
      return ReturnedSize
  else:
    return ReturnedSize # 0

def GetTimedSuffix(Opts):
  """Return a timed suffix like _20140208_183716 for 2014/feb/08 6:37:16PM"""
  DebugFn(Opts)
  TimeStr="_%04d%02d%02d_%02d%02d%02d" % (time.localtime(time.time())[0:6])
  return TimeStr

def CreateNowNamedVolume(Opts,VolumeName):
  """Create a now named volume based on VolumeName, and return the name"""
  DebugFn(Opts)
  Msg(Opts,"trying to create new volume to snap %s..."%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      TimeSuffix=GetTimedSuffix(Opts)
      NowVolumeName="%s%s" % (VolumeName,TimeSuffix)
      NewSnapSize=GetVolumeSize(Opts,VolumeName)
      CxCommand="mkvdisk -mdiskgrp %s -iogrp %d -size %d -unit b -rsize %d%% -warning %d%% -autoexpand -easytier %s -name %s" % (Opts.Pool,Opts.IOgroup,NewSnapSize,Opts.PercentThin,Opts.SnapWarning,Opts.SnapEasy,NowVolumeName)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        Msg(Opts,"volume %s created" % (NowVolumeName,))
        return NowVolumeName
      else:
        Msg(Opts,"could not create volume %s!" % (NowVolumeName,))
        return COULD_NOT_CREATE
    except:
      Msg(Opts,"could not create volume %s!" % (NowVolumeName,))
      return COULD_NOT_CREATE
  else:
    return COULD_NOT_CREATE

def GetListOfNamedSnaps(Opts,VolumeName):
  """Get the list of volumes (snapshots) with VolumeName like base name"""
  DebugFn(Opts)
  Msg(Opts,"trying to get the list of snapshots of %s..."%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      VolumeList=[]
      CxCommand="lsvdisk -bytes"
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      if len(OutputText)>0:
        # Filter lines
        for TextLine in OutputText.splitlines():
          SecondWord=TextLine.split()[1]
          if SecondWord.startswith("%s_" % (VolumeName,)):
            # Append to result list
            # Msg(Opts,"%s volume found" % (SecondWord,))
            VolumeList.append(SecondWord)
        Msg(Opts,"done listing snapshots for %s"%(VolumeName,))
        return VolumeList
      else:
        return []
    except:
      return []
  else:
    return []

def CountNamedSnaps(Opts,VolumeName):
  """Count how many snapshots a VolumeName has"""
  DebugFn(Opts)
  Msg(Opts,"trying to count snapshots for volume %s"%(VolumeName,))
  return len(GetListOfNamedSnaps(Opts,VolumeName))

def GetNameOfFirstNamedSnap(Opts,VolumeName):
  """Get name of first volume (snapshot) with VolumeName like base name"""
  DebugFn(Opts)
  Msg(Opts,"trying to get first snapshot for %s"%(VolumeName,))
  return sorted(GetListOfNamedSnaps(Opts,VolumeName))[0]

def RemoveVolume(Opts,VolumeName):
  """Remove named volume from storage"""
  DebugFn(Opts)
  Msg(Opts,"trying to force remove volume %s"%(VolumeName,))
  if Opts.Storage1Type=="storwize":
    try:
      CxCommand="rmvdisk -force %s" % (VolumeName,)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Msg(Opts,"Volume %s removed." % (VolumeName))
    except:
      sys.stderr.write("%s: volume %s could not be removed.\n" % (Opts.PrgName,VolumeName))
  else:
    sys.stderr.write("%s: volume %s could not be removed.\n" % (Opts.PrgName,VolumeName))
  return

def SnapVolumeToVolume(Opts,SourceVolume,TargetVolume):
  """Create snapshot mapping between source volume and target volume"""
  DebugFn(Opts)
  Msg(Opts,"trying to snap %s into %s"%(SourceVolume,TargetVolume))
  if Opts.Storage1Type=="storwize":
    try:
      MatchOb = re.match( '%s_([0-9]{8}_[0-9]{6})'%(SourceVolume), TargetVolume)
      if MatchOb:
        TimeSuffix=MatchOb.group(1)
      else:
        TimeSuffix="__NOTSEQ__%d" % (random.randint(1000,10000),)
      SnapshotNow="%s%s%s" % (SourceVolume,"_snapshot_",TimeSuffix)
      CxCommand="mkfcmap -source %s -target %s -name %s -copyrate %d" % (SourceVolume,TargetVolume,SnapshotNow,Opts.SnapSpace)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      CxCommand="startfcmap -prep -restore %s" % (SnapshotNow,)
      OutputText=UNIXconnect(Opts,Opts.Storage1User,Opts.Storage1Name,CxCommand)
      Msg(Opts,"%s: snapshot of volume %s created into %s (pair named %s)" % (Opts.PrgName,SourceVolume,TargetVolume,SnapshotNow))
    except:
      sys.stderr.write("%s: snapshot of volume %s could not created into %s!\n" % (Opts.PrgName,SourceVolume,TargetVolume))
  return
  
def ExitIfKillFile(Opts):
  """Terminates script if kill file is found"""
  DebugFn(Opts)
  if os.path.exists(Opts.KillFile):
    # Exit now
    try:
      os.unlink(Opts.KillFile)
      sys.stdout.write("%s: kill file found and removed, exiting...\n" % (Opts.PrgName,))
      FileLog(Opts,"kill file found and removed, exiting...")
    except IOError:
      sys.stdout.write("%s: error trying to remove killfile (%s)\n" % (Opts.PrgName,Opts.KillFile))
      FileLog(Opts,"error trying to remove killfile (%s)"%(Opts.KillFile,))
    sys.exit(5)
  return
  
def WaitNextIteration(Opts):
  """Wait for next iteration"""
  # This function waits ONE HOUR if RunOClock==FALSE
  # This function waits for HOUR OCLOCK if RunOClock==TRUE
  DebugFn(Opts)
  StartingMinute=Opts.StartingSecond//60
  FullWait=Opts.FullWait//60
  Msg(Opts, "waiting for next iteration, now is %s seq minutes"%(StartingMinute,))
  while True:
    # Run forever until break
    ExitIfKillFile(Opts)
    WaitSeconds(Opts)
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
  sys.stdout.write("\n")
  sys.stdout.flush()
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
  parser.add_option("-O", "--no-log", dest="NoLog", action="store_true", help="No log to a file", default=False)
  parser.add_option("-d", "--workdir", dest="WorkDir", action="store", type="string", help="Working directory", default="M:\Automatizacion")
  parser.add_option("-r", "--ur", "--remote-unix-command", dest="RemoteUnixCommand", action="store", type="string", help="Remote execution command for Unix connections", default="plink")
  parser.add_option("-R", "--wr", "--remote-windows-command", dest="RemoteWindowsCommand", action="store", type="string", help="Remote execution command for Windows connections", default="psexec")
  parser.add_option("--t1n", "--storage1name", dest="Storage1Name", action="store", type="string", help="Storage server #1 hostname", default="V3700")
  parser.add_option("--t1u", "--storage1user", dest="Storage1User", action="store", type="string", help="Storage server #1 username to connect to", default="soporte")
  parser.add_option("--t1t", "--storage1type", dest="Storage1Type", action="store", type="string", help="Storage server #1 type of OS", default="storwize")
  parser.add_option("-n", "--snapshots", dest="Snapshots", action="store", type="int", help="How many snapshots to maintain", default=6)
  parser.add_option("-p", "--percent-thin", dest="PercentThin", action="store", type="int", help="How thin make snapshots, percent integer", default=5)
  parser.add_option("-P", "--storage-pool", dest="Pool", action="store", type="string", help="Storage pool name", default="CLUSTER_VMWARE")
  parser.add_option("-c", "--clock-minute", dest="OClock", action="store", type="int", help="Minutes to replicate on", default=5)
  parser.add_option("-w", "--small-wait", dest="SmallWait", action="store", type="int", help=SUPPRESS_HELP, default=60)
  parser.add_option("-W", "--full-wait", dest="FullWait",action="store", type="int", help="Time between snapshots (seconds)", default=60*60)
  parser.add_option("-C", "--only-clean", "--clean-only", dest="OnlyClean", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("-K", "--kill", dest="Kill", action="store_true", default=False, help="Kill another instance of script")
  parser.add_option("--run-each",dest="RunOClock",action="store_false",default=True,help=SUPPRESS_HELP)
  parser.add_option("--DEBUG", dest="DEBUG", action="store_true", default=False, help=SUPPRESS_HELP)
  parser.add_option("--DEBUGUNIX", dest="DEBUGUNIX", action="store_true", default=False, help=SUPPRESS_HELP)

  (Options, Args)=parser.parse_args()
  Options.PrgName=PrgName
  Options.KillFile=KillFile
  Options.ExitCode=0
  # Internal variables
  Options.NoWaitOnDebug=True
  Options.MiniWait=3
  Options.Raise=True
  Options.IOgroup=0
  Options.SnapWarning=95
  Options.SnapTier="generic_hdd"
  Options.SnapEasy="on"
  Options.SnapSpace=0

  
  if Options.Kill:
    CreateKillFile(KillFile)

  TimeStr="%04d/%02d/%02d %02d:%02d:%02d" % (time.localtime(time.time())[0:6])
  Options.StartingSecond=int(time.time())
  sys.stdout.write("------------------------------------------------------------------------\n")
  if Options.OnlyClean:
    Msg(Options,"starting to clean at %s"%(TimeStr,))
  else:
    Msg(Options,"starting out at %s"%(TimeStr,))
  # ----------------------------------------------------------- Only for connectivity tests

  # ----------------------------------------------------------- Only for connectivity tests
  if Options.DEBUGUNIX:
    Options.DEBUG=True
    if len(Args)>0:
      for OneName in Args:
        UNIXconnect(Options,"root",OneName,"ping %s"%(OneName,))
    else:
      UNIXconnect(Options,"root","ESX11CO","ping 192.168.20.1")
    sys.exit(0)
  # ----------------------------------------------------------- Only for connectivity tests
  
  # Change to working directory
  if not Options.DEBUG:
    os.chdir(Options.WorkDir)
  
  while len(Args)>0:
    # Do forever
    # Create snapshots
    TimeStr="%04d/%02d/%02d %02d:%02d:%02d" % (time.localtime(time.time())[0:6])
    Msg(Options,"waking at %s"%(TimeStr,))
    for OneVolume in Args:
      NewVolumeName=CreateNowNamedVolume(Options,OneVolume)
      SnapVolumeToVolume(Options,OneVolume,NewVolumeName)
      while CountNamedSnaps(Options,OneVolume)>Options.Snapshots:
        # Remove excess of snapshots
        try:
          FirstSnapshot=GetNameOfFirstNamedSnap(Options,OneVolume)
          RemoveVolume(Options,FirstSnapshot)
        except:
          continue # with while
    WaitNextIteration(Options)
  else:
    ErrMsg(Options,"No arguments!")
  #The End
  sys.exit(0)
      
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
  
# --------------------------------------------------------------------------------
# ASSERTS:
# PythonWin or ActivePython installed on machine running script
# On Windows servers:
#   Directory M:\Automatizacion or option -d WORKINGDIR
#   Command   M:\Automatizacion\PLINK.exe or option -r X:\PATH\REMOTE.EXE
#   File      M:\Automatizacion\windowsprivdsa.ppk or PuTTY configuration for host
#   ### This is user PRIVATE DSA KEY ###
#   File      M:\Automatizacion\windowspubdsa or PuTTY configuration for host
# Must be a V3700 host definition on PuTTY saved, with priv/pub DSA keys defined or
#   a named configuration named with option --t1n STORAGESERVER or with option
#   --storage1name STORAGESERVER
# On Storwize Storage servers:
#   windowspubdsa installed
#   ### This is user PUBLIC DSA KEY  ###
#
# --------------------------------------------------------------------------------
# Ramon Barrios Lascar, 2014, Ínodo S.A.S.
# --------------------------------------------------------------------------------
